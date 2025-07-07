import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock # Para mocks síncronos y asíncronos

# Clases a mockear o instanciar
from Aletheia_v3.application.use_cases import CubicAnalysisPipeline, ApplicationServiceFacade
from Aletheia_v3.core.cube_models import CuboMDU
from Aletheia_v3.application.ports import IAnalysisRepository
from Aletheia_v3.core.domain_models import UnifiedTheory, Pattern
from Aletheia_v3.core.domain_services import DomainService # Para tipar el mock de domain_service
from Aletheia_v3.api.schemas import AnalisisRequest
from Aletheia_v3.application.use_cases import StateTrackerLocal, AnalysisOrchestrator


@pytest_asyncio.fixture
async def mock_dependencies():
    """Prepara mocks para las dependencias de CubicAnalysisPipeline."""
    mock_cubo_mdu = MagicMock(spec=CuboMDU)
    mock_cubo_mdu.rotate_to_perspective = MagicMock()

    mock_app_service_facade = MagicMock(spec=ApplicationServiceFacade)

    # Mock para el resultado de handle_analysis_request
    initial_analysis_result_mock = {
        "analysis_id": "initial_analysis_123",
        "run_id": "initial_run_abc",
        "model": {"type": "initial_model_data", "content": {"data": "initial"}},
        "metrics": {"initial_metric": 0.99}
    }
    mock_app_service_facade.handle_analysis_request = AsyncMock(return_value=initial_analysis_result_mock)

    # Mock para domain_service dentro de app_service_facade
    # Necesitamos que app_service_facade.domain_service exista y tenga los métodos synthesize_model y calculate_metrics
    mock_domain_service_for_facade = MagicMock(spec=DomainService)

    # Mock para UnifiedTheory devuelto por synthesize_model
    def create_mock_unified_theory(perspective_name: str):
        theory_data = {
            "id": f"theory_{perspective_name}",
            "patterns": [Pattern(id=f"p1_{perspective_name}", description="desc", elements=[])],
            "principles": [f"principle_{perspective_name}"],
            "relations": {},
            "validation_metrics": {"val_metric": 0.5},
            "model_data": {"perspective_content": perspective_name},
            "metrics": {f"metric_for_{perspective_name}": 0.75}
        }
        # Usamos una instancia real para obtener .to_dict() gratis
        mock_theory = UnifiedTheory(**theory_data)
        return mock_theory

    # Hacer que synthesize_model devuelva una teoría diferente para cada llamada (o una genérica)
    mock_domain_service_for_facade.synthesize_model = AsyncMock(
        side_effect=lambda theories_list: create_mock_unified_theory("perspective_sim")
    )

    mock_domain_service_for_facade.calculate_metrics = MagicMock(
        side_effect=lambda model_obj: {f"calc_metric_for_{model_obj.id}": 0.88}
    )

    mock_app_service_facade.domain_service = mock_domain_service_for_facade

    mock_repo = MagicMock(spec=IAnalysisRepository)

    # Mock para StateTrackerLocal y AnalysisOrchestrator (aunque no se verifiquen sus llamadas internas en detalle aquí)
    mock_state_tracker = MagicMock(spec=StateTrackerLocal)
    mock_orchestrator = MagicMock(spec=AnalysisOrchestrator) # No usado activamente por el flujo a probar

    # Patchear los constructores si CubicAnalysisPipeline los llama directamente
    # En este caso, se pasan como argumentos, así que no es necesario patch global.

    return {
        "cube": mock_cubo_mdu,
        "app_service_facade": mock_app_service_facade,
        "repo": mock_repo,
        "state_tracker": mock_state_tracker,
        "orchestrator": mock_orchestrator # Aunque no se use mucho, para instanciar pipeline
    }


@pytest.mark.asyncio
async def test_cubic_analysis_pipeline_execute_full_analysis(mock_dependencies, mocker):
    """
    Test para CubicAnalysisPipeline.execute_full_analysis.
    Verifica el flujo de orquestación y la estructura de datos de salida.
    """
    # Desempaquetar mocks
    mock_cubo = mock_dependencies["cube"]
    mock_app_service = mock_dependencies["app_service_facade"]
    mock_repo = mock_dependencies["repo"]
    mock_state_tracker_instance = mock_dependencies["state_tracker"]
    mock_orchestrator_instance = mock_dependencies["orchestrator"]

    # Sobrescribir las instancias de state_tracker y orchestrator que crea el pipeline en su __init__
    # si no se inyectan. En este caso, se inyectan indirectamente por __init__ si cambiamos el constructor
    # o se parchean globalmente.
    # El __init__ actual es: def __init__(self, cube: CuboMDU, app_service_facade: ApplicationServiceFacade, repo: IAnalysisRepository):
    # Y crea internamente: self.orchestrator = AnalysisOrchestrator(); self.state_tracker = StateTrackerLocal()
    # Así que necesitamos parchear AnalysisOrchestrator y StateTrackerLocal a nivel de módulo

    mocker.patch('Aletheia_v3.application.use_cases.AnalysisOrchestrator', return_value=mock_orchestrator_instance)
    mocker.patch('Aletheia_v3.application.use_cases.StateTrackerLocal', return_value=mock_state_tracker_instance)


    # Instanciar CubicAnalysisPipeline
    pipeline = CubicAnalysisPipeline(
        cube=mock_cubo,
        app_service_facade=mock_app_service,
        repo=mock_repo
        # orchestrator y state_tracker serán reemplazados por los mocks gracias al patch
    )

    # Preparar datos de entrada simulados
    mock_request = AnalisisRequest(
        sesion_id="test_pipeline_session_001",
        tipo_analisis="cubic_full",
        parametros={"data": "sample_input_for_pipeline"},
        nivel_profundidad=3
    )
    session_data_str = "{}" # No es usado directamente por el pipeline, sino por app_service

    # Ejecutar el método a probar
    results = await pipeline.execute_full_analysis(session_data_str, mock_request)

    # Verificar la estructura del resultado
    assert isinstance(results, dict)
    expected_perspectives = ['initial', 'temporal', 'causal', 'emergent', 'hierarchical']
    for p_name in expected_perspectives:
        assert p_name in results
        assert "model" in results[p_name]
        assert "metrics" in results[p_name]
        assert isinstance(results[p_name]["model"], dict)
        assert isinstance(results[p_name]["metrics"], dict)

    # Verificar que el modelo 'initial' proviene del mock de handle_analysis_request
    assert results["initial"]["model"]["content"]["data"] == "initial"
    assert results["initial"]["metrics"]["initial_metric"] == 0.99

    # Verificar que los modelos de perspectiva provienen de synthesize_model
    for p_name in expected_perspectives[1:]: # Excluir 'initial'
        assert results[p_name]["model"]["perspective_content"] == "perspective_sim" # De create_mock_unified_theory
        # Y las métricas de calculate_metrics
        # El ID de la teoría simulada es "theory_perspective_sim"
        assert results[p_name]["metrics"]["calc_metric_for_theory_perspective_sim"] == 0.88


    # Verificar llamadas a los mocks
    mock_app_service.handle_analysis_request.assert_called_once_with(mock_request, {"sub": "pipeline_user_from_cubic_pipeline"})

    assert mock_cubo.rotate_to_perspective.call_count == 4 # Para 'temporal', 'causal', 'emergent', 'hierarchical'
    perspectives_called_with = [call.args[0] for call in mock_cubo.rotate_to_perspective.call_args_list]
    assert perspectives_called_with == ['temporal', 'causal', 'emergent', 'hierarchical']

    # domain_service.synthesize_model y calculate_metrics son llamados a través de mock_app_service.domain_service
    assert mock_app_service.domain_service.synthesize_model.call_count == 4
    # Cada llamada a synthesize_model recibe una lista vacía de teorías
    for call_arg in mock_app_service.domain_service.synthesize_model.call_args_list:
        assert call_arg.args[0] == []

    assert mock_app_service.domain_service.calculate_metrics.call_count == 4

    # Verificar StateTrackerLocal (ahora mock_state_tracker_instance gracias al patch)
    # Se espera que se llame 4 veces: pipeline_started, app_layer_processed, multidim_analysis_complete, pipeline_synthesized
    assert mock_state_tracker_instance.update_analysis_state.call_count == 4
    # Se podría verificar los argumentos de cada llamada si es necesario.
    # Ejemplo de la primera llamada:
    mock_state_tracker_instance.update_analysis_state.assert_any_call(
        mock_request.sesion_id,
        {"status": "pipeline_started", "data_snippet": session_data_str[:50]}
    )
    mock_state_tracker_instance.update_analysis_state.assert_any_call(
        mock_request.sesion_id,
        {"status": "pipeline_synthesized", "final_keys": list(results.keys())}
    )

    # AnalysisOrchestrator no es usado directamente en el flujo de datos de execute_full_analysis,
    # solo se instancia. mock_orchestrator_instance.method.assert_not_called() podría ser útil si tuviera métodos.
    # Por ahora, solo verificamos que el parche funcionó y se usó la instancia mockeada.
    assert pipeline.orchestrator == mock_orchestrator_instance
    assert pipeline.state_tracker == mock_state_tracker_instance

```
