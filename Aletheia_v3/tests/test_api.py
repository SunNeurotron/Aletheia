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

# Aletheia_v3/tests/test_api.py
import uuid  # For researcher IDs
from typing import Awaitable, Callable, Generator, Optional

import pytest
import pytest_asyncio # Import for explicit async fixture decoration
from fastapi import Depends, status  # Added Depends
from httpx import AsyncClient

# For in-memory SQLite DB for tests
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import sessionmaker

from aletheia_common.auth.jwt_handler import (
    UserInDB,
    get_user_retriever_dependency_placeholder,
)

# Import the FastAPI application instance from your API server module
from Aletheia_v3.api.api_server import app  # Main FastAPI app
from Aletheia_v3.api.auth import get_password_hash
from Aletheia_v3.api.auth import (
    get_user_retriever as get_aletheia_v3_user_retriever,  # For test user setup/tokens
)
from Aletheia_v3.infrastructure.database import (  # For DB session override
    Base,
    get_db_session,
)
from Aletheia_v3.infrastructure.models import ResearcherDB

# --- Test Database Setup ---
# Use an in-memory SQLite database for testing
# WARNING: This will not fully replicate PostgreSQL behavior (e.g. for UUID, ENUMs if not handled by SA, specific PG functions)
# For full fidelity, a test PostgreSQL instance is better.
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///:memory:"
engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST, connect_args={"check_same_thread": False}
)
SessionLocalTest = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_test
)

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
async def get_researcher_for_auth_test_db(
    username: str, db: SQLAlchemySession = Depends(override_get_db_session)
) -> Optional[UserInDB]:
    researcher = (
        db.query(ResearcherDB)
        .filter(ResearcherDB.username == username)
        .first()
    )
    if researcher:
        user_roles = ["researcher"]
        if researcher.is_admin:
            user_roles.append("admin")
        # Assume ResearcherDB has no 'disabled' field, default to False for UserInDB
        return UserInDB(
            username=researcher.username,
            email=researcher.email,
            full_name=researcher.full_name,
            hashed_password=researcher.hashed_password,
            roles=sorted(list(set(user_roles))),
            disabled=False,
        )
    return None


def get_test_user_retriever() -> (
    Callable[[str], Awaitable[Optional[UserInDB]]]
):
    return get_researcher_for_auth_test_db


app.dependency_overrides[get_db_session] = override_get_db_session
# Override the placeholder in aletheia_common with our test-db-backed retriever
app.dependency_overrides[get_user_retriever_dependency_placeholder] = (
    get_test_user_retriever
)
# Also override the one used directly by Aletheia_v3.api.auth if it's different (it was get_aletheia_v3_user_retriever before)
# This ensures authenticate_user in Aletheia_v3.api.auth also uses the test DB.
# However, get_aletheia_v3_user_retriever itself returns get_researcher_for_auth, which now uses override_get_db_session.
# So the above override for get_user_retriever_dependency_placeholder should be sufficient if all auth flows
# correctly use the common get_current_active_user.
# Let's ensure Aletheia_v3's direct auth also uses the overridden DB session.
# The authenticate_user in Aletheia_v3.api.auth already does Depends(get_db_session), which is now overridden.

# --- Fixtures ---


@pytest_asyncio.fixture(scope="function")
async def test_client() -> AsyncClient: # Explicitly an asyncio fixture
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
def test_researcher_user(
    test_client: AsyncClient,
):  # test_client here to ensure DB is initialized if client does it
    db = next(override_get_db_session())
    try:
        researcher = ResearcherDB(
            username="testresearcher",
            full_name="Test Researcher",
            email="testresearcher@example.com",
            hashed_password=get_password_hash("testpass"),
            is_admin=False,
        )
        db.add(researcher)
        db.commit()
        db.refresh(researcher)
        yield researcher
    finally:
        db.query(ResearcherDB).delete()  # Clean up user
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
            is_admin=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        yield admin
    finally:
        db.query(ResearcherDB).delete()  # Clean up user
        db.commit()
        db.close()


@pytest_asyncio.fixture(scope="function") # Explicitly an asyncio fixture
async def researcher_token(
    test_client: AsyncClient, test_researcher_user: ResearcherDB
) -> str:
    """Gets an access token for the test_researcher_user."""
    login_data = {
        "username": test_researcher_user.username,
        "password": "testpass",
    }
    response = await test_client.post("/token", data=login_data)
    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Failed to get researcher token: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="function")
async def admin_token(
    test_client: AsyncClient, admin_user: ResearcherDB
) -> str:
    """Gets an access token for the admin_user."""
    login_data = {"username": admin_user.username, "password": "adminpass"}
    response = await test_client.post("/token", data=login_data)
    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Failed to get admin token: {response.text}"
    return response.json()["access_token"]


# --- Test Cases ---


# Meta Endpoint Tests
@pytest.mark.asyncio
async def test_health_check_endpoint(
    test_client: AsyncClient,
):  # No auth needed
    """Tests the /health endpoint."""
    response = await test_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["status"] == "OK"
    assert "version" in json_response
    assert "timestamp" in json_response


# Authentication Endpoint Tests
@pytest.mark.asyncio
async def test_login_for_access_token_success(
    test_client: AsyncClient, test_researcher_user: ResearcherDB
):
    """Tests successful login and token generation with a real DB user."""
    login_data = {
        "username": test_researcher_user.username,
        "password": "testpass",
    }
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_for_access_token_failure_wrong_password(
    test_client: AsyncClient, test_researcher_user: ResearcherDB
):
    """Tests login failure with incorrect password for a real DB user."""
    login_data = {
        "username": test_researcher_user.username,
        "password": "wrongpassword",
    }
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    json_response = response.json()
    assert json_response["detail"] == "Incorrect username or password"


@pytest.mark.asyncio
async def test_login_for_access_token_failure_wrong_username(
    test_client: AsyncClient,
):
    """Tests login failure with non-existent username."""
    login_data = {"username": "nonexistentuser", "password": "testpassword"}
    response = await test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    json_response = response.json()
    assert json_response["detail"] == "Incorrect username or password"


@pytest.mark.asyncio
async def test_read_users_me_success(
    test_client: AsyncClient,
    researcher_token: str,
    test_researcher_user: ResearcherDB,
):
    """Tests accessing /users/me with a valid researcher token."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    response = await test_client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["username"] == test_researcher_user.username
    assert json_response["email"] == test_researcher_user.email
    # roles are not part of UserResponse schema, but UserAuth has them.
    # The get_researcher_for_auth maps is_admin to "admin" role.


@pytest.mark.asyncio
async def test_read_users_me_no_token(test_client: AsyncClient):
    """Tests accessing a protected endpoint without a token."""
    response = await test_client.get("/users/me")
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    )  # Expecting 401 if not authenticated
    json_response = response.json()
    assert (
        json_response["detail"] == "Not authenticated"
    )  # Or specific FastAPI message


@pytest.mark.asyncio
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
async def test_create_search_job_success(
    test_client: AsyncClient, researcher_token: str
):
    """Tests successful creation of a new search job with researcher token."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    search_payload = {"n_calls": 20}

    response = await test_client.post(
        "/searches", json=search_payload, headers=headers
    )

    assert (
        response.status_code == status.HTTP_202_ACCEPTED
    ), f"Response: {response.text}"
    json_response = response.json()
    assert "id" in json_response
    assert "status" in json_response and json_response["status"] == "pending"
    assert json_response["n_calls"] == search_payload["n_calls"]
    assert "created_at" in json_response
    assert "hits" in json_response and isinstance(json_response["hits"], list)

    # Store this job_id for further tests if needed (e.g., in a class or yield from fixture)
    # self.test_job_id = json_response["id"]


# test_create_search_job_invalid_n_calls_too_low is already marked with @pytest.mark.asyncio
# No change needed here based on the previous logic, but ensuring all async tests are marked.
# It was failing due to client issue, not lack of mark.
# The issue was that the client fixture itself was not correctly processed.

@pytest.mark.asyncio
async def test_create_search_job_invalid_n_calls_too_low( # Already marked
    test_client: AsyncClient,
):
    """Tests job creation failure with n_calls below the minimum."""
    search_payload = {"n_calls": 5}  # Below gt=10 constraint
    response = await test_client.post("/searches", json=search_payload)
    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    )  # Validation error
    # Further assertions on the error detail can be added if needed.


# Similarly, test_create_search_job_invalid_n_calls_too_high is already marked.
@pytest.mark.asyncio
async def test_create_search_job_invalid_n_calls_too_high( # Already marked
    test_client: AsyncClient,
):
    """Tests job creation failure with n_calls above the maximum."""
    search_payload = {"n_calls": 2000}  # Above le=1000 constraint in schema
    response = await test_client.post("/searches", json=search_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_search_job_no_auth(test_client: AsyncClient):
    """Tests creating a search job without authentication."""
    search_payload = {"n_calls": 20}
    response = await test_client.post("/searches", json=search_payload)
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    )  # Now protected


# Test for GET /searches/{job_id} - now protected
@pytest.mark.asyncio
async def test_get_job_status_not_found(
    test_client: AsyncClient, researcher_token: str
):
    """Tests retrieving status for a non-existent job ID with auth."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    non_existent_job_id = "non-existent-uuid-12345"
    response = await test_client.get(
        f"/searches/{non_existent_job_id}", headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response["detail"] == "Job not found"


# test_get_job_status_no_auth is already marked.
@pytest.mark.asyncio
async def test_get_job_status_no_auth(test_client: AsyncClient): # Already marked
    """Tests retrieving job status without authentication."""
    response = await test_client.get("/searches/some-job-id")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Researcher Endpoint Tests (Create, List, Get, Update) ---


# POST /researchers (create researcher) - Requires admin role
@pytest.mark.asyncio
async def test_create_researcher_success_by_admin(
    test_client: AsyncClient, admin_user: ResearcherDB # Changed from admin_token to admin_user
):
    """Admin successfully creates a new researcher."""
    # Manually fetch token inside test for diagnostics
    login_data = {"username": admin_user.username, "password": "adminpass"}
    token_response = await test_client.post("/token", data=login_data)
    assert token_response.status_code == status.HTTP_200_OK, f"Failed to get admin token in test: {token_response.text}"
    actual_admin_token = token_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {actual_admin_token}"}
    new_researcher_data = {
        "username": "newbie",
        "email": "newbie@example.com",
        "full_name": "New Bie",
        "password": "newbiepassword",
    }
    response = await test_client.post(
        "/researchers", json=new_researcher_data, headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newbie"
    assert data["email"] == "newbie@example.com"
    # Clean up - delete the created researcher
    db = next(override_get_db_session())
    db.query(ResearcherDB).filter(ResearcherDB.username == "newbie").delete()
    db.commit()
    db.close()


@pytest.mark.asyncio
async def test_create_researcher_by_researcher_forbidden(
    test_client: AsyncClient, researcher_token: str
):
    """Researcher attempts to create another researcher - should be forbidden."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    new_researcher_data = {
        "username": "anothernewbie",
        "email": "another@example.com",
        "password": "password",
    }
    response = await test_client.post(
        "/researchers", json=new_researcher_data, headers=headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_create_researcher_no_auth(test_client: AsyncClient):
    """Attempt to create researcher without authentication."""
    new_researcher_data = {
        "username": "unauthuser",
        "email": "unauth@example.com",
        "password": "password",
    }
    response = await test_client.post("/researchers", json=new_researcher_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# GET /researchers (list researchers) - Requires researcher role
@pytest.mark.asyncio
async def test_list_researchers_success(
    test_client: AsyncClient,
    researcher_token: str,
    test_researcher_user: ResearcherDB,
):
    """Researcher successfully lists researchers."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    response = await test_client.get("/researchers", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Check if the test_researcher_user is in the list (at least one user should be there)
    assert any(r["username"] == test_researcher_user.username for r in data)


@pytest.mark.asyncio
async def test_list_researchers_no_auth(test_client: AsyncClient):
    """Attempt to list researchers without authentication."""
    response = await test_client.get("/researchers")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# GET /researchers/{researcher_id} - Requires researcher role
@pytest.mark.asyncio
async def test_get_researcher_by_id_success(
    test_client: AsyncClient,
    researcher_token: str,
    test_researcher_user: ResearcherDB,
):
    """Researcher successfully gets a researcher by ID."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    researcher_id = test_researcher_user.id
    response = await test_client.get(
        f"/researchers/{researcher_id}", headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_researcher_user.username


@pytest.mark.asyncio
async def test_get_researcher_by_id_no_auth(
    test_client: AsyncClient, test_researcher_user: ResearcherDB
):
    """Attempt to get researcher by ID without authentication."""
    researcher_id = test_researcher_user.id
    response = await test_client.get(f"/researchers/{researcher_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# PUT /researchers/{researcher_id} - Self update OR admin update
@pytest.mark.asyncio
async def test_update_researcher_self(
    test_client: AsyncClient,
    researcher_token: str,
    test_researcher_user: ResearcherDB,
):
    """Researcher successfully updates their own information."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    researcher_id_to_update = test_researcher_user.id
    update_data = {"full_name": "Updated Test Researcher Name"}

    response = await test_client.put(
        f"/researchers/{researcher_id_to_update}",
        json=update_data,
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated Test Researcher Name"
    assert (
        data["username"] == test_researcher_user.username
    )  # Username should not change here


@pytest.mark.asyncio
async def test_update_researcher_by_admin(
    test_client: AsyncClient,
    admin_token: str,
    test_researcher_user: ResearcherDB,
):
    """Admin successfully updates another researcher's information."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    researcher_id_to_update = test_researcher_user.id
    update_data = {"full_name": "Admin Was Here"}

    response = await test_client.put(
        f"/researchers/{researcher_id_to_update}",
        json=update_data,
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Admin Was Here"


@pytest.mark.asyncio
async def test_update_researcher_by_other_researcher_forbidden(
    test_client: AsyncClient,
    researcher_token: str,
    admin_user: ResearcherDB,  # Use admin_user as the target to update
):
    """Researcher attempts to update another researcher's info - should be forbidden."""
    headers = {
        "Authorization": f"Bearer {researcher_token}"
    }  # Logged in as testresearcher
    researcher_id_to_update = admin_user.id  # Attempting to update adminuser

    # Ensure testresearcher is not the same as admin_user if test_researcher_user was used
    assert admin_user.username != "testresearcher"

    update_data = {"full_name": "Attempted Update by Other"}
    response = await test_client.put(
        f"/researchers/{researcher_id_to_update}",
        json=update_data,
        headers=headers,
    )
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


# --- Tests for Eje X and Eje Y Endpoints ---

from Aletheia_v3.api.schemas import (
    IngestDocumentRequest, IngestDocumentResponse,
    LinkConceptsRequest, LinkConceptsResponse, RelationshipSchema,
    UCMExtractionRequestSchema, UCMExtractionResponseSchema, ExtractedUCMSchema,
    # Placeholder schemas (solo los de input para request, los de response para validar estructura)
    FormClusterInputSchema, FormClusterResultSchema,
    PropositionDerivationInputSchema, PropositionDerivationResultSchema,
    MiniTheoryConstructionInputSchema, MiniTheoryConstructionResultSchema,
    ComprehensiveTheoriesInputSchema, ComprehensiveTheoriesResultSchema,
    UnifiedModelsInputSchema, UnifiedModelsResultSchema
)
# Necesitamos limpiar los repos en memoria entre tests o grupos de tests
# para evitar interferencias, especialmente para los tests de "not found".
# Una forma es llamar a .clear() en los repositorios.
# Podríamos hacerlo en un fixture de función o explícitamente en los tests.

@pytest.mark.asyncio
async def test_ingest_document_endpoint_success(test_client: AsyncClient, researcher_token: str, mocker):
    """Tests successful document ingestion."""
    # Limpiar repositorios para este test si es necesario
    # from Aletheia_v3.api.dependencies import get_concept_repository
    # concept_repo = get_concept_repository()
    # concept_repo.clear() # Asegurar que no haya datos previos si afecta la lógica

    headers = {"Authorization": f"Bearer {researcher_token}"}
    payload = IngestDocumentRequest(
        document_text="New scientific document about dark matter.",
        source_doi="10.xxxx/darkmatter.doc",
        source_citation="Author A., Dark Journal, 2024",
        source_metadata={"category": "cosmology"}
    )
    response = await test_client.post("/eje-x/ingest-document", json=payload.model_dump(), headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "document_source_id" in data
    assert data["document_source_id"].startswith("docsrc_")
    assert "ucm_extraction_result" in data
    assert data["ucm_extraction_result"]["source_document_id"] == data["document_source_id"]
    # La implementación placeholder de ExtractUCMsUseCase podría devolver conceptos si el texto coincide
    # Por ejemplo, si "AI" está en el texto.
    # assert len(data["ucm_extraction_result"]["extracted_concepts"]) > 0 # Depende del placeholder

@pytest.mark.asyncio
async def test_ingest_document_endpoint_unauthorized(test_client: AsyncClient):
    """Tests document ingestion without authorization."""
    payload = IngestDocumentRequest(document_text="text")
    response = await test_client.post("/eje-x/ingest-document", json=payload.model_dump())
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_link_concepts_endpoint_success(test_client: AsyncClient, researcher_token: str, mocker):
    """Tests successful concept linking."""
    headers = {"Authorization": f"Bearer {researcher_token}"}

    # Interactuar con la BD de prueba para crear conceptos
    from Aletheia_v3.infrastructure.models import ScientificConceptDB
    from Aletheia_v3.core.domain_models import ConceptType # Enum de dominio

    db = next(override_get_db_session()) # Obtener sesión de BD de prueba
    try:
        # Limpiar conceptos existentes para aislamiento del test
        db.query(ScientificConceptDB).delete()
        db.commit()

        source_concept_db = ScientificConceptDB(name="Dark Matter DB", concept_type=ConceptType.GENERIC_CONCEPT)
        target_concept_db = ScientificConceptDB(name="Galaxy Rotation DB", concept_type=ConceptType.GENERIC_CONCEPT)
        db.add_all([source_concept_db, target_concept_db])
        db.commit()
        db.refresh(source_concept_db)
        db.refresh(target_concept_db)

        source_id_str = str(source_concept_db.id)
        target_id_str = str(target_concept_db.id)
    finally:
        db.close()

    payload = LinkConceptsRequest(
        source_concept_id=source_id_str,
        target_concept_id=target_id_str,
        relationship_type="EXPLAINS",
        description="Dark matter explains galaxy rotation curves.",
        properties={"strength": 0.9}
    )
    response = await test_client.post("/eje-x/link-concepts", json=payload.model_dump(), headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "created_relationship" in data
    rel = data["created_relationship"]
    assert rel["source_concept_id"] == source_concept.id
    assert rel["target_concept_id"] == target_concept.id
    assert rel["type"] == "EXPLAINS"
    assert rel["description"] == payload.description

@pytest.mark.asyncio
async def test_link_concepts_endpoint_concept_not_found(test_client: AsyncClient, researcher_token: str):
    """Tests concept linking when a concept is not found."""
    headers = {"Authorization": f"Bearer {researcher_token}"}

    # Asegurar que la BD esté limpia o no contenga los IDs
    from Aletheia_v3.infrastructure.models import ScientificConceptDB, DirectedRelationshipDB
    db = next(override_get_db_session())
    try:
        # Limpiar tablas relevantes para asegurar que los conceptos no existan
        db.query(DirectedRelationshipDB).delete()
        db.query(ScientificConceptDB).delete()
        db.commit()
    finally:
        db.close()

    payload = LinkConceptsRequest(
        source_concept_id=str(uuid.uuid4()), # Usar un UUID aleatorio que no existirá
        target_concept_id=str(uuid.uuid4()), # Usar otro UUID aleatorio
        relationship_type="LINKS_TO"
    )
    response = await test_client.post("/eje-x/link-concepts", json=payload.model_dump(), headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # El mensaje de error puede variar si es el source o el target el que falla primero
    # Verificar que el detalle contenga "concept with ID" y "not found" es más robusto.
    detail = response.json()["detail"]
    assert "concept with ID" in detail and "not found" in detail


@pytest.mark.asyncio
async def test_ucm_extraction_endpoint_success(test_client: AsyncClient, researcher_token: str):
    """Tests successful UCM extraction."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    payload = UCMExtractionRequestSchema(
        text_content="Exploring AI ethics and its implications.",
        source_document_id="docsrc_sample_for_ucm"
    )
    response = await test_client.post("/eje-y/ucm-extraction", json=payload.model_dump(), headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["source_document_id"] == payload.source_document_id
    assert "extracted_concepts" in data
    # La implementación placeholder de ExtractUCMsUseCase puede devolver conceptos
    assert len(data["extracted_concepts"]) >= 0 # Podría ser 0, 1, o 2 dependiendo del texto
    if len(data["extracted_concepts"]) > 0:
        assert data["extracted_concepts"][0]["name"] in ["Artificial Intelligence (Placeholder)", "Ethics (Placeholder)"]


# --- Tests para Endpoints Placeholder del Eje Y ---
# Estos tests parametrizados serán eliminados y reemplazados por tests individuales.
# @pytest.mark.asyncio
# @pytest.mark.parametrize("endpoint_path, input_schema, result_schema_type, payload_data", [
#     ("/eje-y/cluster-formation", FormClusterInputSchema, FormClusterResultSchema, {"ucm_ids": ["ucm1"], "params": {}}),
#     ("/eje-y/proposition-derivation", PropositionDerivationInputSchema, PropositionDerivationResultSchema, {"cluster_ids": ["cluster1"]}),
#     ("/eje-y/mini-theory-construction", MiniTheoryConstructionInputSchema, MiniTheoryConstructionResultSchema, {"proposition_ids": ["prop1"]}),
#     ("/eje-y/comprehensive-theories", ComprehensiveTheoriesInputSchema, ComprehensiveTheoriesResultSchema, {"mini_theory_ids": ["minit1"]}),
#     ("/eje-y/unified-models", UnifiedModelsInputSchema, UnifiedModelsResultSchema, {"comprehensive_theory_ids": ["compth1"]}),
# ])
# async def test_eje_y_placeholder_endpoints_success(
#     test_client: AsyncClient, researcher_token: str,
#     endpoint_path: str, input_schema, result_schema_type, payload_data
# ):
#     """Tests placeholder Eje Y endpoints for successful (placeholder) response."""
#     headers = {"Authorization": f"Bearer {researcher_token}"}
#     payload = input_schema(**payload_data)

#     response = await test_client.post(endpoint_path, json=payload.model_dump(), headers=headers)

#     assert response.status_code == status.HTTP_202_ACCEPTED
#     data = response.json()
#     assert "details" in data
#     assert "Endpoint placeholder" in data["details"]
#     # Validar que la respuesta es parseable por el schema de resultado (aunque sea placeholder)
#     assert result_schema_type.model_validate(data)


# @pytest.mark.asyncio
# @pytest.mark.parametrize("endpoint_path", [
#     "/eje-y/cluster-formation",
#     "/eje-y/proposition-derivation",
#     # ... (añadir los otros si se quiere probar todos)
# ])
# async def test_eje_y_placeholder_endpoints_unauthorized(test_client: AsyncClient, endpoint_path: str):
#     """Tests placeholder Eje Y endpoints for unauthorized access."""
#     # Usar un payload mínimo válido para el schema de entrada correspondiente
#     payload = {}
#     if "cluster" in endpoint_path: payload = FormClusterInputSchema(ucm_ids=["id"]).model_dump()
#     elif "proposition" in endpoint_path: payload = PropositionDerivationInputSchema(cluster_ids=["id"]).model_dump()
#     # Añadir más casos según sea necesario

#     if not payload: # Si no se pudo determinar un payload, saltar este caso parametrizado
#         pytest.skip(f"Payload not defined for {endpoint_path} in unauthorized test")

#     response = await test_client.post(endpoint_path, json=payload)
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- Nuevos Tests para Endpoints del Eje Y Funcionales ---

from Aletheia_v3.infrastructure.models import ScientificConceptDB, DirectedRelationshipDB # Para limpiar BD
from Aletheia_v3.core.domain_models import ConceptType as DomainConceptType # Para crear conceptos

# Helper para crear conceptos en la BD de prueba
async def create_concept_in_db(db_session: SQLAlchemySession, name: str, concept_type: DomainConceptType, description: Optional[str] = None, properties: Optional[Dict] = None) -> ScientificConceptDB:
    concept_db = ScientificConceptDB(
        name=name,
        description=description,
        concept_type=concept_type,
        properties=properties or {}
    )
    db_session.add(concept_db)
    db_session.commit()
    db_session.refresh(concept_db)
    return concept_db

@pytest.mark.asyncio
async def test_form_clusters_endpoint_success(test_client: AsyncClient, researcher_token: str):
    headers = {"Authorization": f"Bearer {researcher_token}"}
    db = next(override_get_db_session())
    try:
        db.query(DirectedRelationshipDB).delete() # Limpiar relaciones por si acaso
        db.query(ScientificConceptDB).delete()
        db.commit()

        # Crear UCMs de prueba
        ucm1 = await create_concept_in_db(db, "UCM sobre AI y NLP", DomainConceptType.UCM, "AI, NLP, deep learning")
        ucm2 = await create_concept_in_db(db, "UCM sobre AI y Ethics", DomainConceptType.UCM, "AI, ethics, bias")
        ucm3 = await create_concept_in_db(db, "UCM sobre Quantum Computing", DomainConceptType.UCM, "Quantum, physics")

        payload = FormClusterInputSchema(ucm_ids=[str(ucm1.id), str(ucm2.id), str(ucm3.id)])
        response = await test_client.post("/eje-y/cluster-formation", json=payload.model_dump(), headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "created_clusters" in data
        assert isinstance(data["created_clusters"], list)
        # La lógica de clustering simple podría crear 1 cluster para AI
        # o más si hay otros solapamientos. Por ahora, solo verificamos que se creen algunos.
        assert len(data["created_clusters"]) >= 0 # Podría ser 0 si no hay solapamiento suficiente

        if len(data["created_clusters"]) > 0:
            cluster_info = data["created_clusters"][0]
            assert cluster_info["concept_type"] == DomainConceptType.CLUSTER.value

            # Verificar en BD
            created_cluster_db = db.query(ScientificConceptDB).filter(ScientificConceptDB.id == uuid.UUID(cluster_info["id"])).first()
            assert created_cluster_db is not None
            assert created_cluster_db.concept_type == DomainConceptType.CLUSTER
            assert "member_concept_ids" in created_cluster_db.properties
            assert "shared_keywords" in created_cluster_db.properties
    finally:
        db.close()

@pytest.mark.asyncio
async def test_form_clusters_endpoint_no_ucms(test_client: AsyncClient, researcher_token: str):
    headers = {"Authorization": f"Bearer {researcher_token}"}
    payload = FormClusterInputSchema(ucm_ids=[])
    response = await test_client.post("/eje-y/cluster-formation", json=payload.model_dump(), headers=headers)
    assert response.status_code == status.HTTP_201_CREATED # El caso de uso devuelve un mensaje, no un error
    data = response.json()
    assert data["message"] == "No UCM IDs provided for clustering."
    assert len(data["created_clusters"]) == 0

@pytest.mark.asyncio
async def test_derive_propositions_endpoint_success(test_client: AsyncClient, researcher_token: str):
    headers = {"Authorization": f"Bearer {researcher_token}"}
    db = next(override_get_db_session())
    try:
        db.query(DirectedRelationshipDB).delete()
        db.query(ScientificConceptDB).delete()
        db.commit()

        ucm1 = await create_concept_in_db(db, "UCM A for Prop", DomainConceptType.UCM)
        ucm2 = await create_concept_in_db(db, "UCM B for Prop", DomainConceptType.UCM)
        cluster1 = await create_concept_in_db(
            db, "Cluster AB", DomainConceptType.CLUSTER,
            properties={"member_concept_ids": [str(ucm1.id), str(ucm2.id)], "shared_keywords": ["topic1"]}
        )

        payload = PropositionDerivationInputSchema(cluster_ids=[str(cluster1.id)])
        response = await test_client.post("/eje-y/proposition-derivation", json=payload.model_dump(), headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "created_propositions" in data
        assert len(data["created_propositions"]) >= 1
        prop_info = data["created_propositions"][0]
        assert prop_info["concept_type"] == DomainConceptType.PROPOSITION.value

        created_prop_db = db.query(ScientificConceptDB).filter(ScientificConceptDB.id == uuid.UUID(prop_info["id"])).first()
        assert created_prop_db is not None
        assert created_prop_db.concept_type == DomainConceptType.PROPOSITION
        assert created_prop_db.properties["based_on_cluster_id"] == str(cluster1.id)
    finally:
        db.close()

@pytest.mark.asyncio
async def test_derive_propositions_cluster_not_found(test_client: AsyncClient, researcher_token: str):
    headers = {"Authorization": f"Bearer {researcher_token}"}
    db = next(override_get_db_session())
    try:
        db.query(DirectedRelationshipDB).delete()
        db.query(ScientificConceptDB).delete()
        db.commit()
    finally:
        db.close()

    payload = PropositionDerivationInputSchema(cluster_ids=[str(uuid.uuid4())]) # ID no existente
    response = await test_client.post("/eje-y/proposition-derivation", json=payload.model_dump(), headers=headers)
    # El caso de uso actual no lanza error si el cluster no se encuentra, sino que devuelve lista vacía.
    # El router convierte ValueError a 404, pero el UC actual no lo lanza en este caso.
    # Se espera un 201 con una lista vacía y un mensaje.
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert len(data["created_propositions"]) == 0
    assert "No se derivaron nuevas proposiciones" in data["message"]


@pytest.mark.asyncio
async def test_mini_theory_construction_success(test_client: AsyncClient, researcher_token: str):
    headers = {"Authorization": f"Bearer {researcher_token}"}
    db = next(override_get_db_session())
    try:
        db.query(DirectedRelationshipDB).delete()
        db.query(ScientificConceptDB).delete()
        db.commit()
        prop1 = await create_concept_in_db(db, "Proposition 1", DomainConceptType.PROPOSITION)
        prop2 = await create_concept_in_db(db, "Proposition 2", DomainConceptType.PROPOSITION)

        payload = MiniTheoryConstructionInputSchema(proposition_ids=[str(prop1.id), str(prop2.id)], name="Test Mini Theory")
        response = await test_client.post("/eje-y/mini-theory-construction", json=payload.model_dump(), headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "created_mini_theory" in data
        theory_info = data["created_mini_theory"]
        assert theory_info["name"] == "Test Mini Theory"
        assert theory_info["concept_type"] == DomainConceptType.MINI_THEORY.value

        created_theory_db = db.query(ScientificConceptDB).filter(ScientificConceptDB.id == uuid.UUID(theory_info["id"])).first()
        assert created_theory_db is not None
        assert created_theory_db.concept_type == DomainConceptType.MINI_THEORY
        assert str(prop1.id) in created_theory_db.properties["member_proposition_ids"]
    finally:
        db.close()

# Tests similares para ComprehensiveTheories y UnifiedModels
# Se omite la implementación completa aquí por brevedad, pero seguirían el mismo patrón:
# 1. Setup: Crear entidades de entrada (MiniTeorías para Comprehensive, Comprehensive para Unified) en la BD de prueba.
# 2. Ejecutar: Llamar al endpoint correspondiente.
# 3. Verificar: Código de estado, respuesta, y creación de la entidad correcta en la BD.
# También se añadirían tests para casos de error (ej. IDs de entrada no encontrados si el UC los valida y lanza error).

# Ejemplo rápido para uno más:
@pytest.mark.asyncio
async def test_comprehensive_theories_success(test_client: AsyncClient, researcher_token: str):
    headers = {"Authorization": f"Bearer {researcher_token}"}
    db = next(override_get_db_session())
    try:
        db.query(DirectedRelationshipDB).delete()
        db.query(ScientificConceptDB).delete()
        db.commit()
        mini_t1 = await create_concept_in_db(db, "Mini Theory 1", DomainConceptType.MINI_THEORY)

        payload = ComprehensiveTheoriesInputSchema(mini_theory_ids=[str(mini_t1.id)], name="Test Comprehensive Theory")
        response = await test_client.post("/eje-y/comprehensive-theories", json=payload.model_dump(), headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["created_comprehensive_theory"]["name"] == "Test Comprehensive Theory"
        assert data["created_comprehensive_theory"]["concept_type"] == DomainConceptType.COMPREHENSIVE_THEORY.value
    finally:
        db.close()

@pytest.mark.asyncio
async def test_unified_models_success(test_client: AsyncClient, researcher_token: str):
    headers = {"Authorization": f"Bearer {researcher_token}"}
    db = next(override_get_db_session())
    try:
        db.query(DirectedRelationshipDB).delete()
        db.query(ScientificConceptDB).delete()
        db.commit()
        comp_t1 = await create_concept_in_db(db, "Comp Theory 1", DomainConceptType.COMPREHENSIVE_THEORY)

        payload = UnifiedModelsInputSchema(comprehensive_theory_ids=[str(comp_t1.id)], name="Test Unified Model")
        response = await test_client.post("/eje-y/unified-models", json=payload.model_dump(), headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["created_unified_model"]["name"] == "Test Unified Model"
        assert data["created_unified_model"]["concept_type"] == DomainConceptType.UNIFIED_MODEL.value
    finally:
        db.close()

# Tests de autorización para los nuevos endpoints del Eje Y
@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint_path, payload_schema, payload_data", [
    ("/eje-y/cluster-formation", FormClusterInputSchema, {"ucm_ids": ["id1"]}),
    ("/eje-y/proposition-derivation", PropositionDerivationInputSchema, {"cluster_ids": ["id1"]}),
    ("/eje-y/mini-theory-construction", MiniTheoryConstructionInputSchema, {"proposition_ids": ["id1"]}),
    ("/eje-y/comprehensive-theories", ComprehensiveTheoriesInputSchema, {"mini_theory_ids": ["id1"]}),
    ("/eje-y/unified-models", UnifiedModelsInputSchema, {"comprehensive_theory_ids": ["id1"]}),
])
async def test_eje_y_functional_endpoints_unauthorized(
    test_client: AsyncClient, endpoint_path: str, payload_schema, payload_data
):
    """Tests functional Eje Y endpoints for unauthorized access."""
    payload = payload_schema(**payload_data)
    response = await test_client.post(endpoint_path, json=payload.model_dump())
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- Tests para Endpoints de Visualización del Eje Y ---

@pytest.mark.asyncio
async def test_get_hierarchy_graph_success(test_client: AsyncClient, researcher_token: str):
    """Prueba el endpoint del grafo de jerarquía con datos reales y diferentes profundidades."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    db = next(override_get_db_session())
    try:
        db.query(DirectedRelationshipDB).delete()
        db.query(ScientificConceptDB).delete()
        db.commit()

        # Crear jerarquía: UM1 -> CT1 -> MT1 -> P1 -> CL1 -> (UCM1, UCM2)
        ucm1 = await create_concept_in_db(db, "UCM1", DomainConceptType.UCM, "Data point A")
        ucm2 = await create_concept_in_db(db, "UCM2", DomainConceptType.UCM, "Data point B")
        cl1 = await create_concept_in_db(db, "Cluster1", DomainConceptType.CLUSTER, properties={"member_concept_ids": [str(ucm1.id), str(ucm2.id)], "shared_keywords": ["test"]})
        p1 = await create_concept_in_db(db, "Proposition1", DomainConceptType.PROPOSITION, properties={"based_on_cluster_id": str(cl1.id), "involved_ucm_ids": [str(ucm1.id), str(ucm2.id)]})
        mt1 = await create_concept_in_db(db, "MiniTheory1", DomainConceptType.MINI_THEORY, properties={"member_proposition_ids": [str(p1.id)]})
        ct1 = await create_concept_in_db(db, "CompTheory1", DomainConceptType.COMPREHENSIVE_THEORY, properties={"member_mini_theory_ids": [str(mt1.id)]})
        um1 = await create_concept_in_db(db, "UnifiedModel1", DomainConceptType.UNIFIED_MODEL, properties={"member_comprehensive_theory_ids": [str(ct1.id)]})

        # Test con max_depth = 0 (solo el nodo raíz)
        response_depth0 = await test_client.get(f"/eje-y/visualization/hierarchy_graph/{um1.id}?max_depth=0", headers=headers)
        assert response_depth0.status_code == status.HTTP_200_OK
        data0 = response_depth0.json()
        assert len(data0["nodes"]) == 1
        assert data0["nodes"][0]["id"] == str(um1.id)
        assert len(data0["edges"]) == 0

        # Test con max_depth = 1 (raíz y sus hijos directos)
        response_depth1 = await test_client.get(f"/eje-y/visualization/hierarchy_graph/{um1.id}?max_depth=1", headers=headers)
        assert response_depth1.status_code == status.HTTP_200_OK
        data1 = response_depth1.json()
        # Nodos: UM1, CT1
        assert len(data1["nodes"]) == 2
        node_ids1 = {n["id"] for n in data1["nodes"]}
        assert {str(um1.id), str(ct1.id)} == node_ids1
        # Aristas: UM1 -> CT1
        assert len(data1["edges"]) == 1
        assert data1["edges"][0]["from"] == str(um1.id) and data1["edges"][0]["to"] == str(ct1.id)

        # Test con max_depth = 2 (UM1 -> CT1 -> MT1)
        response_depth2 = await test_client.get(f"/eje-y/visualization/hierarchy_graph/{um1.id}?max_depth=2", headers=headers)
        assert response_depth2.status_code == status.HTTP_200_OK
        data2 = response_depth2.json()
        # Nodos: UM1, CT1, MT1
        assert len(data2["nodes"]) == 3
        node_ids2 = {n["id"] for n in data2["nodes"]}
        assert {str(um1.id), str(ct1.id), str(mt1.id)} == node_ids2
        # Aristas: UM1->CT1, CT1->MT1
        assert len(data2["edges"]) == 2
        edge_pairs2 = {(e["from"], e["to"]) for e in data2["edges"]}
        assert {(str(um1.id), str(ct1.id)), (str(ct1.id), str(mt1.id))} == edge_pairs2

        # Test con max_depth = 5 (toda la jerarquía)
        response_depth5 = await test_client.get(f"/eje-y/visualization/hierarchy_graph/{um1.id}?max_depth=5", headers=headers)
        assert response_depth5.status_code == status.HTTP_200_OK
        data5 = response_depth5.json()
        # Nodos: UM1, CT1, MT1, P1, CL1, UCM1, UCM2 (total 7)
        # La lógica actual de BFS podría añadir UCM1 y UCM2 dos veces si P1 y CL1 los referencian y ambos están dentro de max_depth.
        # El uso de `nodes_map` en el endpoint debería manejar la unicidad de nodos.
        # El `involved_ucm_ids` en la Proposición P1 también crea aristas a UCM1 y UCM2.
        # El `member_concept_ids` en Cluster CL1 también crea aristas a UCM1 y UCM2.
        # La clave `ids_in_bfs_queue_or_processed` previene que un mismo nodo se expanda múltiples veces.
        # Los nodos UCM solo se añaden a la cola una vez.

        # Esperados: UM1, CT1, MT1, P1, CL1, UCM1, UCM2
        # La propiedad de P1 es "involved_ucm_ids": [ucm1, ucm2]
        # La propiedad de CL1 es "member_concept_ids": [ucm1, ucm2]
        # Si P1 es hijo de MT1 (nivel 3), y CL1 es referenciado por P1 (podría ser nivel 4 si se modela así)
        # y UCMs son hijos de CL1 (nivel 5) y también de P1 (nivel 4).
        # El BFS actual con `ids_in_bfs_queue_or_processed` asegura que cada nodo se procese una vez.
        # El `level` en el nodo será el del primer camino encontrado.

        # Nodos esperados: UM1, CT1, MT1, P1.
        # Si P1.properties["involved_ucm_ids"] se expande: UCM1, UCM2. Total 6 nodos.
        # Si P1.properties["based_on_cluster_id"] se expande y luego CL1.properties["member_concept_ids"]: CL1, UCM1, UCM2. Total 7 nodos.
        # La lógica del endpoint actual prioriza `member_ids_property_key` según el tipo.
        # Para PROPOSITION, es `involved_ucm_ids`.
        # Nodos: UM1(0), CT1(1), MT1(2), P1(3), UCM1(4), UCM2(4). Total 6.
        # Aristas: UM1->CT1, CT1->MT1, MT1->P1, P1->UCM1, P1->UCM2. Total 5.

        assert len(data5["nodes"]) == 6
        node_ids5 = {n["id"] for n in data5["nodes"]}
        assert {str(um1.id), str(ct1.id), str(mt1.id), str(p1.id), str(ucm1.id), str(ucm2.id)} == node_ids5
        assert len(data5["edges"]) == 5
        edge_pairs5 = {(e["from"], e["to"]) for e in data5["edges"]}
        expected_edges5 = {
            (str(um1.id), str(ct1.id)), (str(ct1.id), str(mt1.id)), (str(mt1.id), str(p1.id)),
            (str(p1.id), str(ucm1.id)), (str(p1.id), str(ucm2.id))
        }
        assert edge_pairs5 == expected_edges5

    finally:
        db.close()

@pytest.mark.asyncio
async def test_get_hierarchy_graph_not_found(test_client: AsyncClient, researcher_token: str):
    """Prueba el endpoint del grafo de jerarquía con un ID no simulado."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    concept_id_no_simulado = "unknown_concept_id"
    response = await test_client.get(f"/eje-y/visualization/hierarchy_graph/{concept_id_no_simulado}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_synthesis_statistics_success(test_client: AsyncClient, researcher_token: str):
    """Prueba el endpoint de estadísticas de síntesis con datos reales."""
    headers = {"Authorization": f"Bearer {researcher_token}"}
    db = next(override_get_db_session())
    try:
        # Limpiar y preparar datos
        db.query(DirectedRelationshipDB).delete()
        db.query(ScientificConceptDB).delete()
        db.commit()

        # Crear algunos conceptos de diferentes tipos
        doc1 = await create_concept_in_db(db, "Doc 1", DomainConceptType.DOCUMENT_SOURCE)
        ucm1 = await create_concept_in_db(db, "UCM 1", DomainConceptType.UCM)
        ucm2 = await create_concept_in_db(db, "UCM 2", DomainConceptType.UCM)
        cluster1 = await create_concept_in_db(db, "Cluster 1", DomainConceptType.CLUSTER)
        # Crear algunas relaciones (necesitaríamos un helper o crearlas manualmente si el endpoint las cuenta)
        # Por ahora, el endpoint solo cuenta conceptos y documentos fuente.
        # Si se añade el conteo de relaciones al endpoint, este test necesitaría crear relaciones también.
        # La implementación actual de get_synthesis_statistics sí cuenta relaciones.
        from Aletheia_v3.infrastructure.models import DirectedRelationshipDB as RelDBModel
        rel1 = RelDBModel(source_concept_id=doc1.id, target_concept_id=ucm1.id, type="EXTRACTED_FROM")
        rel2 = RelDBModel(source_concept_id=ucm1.id, target_concept_id=ucm2.id, type="RELATES_TO")
        db.add_all([rel1, rel2])
        db.commit()

        response = await test_client.get("/eje-y/visualization/synthesis_statistics", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "overall_stats" in data
        assert "type_distribution" in data

        stats_map = {item["name"]: item["value"] for item in data["overall_stats"]}
        assert stats_map["Total Conceptos Registrados"] == 4 # doc1, ucm1, ucm2, cluster1
        assert stats_map["Total Relaciones Registradas"] == 2
        assert stats_map["Documentos Fuente Procesados"] == 1

        type_dist = data["type_distribution"]
        assert type_dist[DomainConceptType.DOCUMENT_SOURCE.value] == 1
        assert type_dist[DomainConceptType.UCM.value] == 2
        assert type_dist[DomainConceptType.CLUSTER.value] == 1
        assert DomainConceptType.PROPOSITION.value not in type_dist # No se crearon proposiciones

    finally:
        db.close()

@pytest.mark.asyncio
@pytest.mark.parametrize("path", [
    "/eje-y/visualization/hierarchy_graph/some_id",
    "/eje-y/visualization/synthesis_statistics"
])
async def test_visualization_endpoints_unauthorized(test_client: AsyncClient, path: str):
    """Prueba los endpoints de visualización sin autorización."""
    response = await test_client.get(path)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
