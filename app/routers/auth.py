from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pydantic import BaseModel
from app.database import get_db
from app.models.models import Usuario
from app.auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: dict


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    identificador = form_data.username.strip().lower()

    user = db.query(Usuario).filter(
        or_(
            func.lower(Usuario.username) == identificador,
            func.lower(Usuario.email) == identificador,
        ),
        Usuario.activo == True
    ).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    token = create_access_token({"sub": str(user.id), "rol": user.rol})

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": user.id,
            "nombre": user.nombre,
            "username": user.username,
            "rol": user.rol,
            "edificio": user.edificio,
            "planta": user.planta,
        },
    }


@router.get("/me")
def me(current_user: Usuario = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "nombre": current_user.nombre,
        "username": current_user.username,
        "email": current_user.email,
        "rol": current_user.rol,
        "edificio": current_user.edificio,
        "planta": current_user.planta,
    }
