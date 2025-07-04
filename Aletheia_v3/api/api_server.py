# Aletheia_v3/api/api_server.py
import logging  # Import logging module
import os  # For LOG_LEVEL env var

from fastapi import FastAPI

# Import common authentication components
from aletheia_common.auth.jwt_handler import get_user_retriever_dependency_placeholder

# Import la implementación del user_retriever de Aletheia_v3
from .auth import get_user_retriever as get_aletheia_v3_user_retriever

# --- Basic Logging Configuration ---
# Configure logging at the beginning of the application module.
# This ensures that loggers used in this module and submodules (if they don't define their own handlers)
# will output messages. Uvicorn's logging can also be configured separately.
LOG_LEVEL = os.getenv("ALETHEIA_V3_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s",
    handlers=[logging.StreamHandler()],
)
# --- Application Setup ---
# Metadata for API documentation
API_VERSION = "3.0.0-MDU"
API_TITLE = "Aletheia AI-Guided Scientific Discovery Platform"
API_DESCRIPTION = """
Aletheia v3.0 (MDU Edition) for AI-guided research into the ABC Conjecture.
Features include JWT authentication, MLflow experiment tracking, and a robust testing suite.
"""

# Main FastAPI application instance
# It's good practice to initialize the app and then include routers.
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    # docs_url="/docs", # Default
    # redoc_url="/redoc", # Default
    # openapi_url="/openapi.json" # Default
)

# Override the placeholder dependency in aletheia_common with the actual implementation from Aletheia_v3
app.dependency_overrides[get_user_retriever_dependency_placeholder] = (
    get_aletheia_v3_user_retriever
)


# Import routers
from .routers import (
    attribution_router,
    auth_router,
    conjecture_router,
    meta_router,
    researcher_router,
    search_router,
)

# Get a logger instance for this module
logger = logging.getLogger(__name__)


# --- Event Handlers ---
@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    """
    logger.info("Aletheia_v3 FastAPI application startup...")
    try:
        # initialize_database() # Commented out: Alembic will now handle table creation and migrations.
        logger.info("Database auto-creation (create_all) is DISABLED.")
        logger.info(
            "Ensure Alembic migrations are run to set up the database schema."
        )
    except Exception as e:
        logger.exception(
            "Error during other startup tasks (if any)."
        )  # Use logger.exception to include traceback


@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform on application shutdown.
    """
    logger.info("Aletheia_v3 FastAPI application shutdown...")
    # Cleanup tasks can go here.


# Include all the routers.
# Note: The prefix for some routers (like /researchers) is defined within the router itself.
# Others (like /searches, /token) are defined at the root level.
app.include_router(auth_router.router)  # Includes /token, /users/me
app.include_router(
    search_router.router
)  # Includes /searches, /searches/{job_id}
app.include_router(researcher_router.router)  # Includes /researchers/*
app.include_router(conjecture_router.router)  # Includes /conjectures/*
app.include_router(
    attribution_router.router
)  # Includes /hits/{hit_id}/attributions/*
app.include_router(meta_router.router)  # Includes /health


# --- Main guard for running with Uvicorn (optional, for direct execution) ---
if __name__ == "__main__":
    # This allows running the app directly with `python api_server.py`
    # Uvicorn is the ASGI server.
    # Host 0.0.0.0 makes it accessible externally (e.g., from Docker).
    # Reload=True is useful for development, automatically reloads on code changes.
    import uvicorn

    # Configure basic logging for direct Uvicorn run if not already configured by FastAPI/Uvicorn
    # This is more for when running `python Aletheia_v3/api/api_server.py` directly.
    # Uvicorn itself has logging, and FastAPI might add handlers.
    # Ensure a basic config if no other logging is set up by this point for the __main__ block.
    if (
        not logging.getLogger().hasHandlers()
    ):  # Check if root logger has handlers
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    logger.info(
        "Starting Uvicorn server directly for development via __main__..."
    )
    uvicorn.run(
        "Aletheia_v3.api.api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
    # In docker-compose, uvicorn is typically started like:
    # uvicorn Aletheia_v3.api.api_server:app --host 0.0.0.0 --port 8000 --log-config uvicorn_log_config.yml
    # Note the module path `Aletheia_v3.api.api_server:app` when run from project root.
    # The `if __name__ == "__main__":` block uses `api_server:app` because it's run from within the `api` dir.
    # For consistency with Docker, it's better to rely on the docker-compose command.
    # This block is more for local, non-Dockerized testing of this specific file.
    # To run from project root: `python -m Aletheia_v3.api.api_server`
    # Then uvicorn.run("Aletheia_v3.api.api_server:app"...) would be needed.
    # For simplicity and standard Docker execution, this direct run method is secondary.
    # The primary way to run is `docker-compose up`.

    # To make `python Aletheia_v3/api/api_server.py` work from the project root,
    # you might need to adjust PYTHONPATH or use `uvicorn Aletheia_v3.api.api_server:app ...` directly.
    # The current uvicorn.run("api_server:app"...) assumes you `cd Aletheia_v3/api` then `python api_server.py`.

    # Corrected uvicorn run command for direct execution from project root,
    # assuming PYTHONPATH includes the project root.
    # uvicorn.run("Aletheia_v3.api.api_server:app", host="0.0.0.0", port=8000, reload=True)
    # For this to work, ensure Aletheia_v3's parent directory is in PYTHONPATH or run as module:
    # `python -m Aletheia_v3.api.api_server`
    # If running as a script from Aletheia_v3/api/: uvicorn api_server:app ...
    # The provided docker-compose.yml will handle the correct invocation path for uvicorn.
