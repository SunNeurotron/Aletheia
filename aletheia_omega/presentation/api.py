# aletheia_omega/presentation/api.py

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, FastAPI, Path # Path para trajectory_id

from ..application.use_cases import ( # Importar todos los casos de uso
    FindOptimalModelUseCase,
    EvolveTrajectoryUseCase,
    ClassifyTrajectoryUseCase
)
from ..domain.entities import OptimizationResult, Trajectory, TrajectoryAnalysis # Importar entidades de dominio
from .schemas import ( # Importar todos los schemas necesarios
    OptimizationRequest,
    OptimizationResultResponse,
    TrajectoryCreationRequest,
    TrajectoryResponse,
    EvolveTrajectoryRequest,
    TrajectoryAnalysisResponse,
    TrajectoryStepSchema # Importar TrajectoryStepSchema
)

from .dependencies import (
    get_find_optimal_model_use_case,
    get_omega_repository,
    dev_get_current_user,
    UserAuth,
    get_evolve_trajectory_use_case,    # Nuevas dependencias de caso de uso
    get_classify_trajectory_use_case
)
from ..infrastructure.repository import OmegaRepository # Para tipo de `repo`
from ..infrastructure.models import TrajectoryDB # Para el tipo de retorno de repo.create_trajectory


app = FastAPI(title="Aletheia-Omega Module", version="0.1.0")
# Router principal para /omega
omega_router = APIRouter(prefix="/omega", tags=["Omega Module"])
# Sub-router para trayectorias
trajectories_router = APIRouter(prefix="/trajectories", tags=["Omega Trajectories"])

logger = logging.getLogger(__name__)

# Helper de autenticación (sin cambios)
def require_roles(roles_set: set):
    async def _role_checker_dependency(user: UserAuth = Depends(dev_get_current_user)) -> UserAuth:
        return user
    return _role_checker_dependency


# --- Endpoints para Trayectorias (Fase 2) ---

@trajectories_router.post("", response_model=TrajectoryResponse, status_code=status.HTTP_201_CREATED)
async def create_trajectory(
    request: TrajectoryCreationRequest,
    repo: OmegaRepository = Depends(get_omega_repository),
    current_user: UserAuth = Depends(require_roles({"researcher"}))
):
    user_identifier = getattr(current_user, 'username', 'unknown_user')
    logger.info(f"Usuario '{user_identifier}' creando nueva trayectoria con nombre: '{request.name}'.")
    try:
        trajectory_db: TrajectoryDB = repo.create_trajectory(name=request.name)
        return TrajectoryResponse(
            id=trajectory_db.id,
            name=trajectory_db.name,
            created_at=trajectory_db.created_at,
            steps=[]
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error inesperado al crear trayectoria '{request.name}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al crear trayectoria.")


@trajectories_router.post("/{trajectory_id}/evolve", response_model=TrajectoryResponse)
async def evolve_trajectory(
    request: EvolveTrajectoryRequest,
    trajectory_id: uuid.UUID = Path(..., description="ID de la trayectoria a evolucionar."),
    evolve_uc: EvolveTrajectoryUseCase = Depends(get_evolve_trajectory_use_case),
    repo: OmegaRepository = Depends(get_omega_repository), # Necesario para obtener created_at
    current_user: UserAuth = Depends(require_roles({"researcher"}))
):
    user_identifier = getattr(current_user, 'username', 'unknown_user')
    logger.info(f"Usuario '{user_identifier}' evolucionando trayectoria ID: {trajectory_id}.")
    try:
        updated_trajectory_domain: Trajectory = evolve_uc.execute(
            trajectory_id=trajectory_id,
            new_data=request.data_context,
            model_search_space=request.candidate_models,
            lambda_param=request.lambda_param,
            optimization_parameters=request.optimization_parameters
        )

        # Obtener TrajectoryDB para el created_at, ya que el objeto de dominio no lo tiene
        trajectory_db_for_date = repo.get_trajectory_db_by_id(updated_trajectory_domain.id)
        if not trajectory_db_for_date:
            logger.error(f"No se pudo encontrar TrajectoryDB {updated_trajectory_domain.id} después de la evolución para obtener created_at.")
            # Esto es un estado inconsistente o un error grave si el caso de uso tuvo éxito.
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al recuperar metadatos de la trayectoria post-evolución.")

        return TrajectoryResponse(
            id=updated_trajectory_domain.id,
            name=updated_trajectory_domain.name,
            created_at=trajectory_db_for_date.created_at, # Tomado de TrajectoryDB
            steps=[TrajectoryStepSchema.model_validate(step) for step in updated_trajectory_domain.steps]
        )

    except ValueError as e:
        logger.warning(f"Error de valor al evolucionar trayectoria {trajectory_id}: {e}", exc_info=False)
        status_code = status.HTTP_404_NOT_FOUND if "no existe" in str(e).lower() or "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Error de ejecución al evolucionar trayectoria {trajectory_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error inesperado al evolucionar trayectoria {trajectory_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor.")


@trajectories_router.get("/{trajectory_id}/classification", response_model=TrajectoryAnalysisResponse)
async def get_trajectory_classification(
    trajectory_id: uuid.UUID = Path(..., description="ID de la trayectoria a clasificar."),
    classify_uc: ClassifyTrajectoryUseCase = Depends(get_classify_trajectory_use_case),
    current_user: UserAuth = Depends(require_roles({"researcher"}))
):
    user_identifier = getattr(current_user, 'username', 'unknown_user')
    logger.info(f"Usuario '{user_identifier}' solicitando clasificación para trayectoria ID: {trajectory_id}.")
    try:
        analysis_domain: TrajectoryAnalysis = classify_uc.execute(trajectory_id)
        return TrajectoryAnalysisResponse.model_validate(analysis_domain)
    except ValueError as e:
        logger.warning(f"Error de valor al clasificar trayectoria {trajectory_id}: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error inesperado al clasificar trayectoria {trajectory_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor.")


@trajectories_router.get("/{trajectory_id}", response_model=TrajectoryResponse)
async def get_trajectory_details(
    trajectory_id: uuid.UUID = Path(..., description="ID de la trayectoria a recuperar."),
    repo: OmegaRepository = Depends(get_omega_repository),
    current_user: UserAuth = Depends(require_roles({"researcher"}))
):
    user_identifier = getattr(current_user, 'username', 'unknown_user')
    logger.info(f"Usuario '{user_identifier}' solicitando detalles de trayectoria ID: {trajectory_id}.")
    try:
        trajectory_domain = repo.get_trajectory_with_steps(trajectory_id)
        if not trajectory_domain:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Trayectoria con ID {trajectory_id} no encontrada.")

        trajectory_db = repo.get_trajectory_db_by_id(trajectory_id)
        if not trajectory_db:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Datos de base de Trayectoria con ID {trajectory_id} no encontrados.")

        return TrajectoryResponse(
            id=trajectory_domain.id,
            name=trajectory_domain.name,
            created_at=trajectory_db.created_at,
            steps=[TrajectoryStepSchema.model_validate(step) for step in trajectory_domain.steps]
        )
    except HTTPException as http_exc:
        raise http_exc
    except ValueError as e:
        logger.warning(f"Error de valor al obtener detalles de trayectoria {trajectory_id}: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Error inesperado al recuperar detalles de trayectoria {trajectory_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor.")


omega_router.include_router(trajectories_router)
app.include_router(omega_router)
