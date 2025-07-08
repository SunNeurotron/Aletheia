from typing import Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm # OAuth2PasswordRequestForm needed for token endpoint
from datetime import datetime, timedelta
import jwt # For token generation and verification

# Schemas for MDU specific requests/responses
from .schemas import AnalisisRequest, MDUAnalisisResponse, MDUAnalysisStatusResponse

# Application layer facade/service (adjust import path as needed)
# Assuming ApplicationServiceFacade is in application.use_cases
from ..application.use_cases import ApplicationServiceFacade
# Placeholder for actual ApplicationServiceFacade dependencies if not using default create_mdu_application_instance style
from ..application.ports import IAnalysisRepository, IExperimentTracker, ITaskQueue
from ..core.domain_services import DomainService
from ..core.cube_models import CuboMDU # PresentationFace takes CuboMDU
from .dependencies import get_monitoring_system # Import for monitoring system

# Default/Placeholder infrastructure components if create_mdu_application_instance is not used directly
# This is for allowing PresentationFace to be instantiated.
# In a real setup, these would be properly injected.
from ..infrastructure.repositories import PostgreSQLRepository # Example
from ..infrastructure.trackers import MLflowTracker # Example
from ..infrastructure.queues import CeleryTaskQueue # Example
from ..core.domain_services import TheoryBuilder # Example dependency for DomainService


class SecurityConfig:
    """Configuración de seguridad para la API MDU."""
    SECRET_KEY: str = "mdu_secret_key_example_please_change" # TODO: Load from env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

class PresentationFace:
    """
    Cara de Presentación del Cubo MDU. Expone los endpoints de la API.
    """
    def __init__(self, app_service: ApplicationServiceFacade, cube_mdu_instance: CuboMDU, security_config: SecurityConfig):
        self.app_service = app_service
        self.cube = cube_mdu_instance # Though not directly used in these specific endpoints
        self.security_config = security_config
        self._oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/mdu/token") # Adjusted tokenUrl for MDU context

        # FastAPI app instance specific to this PresentationFace, can be mounted by a main app
        self.router = FastAPI() # Using a sub-FastAPI instance as a router is also an option
                                # Or directly add routes to a main app instance passed in.
                                # For now, let's assume this will be the main app for MDU.
        self._setup_routes()

    def _setup_routes(self):
        # Define routes on self.router
        # Prefixing with /mdu to namespace these API endpoints
        @self.router.post("/mdu/analyze", response_model=MDUAnalisisResponse, tags=["MDU Analysis"])
        async def analyze_session(
            request: AnalisisRequest,
            # TODO: User type hint should be more specific if possible (e.g. a Pydantic model for user claims)
            user: Dict[str, Any] = Depends(self._get_current_user) # Use dependency for user
        ):
            """
            Endpoint principal para iniciar un análisis MDU.
            Requiere autenticación JWT.
            """
            # Delegate to application service
            # The ApplicationServiceFacade.handle_analysis_request expects (request, user_dict)
            # The _get_current_user provides the user_dict (payload of JWT)
            result = await self.app_service.handle_analysis_request(request, user)
            # Adapt result from app_service to MDUAnalisisResponse
            # Assuming app_service result contains: analysis_id, model, metrics, run_id
            return MDUAnalisisResponse(
                analysis_id=result.get("analysis_id", "N/A"),
                status_message=f"Analysis {result.get('analysis_id', 'N/A')} started with run ID {result.get('run_id', 'N/A')}.",
                details_url=f"/api/v1/mdu/status/{result.get('analysis_id', '')}" # Example, adjust base path
            )

        @self.router.get("/mdu/status/{session_id}", response_model=MDUAnalysisStatusResponse, tags=["MDU Analysis"])
        async def get_analysis_status(session_id: str, user: Dict[str, Any] = Depends(self._get_current_user)):
            """
            Monitorea el estado de un análisis MDU en tiempo real.
            Requiere autenticación JWT.
            """
            # print(f"MDU API: User {user.get('sub')} requesting status for {session_id}") # For debug
            status_details = await self.app_service.get_analysis_status(session_id)
            return MDUAnalysisStatusResponse(
                session_id=session_id,
                current_status=status_details.get("status", "UNKNOWN"),
                progress_percent=float(status_details.get("progress", "0.0").replace('%','')), # Convert progress
                details=status_details.get("details")
            )

        @self.router.post("/mdu/token", tags=["MDU Authentication"]) # No response_model for direct token return
        async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
            """
            Endpoint para obtener un token de acceso JWT.
            (Simulación de autenticación - usar credenciales de prueba)
            """
            # Simple hardcoded user for demonstration
            if form_data.username == "mdu_user" and form_data.password == "mdu_pass":
                user_identity = form_data.username
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, # type: ignore # Use status from fastapi
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            access_token_expires = timedelta(minutes=self.security_config.ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode = {"sub": user_identity, "exp": datetime.utcnow() + access_token_expires}
            encoded_jwt = jwt.encode(to_encode, self.security_config.SECRET_KEY, algorithm=self.security_config.ALGORITHM)
            return {"access_token": encoded_jwt, "token_type": "bearer"}

    async def _get_current_user(self, token: str = Depends(OAuth2PasswordBearer(tokenUrl="/mdu/token"))) -> Dict[str, Any]:
        """
        Dependencia para obtener el usuario actual a partir del token JWT.
        Verifica el token y devuelve su payload.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # type: ignore
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.security_config.SECRET_KEY, algorithms=[self.security_config.ALGORITHM])
            username: Optional[str] = payload.get("sub")
            if username is None:
                raise credentials_exception
            # Here you could add more checks, e.g., fetch user from DB, check active status etc.
            # For now, payload itself is considered the user identity.
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"}) # type: ignore
        except jwt.JWTError:
            raise credentials_exception


# --- FastAPI App Instantiation ---
# This function sets up the MDU specific API with its dependencies.
# It can be called by a main factory in the root of Aletheia_v3/api/ or directly by main.py

def create_mdu_api_application() -> FastAPI:
    """
    Crea y configura la instancia de la aplicación FastAPI para el MDU Cube API.
    """
    # Instantiate dependencies (placeholders or real ones based on config)
    # These would typically come from a dependency injection system or config files.

    # Placeholder/Default Infrastructure (replace with actual configuration/DI)
    # Ensure connection strings and URIs are sensible defaults or loaded from env/config
    db_connection_str = "postgresql+asyncpg://user:pass@localhost:5432/mdu_db_default"
    mlflow_tracking_uri = "file:./mdu_mlruns"
    celery_broker_url = "redis://localhost:6379/0"

    try:
        repo = PostgreSQLRepository(db_connection_str)
    except Exception as e_repo:
        print(f"MDU API Server: Failed to init PostgreSQLRepository ({e_repo}). Using mock.")
        # Fallback to a simple mock if DB connection fails at setup
        class MockRepo(IAnalysisRepository):
            async def save(self, data: Any) -> str: return "mock_analysis_id"
            async def get(self, id_str: str) -> Optional[Any]: return None
            async def update(self, id_str: str, data: Dict) -> None: pass
        repo = MockRepo() # type: ignore

    tracker = MLflowTracker(mlflow_tracking_uri)
    queue = CeleryTaskQueue(broker_url=celery_broker_url, backend_url=celery_broker_url)

    # Domain
    theory_builder = TheoryBuilder()
    domain_service = DomainService(theory_builder=theory_builder)

    # Application Service
    app_service = ApplicationServiceFacade(domain_service, repo, tracker, queue)

    # Monitoring System
    monitoring_system = get_monitoring_system()

    # MDU Cube instance (if needed by PresentationFace logic directly)
    mdu_cube = CuboMDU(monitoring_system=monitoring_system)

    # Security Config
    sec_config = SecurityConfig() # Load from env vars in a real app

    # Presentation Face
    mdu_presentation_face = PresentationFace(app_service, mdu_cube, sec_config)

    # The FastAPI instance to be returned (can be mdu_presentation_face.router or a new FastAPI app that mounts it)
    # If mdu_presentation_face.router is a FastAPI instance itself:
    # return mdu_presentation_face.router

    # If we want a root FastAPI app that might include other routers from Aletheia_v3:
    # For now, let's assume the MDU API is standalone or its router is the main app for this module.
    # The global `app` in mdu_cube_system.py was `PresentationFace(...).app`
    # So, `mdu_presentation_face.router` (which is a FastAPI instance) is the equivalent.

    # Add OpenAPI endpoint to this specific MDU API router
    from .openapi_spec import OpenAPIGenerator # Assuming openapi_spec.py is created
    openapi_gen = OpenAPIGenerator(mdu_router_app=mdu_presentation_face.router) # Pass the app to generator

    @mdu_presentation_face.router.get("/mdu/openapi.json", include_in_schema=False, tags=["MDU Documentation"])
    async def get_mdu_openapi_schema():
        return openapi_gen.generate_spec() # Call method on instance

    return mdu_presentation_face.router


# This `app` instance can be imported by the main `main.py` at the project root
# or by Aletheia_v3/api/api_server.py if that's the main aggregator for all APIs.
# For now, this provides the MDU-specific FastAPI app.
# The plan suggests `Aletheia_v3/api/main.py or api_server.py` will contain this.
# So, this file (mdu_api_server.py) defines create_mdu_api_application(),
# and the actual `app` instance would be created in Aletheia_v3/api/api_server.py (or main.py).

# For direct runnable example if this file were the main entry:
# app = create_mdu_api_application()
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001) # Run on a different port if main Aletheia API is on 8000

# Need to import status for HTTPException
from fastapi import status
