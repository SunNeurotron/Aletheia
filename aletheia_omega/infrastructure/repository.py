# aletheia_omega/infrastructure/repository.py

import logging
import uuid # Para el tipo PyUUID
from typing import Optional, List, Dict, Any # Añadido List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session, joinedload, selectinload # Para eager loading
from sqlalchemy.exc import SQLAlchemyError

from ..domain.entities import (
    OptimizationResult,
    Trajectory,
    TrajectoryStep,
    ModelRepresentation, # Necesario para construir TrajectoryStep desde OptimizationRunDB
    ModelMetrics         # Necesario para construir TrajectoryStep desde OptimizationRunDB
)
from .models import OptimizationRunDB, TrajectoryDB # Importar TrajectoryDB

logger = logging.getLogger(__name__)

class OmegaRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Métodos para Trayectorias ---

    def create_trajectory(self, name: Optional[str] = None) -> TrajectoryDB:
        """
        Crea una nueva trayectoria en la base de datos.
        Devuelve el objeto TrajectoryDB persistido.
        """
        try:
            trajectory_db = TrajectoryDB(name=name, id=uuid.uuid4()) # Generar UUID aquí
            self.db.add(trajectory_db)
            self.db.commit()
            self.db.refresh(trajectory_db)
            logger.info(f"Trayectoria creada con ID: {trajectory_db.id}, Nombre: '{name}'.")
            return trajectory_db
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error de BD al crear trayectoria '{name}': {e}", exc_info=True)
            raise

    def get_trajectory_db_by_id(self, trajectory_id: uuid.UUID) -> Optional[TrajectoryDB]:
        """Recupera un TrajectoryDB por su ID, opcionalmente cargando sus pasos."""
        try:
            # Usar selectinload para cargar eficientemente los pasos (OptimizationRunDB)
            # si se van a acceder inmediatamente.
            return (
                self.db.query(TrajectoryDB)
                .options(selectinload(TrajectoryDB.steps))
                .filter(TrajectoryDB.id == trajectory_id)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de BD al obtener TrajectoryDB {trajectory_id}: {e}", exc_info=True)
            raise

    def get_trajectory_with_steps(self, trajectory_id: uuid.UUID) -> Optional[Trajectory]:
        """
        Recupera una trayectoria y sus pasos de la BD y los mapea a objetos de dominio.
        """
        try:
            trajectory_db = self.get_trajectory_db_by_id(trajectory_id)
            if not trajectory_db:
                return None

            # Mapear TrajectoryDB y sus OptimizationRunDB a entidades de dominio Trajectory y TrajectoryStep
            domain_steps = []
            for run_db in trajectory_db.steps: # Asumiendo que steps están ordenados por step_index (hecho en el modelo)
                model_repr = ModelRepresentation(
                    identifier=run_db.best_model_identifier,
                    content=b"" # El contenido del modelo no se guarda en OptimizationRunDB directamente
                                # Esto es una limitación si se necesita el contenido real del modelo aquí.
                                # Podríamos necesitar otra tabla para ModelRepresentation.content si es grande,
                                # o guardarlo en OptimizationRunDB.best_model_content (bytes)
                )
                model_metrics = ModelMetrics(
                    complexity=run_db.best_model_complexity,
                    log_likelihood=run_db.best_model_likelihood,
                    mdl_cost=run_db.best_model_mdl_cost
                )
                domain_steps.append(
                    TrajectoryStep(
                        step_index=run_db.step_index,
                        model=model_repr,
                        metrics=model_metrics
                        # Podríamos añadir más campos si se guardan en run_db, como run_db.id
                    )
                )

            return Trajectory(
                id=trajectory_db.id,
                name=trajectory_db.name,
                steps=domain_steps
            )
        except SQLAlchemyError as e: # get_trajectory_db_by_id ya loguea y lanza si hay error de BD
            # Este catch es por si algo más falla durante el mapeo.
            logger.error(f"Error al mapear TrajectoryDB a dominio para {trajectory_id}: {e}", exc_info=True)
            return None # O relanzar

    def add_step_to_trajectory(
        self,
        trajectory_id: uuid.UUID,
        step_domain: TrajectoryStep,
        run_parameters: Dict[str, Any], # Parámetros de la ejecución (ej. lambda, search_space_size)
                                        # que vienen de OptimizationResult.parameters
        mlflow_run_id: Optional[str] = None, # Opcional
        run_id_override: Optional[uuid.UUID] = None # Para permitir que la API genere el ID del run
    ) -> Trajectory:
        """
        Añade un nuevo paso (OptimizationRunDB) a una trayectoria existente.
        El `step_domain` contiene el modelo y métricas del dominio.
        `run_parameters` contiene lambda, search_space_size, etc.
        Devuelve el objeto de dominio Trajectory actualizado.
        """
        try:
            trajectory_db = self.db.query(TrajectoryDB).filter(TrajectoryDB.id == trajectory_id).first()
            if not trajectory_db:
                raise ValueError(f"No se encontró la trayectoria con ID {trajectory_id} para añadir el paso.")

            # Crear la nueva instancia de OptimizationRunDB
            new_run_db = OptimizationRunDB(
                id=run_id_override or uuid.uuid4(), # Usar override o generar nuevo UUID
                trajectory_id=trajectory_id,
                step_index=step_domain.step_index,
                status="COMPLETED", # Asumimos que el paso se añade cuando el modelo ya fue encontrado

                lambda_param=run_parameters.get("lambda"), # Extraer de run_parameters
                search_space_size=run_parameters.get("search_space_size"), # Extraer de run_parameters
                request_parameters=run_parameters, # Guardar todos los params del resultado de la optimización

                best_model_identifier=step_domain.model.identifier,
                best_model_complexity=step_domain.metrics.complexity,
                best_model_likelihood=step_domain.metrics.log_likelihood,
                best_model_mdl_cost=step_domain.metrics.mdl_cost,

                mlflow_run_id=mlflow_run_id,
                completed_at=datetime.utcnow() # El paso se completa ahora
            )

            # trajectory_db.steps.append(new_run_db) # SQLAlchemy maneja esto si la relación está bien configurada
            self.db.add(new_run_db)
            self.db.commit()
            # No es necesario self.db.refresh(trajectory_db) aquí si solo queremos la trayectoria actualizada.
            # Es mejor recargarla para asegurar que tenemos todos los datos y el nuevo paso.
            logger.info(f"Nuevo paso (índice {step_domain.step_index}, run ID {new_run_db.id}) añadido a trayectoria {trajectory_id}.")

            # Devolver la trayectoria de dominio actualizada
            return self.get_trajectory_with_steps(trajectory_id)

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error de BD al añadir paso a trayectoria {trajectory_id}: {e}", exc_info=True)
            raise
        except Exception as e: # Capturar otros errores como ValueError de arriba
            logger.error(f"Error al añadir paso a trayectoria {trajectory_id}: {e}", exc_info=True)
            raise


    # --- Métodos para OptimizationRunDB (existentes, necesitan revisión) ---
    # El método create_run original ahora es problemático porque OptimizationRunDB requiere trajectory_id y step_index.
    # Los runs individuales (no parte de una trayectoria) ya no tienen sentido en este nuevo modelo.
    # Si se necesitan runs "huérfanos", el modelo de BD necesitaría que trajectory_id sea nullable.
    # Por ahora, asumimos que todos los runs son pasos de una trayectoria.

    def get_run_by_id(self, run_id: uuid.UUID) -> Optional[OptimizationRunDB]:
        """Recupera una ejecución de optimización (un paso de trayectoria) por su ID."""
        try:
            return self.db.query(OptimizationRunDB).filter(OptimizationRunDB.id == run_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error de BD al obtener OptimizationRunDB {run_id}: {e}", exc_info=True)
            raise

    # update_run_with_result y update_run_status podrían seguir siendo útiles si se quiere
    # actualizar un paso específico de una trayectoria después de que fue creado.
    # Pero la lógica de "completar" un run ahora está más ligada a add_step_to_trajectory.

    def update_run_details( # Renombrado de update_run_with_result para reflejar un uso más genérico
        self,
        run_id: uuid.UUID,
        status: Optional[str] = None,
        # Permitir actualizar otros campos si es necesario, pero con cuidado.
        # Por ejemplo, si un análisis posterior añade más info al 'request_parameters' o 'mlflow_run_id'
        new_request_parameters: Optional[Dict[str, Any]] = None,
        new_mlflow_run_id: Optional[str] = None
    ) -> Optional[OptimizationRunDB]:
        try:
            run_db = self.db.query(OptimizationRunDB).filter(OptimizationRunDB.id == run_id).first()
            if not run_db:
                logger.warning(f"No se encontró OptimizationRunDB {run_id} para actualizar detalles.")
                return None

            updated = False
            if status:
                run_db.status = status
                if status in ["COMPLETED", "FAILED", "CALC_DONE_SAVE_FAILED", "FAILED_VALIDATION", "FAILED_UNEXPECTED", "FAILED_NOT_IMPLEMENTED"]:
                    run_db.completed_at = datetime.utcnow()
                updated = True
            if new_request_parameters is not None: # Usar 'is not None' para permitir dict vacío
                run_db.request_parameters = new_request_parameters
                updated = True
            if new_mlflow_run_id:
                run_db.mlflow_run_id = new_mlflow_run_id
                updated = True

            if updated:
                self.db.add(run_db)
                self.db.commit()
                self.db.refresh(run_db)
                logger.info(f"OptimizationRunDB {run_id} actualizado. Nuevo estado: {status if status else run_db.status}.")
            return run_db
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error de BD al actualizar OptimizationRunDB {run_id}: {e}", exc_info=True)
            raise

    # El antiguo create_run y update_run_with_result se eliminan o se adaptan drásticamente.
    # El flujo ahora es:
    # 1. create_trajectory()
    # 2. EvolveTrajectoryUseCase llama a FindOptimalModelUseCase
    # 3. EvolveTrajectoryUseCase llama a repository.add_step_to_trajectory() con los resultados.
    #    Este add_step_to_trajectory crea el OptimizationRunDB.
    # Si la API crea un run_id primero y luego el caso de uso lo completa, entonces
    # add_step_to_trajectory podría tomar un run_id opcional.
    # Y la API podría usar update_run_details para cambiar el estado si algo falla.
    # La lógica de la API que usaba create_run y luego update_run_with_result necesitará cambiar.
    # La API ahora llamará a create_trajectory, luego EvolveTrajectoryUseCase que usa add_step_to_trajectory.
    # Los métodos create_run, update_run_with_result, update_run_status originales se han modificado/integrado.
    # El `update_run_status` original es ahora parte de `update_run_details`.
