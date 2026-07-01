from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models.models import (
    Incidencia, CambioEstado, Habitacion, FotoIncidencia,
    EstadoEnum, TipoEnum, PrioridadEnum, OrigenEnum, TipoSolicitudEnum, TipoLimpiezaEnum
)
from app.websocket_manager import manager
from app.routers.incidencias import notificar_relevantes
import cloudinary
import cloudinary.uploader
import os

router = APIRouter(prefix="/h", tags=["huesped"])

TIPO_LIMPIEZA_LABELS = {
    "toallas": "Toallas",
    "sabanas": "Cambio de ropa de cama",
    "amenities": "Amenities (jabón, champú, etc.)",
    "limpieza_general": "Limpieza general de la habitación",
    "otro": "Otra necesidad de limpieza",
    None: "Solicitud de limpieza",
}

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", "ddamj384r"),
    api_key=os.environ.get("CLOUDINARY_API_KEY", "151665652414153"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", "j1AEOuDOoLSmVi-mcP6lbwHRVPc"),
)


class IncidenciaHuespedCreate(BaseModel):
    tipo_solicitud: TipoSolicitudEnum          # mantenimiento | limpieza
    tipo: Optional[TipoEnum] = None            # solo si mantenimiento
    tipo_limpieza: Optional[TipoLimpiezaEnum] = None  # solo si limpieza
    descripcion: Optional[str] = None
    nombre_huesped: Optional[str] = None
    idioma: Optional[str] = "es"
    dispositivo_id: Optional[str] = None


def gen_codigo(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(Incidencia).count() + 1
    return f"INC-{year}-{count:04d}"


def _habitacion_de_token(db: Session, token: str) -> Habitacion:
    hab = db.query(Habitacion).filter(
        Habitacion.token == token,
        Habitacion.activa == True
    ).first()
    if not hab:
        raise HTTPException(status_code=404, detail="Enlace no válido")
    return hab


@router.get("/{token}/info")
def info_habitacion(token: str, db: Session = Depends(get_db)):
    """Devuelve el número de habitación asociado al token — para que la pantalla muestre 'Hab. 204'."""
    hab = _habitacion_de_token(db, token)
    return {"habitacion": hab.numero}


@router.post("/{token}")
async def crear_incidencia_huesped(
    token: str,
    data: IncidenciaHuespedCreate,
    db: Session = Depends(get_db),
):
    hab = _habitacion_de_token(db, token)

    es_limpieza = data.tipo_solicitud == TipoSolicitudEnum.limpieza
    tipo = None if es_limpieza else (data.tipo if data.tipo else TipoEnum.otro)
    descripcion = data.descripcion

    # Si es limpieza sin descripción, usamos la etiqueta del tipo elegido
    if es_limpieza and not descripcion:
        descripcion = TIPO_LIMPIEZA_LABELS.get(
            data.tipo_limpieza.value if data.tipo_limpieza else None, "Solicitud de limpieza"
        )

    inc = Incidencia(
        codigo=gen_codigo(db),
        habitacion=hab.numero,
        tipo=tipo,
        tipo_limpieza=data.tipo_limpieza if es_limpieza else None,
        descripcion=descripcion,
        prioridad=PrioridadEnum.normal,
        estado=EstadoEnum.recibido,
        origen=OrigenEnum.huesped,
        tipo_solicitud=data.tipo_solicitud,
        nombre_huesped=data.nombre_huesped or None,
        idioma=data.idioma or "es",
        dispositivo_id=data.dispositivo_id or None,
        reporter_id=None,  # sin usuario registrado
    )
    db.add(inc)
    db.flush()

    cambio = CambioEstado(
        incidencia_id=inc.id,
        usuario_id=None,
        estado_anterior=None,
        estado_nuevo=EstadoEnum.recibido,
        nota=f"Solicitud de huésped{' — ' + data.nombre_huesped if data.nombre_huesped else ''}",
    )
    db.add(cambio)
    db.commit()
    db.refresh(inc)

    # Aviso en tiempo real a mantenimiento/gobernanta/admin conectados
    await manager.broadcast({"evento": "nueva_incidencia", "incidencia": {
        "id": inc.id, "habitacion": inc.habitacion, "tipo_solicitud": inc.tipo_solicitud,
    }})

    # Notificación push: mantenimiento+admin si es avería, gobernanta+admin si es limpieza
    destino_txt = "mantenimiento" if data.tipo_solicitud == TipoSolicitudEnum.mantenimiento else "limpieza"
    quien = data.nombre_huesped or "Un huésped"
    notificar_relevantes(
        db, inc,
        titulo=f"Hab. {inc.habitacion} — Solicitud de {destino_txt}",
        cuerpo=f"{quien}: {descripcion or 'Nueva solicitud'}",
    )

    return {"ok": True, "codigo": inc.codigo, "id": inc.id}


@router.post("/{token}/fotos/{incidencia_id}")
async def subir_foto_huesped(
    token: str,
    incidencia_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Permite al huésped adjuntar fotos a la solicitud que acaba de crear, sin necesidad de login."""
    hab = _habitacion_de_token(db, token)

    inc = db.query(Incidencia).filter(
        Incidencia.id == incidencia_id,
        Incidencia.habitacion == hab.numero,
        Incidencia.origen == OrigenEnum.huesped,
    ).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    count = db.query(FotoIncidencia).filter(FotoIncidencia.incidencia_id == incidencia_id).count()
    if count >= 3:
        raise HTTPException(status_code=400, detail="Máximo 3 fotos por solicitud")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo imágenes")

    contents = await file.read()
    result = cloudinary.uploader.upload(
        contents,
        folder=f"hotelpintor/{incidencia_id}",
        transformation=[{"width": 1200, "crop": "limit", "quality": "auto:good"}],
    )

    foto = FotoIncidencia(
        incidencia_id=incidencia_id,
        url=result["secure_url"],
        subida_por_id=None,
    )
    db.add(foto)
    db.commit()
    db.refresh(foto)

    await manager.broadcast({"evento": "foto_agregada", "incidencia_id": incidencia_id})

    return {"id": foto.id, "url": foto.url}


@router.get("/{token}/mis-solicitudes")
def mis_solicitudes(
    token: str,
    dispositivo_id: str,
    db: Session = Depends(get_db),
):
    """
    Solicitudes hechas desde este mismo dispositivo, en esta misma habitación,
    en los últimos 30 días. Solo devuelve lo que le concierne al huésped
    (estado, su propio mensaje, nota para cliente si la hay) — nunca los
    comentarios internos de staff, quién lo reportó/asignó, etc.
    """
    hab = _habitacion_de_token(db, token)
    if not dispositivo_id:
        return []

    desde = datetime.utcnow() - timedelta(days=30)
    incidencias = db.query(Incidencia).filter(
        Incidencia.habitacion == hab.numero,
        Incidencia.dispositivo_id == dispositivo_id,
        Incidencia.origen == OrigenEnum.huesped,
        Incidencia.creado_en >= desde,
    ).order_by(Incidencia.creado_en.desc()).all()

    return [
        {
            "id": i.id,
            "codigo": i.codigo,
            "habitacion": i.habitacion,
            "tipo_solicitud": i.tipo_solicitud,
            "tipo": i.tipo,
            "tipo_limpieza": i.tipo_limpieza,
            "descripcion": i.descripcion,
            "estado": i.estado,
            "nota_cliente": i.nota_cliente,
            "creado_en": i.creado_en,
            "resuelto_en": i.resuelto_en,
        }
        for i in incidencias
    ]
