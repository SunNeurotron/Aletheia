# aletheia_omega/tests/integration/test_api.py

import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from aletheia_omega.presentation.api import app
from aletheia_omega.presentation.dependencies import (
    get_find_optimal_model_use_case,
    get_omega_repository,
    get_db_placeholder,
    dev_get_current_user, # La dependencia que vamos a sobreescribir
    UserAuth # Importar UserAuth para el mock
)
from aletheia_omega.domain.entities import OptimizationResult, ModelRepresentation, ModelMetrics
from aletheia_omega.infrastructure.repository import OmegaRepository
from aletheia_omega.application.use_cases import FindOptimalModelUseCase


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides = {}
    yield TestClient(app)
    app.dependency_overrides = {}


@pytest.fixture
def mock_find_optimal_model_use_case_instance():
    use_case_mock = MagicMock(spec=FindOptimalModelUseCase)
    mock_domain_result = OptimizationResult(
        best_model=ModelRepresentation(identifier="mock_best_model", content=b"mock_content"),
        best_model_metrics=ModelMetrics(complexity=10.0, log_likelihood=100.0, mdl_cost=-90.0),
        search_space_size=2,
        parameters={"lambda": 0.1, "source": "mock_test"}
    )
    use_case_mock.execute.return_value = mock_domain_result
    return use_case_mock

@pytest.fixture
def mock_omega_repository_instance():
    repo_mock = MagicMock(spec=OmegaRepository)
    return repo_mock # Los return_values se pueden configurar en cada test si es necesario

# Función de override para la autenticación
async def mock_auth_override_success() -> UserAuth:
    return UserAuth(username="test_user_from_override", roles=["researcher"], user_id="test_user_id_override")

class TestOmegaOptimizeEndpoint:

    def test_optimize_success(
        self, client: TestClient,
        mock_find_optimal_model_use_case_instance: MagicMock,
        mock_omega_repository_instance: MagicMock
    ):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        app.dependency_overrides[get_find_optimal_model_use_case] = lambda: mock_find_optimal_model_use_case_instance
        app.dependency_overrides[get_omega_repository] = lambda: mock_omega_repository_instance

        request_payload = {
            "lambda_param": 0.1,
            "candidate_models": [{"identifier": "model1", "content": "Y29udGVudDE="}, {"identifier": "model2", "content": "Y29udGVudDI="}],
            "data_context": {"X_source": "path/to/data_X.csv", "y_source": "path/to/data_y.csv"},
            "optimization_parameters": {"dataset_version": "v1.2"}
        }
        response = client.post("/omega/optimize", json=request_payload)

        assert response.status_code == 200
        data = response.json()
        mock_omega_repository_instance.create_run.assert_called_once()
        mock_find_optimal_model_use_case_instance.execute.assert_called_once()
        mock_omega_repository_instance.update_run_with_result.assert_called_once()
        assert data["status"] == "COMPLETED"
        assert data["best_model"]["identifier"] == "mock_best_model"


    def test_optimize_validation_error_empty_candidates(self, client: TestClient):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        app.dependency_overrides[get_db_placeholder] = lambda: MagicMock() # Para que el repo no falle si se instancia

        request_payload = {"lambda_param": 0.1, "candidate_models": [], "data_context": {},}
        response = client.post("/omega/optimize", json=request_payload)
        assert response.status_code == 422

    def test_optimize_value_error_from_use_case(
        self, client: TestClient,
        mock_find_optimal_model_use_case_instance: MagicMock,
        mock_omega_repository_instance: MagicMock
    ):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        mock_find_optimal_model_use_case_instance.execute.side_effect = ValueError("Test value error from use case")

        app.dependency_overrides[get_find_optimal_model_use_case] = lambda: mock_find_optimal_model_use_case_instance
        app.dependency_overrides[get_omega_repository] = lambda: mock_omega_repository_instance

        request_payload = {"lambda_param": 0.1, "candidate_models": [{"identifier": "m1", "content": "Yw=="}], "data_context": {"X": [], "y": []}}
        response = client.post("/omega/optimize", json=request_payload)
        assert response.status_code == 400
        mock_omega_repository_instance.create_run.assert_called_once()
        mock_omega_repository_instance.update_run_status.assert_called_once_with(run_id=mock_omega_repository_instance.create_run.call_args[1]['run_id'], status="FAILED_VALIDATION")


    def test_optimize_db_error_on_create_run(
        self, client: TestClient,
        mock_find_optimal_model_use_case_instance: MagicMock,
        mock_omega_repository_instance: MagicMock
    ):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        mock_omega_repository_instance.create_run.side_effect = Exception("Simulated DB error on create")

        app.dependency_overrides[get_find_optimal_model_use_case] = lambda: mock_find_optimal_model_use_case_instance
        app.dependency_overrides[get_omega_repository] = lambda: mock_omega_repository_instance

        request_payload = {"lambda_param": 0.1, "candidate_models": [{"identifier": "m1", "content": "Yw=="}], "data_context": {}}
        response = client.post("/omega/optimize", json=request_payload)
        assert response.status_code == 500
        mock_find_optimal_model_use_case_instance.execute.assert_not_called()

    def test_optimize_db_error_on_update_result(
        self, client: TestClient,
        mock_find_optimal_model_use_case_instance: MagicMock,
        mock_omega_repository_instance: MagicMock
    ):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        # Configurar create_run para que no falle y devuelva un mock si es necesario para obtener run_id
        mock_omega_repository_instance.create_run.return_value = MagicMock(id=uuid.uuid4())
        mock_omega_repository_instance.update_run_with_result.side_effect = Exception("Simulated DB error on update")

        app.dependency_overrides[get_find_optimal_model_use_case] = lambda: mock_find_optimal_model_use_case_instance
        app.dependency_overrides[get_omega_repository] = lambda: mock_omega_repository_instance

        request_payload = {"lambda_param": 0.1, "candidate_models": [{"identifier": "m1", "content": "Yw=="}], "data_context": {}}
        response = client.post("/omega/optimize", json=request_payload)
        assert response.status_code == 500
        mock_omega_repository_instance.create_run.assert_called_once()
        # Capturar el run_id con el que create_run fue llamado
        actual_run_id_in_create_run = mock_omega_repository_instance.create_run.call_args[1]['run_id']

        mock_find_optimal_model_use_case_instance.execute.assert_called_once()
        mock_omega_repository_instance.update_run_status.assert_called_once_with(run_id=actual_run_id_in_create_run, status="CALC_DONE_SAVE_FAILED")
