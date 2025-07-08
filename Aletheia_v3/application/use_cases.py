from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json # For session_data_for_uc in ApplicationFace (if kept here)
import contextlib # For nullcontext in refactored execute_multilevel_analysis
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
    monitoring: Optional[Any] # Optional CubeMonitoring, will be injected

    def __init__(self, repository: IAnalysisRepository, tracker: IExperimentTracker, queue: ITaskQueue, domain_service: DomainService, monitoring: Optional[Any] = None): # Adjusted as per instructions
        self.repository = repository
        self.tracker = tracker
        self.queue = queue
        self.domain_service = domain_service
        self.monitoring = monitoring

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
        if self.monitoring:
            self.monitoring.increment_active_analyses()

        run_id = "default_run_id" # Inicializar por si start_run falla o monitoring es None

        try:
            strategy = config.get('strategy', 'default')

            # Context manager condicional
            duration_tracker = self.monitoring.track_analysis_duration(level="full_multilevel", strategy=strategy) if self.monitoring else contextlib.nullcontext()

            with duration_tracker:
                run_id = self.tracker.start_run(f"analysis_{config.get('session_id', 'unknown_session')}")
                self.tracker.log_params(config)

                atoms = await self.domain_service.extract_atomic_units(session_data_str)
                clusters = await self.domain_service.form_clusters(atoms)
                theories = await self.domain_service.build_mini_theories(clusters)
                unified_model_obj = await self.domain_service.synthesize_model(theories)

                # Prepare data for repository (expects AnalysisData Pydantic model from ports.py)
                unified_model_dict = unified_model_obj.to_dict()
                analysis_id_for_repo = config.get('id', config.get('session_id', 'default_analysis_id'))
                session_id_for_repo = config.get('session_id', 'default_session_id')
                model_data_from_theory = unified_model_dict.get('model_data', {})
                metrics_from_theory = unified_model_dict.get('metrics', {})
                if 'levels' not in model_data_from_theory:
                    model_data_from_theory['levels'] = []

                analysis_data_payload = {
                    "id": analysis_id_for_repo,
                    "session_id": session_id_for_repo,
                    "model_data": model_data_from_theory,
                    "metrics": metrics_from_theory,
                    # status and created_at can be defaulted by AnalysisData or set by the repository
                }
                from .ports import AnalysisData # Import here to avoid circularity if AnalysisData moves
                analysis_pydantic_obj = AnalysisData(**analysis_data_payload)
                saved_analysis_id = await self.repository.save(analysis_pydantic_obj) # repository.save returns the id
                calculated_metrics = self.domain_service.calculate_metrics(unified_model_obj)
                self.tracker.log_metrics(calculated_metrics)

                # El 'return' debe estar dentro del bloque 'try' (y 'with')
                return {
                    "analysis_id": saved_analysis_id,
                    "run_id": run_id,
                    "model": analysis_pydantic_obj.model_dump(),
                    "metrics": calculated_metrics
                }
        finally:
            if run_id != "default_run_id": # Solo terminar el run si se inició
                self.tracker.end_run()
            if self.monitoring:
                self.monitoring.decrement_active_analyses()


# The ApplicationFace from mdu_cube_system.py acts as a higher-level service facade or controller.
# It's not strictly a use case itself but orchestrates them.
# For now, placing it here as it was closely tied to AnalysisUseCase.
# It might be better placed in a dedicated 'services.py' or refactored.
class ApplicationServiceFacade: # Renamed from ApplicationFace for clarity
    def __init__(self, domain_service: DomainService, repo: IAnalysisRepository, tracker: IExperimentTracker, queue: ITaskQueue, monitoring: Optional[Any] = None): # Added monitoring
        self.analysis_use_case = AnalysisUseCase(repo, tracker, queue, domain_service, monitoring) # Pass monitoring
        self.domain_service = domain_service
        # self.monitoring = monitoring # Facade itself might not need to store it if only AnalysisUseCase uses it

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

    def _calculate_success_metric(self, metrics: dict) -> float:
        """
        Calcula una métrica de éxito compuesta basada en las métricas de rendimiento.
        """
        confidence = metrics.get('consensus_confidence', 0.0) or 0.0 # Asegurar que no sea None

        num_insights = 0
        final_model = metrics.get('final_model')
        if isinstance(final_model, dict):
            # La estructura esperada es que final_model contenga combined_unique_insights_app
            # como se define en CubeHoneycombIntegration._integrate_perspectives
            insights = final_model.get('combined_unique_insights_app', [])
            if isinstance(insights, list):
                num_insights = len(insights)

        # Métrica de éxito: ponderar confianza y número de insights (normalizado)
        # Normalizar num_insights a un rango [0,1] (ej. capado a 10 insights max para la contribución)
        normalized_insights_score = min(num_insights, 10) / 10.0

        success_score = (confidence * 0.7) + (normalized_insights_score * 0.3)
        return success_score

    def _calculate_performance_gradients(self, performance_metrics: dict) -> Dict[str, float]:
        """
        Calcula los gradientes de rendimiento para cada estrategia.
        El gradiente es positivo si la estrategia usada tuvo éxito, negativo si no.
        Las estrategias no usadas tienen gradiente cero.
        """
        success_score = self._calculate_success_metric(performance_metrics)

        gradients: Dict[str, float] = {}
        strategy_used = performance_metrics.get('strategy_used', 'exhaustive') # Default a una estrategia conocida

        for strategy_name in self.strategy_weights.keys():
            if strategy_name == strategy_used:
                # El gradiente es la "sorpresa": éxito actual vs. un umbral (0.5).
                # Un valor > 0 significa mejor que el umbral, < 0 peor.
                gradient = success_score - 0.5
                gradients[strategy_name] = gradient
            else:
                # No actualizamos las estrategias que no se usaron en esta ronda.
                gradients[strategy_name] = 0.0

        return gradients

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
        """
        Evalúa qué tan adecuada es una estrategia dado un contexto de análisis.
        Devuelve un score entre (aprox) 0.1 y 1.0.
        """
        data_size = features.get('data_size', 1000) # Default si no está
        complexity = features.get('complexity_est', 0.5) # Default si no está

        score = 0.1 # Default score bajo

        if strategy == 'exhaustive':
            # Favorece datos pequeños y de baja complejidad. Penalizado por tamaño y complejidad.
            # El score disminuye a medida que data_size o complexity aumentan.
            # (data_size / 5000.0) -> 0.2 para data_size=1000; 1.0 para data_size=5000; 2.0 para data_size=10000
            # complexity es 0.0 a 1.0
            denominator = 1.0 + (data_size / 5000.0) + (complexity * 2.0) # Ponderar más la complejidad
            score = 1.0 / denominator if denominator > 0.1 else 0.1 # Evitar división por cero o score muy alto

        elif strategy == 'progressive':
            # Bueno para datos de tamaño medio, menos sensible a la complejidad inicial.
            # Score base alto, penalizado ligeramente por extremos de tamaño.
            base_score = 0.8
            if data_size > 15000 or data_size < 500:
                base_score -= 0.2 # Penalización mayor
            elif data_size > 8000 or data_size < 1000:
                base_score -= 0.1
            # Ligera penalización por muy baja complejidad (podría no necesitar 'progressive')
            if complexity < 0.2:
                 base_score -= 0.1
            score = base_score

        elif strategy == 'temporal' or strategy == 'causal':
            # Favorecido si la complejidad estimada es alta (sugiere que hay estructura para encontrar).
            # Score base + bonus por complejidad.
            score = 0.3 + complexity * 0.7 # Rango ~0.3 a 1.0

        elif strategy == 'emergent':
             # Favorecido por datos grandes y de alta complejidad.
             # Normalizar data_size, ej. capado a 20000 para el score.
             norm_data_size = min(data_size, 20000) / 20000.0 # Rango 0 a 1
             # Score base bajo, aumenta con tamaño y complejidad
             score = 0.1 + (norm_data_size * 0.45) + (complexity * 0.45) # Rango ~0.1 a 1.0

        return max(0.05, min(score, 1.0)) # Asegurar que el score esté entre 0.05 y 1.0


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

# --- Casos de Uso del Eje X (Ingesta y Vinculación) ---
import uuid
from datetime import datetime, timezone

from .ports import IConceptRepository # Asegurar que IConceptRepository esté en ports.py
from ..core.domain_models import ScientificConcept, ConceptType
# Actualizar la ruta de importación de DTOs para que apunte a api.schemas
from ..api.schemas import (
    IngestDocumentRequest as IngestDocumentInput, # Usar alias si los casos de uso esperan nombres específicos
    IngestDocumentResponse as IngestDocumentResult,
    UCMExtractionRequestSchema as UCMExtractionInput, # Ajustar según los nombres en schemas.py
    UCMExtractionResponseSchema as UCMExtractionResult,
    LinkConceptsRequest as LinkConceptsInput,
    LinkConceptsResponse as LinkConceptsResult,
    RelationshipSchema as RelationshipDTO # Si LinkConceptsResult usa RelationshipDTO con ese nombre
)
# Nota: Los nombres exactos de los DTOs/Schemas importados deben coincidir con los definidos en api.schemas.py
# Si se usaron nombres como IngestDocumentInput en schemas.py, no se necesita alias.
# Revisando schemas.py, los nombres son IngestDocumentRequest, UCMExtractionRequestSchema, etc.
# Los alias son una buena forma de mantener la lógica del caso de uso sin cambios si los nombres de DTO internos eran diferentes.

# Placeholder para ExtractUCMsUseCase si no está definido en otra parte.
# En una implementación real, esto se importaría de su módulo correspondiente.
# Si ya existe en este archivo (lo cual es poco probable para un caso de uso diferente),
# esta definición no sería necesaria.
# class ExtractUCMsUseCase: # Comentado para evitar redefinición si ya existe.
#     async def execute(self, input_data: UCMExtractionInput) -> UCMExtractionResult:
#         print(f"Placeholder ExtractUCMsUseCase: Processing text for {input_data.source_document_id}")
#         return UCMExtractionResult(
#             source_document_id=input_data.source_document_id,
#             extracted_concepts=[],
#             extracted_relationships=[],
#             processing_log=["Placeholder UCM extraction complete."]
#         )

# Para que el código sea ejecutable, necesito una definición de ExtractUCMsUseCase.

# --- Implementación Real de ExtractUCMsUseCase ---
import re
from collections import Counter
# uuid, datetime, timezone, IConceptRepository, IRelationshipRepository,
# ScientificConcept, ConceptType, DirectedRelationship
# UCMExtractionInput, UCMExtractionResponseSchema, ExtractedUCMSchema, ExtractedRelationshipSchema
# ya están importados o se importarán con los otros casos de uso del Eje X.
import spacy # For NER
import logging # For logging spaCy model loading issues

logger = logging.getLogger(__name__)

# Definir constantes para la extracción (pueden ser eliminadas o ajustadas si NER es suficiente)
# STOP_WORDS_UCM = set([...])
# PHRASE_REGEX_UCM = re.compile(...)
# SINGLE_WORD_REGEX_UCM = re.compile(...)

class ExtractUCMsUseCase: # Reemplaza el Protocol
    """
    Caso de uso para extraer Unidades Conceptuales Mínimas (UCMs) y sus relaciones
    a partir del contenido textual de un documento. Utiliza NER y opcionalmente regex.
    """
    def __init__(self,
                 concept_repo: IConceptRepository,
                 relationship_repo: IRelationshipRepository):
        self.concept_repo = concept_repo
        self.relationship_repo = relationship_repo
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model 'en_core_web_sm' loaded successfully for ExtractUCMsUseCase.")
        except OSError:
            logger.error(
                "spaCy model 'en_core_web_sm' not found. "
                "Please download it by running: python -m spacy download en_core_web_sm"
            )
            self.nlp = None # Allow graceful degradation or raise an error

    # Regex-based extraction can be kept as a helper or complementary method
    def _extract_terms_via_regex(self, text: str, min_freq: int = 2) -> List[str]:
        # ... (previous _extract_terms_from_text logic can be moved here or adapted)
        # For now, let's assume it's available if needed.
        # This is just a placeholder for where the old logic would go.
        text_lower = text.lower()
        potential_terms = set()
        # Simplified version of previous regex logic for brevity in this diff
        # In real implementation, copy the full logic if used.
        # Example:
        # phrase_regex = re.compile(r'\b[A-Z][\w\s-]*[a-zA-Z0-9]\b')
        # for match in phrase_regex.finditer(text):
        # potential_terms.add(match.group(0).strip())
        return sorted(list(potential_terms))


    async def execute(self, input_data: UCMExtractionInput) -> UCMExtractionResponseSchema:
        persisted_concepts_dtos: List[ExtractedUCMSchema] = []
        persisted_concept_entities: List[ScientificConcept] = []
        processing_log = [f"Processing text of length: {len(input_data.text_content)} characters."]

        extracted_entities_info = [] # To store (text, label, start_char, end_char) from NER

        if self.nlp:
            doc = self.nlp(input_data.text_content)
            processing_log.append(f"Processed text with spaCy NER. Found {len(doc.ents)} entities.")

            for ent in doc.ents:
                extracted_entities_info.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start_char": ent.start_char,
                    "end_char": ent.end_char
                })

                ucm_id = f"ucm_ner_{uuid.uuid4().hex}"
                # Map NER labels to a more generic description or keep as is
                description_ucm = f"Named Entity: {ent.label_} ('{ent.text}') identified by spaCy NER."

                concept_properties = {
                    "source_document_id": input_data.source_document_id,
                    "extraction_method": "spacy_ner_en_core_web_sm",
                    "ner_label": ent.label_,
                    "ner_entity_text": ent.text,
                    "start_char": ent.start_char,
                    "end_char": ent.end_char,
                    **(input_data.source_metadata or {})
                }

                ucm_entity = ScientificConcept(
                    id=ucm_id,
                    name=ent.text, # Use entity text as name
                    description=description_ucm,
                    concept_type=ConceptType.UCM, # Or map ent.label_ to a more specific ConceptType
                    properties=concept_properties,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                await self.concept_repo.add(ucm_entity)
                persisted_concept_entities.append(ucm_entity)
                persisted_concepts_dtos.append(ExtractedUCMSchema(
                    id=ucm_entity.id, name=ucm_entity.name, description=ucm_entity.description,
                    concept_type=ucm_entity.concept_type.value, # Use enum's value
                    metadata=ucm_entity.properties
                ))
            processing_log.append(f"Persisted {len(persisted_concepts_dtos)} UCMs from NER.")
        else:
            processing_log.append("spaCy NLP model not available. NER extraction skipped.")

        # --- Optional: Complementary Regex Extraction ---
        # Ensure regex terms do not significantly overlap with NER entities to avoid redundancy.
        # This is a simple overlap check based on text; more sophisticated merging might be needed.
        # For now, this part is conceptual and not fully implemented to keep diff manageable.
        # if self.nlp: # Only run regex if NER ran, to complement it
        #     regex_terms = self._extract_terms_via_regex(input_data.text_content)
        #     ner_entity_texts = {info['text'] for info in extracted_entities_info}
        #     complementary_terms_added = 0
        #     for term in regex_terms:
        #         if term not in ner_entity_texts: # Basic check, ignores partial overlaps
        #             # ... (create ScientificConcept for regex term, similar to above) ...
        #             # ... (append to persisted_concepts_dtos and persisted_concept_entities) ...
        #             complementary_terms_added +=1
        #     if complementary_terms_added > 0:
        #         processing_log.append(f"Added {complementary_terms_added} UCMs from complementary regex extraction.")

        if not persisted_concept_entities:
            processing_log.append("No UCMs were extracted from the document.")
            # Fallback to old regex if NER produced nothing and NLP model was available
            # This part is removed for now to simplify the primary NER focus.
            # If NER is primary and produces nothing, that might be the intended outcome.

        # Relationship generation (placeholder, as per original logic, if still desired)
        # This part might need re-evaluation if UCMs are now more granular or different.
        # For now, keeping the simple co-occurrence based relationship generation.
        persisted_relationships_dtos: List[ExtractedRelationshipSchema] = []
        if len(persisted_concept_entities) > 1:
            # ... (original relationship generation logic can be copied here) ...
            # This creates relationships between ALL persisted UCMs (NER + optional regex)
            # This part is kept similar to original for brevity in this diff.
            for i in range(len(persisted_concept_entities)):
                for j in range(i + 1, len(persisted_concept_entities)):
                    source_ucm = persisted_concept_entities[i]
                    target_ucm = persisted_concept_entities[j]
                    rel_id = f"rel_{uuid.uuid4().hex}"
                    rel_description = f"Relación temática inferida (co-occurrence) entre '{source_ucm.name}' y '{target_ucm.name}'."
                    relationship_entity = DirectedRelationship(
                        id=rel_id, source_concept_id=source_ucm.id, target_concept_id=target_ucm.id,
                        type="RELATED_TO_DOCUMENT_CONTEXT", description=rel_description,
                        properties={"source_document_id": input_data.source_document_id, "inference_method": "co-occurrence_in_document_v2_ner_based"},
                        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
                    )
                    await self.relationship_repo.add(relationship_entity)
                    persisted_relationships_dtos.append(ExtractedRelationshipSchema(
                        id=relationship_entity.id, source_ucm_id=relationship_entity.source_concept_id,
                        target_ucm_id=relationship_entity.target_concept_id, type=relationship_entity.type,
                        description=relationship_entity.description, metadata=relationship_entity.properties
                    ))
            processing_log.append(f"Creadas {len(persisted_relationships_dtos)} relaciones entre UCMs.")


        return UCMExtractionResponseSchema(
            source_document_id=input_data.source_document_id,
            extracted_concepts=persisted_concepts_dtos,
            extracted_relationships=persisted_relationships_dtos,
            processing_log=processing_log
        )

# --- Interfaces (Protocolos) para otros Casos de Uso del Eje Y ---
from ..api.schemas import ( # Suponiendo que los schemas placeholder están en api.schemas
    FormClusterInputSchema, FormClusterResultSchema,
    PropositionDerivationInputSchema, PropositionDerivationResultSchema,
    MiniTheoryConstructionInputSchema, MiniTheoryConstructionResultSchema,
    ComprehensiveTheoriesInputSchema, ComprehensiveTheoriesResultSchema,
    UnifiedModelsInputSchema, UnifiedModelsResultSchema
)
import re # Para tokenización simple
from collections import Counter, defaultdict # Para clustering por palabras clave
# Nota: uuid, datetime, timezone, IConceptRepository, ScientificConcept, ConceptType
# ya están importados en el contexto del archivo use_cases.py.

# Adapter for MDL
from ..core.mdl_synthesis.adapters import map_concept_to_representation
# For placeholder embeddings
import numpy as np
# For unique IDs
import uuid
# For timestamps
from datetime import datetime, timezone


# Stopwords muy básicas, se podrían expandir
STOP_WORDS = set([
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "should", "can",
    "could", "may", "might", "must", "and", "but", "or", "nor", "for", "so", "yet",
    "in", "on", "at", "by", "from", "to", "with", "about", "above", "below",
    "of", "s", "t"
])

MIN_COMMON_KEYWORDS_FOR_CLUSTER = 2


class FormClustersUseCase: # Reemplaza el Protocol
# Import FindOptimalModelUseCase for dependency injection
from .mdl_synthesis_use_cases import FindOptimalModelUseCase

class FormClustersUseCase: # Reemplaza el Protocol
    """
    Caso de uso para formar clústeres de conceptos (UCMs).
    Refactorizado para usar FindOptimalModelUseCase para seleccionar el mejor clustering.
    """
    def __init__(self,
                 concept_repo: IConceptRepository,
                 find_optimal_model_uc: FindOptimalModelUseCase):
        self.concept_repo = concept_repo
        self.find_optimal_model_uc = find_optimal_model_uc

    def _extract_keywords(self, text: Optional[str]) -> Set[str]: # This method might become obsolete or change
        if not text:
            return set()
        # Tokenización simple y eliminación de stopwords
        words = re.findall(r'\b\w+\b', text.lower())
        return {word for word in words if word not in STOP_WORDS and len(word) > 2}

    async def execute(self, input_data: FormClusterInputSchema) -> FormClusterResponseSchema:
        """
        Ejecuta la formación de clústeres.

        1. Obtiene los ScientificConcepts (UCMs) de entrada.
        2. Extrae palabras clave de sus nombres y descripciones.
        3. Agrupa UCMs que compartan un número mínimo de palabras clave.
        4. Crea y persiste un nuevo ScientificConcept de tipo CLUSTER para cada grupo.
        5. Devuelve información sobre los clústeres creados.
        """
        if not input_data.ucm_ids:
            return FormClusterResponseSchema(created_clusters=[], message="No UCM IDs provided for clustering.")

        ucm_concepts: List[ScientificConcept] = []
        for ucm_id in input_data.ucm_ids:
            concept = await self.concept_repo.get_by_id(ucm_id)
            if concept and concept.concept_type == ConceptType.UCM:
                ucm_concepts.append(concept)
            # else: # Opcional: registrar advertencia si un ID no es UCM o no se encuentra

        if not ucm_concepts:
            return FormClusterResponseSchema(created_clusters=[], message="No valid UCMs found for clustering.")

        ucm_keywords: Dict[str, Set[str]] = {}
        for ucm in ucm_concepts:
            keywords = self._extract_keywords(ucm.name)
            if ucm.description:
                keywords.update(self._extract_keywords(ucm.description))
            if keywords:
                 ucm_keywords[ucm.id] = keywords

        potential_clusters_data: List[Dict[str, Any]] = []

        ucm_ids_with_keywords = list(ucm_keywords.keys())

        # Agrupación simple: encontrar conjuntos de UCMs que comparten al menos N keywords
        # Esta es una heurística y puede ser mejorada.
        # Aquí, cualquier par que comparta suficientes keywords inicia un potencial clúster,
        # luego se intenta una fusión muy simple.

        # Paso 1: Identificar todos los pares que comparten suficientes keywords
        candidate_links: Dict[str, Set[str]] = defaultdict(set)
        for i in range(len(ucm_ids_with_keywords)):
            for j in range(i + 1, len(ucm_ids_with_keywords)):
                ucm1_id = ucm_ids_with_keywords[i]
                ucm2_id = ucm_ids_with_keywords[j]

                common_kws = ucm_keywords[ucm1_id].intersection(ucm_keywords[ucm2_id])
                if len(common_kws) >= MIN_COMMON_KEYWORDS_FOR_CLUSTER:
                    candidate_links[ucm1_id].add(ucm2_id)
                    candidate_links[ucm2_id].add(ucm1_id)

        # Paso 2: Encontrar componentes conectados en el grafo de UCMs vinculados
        # Cada componente conectado formará un clúster.
        if not candidate_links:
             return FormClusterResponseSchema(created_clusters=[], message="No UCMs found sharing enough common keywords to form clusters.")

        visited_ucms = set()
        for ucm_id_start_node in ucm_ids_with_keywords:
            if ucm_id_start_node not in candidate_links or ucm_id_start_node in visited_ucms:
                continue

            current_cluster_members = set()
            queue = [ucm_id_start_node]
            visited_ucms.add(ucm_id_start_node)

            head = 0
            while head < len(queue):
                current_ucm = queue[head]
                head += 1
                current_cluster_members.add(current_ucm)
                for neighbor in candidate_links.get(current_ucm, set()):
                    if neighbor not in visited_ucms:
                        visited_ucms.add(neighbor)
                        queue.append(neighbor)

            if len(current_cluster_members) >= 2: # Solo formar clúster si hay al menos 2 miembros
                # Calcular las keywords compartidas por este clúster
                cluster_shared_keywords = set()
                if current_cluster_members:
                    # Intersección de todas las keywords de los miembros
                    # O unión y luego filtrar las que aparecen en muchos
                    # Por simplicidad, tomemos la intersección de todas las keywords de los miembros.
                    # Esto podría resultar en un conjunto vacío si no todas comparten las mismas.
                    # Una mejor aproximación sería tomar las keywords más frecuentes entre los miembros.

                    # Estrategia alternativa para shared_keywords:
                    # Tomar todas las keywords de los miembros y contar frecuencias.
                    # Las keywords que aparecen en > X% de los miembros son las "shared_keywords".
                    # O, las keywords que llevaron a la formación del clúster (más complejo de rastrear con CC).
                    # Por ahora, tomaremos la intersección de las keywords del primer par que inició el componente.
                    # Esto es una simplificación.

                    # Lógica mejorada para shared_keywords: unión de todas las keywords de los miembros del clúster
                    all_kws_in_cluster = set()
                    for member_id in current_cluster_members:
                        all_kws_in_cluster.update(ucm_keywords.get(member_id, set()))

                    # Y luego, filtrar las que son comunes a al menos MIN_COMMON_KEYWORDS_FOR_CLUSTER UCMs *dentro* del clúster
                    # O, más simple, las keywords que aparecen en más de N miembros del clúster.
                    # Por ahora, usar una intersección de un par representativo o las más comunes.
                    # Para este ejemplo, vamos a usar las keywords que son comunes a *todos* los miembros del clúster
                    # si tal conjunto no es vacío y cumple el mínimo.
                    if current_cluster_members:
                        sets_of_keywords = [ucm_keywords.get(m_id, set()) for m_id in current_cluster_members]
                        if sets_of_keywords:
                            intersected_kws = sets_of_keywords[0].intersection(*sets_of_keywords[1:])
                            if len(intersected_kws) >= MIN_COMMON_KEYWORDS_FOR_CLUSTER: # O un umbral diferente
                                cluster_shared_keywords = intersected_kws
                            else: # Fallback: unión de todas las keywords
                                cluster_shared_keywords = all_kws_in_cluster if len(all_kws_in_cluster) < 15 else set(list(all_k_ws_in_cluster)[:15])


                if cluster_shared_keywords: # Solo si encontramos keywords representativas
                    potential_clusters_data.append({
                        "members": list(current_cluster_members),
                        "shared_kws": sorted(list(cluster_shared_keywords))
                    })

        created_cluster_infos: List[ConceptInfoSchema] = []

        for p_cluster_data in potential_clusters_data:
            member_ids = p_cluster_data["members"]
            shared_kws_list = p_cluster_data["shared_kws"]

            if not member_ids or not shared_kws_list: continue # Evitar clústeres vacíos o sin keywords

            cluster_name_kws = shared_kws_list[:3] # Usar hasta 3 keywords para el nombre
            cluster_name = f"Cluster: {', '.join(cluster_name_kws)}"
            if len(shared_kws_list) > 3:
                cluster_name += "..."
            cluster_name += f" ({len(member_ids)} UCMs)"

            # Generar ID para el nuevo concepto de clúster
            cluster_id = f"cluster_{uuid.uuid4().hex}"

            cluster_concept = ScientificConcept(
                id=cluster_id,
                name=cluster_name,
                description=f"Clúster de {len(member_ids)} UCMs compartiendo palabras clave comunes: {', '.join(shared_kws_list)}.",
                concept_type=ConceptType.CLUSTER,
                properties={
                    "member_concept_ids": member_ids,
                    "shared_keywords": shared_kws_list,
                    "cluster_algorithm": f"connected_components_keyword_overlap_min{MIN_COMMON_KEYWORDS_FOR_CLUSTER}"
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await self.concept_repo.add(cluster_concept)
            created_cluster_infos.append(ConceptInfoSchema(
                id=cluster_concept.id,
                name=cluster_concept.name,
                concept_type=cluster_concept.concept_type.value
            ))

        message = f"Procesados {len(ucm_concepts)} UCMs. Formados {len(created_cluster_infos)} clústeres."
        if not created_cluster_infos and ucm_concepts:
            message = "No se formaron clústeres con los criterios actuales."

        return FormClusterResponseSchema(created_clusters=created_cluster_infos, message=message)


class DerivePropositionsUseCase: # Nombre actualizado y reemplaza Protocol
    """
    Caso de uso para derivar proposiciones a partir de clústeres de conceptos.
    Refactorizado para usar FindOptimalModelUseCase.
    """
    def __init__(self,
                 concept_repo: IConceptRepository,
                 find_optimal_model_uc: FindOptimalModelUseCase): # Added dependency
        self.concept_repo = concept_repo
        self.find_optimal_model_uc = find_optimal_model_uc # Store dependency

    async def execute(self, input_data: PropositionDerivationInputSchema) -> PropositionDerivationResultSchema:
        """
        Ejecuta la derivación de proposiciones.

        1. Para cada ID de clúster proporcionado, obtiene el clúster.
        2. Extrae los UCMs miembros del clúster.
        3. Genera una o más proposiciones (conceptos de tipo PROPOSITION) basadas
           en los UCMs del clúster y las palabras clave compartidas del clúster.
        4. Persiste las nuevas proposiciones.
        5. Devuelve información sobre las proposiciones creadas.
        """
        if not input_data.cluster_ids:
            return PropositionDerivationResponseSchema(created_propositions=[], message="No cluster IDs provided for proposition derivation.")

        created_proposition_infos: List[ConceptInfoSchema] = []
        processed_clusters = 0

        for cluster_id in input_data.cluster_ids:
            cluster_concept = await self.concept_repo.get_by_id(cluster_id)

            if not cluster_concept or cluster_concept.concept_type != ConceptType.CLUSTER:
                # Opcional: Registrar advertencia si un ID no es un clúster válido o no encontrado
                continue

            processed_clusters += 1
            member_ucm_ids = cluster_concept.properties.get("member_concept_ids", [])
            shared_keywords = cluster_concept.properties.get("shared_keywords", [])

            if not member_ucm_ids or len(member_ucm_ids) < 1:
                continue

            member_ucms: List[ScientificConcept] = []
            for ucm_id in member_ucm_ids:
                ucm = await self.concept_repo.get_by_id(ucm_id)
                if ucm:
                    member_ucms.append(ucm)

            if not member_ucms:
                continue

            prop_name: str
            prop_description: str

            if len(member_ucms) == 1:
                ucm1_name = member_ucms[0].name
                prop_name = f"Proposición sobre: '{ucm1_name}'"
                prop_description = f"El concepto '{ucm1_name}' (del clúster '{cluster_concept.name}') sugiere una proposición basada en los temas: {', '.join(shared_keywords)}."
            else:
                ucm1_name = member_ucms[0].name
                ucm2_name = member_ucms[1].name
                additional_members_count = len(member_ucms) - 2

                name_suffix = f" y '{ucm2_name}'"
                if additional_members_count > 0:
                    name_suffix += f" (y otros {additional_members_count})"

                prop_name = f"Proposición conectando '{ucm1_name}'{name_suffix}"
                prop_description = (
                    f"Se propone una conexión temática entre los conceptos '{ucm1_name}'"
                    f"{name_suffix} dentro del clúster '{cluster_concept.name}'. "
                    f"Esta conexión se basa en los temas compartidos: {', '.join(shared_keywords)}."
                )

            proposition_id = f"prop_{uuid.uuid4().hex}"
            proposition_concept = ScientificConcept(
                id=proposition_id,
                name=prop_name,
                description=prop_description,
                concept_type=ConceptType.PROPOSITION,
                properties={
                    "based_on_cluster_id": cluster_id,
                    "involved_ucm_ids": member_ucm_ids,
                    "shared_keywords_from_cluster": shared_keywords,
                    "derivation_method": "heuristic_cluster_aggregation_v1"
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await self.concept_repo.add(proposition_concept)
            created_proposition_infos.append(ConceptInfoSchema(
                id=proposition_concept.id,
                name=proposition_concept.name,
                concept_type=proposition_concept.concept_type.value
            ))

        message = f"Procesados {processed_clusters} clústeres. Derivadas {len(created_proposition_infos)} proposiciones."
        if not created_proposition_infos and processed_clusters > 0:
            message = "No se derivaron nuevas proposiciones de los clústeres proporcionados con los criterios actuales."

        return PropositionDerivationResponseSchema(created_propositions=created_proposition_infos, message=message)


class MiniTheoryConstructionUseCase: # Reemplaza Protocol
    """
    Caso de uso para construir una mini-teoría a partir de un conjunto de proposiciones.
    Refactorizado para usar FindOptimalModelUseCase.
    """
    def __init__(self,
                 concept_repo: IConceptRepository,
                 find_optimal_model_uc: FindOptimalModelUseCase): # Added dependency
        self.concept_repo = concept_repo
        self.find_optimal_model_uc = find_optimal_model_uc # Store dependency

    async def execute(self, input_data: MiniTheoryConstructionInputSchema) -> MiniTheoryConstructionResultSchema:
        """
        Ejecuta la construcción de una mini-teoría.

        1. Valida que se proporcionen IDs de proposiciones.
        2. (Opcional) Valida que las proposiciones de entrada existan y sean de tipo PROPOSITION.
        3. Crea un nuevo ScientificConcept de tipo MINI_THEORY.
        4. Almacena los IDs de las proposiciones miembro en las propiedades del concepto.
        5. Persiste la nueva mini-teoría.
        6. Devuelve información sobre la mini-teoría creada.
        """
        if not input_data.proposition_ids:
            return MiniTheoryConstructionResponseSchema(created_mini_theory=None, message="No proposition IDs provided.")

        # Opcional: Validación de existencia y tipo de las proposiciones de entrada
        # valid_propositions = []
        # for prop_id in input_data.proposition_ids:
        #     prop = await self.concept_repo.get_by_id(prop_id)
        #     if prop and prop.concept_type == ConceptType.PROPOSITION:
        #         valid_propositions.append(prop)
        # if not valid_propositions:
        #     return MiniTheoryConstructionResponseSchema(created_mini_theory=None, message="No valid propositions found for the given IDs.")
        # proposition_ids_to_link = [p.id for p in valid_propositions]

        # Por ahora, asumimos que los IDs son válidos y procedemos directamente
        proposition_ids_to_link = input_data.proposition_ids

        mini_theory_id = f"minit_{uuid.uuid4().hex}"
        mini_theory_name = input_data.name or f"Mini-Teoría basada en {len(proposition_ids_to_link)} proposiciones"

        mini_theory_concept = ScientificConcept(
            id=mini_theory_id,
            name=mini_theory_name,
            description=f"Mini-teoría agregando las siguientes proposiciones: {', '.join(proposition_ids_to_link)}.",
            concept_type=ConceptType.MINI_THEORY, # Necesita estar en el Enum ConceptType
            properties={
                "member_proposition_ids": proposition_ids_to_link,
                "construction_method": "aggregation_v1"
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await self.concept_repo.add(mini_theory_concept)

        created_info = ConceptInfoSchema(
            id=mini_theory_concept.id,
            name=mini_theory_concept.name,
            concept_type=mini_theory_concept.concept_type.value
        )
        return MiniTheoryConstructionResponseSchema(created_mini_theory=created_info, message=f"Mini-teoría '{mini_theory_name}' creada con éxito.")


class ComprehensiveTheoriesUseCase: # Reemplaza Protocol
    """
    Caso de uso para construir una teoría comprehensiva a partir de un conjunto de mini-teorías.
    Refactorizado para usar FindOptimalModelUseCase.
    """
    def __init__(self,
                 concept_repo: IConceptRepository,
                 find_optimal_model_uc: FindOptimalModelUseCase): # Added dependency
        self.concept_repo = concept_repo
        self.find_optimal_model_uc = find_optimal_model_uc # Store dependency

    async def execute(self, input_data: ComprehensiveTheoriesInputSchema) -> ComprehensiveTheoriesResponseSchema:
        """
        Ejecuta la construcción de una teoría comprehensiva.

        1. Valida que se proporcionen IDs de mini-teorías.
        2. (Opcional) Valida que las entradas existan y sean de tipo MINI_THEORY.
        3. Crea un nuevo ScientificConcept de tipo COMPREHENSIVE_THEORY.
        4. Almacena los IDs de las mini-teorías miembro en las propiedades.
        5. Persiste la nueva teoría comprehensiva.
        6. Devuelve información sobre la teoría creada.
        """
        if not input_data.mini_theory_ids:
            return ComprehensiveTheoriesResponseSchema(created_comprehensive_theory=None, message="No mini-theory IDs provided for construction.")

        # 1. Load input mini-theory ScientificConcept objects
        input_mini_theories: List[ScientificConcept] = []
        for mt_id in input_data.mini_theory_ids:
            mt_concept = await self.concept_repo.get_by_id(mt_id)
            if mt_concept and mt_concept.concept_type == ConceptType.MINI_THEORY:
                input_mini_theories.append(mt_concept)
            else:
                # Handle case where a mini-theory ID is invalid or not a mini-theory
                # For now, log a warning or skip
                # logger.warning(f"Mini-theory with ID {mt_id} not found or not a MINI_THEORY.")
                pass

        if not input_mini_theories:
            return ComprehensiveTheoriesResponseSchema(created_comprehensive_theory=None, message="No valid mini-theories found for input IDs.")

        # 2. Generate Candidate Comprehensive Theories
        candidate_comp_theories: List[ScientificConcept] = []

        # Candidate 1: Aggregate all input mini-theories
        comp_theory_id_1 = f"compth_{uuid.uuid4().hex}"
        name_1 = input_data.name or f"Comprehensive Theory from {len(input_mini_theories)} mini-theories"
        desc_1 = f"Comprehensive theory integrating mini-theories: {', '.join(mt.name for mt in input_mini_theories)}."
        cand1_props = {
            "member_mini_theory_ids": [mt.id for mt in input_mini_theories],
            "construction_method": "mdl_aggregation_v1",
            "derivation_details": "Aggregated all provided mini-theories."
        }
        # Add placeholder embedding for the candidate theory itself
        cand1_props["embedding"] = np.random.rand(1, 384).tolist()[0] # Assuming 384-dim embeddings

        candidate_1 = ScientificConcept(
            id=comp_theory_id_1, name=name_1, description=desc_1,
            concept_type=ConceptType.COMPREHENSIVE_THEORY, properties=cand1_props,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )
        candidate_comp_theories.append(candidate_1)

        # Candidate 2: (If > 3 inputs) Aggregate a subset (e.g., first 3)
        if len(input_mini_theories) > 3:
            subset_mini_theories = input_mini_theories[:3]
            comp_theory_id_2 = f"compth_{uuid.uuid4().hex}"
            name_2 = f"Focused Comprehensive Theory from {len(subset_mini_theories)} mini-theories"
            desc_2 = f"Focused comprehensive theory from subset: {', '.join(mt.name for mt in subset_mini_theories)}."
            cand2_props = {
                "member_mini_theory_ids": [mt.id for mt in subset_mini_theories],
                "construction_method": "mdl_subset_aggregation_v1",
                "derivation_details": f"Aggregated first {len(subset_mini_theories)} provided mini-theories."
            }
            cand2_props["embedding"] = np.random.rand(1, 384).tolist()[0]
            candidate_2 = ScientificConcept(
                id=comp_theory_id_2, name=name_2, description=desc_2,
                concept_type=ConceptType.COMPREHENSIVE_THEORY, properties=cand2_props,
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
            )
            candidate_comp_theories.append(candidate_2)

        # Candidate 3: Alternative description for Candidate 1
        comp_theory_id_3 = f"compth_{uuid.uuid4().hex}"
        name_3 = input_data.name or f"Integrated Perspective from {len(input_mini_theories)} mini-theories"
        desc_3 = f"An integrated perspective synthesizing the following mini-theories: {'; '.join(mt.name for mt in input_mini_theories)}."
        cand3_props = { # Same members as candidate 1
            "member_mini_theory_ids": [mt.id for mt in input_mini_theories],
            "construction_method": "mdl_aggregation_v1_alt_desc",
            "derivation_details": "Aggregated all provided mini-theories with alternative phrasing."
        }
        cand3_props["embedding"] = np.random.rand(1, 384).tolist()[0]
        candidate_3 = ScientificConcept(
            id=comp_theory_id_3, name=name_3, description=desc_3,
            concept_type=ConceptType.COMPREHENSIVE_THEORY, properties=cand3_props,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )
        candidate_comp_theories.append(candidate_3)

        if not candidate_comp_theories:
            return ComprehensiveTheoriesResponseSchema(created_comprehensive_theory=None, message="Could not generate candidate comprehensive theories.")

        # 3. Map Candidates to ModelRepresentation
        model_representations = [map_concept_to_representation(ct) for ct in candidate_comp_theories]

        # 4. Invoke Optimization
        lambda_param = 1.0  # Example value, might need tuning
        try:
            optimization_result = self.find_optimal_model_uc.execute(
                candidate_models=model_representations,
                data=input_mini_theories, # Data D is the list of input mini-theory ScientificConcepts
                lambda_param=lambda_param,
                optimization_parameters={"use_case": "ComprehensiveTheoriesUseCase"}
            )
        except Exception as e:
            # logger.error(f"Error during MDL optimization in ComprehensiveTheoriesUseCase: {e}")
            return ComprehensiveTheoriesResponseSchema(created_comprehensive_theory=None, message=f"Optimization error: {e}")

        # 5. Process Result
        winning_theory_id_str = optimization_result.best_model.identifier
        winning_theory_concept = next((cand for cand in candidate_comp_theories if str(cand.id) == winning_theory_id_str), None)

        if not winning_theory_concept:
            # This should not happen if find_optimal_model_uc returns a valid model from candidates
            # logger.error("Winning comprehensive theory ID not found among candidates.")
            return ComprehensiveTheoriesResponseSchema(created_comprehensive_theory=None, message="Could not identify winning comprehensive theory among candidates.")

        # Update winning concept with MDL metrics if desired (optional, as per design they are in properties)
        winning_theory_concept.properties["mdl_synthesis_details"] = {
            "complexity": optimization_result.best_model_metrics.complexity,
            "log_likelihood": optimization_result.best_model_metrics.log_likelihood,
            "mdl_cost": optimization_result.best_model_metrics.mdl_cost,
            "parameters": optimization_result.parameters
        }
        winning_theory_concept.updated_at = datetime.now(timezone.utc)


        # 6. Persist and Return
        await self.concept_repo.add(winning_theory_concept)

        created_info = ConceptInfoSchema(
            id=str(winning_theory_concept.id), # Ensure ID is string for schema
            name=winning_theory_concept.name,
            concept_type=winning_theory_concept.concept_type.value
        )
        return ComprehensiveTheoriesResponseSchema(
            created_comprehensive_theory=created_info,
            message=f"Comprehensive theory '{winning_theory_concept.name}' selected and created via MDL."
        )


class UnifiedModelsUseCase: # Reemplaza Protocol
    """
    Caso de uso para sintetizar un modelo unificado a partir de teorías comprehensivas.
    """
    def __init__(self, concept_repo: IConceptRepository):
        self.concept_repo = concept_repo

    async def execute(self, input_data: UnifiedModelsInputSchema) -> UnifiedModelsResponseSchema:
        """
        Ejecuta la síntesis de un modelo unificado.

        1. Valida que se proporcionen IDs de teorías comprehensivas.
        2. (Opcional) Valida que las entradas existan y sean de tipo COMPREHENSIVE_THEORY.
        3. Crea un nuevo ScientificConcept de tipo UNIFIED_MODEL.
        4. Almacena los IDs de las teorías miembro en las propiedades.
        5. Persiste el nuevo modelo unificado.
        6. Devuelve información sobre el modelo creado.
        """
        if not input_data.comprehensive_theory_ids:
            return UnifiedModelsResponseSchema(created_unified_model=None, message="No comprehensive theory IDs provided.")

        # Asumimos que los IDs son válidos por ahora
        comp_theory_ids_to_link = input_data.comprehensive_theory_ids

        unified_model_id = f"unifiedm_{uuid.uuid4().hex}"
        unified_model_name = input_data.name or f"Modelo Unificado basado en {len(comp_theory_ids_to_link)} teorías"

        unified_model_concept = ScientificConcept(
            id=unified_model_id,
            name=unified_model_name,
            description=f"Modelo unificado agregando: {', '.join(comp_theory_ids_to_link)}.",
            concept_type=ConceptType.UNIFIED_MODEL, # Necesita estar en Enum ConceptType
            properties={
                "member_comprehensive_theory_ids": comp_theory_ids_to_link,
                "synthesis_method": "aggregation_v1"
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await self.concept_repo.add(unified_model_concept)

        created_info = ConceptInfoSchema(
            id=unified_model_concept.id,
            name=unified_model_concept.name,
            concept_type=unified_model_concept.concept_type.value
        )
        return UnifiedModelsResponseSchema(created_unified_model=created_info, message=f"Modelo unificado '{unified_model_name}' creado.")

class IngestDocumentUseCase:
    """
    Caso de uso para la ingesta de un nuevo documento en el sistema.
    Crea un concepto fuente para el documento y luego extrae UCMs de su contenido.
    """
    def __init__(self,
                 concept_repo: IConceptRepository,
                 extract_ucms_use_case: ExtractUCMsUseCase):
        self.concept_repo = concept_repo
        self.extract_ucms_use_case = extract_ucms_use_case

    async def execute(self, input_data: IngestDocumentInput) -> IngestDocumentResult:
        """
        Ejecuta el proceso de ingesta de documentos.

        1. Crea un ScientificConcept de tipo DOCUMENT_SOURCE.
        2. Guarda este concepto en el repositorio de conceptos.
        3. Invoca a ExtractUCMsUseCase para procesar el texto del documento.
        4. Devuelve el ID del concepto fuente y el resultado de la extracción de UCMs.
        """
        doc_source_id = f"docsrc_{uuid.uuid4().hex}"

        doc_name = input_data.source_doi if input_data.source_doi else \
                   (input_data.source_citation[:70] + "..." if input_data.source_citation and len(input_data.source_citation) > 70 else input_data.source_citation) \
                   or f"Document Source {doc_source_id}"

        document_source_concept = ScientificConcept(
            id=doc_source_id,
            name=doc_name,
            description=f"Document source: {input_data.source_citation or input_data.source_doi or 'N/A'}",
            concept_type=ConceptType.DOCUMENT_SOURCE,
            properties={
                "doi": input_data.source_doi,
                "citation": input_data.source_citation,
                # Expandir metadatos directamente en properties para que sean buscables/visibles
                **(input_data.source_metadata or {})
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
            # embeddings se omite, no es relevante para un DOCUMENT_SOURCE por defecto
        )

        await self.concept_repo.add(document_source_concept)

        ucm_extraction_input = UCMExtractionInput(
            text_content=input_data.document_text,
            source_document_id=doc_source_id,
            source_metadata=input_data.source_metadata
        )

        extraction_result = await self.extract_ucms_use_case.execute(ucm_extraction_input)

        return IngestDocumentResult(
            document_source_id=doc_source_id,
            ucm_extraction_result=extraction_result
        )

from .ports import IRelationshipRepository # IConceptRepository ya debería estar importado
from ..core.domain_models import DirectedRelationship # ScientificConcept ya debería estar importado
from .dtos import LinkConceptsInput, LinkConceptsResult, RelationshipDTO

class LinkConceptsUseCase:
    """
    Caso de uso para crear una relación dirigida entre dos conceptos existentes.
    """
    def __init__(self,
                 concept_repo: IConceptRepository,
                 relationship_repo: IRelationshipRepository):
        self.concept_repo = concept_repo
        self.relationship_repo = relationship_repo

    async def execute(self, input_data: LinkConceptsInput) -> LinkConceptsResult:
        """
        Ejecuta el proceso de vinculación de conceptos.

        1. Obtiene los conceptos de origen y destino del repositorio.
        2. Valida que ambos conceptos existan.
        3. Genera una descripción para la relación si no se proporciona.
        4. Crea una nueva entidad DirectedRelationship.
        5. Guarda la relación en el repositorio de relaciones.
        6. Devuelve la relación creada (como DTO).
        """
        source_concept = await self.concept_repo.get_by_id(input_data.source_concept_id)
        if not source_concept:
            raise ValueError(f"Source concept with ID '{input_data.source_concept_id}' not found.")

        target_concept = await self.concept_repo.get_by_id(input_data.target_concept_id)
        if not target_concept:
            raise ValueError(f"Target concept with ID '{input_data.target_concept_id}' not found.")

        description = input_data.description
        if not description:
            # Asumimos que ScientificConcept tiene un atributo 'name'
            source_name = getattr(source_concept, 'name', input_data.source_concept_id)
            target_name = getattr(target_concept, 'name', input_data.target_concept_id)
            description = f"{source_name} {input_data.relationship_type} {target_name}."

        relationship_id = f"rel_{uuid.uuid4().hex}" # uuid ya importado globalmente
        now_utc = datetime.now(timezone.utc) # datetime, timezone ya importados globalmente

        new_relationship = DirectedRelationship(
            id=relationship_id,
            source_concept_id=input_data.source_concept_id,
            target_concept_id=input_data.target_concept_id,
            type=input_data.relationship_type,
            description=description,
            properties=input_data.properties or {},
            created_at=now_utc,
            updated_at=now_utc
        )

        await self.relationship_repo.add(new_relationship)

        relationship_dto = RelationshipDTO(
            id=new_relationship.id,
            source_concept_id=new_relationship.source_concept_id,
            target_concept_id=new_relationship.target_concept_id,
            type=new_relationship.type,
            description=new_relationship.description,
            properties=new_relationship.properties,
            created_at=new_relationship.created_at
        )

        return LinkConceptsResult(created_relationship=relationship_dto)
