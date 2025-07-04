# aletheia_omega/presentation/dependencies.py

import logging
from fastapi import Depends
from sqlalchemy.orm import Session
# unittest.mock no debería ser necesario aquí para producción, se usa en tests.
# from unittest.mock import MagicMock

# --- UserAuth Placeholder (si aletheia_common no está) ---
# El logger se instancia después de la sección try-except para evitar NameError si logging no está importado aún.
_logger_init = False
try:
    from aletheia_common.auth.jwt_handler import UserAuth
    # Si se importa bien, el logger global de este módulo se puede inicializar
    logger = logging.getLogger(__name__)
    logger.info("UserAuth importada de aletheia_common.auth.jwt_handler")
    _logger_init = True
except ImportError:
    # Si la importación falla, definir UserAuth placeholder ANTES de inicializar el logger
    class UserAuth:
        def __init__(self, username: str = "placeholder_user", roles: list = None, user_id: str = "placeholder_id"):
            self.username = username
            self.roles = roles if roles is not None else []
            self.user_id = user_id
    logger = logging.getLogger(__name__)
    logger.warning("UserAuth de aletheia_common no encontrada. Usando placeholder UserAuth en dependencies.py")
    _logger_init = True

if not _logger_init: # Por si acaso el try-except no inicializa el logger
    logger = logging.getLogger(__name__)


# --- Importaciones de Servicios y Casos de Uso del Módulo ---
from ..application.use_cases import (
    FindOptimalModelUseCase,
    EvolveTrajectoryUseCase,    # Nuevo
    ClassifyTrajectoryUseCase   # Nuevo
)
from ..domain.services import (
    KolmogorovComplexityProxyService,
    LikelihoodService,
    OmegaCostService,
    TrajectoryAnalysisService # Nuevo
)
from ..infrastructure.repository import OmegaRepository


# --- Placeholder para la Sesión de Base de Datos ---
def get_db_placeholder() -> Session: # Especificar tipo de retorno
    # Esta es una dependencia que DEBE ser sobreescrita por la aplicación principal
    # o por las pruebas para proporcionar una sesión de SQLAlchemy real.
    logger.critical("Dependencia 'get_db_placeholder' fue llamada. DEBE ser sobreescrita.")
    raise NotImplementedError(
        "La dependencia get_db (o get_db_placeholder) no está implementada/sobreescrita. "
        "Debe ser proporcionada por aletheia_common o configurada localmente para este módulo."
    )

# --- Inyección de Servicios de Dominio ---
def get_kolmogorov_complexity_service() -> KolmogorovComplexityProxyService:
    return KolmogorovComplexityProxyService()

def get_likelihood_service() -> LikelihoodService:
    return LikelihoodService()

def get_omega_cost_service() -> OmegaCostService:
    return OmegaCostService()

def get_trajectory_analysis_service() -> TrajectoryAnalysisService: # Nuevo
    return TrajectoryAnalysisService()

# --- Inyección de Repositorio ---
def get_omega_repository(db: Session = Depends(get_db_placeholder)) -> OmegaRepository:
    return OmegaRepository(db=db)

# --- Dependencia de Autenticación (Placeholder/Desarrollo) ---
async def dev_get_current_user(required_roles: set = Depends(lambda: set())) -> UserAuth:
    logger.warning(
        f"Usando 'dev_get_current_user' placeholder para autenticación. Roles requeridos: {required_roles}. "
        "Esto debería ser sobreescrito en pruebas y reemplazado por la autenticación real en producción."
    )
    return UserAuth(username="dev_default_user", roles=list(required_roles), user_id="dev_default_id")


# --- Inyección para Casos de Uso ---
def get_find_optimal_model_use_case( # Ya existente
    complexity_service: KolmogorovComplexityProxyService = Depends(get_kolmogorov_complexity_service),
    likelihood_service: LikelihoodService = Depends(get_likelihood_service),
    omega_cost_service: OmegaCostService = Depends(get_omega_cost_service),
) -> FindOptimalModelUseCase:
    return FindOptimalModelUseCase(
        complexity_service=complexity_service,
        likelihood_service=likelihood_service,
        omega_cost_service=omega_cost_service,
    )

def get_evolve_trajectory_use_case( # Nuevo
    find_optimal_model_uc: FindOptimalModelUseCase = Depends(get_find_optimal_model_use_case),
    repository: OmegaRepository = Depends(get_omega_repository)
) -> EvolveTrajectoryUseCase:
    return EvolveTrajectoryUseCase(
        find_optimal_model_uc=find_optimal_model_uc,
        repository=repository
    )

def get_classify_trajectory_use_case( # Nuevo
    analysis_service: TrajectoryAnalysisService = Depends(get_trajectory_analysis_service),
    repository: OmegaRepository = Depends(get_omega_repository)
) -> ClassifyTrajectoryUseCase:
    return ClassifyTrajectoryUseCase(
        analysis_service=analysis_service,
        repository=repository
    )
