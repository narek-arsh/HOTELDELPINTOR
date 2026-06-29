from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class RolEnum(str, enum.Enum):
    limpiadora = "limpiadora"
    mantenimiento = "mantenimiento"
    admin = "admin"


class EstadoEnum(str, enum.Enum):
    recibido = "recibido"
    en_curso = "en_curso"
    esperando_material = "esperando_material"
    resuelto = "resuelto"
    archivado = "archivado"


class PrioridadEnum(str, enum.Enum):
    urgente = "urgente"
    normal = "normal"
    baja = "baja"


class TipoEnum(str, enum.Enum):
    bombilla = "bombilla"
    puerta = "puerta"
    fontaneria = "fontaneria"
    calefaccion = "calefaccion"
    mueble = "mueble"
    otro = "otro"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(SAEnum(RolEnum), nullable=False)
    edificio = Column(String(100), nullable=True)   # solo limpiadoras
    planta = Column(String(50), nullable=True)       # solo limpiadoras
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    incidencias = relationship("Incidencia", back_populates="reporter", foreign_keys="Incidencia.reporter_id")
    cambios_estado = relationship("CambioEstado", back_populates="usuario")
    


class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True)  # INC-2026-001
    habitacion = Column(String(20), nullable=False)
    edificio = Column(String(100), nullable=True)
    tipo = Column(SAEnum(TipoEnum), nullable=False)
    descripcion = Column(Text, nullable=True)       # obligatorio si tipo=otro
    prioridad = Column(SAEnum(PrioridadEnum), default=PrioridadEnum.normal)
    estado = Column(SAEnum(EstadoEnum), default=EstadoEnum.recibido)
    notas_mantenimiento = Column(Text, nullable=True)

    reporter_id = Column(Integer, ForeignKey("usuarios.id"))
    asignado_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resuelto_en = Column(DateTime, nullable=True)

    reporter = relationship("Usuario", back_populates="incidencias", foreign_keys=[reporter_id])
    asignado = relationship("Usuario", foreign_keys=[asignado_id])
    cambios = relationship("CambioEstado", back_populates="incidencia", order_by="CambioEstado.fecha")


class CambioEstado(Base):
    __tablename__ = "cambios_estado"

    id = Column(Integer, primary_key=True, index=True)
    incidencia_id = Column(Integer, ForeignKey("incidencias.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    estado_anterior = Column(SAEnum(EstadoEnum), nullable=True)
    estado_nuevo = Column(SAEnum(EstadoEnum), nullable=False)
    nota = Column(Text, nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)

    incidencia = relationship("Incidencia", back_populates="cambios")
    usuario = relationship("Usuario", back_populates="cambios_estado")


class FotoIncidencia(Base):
    __tablename__ = "fotos_incidencia"

    id = Column(Integer, primary_key=True, index=True)
    incidencia_id = Column(Integer, ForeignKey("incidencias.id"))
    url = Column(String(500), nullable=False)
    subida_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creada_en = Column(DateTime, default=datetime.utcnow)

    incidencia = relationship("Incidencia", backref="fotos")
    subida_por = relationship("Usuario", foreign_keys=[subida_por_id])
