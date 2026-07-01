from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.models import Usuario, Incidencia, Habitacion, RolEnum
from app.auth import hash_password, require_rol

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Usuarios ─────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nombre: str
    username: str
    password: str
    rol: RolEnum
    planta: Optional[str] = None


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    planta: Optional[str] = None
    activo: Optional[bool] = None


def usuario_dict(u: Usuario) -> dict:
    return {
        "id": u.id,
        "nombre": u.nombre,
        "username": u.username,
        "rol": u.rol,
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
    username_norm = data.username.strip().lower()
    if not username_norm:
        raise HTTPException(status_code=400, detail="Username obligatorio")
    if db.query(Usuario).filter(func.lower(Usuario.username) == username_norm).first():
        raise HTTPException(status_code=400, detail="Username ya en uso")

    u = Usuario(
        nombre=data.nombre,
        username=username_norm,
        password_hash=hash_password(data.password),
        rol=data.rol,
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

    if data.nombre is not None:
        u.nombre = data.nombre
    if data.username is not None:
        username_norm = data.username.strip().lower()
        existe = db.query(Usuario).filter(
            func.lower(Usuario.username) == username_norm, Usuario.id != uid
        ).first()
        if existe:
            raise HTTPException(status_code=400, detail="Username ya en uso")
        u.username = username_norm
    if data.password is not None:
        u.password_hash = hash_password(data.password)
    if data.planta is not None:
        u.planta = data.planta
    if data.activo is not None:
        u.activo = data.activo

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


# ── Habitaciones ─────────────────────────────────────────────────

class HabitacionCreate(BaseModel):
    numero: str


class HabitacionesBulkCreate(BaseModel):
    numeros: List[str]


import secrets

def habitacion_dict(h: Habitacion) -> dict:
    return {"id": h.id, "numero": h.numero, "activa": h.activa, "token": h.token}


def _gen_token(db) -> str:
    """Genera un token único de 10 caracteres alfanuméricos."""
    while True:
        tok = secrets.token_urlsafe(7)[:10]
        if not db.query(Habitacion).filter(Habitacion.token == tok).first():
            return tok


@router.get("/habitaciones")
def listar_habitaciones(
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin, RolEnum.limpiadora, RolEnum.gobernanta, RolEnum.mantenimiento)),
):
    habs = db.query(Habitacion).filter(Habitacion.activa == True).order_by(Habitacion.orden, Habitacion.numero).all()
    return [habitacion_dict(h) for h in habs]


@router.post("/habitaciones")
def crear_habitacion(
    data: HabitacionCreate,
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin)),
):
    numero = data.numero.strip()
    if not numero:
        raise HTTPException(status_code=400, detail="Número obligatorio")
    existente = db.query(Habitacion).filter(Habitacion.numero == numero).first()
    if existente:
        if not existente.activa:
            existente.activa = True
            if not existente.token:
                existente.token = _gen_token(db)
            db.commit()
            return habitacion_dict(existente)
        raise HTTPException(status_code=400, detail="Esa habitación ya existe")
    max_orden = db.query(Habitacion).count()
    h = Habitacion(numero=numero, orden=max_orden, token=_gen_token(db))
    db.add(h)
    db.commit()
    db.refresh(h)
    return habitacion_dict(h)


@router.post("/habitaciones/bulk")
def crear_habitaciones_bulk(
    data: HabitacionesBulkCreate,
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin)),
):
    creadas = []
    max_orden = db.query(Habitacion).count()
    for numero in data.numeros:
        numero = numero.strip()
        if not numero:
            continue
        existente = db.query(Habitacion).filter(Habitacion.numero == numero).first()
        if existente:
            if not existente.activa:
                existente.activa = True
                if not existente.token:
                    existente.token = _gen_token(db)
                creadas.append(numero)
            continue
        h = Habitacion(numero=numero, orden=max_orden, token=_gen_token(db))
        db.add(h)
        max_orden += 1
        creadas.append(numero)
    db.commit()
    return {"creadas": creadas, "total": len(creadas)}


@router.delete("/habitaciones/{hid}")
def eliminar_habitacion(
    hid: int,
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin)),
):
    h = db.query(Habitacion).filter(Habitacion.id == hid).first()
    if not h:
        raise HTTPException(status_code=404, detail="No encontrada")
    h.activa = False
    db.commit()
    return {"ok": True}


# ── Estadísticas ─────────────────────────────────────────────────

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
