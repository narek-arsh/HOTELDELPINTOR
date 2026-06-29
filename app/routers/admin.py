from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.database import get_db
from app.models.models import Usuario, Incidencia, RolEnum, EstadoEnum
from app.auth import hash_password, require_rol
from sqlalchemy import func

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Schemas ──────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: RolEnum
    edificio: Optional[str] = None
    planta: Optional[str] = None


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    edificio: Optional[str] = None
    planta: Optional[str] = None
    activo: Optional[bool] = None


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/usuarios")
def listar_usuarios(
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin))
):
    usuarios = db.query(Usuario).order_by(Usuario.rol, Usuario.nombre).all()
    return [
        {
            "id": u.id,
            "nombre": u.nombre,
            "email": u.email,
            "rol": u.rol,
            "edificio": u.edificio,
            "planta": u.planta,
            "activo": u.activo,
            "creado_en": u.creado_en,
        }
        for u in usuarios
    ]


@router.post("/usuarios")
def crear_usuario(
    data: UsuarioCreate,
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin))
):
    existente = db.query(Usuario).filter(Usuario.email == data.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    usuario = Usuario(
        nombre=data.nombre,
        email=data.email,
        password_hash=hash_password(data.password),
        rol=data.rol,
        edificio=data.edificio,
        planta=data.planta,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"id": usuario.id, "nombre": usuario.nombre, "rol": usuario.rol}


@router.patch("/usuarios/{usuario_id}")
def actualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin))
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.nombre is not None:
        usuario.nombre = data.nombre
    if data.email is not None:
        usuario.email = data.email
    if data.password is not None:
        usuario.password_hash = hash_password(data.password)
    if data.edificio is not None:
        usuario.edificio = data.edificio
    if data.planta is not None:
        usuario.planta = data.planta
    if data.activo is not None:
        usuario.activo = data.activo

    db.commit()
    return {"ok": True}


@router.delete("/usuarios/{usuario_id}")
def desactivar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin))
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.activo = False
    db.commit()
    return {"ok": True}


@router.get("/estadisticas")
def estadisticas(
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin))
):
    total = db.query(Incidencia).count()
    por_estado = dict(
        db.query(Incidencia.estado, func.count(Incidencia.id))
        .group_by(Incidencia.estado).all()
    )
    por_tipo = dict(
        db.query(Incidencia.tipo, func.count(Incidencia.id))
        .group_by(Incidencia.tipo).all()
    )
    por_prioridad = dict(
        db.query(Incidencia.prioridad, func.count(Incidencia.id))
        .group_by(Incidencia.prioridad).all()
    )
    return {
        "total": total,
        "por_estado": por_estado,
        "por_tipo": por_tipo,
        "por_prioridad": por_prioridad,
    }
