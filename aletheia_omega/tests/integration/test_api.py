# aletheia_omega/tests/integration/test_api.py

import pytest
import uuid
import datetime # Para comparar fechas
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, ANY # ANY para comparar objetos complejos

from aletheia_omega.presentation.api import app
from aletheia_omega.presentation.dependencies import (
    get_find_optimal_model_use_case,
    get_omega_repository,
    get_db_placeholder,
    dev_get_current_user,
    UserAuth,
    get_evolve_trajectory_use_case,  # Nuevas dependencias de caso de uso
    get_classify_trajectory_use_case
)
from aletheia_omega.domain.entities import ( # Entidades de dominio para mocks y aserciones
    OptimizationResult,
    ModelRepresentation,
    ModelMetrics,
    Trajectory,
    TrajectoryStep,
    TrajectoryAnalysis,
    TrajectoryState
)
from aletheia_omega.infrastructure.repository import OmegaRepository
from aletheia_omega.infrastructure.models import TrajectoryDB # Para mock de repo.create_trajectory
from aletheia_omega.application.use_cases import (
    FindOptimalModelUseCase,
    EvolveTrajectoryUseCase,
    ClassifyTrajectoryUseCase
)


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides = {}
    yield TestClient(app)
    app.dependency_overrides = {} # Limpiar después de cada test

# --- Fixtures para Mocks de Casos de Uso y Repositorio ---
@pytest.fixture
def mock_find_optimal_model_use_case_instance():
    mock = MagicMock(spec=FindOptimalModelUseCase)
    mock.execute.return_value = OptimizationResult(
        best_model=ModelRepresentation(identifier="mock_optimal_model", content=b"content"),
        best_model_metrics=ModelMetrics(complexity=1.0, log_likelihood=1.0, mdl_cost=0.0),
        search_space_size=1,
        parameters={"lambda": 0.1, "source": "find_optimal_mock"}
    )
    return mock

@pytest.fixture
def mock_evolve_trajectory_use_case_instance():
    mock = MagicMock(spec=EvolveTrajectoryUseCase)
    # Configurar un valor de retorno por defecto para EvolveTrajectoryUseCase.execute
    # Devuelve un objeto de dominio Trajectory
    mock.execute.return_value = Trajectory(
        id=uuid.uuid4(),
        name="Evolved Trajectory",
        steps=[
            TrajectoryStep(
                step_index=0,
                model=ModelRepresentation(identifier="evolved_model_step0", content=b"s0"),
                metrics=ModelMetrics(complexity=1.0,log_likelihood=1.0,mdl_cost=0.0) # Corregido
            )
        ]
    )
    return mock

@pytest.fixture
def mock_classify_trajectory_use_case_instance():
    mock = MagicMock(spec=ClassifyTrajectoryUseCase)
    mock.execute.return_value = TrajectoryAnalysis(
        trajectory_id=uuid.uuid4(),
        state=TrajectoryState.PROGRESSIVE,
        comment="Mocked analysis: Progressive",
        step_count=3
    )
    return mock

@pytest.fixture
def mock_omega_repository_instance():
    repo_mock = MagicMock(spec=OmegaRepository)
    # Configurar retornos por defecto para los métodos del repo si es necesario globalmente
    # o hacerlo en cada test.
    repo_mock.create_trajectory.return_value = TrajectoryDB( # Devuelve el objeto de BD
        id=uuid.uuid4(),
        name="Default Mocked Trajectory",
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    repo_mock.get_trajectory_with_steps.return_value = Trajectory( # Devuelve objeto de Dominio
        id=uuid.uuid4(),
        name="Default Mocked Trajectory with Steps",
        steps=[]
    )
    return repo_mock

# --- Fixture para Autenticación ---
async def mock_auth_override_success() -> UserAuth:
    return UserAuth(username="test_user_from_override", roles=["researcher"], user_id="test_user_id_override")

# --- Tests para el endpoint /omega/optimize (comentado) ---
# La clase TestOmegaOptimizeEndpoint y sus tests se mantienen comentados o se eliminan
# ya que el endpoint /omega/optimize está comentado en api.py.

# --- Tests para los nuevos endpoints de Trayectorias ---

TRAJECTORIES_BASE_URL = "/omega/trajectories"

class TestTrajectoryEndpoints:

    def test_create_trajectory_success(self, client: TestClient, mock_omega_repository_instance: MagicMock):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        app.dependency_overrides[get_omega_repository] = lambda: mock_omega_repository_instance

        trajectory_name = "My New Trajectory"
        # Configurar el mock para devolver un ID específico para poder comparar
        mock_trajectory_id = uuid.uuid4()
        mock_created_at = datetime.datetime.now(datetime.timezone.utc)
        mock_omega_repository_instance.create_trajectory.return_value = TrajectoryDB(
            id=mock_trajectory_id, name=trajectory_name, created_at=mock_created_at
        )

        response = client.post(TRAJECTORIES_BASE_URL, json={"name": trajectory_name})

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == trajectory_name
        assert data["id"] == str(mock_trajectory_id)
        assert data["steps"] == []
        mock_omega_repository_instance.create_trajectory.assert_called_once_with(name=trajectory_name)

    def test_create_trajectory_no_name_success(self, client: TestClient, mock_omega_repository_instance: MagicMock):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        app.dependency_overrides[get_omega_repository] = lambda: mock_omega_repository_instance

        mock_trajectory_id = uuid.uuid4()
        mock_created_at = datetime.datetime.now(datetime.timezone.utc)
        mock_omega_repository_instance.create_trajectory.return_value = TrajectoryDB(
            id=mock_trajectory_id, name=None, created_at=mock_created_at
        )

        response = client.post(TRAJECTORIES_BASE_URL, json={}) # Sin nombre
        assert response.status_code == 201
        data = response.json()
        assert data["name"] is None
        assert data["id"] == str(mock_trajectory_id)
        mock_omega_repository_instance.create_trajectory.assert_called_once_with(name=None)

    def test_evolve_trajectory_success(
        self, client: TestClient,
        mock_evolve_trajectory_use_case_instance: MagicMock,
        mock_omega_repository_instance: MagicMock # Añadir el mock del repo
    ):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        app.dependency_overrides[get_evolve_trajectory_use_case] = lambda: mock_evolve_trajectory_use_case_instance
        app.dependency_overrides[get_omega_repository] = lambda: mock_omega_repository_instance # Sobreescribir repo

        test_trajectory_id = uuid.uuid4()
        # Configurar el mock para devolver una trayectoria con el ID correcto
        evolved_trajectory_mock_return = Trajectory(
            id=test_trajectory_id, name="Evolved Trajectory", steps=[
                TrajectoryStep(step_index=0, model=ModelRepresentation(identifier="m1", content=b"c1"), metrics=ModelMetrics(complexity=1.0,log_likelihood=1.0,mdl_cost=0.0)), # Corregido
                TrajectoryStep(step_index=1, model=ModelRepresentation(identifier="m2", content=b"c2"), metrics=ModelMetrics(complexity=2.0,log_likelihood=2.0,mdl_cost=1.0))  # Corregido
            ]
        )
        mock_evolve_trajectory_use_case_instance.execute.return_value = evolved_trajectory_mock_return

        evolve_request_payload = {
            "lambda_param": 0.1,
            "candidate_models": [{"identifier": "new_model", "content": "bmV3X2NvbnRlbnQ="}], # Base64 de "new_content"
            "data_context": {"new_data": "some_data"},
            "optimization_parameters": {"param": "value"}
        }
        response = client.post(f"{TRAJECTORIES_BASE_URL}/{test_trajectory_id}/evolve", json=evolve_request_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_trajectory_id)
        assert len(data["steps"]) == 2
        assert data["steps"][1]["model"]["identifier"] == "m2"

        mock_evolve_trajectory_use_case_instance.execute.assert_called_once_with(
            trajectory_id=test_trajectory_id,
            new_data=evolve_request_payload["data_context"],
            model_search_space=ANY,
            lambda_param=evolve_request_payload["lambda_param"],
            optimization_parameters=evolve_request_payload["optimization_parameters"]
        )
        args, kwargs = mock_evolve_trajectory_use_case_instance.execute.call_args
        assert isinstance(kwargs['model_search_space'][0], ModelRepresentation)
        assert kwargs['model_search_space'][0].identifier == "new_model"


    def test_evolve_trajectory_not_found(
        self, client: TestClient,
        mock_evolve_trajectory_use_case_instance: MagicMock,
        mock_omega_repository_instance: MagicMock # Añadir el mock del repo
    ):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        app.dependency_overrides[get_evolve_trajectory_use_case] = lambda: mock_evolve_trajectory_use_case_instance
        app.dependency_overrides[get_omega_repository] = lambda: mock_omega_repository_instance # Sobreescribir repo

        mock_evolve_trajectory_use_case_instance.execute.side_effect = ValueError("La trayectoria con ID some_id no existe.")

        non_existent_id = uuid.uuid4()
        # Payload VÁLIDO para que Pydantic no falle primero
        evolve_request_payload = {
            "lambda_param": 0.1,
            "candidate_models": [{"identifier": "valid_model", "content": "dmFsaWQ="}], # "valid" en base64
            "data_context": {"data":"valid"}
        }
        response = client.post(f"{TRAJECTORIES_BASE_URL}/{non_existent_id}/evolve", json=evolve_request_payload)
        assert response.status_code == 404
        assert "no existe" in response.json()["detail"]

    def test_get_trajectory_classification_success(
        self, client: TestClient, mock_classify_trajectory_use_case_instance: MagicMock
    ):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        app.dependency_overrides[get_classify_trajectory_use_case] = lambda: mock_classify_trajectory_use_case_instance

        test_trajectory_id = uuid.uuid4()
        analysis_mock_return = TrajectoryAnalysis(
            trajectory_id=test_trajectory_id, state=TrajectoryState.PROGRESSIVE, comment="Is great!", step_count=5
        )
        mock_classify_trajectory_use_case_instance.execute.return_value = analysis_mock_return

        response = client.get(f"{TRAJECTORIES_BASE_URL}/{test_trajectory_id}/classification")

        assert response.status_code == 200
        data = response.json()
        assert data["trajectory_id"] == str(test_trajectory_id)
        assert data["state"] == TrajectoryState.PROGRESSIVE.value
        assert data["comment"] == "Is great!"
        assert data["step_count"] == 5
        mock_classify_trajectory_use_case_instance.execute.assert_called_once_with(test_trajectory_id)

    def test_get_trajectory_classification_not_found(
        self, client: TestClient, mock_classify_trajectory_use_case_instance: MagicMock
    ):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        app.dependency_overrides[get_classify_trajectory_use_case] = lambda: mock_classify_trajectory_use_case_instance

        mock_classify_trajectory_use_case_instance.execute.side_effect = ValueError("Trayectoria no encontrada.")

        non_existent_id = uuid.uuid4()
        response = client.get(f"{TRAJECTORIES_BASE_URL}/{non_existent_id}/classification")
        assert response.status_code == 404
        assert "Trayectoria no encontrada" in response.json()["detail"]

    def test_get_trajectory_details_success(self, client: TestClient, mock_omega_repository_instance: MagicMock):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        app.dependency_overrides[get_omega_repository] = lambda: mock_omega_repository_instance

        test_trajectory_id = uuid.uuid4()
        # Mock para el objeto de dominio Trajectory devuelto por el repositorio
        trajectory_domain_mock = Trajectory(
            id=test_trajectory_id,
            name="Detailed Trajectory",
            steps=[
                TrajectoryStep(
                    step_index=0,
                    model=ModelRepresentation(identifier="m1", content=b"c1"),
                    metrics=ModelMetrics(complexity=1.0, log_likelihood=1.0, mdl_cost=0.0) # Corregido
                )
            ]
        )
        mock_omega_repository_instance.get_trajectory_with_steps.return_value = trajectory_domain_mock

        # El endpoint api.py también necesita created_at para el TrajectoryResponse.
        # El repo.get_trajectory_with_steps devuelve el obj de dominio.
        # El endpoint debe obtener TrajectoryDB para created_at. Mockeamos eso también.
        mock_trajectory_db = TrajectoryDB(
            id=test_trajectory_id,
            name="Detailed Trajectory",
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        mock_omega_repository_instance.get_trajectory_db_by_id.return_value = mock_trajectory_db


        response = client.get(f"{TRAJECTORIES_BASE_URL}/{test_trajectory_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_trajectory_id)
        assert data["name"] == "Detailed Trajectory"
        assert len(data["steps"]) == 1
        assert data["steps"][0]["model"]["identifier"] == "m1"
        assert "created_at" in data # Verificar que created_at esté presente

    def test_get_trajectory_details_not_found(self, client: TestClient, mock_omega_repository_instance: MagicMock):
        app.dependency_overrides[dev_get_current_user] = mock_auth_override_success
        app.dependency_overrides[get_omega_repository] = lambda: mock_omega_repository_instance
        # get_trajectory_with_steps devuelve None si no se encuentra
        mock_omega_repository_instance.get_trajectory_with_steps.return_value = None
        # get_trajectory_db_by_id también debería devolver None en este caso para el endpoint
        mock_omega_repository_instance.get_trajectory_db_by_id.return_value = None


        non_existent_id = uuid.uuid4()
        response = client.get(f"{TRAJECTORIES_BASE_URL}/{non_existent_id}")
        assert response.status_code == 404 # Ahora el endpoint debería manejar esto y devolver 404
