from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine
from app.models.models import Base
from app.routers import auth, incidencias, admin, websocket, fotos, perfil, notificaciones
from app.auth import hash_password
from app.database import SessionLocal
from app.models.models import Usuario, RolEnum
from app.notifications import init_firebase
from dotenv import load_dotenv
import os

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hotel del Pintor", version="2.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(incidencias.router)
app.include_router(admin.router)
app.include_router(websocket.router)
app.include_router(fotos.router)
app.include_router(perfil.router)
app.include_router(notificaciones.router)

PWA_DIR = os.path.join(os.path.dirname(__file__), "pwa")
if os.path.exists(PWA_DIR):
    app.mount("/static", StaticFiles(directory=PWA_DIR), name="static")

    @app.get("/manifest.json")
    def manifest(): return FileResponse(os.path.join(PWA_DIR, "manifest.json"))

    @app.get("/sw.js")
    def sw(): return FileResponse(os.path.join(PWA_DIR, "sw.js"))

    @app.get("/firebase-messaging-sw.js")
    def fcm_sw(): return FileResponse(os.path.join(PWA_DIR, "firebase-messaging-sw.js"))

    @app.get("/icon-192.png")
    def icon192(): return FileResponse(os.path.join(PWA_DIR, "icon-192.png"))

    @app.get("/icon-512.png")
    def icon512(): return FileResponse(os.path.join(PWA_DIR, "icon-512.png"))

    @app.get("/logo-login.png")
    def logo_login(): return FileResponse(os.path.join(PWA_DIR, "logo-login.png"))

    @app.get("/")
    def pwa(): return FileResponse(os.path.join(PWA_DIR, "index.html"))
else:
    @app.get("/")
    def root(): return {"status": "ok", "app": "Hotel del Pintor v2"}


@app.on_event("startup")
def init_db():
    init_firebase()
    db = SessionLocal()
    try:
        existe = db.query(Usuario).filter(Usuario.rol == RolEnum.admin).first()
        if not existe:
            db.add(Usuario(
                nombre="Administrador",
                username="admin",
                password_hash=hash_password("Admin2024"),
                rol=RolEnum.admin,
                activo=True,
            ))
            db.commit()
            print("Admin creado: admin / Admin2024")
    finally:
        db.close()
