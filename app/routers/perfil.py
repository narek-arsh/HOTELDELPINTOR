from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.models import Usuario
from app.auth import get_current_user, verify_password, hash_password

router = APIRouter(prefix="/api/perfil", tags=["perfil"])

class CambioPassword(BaseModel):
    password_actual: str
    password_nuevo: str

@router.post("/cambiar-password")
def cambiar_password(
    data: CambioPassword,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if not verify_password(data.password_actual, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    if len(data.password_nuevo) < 6:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 6 caracteres")
    current_user.password_hash = hash_password(data.password_nuevo)
    db.commit()
    return {"ok": True}
