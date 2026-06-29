from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app.models.models import Incidencia, CambioEstado, Usuario, EstadoEnum, TipoEnum, PrioridadEnum, RolEnum
from app.auth import get_current_user, require_rol
from app.websocket_manager import manager

router = APIRouter(prefix="/api/incidencias", tags=["incidencias"])


# ── Schemas ──────────────────────────────────────────────────────

class IncidenciaCreate(BaseModel):
    habitacion: str
    tipo: TipoEnum
    descripcion: Optional[str] = None
    prioridad: PrioridadEnum = PrioridadEnum.normal
    notas: Optional[str] = None


class CambioEstadoRequest(BaseModel):
    estado: EstadoEnum
    nota: Optional[str] = None


def incidencia_to_dict(inc: Incidencia) -> dict:
    return {
        "id": inc.id,
        "codigo": inc.codigo,
        "habitacion": inc.habitacion,
        "edificio": inc.edificio,
        "tipo": inc.tipo,
        "descripcion": inc.descripcion,
        "prioridad": inc.prioridad,
        "estado": inc.estado,
        "notas_mantenimiento": inc.notas_mantenimiento,
        "reporter": {"id": inc.reporter.id, "nombre": inc.reporter.nombre, "planta": inc.reporter.planta} if inc.reporter else None,
        "asignado": {"id": inc.asignado.id, "nombre": inc.asignado.nombre} if inc.asignado else None,
        "creado_en": inc.creado_en,
        "actualizado_en": inc.actualizado_en,
        "resuelto_en": inc.resuelto_en,
        "cambios": [
            {
                "estado_anterior": c.estado_anterior,
                "estado_nuevo": c.estado_nuevo,
                "nota": c.nota,
                "fecha": c.fecha,
                "usuario": c.usuario.nombre if c.usuario else None,
            }
            for c in inc.cambios
        ],
    }


def generar_codigo(db: Session) -> str:
    year = datetime.utcnow().year
    count = db.query(Incidencia).count() + 1
    return f"INC-{year}-{count:04d}"


# ── Endpoints ────────────────────────────────────────────────────

@router.post("/")
async def crear_incidencia(
    data: IncidenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol(RolEnum.limpiadora, RolEnum.admin))
):
    if data.tipo == TipoEnum.otro and not data.descripcion:
        raise HTTPException(status_code=400, detail="Descripción obligatoria para tipo 'otro'")

    inc = Incidencia(
        codigo=generar_codigo(db),
        habitacion=data.habitacion,
        edificio=current_user.edificio,
        tipo=data.tipo,
        descripcion=data.descripcion,
        prioridad=data.prioridad,
        notas_mantenimiento=data.notas,
        estado=EstadoEnum.recibido,
        reporter_id=current_user.id,
    )
    db.add(inc)
    db.flush()

    cambio = CambioEstado(
        incidencia_id=inc.id,
        usuario_id=current_user.id,
        estado_anterior=None,
        estado_nuevo=EstadoEnum.recibido,
        nota="Incidencia creada",
    )
    db.add(cambio)
    db.commit()
    db.refresh(inc)

    payload = incidencia_to_dict(inc)
    await manager.broadcast({"evento": "nueva_incidencia", "incidencia": payload})

    return payload


@router.get("/")
def listar_incidencias(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(Incidencia)

    # Limpiadora solo ve las suyas
    if current_user.rol == RolEnum.limpiadora:
        query = query.filter(Incidencia.reporter_id == current_user.id)

    if estado:
        query = query.filter(Incidencia.estado == estado)

    incidencias = query.order_by(Incidencia.creado_en.desc()).all()
    return [incidencia_to_dict(i) for i in incidencias]


@router.get("/{incidencia_id}")
def obtener_incidencia(
    incidencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    inc = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    if current_user.rol == RolEnum.limpiadora and inc.reporter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso")
    return incidencia_to_dict(inc)


@router.patch("/{incidencia_id}/estado")
async def cambiar_estado(
    incidencia_id: int,
    data: CambioEstadoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol(RolEnum.mantenimiento, RolEnum.admin))
):
    inc = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    estado_anterior = inc.estado
    inc.estado = data.estado
    inc.actualizado_en = datetime.utcnow()

    if data.estado == EstadoEnum.resuelto:
        inc.resuelto_en = datetime.utcnow()
        inc.asignado_id = current_user.id

    cambio = CambioEstado(
        incidencia_id=inc.id,
        usuario_id=current_user.id,
        estado_anterior=estado_anterior,
        estado_nuevo=data.estado,
        nota=data.nota,
    )
    db.add(cambio)
    db.commit()
    db.refresh(inc)

    payload = incidencia_to_dict(inc)
    await manager.broadcast({"evento": "estado_cambiado", "incidencia": payload})

    return payload


@router.delete("/{incidencia_id}")
def archivar_incidencia(
    incidencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol(RolEnum.admin))
):
    inc = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    inc.estado = EstadoEnum.archivado
    db.commit()
    return {"ok": True}
