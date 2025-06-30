# Aletheia_v3/api/api_server.py
import uuid
from datetime import timedelta

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Project-specific imports
# Infrastructure
from infrastructure.database import get_db_session, init_db as initialize_database # Renamed to avoid conflict
from infrastructure.models import JobDB # HitDB is accessed via JobDB relationship
from infrastructure.celery_worker import intelligent_discovery_task

# API specific (schemas, auth)
from . import auth # Using . for relative import from the same package
from . import schemas # Using . for relative import

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

# API Router - Helps in organizing endpoints, especially if the API grows.
# All routes defined in this router will be prefixed with /api/v1
# However, for this project, the user's docker-compose and dashboard expect /searches at root.
# So, we'll define routes directly on `app` or use a router without a prefix for now.
# If a prefix is desired later: router = APIRouter(prefix="/api/v1")
router = APIRouter()


# --- Event Handlers ---
@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    For example, initializing the database.
    """
    print("FastAPI application startup...")
    try:
        # This will create tables if they don't exist.
        # In a production setup with migrations (e.g., Alembic), this might be handled differently.
        initialize_database()
        print("Database initialization check complete.")
    except Exception as e:
        print(f"Error during database initialization on startup: {e}")
        # Depending on the severity, you might want to prevent the app from starting.
        # For now, just logging the error.

@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform on application shutdown.
    """
    print("FastAPI application shutdown...")
    # Cleanup tasks can go here, e.g., closing database connection pools if not handled by sessions.


# --- Authentication Endpoints ---

@router.post("/token", response_model=schemas.Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Provides a JWT token for valid user credentials.
    This is the standard OAuth2 password flow endpoint.
    """
    user = await auth.authenticate_user(form_data) # authenticate_user handles exceptions
    if not user: # Should be handled by authenticate_user, but as a safeguard
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password (safeguard)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=schemas.UserResponse, tags=["Users"])
async def read_users_me(current_user: auth.User = Depends(auth.get_current_active_user)):
    """
    Fetches the details of the currently authenticated user.
    This is a protected endpoint.
    """
    # The `current_user` object is already a Pydantic-compatible model (or dict that Pydantic can handle)
    # as returned by `get_current_active_user` after fetching from `auth.User`.
    return schemas.UserResponse(
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        disabled=current_user.disabled
    )


# --- Core Application Endpoints (ABC Discovery) ---

@router.post("/searches", response_model=schemas.JobResponse, status_code=status.HTTP_202_ACCEPTED, tags=["ABC Discovery"])
async def create_new_search_job(
    request: schemas.JobCreateRequest,
    db: Session = Depends(get_db_session),
    # current_user: auth.User = Depends(auth.get_current_active_user) # Uncomment to protect this endpoint
):
    """
    Creates a new intelligent search job for abc-triples.

    - **n_calls**: The budget (number of evaluations) for the Bayesian optimization.
    """
    job_id = str(uuid.uuid4())

    db_job = JobDB(
        id=job_id,
        n_calls=request.n_calls,
        status="pending" # Initial status
        # created_at and updated_at will be set by default in the model
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job) # To get any DB-generated values like timestamps

    # Dispatch the computationally intensive task to Celery
    try:
        task_result = intelligent_discovery_task.delay(job_id=db_job.id, n_calls=request.n_calls)
        print(f"Celery task enqueued with ID: {task_result.id} for job_id: {db_job.id}")
    except Exception as e:
        # If Celery task queuing fails, we should probably mark the job as failed
        # and raise an HTTP exception.
        db_job.status = "failed_queuing"
        db.commit()
        db.refresh(db_job)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue discovery task: {e}"
        )

    # Return the JobResponse schema.
    # Note: `hits` will be empty initially.
    return db_job # FastAPI will convert JobDB to JobResponse due to orm_mode=True

@router.get("/searches/{job_id}", response_model=schemas.JobResponse, tags=["ABC Discovery"])
async def get_search_job_status_and_results(
    job_id: str,
    db: Session = Depends(get_db_session)
    # current_user: auth.User = Depends(auth.get_current_active_user) # Uncomment to protect
):
    """
    Retrieves the status and results of a specific search job.
    """
    # Fetch the job including its related hits using SQLAlchemy's relationship loading.
    # `joinedload(JobDB.hits)` can be used for Eager Loading if performance becomes an issue
    # with many hits, but default lazy loading is often fine.
    db_job = db.query(JobDB).filter(JobDB.id == job_id).first()

    if db_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return db_job # FastAPI converts JobDB (with its hits) to JobResponse

@router.get("/health", response_model=schemas.HealthCheckResponse, tags=["Meta"])
async def health_check():
    """
    Provides a simple health check endpoint for monitoring.
    """
    return schemas.HealthCheckResponse(version=API_VERSION)

# Include the router in the main application
# If using a prefix for the router, it would be app.include_router(router, prefix="/api/v1")
app.include_router(router)

# --- Main guard for running with Uvicorn (optional, for direct execution) ---
if __name__ == "__main__":
    # This allows running the app directly with `python api_server.py`
    # Uvicorn is the ASGI server.
    # Host 0.0.0.0 makes it accessible externally (e.g., from Docker).
    # Reload=True is useful for development, automatically reloads on code changes.
    import uvicorn
    print("Starting Uvicorn server directly for development...")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
    # In docker-compose, uvicorn is typically started like:
    # uvicorn Aletheia_v3.api.api_server:app --host 0.0.0.0 --port 8000
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
