from typing import List, Optional, Tuple, Any, Dict
from uuid import UUID
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Importar entidades de dominio y modelos de infraestructura
from ..domain.entities import Experiment as DomainExperiment, TTestResult as DomainTTestResult
from .models import ExperimentModel, TTestResultModel # Modelos SQLAlchemy

logger = logging.getLogger(__name__)

class SQLAlchemyStatsRepository: # Podría heredar de un StatsRepositoryPort si se define una interfaz abstracta
    def __init__(self, db: Session):
        """
        Initializes the repository with a SQLAlchemy session.

        Args:
            db: The SQLAlchemy Session object to use for database operations.
        """
        self.db = db

    def _to_domain_ttest_result(self, result_model: TTestResultModel) -> Optional[DomainTTestResult]:
        if not result_model:
            return None
        return DomainTTestResult(
            statistic=result_model.statistic,
            p_value=result_model.p_value,
            degrees_freedom=result_model.degrees_freedom,
            mean_group_a=result_model.mean_group_a,
            variance_group_a=result_model.variance_group_a,
            mean_group_b=result_model.mean_group_b,
            variance_group_b=result_model.variance_group_b,
            confidence_interval_95=[result_model.confidence_interval_95_lower, result_model.confidence_interval_95_upper],
            is_significant_05=result_model.is_significant_05,
            normality_p_value_group_a=result_model.normality_p_value_group_a,
            normality_p_value_group_b=result_model.normality_p_value_group_b,
            comment=result_model.comment
        )

    def _to_domain_experiment(self, exp_model: ExperimentModel) -> DomainExperiment:
        domain_result = self._to_domain_ttest_result(exp_model.result_model)

        # Asegurar que tracking_warnings sea una lista si es None en la BD
        tracking_warnings_list = exp_model.tracking_warnings if exp_model.tracking_warnings is not None else []

        return DomainExperiment(
            id=exp_model.id,
            name=exp_model.name,
            description=exp_model.description,
            group_a_data=exp_model.group_a_data, # Asumiendo que JSONB se deserializa a lista
            group_b_data=exp_model.group_b_data, # Asumiendo que JSONB se deserializa a lista
            parameters=exp_model.parameters,     # Asumiendo que JSONB se deserializa a dict
            result=domain_result,
            mlflow_run_id=exp_model.mlflow_run_id,
            created_at=exp_model.created_at,
            updated_at=exp_model.updated_at,
            tracking_warnings=tracking_warnings_list # Nuevo campo
        )

    def save(self, experiment_domain: DomainExperiment) -> DomainExperiment:
        logger.debug(f"Attempting to save experiment ID: {experiment_domain.id}")
        try:
            # Convertir entidad de dominio a modelo SQLAlchemy
            exp_model = self.db.query(ExperimentModel).filter(ExperimentModel.id == experiment_domain.id).first()
            if not exp_model:
                exp_model = ExperimentModel(id=experiment_domain.id)

            exp_model.name = experiment_domain.name
            exp_model.description = experiment_domain.description
            exp_model.group_a_data = experiment_domain.group_a_data
            exp_model.group_b_data = experiment_domain.group_b_data
            exp_model.parameters = experiment_domain.parameters
            exp_model.mlflow_run_id = experiment_domain.mlflow_run_id
            exp_model.tracking_warnings = experiment_domain.tracking_warnings # Guardar warnings

            if experiment_domain.result:
                # Si hay un resultado, crear/actualizar TTestResultModel
                result_model = exp_model.result_model
                if not result_model:
                    result_model = TTestResultModel(experiment_id=exp_model.id)

                result_model.statistic = experiment_domain.result.statistic
                result_model.p_value = experiment_domain.result.p_value
                result_model.degrees_freedom = experiment_domain.result.degrees_freedom
                result_model.mean_group_a = experiment_domain.result.mean_group_a
                result_model.variance_group_a = experiment_domain.result.variance_group_a
                result_model.mean_group_b = experiment_domain.result.mean_group_b
                result_model.variance_group_b = experiment_domain.result.variance_group_b
                result_model.confidence_interval_95_lower = experiment_domain.result.confidence_interval_95[0]
                result_model.confidence_interval_95_upper = experiment_domain.result.confidence_interval_95[1]
                result_model.is_significant_05 = experiment_domain.result.is_significant_05
                result_model.normality_p_value_group_a = experiment_domain.result.normality_p_value_group_a
                result_model.normality_p_value_group_b = experiment_domain.result.normality_p_value_group_b
                result_model.comment = experiment_domain.result.comment
                exp_model.result_model = result_model # Asociar

            self.db.add(exp_model)
            self.db.commit()
            self.db.refresh(exp_model)
            if exp_model.result_model: # Refrescar también el resultado si existe
                 self.db.refresh(exp_model.result_model)
            logger.info(f"Successfully saved experiment ID: {exp_model.id}")
            return self._to_domain_experiment(exp_model)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error while saving experiment ID {experiment_domain.id}: {e}", exc_info=True)
            raise # Re-lanzar para que la capa de aplicación lo maneje

    def get(self, experiment_id: UUID) -> Optional[DomainExperiment]:
        logger.debug(f"Attempting to retrieve experiment ID: {experiment_id}")
        try:
            # Usar joinedload para cargar el resultado ansiosamente si siempre se necesita
            exp_model = self.db.query(ExperimentModel).filter(ExperimentModel.id == experiment_id).first()
            # exp_model = self.db.query(ExperimentModel).options(joinedload(ExperimentModel.result_model)).filter(ExperimentModel.id == experiment_id).first()

            if exp_model:
                logger.debug(f"Found experiment ID: {experiment_id}")
                return self._to_domain_experiment(exp_model)
            logger.debug(f"Experiment ID: {experiment_id} not found.")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving experiment ID {experiment_id}: {e}", exc_info=True)
            raise

    def list_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[DomainExperiment], int]:
        logger.debug(f"Listing experiments with skip={skip}, limit={limit}")
        try:
            total_count = self.db.query(func.count(ExperimentModel.id)).scalar()

            query = self.db.query(ExperimentModel).order_by(ExperimentModel.created_at.desc())

            exp_models = query.offset(skip).limit(limit).all()

            domain_experiments = [self._to_domain_experiment(em) for em in exp_models]
            logger.info(f"Retrieved {len(domain_experiments)} experiments. Total count: {total_count}")
            return domain_experiments, total_count
        except SQLAlchemyError as e:
            logger.error(f"Database error while listing experiments: {e}", exc_info=True)
            raise

# Alias para consistencia si en otras partes se usa StatsRepository
StatsRepository = SQLAlchemyStatsRepository
```
