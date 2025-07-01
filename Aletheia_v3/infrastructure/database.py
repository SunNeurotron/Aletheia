import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Environment variables for database connection parameters
# Default values are provided for local development with Docker Compose.
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_NAME = os.getenv("POSTGRES_DB", "abc_db") # This will also be used by MLflow
DB_HOST = os.getenv("DB_HOST", "db") # Service name in docker-compose.yml
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy engine
# `echo=True` can be useful for debugging SQL queries during development
engine = create_engine(DATABASE_URL) # Add echo=True for query logging if needed

# SessionLocal class for creating database sessions
# autocommit=False and autoflush=False are standard settings for FastAPI/Celery integration
# where commit and flush operations are handled explicitly.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
# All SQLAlchemy models will inherit from this class.
Base = declarative_base()

def get_db_session():
    """
    Dependency provider for FastAPI to get a database session.
    It ensures the session is closed after the request is finished.
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
    Base.metadata.create_all(bind=engine) # Creates tables based on SQLAlchemy models
    print("Database tables created/verified by SQLAlchemy (if they didn't exist).")
    print("Note: Advanced optimizations like table partitioning defined in")
    print("'infrastructure/db_optimizations.sql' need to be applied manually by a DBA")
    print("or through a database migration tool like Alembic for production environments.")

# If you need to run init_db from a script or command line:
if __name__ == "__main__":
    print(f"Attempting to initialize database at {DATABASE_URL}...")
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
        time.sleep(5) # Basic retry delay
        try:
            print("Retrying database initialization...")
            init_db()
            print("Database initialization successful on retry.")
        except Exception as e_retry:
            print(f"Error during database initialization on retry: {e_retry}")
            print("Please ensure the PostgreSQL database is running and accessible.")
