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
    ya existen en la base real. Si el modelo gana una columna nueva (como
    pasó con Habitacion.token, o con Incidencia.origen/tipo_solicitud/
    nombre_huesped al añadir el flujo de huéspedes) y la tabla ya existía
    en Postgres, cualquier INSERT que use esa columna falla con
    'column ... does not exist'.

    Este parche revisa, en cada arranque, si faltan columnas del modelo en
    la tabla real y las añade con ALTER TABLE. Para columnas de tipo Enum
    (como origen/tipo_solicitud), Postgres exige que el TYPE exista antes
    de poder usarlo en una columna, así que se crea primero con
    CREATE TYPE si no existe.

    No borra ni modifica filas existentes. Es un parche mínimo mientras
    no se use Alembic.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue  # tabla nueva -> create_all() ya la crea completa
            existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
            for col in table.columns:
                if col.name in existing_cols:
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
