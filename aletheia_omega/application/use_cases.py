# Copyright 2025 Alant
#
# Licensed under the Aletheia Unificada Ethical Public License (AUEPL);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# aletheia_omega/application/use_cases.py

import logging
import uuid # Necesario para trajectory_id
from typing import Any, List, Dict, Optional # Optional añadido

from aletheia_omega.domain.entities import (
    ModelRepresentation,
    ModelMetrics,
    OptimizationResult,
    Trajectory,         # Nuevas entidades
    TrajectoryStep,
    TrajectoryAnalysis
)
from aletheia_omega.domain.services import (
    KolmogorovComplexityProxyService,
    LikelihoodService,
    OmegaCostService,
    TrajectoryAnalysisService # Nuevo servicio
)
# Importamos el repositorio concreto por simplicidad de DI para los nuevos casos de uso.
# En una arquitectura más grande, podríamos usar interfaces abstractas aquí también.
from aletheia_omega.infrastructure.repository import OmegaRepository


logger = logging.getLogger(__name__)


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
        self.complexity_service = complexity_service
        self.likelihood_service = likelihood_service
        self.omega_cost_service = omega_cost_service
        # No loguear aquí en __init__ si el logger no está configurado aún,
        # o asegurarse de que el logging esté configurado globalmente antes.
        # logger.info("FindOptimalModelUseCase inicializado con sus servicios de dominio.")
        # Es mejor que el logging de inicialización lo haga quien crea la instancia.

    def execute(
        self,
        candidate_models: List[ModelRepresentation],
        data: Any,
        lambda_param: float,
        optimization_parameters: Optional[Dict[str, Any]] = None # Optional y default
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
            logger.error("Se intentó ejecutar FindOptimalModelUseCase con una lista de modelos vacía.")
            raise ValueError("La lista de modelos candidatos no puede estar vacía.")
        if lambda_param < 0:
            logger.error(f"Se intentó ejecutar FindOptimalModelUseCase con lambda negativo: {lambda_param}")
            raise ValueError("El parámetro de regularización λ no puede ser negativo.")

        logger.info(
            f"FindOptimalModelUseCase: Iniciando búsqueda del modelo óptimo en un espacio de "
            f"{len(candidate_models)} modelos con lambda={lambda_param}."
        )

        best_model: Optional[ModelRepresentation] = None # Optional
        best_metrics: Optional[ModelMetrics] = None      # Optional
        min_mdl_cost = float('inf')

        for model_repr in candidate_models:
            complexity = self.complexity_service.compute(model_repr.content)
            log_likelihood = self.likelihood_service.compute(model_repr.content, data)
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

        if best_model is None or best_metrics is None: # Chequeo más explícito
            logger.error(
                "FindOptimalModelUseCase: La búsqueda finalizó sin encontrar un modelo óptimo. "
                "Esto puede ocurrir si todos los modelos evaluados resultaron en costos inválidos."
            )
            raise RuntimeError("No se pudo determinar un modelo óptimo. Verifique los modelos y datos de entrada.")

        logger.info(
            f"FindOptimalModelUseCase: Búsqueda finalizada. Mejor modelo: '{best_model.identifier}' (Coste MDL: {min_mdl_cost:.4f})."
        )

        # Incluir lambda_param en los parámetros del resultado para trazabilidad
        final_params = optimization_parameters or {}
        final_params["lambda"] = lambda_param # Asegurar que lambda esté aquí

        return OptimizationResult(
            best_model=best_model,
            best_model_metrics=best_metrics,
            search_space_size=len(candidate_models),
            parameters=final_params
        )


# --- Casos de Uso para la Fase 2: Trayectorias ---

class EvolveTrajectoryUseCase:
    """
    Orquesta la evolución de una trayectoria de un estado i a i+1.
    Añade un nuevo modelo óptimo (M*ᵢ₊₁) a la trayectoria basado en nuevos datos.
    """
    def __init__(
        self,
        find_optimal_model_uc: FindOptimalModelUseCase,
        repository: OmegaRepository # Usamos la implementación concreta del repo
    ):
        self.find_optimal_model_uc = find_optimal_model_uc
        self.repository = repository
        logger.info("EvolveTrajectoryUseCase inicializado.")

    def execute(
        self,
        trajectory_id: uuid.UUID,
        new_data: Any, # Los datos para el nuevo paso
        model_search_space: List[ModelRepresentation], # El espacio de búsqueda para el nuevo modelo
        lambda_param: float, # Lambda para este paso de optimización
        optimization_parameters: Optional[Dict[str, Any]] = None # Params para FindOptimalModelUseCase
    ) -> Trajectory: # Devuelve la trayectoria actualizada del dominio
        """
        Toma una trayectoria existente, nuevos datos, un espacio de búsqueda de modelos candidatos,
        y el parámetro lambda, para calcular el siguiente modelo óptimo y añadirlo a la trayectoria.

        @param trajectory_id: ID de la trayectoria a evolucionar.
        @param new_data: Nuevos datos para encontrar el siguiente modelo óptimo.
        @param model_search_space: Lista de modelos candidatos para el nuevo paso.
        @param lambda_param: Parámetro lambda para la optimización de este paso.
        @param optimization_parameters: Parámetros adicionales para FindOptimalModelUseCase.
        @return: El objeto de dominio Trajectory actualizado.
        @raises ValueError: Si la trayectoria no existe o si los parámetros de optimización son inválidos.
        """
        logger.info(f"EvolveTrajectoryUseCase: Iniciando evolución para trayectoria ID: {trajectory_id}.")

        # 1. Recuperar la trayectoria actual del repositorio.
        #    get_trajectory_with_steps debe devolver un objeto de dominio Trajectory.
        trajectory_domain_obj = self.repository.get_trajectory_with_steps(trajectory_id)
        if not trajectory_domain_obj:
            logger.error(f"EvolveTrajectoryUseCase: Trayectoria con ID {trajectory_id} no encontrada.")
            raise ValueError(f"La trayectoria con ID {trajectory_id} no existe.")

        # 2. Encontrar el siguiente modelo óptimo usando el FindOptimalModelUseCase.
        #    Este caso de uso ya maneja su propio logging y errores de parámetros.
        logger.debug(f"EvolveTrajectoryUseCase: Buscando nuevo modelo óptimo para trayectoria {trajectory_id}.")
        current_step_count = len(trajectory_domain_obj.steps)

        # Pasar optimization_parameters al sub-caso de uso.
        # Asegurar que lambda_param se pasa correctamente y se registra en OptimizationResult.
        opt_params_for_find = optimization_parameters or {}
        # No es necesario añadir lambda aquí si FindOptimalModelUseCase.execute lo añade a sus propios resultados.

        optimization_result = self.find_optimal_model_uc.execute(
            candidate_models=model_search_space,
            data=new_data,
            lambda_param=lambda_param,
            optimization_parameters=opt_params_for_find
        )

        # 3. Crear el nuevo objeto TrajectoryStep del dominio.
        #    El step_index es el siguiente número de secuencia.
        new_step_domain = TrajectoryStep(
            step_index=current_step_count, # Los índices son base 0
            model=optimization_result.best_model,
            metrics=optimization_result.best_model_metrics
            # Aquí podríamos también querer guardar los `optimization_result.parameters`
            # si son relevantes para el paso (ej. el lambda usado, etc.).
            # El modelo `OptimizationRunDB` los guardará.
        )

        # 4. Añadir el nuevo paso a la trayectoria a través del repositorio.
        #    add_step_to_trajectory se encargará de persistir el nuevo OptimizationRunDB
        #    y actualizar la relación, devolviendo la trayectoria de dominio actualizada.
        logger.debug(f"EvolveTrajectoryUseCase: Añadiendo nuevo paso a trayectoria {trajectory_id}.")
        updated_trajectory_domain_obj = self.repository.add_step_to_trajectory(
            trajectory_id, new_step_domain, optimization_result.parameters
        )

        logger.info(
            f"EvolveTrajectoryUseCase: Trayectoria {trajectory_id} evolucionada al paso {new_step_domain.step_index} "
            f"con el modelo '{new_step_domain.model.identifier}'.")

        return updated_trajectory_domain_obj


class ClassifyTrajectoryUseCase:
    """
    Clasifica la dinámica de una trayectoria existente utilizando TrajectoryAnalysisService.
    """
    def __init__(
        self,
        analysis_service: TrajectoryAnalysisService, # Servicio de dominio para el análisis
        repository: OmegaRepository                 # Repositorio para obtener la trayectoria
    ):
        self.analysis_service = analysis_service
        self.repository = repository
        logger.info("ClassifyTrajectoryUseCase inicializado.")

    def execute(self, trajectory_id: uuid.UUID) -> TrajectoryAnalysis:
        """
        Recupera una trayectoria y la analiza para clasificar su dinámica.

        @param trajectory_id: ID de la trayectoria a clasificar.
        @return: Un objeto TrajectoryAnalysis con la clasificación.
        @raises ValueError: Si la trayectoria no existe.
        """
        logger.info(f"ClassifyTrajectoryUseCase: Iniciando clasificación para trayectoria ID: {trajectory_id}.")

        # 1. Recuperar la trayectoria completa (con todos sus pasos) del repositorio.
        trajectory_domain_obj = self.repository.get_trajectory_with_steps(trajectory_id)
        if not trajectory_domain_obj:
            logger.error(f"ClassifyTrajectoryUseCase: Trayectoria con ID {trajectory_id} no encontrada.")
            raise ValueError(f"La trayectoria con ID {trajectory_id} no existe.")

        if not trajectory_domain_obj.steps:
            logger.warning(f"ClassifyTrajectoryUseCase: Trayectoria {trajectory_id} no tiene pasos para analizar.")
            # El TrajectoryAnalysisService maneja esto y devuelve UNDEFINED.
            # No necesitamos un error aquí, el servicio lo gestionará.

        # 2. Usar el servicio de dominio para analizar la trayectoria.
        logger.debug(f"ClassifyTrajectoryUseCase: Analizando trayectoria {trajectory_id} con {len(trajectory_domain_obj.steps)} pasos.")
        analysis_result = self.analysis_service.analyze(trajectory_domain_obj)

        logger.info(
            f"ClassifyTrajectoryUseCase: Clasificación para trayectoria {trajectory_id} completada. "
            f"Estado: {analysis_result.state.value}, Comentario: '{analysis_result.comment}'."
        )

        return analysis_result
