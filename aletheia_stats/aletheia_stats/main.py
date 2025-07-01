import os
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the API router from the presentation layer
from .presentation.api import api_router as presentation_api_router

# Import dependency providers (if they are not auto-setup in api.py or managed by a DI framework)
# from .presentation.api import get_db_url, get_mlflow_uri, get_stats_service, get_stats_repository, get_mlflow_tracker

# --- Logging Configuration ---
# Basic logging setup. In a production app, use a more robust logging configuration (e.g., from a file).
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()] # Output logs to console
)
logger = logging.getLogger(__name__)
logger.info(f"Aletheia-Stats API starting with log level: {LOG_LEVEL}")


# --- FastAPI Application Instantiation ---
app = FastAPI(
    title="Aletheia-Stats API",
    version=os.getenv("API_VERSION", "0.1.0"),
    description="API for statistical analysis, including t-tests, with MDU compliance.",
    openapi_url="/api/v1/openapi.json", # Customize OpenAPI path
    docs_url="/api/docs",               # Customize Swagger UI path
    redoc_url="/api/redoc"              # Customize ReDoc path
)

# --- CORS (Cross-Origin Resource Sharing) Middleware ---
# Configure CORS to allow requests from specific origins (e.g., a frontend application).
# For development, allowing all origins might be acceptable, but be restrictive in production.
origins = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",") # Default to all if not set
if "*" in origins and len(origins) > 1:
    logger.warning("CORS_ALLOWED_ORIGINS contains '*' along with other origins. This is likely a misconfiguration. Defaulting to '*' for broad compatibility during dev.")
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # Allow cookies if your auth uses them
    allow_methods=["*"],    # Or specify methods like ["GET", "POST"]
    allow_headers=["*"],    # Or specify necessary headers
)
logger.info(f"CORS middleware configured for origins: {origins}")


# --- Event Handlers (Startup and Shutdown) ---
@app.on_event("startup")
async def startup_event():
    """
    Actions to perform when the application starts.
    - Initialize database connections (SQLAlchemy engine is created on repo instantiation)
    - Initialize MLflow tracker (MLflow client is configured on tracker instantiation)
    - Warm up caches, etc.
    """
    logger.info("Aletheia-Stats API application startup...")
    try:
        # Trigger instantiation of dependencies to check connections early
        # (These are lazily loaded by Depends in api.py, but can be pre-warmed)
        # from .presentation.api import get_stats_repository, get_mlflow_tracker
        # get_stats_repository() # This will create engine and potentially test connection if pool_pre_ping is true
        # if get_mlflow_tracker(): # This will set tracking URI
        #     logger.info("MLflow tracker successfully initialized at startup.")
        # else:
        #     logger.warning("MLflow tracker not available at startup (MLFLOW_TRACKING_URI might be missing).")

        # Check if DB can be reached (simple way, actual query)
        # from .infrastructure.database import SessionLocal # If you have a SessionLocal
        # try:
        #     db = SessionLocal()
        #     db.execute("SELECT 1")
        # finally:
        #     db.close()
        # logger.info("Database connection successful at startup.")

        logger.info("Aletheia-Stats API startup complete.")
    except Exception as e:
        logger.critical(f"Error during API startup: {e}", exc_info=True)
        # Depending on the severity, you might want to exit or prevent the app from starting fully.
        # For now, just log critical.
        # raise # Re-raise to prevent app from starting if critical (e.g. DB down)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform when the application shuts down.
    - Close database connections
    - Clean up resources
    """
    logger.info("Aletheia-Stats API application shutting down...")
    # Add cleanup logic here if necessary (e.g., closing DB engine explicitly if not handled by SQLAlchemy's pool)
    logger.info("Aletheia-Stats API shutdown complete.")


# --- Include API Routers ---
# Mount the router defined in presentation.api
app.include_router(presentation_api_router, prefix="/api/v1", tags=["Aletheia-Stats"])
logger.info("Presentation API router included at prefix /api/v1.")


# --- Root Endpoint (Optional) ---
@app.get("/", summary="Root Endpoint", tags=["General"])
async def read_root():
    """
    Root endpoint providing basic information about the API.
    """
    return {
        "message": "Welcome to Aletheia-Stats API",
        "version": app.version,
        "docs_url": app.docs_url,
        "redoc_url": app.redoc_url,
        "description": "Please visit the /api/docs for detailed API documentation."
    }

# --- Health Check Endpoint (Optional but Recommended) ---
@app.get("/health", status_code=status.HTTP_200_OK, summary="Health Check", tags=["General"])
async def health_check():
    """
    Simple health check endpoint.
    Can be expanded to check database connectivity, etc.
    """
    # Add more sophisticated health checks if needed (e.g., DB, MLflow connectivity)
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# --- Main execution (for running with uvicorn directly) ---
if __name__ == "__main__":
    # This block allows running the FastAPI app directly using `python main.py`
    # Uvicorn server configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000")) # Default to 8000
    LOG_LEVEL_UVICORN = os.getenv("LOG_LEVEL_UVICORN", "info").lower() # Uvicorn's own log level

    logger.info(f"Starting Uvicorn server on {API_HOST}:{API_PORT} with log level {LOG_LEVEL_UVICORN}")

    # Ensure DATABASE_URL and MLFLOW_TRACKING_URI are set if you want to test dependencies
    if not os.getenv("DATABASE_URL"):
        logger.warning("DATABASE_URL is not set. Database operations will likely fail.")
    if not os.getenv("MLFLOW_TRACKING_URI"):
        logger.warning("MLFLOW_TRACKING_URI is not set. MLflow operations will be disabled or fail.")

    uvicorn.run(
        "aletheia_stats.aletheia_stats.main:app", # Path to the FastAPI app instance
        host=API_HOST,
        port=API_PORT,
        log_level=LOG_LEVEL_UVICORN,
        reload=True # Enable auto-reload for development (set to False in production)
        # workers=N # Number of worker processes for production
    )
    # Note: `reload=True` is convenient for development but should not be used in production.
    # For production, consider using Gunicorn with Uvicorn workers:
    # gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000
