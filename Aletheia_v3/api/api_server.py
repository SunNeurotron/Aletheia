# Aletheia_v3/api/api_server.py
import uuid
from datetime import timedelta, datetime, timezone # Added datetime, timezone
from typing import List # Added List

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Project-specific imports
# Infrastructure
from infrastructure.database import get_db_session, init_db as initialize_database # Renamed to avoid conflict
from infrastructure.models import JobDB, HitDB, ResearcherDB, DerivedConjectureDB, DiscoveryAttributionDB, conjecture_hits_association
from infrastructure.celery_worker import intelligent_discovery_task

# API specific (schemas, auth)
from . import auth as aletheia_v3_auth # Alias para el módulo de auth local de Aletheia_v3
from . import schemas # Using . for relative import
from infrastructure.models import ContributionTypeEnum, ConjectureStatusEnum # Added ConjectureStatusEnum

# Import common authentication components
from aletheia_common.auth.jwt_handler import (
    get_current_active_user as common_get_current_active_user,
    get_current_active_user_optional as common_get_current_active_user_optional, # Importar la versión opcional
    UserAuth as CommonUserAuth, # Modelo Pydantic para el usuario autenticado
    get_user_retriever_dependency_placeholder,
    require_roles, # Importar para la autorización basada en roles
    require_any_role # Importar si se necesita lógica OR para roles
)
# Import la implementación del user_retriever de Aletheia_v3
from .auth import get_user_retriever as get_aletheia_v3_user_retriever

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
app.dependency_overrides[get_user_retriever_dependency_placeholder] = get_aletheia_v3_user_retriever


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
        # initialize_database() # Commented out: Alembic will now handle table creation and migrations.
        print("Database initialization via initialize_database() (create_all) is now DIASABLED.")
        print("Ensure Alembic migrations are run to set up the database schema.")
        # print("Database initialization check complete.") # No longer accurate
    except Exception as e:
        # This exception block might still be relevant if other startup tasks are added.
        print(f"Error during other startup tasks (if any): {e}")
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
    Uses authenticate_user from Aletheia_v3.api.auth which now hits the DB.
    """
    # aletheia_v3_auth.authenticate_user now takes db session
    user_in_db = await aletheia_v3_auth.authenticate_user(form_data=form_data, db=Depends(get_db_session))
    # user_in_db is of type UserInDB from common, which includes roles

    access_token_expires = timedelta(minutes=aletheia_v3_auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Create token using Aletheia_v3's local create_access_token or common one
    # For consistency, if jwt_handler.create_access_token is suitable, use it.
    # Assuming aletheia_v3_auth.create_access_token is what we want for now.
    access_token = aletheia_v3_auth.create_access_token(
        data={"sub": user_in_db.username, "roles": user_in_db.roles}, # Include roles in token
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=schemas.UserResponse, tags=["Users"]) # UserResponse needs to be compatible with CommonUserAuth
async def read_users_me(current_user: CommonUserAuth = Depends(common_get_current_active_user)):
    """
    Fetches the details of the currently authenticated user.
    Uses the common get_current_active_user which now relies on the overridden user_retriever.
    This is a protected endpoint.
    """
    # CommonUserAuth has 'username' and 'roles'.
    # schemas.UserResponse expects 'username', 'email', 'full_name', 'disabled'.
    # We need to fetch the full UserInDB or ResearcherDB again, or expand CommonUserAuth/token.
    # For now, let's assume UserResponse can be partially filled or we adapt.
    # To get full details, we'd re-fetch from DB or put more in token (not ideal for all fields).

    # Simplest for now: schemas.UserResponse needs to be updated or only return what CommonUserAuth provides.
    # Let's assume we want to show what's in CommonUserAuth for this endpoint.
    # This means schemas.UserResponse might need adjustment if it strictly requires email/full_name.
    # For this step, we focus on wiring up auth.
    # A proper UserResponse would re-fetch the ResearcherDB object.
    # Let's simulate that:
    db_researcher = await aletheia_v3_auth.get_researcher_for_auth(username=current_user.username, db=Depends(get_db_session))
    if not db_researcher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Authenticated user not found in database.")

    return schemas.UserResponse(
        username=db_researcher.username,
        email=db_researcher.email,
        full_name=db_researcher.full_name,
        disabled=db_researcher.disabled # Assuming UserInDB has disabled, and get_researcher_for_auth maps it
    )


# --- Core Application Endpoints (ABC Discovery) ---

@router.post("/searches", response_model=schemas.JobResponse, status_code=status.HTTP_202_ACCEPTED, tags=["ABC Discovery"])
async def create_new_search_job(
    request: schemas.JobCreateRequest,
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(require_roles({"researcher"})) # Protegido: requiere rol researcher
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
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(require_roles({"researcher"})) # Protegido: requiere rol researcher
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

# --- Researcher Endpoints ---
@router.post("/researchers", response_model=schemas.ResearcherResponse, status_code=status.HTTP_201_CREATED, tags=["Researchers"])
async def create_researcher(
    researcher_in: schemas.ResearcherCreate,
    db: Session = Depends(get_db_session),
    current_admin: CommonUserAuth = Depends(require_roles({"admin"})) # Protegido: Solo admin puede crear researchers
):
    """
    Creates a new researcher. Only accessible by users with the 'admin' role.
    Passwords are automatically hashed.
    """
    # Check if username or email already exists
    existing_researcher_username = db.query(ResearcherDB).filter(ResearcherDB.username == researcher_in.username).first()
    if existing_researcher_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    existing_researcher_email = db.query(ResearcherDB).filter(ResearcherDB.email == researcher_in.email).first()
    if existing_researcher_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = auth.get_password_hash(researcher_in.password)
    db_researcher = ResearcherDB(
        username=researcher_in.username,
        full_name=researcher_in.full_name,
        email=researcher_in.email,
        orcid=researcher_in.orcid,
        hashed_password=hashed_password
    )
    db.add(db_researcher)
    db.commit()
    db.refresh(db_researcher)
    return db_researcher

@router.get("/researchers", response_model=List[schemas.ResearcherResponse], tags=["Researchers"])
async def list_researchers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(require_roles({"researcher"})) # Protegido: requiere rol researcher (o viewer si se define)
):
    """
    Retrieves a list of researchers. Requires 'researcher' role.
    """
    researchers = db.query(ResearcherDB).offset(skip).limit(limit).all()
    return researchers

@router.get("/researchers/{researcher_id}", response_model=schemas.ResearcherResponse, tags=["Researchers"])
async def get_researcher(
    researcher_id: uuid.UUID, # FastAPI handles UUID conversion
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(require_roles({"researcher"})) # Protegido: requiere rol researcher
):
    """
    Retrieves a specific researcher by their ID. Requires 'researcher' role.
    """
    db_researcher = db.query(ResearcherDB).filter(ResearcherDB.id == researcher_id).first()
    if db_researcher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Researcher not found")
    return db_researcher

@router.put("/researchers/{researcher_id}", response_model=schemas.ResearcherResponse, tags=["Researchers"])
async def update_researcher_info(
    researcher_id: uuid.UUID,
    researcher_update: schemas.ResearcherUpdate,
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(common_get_current_active_user) # Ensure only admin or self can update
):
    """
    Updates a researcher's information. (Password update should be separate)
    Requires authentication. Current user must be the researcher being updated or an admin.
    """
    db_researcher = db.query(ResearcherDB).filter(ResearcherDB.id == researcher_id).first()
    if db_researcher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Researcher not found")

    # Authorization: User can update themselves, or an admin can update anyone.
    is_self = db_researcher.username == current_user.username
    is_admin_user = "admin" in current_user.roles

    if not (is_self or is_admin_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this researcher's information."
        )

    update_data = researcher_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_researcher, key, value)

    db_researcher.updated_at = datetime.now(timezone.utc) # Manually update timestamp if not server_default onupdate
    db.commit()
    db.refresh(db_researcher)
    return db_researcher


# --- Derived Conjecture Endpoints ---
@router.post("/conjectures", response_model=schemas.ConjectureResponse, status_code=status.HTTP_201_CREATED, tags=["Conjectures"])
async def create_derived_conjecture(
    conjecture_in: schemas.ConjectureCreate,
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(require_roles({"researcher"})) # Requiere rol researcher
):
    """
    Creates a new derived conjecture. Requires 'researcher' role.
    The proposer is automatically set to the currently authenticated researcher.
    """
    # current_user is already validated to be a researcher by require_roles
    # and get_researcher_for_auth would have failed if not found in ResearcherDB.
    # However, we still need the ResearcherDB object to link as proposer_id.
    researcher = db.query(ResearcherDB).filter(ResearcherDB.username == current_user.username).first()
    if not researcher: # Should not happen if require_roles and get_researcher_for_auth work
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authenticated researcher could not be retrieved from database.")

    db_conjecture = DerivedConjectureDB(
        title=conjecture_in.title,
        description=conjecture_in.description,
        proposer_id=researcher.id,
        status=ConjectureStatusEnum.PROPOSED # Default status, using imported Enum
    )

    # Handle supporting hits if provided
    if conjecture_in.supporting_hit_ids:
        hits = db.query(HitDB).filter(HitDB.id.in_(conjecture_in.supporting_hit_ids)).all()
        if len(hits) != len(set(conjecture_in.supporting_hit_ids)): # Check if all provided IDs were found
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more supporting hit IDs not found.")
        db_conjecture.supporting_hits.extend(hits)

    db.add(db_conjecture)
    db.commit()
    db.refresh(db_conjecture)
    # To populate proposer and supporting_hits_count for response:
    db.refresh(db_conjecture.proposer) # Eager load proposer for response schema if needed
    response_data = schemas.ConjectureResponse.model_validate(db_conjecture)
    response_data.supporting_hits_count = len(db_conjecture.supporting_hits)
    return response_data


@router.get("/conjectures", response_model=List[schemas.ConjectureResponse], tags=["Conjectures"])
async def list_derived_conjectures( # Ya estaba usando common_get_current_active_user_optional
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session),
    current_user: Optional[CommonUserAuth] = Depends(common_get_current_active_user_optional)
):
    """
    Retrieves a list of derived conjectures. Publicly accessible.
    If user is authenticated, future enhancements could personalize results.
    """
    conjectures_db = db.query(DerivedConjectureDB).order_by(DerivedConjectureDB.created_at.desc()).offset(skip).limit(limit).all()

    # Populate supporting_hits_count for each conjecture
    response_list = []
    for conj in conjectures_db:
        data = schemas.ConjectureResponse.model_validate(conj)
        data.supporting_hits_count = len(conj.supporting_hits) # SQLAlchemy loads this on access if lazy
        response_list.append(data)
    return response_list


@router.get("/conjectures/{conjecture_id}", response_model=schemas.ConjectureResponse, tags=["Conjectures"])
async def get_derived_conjecture(
    conjecture_id: int,
    db: Session = Depends(get_db_session),
    current_user: Optional[CommonUserAuth] = Depends(common_get_current_active_user_optional) # Opcional
):
    """
    Retrieves a specific derived conjecture by its ID. Publicly accessible.
    """
    db_conjecture = db.query(DerivedConjectureDB).filter(DerivedConjectureDB.id == conjecture_id).first()
    if db_conjecture is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conjecture not found")

    response_data = schemas.ConjectureResponse.model_validate(db_conjecture)
    response_data.supporting_hits_count = len(db_conjecture.supporting_hits)
    return response_data

# PUT /conjectures/{conjecture_id} (for updates) would be similar to researcher update.
# DELETE /conjectures/{conjecture_id} could also be added.

# --- Discovery Attribution Endpoints (Conceptual / Simplified) ---
# Full CRUD for attributions can be extensive.
# For now, let's consider that attributions might be created more implicitly
# (e.g., job submitter gets an automatic 'discovered_by_job' attribution)
# or via a more specialized service/logic.
# A simple endpoint to add a 'verified_by_user' or 'analyzed_by_user' attribution:

@router.post("/hits/{hit_id}/attributions", response_model=schemas.AttributionResponse, status_code=status.HTTP_201_CREATED, tags=["Attributions"])
async def add_attribution_to_hit(
    hit_id: int,
    attribution_in: schemas.AttributionCreate, # Should not contain researcher_id, that's the current user
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(require_roles({"researcher"})) # Requiere rol researcher
):
    """
    Adds an attribution (e.g., 'verified', 'analyzed') to a specific discovery hit
    by the currently authenticated researcher. Requires 'researcher' role.
    """
    researcher = db.query(ResearcherDB).filter(ResearcherDB.username == current_user.username).first()
    if not researcher: # Should not happen if require_roles and get_researcher_for_auth work
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authenticated researcher could not be retrieved from database.")

    db_hit = db.query(HitDB).filter(HitDB.id == hit_id).first()
    if not db_hit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hit not found.")

    # Ensure contribution_type is valid (from Enum)
    try:
        contribution_type_enum = ContributionTypeEnum(attribution_in.contribution_type)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid contribution_type.")


    db_attribution = DiscoveryAttributionDB(
        hit_id=db_hit.id,
        researcher_id=researcher.id,
        contribution_type=contribution_type_enum,
        details=attribution_in.details
    )
    db.add(db_attribution)
    db.commit()
    db.refresh(db_attribution)
    return db_attribution


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
