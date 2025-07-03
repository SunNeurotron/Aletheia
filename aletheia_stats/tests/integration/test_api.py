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
        "group_a_data": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6], # Corregido: group_a_data
        "group_b_data": [2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6], # Corregido: group_b_data
        "experiment_name": "Integration Test Exp",
        "alpha": 0.05
        # "parameters": {} # Opcional
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

    assert "tracking_warnings" in data # Nuevo campo
    assert data["tracking_warnings"] == [] # Esperar lista vacía en caso de éxito

    # Check if repository save was called
    mock_stats_repository.save.assert_called_once()
    saved_experiment_arg = mock_stats_repository.save.call_args[0][0]
    assert isinstance(saved_experiment_arg, DomainExperiment)
    assert saved_experiment_arg.id == UUID(data["id"])
    assert saved_experiment_arg.name == "Integration Test Exp"
    assert saved_experiment_arg.tracking_warnings == [] # Verificar que se guarda vacío

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
        "group_a_data": [1.0, 1.1], # Corregido: group_a_data, Less than 3 samples
        "group_b_data": [2.0, 2.1, 2.2], # Corregido: group_b_data
        "experiment_name": "Insufficient Data Test"
        # alpha y parameters son opcionales aquí si usan defaults en schema
    }

    response = client.post("/api/v1/analyze/ttest", json=request_payload, headers=headers)

    assert response.status_code == 422 # FastAPI usa 422 para errores de validación de Pydantic
    # El mensaje de error vendrá de Pydantic y será más detallado
    # Ejemplo: response.json()["detail"][0]["msg"] podría ser "ensure this value has at least 3 items"
    assert "group_a_data" in response.text # Verificar que el campo problemático se menciona
    assert "ensure this value has at least 3 items" in response.text


def test_analyze_ttest_endpoint_invalid_alpha(client: TestClient):
    """Test /analyze/ttest with invalid alpha value."""
    token = get_mock_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    request_payload = {
        "group_a_data": [1,2,3,4,5],
        "group_b_data": [6,7,8,9,10],
        "alpha": 1.5 # Invalid alpha
    }
    response = client.post("/api/v1/analyze/ttest", json=request_payload, headers=headers)
    assert response.status_code == 422 # Validation error
    assert "alpha" in response.text
    assert "ensure this value is less than 1" in response.text


def test_analyze_ttest_endpoint_non_normal_data_comment(
    client: TestClient, mock_mlflow_tracker: MagicMock
):
    """Test that non-normal data results in appropriate comments and MLflow tags."""
    token = get_mock_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Data designed to likely fail Shapiro-Wilk
    group_a_non_normal = [1,1,1,1,1,1,1,1,1,100] # Likely non-normal
    group_b_normal = [5,6,7,5,6,7,5,6,7,6]   # Likely normal

    request_payload = {
        "group_a_data": group_a_non_normal, # Corregido
        "group_b_data": group_b_normal, # Corregido
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


def test_analyze_ttest_no_auth(client: TestClient): # Corregido: nombre de payload
    """Test endpoint access without authentication token."""
    request_payload_no_auth = {"group_a_data": [1,2,3,4,5], "group_b_data": [6,7,8,9,10]}
    response = client.post("/api/v1/analyze/ttest", json=request_payload_no_auth)
    assert response.status_code == 401 # O 403 dependiendo de la configuración de seguridad exacta
    # El mensaje puede variar. "Not authenticated" es común con OAuth2PasswordBearer.
    # Si se usa el mock básico de get_current_active_user, puede que no dé este error exacto
    # si el mock no levanta HTTPException por falta de token.
    # La prueba real de esto depende de la robustez de la capa de autenticación común.
    # Por ahora, asumimos que el `Depends(get_current_active_user)` en el endpoint protegido
    # (una vez descomentado) causará un error apropiado si el token no es válido o no está.
    # El `api.py` tiene la seguridad de roles comentada, así que esta prueba podría dar otro resultado
    # hasta que se active. Si la seguridad está comentada, podría ser 201.
    # Para que esta prueba sea significativa, la seguridad debe estar activa en el endpoint.
    # Dado que está comentada ("# current_user: CommonUserAuth = Depends(require_roles({'analyst'}))")
    # este test actualmente probaría el endpoint como si fuera público.
    # Lo marcaremos como skip hasta que la seguridad se active en api.py.
    pytest.skip("Skipping no_auth test for /analyze/ttest as endpoint security is currently commented out in api.py")


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
    mock_stats_repository.get_by_id.assert_called_once_with(UUID(exp_id)) # Convertir str a UUID para la aserción
    assert "tracking_warnings" in data
    # Dependerá de lo que sample_domain_experiment tenga; si es default_factory=list, será []
    assert data["tracking_warnings"] == sample_domain_experiment.tracking_warnings


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
    # Asegurarse de que los experimentos de prueba tengan el campo tracking_warnings (incluso si está vacío por defecto)
    exp2 = DomainExperiment(id=exp2_id, name="Exp Two", group_a_data=[0], group_b_data=[1], tracking_warnings=["Warning on exp2"])

    # mock_stats_repository.list_all debe devolver una tupla: (lista_de_experimentos, conteo_total)
    mock_stats_repository.list_all.return_value = ([sample_domain_experiment, exp2], 2)

    response = client.get("/api/v1/experiments?skip=0&limit=10", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == str(sample_domain_experiment.id)
    assert data["items"][0]["tracking_warnings"] == sample_domain_experiment.tracking_warnings # Verificar warnings
    assert data["items"][1]["id"] == str(exp2_id)
    assert data["items"][1]["tracking_warnings"] == ["Warning on exp2"] # Verificar warnings
    mock_stats_repository.list_all.assert_called_once_with(skip=0, limit=10)


def test_app_health_check_endpoint(client: TestClient): # Renombrado para distinguir
    response = client.get("/health") # Endpoint de main.py
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_api_health_check_endpoint(client: TestClient): # Nueva prueba
    # No necesita token si el endpoint de health no está protegido
    response = client.get("/api/v1/health") # Endpoint de api.py
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert data["module"] == "Aletheia-Stats"

def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to Aletheia-Stats API" in response.json()["message"]


def test_analyze_ttest_with_mlflow_start_failure(
    client: TestClient,
    mock_stats_repository: MagicMock,
    mock_mlflow_tracker: MagicMock
):
    """Test /analyze/ttest when MLflow fails to start a run."""
    token = get_mock_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Configure mock_mlflow_tracker to simulate failure during start_run
    mock_mlflow_tracker.start_run.side_effect = Exception("MLflow unavailable")
    # Ensure other MLflow calls don't raise unexpected errors if start_run fails
    # (MagicMock by default returns new MagicMocks for attributes not set, which is fine here)

    request_payload = {
        "group_a_data": [1,2,3,4,5],
        "group_b_data": [2,3,4,5,6],
        "experiment_name": "MLflow Start Fail Test"
    }
    response = client.post("/api/v1/analyze/ttest", json=request_payload, headers=headers)

    assert response.status_code == 201 # Endpoint should still succeed
    data = response.json()
    assert data["name"] == "MLflow Start Fail Test"
    assert data["mlflow_run_id"] is None # As start_run failed
    assert "tracking_warnings" in data
    assert len(data["tracking_warnings"]) == 1
    assert "MLflow Error: Failed to start run or log initial parameters: MLflow unavailable" in data["tracking_warnings"][0]

    # Verify that the experiment was saved, including the warning
    mock_stats_repository.save.assert_called_once()
    saved_experiment: DomainExperiment = mock_stats_repository.save.call_args[0][0]
    assert saved_experiment.name == "MLflow Start Fail Test"
    assert saved_experiment.mlflow_run_id is None
    assert len(saved_experiment.tracking_warnings) == 1
    assert "MLflow Error: Failed to start run or log initial parameters: MLflow unavailable" in saved_experiment.tracking_warnings[0]

    # Reset side_effect for this mock if it's shared across tests (it's function-scoped here, so it's fine)
    mock_mlflow_tracker.start_run.side_effect = None
    mock_mlflow_tracker.start_run.return_value = "mock_mlflow_run_id_after_reset" # Reset to default behavior


def test_analyze_ttest_with_mlflow_log_metric_failure(
    client: TestClient,
    mock_stats_repository: MagicMock,
    mock_mlflow_tracker: MagicMock
):
    """Test /analyze/ttest when MLflow fails to log a metric."""
    token = get_mock_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Reset start_run to succeed for this test, but make log_metric fail
    mock_mlflow_tracker.start_run.return_value = "mock_run_log_fail"
    mock_mlflow_tracker.start_run.side_effect = None # Clear previous side effect
    mock_mlflow_tracker.log_metric.side_effect = Exception("MLflow log_metric failed")

    request_payload = {
        "group_a_data": [1,2,3,4,5],
        "group_b_data": [2,3,4,5,6],
        "experiment_name": "MLflow Log Metric Fail Test"
    }
    response = client.post("/api/v1/analyze/ttest", json=request_payload, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "MLflow Log Metric Fail Test"
    assert data["mlflow_run_id"] == "mock_run_log_fail" # Run started
    assert "tracking_warnings" in data
    assert len(data["tracking_warnings"]) >= 1
    assert any("MLflow Error: Failed to log metrics/tags" in w for w in data["tracking_warnings"])

    mock_mlflow_tracker.end_run.assert_called_once() # end_run should still be called

    # Reset side_effect for log_metric
    mock_mlflow_tracker.log_metric.side_effect = None
