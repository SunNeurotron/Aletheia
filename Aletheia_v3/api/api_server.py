# Copyright 2025 Alant
#
# Licensed under the Apache License, Version 2.0 (the "License");
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
Main FastAPI application server for Aletheia v3.

This module initializes the FastAPI application, sets up logging,
configures global metadata for the API documentation, includes all the
API routers from the `routers` submodule, and defines application
startup and shutdown event handlers.
"""

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
API_VERSION = "4.0.0"
API_TITLE = "Aletheia AI-Guided Scientific Discovery Platform"
API_DESCRIPTION = """
Aletheia v4.0 for AI-guided research into the ABC Conjecture.
This version includes a PARI/GP mathematical core, a plugin architecture, advanced scalability configurations (Kubernetes),
and collaborative features with role-based access control.
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


# Import routers from the new modular structure
from .routers import (
    attribution_router,
    auth_router,
    conjecture_router,
    meta_router,
    researcher_router,
    search_router,
    # Nuevos routers para Eje X y Eje Y
    ontology_management_router,
    knowledge_synthesis_router,
)

# Get a logger instance for this module
logger = logging.getLogger(__name__)


# --- Event Handlers ---
@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    """
    logger.info(f"Aletheia API v{API_VERSION} starting up...")
    try:
        # Alembic now handles all DB schema management via docker-compose.
        # No need for `init_db()` or `Base.metadata.create_all()` here.
        logger.info(
            "Database initialization via `create_all()` is DISABLED. "
            "Alembic migrations are expected to manage the schema."
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
    logger.info("Aletheia API application shutting down...")
    # Cleanup tasks can go here.


# --- Include Routers ---
# Modular router inclusion improves organization
app.include_router(auth_router.router)
app.include_router(search_router.router)
app.include_router(researcher_router.router)
app.include_router(conjecture_router.router)
app.include_router(attribution_router.router)
app.include_router(meta_router.router)

# Incluir los nuevos routers del Eje X y Eje Y
app.include_router(ontology_management_router.router)
app.include_router(knowledge_synthesis_router.router)

logger.info("All API routers have been included.")


# --- Main guard for running with Uvicorn (optional, for direct execution) ---
if __name__ == "__main__":
    # This allows running the app directly with `python -m Aletheia_v3.api.api_server`
    # from the project root.
    import uvicorn

    logger.info(
        "Starting Uvicorn server directly for development via __main__..."
    )
    uvicorn.run(
        "Aletheia_v3.api.api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
