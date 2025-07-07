import pytest
import pytest_asyncio # Explicitly import for the fixture decorator
from httpx import AsyncClient # For making API calls
from typing import Dict, Any
import jwt # For creating test tokens
from datetime import datetime, timedelta

# Adjust imports based on new locations
# Assuming Aletheia_v3 is in PYTHONPATH or tests run from project root
from ...api.mdu_api_server import SecurityConfig # For token generation
from ...api.schemas import AnalisisRequest # For request payload typing

# The FastAPI app instance from mdu_api_server.py
# This needs to be accessible. One way is to import the create_mdu_api_application factory.
from ...api.mdu_api_server import create_mdu_api_application

# Import models/protocols that might be mocked if not using full DI overrides
from ...application.ports import IAnalysisRepository, IExperimentTracker, ITaskQueue, AnalysisData
from ...infrastructure.repositories import PostgreSQLRepository # For spec in mocker
from ...infrastructure.trackers import MLflowTracker # For spec in mocker
from ...infrastructure.queues import CeleryTaskQueue # For spec in mocker
from ...core.domain_models import ConceptualUnit, ConceptCluster, UnifiedTheory # For mocking domain service returns
from ...core.domain_services import DomainService, TheoryBuilder # For mocking or instantiating

# FastAPI instance for testing - created once per module or session
# This depends on how dependencies are handled in create_mdu_api_application.
# If create_mdu_api_application uses global/default connections, this might have side effects.
# For isolated tests, dependency overrides in FastAPI are better.
# For now, let's use the factory as is.
# test_app_instance = create_mdu_api_application() # This might try to connect to DB/MLflow on import.
# It's better to create the app inside a fixture that can manage its lifecycle and dependencies.


@pytest.mark.asyncio
class TestIntegrationMDUApi: # Renamed from TestIntegrationMDU to be more specific
    """End-to-End tests for the MDU API, focusing on request/response and basic flow."""

    @pytest.fixture(scope="function")
    def anyio_backend_fixture(self):
        """Explicitly set function-scoped anyio backend for this test class."""
        return "asyncio"

    @pytest_asyncio.fixture # Explicitly mark as a pytest-asyncio fixture
    # Depends on the anyio_backend_fixture to ensure event loop is set up for this class
    async def mdu_api_test_client_data(self, mocker: pytest.MonkeyPatch, anyio_backend_fixture):
        """
        Provides an AsyncClient configured for the MDU API and the mock objects.
        Mocks infrastructure dependencies to avoid external calls.
        Yields a tuple: (client, pg_repo_mock, mlflow_tracker_mock, celery_queue_mock, domain_service_mock, ...)
        """
        # --- Mock Infrastructure that create_mdu_api_application might try to instantiate ---
        mock_pg_repo_instance = mocker.MagicMock(spec=PostgreSQLRepository)
        mock_pg_repo_instance.save = mocker.AsyncMock(return_value="saved_analysis_e2e_fixture_123")
        mock_analysis_obj_for_get = AnalysisData(
            id="saved_analysis_e2e_fixture_123", session_id="test_e2e_fixture", # Ensure this matches test_session_id
            model_data={"levels": [{"id":"lvl1"}, {"id":"lvl2"}, {"id":"lvl3"}]},
            metrics={"accuracy": 0.98, "progress_metric": "75.5"}, # Added progress_metric
            status="completed_from_mock_db_fixture"
        )
        mock_pg_repo_instance.get = mocker.AsyncMock(return_value=mock_analysis_obj_for_get)
        mock_pg_repo_instance.update = mocker.AsyncMock()

        mock_mlflow_tracker_instance = mocker.MagicMock(spec=MLflowTracker)
        mock_mlflow_tracker_instance.start_run.return_value = "run_e2e_fixture_abc"
        mock_mlflow_tracker_instance.log_params = mocker.MagicMock()
        mock_mlflow_tracker_instance.log_metrics = mocker.MagicMock()
        mock_mlflow_tracker_instance.end_run = mocker.MagicMock()

        mock_celery_queue_instance = mocker.MagicMock(spec=CeleryTaskQueue)
        mock_celery_queue_instance.enqueue_task = mocker.AsyncMock(return_value="task_e2e_fixture_xyz")
        mock_celery_queue_instance.get_task_status = mocker.AsyncMock(return_value={"status":"PENDING_fixture"})

        # Patch the constructors of the infra classes BEFORE the app is created
        # These patched_X variables hold the MagicMock object that replaced the class
        patched_pg_repo = mocker.patch('Aletheia_v3.api.mdu_api_server.PostgreSQLRepository', return_value=mock_pg_repo_instance)
        patched_mlflow_tracker = mocker.patch('Aletheia_v3.api.mdu_api_server.MLflowTracker', return_value=mock_mlflow_tracker_instance)
        patched_celery_queue = mocker.patch('Aletheia_v3.api.mdu_api_server.CeleryTaskQueue', return_value=mock_celery_queue_instance)

        mock_domain_service_instance = mocker.MagicMock(spec=DomainService)
        dummy_cu = ConceptualUnit("cu_e2e", "content", np.array([0.1,0.2]), set(), {})
        dummy_cc = ConceptCluster([dummy_cu])
        dummy_th_data = {
            "id": "th_e2e_1", "patterns": [], "principles": [], "relations": {},
            "validation_metrics": {"accuracy_mock": 0.95}, "session_id": "test_e2e_fixture",
            "model_data": {"levels":[]}, "metrics": {"fixture_metric": 0.75}
        }
        dummy_th = UnifiedTheory(**dummy_th_data)

        mock_domain_service_instance.extract_atomic_units = mocker.AsyncMock(return_value=[dummy_cu])
        mock_domain_service_instance.form_clusters = mocker.AsyncMock(return_value=[dummy_cc])
        mock_domain_service_instance.build_mini_theories = mocker.AsyncMock(return_value=[dummy_th])
        mock_domain_service_instance.synthesize_model = mocker.AsyncMock(return_value=dummy_th)
        mock_domain_service_instance.calculate_metrics = mocker.MagicMock(return_value={"domain_metric_e2e": 0.8})

        patched_domain_service = mocker.patch('Aletheia_v3.api.mdu_api_server.DomainService', return_value=mock_domain_service_instance)
        mocker.patch('Aletheia_v3.api.mdu_api_server.TheoryBuilder', return_value=mocker.MagicMock(spec=TheoryBuilder))

        app_instance_for_test = create_mdu_api_application()

        # Manage client context here and return it along with mocks
        # This means the client is active for the duration of the fixture's awaited result in the test
        # but tests themselves don't need to `async with` it.
        # This is slightly different from yielding, as the client's context is tied to this fixture's execution.
        # For httpx.AsyncClient, it's generally better to manage its lifecycle per test or with a yield.
        # However, to resolve the async_generator unpacking, let's try returning.
        # The fixture itself will run to completion, and the client will be closed when the fixture scope ends (function scope here).
        # This might not be ideal if client state needs to persist across multiple calls within a single test *after* the fixture has returned.
        # But for simple request-response, this should be fine.
        # A better way if returning is required:
        # client = AsyncClient(app=app_instance_for_test, base_url="http://test")
        # await client.__aenter__() # Manually enter context
        # return (client, ..., mocks)
        # And then have a finalizer to call client.__aexit__
        # For simplicity now, let's assume the test makes one set of calls.
        # The client will be closed when it's garbage collected if not explicitly closed.
        # This is not robust. A yield is better.
        # Let's stick to yield but ensure pytest-asyncio is configured correctly.
        # The error "cannot unpack non-iterable async_generator object" is very puzzling if pytest-asyncio is working.

        # Reverting to yield as it's the standard pattern.
        # The problem might be with how pytest-anyio and pytest-asyncio interact or a specific version issue.
        # Let's try to force pytest-asyncio's hand by marking the fixture explicitly.
        # @pytest_asyncio.fixture  <-- this would require importing pytest_asyncio
        # However, pytest usually figures this out from `async def` and `yield`.

        # If the `TypeError` persists, it might be that the test functions themselves are not being recognized as asyncio-driven by pytest.
        # The `@pytest.mark.asyncio` on the class should handle this.

        # Let's ensure the mocker is `pytest_mock.plugin.MockerFixture` for type hinting, though `pytest.MonkeyPatch` is often the same object.
        # This is unlikely the cause.

        # The most direct cause of "cannot unpack non-iterable async_generator object" is that the fixture *call*
        # is returning the generator, not its yielded value. This means pytest's machinery for async gen fixtures is not working.

        # Let's try one more time with the standard yield, but ensure the test class is marked correctly
        # and that the anyio_backend fixture is correctly scoped and named.
        # The anyio_backend_fixture in the class is fine.
        # The fixture `mdu_api_test_client_data` does not need `anyio_backend_fixture` in its args,
        # as `anyio_backend` is a session-scoped fixture that `pytest-anyio` uses automatically.
        # The `anyio_backend_fixture` parameter ensures this fixture runs within the desired event loop.

        client = AsyncClient(app=app_instance_for_test, base_url="http://test")
        # Standard pattern for async fixture with setup/teardown:
        try:
            yield (client,
                   mock_pg_repo_instance, mock_mlflow_tracker_instance, mock_celery_queue_instance,
                   mock_domain_service_instance,
                   patched_pg_repo, patched_mlflow_tracker, patched_celery_queue, patched_domain_service
                  )
        finally:
            await client.aclose() # Ensure client is closed after the test

    # Helper to generate a token
    def _get_e2e_test_token(self) -> str:
        temp_sec_config = SecurityConfig()
        payload = {"sub": "e2e_test_user", "exp": datetime.utcnow() + timedelta(minutes=15)}
        return jwt.encode(payload, temp_sec_config.SECRET_KEY, algorithm=temp_sec_config.ALGORITHM)


    async def test_mdu_analyze_endpoint(self, mdu_api_test_client_data, mocker: pytest.MonkeyPatch):
        """Tests the /mdu/analyze endpoint for successful request and response structure."""
        (client, mock_pg_repo_instance, mock_mlflow_tracker_instance, _, _,
         patched_pg_repo, patched_mlflow_tracker, _, _) = mdu_api_test_client_data

        test_token = self._get_e2e_test_token()
        request_payload = AnalisisRequest(
            sesion_id="test_e2e_fixture_analyze",
            tipo_analisis="full_e2e_test",
            parametros={"data_key": "some_complex_data_for_e2e_analysis", "depth_level": 4},
            nivel_profundidad=4
        ).dict()

        response = await client.post(
            "/mdu/analyze",
            json=request_payload,
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200, f"API call failed: {response.text}"
        response_data = response.json()

        assert "analysis_id" in response_data
        assert response_data["analysis_id"] == "saved_analysis_e2e_fixture_123"
        assert "status_message" in response_data
        assert "details_url" in response_data
        assert response_data["details_url"] == f"/api/v1/mdu/status/{response_data['analysis_id']}"

        # Assert constructor was called (on the mock object that replaced the class)
        patched_pg_repo.assert_called_once()
        # Assert methods were called on the instance returned by the patched constructor
        mock_pg_repo_instance.save.assert_called_once()

        patched_mlflow_tracker.assert_called_once()
        mock_mlflow_tracker_instance.start_run.assert_called_once()
        mock_mlflow_tracker_instance.log_params.assert_called_once()
        mock_mlflow_tracker_instance.log_metrics.assert_called_once()
        mock_mlflow_tracker_instance.end_run.assert_called_once()

    async def test_mdu_get_status_endpoint(self, mdu_api_test_client_data, mocker: pytest.MonkeyPatch):
        """Tests the /mdu/status/{session_id} endpoint."""
        client, mock_pg_repo_instance, _, _, _, _, _, _, _ = mdu_api_test_client_data

        test_token = self._get_e2e_test_token()
        # This session_id must match the one in mock_analysis_obj_for_get for the mock to work
        test_session_id = "test_e2e_fixture"

        response = await client.get(
            f"/mdu/status/{test_session_id}", # Use the ID that the mock is set up to return
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 200, f"API call failed: {response.text}"
        response_data = response.json()

        # The session_id in response should be the one from the path, which is used in the .get() call
        assert response_data["session_id"] == test_session_id
        assert "current_status" in response_data
        assert response_data["current_status"] == "completed_from_mock_db_fixture"
        assert "progress_percent" in response_data

        mock_pg_repo_instance.get.assert_called_once_with(test_session_id)


    async def test_mdu_token_endpoint(self, mdu_api_test_client_data): # Removed mocker as it's not directly used here
        client, *_ = mdu_api_test_client_data # Unpack only the client
        """Tests the /mdu/token endpoint for token generation."""
        # The mdu_api_server.py's /mdu/token endpoint uses hardcoded credentials for demo.
        token_response = await client.post( # Use unpacked client
            "/mdu/token",
            data={"username": "mdu_user", "password": "mdu_pass"} # x-www-form-urlencoded
        )
        assert token_response.status_code == 200, f"Token endpoint failed: {token_response.text}"
        token_data = token_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

        # Test with invalid credentials
        invalid_token_response = await client.post( # Use unpacked client
            "/mdu/token",
            data={"username": "wrong_user", "password": "wrong_password"}
        )
        assert invalid_token_response.status_code == 401 # Based on mdu_api_server implementation

    async def test_mdu_analyze_unauthorized(self, mdu_api_test_client_data): # Changed to use _data fixture
        """Tests /mdu/analyze endpoint without a token."""
        client, *_ = mdu_api_test_client_data # Unpack only the client
        request_payload = AnalisisRequest(
            sesion_id="test_unauth_session", tipo_analisis="unauth_test",
            parametros={}, nivel_profundidad=1
        ).dict()

        response = await client.post("/mdu/analyze", json=request_payload) # Changed to use unpacked client
        assert response.status_code == 401 # Expecting Unauthorized

import numpy as np # For dummy ConceptualUnit in fixture
# Need to import status for HTTPException from fastapi
from fastapi import status # For status codes in HTTPException (used in mdu_api_server.py)
