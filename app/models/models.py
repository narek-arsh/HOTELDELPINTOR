from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class RolEnum(str, enum.Enum):
    limpiadora = "limpiadora"
    mantenimiento = "mantenimiento"
    gobernanta = "gobernanta"
    admin = "admin"


class EstadoEnum(str, enum.Enum):
    recibido = "recibido"
    en_curso = "en_curso"
    esperando_material = "esperando_material"
    resuelto = "resuelto"


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
    nombre = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(SAEnum(RolEnum), nullable=False)
    planta = Column(String(50), nullable=True)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    incidencias = relationship("Incidencia", back_populates="reporter", foreign_keys="Incidencia.reporter_id")
    cambios_estado = relationship("CambioEstado", back_populates="usuario")


class Habitacion(Base):
    __tablename__ = "habitaciones"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(20), unique=True, index=True, nullable=False)
    activa = Column(Boolean, default=True)
    orden = Column(Integer, default=0)
    creado_en = Column(DateTime, default=datetime.utcnow)


class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True)  # INC-2026-001
    habitacion = Column(String(20), nullable=False)
    tipo = Column(SAEnum(TipoEnum), nullable=False)
    descripcion = Column(Text, nullable=True)       # obligatorio si tipo=otro
    prioridad = Column(SAEnum(PrioridadEnum), default=PrioridadEnum.normal)
    estado = Column(SAEnum(EstadoEnum), default=EstadoEnum.recibido)

    notas = Column(Text, nullable=True)                  # nota original de quien reporta, fija
    notas_mantenimiento = Column(Text, nullable=True)     # nota de mantenimiento, editable
    notas_mantenimiento_autor_rol = Column(String(20), nullable=True)  # 'mantenimiento' o 'admin'

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


class ComentarioInterno(Base):
    """Hilo de comentarios privado entre mantenimiento y admin, no visible para quien reporta."""
    __tablename__ = "comentarios_internos"

    id = Column(Integer, primary_key=True, index=True)
    incidencia_id = Column(Integer, ForeignKey("incidencias.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    texto = Column(Text, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)

    incidencia = relationship("Incidencia", backref="comentarios_internos")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])


class DeviceToken(Base):
    """Token FCM de un dispositivo/navegador para enviarle notificaciones push."""
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    token = Column(String(500), unique=True, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", foreign_keys=[usuario_id])
