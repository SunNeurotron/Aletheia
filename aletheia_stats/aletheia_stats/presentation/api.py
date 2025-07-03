import uuid
from typing import List, Optional, Dict, Any
import logging
import os
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # No se usa OAuth2PasswordRequestForm si no hay /token local
from sqlalchemy.orm import Session
# from sqlalchemy import func # No parece usarse directamente aquí

# Imports locales
from ..application.use_cases import PerformTTestUseCase
from ..domain.entities import Experiment as ExperimentDomain
from ..domain.services import StatsService
from ..infrastructure.database import get_db_session_stats # Asegúrate que esta función exista y funcione
from .schemas import (
    TTestRequest, ExperimentResponse, UserSchema, HealthCheckResponse,
    PaginatedExperimentResponse, TTestResultSchema # Token ya no es necesario aquí
)

# Logger
logger = logging.getLogger(__name__)

# OAuth2 scheme para autenticación mock local si aletheia_common falla
# El tokenUrl es relativo al prefijo del router, que es /api/v1.
# Entonces, si hubiera un /token mock, sería /api/v1/token.
# auto_error=False es importante para que Depends(oauth2_scheme_mock) devuelva None si no hay token.
oauth2_scheme_mock = OAuth2PasswordBearer(tokenUrl="token", auto_error=False) # tokenUrl es relativo al router

# Configuración MLflow
MLFLOW_TRACKING_URI_ENV = "STATS_MLFLOW_TRACKING_URI"
DEFAULT_MLFLOW_TRACKING_URI = "http://localhost:5001" # Ajustar si es necesario
MLFLOW_TRACKING_URI = os.getenv(MLFLOW_TRACKING_URI_ENV, DEFAULT_MLFLOW_TRACKING_URI)

# Router
router = APIRouter(tags=["Aletheia-Stats"]) # El prefijo /api/v1 se aplica en main.py

# --- Autenticación: Lógica de Fallback y Selección ---
class MockUserAuth: # Modelo Pydantic-like para el usuario mock
    def __init__(self, username: str, roles: List[str]):
        self.username = username
        self.roles = roles

async def get_current_active_user_mock(token: Optional[str] = Depends(oauth2_scheme_mock)) -> MockUserAuth:
    """Mock de autenticación para desarrollo/testing si aletheia_common no está."""
    logger.debug(f"Mock Auth: Token recibido: {'Presente' if token else 'Ausente'}")
    if not token: # Si no hay token, y auto_error=False, token es None.
        # Para endpoints protegidos que usan este mock, necesitamos decidir qué hacer.
        # Si el endpoint está protegido, esta función debería levantar 401 si no hay token.
        # El OAuth2PasswordBearer con auto_error=True lo haría automáticamente.
        # Con auto_error=False, debemos hacerlo nosotros si el endpoint es protegido.
        # Sin embargo, los endpoints usarán require_user_roles que internamente llamará a esto.
        # require_user_roles_mock SÍ espera un current_user.
        # Por lo tanto, si no hay token, este mock debe fallar para proteger el endpoint.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (mock)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # En desarrollo/testing con mock, aceptar cualquier token y asignar roles.
    # Aquí se podría decodificar un token de prueba si fuera necesario.
    logger.info(f"Mock Auth: Usuario 'testuser_stats_mock' autenticado con roles ['analyst', 'viewer']")
    return MockUserAuth(username="testuser_stats_mock", roles=["analyst", "viewer"])

def require_roles_mock(required_roles: set):
    """Mock de require_roles que siempre permite acceso en desarrollo si el mock está activo."""
    async def role_checker(current_user: MockUserAuth = Depends(get_current_active_user_mock)) -> MockUserAuth:
        logger.warning(
            f"Auth Mock: Acceso permitido por require_roles_mock. "
            f"Usuario: {current_user.username}, Roles Requeridos: {required_roles}, Roles del Usuario: {current_user.roles}"
        )
        # Podríamos añadir una comprobación simple de roles si quisiéramos que el mock fuera más realista:
        # if not required_roles.issubset(set(current_user.roles)):
        #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mock: Insufficient roles")
        return current_user
    return role_checker

try:
    from aletheia_common.auth.jwt_handler import (
        get_current_active_user as common_get_current_active_user,
        require_roles as common_require_roles,
        UserAuth as CommonUserAuthType # Evitar conflicto de nombres con la clase mock
    )
    logger.info("aletheia_common.auth importado exitosamente para aletheia_stats.api.")
    # Usar las funciones y clases reales de aletheia_common
    get_current_user_dependency = common_get_current_active_user
    require_user_roles_dependency = common_require_roles
    UserAuthClassForTypeHint = CommonUserAuthType # Para type hints en endpoints
except ImportError as e:
    logger.warning(f"ADVERTENCIA: aletheia_common.auth no encontrado ({e}). Usando autenticación MOCK para aletheia_stats.api. Esto NO es para producción.")
    # Usar las funciones y clases mock
    get_current_user_dependency = get_current_active_user_mock
    require_user_roles_dependency = require_roles_mock
    UserAuthClassForTypeHint = MockUserAuth # Para type hints en endpoints

# --- Dependencias de la Aplicación ---
def get_stats_service() -> StatsService:
    return StatsService()

def get_mlflow_tracker() -> Optional[MLflowExperimentTracker]:
    """Obtiene el tracker de MLflow o None si no está configurado."""
    if not MLFLOW_TRACKING_URI or MLFLOW_TRACKING_URI.lower() == "none":
        logger.warning("MLflow no configurado o URI es 'none'. MLflowTracker no se inicializará.")
        return None
    try:
        from ..infrastructure.mlflow_tracker import MLflowExperimentTracker # Importación local
        logger.info(f"Intentando inicializar MLflowTracker con URI: {MLFLOW_TRACKING_URI}")
        return MLflowExperimentTracker(tracking_uri=MLFLOW_TRACKING_URI)
    except ImportError: # Si mlflow_tracker.py no existe o tiene problemas
        logger.error("Error al importar MLflowExperimentTracker desde ..infrastructure.mlflow_tracker")
        return None
    except Exception as e:
        logger.error(f"Error inicializando MLflowTracker con URI '{MLFLOW_TRACKING_URI}': {e}", exc_info=True)
        return None

def get_stats_repository(db: Session = Depends(get_db_session_stats)):
    """Obtiene el repositorio de estadísticas."""
    from ..infrastructure.sqlalchemy_repository import SQLAlchemyStatsRepository # Importación local
    return SQLAlchemyStatsRepository(db=db)

def get_perform_ttest_use_case(
    stats_service: StatsService = Depends(get_stats_service),
    stats_repository = Depends(get_stats_repository), # FastAPI infiere el tipo del type hint de la función
    mlflow_tracker = Depends(get_mlflow_tracker)  # FastAPI infiere el tipo
) -> PerformTTestUseCase:
    # Asegurarse de que stats_repository y mlflow_tracker tengan los tipos esperados por PerformTTestUseCase
    # PerformTTestUseCase espera: stats_repository: StatsRepository (alias de SQLAlchemyStatsRepository)
    #                         mlflow_tracker: Optional[MLflowExperimentTracker]
    return PerformTTestUseCase(
        stats_service=stats_service,
        stats_repository=stats_repository, # type: ignore
        mlflow_tracker=mlflow_tracker   # type: ignore
    )

# --- Endpoints ---
@router.get("/users/me", response_model=UserSchema, tags=["Users"])
async def read_users_me_stats(current_user: UserAuthClassForTypeHint = Depends(get_current_user_dependency)): # type: ignore
    """Devuelve detalles del usuario autenticado actualmente."""
    # UserSchema espera 'username' y 'roles', que están en MockUserAuth y CommonUserAuthType
    return UserSchema(username=current_user.username, roles=current_user.roles)

@router.post("/analyze/ttest", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED, tags=["Analysis"])
async def perform_ttest_analysis_endpoint(
    request_data: TTestRequest,
    use_case: PerformTTestUseCase = Depends(get_perform_ttest_use_case),
    current_user: UserAuthClassForTypeHint = Depends(require_user_roles_dependency({"analyst"})) # type: ignore
):
    """Realiza un análisis de prueba t para dos grupos de datos independientes."""
    try:
        experiment_uuid = uuid.uuid4()
        logger.info(f"Endpoint /analyze/ttest llamado por usuario '{current_user.username if current_user else 'anonymous'}' para nuevo experiment_id: {experiment_uuid}")

        domain_experiment: ExperimentDomain = use_case.execute(
            experiment_id=experiment_uuid,
            group_a_data=request_data.group_a_data,
            group_b_data=request_data.group_b_data,
            experiment_name=request_data.experiment_name,
            experiment_description=request_data.experiment_description,
            parameters=request_data.parameters,
            alpha=request_data.alpha
        )

        logger.info(f"Análisis para experiment_id {domain_experiment.id} completado. MLflow run ID: {domain_experiment.mlflow_run_id}")
        if domain_experiment.tracking_warnings:
            logger.warning(f"Experiment {domain_experiment.id} tiene las siguientes advertencias de seguimiento: {domain_experiment.tracking_warnings}")

        response = ExperimentResponse(
            id=domain_experiment.id,
            name=domain_experiment.name,
            description=domain_experiment.description,
            group_a_data_summary={
                "count": len(domain_experiment.group_a_data),
                "mean": domain_experiment.result.mean_group_a if domain_experiment.result else None
            },
            group_b_data_summary={
                "count": len(domain_experiment.group_b_data),
                "mean": domain_experiment.result.mean_group_b if domain_experiment.result else None
            },
            parameters=domain_experiment.parameters,
            result=TTestResultSchema.from_orm(domain_experiment.result) if domain_experiment.result else None,
            mlflow_run_id=domain_experiment.mlflow_run_id,
            tracking_warnings=domain_experiment.tracking_warnings,
            created_at=domain_experiment.created_at,
            updated_at=domain_experiment.updated_at
        )
        return response

    except ValueError as ve:
        logger.warning(f"ValueError en endpoint /analyze/ttest: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint /analyze/ttest. Request data: {request_data.model_dump_json() if request_data else 'No request data'}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno durante el análisis.")

@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse, tags=["Experiments"])
async def get_experiment_endpoint(
    experiment_id: uuid.UUID, # Cambiado a uuid.UUID para consistencia con el modelo de dominio/DB
    stats_repository = Depends(get_stats_repository), # Inferencia de tipo
    current_user: UserAuthClassForTypeHint = Depends(require_user_roles_dependency({"viewer", "analyst"})) # type: ignore
):
    """Obtiene un experimento por su ID."""
    logger.info(f"Endpoint /experiments/{experiment_id} llamado por usuario '{current_user.username if current_user else 'anonymous'}'")
    domain_experiment = stats_repository.get(experiment_id=experiment_id)
    if not domain_experiment:
        logger.warning(f"Experimento con ID {experiment_id} no encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experimento no encontrado.")

    response = ExperimentResponse(
        id=domain_experiment.id,
        name=domain_experiment.name,
        description=domain_experiment.description,
        group_a_data_summary={
            "count": len(domain_experiment.group_a_data),
            "mean": domain_experiment.result.mean_group_a if domain_experiment.result else None
        },
        group_b_data_summary={
            "count": len(domain_experiment.group_b_data),
            "mean": domain_experiment.result.mean_group_b if domain_experiment.result else None
        },
        parameters=domain_experiment.parameters,
        result=TTestResultSchema.from_orm(domain_experiment.result) if domain_experiment.result else None,
        mlflow_run_id=domain_experiment.mlflow_run_id,
        tracking_warnings=domain_experiment.tracking_warnings,
        created_at=domain_experiment.created_at,
        updated_at=domain_experiment.updated_at
    )
    return response

@router.get("/experiments", response_model=PaginatedExperimentResponse, tags=["Experiments"])
async def list_experiments_endpoint(
    skip: int = 0,
    limit: int = 100,
    stats_repository = Depends(get_stats_repository), # Inferencia de tipo
    current_user: UserAuthClassForTypeHint = Depends(require_user_roles_dependency({"viewer", "analyst"})) # type: ignore
):
    """Lista todos los experimentos con paginación."""
    logger.info(f"Endpoint /experiments llamado por usuario '{current_user.username if current_user else 'anonymous'}' con skip={skip}, limit={limit}")
    if limit > 500: # Prevenir
        logger.warning(f"Se solicitó un límite de {limit}, reducido a 500.")
        limit = 500

    domain_experiments, total_count = stats_repository.list_all(skip=skip, limit=limit)

    response_items = []
    for dexp in domain_experiments:
        response_items.append(ExperimentResponse(
            id=dexp.id,
            name=dexp.name,
            description=dexp.description,
            group_a_data_summary={
                "count": len(dexp.group_a_data),
                "mean": dexp.result.mean_group_a if dexp.result else None # type: ignore
            },
            group_b_data_summary={
                "count": len(dexp.group_b_data),
                "mean": dexp.result.mean_group_b if dexp.result else None # type: ignore
            },
            parameters=dexp.parameters,
            result=TTestResultSchema.from_orm(dexp.result) if dexp.result else None,
            mlflow_run_id=dexp.mlflow_run_id,
            tracking_warnings=dexp.tracking_warnings,
            created_at=dexp.created_at,
            updated_at=dexp.updated_at
        ))
    logger.info(f"Devolviendo {len(response_items)} experimentos de un total de {total_count}.")
    return PaginatedExperimentResponse(total=total_count, items=response_items)

@router.get("/health", response_model=HealthCheckResponse, tags=["Meta"])
async def health_check_stats():
    """Endpoint de Health Check para el módulo Aletheia-Stats."""
    logger.info("Health check para Aletheia-Stats API invocado.")
    return HealthCheckResponse(status="OK", module="Aletheia-Stats")

logger.info("Aletheia-Stats API Router (presentation.api) cargado y configurado.")

```
