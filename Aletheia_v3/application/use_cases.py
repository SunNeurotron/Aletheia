from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json # For session_data_for_uc in ApplicationFace (if kept here)
import random # For AdaptiveAnalysisEngine placeholders

# Domain services and models (adjust path based on final structure)
from ..core.domain_services import DomainService # Assuming DomainService is defined here
# from ..core.domain_models import ... # If specific domain models are directly used by use cases

# Ports
from .ports import IAnalysisRepository, IExperimentTracker, ITaskQueue

# Cube models (if CubicAnalysisPipeline interacts with it directly)
from ..core.cube_models import CuboMDU # For CubicAnalysisPipeline

# Honeycomb models for CubeHoneycombIntegration
from ..core.honeycomb_models import HoneycombGrid, PathOptimizer, ReplicationManager, ConsensusEngine, WavePropagation, HexagonalCell # Added HexagonalCell
import hashlib # For CubeHoneycombIntegration analysis_id generation
import asyncio # For CubeHoneycombIntegration async methods


# Presentation layer models (if use cases accept them directly)
# from ..api.schemas import AnalisisRequest # This creates a dependency from app to api layer, usually avoided.
# Instead, use cases should operate on more generic data types or application-specific request models.
# For now, keeping AnalisisRequest for CubicAnalysisPipeline as per mdu_cube_system.py structure.
# This might need refactoring later to decouple application from specific presentation models.
from ..api.schemas import AnalisisRequest # Temporary, for direct use from mdu_cube_system.py


@dataclass
class AnalysisUseCase:
    """Caso de uso principal - orquestación del análisis multinivel."""
    repository: IAnalysisRepository
    tracker: IExperimentTracker
    queue: ITaskQueue
    domain_service: DomainService

    async def execute_multilevel_analysis(
        self,
        session_data_str: str, # String representation of session specific data
        config: Dict[str, Any] # Configuration for the analysis run
    ) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo de análisis multinivel.

        Este método orquesta la extracción de unidades atómicas, formación de clusters,
        construcción de miniteorías y la síntesis de un modelo unificado a través
        del DomainService. El resultado se persiste utilizando el repositorio
        configurado y las métricas clave se registran con el tracker de experimentos.

        Args:
            session_data_str: String JSON que contiene los datos específicos de la sesión
                              necesarios para el análisis (e.g., parámetros de entrada).
            config: Un diccionario con parámetros de configuración para la ejecución del
                    análisis, incluyendo 'session_id' y, opcionalmente, 'id' para el
                    registro del análisis.

        Returns:
            Un diccionario que contiene:
                - "analysis_id": El ID del análisis guardado en el repositorio.
                - "run_id": El ID de la ejecución del tracker de experimentos.
                - "model": El volcado del modelo de datos de AnalysisData (Pydantic)
                           que fue persistido.
                - "metrics": Un diccionario con las métricas calculadas por el
                             DomainService para el modelo unificado.
        """
        run_id = self.tracker.start_run(f"analysis_{config.get('session_id', 'unknown_session')}")
        self.tracker.log_params(config)

        try:
            atoms = await self.domain_service.extract_atomic_units(session_data_str)
            clusters = await self.domain_service.form_clusters(atoms)
            theories = await self.domain_service.build_mini_theories(clusters)
            unified_model_obj = await self.domain_service.synthesize_model(theories)

            # Prepare data for repository (expects AnalysisData Pydantic model from ports.py)
            # unified_model_obj is likely a UnifiedTheory domain object.
            # We need to convert it to the structure expected by IAnalysisRepository.save, which is AnalysisData.

            # Convert UnifiedTheory domain object to a dictionary
            unified_model_dict = unified_model_obj.to_dict()

            # Prepare data for AnalysisData Pydantic model
            # The 'id' for AnalysisData should be the overall analysis/session identifier,
            # typically from config. The 'id' within unified_model_dict is for the theory itself.
            analysis_id_for_repo = config.get('id', config.get('session_id', 'default_analysis_id'))
            session_id_for_repo = config.get('session_id', 'default_session_id')

            model_data_from_theory = unified_model_dict.get('model_data', {})
            metrics_from_theory = unified_model_dict.get('metrics', {})

            # Ensure levels for test compatibility if not present in model_data_from_theory
            # This was a previous requirement, keeping it for now.
            if 'levels' not in model_data_from_theory:
                model_data_from_theory['levels'] = []

            analysis_data_payload = {
                "id": analysis_id_for_repo,
                "session_id": session_id_for_repo,
                "model_data": model_data_from_theory,
                "metrics": metrics_from_theory,
                # status and created_at can be defaulted by AnalysisData or set by the repository
            }

            # Create AnalysisData Pydantic model instance
            from .ports import AnalysisData # Import here to avoid circularity if AnalysisData moves
            analysis_pydantic_obj = AnalysisData(**analysis_data_payload)

            # Save to repository
            saved_analysis_id = await self.repository.save(analysis_pydantic_obj) # repository.save returns the id

            # Log metrics (calculated_metrics might be more comprehensive or specific than those in unified_model_obj.metrics)
            calculated_metrics = self.domain_service.calculate_metrics(unified_model_obj)
            self.tracker.log_metrics(calculated_metrics)

            return {
                "analysis_id": saved_analysis_id, # Use the ID returned by the save operation
                "run_id": run_id,
                "model": analysis_pydantic_obj.model_dump(), # Return dict version of the saved data
                "metrics": calculated_metrics # Return the freshly calculated metrics
            }
        finally:
            self.tracker.end_run()


# The ApplicationFace from mdu_cube_system.py acts as a higher-level service facade or controller.
# It's not strictly a use case itself but orchestrates them.
# For now, placing it here as it was closely tied to AnalysisUseCase.
# It might be better placed in a dedicated 'services.py' or refactored.
class ApplicationServiceFacade: # Renamed from ApplicationFace for clarity
    def __init__(self, domain_service: DomainService, repo: IAnalysisRepository, tracker: IExperimentTracker, queue: ITaskQueue):
        self.analysis_use_case = AnalysisUseCase(repo, tracker, queue, domain_service)
        self.domain_service = domain_service

    async def handle_analysis_request(self, request: AnalisisRequest, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja una solicitud de análisis entrante.

        Prepara la configuración y los datos de sesión a partir de la solicitud
        y el usuario, y luego invoca el AnalysisUseCase para ejecutar el análisis.

        Args:
            request: El objeto AnalisisRequest (Pydantic model) proveniente de la API.
            user: Un diccionario que representa al usuario autenticado (e.g., de un token JWT).

        Returns:
            Un diccionario con el resultado de la ejecución del análisis,
            generalmente incluyendo 'analysis_id', 'run_id', 'model', y 'metrics'.
        """
        config = request.dict() # Convierte el Pydantic model a dict para la config
        config['user_id'] = user.get('sub') # Añade el ID del usuario a la config

        # The session_data for execute_multilevel_analysis should be derived from the request.
        # Example: if parameters contain the core data to analyze.
        session_data_for_uc = json.dumps(request.parametros) if request.parametros else ""

        result = await self.analysis_use_case.execute_multilevel_analysis(
            session_data_str=session_data_for_uc,
            config=config
        )
        return result

    async def get_analysis_status(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de un análisis existente.

        Consulta el repositorio para obtener los datos de un análisis basado en su session_id.
        Si se encuentra, formatea los datos para que coincidan con el esquema
        MDUAnalysisStatusResponse, incluyendo el estado actual, el porcentaje de progreso
        (calculado a partir de 'progress_metric' en las métricas del análisis),
        y los detalles completos del análisis.

        Args:
            session_id: El ID de la sesión del análisis a consultar.

        Returns:
            Un diccionario que representa el estado del análisis:
            - "session_id": El ID de la sesión consultada.
            - "current_status": El estado actual del análisis (e.g., "completed", "running", "NOT_FOUND").
            - "progress_percent": Un float que indica el progreso (0.0-100.0).
            - "details": Un diccionario con los datos completos del análisis (si se encuentra),
                         o None si no se encuentra.
        """
        analysis_data = await self.analysis_use_case.repository.get(session_id)
        if analysis_data:
            progress_percent_float = 0.0
            if analysis_data.metrics:
                metric_val = analysis_data.metrics.get("progress_metric") # Assuming progress_metric is a value between 0 and 100 or can be converted.
                if metric_val is not None:
                    try:
                        progress_percent_float = float(str(metric_val).replace('%', ''))
                        if not (0.0 <= progress_percent_float <= 100.0): # Clamp to range
                            progress_percent_float = max(0.0, min(progress_percent_float, 100.0))
                    except ValueError:
                        progress_percent_float = 0.0 # Fallback if not floatable

            # Ensure analysis_data.status is not None, default to a generic status if it is.
            current_status_str = analysis_data.status if analysis_data.status is not None else "UNKNOWN"

            return {
                "session_id": session_id,
                "current_status": current_status_str,
                "progress_percent": progress_percent_float,
                "details": analysis_data.model_dump() # model_dump() returns a dict
            }

        # Case: Analysis not found
        return {
            "session_id": session_id,
            "current_status": "NOT_FOUND",
            "progress_percent": 0.0,
            "details": None # Conforms to MDUAnalysisStatusResponse where details is Optional
        }


# --- Classes from original Section 3.2 and 4, now part of Application Layer ---

class MessageBus: # Placeholder, potentially an interface for a real bus
    async def publish(self, channel: str, message: dict):
        # print(f"MessageBus (Application Placeholder): Publishing to {channel}: {message}")
        pass
    async def subscribe(self, channel: str, callback: Any): # callback type Any for simplicity
        # print(f"MessageBus (Application Placeholder): Subscribing to {channel}")
        pass

class StateManager: # Placeholder
    def __init__(self):
        self.global_state: Dict[str, Dict[Any, Any]] = {}
    def update_state(self, layer: str, data: dict):
        # print(f"StateManager (Application Placeholder): Updating state for {layer} with {data}")
        if layer not in self.global_state:
            self.global_state[layer] = {}
        self.global_state[layer].update(data)
    def get_state(self, layer: str) -> dict:
        return self.global_state.get(layer, {})

class LayerSynchronizer:
    """Sincronización bidireccional entre capas (Conceptual)."""
    def __init__(self):
        self.message_bus = MessageBus()
        self.state_manager = StateManager()

    async def synchronize_layers(
        self, source_layer: str, target_layer: str, data: dict
    ) -> None:
        if not self._validate_compatibility(source_layer, target_layer, data):
            raise ValueError(f"Incompatible data transfer from {source_layer} to {target_layer}")

        transformed_data = self._transform_data(source_layer, target_layer, data)
        await self.message_bus.publish(
            channel=f"{source_layer}_to_{target_layer}", message=transformed_data
        )
        self.state_manager.update_state(target_layer, transformed_data)

    def _validate_compatibility(self, source: str, target: str, data: dict) -> bool:
        # print(f"LayerSynchronizer: Validating compatibility {source} -> {target}")
        return True

    def _transform_data(self, source: str, target: str, data: dict) -> dict:
        # print(f"LayerSynchronizer: Transforming data {source} -> {target}")
        if (source, target) == ('presentation', 'application'): return self._transform_request_to_command(data)
        elif (source, target) == ('application', 'domain'): return self._transform_command_to_domain(data)
        return data

    def _transform_request_to_command(self, data: dict) -> dict: return {"command": data.get("tipo_analisis"), "params": data}
    def _transform_command_to_domain(self, data: dict) -> dict: return {"domain_action": data.get("command"), "data": data.get("params")}
    # Other transform methods from spec would go here

class AnalysisOrchestrator: # Placeholder
    async def coordinate_phase(self, phase_name: str, input_data: Any) -> Any:
        # print(f"AnalysisOrchestrator (Application Placeholder): Coordinating phase {phase_name}")
        if phase_name == "presentation_entry": return {"request_obj_processed": input_data}
        return {"output_from_orchestrated_" + phase_name: input_data}

class StateTrackerLocal: # Renamed to avoid conflict if a more global StateTracker exists
    def __init__(self):
        self.analysis_states: Dict[str, Dict[Any, Any]] = {}
    def update_analysis_state(self, analysis_id: str, state_info: dict):
        # print(f"StateTrackerLocal: Updating state for {analysis_id}: {state_info}")
        self.analysis_states[analysis_id] = state_info
    def get_analysis_state(self, analysis_id: str) -> Optional[dict]:
        return self.analysis_states.get(analysis_id)

class CubicAnalysisPipeline:
    """Pipeline que atraviesa todas las caras del cubo (Conceptual Orchestration)."""
    def __init__(self, cube: CuboMDU, app_service_facade: ApplicationServiceFacade, repo: IAnalysisRepository):
        self.cube = cube
        self.orchestrator = AnalysisOrchestrator()
        self.state_tracker = StateTrackerLocal()
        self.app_service = app_service_facade # Renamed from application_face
        self.repository = repo

    async def execute_full_analysis(self, session_data: str, request: AnalisisRequest) -> Dict[str, Any]:
        """
        Orquesta un análisis multidimensional completo.

        Este método sigue un proceso de múltiples fases:
        1. Realiza un análisis inicial utilizando el ApplicationServiceFacade.
        2. Itera a través de múltiples perspectivas (temporal, causal, etc.),
           simulando una rotación del "cubo" y un re-análisis para cada una.
           Estos re-análisis se simulan llamando directamente a los servicios
           de dominio para generar nuevos modelos y métricas.
        3. Agrega los resultados del análisis inicial y de todas las perspectivas.

        Args:
            session_data: Datos de la sesión (actualmente no utilizados directamente aquí,
                          sino pasados a través de `request` al `app_service`).
            request: El objeto AnalisisRequest con los parámetros para el análisis.

        Returns:
            Un diccionario que contiene los resultados del análisis inicial y de
            cada perspectiva. Cada entrada de perspectiva incluye 'model' y 'metrics'.
            Ejemplo: {'initial': {...}, 'temporal': {...}, ...}
        """
        analysis_id = request.sesion_id
        self.state_tracker.update_analysis_state(analysis_id, {"status": "pipeline_started", "data_snippet": session_data[:50]})

        # Phase 1 & 2: Presentation input and Application processing
        # This is largely handled by app_service.handle_analysis_request now
        dummy_user = {"sub": "pipeline_user_from_cubic_pipeline"}
        application_output = await self.app_service.handle_analysis_request(request, dummy_user)
        self.state_tracker.update_analysis_state(analysis_id, {"status": "app_layer_processed", "app_output_keys": list(application_output.keys())})

        # Phase 3 (Domain) is encapsulated within application_output.model
        # Phase 4 (Persistence) is encapsulated within handle_analysis_request (it calls repo.save)

        # Phase 5: Rotación para análisis multidimensional (Conceptual)
        multidim_results = await self._rotate_and_analyze(application_output)
        self.state_tracker.update_analysis_state(analysis_id, {"status": "multidim_analysis_complete", "multidim_keys": list(multidim_results.keys())})

        final_results = await self._synthesize_results(multidim_results)
        self.state_tracker.update_analysis_state(analysis_id, {"status": "pipeline_synthesized", "final_keys": list(final_results.keys())})
        return final_results

    async def _rotate_and_analyze(self, initial_app_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simula el análisis desde múltiples perspectivas rotando el "cubo".

        Toma el resultado del análisis inicial y luego, para cada perspectiva definida
        (temporal, causal, etc.):
        1. Llama conceptualmente a `self.cube.rotate_to_perspective()`.
        2. Simula un re-análisis llamando a `self.app_service.domain_service.synthesize_model([])`
           para obtener un nuevo modelo para la perspectiva.
        3. Calcula las métricas para este nuevo modelo.
        4. Agrega el modelo y las métricas de la perspectiva a los resultados.

        Args:
            initial_app_output: El resultado del `ApplicationServiceFacade.handle_analysis_request`,
                                que incluye 'model' y 'metrics' del análisis inicial.

        Returns:
            Un diccionario donde cada clave es un nombre de perspectiva (incluyendo 'initial')
            y su valor es otro diccionario con 'model' y 'metrics' para esa perspectiva.
        """
        perspectives = ['temporal', 'causal', 'emergent', 'hierarchical']

        # initial_app_output is the result from self.app_service.handle_analysis_request
        # It contains 'model' and 'metrics' at its top level.
        initial_model_data = initial_app_output.get('model', {})
        initial_metrics_data = initial_app_output.get('metrics', {})

        multi_results: Dict[str, Any] = {
            'initial': {
                "model": initial_model_data,
                "metrics": initial_metrics_data
            }
        }

        for perspective in perspectives:
            self.cube.rotate_to_perspective(perspective) # Conceptual call

            # Simulate re-analysis for the current perspective by calling domain_service directly.
            # Assumes app_service has domain_service properly injected.
            # Passing an empty list to synthesize_model to get a simulated/generic model for the perspective.
            perspective_model_obj = await self.app_service.domain_service.synthesize_model([])
            perspective_metrics = self.app_service.domain_service.calculate_metrics(perspective_model_obj)

            multi_results[perspective] = {
                "model": perspective_model_obj.to_dict() if hasattr(perspective_model_obj, 'to_dict') else {},
                "metrics": perspective_metrics if perspective_metrics else {}
            }

        return multi_results

    async def _synthesize_results(self, multidim_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sintetiza los resultados de los análisis de múltiples perspectivas.

        Actualmente, esta función es un passthrough simple y devuelve los resultados
        multidimensionales tal como se reciben. En futuras implementaciones, podría
        realizar una lógica de agregación o síntesis más compleja sobre los modelos
        y métricas de las diferentes perspectivas.

        Args:
            multidim_results: Un diccionario que contiene los resultados del análisis
                              inicial y de cada perspectiva analizada.

        Returns:
            El mismo diccionario `multidim_results` (por ahora).
        """
        # El comentario original de print ya ha sido eliminado o comentado.
        # La lógica actual es devolver directamente, como se especifica.
        return multidim_results

class AdaptiveAnalysisEngine:
    """Motor que adapta el análisis según feedback (Conceptual)."""
    def __init__(self):
        self.learning_rate = 0.01
        self.performance_history: List[Any] = []
        self.strategy_weights = {'exhaustive': 1.0, 'progressive': 1.0, 'temporal': 1.0, 'emergent': 1.0}

    def adapt_strategy(self, performance_metrics: dict) -> None:
        gradients = self._calculate_performance_gradients(performance_metrics)
        for strategy, gradient in gradients.items():
            if strategy in self.strategy_weights:
                self.strategy_weights[strategy] += self.learning_rate * gradient
        self._normalize_weights()

    def _normalize_weights(self):
        total = sum(self.strategy_weights.values())
        if total > 0: self.strategy_weights = {k: v / total for k, v in self.strategy_weights.items()}
        else:
            num_strategies = len(self.strategy_weights)
            if num_strategies > 0: self.strategy_weights = {k: 1.0/num_strategies for k in self.strategy_weights}

    def _calculate_performance_gradients(self, metrics: dict) -> Dict[str, float]:
        # print("AdaptiveAnalysisEngine: Calculating performance gradients (placeholder).")
        return {s: metrics.get(f"{s}_score_improvement", random.uniform(-0.1, 0.1)) for s in self.strategy_weights}

    def select_optimal_path(self, analysis_context: dict) -> List[str]:
        context_features = self._extract_context_features(analysis_context)
        strategy_scores = {
            s: w * self._evaluate_strategy_fit(s, context_features) for s, w in self.strategy_weights.items()
        }
        return [s_name for s_name, _ in sorted(strategy_scores.items(), key=lambda x: x[1], reverse=True)]

    def _extract_context_features(self, context: dict) -> Dict[str, Any]:
        # print("AdaptiveAnalysisEngine: Extracting context features (placeholder).")
        return {"data_size": context.get("data_size", 100), "complexity_est": context.get("complexity_estimate", 0.5)}

    def _evaluate_strategy_fit(self, strategy: str, features: Dict[str, Any]) -> float:
        # print(f"AdaptiveAnalysisEngine: Evaluating fit for strategy {strategy} (placeholder).")
        if strategy == 'exhaustive': return 1.0 / (1 + features.get("data_size", 1000) * 0.01 + 1e-6) # Avoid div by zero
        return random.random()


# --- CubeHoneycombIntegration Class and its methods ---
# Moved from mdu_cube_system.py (Section 8.6) to application layer

class CubeHoneycombIntegration:
    __version__ = "0.1.0-alpha-refactored"

    def __init__(self):
        self.cube = CuboMDU()
        self.honeycomb = HoneycombGrid(radius=3)
        self.path_optimizer = PathOptimizer(self.honeycomb) # PathOptimizer now only takes honeycomb
        self.replication_manager = ReplicationManager(self.honeycomb, replication_factor=2)
        self.consensus_engine = ConsensusEngine(threshold=0.51)

    def _find_optimal_cell(self, segment_info: dict) -> HexagonalCell:
        target_layer = segment_info.get('target_layer_hint', 'application') # Use the hint from mapping
        layer_cells = [cell for cell in self.honeycomb.cells.values() if cell.layer == target_layer]
        if not layer_cells:
            layer_cells = list(self.honeycomb.cells.values()) # Fallback to any cell
        return random.choice(layer_cells) if layer_cells else list(self.honeycomb.cells.values())[0]


    def _map_analysis_to_space(self, session_data: str, strategy: str) -> dict:
        analysis_id = f"mdu_analysis_{hashlib.md5(session_data.encode() + strategy.encode()).hexdigest()[:10]}"
        # print(f"CubeHoneycombIntegration: Mapping analysis {analysis_id} (strategy: {strategy})")
        num_segments = random.randint(1,3) # Dynamic number of segments
        segments = []
        chunk_size = (len(session_data) + num_segments -1) // num_segments
        for i in range(num_segments):
            segment_data_payload = session_data[i*chunk_size : (i+1)*chunk_size]
            # Assign target layer more meaningfully if possible, or cycle
            target_layer = self.honeycomb.layers[i % len(self.honeycomb.layers)]
            segments.append({
                "segment_id": f"{analysis_id}_seg{i+1}",
                "data_payload": segment_data_payload,
                "target_layer_hint": target_layer,
                "original_analysis_id": analysis_id
            })
        return {"analysis_id": analysis_id, "strategy_applied": strategy, "segments": segments}

    async def execute_distributed_analysis(self, session_data: str, strategy: str = 'adaptive') -> dict:
        """
        Ejecuta un análisis distribuido utilizando el sistema de colmena (Honeycomb).

        Este método orquesta un flujo de trabajo complejo que incluye:
        1. Mapeo del análisis al espacio de la colmena (`_map_analysis_to_space`).
        2. Distribución de segmentos de datos a celdas óptimas y replicación del análisis
           inicial en esas celdas (`replication_manager.replicate_analysis`).
        3. Propagación de los resultados del análisis a través de la colmena en ondas
           (`WavePropagation.propagate_analysis`).
        4. Logro de un consenso sobre los resultados propagados (`consensus_engine.achieve_consensus`).
        5. Análisis de los datos consensuados desde múltiples perspectivas conceptuales del cubo
           (`_analyze_from_multiple_perspectives`).
        6. Integración de los resultados de las perspectivas en un modelo final
           (`_integrate_perspectives`).
        7. Recopilación de métricas de rendimiento.

        Args:
            session_data: Los datos de entrada para el análisis (string).
            strategy: La estrategia a utilizar para el análisis (e.g., 'adaptive').

        Returns:
            Un diccionario que contiene los resultados del análisis distribuido, incluyendo:
                - 'analysis_id': ID único del análisis.
                - 'strategy_used': La estrategia empleada.
                - 'distributed_cells_initiated_waves': Número de celdas que iniciaron ondas.
                - 'consensus_confidence': Confianza del consenso logrado (si aplica).
                - 'final_model': El modelo integrado final.
                - 'performance_metrics': Métricas de rendimiento de la ejecución.
        """
        analysis_map = self._map_analysis_to_space(session_data, strategy)
        analysis_id = analysis_map['analysis_id']

        data_for_wave_propagation_starts: Dict[str, Tuple[HexagonalCell, Dict[Any, Any]]] = {}

        for segment_details in analysis_map['segments']:
            optimal_start_cell = self._find_optimal_cell(segment_details)
            replicated_outputs = await self.replication_manager.replicate_analysis(
                optimal_start_cell, segment_details, analysis_id
            )
            if replicated_outputs:
                first_successful_cell, first_successful_result = replicated_outputs[0]
                data_for_wave_propagation_starts[segment_details['segment_id']] = (first_successful_cell, first_successful_result)
            # else:
                # print(f"CubeHoneycombIntegration: Segment {segment_details['segment_id']} - no successful replicas.")

        wave_propagator = WavePropagation(self.honeycomb)
        all_propagation_run_outputs: Dict[str, Any] = {}

        for segment_id, (start_cell, initial_data_for_wave) in data_for_wave_propagation_starts.items():
            propagation_run_summary = await wave_propagator.propagate_analysis(start_cell, initial_data_for_wave)
            all_propagation_run_outputs[f"wave_from_{segment_id}_at_{start_cell.cell_id[:4]}"] = propagation_run_summary

        results_for_final_consensus = {
            key: prop_run_dict.get("aggregation_summary", prop_run_dict)
            for key, prop_run_dict in all_propagation_run_outputs.items()
        }
        if not results_for_final_consensus and data_for_wave_propagation_starts:
             results_for_final_consensus = {seg_id: res_dict for seg_id, (_, res_dict) in data_for_wave_propagation_starts.items()}

        consensus_output = await self.consensus_engine.achieve_consensus(results_for_final_consensus)
        base_data_for_perspectives = consensus_output.get('result_payload', {})
        perspectives_analyzed = await self._analyze_from_multiple_perspectives(base_data_for_perspectives)
        final_integrated_model = self._integrate_perspectives(perspectives_analyzed)

        return {
            'analysis_id': analysis_id,
            'strategy_used': strategy,
            'distributed_cells_initiated_waves': len(data_for_wave_propagation_starts),
            'consensus_confidence': consensus_output.get('confidence', 0.0 if consensus_output.get('consensus_achieved') else None),
            'final_model': final_integrated_model,
            'performance_metrics': self._collect_performance_metrics( # Call with argument
                 num_segments=len(analysis_map['segments']),
                 num_waves=len(all_propagation_run_outputs)
            )
        }

    async def _analyze_from_multiple_perspectives(self, base_result: dict) -> List[dict]:
        perspectives_data = []
        rotations_to_simulate = [("X_View_App", (90,0,0)), ("Y_View_App", (0,90,0)), ("Z_View_App", (0,0,90))]

        for persp_name, (rx,ry,rz) in rotations_to_simulate:
            # print(f"CubeHoneycombIntegration: Simulating cube rotation for perspective {persp_name}")
            # self.cube.rotate(rx,ry,rz) # Placeholder, actual rotation would modify cube state
            # remapped_view = self._remap_honeycomb_to_cube() # Placeholder
            # perspective_specific_analysis_result = await self._analyze_perspective(base_result, remapped_view)

            # Simplified placeholder logic for re-analysis:
            perspective_specific_analysis_result = {
                **base_result,
                f"insight_from_{persp_name}": f"Unique finding for {persp_name} generated in AppLayer",
                "perspective_applied_in_app": persp_name
            }
            unique_insights_found = self._extract_unique_insights(perspective_specific_analysis_result, base_result)
            perspectives_data.append({
                'perspective_name': persp_name,
                'simulated_rotation_params': (rx,ry,rz),
                'result_after_perspective': perspective_specific_analysis_result,
                'unique_insights_identified': unique_insights_found
            })
        # self.cube.reset_orientation()
        return perspectives_data

    def _remap_honeycomb_to_cube(self) -> Dict[str, str]:
        # print("CubeHoneycombIntegration: Remapping honeycomb to new cube orientation (placeholder).")
        return {"mapping_info": "details_of_remapped_view_based_on_cube_state_applayer"}

    async def _analyze_perspective(self, base_result: dict, remapped_cells_view: Dict[str, str]) -> dict:
        # print(f"CubeHoneycombIntegration: Analyzing from new perspective using {remapped_cells_view.get('mapping_info')}")
        return {**base_result, "perspective_analysis_flag_app": True, "view_details_app": remapped_cells_view.get('mapping_info')}

    def _extract_unique_insights(self, perspective_result: dict, base_result: Optional[dict] = None) -> List[str]:
        insights = []
        for key, value in perspective_result.items():
            if base_result is None or key not in base_result or base_result[key] != value:
                if "insight_from_" in key: insights.append(str(value))
        return insights if insights else ["generic_app_layer_insight"]

    def _integrate_perspectives(self, perspectives_output_list: List[dict]) -> dict:
        # print("CubeHoneycombIntegration: Integrating results from multiple perspectives.")
        final_output: Dict[str, Any] = {"integration_summary_app": "Perspectives combined at App Layer."}
        all_insights_collected: List[str] = []

        # Use the result from the first perspective as a base if available
        if perspectives_output_list and 'result_after_perspective' in perspectives_output_list[0]:
            final_output['base_model_merged'] = perspectives_output_list[0]['result_after_perspective'].copy()
        else:
            final_output['base_model_merged'] = {}

        for i, p_data in enumerate(perspectives_output_list):
            perspective_name = p_data.get('perspective_name','unknown_perspective')
            final_output[f"data_from_perspective_{i}_{perspective_name}"] = p_data.get('result_after_perspective')
            all_insights_collected.extend(p_data.get('unique_insights_identified', []))

        final_output["combined_unique_insights_app"] = list(set(all_insights_collected))
        return final_output

    def _collect_performance_metrics(self, num_segments: int, num_waves: int) -> dict:
        return {
            "app_avg_cell_load_sim": random.uniform(0.1, 0.7),
            "app_total_processing_time_ms_sim": random.randint(300, 3000),
            "app_num_segments_processed": num_segments,
            "app_num_waves_propagated": num_waves,
            "app_consensus_history_len": len(self.consensus_engine.voting_history)
        }
