from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models.models import Base
from app.routers import auth, incidencias, admin, websocket
from app.auth import hash_password
from app.database import SessionLocal
from app.models.models import Usuario, RolEnum
from dotenv import load_dotenv

load_dotenv()

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hotel del Pintor — Mantenimiento API", version="1.0.0")

# CORS — permite PWA desde cualquier origen (ajustar en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(incidencias.router)
app.include_router(admin.router)
app.include_router(websocket.router)


@app.on_event("startup")
def crear_admin_inicial():
    """Crea el admin por defecto si no existe ningún usuario."""
    db = SessionLocal()
    try:
        existe = db.query(Usuario).filter(Usuario.rol == RolEnum.admin).first()
        if not existe:
            admin_user = Usuario(
                nombre="Administrador",
                email="admin@hotelpintor.com",
                password_hash=hash_password("Admin24!"),
                rol=RolEnum.admin,
                activo=True,
            )
            db.add(admin_user)
            db.commit()
            print("✅ Admin inicial creado: admin@hotelpintor.com / admin1234")
    finally:
        db.close()


@app.get("/")
def root():
    return {"status": "ok", "app": "Hotel del Pintor — Mantenimiento"}
