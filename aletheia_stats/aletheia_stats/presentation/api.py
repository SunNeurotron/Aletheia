import logging
import os
import uuid
from datetime import timedelta  # Not used, can be removed
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,  # No se usa OAuth2PasswordRequestForm si no hay /token local
)
from sqlalchemy.orm import Session

# Imports locales
from ..application.use_cases import PerformTTestUseCase
from ..domain.entities import Experiment as ExperimentDomain
from ..domain.services import StatsService  # Required for get_stats_service type hint
from ..infrastructure.database import get_db_session_stats

# Need MLflowExperimentTracker for type hint if get_mlflow_tracker returns it
from ..infrastructure.mlflow_tracker import MLflowExperimentTracker
from ..infrastructure.sqlalchemy_repository import (  # For get_stats_repository type hint
    SQLAlchemyStatsRepository,
)
from .schemas import (
    ExperimentResponse,
    HealthCheckResponse,
    PaginatedExperimentResponse,
    TTestRequest,
    TTestResultSchema,
)
from aletheia_common.auth.jwt_handler import (
    UserAuth,
    get_current_active_user,
    require_roles,
)
from aletheia_common.auth.schemas import UserSchema

# Logger
logger = logging.getLogger(__name__)

MLFLOW_TRACKING_URI_ENV = "STATS_MLFLOW_TRACKING_URI"
DEFAULT_MLFLOW_TRACKING_URI = "http://localhost:5001"
MLFLOW_TRACKING_URI = os.getenv(
    MLFLOW_TRACKING_URI_ENV, DEFAULT_MLFLOW_TRACKING_URI
)

router = APIRouter(tags=["Aletheia-Stats"])


def get_stats_service() -> StatsService:
    return StatsService()


def get_mlflow_tracker() -> Optional[MLflowExperimentTracker]:
    if not MLFLOW_TRACKING_URI or MLFLOW_TRACKING_URI.lower() == "none":
        logger.warning(
            "MLflow no configurado o URI es 'none'. MLflowTracker no se inicializará."
        )
        return None
    try:
        # from ..infrastructure.mlflow_tracker import MLflowExperimentTracker # Already imported at top
        logger.info(
            f"Intentando inicializar MLflowTracker con URI: {MLFLOW_TRACKING_URI}"
        )
        return MLflowExperimentTracker(tracking_uri=MLFLOW_TRACKING_URI)
    except ImportError:
        logger.error(
            "Error al importar MLflowExperimentTracker desde ..infrastructure.mlflow_tracker"
        )
        return None
    except Exception as e:
        logger.error(
            f"Error inicializando MLflowTracker con URI '{MLFLOW_TRACKING_URI}': {e}",
            exc_info=True,
        )
        return None


def get_stats_repository(
    db: Session = Depends(get_db_session_stats),
) -> SQLAlchemyStatsRepository:
    # from ..infrastructure.sqlalchemy_repository import SQLAlchemyStatsRepository # Already imported at top
    return SQLAlchemyStatsRepository(db=db)


def get_perform_ttest_use_case(
    stats_service: StatsService = Depends(get_stats_service),
    stats_repository: SQLAlchemyStatsRepository = Depends(
        get_stats_repository
    ),
    mlflow_tracker: Optional[MLflowExperimentTracker] = Depends(
        get_mlflow_tracker
    ),
) -> PerformTTestUseCase:
    return PerformTTestUseCase(
        stats_service=stats_service,
        stats_repository=stats_repository,
        mlflow_tracker=mlflow_tracker,
    )


@router.get("/users/me", response_model=UserSchema, tags=["Users"])
async def read_users_me_stats(current_user: UserAuth = Depends(get_current_active_user)):
    return UserSchema(username=current_user.username, roles=current_user.roles)


@router.post(
    "/analyze/ttest",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Analysis"],
)
async def perform_ttest_analysis_endpoint(
    request_data: TTestRequest,
    use_case: PerformTTestUseCase = Depends(get_perform_ttest_use_case),
    current_user: UserAuth = Depends(require_roles({"analyst"})),
):
    try:
        experiment_uuid = uuid.uuid4()
        logger.info(
            f"Endpoint /analyze/ttest llamado por usuario '{current_user.username if current_user else 'anonymous'}' para nuevo experiment_id: {experiment_uuid}"
        )

        domain_experiment: ExperimentDomain = use_case.execute(
            experiment_id=experiment_uuid,
            group_a_data=request_data.group_a_data,
            group_b_data=request_data.group_b_data,
            experiment_name=request_data.experiment_name,
            experiment_description=request_data.experiment_description,
            parameters=request_data.parameters,
            alpha=request_data.alpha,
        )

        logger.info(
            f"Análisis para experiment_id {domain_experiment.id} completado. MLflow run ID: {domain_experiment.mlflow_run_id}"
        )
        if domain_experiment.tracking_warnings:
            logger.warning(
                f"Experiment {domain_experiment.id} tiene las siguientes advertencias de seguimiento: {domain_experiment.tracking_warnings}"
            )

        response = ExperimentResponse(
            id=domain_experiment.id,
            name=domain_experiment.name,
            description=domain_experiment.description,
            group_a_data_summary={
                "count": len(domain_experiment.group_a_data),
                "mean": (
                    domain_experiment.result.mean_group_a
                    if domain_experiment.result
                    else None
                ),
            },
            group_b_data_summary={
                "count": len(domain_experiment.group_b_data),
                "mean": (
                    domain_experiment.result.mean_group_b
                    if domain_experiment.result
                    else None
                ),
            },
            parameters=domain_experiment.parameters,
            result=(
                TTestResultSchema.from_orm(domain_experiment.result)
                if domain_experiment.result
                else None
            ),
            mlflow_run_id=domain_experiment.mlflow_run_id,
            tracking_warnings=domain_experiment.tracking_warnings,
            created_at=domain_experiment.created_at,
            updated_at=domain_experiment.updated_at,
        )
        return response

    except ValueError as ve:
        logger.warning(
            f"ValueError en endpoint /analyze/ttest: {ve}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)
        )
    except Exception as e:
        logger.exception(
            f"Error inesperado en endpoint /analyze/ttest. Request data: {request_data.model_dump_json() if request_data else 'No request data'}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno durante el análisis.",
        )


@router.get(
    "/experiments/{experiment_id}",
    response_model=ExperimentResponse,
    tags=["Experiments"],
)
async def get_experiment_endpoint(
    experiment_id: uuid.UUID,
    stats_repository: SQLAlchemyStatsRepository = Depends(
        get_stats_repository
    ),
    current_user: UserAuth = Depends(require_roles({"viewer", "analyst"})),
):
    logger.info(
        f"Endpoint /experiments/{experiment_id} llamado por usuario '{current_user.username if current_user else 'anonymous'}'"
    )
    domain_experiment = stats_repository.get(experiment_id=experiment_id)
    if not domain_experiment:
        logger.warning(f"Experimento con ID {experiment_id} no encontrado.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experimento no encontrado.",
        )

    response = ExperimentResponse(
        id=domain_experiment.id,
        name=domain_experiment.name,
        description=domain_experiment.description,
        group_a_data_summary={
            "count": len(domain_experiment.group_a_data),
            "mean": (
                domain_experiment.result.mean_group_a
                if domain_experiment.result
                else None
            ),
        },
        group_b_data_summary={
            "count": len(domain_experiment.group_b_data),
            "mean": (
                domain_experiment.result.mean_group_b
                if domain_experiment.result
                else None
            ),
        },
        parameters=domain_experiment.parameters,
        result=(
            TTestResultSchema.from_orm(domain_experiment.result)
            if domain_experiment.result
            else None
        ),
        mlflow_run_id=domain_experiment.mlflow_run_id,
        tracking_warnings=domain_experiment.tracking_warnings,
        created_at=domain_experiment.created_at,
        updated_at=domain_experiment.updated_at,
    )
    return response


@router.get(
    "/experiments",
    response_model=PaginatedExperimentResponse,
    tags=["Experiments"],
)
async def list_experiments_endpoint(
    skip: int = 0,
    limit: int = 100,
    stats_repository: SQLAlchemyStatsRepository = Depends(
        get_stats_repository
    ),
    current_user: UserAuth = Depends(require_roles({"viewer", "analyst"})),
):
    logger.info(
        f"Endpoint /experiments llamado por usuario '{current_user.username if current_user else 'anonymous'}' con skip={skip}, limit={limit}"
    )
    if limit > 500:
        logger.warning(f"Se solicitó un límite de {limit}, reducido a 500.")
        limit = 500

    domain_experiments, total_count = stats_repository.list_all(
        skip=skip, limit=limit
    )

    response_items = []
    for dexp in domain_experiments:
        response_items.append(
            ExperimentResponse(
                id=dexp.id,
                name=dexp.name,
                description=dexp.description,
                group_a_data_summary={
                    "count": len(dexp.group_a_data),
                    "mean": dexp.result.mean_group_a if dexp.result else None,  # type: ignore
                },
                group_b_data_summary={
                    "count": len(dexp.group_b_data),
                    "mean": dexp.result.mean_group_b if dexp.result else None,  # type: ignore
                },
                parameters=dexp.parameters,
                result=(
                    TTestResultSchema.from_orm(dexp.result)
                    if dexp.result
                    else None
                ),
                mlflow_run_id=dexp.mlflow_run_id,
                tracking_warnings=dexp.tracking_warnings,
                created_at=dexp.created_at,
                updated_at=dexp.updated_at,
            )
        )
    logger.info(
        f"Devolviendo {len(response_items)} experimentos de un total de {total_count}."
    )
    return PaginatedExperimentResponse(total=total_count, items=response_items)


@router.get("/health", response_model=HealthCheckResponse, tags=["Meta"])
async def health_check_stats():
    logger.info("Health check para Aletheia-Stats API invocado.")
    return HealthCheckResponse(status="OK", module="Aletheia-Stats")


logger.info(
    "Aletheia-Stats API Router (presentation.api) cargado y configurado."
)
