# Aletheia_v3/application/mdl_synthesis_use_cases.py
import logging
from typing import Any, List, Dict, Optional

# Import MDL entities and services from Aletheia_v3.core.mdl_synthesis
from ..core.mdl_synthesis.entities import (
    ModelRepresentation,
    ModelMetrics,
    OptimizationResult
)
from ..core.mdl_synthesis.services import (
    KolmogorovComplexityProxyService,
    LikelihoodService, # This will be the new placeholder/Aletheia_v3 specific one
    OmegaCostService
)

logger = logging.getLogger(__name__)

class FindOptimalModelUseCase:
    """
    Caso de uso para encontrar el modelo óptimo (M*) de un conjunto de modelos candidatos,
    minimizando el coste MDL (Axioma 1).
    Adaptado de aletheia_omega.
    """

    def __init__(
        self,
        complexity_service: KolmogorovComplexityProxyService,
        likelihood_service: LikelihoodService, # Expects Aletheia_v3's LikelihoodService
        omega_cost_service: OmegaCostService,
    ):
        self.complexity_service = complexity_service
        self.likelihood_service = likelihood_service
        self.omega_cost_service = omega_cost_service
        # logger.info("FindOptimalModelUseCase (Aletheia_v3) inicializado.")


    def execute(
        self,
        candidate_models: List[ModelRepresentation],
        data: Any, # Data 'D' against which models 'M' are evaluated
        lambda_param: float,
        optimization_parameters: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        Ejecuta el caso de uso para encontrar el modelo óptimo.

        @param candidate_models: Lista de ModelRepresentation de modelos candidatos.
        @param data: Los datos (D) sobre los cuales evaluar los modelos.
                     La estructura de 'data' dependerá del contexto del Eje Y
                     (e.g., lista de UCMs para clustering, lista de Proposiciones para teoría).
        @param lambda_param: Parámetro de regularización λ para la función de coste MDL.
        @param optimization_parameters: Parámetros adicionales de la optimización (opcional).
        @return: Un objeto OptimizationResult con el mejor modelo y sus métricas.
        @raises ValueError: Si no se proporcionan modelos candidatos o lambda_param es negativo.
        """
        if not candidate_models:
            logger.error("FindOptimalModelUseCase: Se intentó ejecutar con una lista de modelos vacía.")
            raise ValueError("La lista de modelos candidatos no puede estar vacía.")
        if lambda_param < 0:
            logger.error(f"FindOptimalModelUseCase: Se intentó ejecutar con lambda negativo: {lambda_param}")
            raise ValueError("El parámetro de regularización λ no puede ser negativo.")

        logger.info(
            f"FindOptimalModelUseCase: Iniciando búsqueda del modelo óptimo en un espacio de "
            f"{len(candidate_models)} modelos con lambda={lambda_param}."
        )

        best_model: Optional[ModelRepresentation] = None
        best_metrics: Optional[ModelMetrics] = None
        min_mdl_cost = float('inf')

        for model_repr in candidate_models:
            complexity = self.complexity_service.compute(model_repr.content)

            # Crucially, this now calls Aletheia_v3's (placeholder) LikelihoodService
            log_likelihood = self.likelihood_service.compute(model_repr, data) # Pass model_repr as per directive

            mdl_cost = self.omega_cost_service.calculate_mdl_cost(
                complexity=complexity,
                log_likelihood=log_likelihood,
                lambda_param=lambda_param,
            )
            logger.debug(
                f"Modelo '{model_repr.identifier}': K={complexity:.2f}, L={log_likelihood:.4f}, MDL={mdl_cost:.4f}"
            )
            if mdl_cost < min_mdl_cost:
                min_mdl_cost = mdl_cost
                best_model = model_repr
                best_metrics = ModelMetrics(
                    complexity=complexity,
                    log_likelihood=log_likelihood,
                    mdl_cost=mdl_cost,
                )

        if best_model is None or best_metrics is None:
            logger.error(
                "FindOptimalModelUseCase: La búsqueda finalizó sin encontrar un modelo óptimo. "
                "Esto puede ocurrir si todos los modelos evaluados resultaron en costos inválidos "
                "o si el espacio de candidatos estaba vacío (aunque ya se verificó)."
            )
            # Consider the case where all log_likelihoods are extremely low (e.g. -1e9 from placeholder)
            # This could lead to all mdl_costs being very high.
            # If candidate_models was not empty, this implies an issue with metric calculation.
            # For now, raising RuntimeError is fine.
            raise RuntimeError("No se pudo determinar un modelo óptimo. Verifique los modelos y datos de entrada, o la implementación de LikelihoodService.")

        logger.info(
            f"FindOptimalModelUseCase: Búsqueda finalizada. Mejor modelo: '{best_model.identifier}' (Coste MDL: {min_mdl_cost:.4f})."
        )

        final_params = optimization_parameters or {}
        final_params["lambda"] = lambda_param # Ensure lambda is recorded

        return OptimizationResult(
            best_model=best_model,
            best_model_metrics=best_metrics,
            search_space_size=len(candidate_models),
            parameters=final_params
        )
