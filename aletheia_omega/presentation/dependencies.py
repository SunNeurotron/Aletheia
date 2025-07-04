# aletheia_omega/presentation/dependencies.py

import logging
from fastapi import Depends
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

# Importar UserAuth desde api.py (donde está el placeholder si aletheia_common falla)
# o directamente desde aletheia_common si se prefiere y está disponible.
# Para mantenerlo simple y desacoplado para esta prueba, asumimos que UserAuth
# es una clase conocida o la definimos/importamos aquí de forma que el mock la pueda usar.
try:
    from aletheia_common.auth.jwt_handler import UserAuth
    logger = logging.getLogger(__name__) # Mover el logger aquí para que esté disponible
    logger.info("UserAuth importada de aletheia_common.auth.jwt_handler")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("UserAuth de aletheia_common no encontrada. Definiendo placeholder UserAuth en dependencies.py")
    class UserAuth: # Placeholder si no se encuentra en common
        def __init__(self, username: str = "placeholder_user", roles: list = None, user_id: str = "placeholder_id"):
            self.username = username
            self.roles = roles if roles is not None else []
            self.user_id = user_id

from ..application.use_cases import FindOptimalModelUseCase
from ..domain.services import (
    KolmogorovComplexityProxyService,
    LikelihoodService,
    OmegaCostService,
)
from ..infrastructure.repository import OmegaRepository


# --- Placeholder para get_db ---
def get_db_placeholder():
    raise NotImplementedError("get_db no está implementado. Debe ser proporcionado por aletheia_common o configurado localmente.")

# --- Inyección de Servicios de Dominio ---
def get_kolmogorov_complexity_service() -> KolmogorovComplexityProxyService:
    return KolmogorovComplexityProxyService()

def get_likelihood_service() -> LikelihoodService:
    return LikelihoodService()

def get_omega_cost_service() -> OmegaCostService:
    return OmegaCostService()

# --- Inyección de Repositorio ---
def get_omega_repository(db: Session = Depends(get_db_placeholder)) -> OmegaRepository:
    return OmegaRepository(db=db)

# --- Dependencia de Autenticación para Pruebas y Desarrollo Aislado ---
async def dev_get_current_user(required_roles: set = Depends(lambda: set())) -> UserAuth:
    """
    Dependencia de autenticación por defecto para desarrollo y pruebas aisladas.
    En un entorno de producción, esto sería reemplazado o configurado para
    usar el sistema de autenticación real (ej. aletheia_common.auth).
    Para las pruebas de este módulo, esta función será sobreescrita.
    El argumento required_roles está aquí para mantener una firma similar,
    pero el chequeo de roles se hará en el override o en la implementación real.
    """
    logger.warning(
        f"Usando 'dev_get_current_user' placeholder para autenticación. Roles requeridos por endpoint: {required_roles}. "
        "Esto debería ser sobreescrito en pruebas y reemplazado en producción."
    )
    # Por defecto, devuelve un usuario con los roles solicitados para facilitar el desarrollo aislado.
    # En las pruebas, esto será mockeado de todas formas.
    return UserAuth(username="dev_default_user", roles=list(required_roles), user_id="dev_default_id")

# --- Inyección para el Caso de Uso ---
def get_find_optimal_model_use_case(
    complexity_service: KolmogorovComplexityProxyService = Depends(get_kolmogorov_complexity_service),
    likelihood_service: LikelihoodService = Depends(get_likelihood_service),
    omega_cost_service: OmegaCostService = Depends(get_omega_cost_service),
) -> FindOptimalModelUseCase:
    return FindOptimalModelUseCase(
        complexity_service=complexity_service,
        likelihood_service=likelihood_service,
        omega_cost_service=omega_cost_service,
    )
