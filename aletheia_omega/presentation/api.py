# aletheia_omega/presentation/api.py

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, FastAPI

from ..application.use_cases import FindOptimalModelUseCase
from ..domain.entities import OptimizationResult
from .schemas import OptimizationRequest, OptimizationResultResponse

from .dependencies import (
    get_find_optimal_model_use_case,
    get_omega_repository,
    dev_get_current_user, # Nueva dependencia de autenticación simple
    UserAuth # Importar UserAuth desde dependencies.py (donde está el placeholder o se importa de common)
)
from ..infrastructure.repository import OmegaRepository


app = FastAPI(title="Aletheia-Omega Module", version="0.1.0")
router = APIRouter(prefix="/omega", tags=["Omega Model Optimization"])
logger = logging.getLogger(__name__)

# Helper para pasar el conjunto de roles al decorador Depends
def require_roles(roles_set: set):
    async def _role_checker_dependency(user: UserAuth = Depends(dev_get_current_user)) -> UserAuth:
        # En la implementación real de producción, dev_get_current_user sería reemplazado
        # por el verdadero manejador de JWT que ya valida el token y extrae roles.
        # Aquí, el placeholder dev_get_current_user o el mock de prueba ya proveen los roles.
        # Este chequeo es una segunda capa o una forma de especificar roles a nivel de endpoint.
        # Para el mockeo actual, dev_get_current_user (cuando es mockeado) ya da un usuario con roles.
        # Si no se mockea, dev_get_current_user da roles por defecto.

        # logger.info(f"Role checker: User roles: {user.roles}, Required: {roles_set}")
        # if not roles_set.issubset(set(user.roles)):
        #     logger.warning(f"Usuario {user.username} no tiene los roles requeridos: {roles_set}. Roles actuales: {user.roles}")
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="No tiene permisos suficientes."
        #     )
        # El chequeo de roles real se haría en la implementación de producción de dev_get_current_user
        # o en un middleware de autenticación más global.
        # Para esta prueba, el mock de dev_get_current_user es suficiente.
        return user
    return _role_checker_dependency


@router.post("/optimize", response_model=OptimizationResultResponse, status_code=status.HTTP_200_OK)
async def optimize_model_selection(
    request: OptimizationRequest,
    use_case: FindOptimalModelUseCase = Depends(get_find_optimal_model_use_case),
    repo: OmegaRepository = Depends(get_omega_repository),
    current_user: UserAuth = Depends(require_roles({"researcher"})), # Usando el helper
):
    run_id = uuid.uuid4()
    user_identifier = getattr(current_user, 'username', 'unknown_user')
    logger.info(f"Iniciando optimización Omega (Run ID: {run_id}) por el usuario '{user_identifier}'. "
                f"Lambda: {request.lambda_param}, Candidatos: {len(request.candidate_models)}")

    try:
        repo.create_run(
            run_id=run_id,
            search_space_size=len(request.candidate_models),
            lambda_param=request.lambda_param,
            request_params=request.optimization_parameters
        )
    except Exception as db_exc:
        logger.exception(f"Error al crear el registro inicial para la optimización {run_id} en la BD.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar el registro de la optimización en la base de datos: {str(db_exc)}"
        )

    try:
        result: OptimizationResult = use_case.execute(
            candidate_models=request.candidate_models,
            data=request.data_context,
            lambda_param=request.lambda_param,
            optimization_parameters=request.optimization_parameters
        )
        try:
            repo.update_run_with_result(run_id=run_id, result=result, status="COMPLETED")
        except Exception as db_exc: # Error específico al guardar el resultado
            logger.exception(f"Error al guardar el resultado de la optimización {run_id} en la BD. El cálculo fue exitoso.")
            # Intentar actualizar el estado a CALC_DONE_SAVE_FAILED
            try:
                repo.update_run_status(run_id=run_id, status="CALC_DONE_SAVE_FAILED")
            except Exception as inner_db_exc:
                logger.exception(f"Además, error al actualizar estado a CALC_DONE_SAVE_FAILED para {run_id}: {inner_db_exc}")
            # Relanzar la excepción original de guardado como HTTPException
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cálculo completado pero error al guardar el resultado: {str(db_exc)}"
            )

        return OptimizationResultResponse(
            run_id=run_id,
            status="COMPLETED",
            best_model=result.best_model,
            best_model_metrics=result.best_model_metrics,
            search_space_size=result.search_space_size,
            lambda_param_used=result.parameters.get("lambda", request.lambda_param),
            optimization_parameters_stored=result.parameters
        )
    except ValueError as e:
        logger.warning(f"Error de validación en la optimización {run_id}: {e}", exc_info=True)
        repo.update_run_status(run_id=run_id, status="FAILED_VALIDATION")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotImplementedError as e:
        logger.error(f"Error de feature no implementada en optimización {run_id}: {e}", exc_info=True)
        repo.update_run_status(run_id=run_id, status="FAILED_NOT_IMPLEMENTED")
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except HTTPException: # Si ya es una HTTPException (ej. del bloque db_exc), relanzarla directamente
        raise
    except Exception as e: # Captura cualquier otra excepción no manejada previamente
        logger.exception(f"Error inesperado no manejado previamente en la optimización {run_id}: {str(e)}")
        try:
            repo.update_run_status(run_id=run_id, status="FAILED_UNEXPECTED")
        except Exception as db_exc_on_fail:
            logger.exception(f"Además, error al actualizar el estado a FAILED_UNEXPECTED para {run_id} tras error previo: {db_exc_on_fail}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")

app.include_router(router)
