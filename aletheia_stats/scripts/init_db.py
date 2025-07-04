import logging
import os

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

# Import Base from the repository where your models are defined
# Adjust this import path according to your project structure.
# This assumes your models (like ExperimentDB) are defined in sqlalchemy_repository.py
# and Base is also defined there.
from aletheia_stats.infrastructure.sqlalchemy_repository import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Construct the path to alembic.ini relative to this script's location
# This script is in aletheia_stats/scripts/
# alembic.ini will be in aletheia_stats/alembic.ini
MODULE_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALEMBIC_INI_PATH = os.path.join(MODULE_ROOT_DIR, "alembic.ini")


def apply_migrations():
    """Applies Alembic migrations to upgrade the database to the latest version."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error(
            "DATABASE_URL environment variable not set. Cannot apply migrations."
        )
        raise ValueError("DATABASE_URL not set.")

    logger.info(
        f"DATABASE_URL found: {db_url.split('@')[-1] if '@' in db_url else db_url}"
    )
    logger.info(f"Using Alembic config file: {ALEMBIC_INI_PATH}")

    if not os.path.exists(ALEMBIC_INI_PATH):
        logger.error(f"Alembic config file not found at {ALEMBIC_INI_PATH}")
        raise FileNotFoundError(
            f"Alembic config file not found: {ALEMBIC_INI_PATH}"
        )

    alembic_cfg = Config(ALEMBIC_INI_PATH)

    # Programmatically set the sqlalchemy.url in alembic.ini if not already set via env var
    # or if you want to ensure this script uses the DATABASE_URL from the env.
    # This overrides the sqlalchemy.url in alembic.ini.
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    logger.info("Applying Alembic migrations to head...")
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied successfully to head.")
    except Exception as e:
        logger.error(f"Error applying Alembic migrations: {e}", exc_info=True)
        raise


def create_tables_direct(db_url: Optional[str] = None):
    """
    Creates all tables directly using SQLAlchemy Base.metadata.create_all().
    Useful for testing or simple setups without Alembic.
    WARNING: This bypasses Alembic migrations and should not be used in production
             if Alembic is the primary way of managing schema.
    """
    if not db_url:
        db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error(
            "DATABASE_URL environment variable not set. Cannot create tables."
        )
        raise ValueError("DATABASE_URL not set for create_tables_direct.")

    logger.info(
        f"Directly creating tables for database: {db_url.split('@')[-1] if '@' in db_url else db_url}"
    )
    try:
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        logger.info("Tables created successfully (if they didn't exist).")
    except Exception as e:
        logger.error(f"Error creating tables directly: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Default action is to apply migrations.
    # You could add command-line arguments to choose action, e.g.,
    # `python init_db.py migrate` or `python init_db.py create_direct`

    ACTION = os.getenv(
        "DB_INIT_ACTION", "migrate"
    ).lower()  # Default to migrate

    logger.info(f"Database initialization script started. Action: {ACTION}")

    try:
        if ACTION == "migrate":
            apply_migrations()
        elif ACTION == "create_direct":
            logger.warning(
                "Executing direct table creation. This bypasses Alembic migrations."
            )
            create_tables_direct()
        else:
            logger.error(
                f"Unknown DB_INIT_ACTION: {ACTION}. Supported actions: 'migrate', 'create_direct'."
            )
            exit(1)

        logger.info("Database initialization process completed.")

    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        exit(1)
