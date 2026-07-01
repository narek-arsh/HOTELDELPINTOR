from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models.models import (
    Incidencia, CambioEstado, Usuario, ComentarioInterno, DeviceToken,
    EstadoEnum, TipoEnum, PrioridadEnum, RolEnum, TipoSolicitudEnum
)
from app.auth import get_current_user, require_rol
from app.websocket_manager import manager
from app.notifications import enviar_notificacion

router = APIRouter(prefix="/api/incidencias", tags=["incidencias"])

TIPO_LABELS = {
    "bombilla": "Cambio de bombilla",
    "puerta": "Puerta / cerradura",
    "fontaneria": "Fontanería",
    "calefaccion": "Calefacción / Aire",
    "mueble": "Mobiliario",
    "otro": "Otro",
}


class IncidenciaCreate(BaseModel):
    habitacion: str
    tipo: TipoEnum
    descripcion: Optional[str] = None
    notas: Optional[str] = None


class CambioEstadoRequest(BaseModel):
    estado: EstadoEnum
    nota: Optional[str] = None
    prioridad: Optional[PrioridadEnum] = None


class AsignarRequest(BaseModel):
    usuario_id: int


def inc_dict(inc: Incidencia, current_user: Optional[Usuario] = None) -> dict:
    es_asignada_a_mi = current_user and inc.asignado_id == current_user.id
    es_staff = current_user and (
        current_user.rol in (RolEnum.mantenimiento, RolEnum.admin, RolEnum.gobernanta)
        or (current_user.rol == RolEnum.limpiadora and es_asignada_a_mi)
    )
    es_reportante = current_user and inc.reporter_id == current_user.id
    puede_ver_chat = es_staff or es_reportante
    return {
        "id": inc.id,
        "codigo": inc.codigo,
        "habitacion": inc.habitacion,
        "tipo": inc.tipo,
        "descripcion": inc.descripcion,
        "prioridad": inc.prioridad,
        "estado": inc.estado,
        "notas": inc.notas,
        "notas_mantenimiento": inc.notas_mantenimiento,
        "notas_mantenimiento_autor_rol": inc.notas_mantenimiento_autor_rol,
        "origen": inc.origen,
        "tipo_solicitud": inc.tipo_solicitud,
        "nombre_huesped": inc.nombre_huesped,
        "reporter": {
            "id": inc.reporter.id,
            "nombre": inc.reporter.nombre,
            "planta": inc.reporter.planta,
            "rol": inc.reporter.rol,
        } if inc.reporter else None,
        "asignado": {
            "id": inc.asignado.id,
            "nombre": inc.asignado.nombre,
        } if inc.asignado else None,
        "fotos": [{"id": f.id, "url": f.url} for f in (inc.fotos or [])],
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
        "comentarios_internos": [
            {
                "id": c.id,
                "texto": c.texto,
                "fecha": c.creado_en,
                "autor": c.usuario.nombre if c.usuario else None,
                "autor_rol": c.usuario.rol if c.usuario else None,
            }
            for c in sorted(inc.comentarios_internos, key=lambda x: x.creado_en)
        ] if puede_ver_chat else [],
    }


def gen_codigo(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(Incidencia).count() + 1
    return f"INC-{year}-{count:04d}"


def tokens_de_roles(db: Session, roles: list) -> list[str]:
    usuarios = db.query(Usuario).filter(Usuario.rol.in_(roles), Usuario.activo == True).all()
    ids = [u.id for u in usuarios]
    if not ids:
        return []
    tokens = db.query(DeviceToken).filter(DeviceToken.usuario_id.in_(ids)).all()
    return [t.token for t in tokens]


def tokens_de_usuario(db: Session, usuario_id: int) -> list[str]:
    tokens = db.query(DeviceToken).filter(DeviceToken.usuario_id == usuario_id).all()
    return [t.token for t in tokens]


def tokens_de_ids(db: Session, ids) -> list[str]:
    if not ids:
        return []
    tokens = db.query(DeviceToken).filter(DeviceToken.usuario_id.in_(list(ids))).all()
    return [t.token for t in tokens]


def notificar(db: Session, tokens: list[str], titulo: str, cuerpo: str, data: dict = None):
    """Envía la notificación y borra de la base de datos cualquier token que Firebase marque como inválido."""
    if not tokens:
        print(f"[notificar] Sin tokens destino para: {titulo}")
        return
    print(f"[notificar] Enviando a {len(tokens)} token(s): {titulo}")
    resultado = enviar_notificacion(tokens, titulo, cuerpo, data)
    print(f"[notificar] Resultado: {resultado}")
    invalidos = resultado.get("tokens_invalidos", [])
    if invalidos:
        db.query(DeviceToken).filter(DeviceToken.token.in_(invalidos)).delete(synchronize_session=False)
        db.commit()
        print(f"[notificar] {len(invalidos)} token(s) inválido(s) eliminado(s)")


def ids_relevantes(db: Session, inc: Incidencia, excluir_id: Optional[int] = None) -> set:
    """
    Quién debe enterarse de esta incidencia:
    - admin siempre
    - si es de limpieza -> gobernanta también
    - si no es de limpieza (mantenimiento o aviso interno) -> mantenimiento también
    - quien la tenga asignada (limpiadora) y quien la haya reportado (si es staff)
    """
    roles = [RolEnum.admin]
    if inc.tipo_solicitud == TipoSolicitudEnum.limpieza:
        roles.append(RolEnum.gobernanta)
    else:
        roles.append(RolEnum.mantenimiento)

    ids = {u.id for u in db.query(Usuario).filter(Usuario.rol.in_(roles), Usuario.activo == True).all()}
    if inc.asignado_id:
        ids.add(inc.asignado_id)
    if inc.reporter_id:
        ids.add(inc.reporter_id)
    if excluir_id:
        ids.discard(excluir_id)
    return ids


def notificar_relevantes(db: Session, inc: Incidencia, titulo: str, cuerpo: str, excluir_id: Optional[int] = None, extra_data: dict = None):
    ids = ids_relevantes(db, inc, excluir_id)
    tokens = tokens_de_ids(db, ids)
    if tokens:
        data = {"link": "/", "incidencia_id": str(inc.id)}
        if extra_data:
            data.update(extra_data)
        notificar(db, tokens, titulo, cuerpo, data)


def puede_gestionar(current_user: Usuario, inc: Incidencia) -> bool:
    """¿Puede este usuario cambiar el estado de esta incidencia?"""
    rol = current_user.rol
    if rol == RolEnum.admin:
        return True
    if rol == RolEnum.mantenimiento:
        return inc.tipo_solicitud != TipoSolicitudEnum.limpieza
    if rol == RolEnum.gobernanta:
        return inc.tipo_solicitud == TipoSolicitudEnum.limpieza
    if rol == RolEnum.limpiadora:
        return inc.asignado_id == current_user.id
    return False


def puede_comentar(current_user: Usuario, inc: Incidencia) -> bool:
    """¿Puede comentar? Igual que puede_gestionar, pero además gobernanta
    conserva la posibilidad de comentar en los avisos que ella misma reportó
    (aunque no sean de limpieza), como podía hacer antes de este cambio."""
    if puede_gestionar(current_user, inc):
        return True
    if current_user.rol == RolEnum.gobernanta and inc.reporter_id == current_user.id:
        return True
    return False


@router.post("/")
async def crear_incidencia(
    data: IncidenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_rol(RolEnum.limpiadora, RolEnum.gobernanta, RolEnum.mantenimiento, RolEnum.admin)
    ),
):
    if data.tipo == TipoEnum.otro and not data.descripcion:
        raise HTTPException(status_code=400, detail="Descripción obligatoria para tipo 'otro'")

    inc = Incidencia(
        codigo=gen_codigo(db),
        habitacion=data.habitacion,
        tipo=data.tipo,
        descripcion=data.descripcion,
        prioridad=PrioridadEnum.normal,
        notas=data.notas,
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

    payload = inc_dict(inc, current_user)
    await manager.broadcast({"evento": "nueva_incidencia", "incidencia": payload})

    tipo_txt = inc.descripcion if inc.tipo == TipoEnum.otro else TIPO_LABELS.get(inc.tipo.value, inc.tipo.value)
    notificar_relevantes(
        db, inc,
        titulo=f"Hab. {inc.habitacion} — Nueva incidencia",
        cuerpo=f"{current_user.nombre} reportó: {tipo_txt}",
        excluir_id=current_user.id,
    )

    return payload


@router.get("/")
def listar_incidencias(
    estado: Optional[str] = None,
    reporter_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    q = db.query(Incidencia)
    rol = current_user.rol

    if rol == RolEnum.limpiadora:
        # Ve lo que ella reportó y lo que se le haya asignado
        q = q.filter(or_(
            Incidencia.reporter_id == current_user.id,
            Incidencia.asignado_id == current_user.id,
        ))
    elif rol == RolEnum.gobernanta:
        # Ve las peticiones de limpieza, más lo que ella misma reportó/tiene asignado
        q = q.filter(or_(
            Incidencia.tipo_solicitud == TipoSolicitudEnum.limpieza,
            Incidencia.reporter_id == current_user.id,
            Incidencia.asignado_id == current_user.id,
        ))
    elif rol == RolEnum.mantenimiento:
        # Ve todo lo que NO sea de limpieza (avisos internos + huésped-mantenimiento)
        q = q.filter(or_(
            Incidencia.tipo_solicitud != TipoSolicitudEnum.limpieza,
            Incidencia.tipo_solicitud.is_(None),
        ))
    elif reporter_id is not None and rol == RolEnum.admin:
        q = q.filter(Incidencia.reporter_id == reporter_id)
    # admin sin filtro de reporter_id: ve todo

    if estado:
        q = q.filter(Incidencia.estado == estado)
    return [inc_dict(i, current_user) for i in q.order_by(Incidencia.creado_en.desc()).all()]


@router.get("/{iid}")
def obtener_incidencia(
    iid: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    inc = db.query(Incidencia).filter(Incidencia.id == iid).first()
    if not inc:
        raise HTTPException(status_code=404, detail="No encontrada")
    if current_user.rol == RolEnum.limpiadora and inc.reporter_id != current_user.id and inc.asignado_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso")
    return inc_dict(inc, current_user)


@router.patch("/{iid}/estado")
async def cambiar_estado(
    iid: int,
    data: CambioEstadoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    inc = db.query(Incidencia).filter(Incidencia.id == iid).first()
    if not inc:
        raise HTTPException(status_code=404, detail="No encontrada")
    if not puede_gestionar(current_user, inc):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta petición")

    anterior = inc.estado
    inc.estado = data.estado
    inc.actualizado_en = datetime.now(timezone.utc)

    if data.nota is not None:
        inc.notas_mantenimiento = data.nota
        inc.notas_mantenimiento_autor_rol = current_user.rol

    if data.prioridad is not None:
        inc.prioridad = data.prioridad

    if data.estado == EstadoEnum.resuelto:
        inc.resuelto_en = datetime.now(timezone.utc)
        if not inc.asignado_id:
            inc.asignado_id = current_user.id

    cambio = CambioEstado(
        incidencia_id=inc.id,
        usuario_id=current_user.id,
        estado_anterior=anterior,
        estado_nuevo=data.estado,
        nota=data.nota,
    )
    db.add(cambio)
    db.commit()
    db.refresh(inc)

    payload = inc_dict(inc, current_user)
    await manager.broadcast({"evento": "estado_cambiado", "incidencia": payload})

    estado_txt = {
        "recibido": "marcada como recibida",
        "en_curso": "en curso",
        "esperando_material": "esperando material",
        "resuelto": "resuelta",
    }.get(data.estado.value, data.estado.value)

    notificar_relevantes(
        db, inc,
        titulo=f"Hab. {inc.habitacion} {estado_txt}",
        cuerpo=data.nota if data.nota else f"{current_user.nombre} actualizó la incidencia",
        excluir_id=current_user.id,
    )

    return payload


@router.patch("/{iid}/asignar")
async def asignar_incidencia(
    iid: int,
    data: AsignarRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_rol(RolEnum.admin, RolEnum.gobernanta)),
):
    inc = db.query(Incidencia).filter(Incidencia.id == iid).first()
    if not inc:
        raise HTTPException(status_code=404, detail="No encontrada")
    if inc.tipo_solicitud != TipoSolicitudEnum.limpieza:
        raise HTTPException(status_code=400, detail="Solo se pueden asignar peticiones de limpieza a una limpiadora")

    limpiadora = db.query(Usuario).filter(
        Usuario.id == data.usuario_id,
        Usuario.rol == RolEnum.limpiadora,
        Usuario.activo == True,
    ).first()
    if not limpiadora:
        raise HTTPException(status_code=400, detail="Selecciona una limpiadora válida")

    anterior = inc.estado
    inc.asignado_id = limpiadora.id
    if inc.estado == EstadoEnum.recibido:
        inc.estado = EstadoEnum.en_curso
    inc.actualizado_en = datetime.now(timezone.utc)

    comentario = ComentarioInterno(
        incidencia_id=inc.id,
        usuario_id=current_user.id,
        texto=f"📌 Asignada a {limpiadora.nombre}",
    )
    db.add(comentario)

    cambio = CambioEstado(
        incidencia_id=inc.id,
        usuario_id=current_user.id,
        estado_anterior=anterior,
        estado_nuevo=inc.estado,
        nota=f"Asignada a {limpiadora.nombre}",
    )
    db.add(cambio)
    db.commit()
    db.refresh(inc)

    payload = inc_dict(inc, current_user)
    await manager.broadcast({"evento": "incidencia_asignada", "incidencia": payload})

    tokens = tokens_de_usuario(db, limpiadora.id)
    notificar(
        db, tokens,
        titulo=f"Hab. {inc.habitacion} — Tarea asignada",
        cuerpo=f"{current_user.nombre} te asignó: {inc.descripcion or 'revisar la habitación'}",
        data={"link": "/", "incidencia_id": str(inc.id)},
    )

    return payload


@router.delete("/{iid}")
def eliminar(
    iid: int,
    db: Session = Depends(get_db),
    _=Depends(require_rol(RolEnum.admin)),
):
    inc = db.query(Incidencia).filter(Incidencia.id == iid).first()
    if not inc:
        raise HTTPException(status_code=404, detail="No encontrada")
    db.delete(inc)
    db.commit()
    return {"ok": True}


# ── Comentarios internos (mantenimiento / gobernanta / admin / limpiadora asignada) ─

class ComentarioCreate(BaseModel):
    texto: str


@router.post("/{iid}/comentarios")
async def crear_comentario(
    iid: int,
    data: ComentarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    inc = db.query(Incidencia).filter(Incidencia.id == iid).first()
    if not inc:
        raise HTTPException(status_code=404, detail="No encontrada")
    if not puede_comentar(current_user, inc):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta petición")
    if not data.texto.strip():
        raise HTTPException(status_code=400, detail="El comentario no puede estar vacío")

    comentario = ComentarioInterno(
        incidencia_id=iid,
        usuario_id=current_user.id,
        texto=data.texto.strip(),
    )
    db.add(comentario)
    db.commit()
    db.refresh(inc)

    payload = inc_dict(inc, current_user)
    await manager.broadcast({"evento": "nuevo_comentario", "incidencia": payload})

    notificar_relevantes(
        db, inc,
        titulo=f"Hab. {inc.habitacion} — Nuevo mensaje",
        cuerpo=f"{current_user.nombre}: {data.texto.strip()[:80]}",
        excluir_id=current_user.id,
    )

    return payload
