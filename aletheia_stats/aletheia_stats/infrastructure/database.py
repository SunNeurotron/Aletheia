import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL_ENV = "STATS_DATABASE_URL"  # Usar una variable de entorno específica para el módulo stats
DEFAULT_DATABASE_URL = "postgresql://user:pass@localhost:5433/aletheia_stats_db_main_py"  # Default si no se setea

SQLALCHEMY_DATABASE_URL = os.getenv(DATABASE_URL_ENV, DEFAULT_DATABASE_URL)

if SQLALCHEMY_DATABASE_URL.startswith(
    "postgres://"
):  # SQLAlchemy <1.4 compatibilidad con psycopg2
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgres://", "postgresql://", 1
    )

logger.info(
    f"Aletheia-Stats Infrastructure: Using database URL: {SQLALCHEMY_DATABASE_URL[:SQLALCHEMY_DATABASE_URL.find('@') if '@' in SQLALCHEMY_DATABASE_URL else len(SQLALCHEMY_DATABASE_URL)]}..."
)  # Log sin creds

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Verifica conexiones antes de usarlas
        # connect_args={"check_same_thread": False} # Solo para SQLite
    )
except Exception as e:
    logger.critical(
        f"Failed to create SQLAlchemy engine for Aletheia-Stats: {e}",
        exc_info=True,
    )
    # Podríamos querer que la aplicación falle al inicio si el engine no se puede crear.
    # Por ahora, solo logueamos. La creación del repo fallará después.
    engine = None


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Función para obtener una sesión de BD, similar a Aletheia_v3
def get_db_session_stats():
    if engine is None:
        logger.error(
            "Database engine for Aletheia-Stats is not initialized. Cannot create session."
        )
        raise ConnectionError(
            "Aletheia-Stats database engine not initialized."
        )

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TODO: Aquí se podrían añadir funciones para inicializar la BD (Alembic)
# def init_db():
#     Base.metadata.create_all(bind=engine) # Para crear tablas si no existen (NO USAR CON ALEMBIC EN PRODUCCIÓN)

logger.info("Aletheia-Stats Database infrastructure module loaded.")
