from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Incidencia, FotoIncidencia, Usuario, RolEnum
from app.auth import get_current_user, require_rol
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os

router = APIRouter(prefix="/api/fotos", tags=["fotos"])

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", "ddamj384r"),
    api_key=os.environ.get("CLOUDINARY_API_KEY", "151665652414153"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", "j1AEOuDOoLSmVi-mcP6lbwHRVPc"),
)


@router.post("/{incidencia_id}")
async def subir_foto(
    incidencia_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    inc = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    count = db.query(FotoIncidencia).filter(
        FotoIncidencia.incidencia_id == incidencia_id
    ).count()
    if count >= 3:
        raise HTTPException(status_code=400, detail="Máximo 3 fotos por incidencia")

    if not file.content_type.startswith("image/"):
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
        subida_por_id=current_user.id,
    )
    db.add(foto)
    db.commit()
    db.refresh(foto)
    return {"id": foto.id, "url": foto.url}


@router.get("/{incidencia_id}")
def listar_fotos(
    incidencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    fotos = db.query(FotoIncidencia).filter(
        FotoIncidencia.incidencia_id == incidencia_id
    ).all()
    return [{"id": f.id, "url": f.url} for f in fotos]


@router.delete("/{foto_id}")
def borrar_foto(
    foto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    foto = db.query(FotoIncidencia).filter(FotoIncidencia.id == foto_id).first()
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    db.delete(foto)
    db.commit()
    return {"ok": True}


@router.get("/sistema/uso-almacenamiento")
def uso_almacenamiento(
    _=Depends(require_rol(RolEnum.admin)),
):
    """Devuelve el consumo actual de la cuenta Cloudinary (plan gratuito: 25GB)."""
    try:
        usage = cloudinary.api.usage()
        storage_bytes = usage.get("storage", {}).get("usage", 0)
        storage_limit = usage.get("storage", {}).get("limit", 25 * 1024 * 1024 * 1024)
        credits_used = usage.get("credits", {}).get("usage", 0)
        credits_limit = usage.get("credits", {}).get("limit", 25)

        porcentaje = round((storage_bytes / storage_limit) * 100, 1) if storage_limit else 0

        return {
            "almacenamiento_usado_mb": round(storage_bytes / (1024 * 1024), 1),
            "almacenamiento_limite_mb": round(storage_limit / (1024 * 1024), 1),
            "porcentaje_usado": porcentaje,
            "creditos_usados": credits_used,
            "creditos_limite": credits_limit,
            "alerta": porcentaje >= 80,
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"No se pudo consultar Cloudinary: {str(e)}")
