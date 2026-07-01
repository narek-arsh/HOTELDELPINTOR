from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models.models import (
    Incidencia, CambioEstado, Habitacion,
    EstadoEnum, TipoEnum, PrioridadEnum, OrigenEnum, TipoSolicitudEnum
)

router = APIRouter(prefix="/h", tags=["huesped"])


class IncidenciaHuespedCreate(BaseModel):
    tipo_solicitud: TipoSolicitudEnum          # mantenimiento | limpieza
    tipo: Optional[TipoEnum] = None            # solo si mantenimiento
    descripcion: Optional[str] = None
    nombre_huesped: Optional[str] = None
    idioma: Optional[str] = "es"


def gen_codigo(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(Incidencia).count() + 1
    return f"INC-{year}-{count:04d}"


@router.get("/{token}/info")
def info_habitacion(token: str, db: Session = Depends(get_db)):
    """Devuelve el número de habitación asociado al token — para que la pantalla muestre 'Hab. 204'."""
    hab = db.query(Habitacion).filter(
        Habitacion.token == token,
        Habitacion.activa == True
    ).first()
    if not hab:
        raise HTTPException(status_code=404, detail="Enlace no válido")
    return {"habitacion": hab.numero}


@router.post("/{token}")
def crear_incidencia_huesped(
    token: str,
    data: IncidenciaHuespedCreate,
    db: Session = Depends(get_db),
):
    hab = db.query(Habitacion).filter(
        Habitacion.token == token,
        Habitacion.activa == True
    ).first()
    if not hab:
        raise HTTPException(status_code=404, detail="Enlace no válido")

    # Para solicitudes de limpieza no hace falta tipo de mantenimiento
    tipo = data.tipo if data.tipo else TipoEnum.otro
    descripcion = data.descripcion

    # Si es limpieza sin descripción, ponemos una por defecto
    if data.tipo_solicitud == TipoSolicitudEnum.limpieza and not descripcion:
        descripcion = "Solicitud de limpieza"

    inc = Incidencia(
        codigo=gen_codigo(db),
        habitacion=hab.numero,
        tipo=tipo,
        descripcion=descripcion,
        prioridad=PrioridadEnum.normal,
        estado=EstadoEnum.recibido,
        origen=OrigenEnum.huesped,
        tipo_solicitud=data.tipo_solicitud,
        nombre_huesped=data.nombre_huesped or None,
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

    return {"ok": True, "codigo": inc.codigo}
