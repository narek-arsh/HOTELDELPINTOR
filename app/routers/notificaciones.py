from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.models import DeviceToken, Usuario
from app.auth import get_current_user

router = APIRouter(prefix="/api/notificaciones", tags=["notificaciones"])


class TokenRegistro(BaseModel):
    token: str


@router.post("/registrar-token")
def registrar_token(
    data: TokenRegistro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    existente = db.query(DeviceToken).filter(DeviceToken.token == data.token).first()
    if existente:
        existente.usuario_id = current_user.id
        db.commit()
        return {"ok": True}

    dt = DeviceToken(usuario_id=current_user.id, token=data.token)
    db.add(dt)
    db.commit()
    return {"ok": True}


@router.delete("/registrar-token")
def eliminar_token(
    data: TokenRegistro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    db.query(DeviceToken).filter(DeviceToken.token == data.token).delete()
    db.commit()
    return {"ok": True}
