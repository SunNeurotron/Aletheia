import pytest
from typing import List, Dict, Any, Optional, Generator
from uuid import uuid4, UUID
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession # For type hinting if needed

# Application components to test or mock
from aletheia_stats.aletheia_stats.main import app # Main FastAPI app
from aletheia_stats.aletheia_stats.domain.entities import Experiment as DomainExperiment, TTestResult as DomainTTestResult
from aletheia_stats.aletheia_stats.application.use_cases import PerformTTestUseCase
from aletheia_stats.aletheia_stats.domain.services import StatsService
from aletheia_stats.aletheia_stats.infrastructure.sqlalchemy_repository import SQLAlchemyStatsRepository
from aletheia_stats.aletheia_stats.infrastructure.mlflow_tracker import MLflowExperimentTracker

# --- Test Client Fixture ---
@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Provides a TestClient for the FastAPI application."""
    with TestClient(app) as c:
        yield c

# --- Mock Dependencies ---
# We'll mock the dependencies of PerformTTestUseCase:
# - StatsService (can use real one as it's pure Python)
# - SQLAlchemyStatsRepository (mocked to avoid DB dependency in this test)
# - MLflowExperimentTracker (mocked to avoid MLflow server dependency)

@pytest.fixture
def mock_stats_service() -> StatsService:
    """Provides a real StatsService instance, as it's self-contained."""
    return StatsService(random_state=42)

@pytest.fixture
def mock_stats_repository() -> MagicMock:
    """Mocks SQLAlchemyStatsRepository."""
    mock = MagicMock(spec=SQLAlchemyStatsRepository)
    mock.save = MagicMock()
    mock.get_by_id = MagicMock(return_value=None) # Default to not found
    mock.list_all = MagicMock(return_value=[])
    return mock

@pytest.fixture
def mock_mlflow_tracker() -> MagicMock:
    """Mocks MLflowExperimentTracker."""
    mock = MagicMock(spec=MLflowExperimentTracker)
    mock.start_run = MagicMock(return_value="mock_mlflow_run_id_123")
    mock.log_param = MagicMock()
    mock.log_params = MagicMock()
    mock.log_metric = MagicMock()
    mock.log_metrics = MagicMock()
    mock.set_tag = MagicMock()
    mock.set_tags = MagicMock()
    mock.end_run = MagicMock()
    mock.active_run_id = "mock_mlflow_run_id_123" # Property mock
    return mock

# --- Override Dependencies for Testing ---
# This uses FastAPI's dependency overriding mechanism.
# These overrides will apply to all tests using the `client` fixture in this module.

# We need to know how dependencies are provided in api.py to override them.
# Assuming api.py has functions like get_stats_service, get_stats_repository, etc.
# that are used with Depends().

# If api.py uses global instances, patching them directly is another option,
# but dependency overrides are cleaner.

# Let's assume `aletheia_stats.aletheia_stats.presentation.api` has these provider functions:
# - get_perform_ttest_use_case
# - get_stats_service (indirectly used by use_case)
# - get_stats_repository (indirectly used by use_case)
# - get_mlflow_tracker (indirectly used by use_case)

# We will override the providers for the repository and tracker at the `app` level.
# The `PerformTTestUseCase` will then be constructed with these mocks.

@pytest.fixture(autouse=True) # Apply to all tests in this module
def override_api_dependencies(
    mock_stats_repository: MagicMock,
    mock_mlflow_tracker: MagicMock,
    # mock_stats_service: StatsService # Real service, but ensure it's the one use_case gets
):
    # Assuming your api.py has provider functions like these for Depends()
    from aletheia_stats.aletheia_stats.presentation import api as presentation_api

    app.dependency_overrides[presentation_api.get_stats_repository] = lambda: mock_stats_repository
    app.dependency_overrides[presentation_api.get_mlflow_tracker] = lambda: mock_mlflow_tracker
    # app.dependency_overrides[presentation_api.get_stats_service] = lambda: mock_stats_service # Use real service

    yield # Run the tests

    app.dependency_overrides = {} # Clear overrides after tests


# --- Helper to get a valid token (mocked) ---
def get_mock_auth_token(client: TestClient, username: str = "testuser", password: str = "testpassword") -> str:
    """Helper to get a mock JWT token."""
    response = client.post("/api/v1/token", data={"username": username, "password": password})
    assert response.status_code == 200, f"Failed to get token: {response.text}"
    return response.json()["access_token"]


# --- Test Cases ---

def test_analyze_ttest_endpoint_success(
    client: TestClient,
    mock_stats_repository: MagicMock,
    mock_mlflow_tracker: MagicMock
):
    """Test the /analyze/ttest endpoint for a successful analysis."""
    token = get_mock_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    request_payload = {
        "group_a": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6],
        "group_b": [2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6],
        "experiment_name": "Integration Test Exp",
        "alpha": 0.05
    }

    response = client.post("/api/v1/analyze/ttest", json=request_payload, headers=headers)

    # Assertions
    assert response.status_code == 201, f"Response: {response.text}"
    data = response.json()

    assert "id" in data
    assert data["name"] == "Integration Test Exp"
    assert data["parameters"]["alpha"] == 0.05
    assert data["mlflow_run_id"] == "mock_mlflow_run_id_123" # From mock

    assert "result" in data
    result_data = data["result"]
    assert "p_value" in result_data
    assert "statistic" in result_data
    assert result_data["is_significant_05"] is True # For these data, expect significance
    assert result_data["normality_p_value_group_a"] > 0.05 # Expect normality for these data
    assert result_data["normality_p_value_group_b"] > 0.05

    # Check if repository save was called
    mock_stats_repository.save.assert_called_once()
    saved_experiment_arg = mock_stats_repository.save.call_args[0][0]
    assert isinstance(saved_experiment_arg, DomainExperiment)
    assert saved_experiment_arg.id == UUID(data["id"])
    assert saved_experiment_arg.name == "Integration Test Exp"

    # Check MLflow interactions
    mock_mlflow_tracker.start_run.assert_called_once()
    mock_mlflow_tracker.log_params.assert_called()
    mock_mlflow_tracker.log_metrics.assert_called()
    mock_mlflow_tracker.set_tag.assert_any_call("status", "SUCCESS") # Check for success tag
    mock_mlflow_tracker.end_run.assert_called_once()


def test_analyze_ttest_endpoint_insufficient_data(client: TestClient):
    """Test /analyze/ttest with data that's insufficient for analysis (ValueError)."""
    token = get_mock_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    request_payload = {
        "group_a": [1.0, 1.1], # Less than 3 samples
        "group_b": [2.0, 2.1, 2.2],
        "experiment_name": "Insufficient Data Test"
    }

    response = client.post("/api/v1/analyze/ttest", json=request_payload, headers=headers)

    assert response.status_code == 400 # Bad Request
    assert "Each group must contain at least three observations" in response.json()["detail"]


def test_analyze_ttest_endpoint_non_normal_data_comment(
    client: TestClient, mock_mlflow_tracker: MagicMock
):
    """Test that non-normal data results in appropriate comments and MLflow tags."""
    token = get_mock_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Data designed to likely fail Shapiro-Wilk
    group_a_non_normal = [1,1,1,1,1,1,1,1,1,100]
    group_b_normal = [5,6,7,5,6,7,5,6,7,6]

    request_payload = {
        "group_a": group_a_non_normal,
        "group_b": group_b_normal,
        "experiment_name": "Non-Normal Data Test"
    }

    response = client.post("/api/v1/analyze/ttest", json=request_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()

    assert "result" in data and data["result"] is not None
    assert "Group A may not be normally distributed" in data["result"]["comment"]

    # Check if MLflow tag for comment was set
    # This requires inspecting call_args_list if multiple tags are set
    # For simplicity, we'll check if set_tag was called with a key related to comment
    comment_tag_found = False
    for call in mock_mlflow_tracker.set_tag.call_args_list:
        if call[0][0] == "analysis_comment" and "Group A may not be normally distributed" in call[0][1]:
            comment_tag_found = True
            break
    assert comment_tag_found


def test_analyze_ttest_no_auth(client: TestClient):
    """Test endpoint access without authentication token."""
    request_payload = {"group_a": [1,2,3,4,5], "group_b": [6,7,8,9,10]}
    response = client.post("/api/v1/analyze/ttest", json=request_payload)
    assert response.status_code == 401 # Unauthorized (or 403 if Depends on scheme directly)
    assert response.json()["detail"] == "Not authenticated" # Or specific message from OAuth2PasswordBearer


def test_analyze_ttest_insufficient_role(client: TestClient):
    """Test endpoint access with a user having insufficient roles."""
    # Assuming "vieweruser" exists and has only "viewer" role (not "analyst")
    # Need to adjust mock_users_db in api.py or mock token generation for this.
    # For this example, let's assume we can generate a token for a "viewer"

    # This requires modifying the mock_users_db in presentation.api or mocking token creation logic.
    # For now, we'll assume the "testuser" used by get_mock_auth_token has "analyst".
    # To test this properly, we'd need a way to get a token for a user *without* "analyst" role.

    # If we had a "vieweruser" with password "viewpassword" and only "viewer" role:
    # token = get_mock_auth_token(client, username="vieweruser", password="viewpassword")
    # headers = {"Authorization": f"Bearer {token}"}
    # request_payload = {"group_a": [1,2,3,4,5], "group_b": [6,7,8,9,10]}
    # response = client.post("/api/v1/analyze/ttest", json=request_payload, headers=headers)
    # assert response.status_code == 403 # Forbidden
    # assert "Insufficient permissions" in response.json()["detail"]
    pytest.skip("Skipping insufficient role test for /analyze/ttest as it requires more complex auth mocking setup for roles.")


# --- Tests for /experiments/{experiment_id} and /experiments ---

@pytest.fixture
def sample_domain_experiment() -> DomainExperiment:
    """A sample domain experiment for mocking repository returns."""
    exp_id = uuid4()
    return DomainExperiment(
        id=exp_id,
        name="Sample Repo Exp",
        group_a_data=[1,2,3],
        group_b_data=[4,5,6],
        parameters={"alpha": 0.05},
        result=DomainTTestResult(
            statistic=-5.196, p_value=0.003, degrees_freedom=4.0,
            confidence_interval_95=(-4.577, -1.423),
            mean_group_a=2.0, mean_group_b=5.0, variance_group_a=1.0, variance_group_b=1.0,
            is_significant_05=True, normality_p_value_group_a=0.6, normality_p_value_group_b=0.6,
            comment="Test comment"
        ),
        mlflow_run_id="mlf_repo_test_1"
    )

def test_get_experiment_by_id_success(
    client: TestClient, mock_stats_repository: MagicMock, sample_domain_experiment: DomainExperiment
):
    token = get_mock_auth_token(client) # "testuser" has "analyst" role, which includes "viewer"
    headers = {"Authorization": f"Bearer {token}"}

    exp_id = sample_domain_experiment.id
    mock_stats_repository.get_by_id.return_value = sample_domain_experiment

    response = client.get(f"/api/v1/experiments/{exp_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(exp_id)
    assert data["name"] == "Sample Repo Exp"
    assert data["result"]["p_value"] == 0.003
    mock_stats_repository.get_by_id.assert_called_once_with(exp_id)


def test_get_experiment_by_id_not_found(client: TestClient, mock_stats_repository: MagicMock):
    token = get_mock_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    non_existent_id = uuid4()
    mock_stats_repository.get_by_id.return_value = None # Ensure mock returns None

    response = client.get(f"/api/v1/experiments/{non_existent_id}", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"
    mock_stats_repository.get_by_id.assert_called_once_with(non_existent_id)


def test_list_experiments_success(
    client: TestClient, mock_stats_repository: MagicMock, sample_domain_experiment: DomainExperiment
):
    token = get_mock_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a second sample experiment for the list
    exp2_id = uuid4()
    exp2 = DomainExperiment(id=exp2_id, name="Exp Two", group_a_data=[0], group_b_data=[1])
    mock_stats_repository.list_all.return_value = [sample_domain_experiment, exp2]

    response = client.get("/api/v1/experiments?skip=0&limit=10", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == str(sample_domain_experiment.id)
    assert data[1]["id"] == str(exp2_id)
    mock_stats_repository.list_all.assert_called_once_with(limit=10, offset=0)


def test_health_check_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to Aletheia-Stats API" in response.json()["message"]
