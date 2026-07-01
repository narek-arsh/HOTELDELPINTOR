from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.sqltypes import Enum as SAEnumType
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "").replace(
    "postgresql://", "postgresql+pg8000://"
)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definida")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sync_missing_columns():
    """
    create_all() solo crea tablas nuevas: nunca añade columnas a tablas que
    ya existen en la base real, ni corrige restricciones antiguas. Esto causa
    dos problemas típicos cuando el modelo evoluciona:

    1. Columna nueva que no existe en la tabla real (ej. Habitacion.token,
       Incidencia.tipo_solicitud) -> 'column ... does not exist'.
    2. Columna que ya existía como NOT NULL desde el principio, pero el
       modelo ahora la marca como opcional (ej. Incidencia.tipo, que ahora
       puede ser null para peticiones de limpieza) -> 'null value ... violates
       not-null constraint'.

    Este parche corrige ambos casos en cada arranque. Para columnas Enum
    nuevas, Postgres exige que el TYPE exista antes de poder usarlo, así que
    se crea primero con CREATE TYPE si no existe.

    No borra ni modifica datos existentes. Es un parche mínimo mientras no
    se use Alembic.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue  # tabla nueva -> create_all() ya la crea completa
            existing_cols_info = {c["name"]: c for c in inspector.get_columns(table.name)}
            for col in table.columns:
                if col.name in existing_cols_info:
                    # La columna ya existe: si el modelo la marca como opcional
                    # pero la tabla real la exige NOT NULL (constraint antigua
                    # de cuando se creó la tabla), lo corregimos para que
                    # coincida con el modelo.
                    info = existing_cols_info[col.name]
                    if col.nullable and not info["nullable"]:
                        try:
                            conn.execute(text(
                                f'ALTER TABLE "{table.name}" ALTER COLUMN "{col.name}" DROP NOT NULL'
                            ))
                            print(f"[sync_missing_columns] Quitado NOT NULL de {table.name}.{col.name}")
                        except Exception as e:
                            print(f"[sync_missing_columns] No se pudo quitar NOT NULL de {table.name}.{col.name}: {e}")
                    continue

                # Si la columna es un Enum de Postgres, el TYPE debe existir
                # antes de poder usarlo en ADD COLUMN.
                if isinstance(col.type, SAEnumType):
                    try:
                        col.type.create(bind=conn, checkfirst=True)
                    except Exception as e:
                        print(f"[sync_missing_columns] No se pudo crear el tipo enum para {table.name}.{col.name}: {e}")

                col_type = col.type.compile(dialect=engine.dialect)
                stmt = f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col_type}'
                try:
                    conn.execute(text(stmt))
                    print(f"[sync_missing_columns] Añadida columna {table.name}.{col.name}")
                except Exception as e:
                    print(f"[sync_missing_columns] No se pudo añadir {table.name}.{col.name}: {e}")
                    continue

                if col.unique:
                    idx_name = f"ix_{table.name}_{col.name}"
                    try:
                        conn.execute(text(
                            f'CREATE UNIQUE INDEX IF NOT EXISTS "{idx_name}" ON "{table.name}" ("{col.name}")'
                        ))
                    except Exception as e:
                        print(f"[sync_missing_columns] No se pudo indexar {table.name}.{col.name}: {e}")


def sync_missing_enum_values():
    """
    Cuando un Enum de Python (p.ej. EstadoEnum) gana un valor nuevo (como
    'asignado'), el TYPE que ya existe en Postgres no lo tiene automáticamente
    — ni create_all() ni sync_missing_columns() tocan los valores de un enum
    ya creado. Hay que añadirlo explícitamente con ALTER TYPE ... ADD VALUE.

    Esto tiene que ejecutarse fuera de una transacción normal (Postgres no
    permite ALTER TYPE ADD VALUE dentro de la misma transacción en la que
    luego se usa), así que se usa una conexión en autocommit.
    """
    vistos = set()
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for table in Base.metadata.sorted_tables:
            for col in table.columns:
                if not isinstance(col.type, SAEnumType) or not getattr(col.type, "enum_class", None):
                    continue
                type_name = col.type.name
                if not type_name or type_name in vistos:
                    continue
                vistos.add(type_name)
                try:
                    filas = conn.execute(text(
                        "SELECT enumlabel FROM pg_enum WHERE enumtypid = "
                        "(SELECT oid FROM pg_type WHERE typname = :t)"
                    ), {"t": type_name}).fetchall()
                    existentes = {f[0] for f in filas}
                except Exception as e:
                    print(f"[sync_missing_enum_values] No se pudo leer el tipo {type_name}: {e}")
                    continue
                if not existentes:
                    continue  # el tipo aún no existe -> ya lo crea create_all()/sync_missing_columns()
                for miembro in col.type.enum_class:
                    valor = miembro.value
                    if valor in existentes:
                        continue
                    try:
                        conn.execute(text(f"ALTER TYPE \"{type_name}\" ADD VALUE IF NOT EXISTS '{valor}'"))
                        print(f"[sync_missing_enum_values] Añadido valor '{valor}' a {type_name}")
                        existentes.add(valor)
                    except Exception as e:
                        print(f"[sync_missing_enum_values] No se pudo añadir '{valor}' a {type_name}: {e}")
