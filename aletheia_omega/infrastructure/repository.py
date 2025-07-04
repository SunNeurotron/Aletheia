# aletheia_omega/infrastructure/repository.py

import logging
from uuid import UUID as PyUUID # Renombrar para evitar conflicto con el tipo de SQLAlchemy
from typing import Optional
from datetime import datetime # Añadido para run_db.completed_at

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..domain.entities import OptimizationResult
from .models import OptimizationRunDB

logger = logging.getLogger(__name__)

class OmegaRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_run(self, run_id: PyUUID, search_space_size: int, lambda_param: float, request_params: Optional[dict] = None) -> OptimizationRunDB:
        """
        Crea un registro inicial para una ejecución de optimización.
        """
        try:
            run_db = OptimizationRunDB(
                id=run_id,
                status="PENDING",
                search_space_size=search_space_size,
                lambda_param=lambda_param,
                request_parameters=request_params
            )
            self.db.add(run_db)
            self.db.commit()
            self.db.refresh(run_db)
            logger.info(f"Registro de optimización {run_id} creado con estado PENDING.")
            return run_db
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error de base de datos al crear el registro de optimización {run_id}: {e}", exc_info=True)
            raise

    def update_run_with_result(self, run_id: PyUUID, result: OptimizationResult, status: str = "COMPLETED") -> Optional[OptimizationRunDB]:
        """
        Actualiza una ejecución de optimización existente con el resultado.
        """
        try:
            run_db = self.db.query(OptimizationRunDB).filter(OptimizationRunDB.id == run_id).first()
            if not run_db:
                logger.warning(f"No se encontró el registro de optimización {run_id} para actualizar.")
                return None

            run_db.status = status
            # lambda_param ya se guardó al crear el run, result.parameters puede tener más cosas.
            # Si se quiere sobreescribir request_parameters con result.parameters:
            # run_db.request_parameters = result.parameters

            run_db.best_model_identifier = result.best_model.identifier
            run_db.best_model_complexity = result.best_model_metrics.complexity
            run_db.best_model_likelihood = result.best_model_metrics.log_likelihood
            run_db.best_model_mdl_cost = result.best_model_metrics.mdl_cost
            run_db.completed_at = datetime.utcnow() # Asegurar que datetime está importado

            self.db.add(run_db) # o self.db.merge(run_db) si es apropiado
            self.db.commit()
            self.db.refresh(run_db)
            logger.info(f"Resultado de la optimización {run_id} guardado/actualizado correctamente con estado {status}.")
            return run_db
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error de base de datos al guardar/actualizar el resultado {run_id}: {e}", exc_info=True)
            raise

    def update_run_status(self, run_id: PyUUID, status: str) -> Optional[OptimizationRunDB]:
        """
        Actualiza solo el estado de una ejecución de optimización.
        """
        try:
            run_db = self.db.query(OptimizationRunDB).filter(OptimizationRunDB.id == run_id).first()
            if not run_db:
                logger.warning(f"No se encontró el registro de optimización {run_id} para actualizar estado.")
                return None

            run_db.status = status
            if status in ["COMPLETED", "FAILED"]: # Asumiendo estados terminales
                 run_db.completed_at = datetime.utcnow()

            self.db.add(run_db)
            self.db.commit()
            self.db.refresh(run_db)
            logger.info(f"Estado de la optimización {run_id} actualizado a {status}.")
            return run_db
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error de base de datos al actualizar estado para {run_id}: {e}", exc_info=True)
            raise

    def get_run_by_id(self, run_id: PyUUID) -> Optional[OptimizationRunDB]:
        """Recupera una ejecución de optimización por su ID."""
        try:
            return self.db.query(OptimizationRunDB).filter(OptimizationRunDB.id == run_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al obtener la ejecución {run_id}: {e}", exc_info=True)
            # Dependiendo de la política, podrías querer relanzar la excepción o devolver None
            raise

    # El método save_run_result original era una combinación de crear y actualizar.
    # Lo he separado en create_run y update_run_with_result para mayor claridad y control,
    # y añadido update_run_status. Si prefieres el comportamiento original, podemos fusionarlos.
    # El método save_run_result que propusiste es más parecido a update_run_with_result,
    # pero con una creación implícita si no existe, lo cual puede ser válido también.
    # Por ahora, he optado por la separación.

    # Si se desea el método save_run_result como lo propusiste:
    # def save_run_result(self, run_id: PyUUID, result: OptimizationResult) -> OptimizationRunDB:
    #     """Guarda o actualiza el resultado de una ejecución de optimización."""
    #     try:
    #         run_db = self.db.query(OptimizationRunDB).filter(OptimizationRunDB.id == run_id).first()
    #         if not run_db:
    #             # Si no existe, creamos una nueva entrada (esto podría manejarse en el caso de uso o API)
    #             # Necesitaríamos lambda_param y request_parameters para crearla aquí.
    #             # El lambda está en result.parameters.get("lambda"), pero los otros optimization_parameters
    #             # del request original no están en OptimizationResult.
    #             # Por eso es mejor separar create y update.
    #             # Si insistes, tendríamos que pasar más parámetros a este método.
    #             raise ValueError(f"Run {run_id} no existe, no se puede actualizar. Crear primero.")

    #         run_db.status = "COMPLETED"
    #         # run_db.lambda_param = result.parameters.get("lambda") # Ya debería estar del create_run
    #         run_db.best_model_identifier = result.best_model.identifier
    #         run_db.best_model_complexity = result.best_model_metrics.complexity
    #         run_db.best_model_likelihood = result.best_model_metrics.log_likelihood
    #         run_db.best_model_mdl_cost = result.best_model_metrics.mdl_cost
    #         run_db.completed_at = datetime.utcnow()
    #         # run_db.search_space_size = result.search_space_size # Ya debería estar del create_run

    #         self.db.add(run_db)
    #         self.db.commit()
    #         self.db.refresh(run_db)
    #         logger.info(f"Resultado de la optimización {run_id} guardado correctamente.")
    #         return run_db
    #     except SQLAlchemyError as e:
    #         self.db.rollback()
    #         logger.error(f"Error de base de datos al guardar el resultado {run_id}: {e}", exc_info=True)
    #         raise
