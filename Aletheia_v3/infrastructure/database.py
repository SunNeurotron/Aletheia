# Copyright 2025 Alant
#
# Licensed under the Aletheia Unificada Ethical Public License (AUEPL);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Database configuration and session management for the Aletheia_v3 module.

This module sets up the SQLAlchemy engine, session factory (`SessionLocal`),
and the declarative base (`Base`) for ORM models. It also provides a
FastAPI dependency (`get_db_session`) for injecting database sessions into
API route handlers.

The database connection URL is configured via the
`ALETHEIA_V3_DATABASE_URL` environment variable.
"""

import logging  # Añadir logging
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Environment variable for the full database URL
ALETHEIA_V3_DATABASE_URL_ENV_VAR = "ALETHEIA_V3_DATABASE_URL"
"""Environment variable name for the Aletheia_v3 module's database URL."""

DEFAULT_ALETHEIA_V3_DATABASE_URL = "postgresql://user:password@db:5432/abc_db"
"""Default database URL, typically used in docker-compose setups if the env var is not set."""

SQLALCHEMY_DATABASE_URL: str = os.getenv(
    ALETHEIA_V3_DATABASE_URL_ENV_VAR, DEFAULT_ALETHEIA_V3_DATABASE_URL
)
"""The actual database URL being used, loaded from environment or default."""

if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    # Ensure compatibility with SQLAlchemy versions that prefer 'postgresql://'
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgres://", "postgresql://", 1
    )

# Log the database URL being used (excluding credentials for security)
db_url_log_display = SQLALCHEMY_DATABASE_URL
if "@" in db_url_log_display:
    db_url_log_display = db_url_log_display.split("@", 1)[1] # Show only host/db part
logger.info(
    f"Aletheia_v3 Infrastructure: Using database at host/db: {db_url_log_display}"
)

engine = None
try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    """The SQLAlchemy engine instance, connected to the database specified by `SQLALCHEMY_DATABASE_URL`."""
except Exception as e:
    logger.critical(
        f"Failed to create SQLAlchemy engine for Aletheia_v3 with URL {db_url_log_display}: {e}",
        exc_info=True,
    )
    # engine remains None, allowing app to start but DB operations will fail.
    # Health checks or startup routines should verify engine availability.

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""A factory for creating new SQLAlchemy `Session` objects.
Configured with autocommit=False and autoflush=False, suitable for FastAPI
dependencies where session lifecycle is managed per request.
"""

Base = declarative_base()
"""Base class for all SQLAlchemy ORM models in the Aletheia_v3 module.
Models should inherit from this `Base` to be registered with SQLAlchemy's metadata.
"""


def get_db_session():
    """
    FastAPI dependency to provide a SQLAlchemy database session per request.

    This function yields a new database session from `SessionLocal` and ensures
    that the session is closed after the request processing is complete,
    regardless of whether an exception occurred.

    Usage:
        @app.get("/items/")
        async def read_items(db: Session = Depends(get_db_session)):
            # ... use db session ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initializes the database by creating all tables defined in the models.
    This is typically called once at application startup (e.g., in entrypoint.sh or main API module).
    """
    # Import all modules that define models here before calling Base.metadata.create_all
    # This ensures that models are registered with SQLAlchemy's metadata.
    # For example: from . import models
    # However, to avoid circular imports if models.py imports Base from here,
    # it's often better to ensure models are imported where init_db is called.
    # For this project structure, models.py will import Base from here.
    # Import all models from .models to ensure they are registered with Base.metadata
    from . import models

    Base.metadata.create_all(
        bind=engine
    )  # Creates tables based on SQLAlchemy models
    print(
        "Database tables created/verified by SQLAlchemy (if they didn't exist)."
    )
    print("Note: Advanced optimizations like table partitioning defined in")
    print(
        "'infrastructure/db_optimizations.sql' need to be applied manually by a DBA"
    )
    print(
        "or through a database migration tool like Alembic for production environments."
    )


# If you need to run init_db from a script or command line:
if __name__ == "__main__":
    print(f"Attempting to initialize database at {SQLALCHEMY_DATABASE_URL}...")
    # In a real app, you might want more robust error handling here
    # or use a migration tool like Alembic.
    try:
        init_db()
        print("Database initialization successful (tables checked/created).")
    except Exception as e:
        print(f"Error during database initialization: {e}")
        # You might want to retry or log this more formally.
        # For Dockerized environments, the entrypoint script often handles waiting for DB.
        import time

        time.sleep(5)  # Basic retry delay
        try:
            print("Retrying database initialization...")
            init_db()
            print("Database initialization successful on retry.")
        except Exception as e_retry:
            print(f"Error during database initialization on retry: {e_retry}")
            print(
                "Please ensure the PostgreSQL database is running and accessible."
            )
