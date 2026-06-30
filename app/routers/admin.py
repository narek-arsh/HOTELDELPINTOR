from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import get_db
from app.models.models import Usuario, Incidencia, RolEnum
from app.auth import hash_password, require_rol

router = APIRouter(prefix="/api/admin", tags=["admin"])


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    username: Optional[str] = None
    password: str
    rol: RolEnum
    edificio: Optional[str] = None
    planta: Optional[str] = None


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    edificio: Optional[str] = None
    planta: Optional[str] = None
    activo: Optional[bool] = None


def usuario_dict(u: Usuario) -> dict:
    return {
        "id": u.id,
        "nombre": u.nombre,
        "email": u.email,
        "username": u.username,
        "rol": u.rol,
        "edificio": u.edificio,
        "planta": u.planta,
        "activo": u.activo,
        "creado_en": u.creado_en,
    }


@router.get("/usuarios")
def listar_usuarios(
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin)),
):
    return [usuario_dict(u) for u in
            db.query(Usuario).order_by(Usuario.rol, Usuario.nombre).all()]


@router.post("/usuarios")
def crear_usuario(
    data: UsuarioCreate,
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin)),
):
    if db.query(Usuario).filter(Usuario.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    if data.username and db.query(Usuario).filter(Usuario.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username ya en uso")

    u = Usuario(
        nombre=data.nombre,
        email=data.email,
        username=data.username or None,
        password_hash=hash_password(data.password),
        rol=data.rol,
        edificio=data.edificio,
        planta=data.planta,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return usuario_dict(u)


@router.patch("/usuarios/{uid}")
def actualizar_usuario(
    uid: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin)),
):
    u = db.query(Usuario).filter(Usuario.id == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.nombre is not None: u.nombre = data.nombre
    if data.email is not None: u.email = data.email
    if data.username is not None: u.username = data.username
    if data.password is not None: u.password_hash = hash_password(data.password)
    if data.edificio is not None: u.edificio = data.edificio
    if data.planta is not None: u.planta = data.planta
    if data.activo is not None: u.activo = data.activo

    db.commit()
    return usuario_dict(u)


@router.delete("/usuarios/{uid}")
def desactivar_usuario(
    uid: int,
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin)),
):
    u = db.query(Usuario).filter(Usuario.id == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="No encontrado")
    u.activo = False
    db.commit()
    return {"ok": True}


@router.get("/estadisticas")
def estadisticas(
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin)),
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
