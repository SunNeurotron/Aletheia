import os
import logging
import datetime # Added import
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the API router from the presentation layer
# El router en api.py ya NO tiene el prefijo /api/v1, se añade aquí.
from .presentation.api import router as stats_api_router # Renombrado para claridad

# Import para inicialización y configuración de dependencias
from .infrastructure.database import engine as stats_db_engine, SessionLocal as StatsSessionLocal, SQLALCHEMY_DATABASE_URL as STATS_DB_URL
from .infrastructure.mlflow_tracker import MLflowExperimentTracker # Para verificación
from .presentation.api import MLFLOW_TRACKING_URI as STATS_MLFLOW_URI # Usar la URI configurada en api.py

# --- Logging Configuration ---
# Basic logging setup. In a production app, use a more robust logging configuration (e.g., from a file).
APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO").upper() # Variable de entorno específica para la app
logging.basicConfig(
    level=APP_LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s",
    handlers=[logging.StreamHandler()] # Output logs to console
)
logger = logging.getLogger(__name__) # Logger para este módulo main.py
logger.info(f"Aletheia-Stats API starting with application log level: {APP_LOG_LEVEL}")


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
    logger.info("Aletheia-Stats API application startup sequence initiated...")
    try:
        # Database connection check
        if stats_db_engine:
            logger.info(f"Database URL configured: {STATS_DB_URL[:STATS_DB_URL.find('@') if '@' in STATS_DB_URL else len(STATS_DB_URL)]}")
            with StatsSessionLocal() as db: # Test getting a session
                db.execute("SELECT 1") # Test executing a simple query
            logger.info("Database connection successful at startup.")
        else:
            logger.critical("Database engine (stats_db_engine) is not available. Database operations will fail.")
            # raise RuntimeError("Stats DB engine failed to initialize.") # Option: Fail fast

        # MLflow tracker check
        if STATS_MLFLOW_URI and STATS_MLFLOW_URI.lower() != "none":
            logger.info(f"MLflow Tracking URI configured: {STATS_MLFLOW_URI}")
            # Attempt to create a tracker instance to verify client setup
            try:
                MLflowExperimentTracker(tracking_uri=STATS_MLFLOW_URI)
                logger.info("MLflow client configured successfully at startup (tracker instance created).")
            except Exception as mlflow_err:
                logger.error(f"Failed to initialize MLflow client with URI '{STATS_MLFLOW_URI}': {mlflow_err}", exc_info=True)
        else:
            logger.warning("MLflow Tracking URI is not configured or set to 'none'. MLflow integration will be disabled.")

        logger.info("Aletheia-Stats API startup sequence complete.")
    except ConnectionError as ce: # Specific error for DB connection issues from get_db_session_stats
        logger.critical(f"Database connection/initialization error during startup: {ce}", exc_info=True)
        # Optionally re-raise to prevent app startup if DB is critical
        # raise RuntimeError(f"Critical dependency failed: {ce}") from ce
    except Exception as e:
        logger.critical(f"An unexpected error occurred during API startup: {e}", exc_info=True)
        # raise # Re-raise to prevent app from starting if critical


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
# Mount the router defined in presentation.api.
# The router itself (stats_api_router) should NOT have a prefix if the prefix is applied here.
# My generated api.py had router = APIRouter(tags=["Aletheia-Stats"]) (no prefix)
# So, adding prefix here is correct.
app.include_router(stats_api_router, prefix="/api/v1") # Removed tags here as they are in the router itself
logger.info("Stats API router (stats_api_router) included at prefix /api/v1.")


# --- Root Endpoint (Optional) ---
@app.get("/", summary="Aletheia-Stats API Root", tags=["General"]) # Clarified summary
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
    API_HOST = os.getenv("STATS_API_HOST", "0.0.0.0") # Specific env var for stats module
    API_PORT = int(os.getenv("STATS_API_PORT", "8001")) # Default to 8001 to avoid main Aletheia API
    LOG_LEVEL_UVICORN = os.getenv("STATS_LOG_LEVEL_UVICORN", "info").lower() # Specific env var

    logger.info(f"Attempting to start Uvicorn server for Aletheia-Stats on {API_HOST}:{API_PORT} with Uvicorn log level {LOG_LEVEL_UVICORN}")

    # Check for critical environment variables needed by infrastructure/dependencies
    # STATS_DATABASE_URL is checked by infrastructure.database directly
    # STATS_MLFLOW_TRACKING_URI is checked by presentation.api directly
    # No need to re-check them here explicitly unless for early exit.

    uvicorn.run(
        "aletheia_stats.aletheia_stats.main:app", # Path to this FastAPI app instance
        host=API_HOST,
        port=API_PORT,
        log_level=LOG_LEVEL_UVICORN,
        reload=True # Enable auto-reload for development (set to False in production)
        # workers=N # Number of worker processes for production
    )
    # Note: `reload=True` is convenient for development but should not be used in production.
    # For production, consider using Gunicorn with Uvicorn workers:
    # gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000
