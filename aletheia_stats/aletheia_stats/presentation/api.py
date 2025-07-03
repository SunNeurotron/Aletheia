import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session # Para inyectar la sesión de BD si es necesario directamente

# Dependencias de este módulo
from ..application.use_cases import PerformTTestUseCase
from ..domain.entities import Experiment as ExperimentDomain # Para type hinting
from ..domain.services import StatsService # Para instanciar
from ..infrastructure.sqlalchemy_repository import StatsRepository # Para instanciar
from ..infrastructure.mlflow_tracker import MLflowExperimentTracker # Para instanciar
from .schemas import (
    Token, TTestRequest, ExperimentResponse, UserSchema, HealthCheckResponse,
    PaginatedExperimentResponse
)

# Dependencias comunes de autenticación
# Asumimos que aletheia_common está en el PYTHONPATH o instalado
# Si no, esta importación fallará en tiempo de ejecución.
# Considerar una estructura de 'common_dependencies' inyectada en la app si es más robusto.
try:
    from aletheia_common.auth.jwt_handler import (
        create_access_token,
        get_current_active_user,
        require_roles,
        UserAuth as CommonUserAuth, # Modelo de usuario de aletheia_common
        MOCK_COMMON_USERS_DB, # Para el endpoint /token mock
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    from aletheia_common.auth.password_utils import verify_password # Para el endpoint /token mock
    from datetime import timedelta
except ImportError:
    # Fallback muy básico si aletheia_common no está disponible
    # Esto NO es para producción, solo para permitir que el módulo se cargue
    # Se necesitaría una estrategia de dependencias adecuada.
    # logger.warning("aletheia_common.auth no encontrado. Usando mocks de autenticación muy básicos.") # Reemplazado abajo
    CommonUserAuth = UserSchema
    async def get_current_active_user(): return CommonUserAuth(username="mockuser", roles=["viewer"])
    def require_roles(roles): return lambda: CommonUserAuth(username="mockuser", roles=list(roles))
    from datetime import timedelta

import logging # Importar logging
logger = logging.getLogger(__name__) # Obtener logger a nivel de módulo

# Fallback de importación con logging
try:
    from aletheia_common.auth.jwt_handler import (
        get_current_active_user as common_get_current_active_user_real, # Renombrar para evitar conflicto con el mock
        require_roles as common_require_roles_real,
        UserAuth as CommonUserAuthReal
    )
    # Asignar los reales si la importación es exitosa
    get_current_active_user = common_get_current_active_user_real
    require_roles = common_require_roles_real
    CommonUserAuth = CommonUserAuthReal
    logger.info("aletheia_common.auth importado exitosamente para aletheia_stats.api.")
except ImportError as e:
    logger.warning(f"ADVERTENCIA: aletheia_common.auth no encontrado ({e}). Usando mocks de autenticación muy básicos para aletheia_stats.api. Esto NO es para producción.")
    # Las definiciones mock de CommonUserAuth, get_current_active_user, require_roles ya están arriba.

import os # Para leer variables de entorno para MLFLOW_TRACKING_URI

# Configuración del Módulo (ej. para MLflow)
# DATABASE_URL se manejará a través del nuevo infrastructure.database
MLFLOW_TRACKING_URI_ENV = "STATS_MLFLOW_TRACKING_URI"
DEFAULT_MLFLOW_TRACKING_URI = "http://localhost:5001" # Puerto diferente al principal
MLFLOW_TRACKING_URI = os.getenv(MLFLOW_TRACKING_URI_ENV, DEFAULT_MLFLOW_TRACKING_URI)


# --- Router de API ---
# El prefijo /api/v1 se aplicará en main.py al incluir el router.
router = APIRouter(tags=["Aletheia-Stats"]) # Tags para agrupar en Swagger

# --- Dependencias de la API (Instanciación de servicios y repositorios) ---
# Se importa la función get_db_session_stats del nuevo módulo de base de datos
from ..infrastructure.database import get_db_session_stats

def get_stats_repository(db: Session = Depends(get_db_session_stats)) -> StatsRepository:
    # StatsRepository ahora debería aceptar una sesión de SQLAlchemy o usar una global si es necesario
    # Por ahora, asumimos que StatsRepository se adapta para tomar la sesión `db`
    # o que su inicialización global usa el `engine` de infrastructure.database.
    # Si StatsRepository(database_url=...) crea su propio engine, esto necesita refactorización.
    # StatsRepository (ahora SQLAlchemyStatsRepository) espera una sesión de BD.
    # La clase real es SQLAlchemyStatsRepository, StatsRepository es un alias en el módulo del repo.
    from ..infrastructure.sqlalchemy_repository import SQLAlchemyStatsRepository
    return SQLAlchemyStatsRepository(db=db)


def get_mlflow_tracker() -> Optional[MLflowExperimentTracker]:
    # Podría retornar None si MLflow no está configurado o es opcional
    if not MLFLOW_TRACKING_URI or MLFLOW_TRACKING_URI.lower() == "none":
        logger.warning("MLFLOW_TRACKING_URI no configurado o es 'none'. MLflowTracker no se inicializará.")
        return None
    try:
        # Usar la variable MLFLOW_TRACKING_URI leída de env var
        logger.info(f"Intentando inicializar MLflowTracker con URI: {MLFLOW_TRACKING_URI}")
        return MLflowExperimentTracker(tracking_uri=MLFLOW_TRACKING_URI)
    except Exception as e:
        logger.error(f"No se pudo inicializar MLflowTracker con URI '{MLFLOW_TRACKING_URI}': {e}", exc_info=True)
        return None

def get_stats_service() -> StatsService:
    return StatsService()

def get_perform_ttest_use_case(
    stats_service: StatsService = Depends(get_stats_service),
    stats_repository: StatsRepository = Depends(get_stats_repository),
    mlflow_tracker: Optional[MLflowExperimentTracker] = Depends(get_mlflow_tracker)
) -> PerformTTestUseCase:
    return PerformTTestUseCase(
        stats_service=stats_service,
        stats_repository=stats_repository,
        mlflow_tracker=mlflow_tracker
    )

# --- Endpoints de Autenticación (Mock/Adaptado) ---
# --- Endpoints de Autenticación ---
# El endpoint /token ha sido eliminado. aletheia_stats ahora depende de tokens emitidos por Aletheia_v3.
# La variable de entorno OAUTH2_SCHEME_TOKEN_URL para este módulo debe apuntar al
# endpoint /token de Aletheia_v3.

@router.get("/users/me", response_model=UserSchema, tags=["Users"]) # Usa UserSchema local
async def read_users_me_stats(current_user: CommonUserAuth = Depends(get_current_active_user)): # get_current_active_user es del fallback mock por ahora
    """
    Devuelve detalles del usuario autenticado actualmente.
    """
    # Convierte CommonUserAuth a UserSchema local si es necesario, o ajusta UserSchema
    return UserSchema(username=current_user.username, roles=current_user.roles)


# --- Endpoints de Análisis Estadístico ---

@router.post("/analyze/ttest", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED, tags=["Analysis"])
async def perform_ttest_analysis_endpoint(
    request_data: TTestRequest,
    use_case: PerformTTestUseCase = Depends(get_perform_ttest_use_case),
    current_user: CommonUserAuth = Depends(require_roles({"analyst"})) # Seguridad de roles activada
):
    """
    Realiza un análisis de prueba t para dos grupos de datos independientes.
    Requiere rol 'analyst'.
    """
    try:
        # El ID del experimento se genera aquí antes de pasarlo al caso de uso.
        experiment_uuid = uuid.uuid4()

        domain_experiment: ExperimentDomain = use_case.execute(
            experiment_id=experiment_uuid,
            group_a_data=request_data.group_a_data,
            group_b_data=request_data.group_b_data,
            experiment_name=request_data.experiment_name,
            experiment_description=request_data.experiment_description,
            parameters=request_data.parameters,
            alpha=request_data.alpha
        )

        # Mapear entidad de dominio a schema de respuesta
        # Esto podría ser más elaborado, ej. con una función de mapeo.
        response = ExperimentResponse(
            id=domain_experiment.id,
            name=domain_experiment.name,
            description=domain_experiment.description,
            group_a_data_summary={"count": len(domain_experiment.group_a_data), "mean": domain_experiment.result.mean_group_a if domain_experiment.result else None},
            group_b_data_summary={"count": len(domain_experiment.group_b_data), "mean": domain_experiment.result.mean_group_b if domain_experiment.result else None},
            parameters=domain_experiment.parameters,
            result=TTestResultSchema.from_orm(domain_experiment.result) if domain_experiment.result else None,
            mlflow_run_id=domain_experiment.mlflow_run_id,
            tracking_warnings=domain_experiment.tracking_warnings, # Añadir tracking_warnings
            created_at=domain_experiment.created_at,
            updated_at=domain_experiment.updated_at
        )
        return response

    except ValueError as ve:
        logger.warning(f"ValueError en endpoint ttest: {ve}") # Loguear el ValueError
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint ttest para experiment_id (potencial): {experiment_uuid}") # Usar logger.exception
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Un error interno ocurrió durante el análisis.")


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse, tags=["Experiments"])
async def get_experiment_endpoint(
    experiment_id: UUID,
    stats_repository: StatsRepository = Depends(get_stats_repository),
    current_user: CommonUserAuth = Depends(require_any_role({"viewer", "analyst"})) # Seguridad de roles activada
):
    """
    Obtiene un experimento por su ID.
    Requiere rol 'viewer' o 'analyst'.
    """
    domain_experiment = stats_repository.get(experiment_id=experiment_id) # SQLAlchemyStatsRepository.get
    if not domain_experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experimento no encontrado.")

    response = ExperimentResponse(
        id=domain_experiment.id,
        name=domain_experiment.name,
        description=domain_experiment.description,
        group_a_data_summary={"count": len(domain_experiment.group_a_data), "mean": domain_experiment.result.mean_group_a if domain_experiment.result else None},
        group_b_data_summary={"count": len(domain_experiment.group_b_data), "mean": domain_experiment.result.mean_group_b if domain_experiment.result else None},
        parameters=domain_experiment.parameters,
        result=TTestResultSchema.from_orm(domain_experiment.result) if domain_experiment.result else None,
        mlflow_run_id=domain_experiment.mlflow_run_id,
            tracking_warnings=domain_experiment.tracking_warnings, # Añadir tracking_warnings
        created_at=domain_experiment.created_at,
        updated_at=domain_experiment.updated_at
    )
    return response

@router.get("/experiments", response_model=PaginatedExperimentResponse, tags=["Experiments"])
async def list_experiments_endpoint(
    skip: int = 0,
    limit: int = 100,
    stats_repository: StatsRepository = Depends(get_stats_repository),
    current_user: CommonUserAuth = Depends(require_any_role({"viewer", "analyst"})) # Seguridad de roles activada
):
    """
    Lista todos los experimentos con paginación.
    Requiere rol 'viewer' o 'analyst'.
    """
    if limit > 500: # Limitar el máximo de `limit`
        limit = 500

    domain_experiments, total_count = stats_repository.list_all(skip=skip, limit=limit) # SQLAlchemyStatsRepository.list_all

    response_items = []
    for dexp in domain_experiments:
        response_items.append(ExperimentResponse(
            id=dexp.id,
            name=dexp.name,
            description=dexp.description,
            group_a_data_summary={"count": len(dexp.group_a_data), "mean": dexp.result.mean_group_a if dexp.result else None}, # type: ignore
            group_b_data_summary={"count": len(dexp.group_b_data), "mean": dexp.result.mean_group_b if dexp.result else None}, # type: ignore
            parameters=dexp.parameters,
            result=TTestResultSchema.from_orm(dexp.result) if dexp.result else None,
            mlflow_run_id=dexp.mlflow_run_id,
            tracking_warnings=dexp.tracking_warnings, # Añadir tracking_warnings
            created_at=dexp.created_at,
            updated_at=dexp.updated_at
        ))

    return PaginatedExperimentResponse(total=total_count, items=response_items)

# --- Endpoint de Health Check ---
@router.get("/health", response_model=HealthCheckResponse, tags=["Meta"])
async def health_check_stats():
    """
    Endpoint de Health Check para el módulo Aletheia-Stats.
    """
    # En el futuro, podría verificar la conexión a la BD o MLflow.
    # version = "0.1.0" # Podría venir de un archivo de versión o var de entorno
    return HealthCheckResponse(status="OK", module="Aletheia-Stats") # version=version

# Nota: La aplicación FastAPI principal que usa este router debe estar en main.py
# y manejar la configuración global, la inicialización de la base de datos (Alembic), etc.
# Este archivo se centra en la definición de los endpoints.
# Los TODOs sobre seguridad y configuración de dependencias son cruciales para producción.
logger.info("Aletheia-Stats API Router (presentation.api) cargado.")
# Las notas sobre seguridad de roles comentada y placeholders de dependencias ya no son tan precisas
# o se manejan con los logs de advertencia/error anteriores.

# TODO:
# 1. Implementar `get_db_session_placeholder` con la gestión real de sesión de SQLAlchemy. # HECHO, usa get_db_session_stats
#    Esto implica tener `infrastructure/database.py` en `aletheia_stats` con `engine`, `SessionLocal`.
# 2. Configurar adecuadamente las URLs de BD y MLflow mediante variables de entorno.
# 3. Descomentar y probar la seguridad de roles (`require_roles`).
# 4. Asegurar que `aletheia_common` sea una dependencia correctamente instalada o accesible.
# 5. Añadir logging estructurado en lugar de `print`.
# 6. Crear migraciones con Alembic para los modelos de `StatsRepository`.
# 7. Escribir pruebas de integración completas.
# 8. El `PaginatedExperimentResponse` podría necesitar un schema más detallado para `items` si `ExperimentResponse` es muy grande.
#    Actualmente, `group_a_data_summary` y `group_b_data_summary` son simplificaciones.
#    Si se necesita la data completa para algunos listados, considerar un `ExperimentDetailResponse`.
# 9. El endpoint `/token` es un mock. Para producción, debe integrarse con un sistema de usuarios real
#    y usar `passlib` para el hash y verificación de contraseñas de forma segura.
#    El `MOCK_COMMON_USERS_DB` y `verify_password` simplificado son inseguros.
#    Idealmente, `aletheia_stats` usaría el mismo proveedor de identidad que `Aletheia_v3`.
#    Si `Aletheia_v3` es el proveedor de tokens, entonces `aletheia_stats` no necesita su propio endpoint `/token`,
#    sino que validaría los tokens emitidos por `Aletheia_v3`.
#    El `README.md` de `aletheia_stats` sugiere un endpoint `/token` propio, lo que implica un manejo de usuarios separado o replicado.
#    Esta es una decisión arquitectónica importante a clarificar.
#    Por ahora, se ha implementado un mock siguiendo la indicación del README.
```
