from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt
from app.websocket_manager import manager
from app.database import SessionLocal
from app.models.models import Usuario, RolEnum
import os

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    # Validar token antes de aceptar conexión
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        rol = payload.get("rol")
    except (JWTError, TypeError, ValueError):
        await websocket.close(code=4001)
        return

    # Solo mantenimiento y admin reciben el feed en tiempo real
    if rol not in [RolEnum.mantenimiento, RolEnum.admin]:
        await websocket.close(code=4003)
        return

    await manager.connect(websocket)
    try:
        while True:
            # Mantener conexión viva esperando pings del cliente
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
