# aletheia_omega/application/use_cases.py

from typing import Any, List, Dict
import math

from aletheia_omega.domain.entities import ModelRepresentation, ModelMetrics, OptimizationResult
from aletheia_omega.domain.services import (
    KolmogorovComplexityProxyService,
    LikelihoodService,
    OmegaCostService
)


class FindOptimalModelUseCase:
    """
    Caso de uso para encontrar el modelo óptimo (M*) de un conjunto de modelos candidatos,
    minimizando el coste MDL (Axioma 1).
    """

    def __init__(
        self,
        complexity_service: KolmogorovComplexityProxyService,
        likelihood_service: LikelihoodService,
        omega_cost_service: OmegaCostService,
    ):
        self._complexity_service = complexity_service
        self._likelihood_service = likelihood_service
        self._omega_cost_service = omega_cost_service

    def execute(
        self,
        candidate_models: List[ModelRepresentation],
        data: Any,
        lambda_param: float,
        optimization_parameters: Dict[str, Any] = None
    ) -> OptimizationResult:
        """
        Ejecuta el caso de uso.

        @param candidate_models: Lista de modelos candidatos a evaluar.
        @param data: Los datos (D) sobre los cuales evaluar los modelos.
        @param lambda_param: Parámetro de regularización λ para la función de coste MDL.
        @param optimization_parameters: Parámetros adicionales de la optimización.
        @return: Un objeto OptimizationResult con el mejor modelo y sus métricas.
        @raises ValueError: Si no se proporcionan modelos candidatos o lambda_param es negativo.
        """
        if not candidate_models:
            raise ValueError("La lista de modelos candidatos no puede estar vacía.")
        if lambda_param < 0:
            # Aunque OmegaCostService también valida, es buena práctica validar
            # los inputs a nivel de caso de uso también.
            raise ValueError("El parámetro de regularización λ no puede ser negativo.")

        best_model: ModelRepresentation = None
        best_metrics: ModelMetrics = None
        min_mdl_cost = float('inf')

        for model_repr in candidate_models:
            # 1. Calcular K(M) - Proxy de la Complejidad de Kolmogorov
            complexity = self._complexity_service.compute(model_repr.content)

            # 2. Calcular L(D|M) - Log-Verosimilitud
            log_likelihood = self._likelihood_service.compute(model_repr.content, data)

            # 3. Calcular Coste MDL: Cost(M) = λ * K(M) - L(D|M)
            mdl_cost = self._omega_cost_service.calculate_mdl_cost(
                complexity=complexity,
                log_likelihood=log_likelihood,
                lambda_param=lambda_param,
            )

            if mdl_cost < min_mdl_cost:
                min_mdl_cost = mdl_cost
                best_model = model_repr
                best_metrics = ModelMetrics(
                    complexity=complexity,
                    log_likelihood=log_likelihood,
                    mdl_cost=mdl_cost,
                )

        if best_model is None:
            # Esto podría suceder si, por alguna razón, todos los modelos resultan en costos inválidos
            # o si la lista de modelos estaba vacía y la guarda inicial falló (poco probable aquí).
            # O si todos los modelos fallan en el cálculo de likelihood y devuelven -1e9,
            # y el cálculo de complejidad es muy alto, resultando en mdl_cost = inf.
            # Para ser robustos, manejamos este caso.
            raise RuntimeError("No se pudo determinar un modelo óptimo. Verifique los modelos y datos de entrada.")


        return OptimizationResult(
            best_model=best_model,
            best_model_metrics=best_metrics,
            search_space_size=len(candidate_models),
            parameters=optimization_parameters or {},
        )
