# Aletheia_v3/tests/test_api.py
import pytest
from httpx import AsyncClient
from fastapi import status

# Import the FastAPI application instance from your API server module
# The path should be relative to the project root if tests are run from there,
# or configured via PYTHONPATH. For Dockerized tests, this path needs to be correct
# with respect to how Python resolves modules within the container.
# Assuming tests are run from project root or PYTHONPATH is set up:
from Aletheia_v3.api.api_server import app  # Main FastAPI app
from Aletheia_v3.api.auth import MOCK_USERS_DB, get_password_hash # For test user setup/tokens

# --- Fixtures ---

@pytest.fixture(scope="session") # Changed to session scope for efficiency if multiple test modules use it
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

@pytest.fixture(scope="session")
async def access_token_testuser(test_client: AsyncClient) -> str:
    """
    Fixture to get an access token for the default 'testuser'.
    This simulates a login.
    """
    # Ensure testuser exists with a known password structure if not already hashed
    # This is usually done once if MOCK_USERS_DB is static
    if "testuser" not in MOCK_USERS_DB or "hashed_password" not in MOCK_USERS_DB["testuser"]:
         # This part should ideally not be needed if MOCK_USERS_DB is correctly pre-populated
        MOCK_USERS_DB["testuser"] = {
            "username": "testuser",
            "full_name": "Test User",
            "email": "testuser@example.com",
            "hashed_password": get_password_hash("testpassword"), # Ensure it's hashed
            "disabled": False,
        }


    login_data = {
        "username": "testuser",
        "password": "testpassword" # Plain password for login form
    }
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK, f"Failed to get token: {response.text}"
    token_data = response.json()
    assert "access_token" in token_data
    return token_data["access_token"]


# --- Test Cases ---

# Meta Endpoint Tests
async def test_health_check_endpoint(test_client: AsyncClient):
    """Tests the /health endpoint."""
    response = await test_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["status"] == "OK"
    assert "version" in json_response
    assert "timestamp" in json_response

# Authentication Endpoint Tests
async def test_login_for_access_token_success(test_client: AsyncClient):
    """Tests successful login and token generation."""
    login_data = {"username": "testuser", "password": "testpassword"}
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"

async def test_login_for_access_token_failure_wrong_password(test_client: AsyncClient):
    """Tests login failure with incorrect password."""
    login_data = {"username": "testuser", "password": "wrongpassword"}
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    json_response = response.json()
    assert json_response["detail"] == "Incorrect username or password"

async def test_login_for_access_token_failure_wrong_username(test_client: AsyncClient):
    """Tests login failure with non-existent username."""
    login_data = {"username": "nonexistentuser", "password": "testpassword"}
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED # Or 404 depending on how auth_user handles it
    json_response = response.json()
    assert json_response["detail"] == "Incorrect username or password" # Assuming generic message for security

async def test_read_users_me_success(test_client: AsyncClient, access_token_testuser: str):
    """Tests accessing a protected endpoint (/users/me) with a valid token."""
    headers = {"Authorization": f"Bearer {access_token_testuser}"}
    response = await test_client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["username"] == "testuser"
    assert "email" in json_response # Check for other expected fields

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

# For /searches POST, this endpoint is currently NOT protected in api_server.py.
# If it were protected, access_token_testuser would be needed.
@pytest.mark.asyncio # Explicitly mark if needed, though pytest usually infers for async def
async def test_create_search_job_success(test_client: AsyncClient): # Add access_token_testuser if endpoint becomes protected
    """Tests successful creation of a new search job."""
    # headers = {"Authorization": f"Bearer {access_token_testuser}"} # If protected
    search_payload = {"n_calls": 20} # Minimum valid n_calls (gt=10)

    response = await test_client.post("/searches", json=search_payload) # Add headers=headers if protected

    assert response.status_code == status.HTTP_202_ACCEPTED
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

# Test for GET /searches/{job_id}
# This requires a job to have been created.
# Ideally, this would use the job_id from a successfully created job.
# For simplicity, we'll test with a known non-existent ID first.
@pytest.mark.asyncio
async def test_get_job_status_not_found(test_client: AsyncClient): # Add access_token_testuser if protected
    """Tests retrieving status for a non-existent job ID."""
    # headers = {"Authorization": f"Bearer {access_token_testuser}"} # If protected
    non_existent_job_id = "non-existent-uuid-12345"
    response = await test_client.get(f"/searches/{non_existent_job_id}") # Add headers=headers if protected
    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response["detail"] == "Job not found"

# To test GET /searches/{job_id} for a real job, you'd typically:
# 1. Create a job via POST /searches.
# 2. Get its ID.
# 3. Poll GET /searches/{job_id} until status is 'completed' or 'failed'.
# This involves Celery workers and can be more complex for an automated test,
# often requiring either:
#    a) Mocking Celery task execution to return immediately with a result.
#    b) Running a full integration test environment with Celery workers, Redis, DB.
#    c) Testing the API endpoint logic assuming the Celery task part works as expected (unit/integration focus on API layer).

# For now, this test suite focuses on API request/response validation, auth, and basic CRUD logic.
# Testing the full asynchronous job flow would be a more involved integration test.

# Example of a placeholder for a more complex test:
@pytest.mark.skip(reason="Full job lifecycle test requires Celery worker and is more of an integration test.")
@pytest.mark.asyncio
async def test_get_completed_job_status_and_results(test_client: AsyncClient, access_token_testuser: str):
    # 1. Create job
    headers = {"Authorization": f"Bearer {access_token_testuser}"} # If protected
    search_payload = {"n_calls": 20} # A small number for faster "completion" if real
    post_response = await test_client.post("/searches", json=search_payload, headers=headers)
    assert post_response.status_code == status.HTTP_202_ACCEPTED
    job_id = post_response.json()["id"]

    # 2. Poll for completion (this part is tricky in a unit/integration test without a running worker or mocks)
    #    For a real test, you might need `await asyncio.sleep()` and retries.
    #    Or, if Celery is configured for `task_always_eager=True` in test settings, it might run synchronously.

    # Assume job completes and we fetch it (replace with actual polling/waiting logic)
    # This step would fail if the job doesn't actually complete in the test environment.
    # await asyncio.sleep(10) # Placeholder - DO NOT use long sleeps in tests without good reason.

    get_response = await test_client.get(f"/searches/{job_id}", headers=headers)
    assert get_response.status_code == status.HTTP_200_OK
    job_data = get_response.json()
    assert job_data["status"] == "completed" # This is the key assertion for a completed job
    assert "hits" in job_data
    # Further assertions on the structure of hits if any were found.
    pass


# Note: If your FastAPI app uses global state or dependencies that are not easily
# reset between tests (like database connections not managed by fixtures),
# you might need more sophisticated fixture setups (e.g., transaction rollbacks for DB tests).
# The `get_db_session` dependency in FastAPI is designed to handle session scope per request,
# which is generally good for testing.
# MLflow integration testing would also be separate, potentially mocking MLflow calls
# or verifying interactions if a test MLflow server is part of the test setup.
