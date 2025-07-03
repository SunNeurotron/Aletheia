# Aletheia_v3/tests/test_api.py
import pytest
from httpx import AsyncClient
from fastapi import status

import uuid # For researcher IDs
from typing import Generator, Optional, Callable, Awaitable

# Import the FastAPI application instance from your API server module
from Aletheia_v3.api.api_server import app  # Main FastAPI app
from Aletheia_v3.infrastructure.database import get_db_session, Base # For DB session override
from Aletheia_v3.infrastructure.models import ResearcherDB
from Aletheia_v3.api.auth import get_password_hash, get_user_retriever as get_aletheia_v3_user_retriever # For test user setup/tokens
from aletheia_common.auth.jwt_handler import UserInDB, get_user_retriever_dependency_placeholder

# For in-memory SQLite DB for tests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession

# --- Test Database Setup ---
# Use an in-memory SQLite database for testing
# WARNING: This will not fully replicate PostgreSQL behavior (e.g. for UUID, ENUMs if not handled by SA, specific PG functions)
# For full fidelity, a test PostgreSQL instance is better.
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///:memory:"
engine_test = create_engine(SQLALCHEMY_DATABASE_URL_TEST, connect_args={"check_same_thread": False})
SessionLocalTest = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# Apply models to the test database (simulates migrations for SQLite)
Base.metadata.create_all(bind=engine_test)

def override_get_db_session() -> Generator[SQLAlchemySession, None, None]:
    db = None
    try:
        db = SessionLocalTest()
        yield db
    finally:
        if db:
            db.close()

# This fixture will provide the actual user retriever that queries the test DB
async def get_researcher_for_auth_test_db(username: str, db: SQLAlchemySession = Depends(override_get_db_session)) -> Optional[UserInDB]:
    researcher = db.query(ResearcherDB).filter(ResearcherDB.username == username).first()
    if researcher:
        user_roles = ["researcher"]
        if researcher.is_admin:
            user_roles.append("admin")
        # Assume ResearcherDB has no 'disabled' field, default to False for UserInDB
        return UserInDB(
            username=researcher.username, email=researcher.email, full_name=researcher.full_name,
            hashed_password=researcher.hashed_password, roles=sorted(list(set(user_roles))), disabled=False
        )
    return None

def get_test_user_retriever() -> Callable[[str], Awaitable[Optional[UserInDB]]]:
    return get_researcher_for_auth_test_db

app.dependency_overrides[get_db_session] = override_get_db_session
# Override the placeholder in aletheia_common with our test-db-backed retriever
app.dependency_overrides[get_user_retriever_dependency_placeholder] = get_test_user_retriever
# Also override the one used directly by Aletheia_v3.api.auth if it's different (it was get_aletheia_v3_user_retriever before)
# This ensures authenticate_user in Aletheia_v3.api.auth also uses the test DB.
# However, get_aletheia_v3_user_retriever itself returns get_researcher_for_auth, which now uses override_get_db_session.
# So the above override for get_user_retriever_dependency_placeholder should be sufficient if all auth flows
# correctly use the common get_current_active_user.
# Let's ensure Aletheia_v3's direct auth also uses the overridden DB session.
# The authenticate_user in Aletheia_v3.api.auth already does Depends(get_db_session), which is now overridden.

# --- Fixtures ---

@pytest.fixture(scope="function") # Changed to function scope to ensure clean DB for some tests
async def test_client() -> AsyncClient:
    """
    Provides an asynchronous test client for making API requests.
    Wraps the FastAPI application.
    """
    # Using `with` ensures lifespan events (startup/shutdown) are handled.
    async with AsyncClient(app=app, base_url="http://test") as client:
        print("Test client created.")
        yield client
        print("Test client closed.")

# Fixture to create a regular researcher user in the test DB
@pytest.fixture(scope="function")
def test_researcher_user(test_client: AsyncClient): # test_client here to ensure DB is initialized if client does it
    db = next(override_get_db_session())
    try:
        researcher = ResearcherDB(
            username="testresearcher",
            full_name="Test Researcher",
            email="testresearcher@example.com",
            hashed_password=get_password_hash("testpass"),
            is_admin=False
        )
        db.add(researcher)
        db.commit()
        db.refresh(researcher)
        yield researcher
    finally:
        db.query(ResearcherDB).delete() # Clean up user
        db.commit()
        db.close()

# Fixture to create an admin user in the test DB
@pytest.fixture(scope="function")
def admin_user(test_client: AsyncClient):
    db = next(override_get_db_session())
    try:
        admin = ResearcherDB(
            username="adminuser",
            full_name="Admin User",
            email="admin@example.com",
            hashed_password=get_password_hash("adminpass"),
            is_admin=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        yield admin
    finally:
        db.query(ResearcherDB).delete() # Clean up user
        db.commit()
        db.close()

@pytest.fixture(scope="function")
async def researcher_token(test_client: AsyncClient, test_researcher_user: ResearcherDB) -> str:
    """Gets an access token for the test_researcher_user."""
    login_data = {"username": test_researcher_user.username, "password": "testpass"}
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK, f"Failed to get researcher token: {response.text}"
    return response.json()["access_token"]

@pytest.fixture(scope="function")
async def admin_token(test_client: AsyncClient, admin_user: ResearcherDB) -> str:
    """Gets an access token for the admin_user."""
    login_data = {"username": admin_user.username, "password": "adminpass"}
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK, f"Failed to get admin token: {response.text}"
    return response.json()["access_token"]


# --- Test Cases ---

# Meta Endpoint Tests
async def test_health_check_endpoint(test_client: AsyncClient): # No auth needed
    """Tests the /health endpoint."""
    response = await test_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["status"] == "OK"
    assert "version" in json_response
    assert "timestamp" in json_response

# Authentication Endpoint Tests
async def test_login_for_access_token_success(test_client: AsyncClient, test_researcher_user: ResearcherDB):
    """Tests successful login and token generation with a real DB user."""
    login_data = {"username": test_researcher_user.username, "password": "testpass"}
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"

async def test_login_for_access_token_failure_wrong_password(test_client: AsyncClient, test_researcher_user: ResearcherDB):
    """Tests login failure with incorrect password for a real DB user."""
    login_data = {"username": test_researcher_user.username, "password": "wrongpassword"}
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    json_response = response.json()
    assert json_response["detail"] == "Incorrect username or password"

async def test_login_for_access_token_failure_wrong_username(test_client: AsyncClient):
    """Tests login failure with non-existent username."""
    login_data = {"username": "nonexistentuser", "password": "testpassword"}
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    json_response = response.json()
    assert json_response["detail"] == "Incorrect username or password"

async def test_read_users_me_success(test_client: AsyncClient, researcher_token: str, test_researcher_user: ResearcherDB):
    """Tests accessing /users/me with a valid researcher token."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    response = await test_client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["username"] == test_researcher_user.username
    assert json_response["email"] == test_researcher_user.email
    # roles are not part of UserResponse schema, but UserAuth has them.
    # The get_researcher_for_auth maps is_admin to "admin" role.

async def test_read_users_me_no_token(test_client: AsyncClient):
    """Tests accessing a protected endpoint without a token."""
    response = await test_client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED # Expecting 401 if not authenticated
    json_response = response.json()
    assert json_response["detail"] == "Not authenticated" # Or specific FastAPI message

async def test_read_users_me_invalid_token(test_client: AsyncClient):
    """Tests accessing a protected endpoint with an invalid or expired token."""
    headers = {"Authorization": "Bearer invalidtoken"}
    response = await test_client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    json_response = response.json()
    assert "Could not validate credentials" in json_response["detail"]


# ABC Discovery Endpoint Tests

# For /searches POST, this endpoint is now protected (requires "researcher" role).
@pytest.mark.asyncio
async def test_create_search_job_success(test_client: AsyncClient, researcher_token: str):
    """Tests successful creation of a new search job with researcher token."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    search_payload = {"n_calls": 20}

    response = await test_client.post("/searches", json=search_payload, headers=headers)

    assert response.status_code == status.HTTP_202_ACCEPTED, f"Response: {response.text}"
    json_response = response.json()
    assert "id" in json_response
    assert "status" in json_response and json_response["status"] == "pending"
    assert json_response["n_calls"] == search_payload["n_calls"]
    assert "created_at" in json_response
    assert "hits" in json_response and isinstance(json_response["hits"], list)

    # Store this job_id for further tests if needed (e.g., in a class or yield from fixture)
    # self.test_job_id = json_response["id"]

@pytest.mark.asyncio
async def test_create_search_job_invalid_n_calls_too_low(test_client: AsyncClient):
    """Tests job creation failure with n_calls below the minimum."""
    search_payload = {"n_calls": 5} # Below gt=10 constraint
    response = await test_client.post("/searches", json=search_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # Validation error
    # Further assertions on the error detail can be added if needed.

@pytest.mark.asyncio
async def test_create_search_job_invalid_n_calls_too_high(test_client: AsyncClient):
    """Tests job creation failure with n_calls above the maximum."""
    search_payload = {"n_calls": 2000} # Above le=1000 constraint in schema
    response = await test_client.post("/searches", json=search_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_search_job_no_auth(test_client: AsyncClient):
    """Tests creating a search job without authentication."""
    search_payload = {"n_calls": 20}
    response = await test_client.post("/searches", json=search_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED # Now protected


# Test for GET /searches/{job_id} - now protected
@pytest.mark.asyncio
async def test_get_job_status_not_found(test_client: AsyncClient, researcher_token: str):
    """Tests retrieving status for a non-existent job ID with auth."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    non_existent_job_id = "non-existent-uuid-12345"
    response = await test_client.get(f"/searches/{non_existent_job_id}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response["detail"] == "Job not found"

@pytest.mark.asyncio
async def test_get_job_status_no_auth(test_client: AsyncClient):
    """Tests retrieving job status without authentication."""
    response = await test_client.get("/searches/some-job-id")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Researcher Endpoint Tests (Create, List, Get, Update) ---

# POST /researchers (create researcher) - Requires admin role
async def test_create_researcher_success_by_admin(test_client: AsyncClient, admin_token: str):
    """Admin successfully creates a new researcher."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    new_researcher_data = {
        "username": "newbie",
        "email": "newbie@example.com",
        "full_name": "New Bie",
        "password": "newbiepassword"
    }
    response = await test_client.post("/researchers", json=new_researcher_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newbie"
    assert data["email"] == "newbie@example.com"
    # Clean up - delete the created researcher
    db = next(override_get_db_session())
    db.query(ResearcherDB).filter(ResearcherDB.username == "newbie").delete()
    db.commit()
    db.close()

async def test_create_researcher_by_researcher_forbidden(test_client: AsyncClient, researcher_token: str):
    """Researcher attempts to create another researcher - should be forbidden."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    new_researcher_data = {"username": "anothernewbie", "email": "another@example.com", "password": "password"}
    response = await test_client.post("/researchers", json=new_researcher_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_create_researcher_no_auth(test_client: AsyncClient):
    """Attempt to create researcher without authentication."""
    new_researcher_data = {"username": "unauthuser", "email": "unauth@example.com", "password": "password"}
    response = await test_client.post("/researchers", json=new_researcher_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# GET /researchers (list researchers) - Requires researcher role
async def test_list_researchers_success(test_client: AsyncClient, researcher_token: str, test_researcher_user: ResearcherDB):
    """Researcher successfully lists researchers."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    response = await test_client.get("/researchers", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Check if the test_researcher_user is in the list (at least one user should be there)
    assert any(r["username"] == test_researcher_user.username for r in data)

async def test_list_researchers_no_auth(test_client: AsyncClient):
    """Attempt to list researchers without authentication."""
    response = await test_client.get("/researchers")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# GET /researchers/{researcher_id} - Requires researcher role
async def test_get_researcher_by_id_success(test_client: AsyncClient, researcher_token: str, test_researcher_user: ResearcherDB):
    """Researcher successfully gets a researcher by ID."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    researcher_id = test_researcher_user.id
    response = await test_client.get(f"/researchers/{researcher_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_researcher_user.username

async def test_get_researcher_by_id_no_auth(test_client: AsyncClient, test_researcher_user: ResearcherDB):
    """Attempt to get researcher by ID without authentication."""
    researcher_id = test_researcher_user.id
    response = await test_client.get(f"/researchers/{researcher_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# PUT /researchers/{researcher_id} - Self update OR admin update
async def test_update_researcher_self(test_client: AsyncClient, researcher_token: str, test_researcher_user: ResearcherDB):
    """Researcher successfully updates their own information."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    researcher_id_to_update = test_researcher_user.id
    update_data = {"full_name": "Updated Test Researcher Name"}

    response = await test_client.put(f"/researchers/{researcher_id_to_update}", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated Test Researcher Name"
    assert data["username"] == test_researcher_user.username # Username should not change here

async def test_update_researcher_by_admin(test_client: AsyncClient, admin_token: str, test_researcher_user: ResearcherDB):
    """Admin successfully updates another researcher's information."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    researcher_id_to_update = test_researcher_user.id
    update_data = {"full_name": "Admin Was Here"}

    response = await test_client.put(f"/researchers/{researcher_id_to_update}", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Admin Was Here"

async def test_update_researcher_by_other_researcher_forbidden(
    test_client: AsyncClient, researcher_token: str, admin_user: ResearcherDB # Use admin_user as the target to update
):
    """Researcher attempts to update another researcher's info - should be forbidden."""
    headers = {"Authorization": f"Bearer {researcher_token}"} # Logged in as testresearcher
    researcher_id_to_update = admin_user.id # Attempting to update adminuser

    # Ensure testresearcher is not the same as admin_user if test_researcher_user was used
    assert admin_user.username != "testresearcher"

    update_data = {"full_name": "Attempted Update by Other"}
    response = await test_client.put(f"/researchers/{researcher_id_to_update}", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

# Note: Tests for Conjectures and Attributions endpoints would follow a similar pattern,
# checking for "researcher" role. They are currently protected by `Depends(common_get_current_active_user)`
# which, with the new setup, means a valid researcher from the DB.
# Adding explicit `Depends(require_roles({"researcher"}))` to them would make the role check more explicit.
# The existing tests for these in `Aletheia_v3/api/api_server.py` already require `current_user`,
# so they would now correctly use the DB-backed user.

# --- Final considerations from original test file ---
# @pytest.mark.skip(reason="Full job lifecycle test requires Celery worker and is more of an integration test.")
# @pytest.mark.asyncio
# async def test_get_completed_job_status_and_results(test_client: AsyncClient, access_token_testuser: str):
# ... (This test remains complex and out of scope for this auth refactor)
