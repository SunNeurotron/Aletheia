from typing import Dict, Any, Optional, List # Added List and Optional
from pydantic import BaseModel, Field # For schema definitions within OpenAPI
# Assuming AnalisisRequest and other MDU schemas are in .schemas
from .schemas import AnalisisRequest, MDUAnalisisResponse, MDUAnalysisStatusResponse, Token

# If CubeHoneycombIntegration.__version__ is needed and it's moved, adjust import
# For now, let's use a static version or assume it's passed if needed.
# from ...mdu_cube_integration_module import CubeHoneycombIntegration # Example if it moves

class OpenAPIGenerator:
    """Generador de especificación OpenAPI para el sistema MDU."""

    def __init__(self, mdu_router_app: Optional[Any] = None, app_version: str = "0.1.0-mdu"):
        """
        Initialize the OpenAPI generator.
        Optionally pass the FastAPI app instance to introspect routes,
        or define paths manually.
        """
        self.mdu_app = mdu_router_app # The FastAPI app instance for MDU routes
        self.app_version = app_version


    def _get_mdu_schemas(self) -> Dict[str, Any]:
        """Genera las definiciones de esquemas Pydantic para OpenAPI."""
        schemas = {
            "MDUAnalisisRequest": AnalisisRequest.schema(),
            "MDUAnalisisResponse": MDUAnalisisResponse.schema(),
            "MDUAnalysisStatusResponse": MDUAnalysisStatusResponse.schema(),
            "MDUTokenResponse": Token.schema(), # Using the existing Token schema
            # Common HTTPValidationError schema for FastAPI
            "HTTPValidationError": {
                "title": "HTTPValidationError",
                "type": "object",
                "properties": {
                    "detail": {
                        "title": "Detail",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "loc": {"title": "Location", "type": "array", "items": {"type": "string"}},
                                "msg": {"title": "Message", "type": "string"},
                                "type": {"title": "Error Type", "type": "string"}
                            },
                            "required": ["loc", "msg", "type"]
                        }
                    }
                }
            }
        }
        # Resolve references if Pydantic v1 style schema() was used.
        # For Pydantic v2, schema() is generally self-contained for simple models.
        # If $defs or definitions are present, they should be moved to components/schemas.

        final_schemas = {}
        for name, schema_def in schemas.items():
            if "$defs" in schema_def: # Pydantic v2 uses $defs
                for def_name, def_content in schema_def["$defs"].items():
                    final_schemas[def_name] = def_content
                del schema_def["$defs"] # Remove from original place
                final_schemas[name] = schema_def
            elif "definitions" in schema_def: # Pydantic v1 compatibility
                 for def_name, def_content in schema_def["definitions"].items():
                    final_schemas[def_name] = def_content
                 del schema_def["definitions"]
                 final_schemas[name] = schema_def
            else:
                final_schemas[name] = schema_def
        return final_schemas

    def generate_spec(self) -> Dict[str, Any]:
        """Genera la especificación OpenAPI completa para los endpoints MDU."""

        # Manually define paths as introspecting from self.mdu_app can be complex
        # or if routes are not yet fully initialized when spec is generated.
        # Paths should match what's defined in mdu_api_server.py PresentationFace.

        mdu_api_paths = {
            "/mdu/analyze": {
                "post": {
                    "summary": "Iniciar un nuevo análisis MDU",
                    "operationId": "mduExecuteAnalysis",
                    "tags": ["MDU Analysis Operations"],
                    "requestBody": {
                        "description": "Parámetros para la solicitud de análisis MDU.",
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MDUAnalisisRequest"}}}
                    },
                    "responses": {
                        "200": {"description": "Análisis MDU iniciado exitosamente.",
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MDUAnalisisResponse"}}}},
                        "400": {"description": "Solicitud inválida.",
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/HTTPValidationError"}}}},
                        "401": {"description": "No autorizado (token inválido o faltante)."}
                    },
                    "security": [{"mduBearerAuth": []}] # Reference security scheme
                }
            },
            "/mdu/status/{session_id}": {
                "get": {
                    "summary": "Obtener el estado de un análisis MDU",
                    "operationId": "mduGetAnalysisStatus",
                    "tags": ["MDU Analysis Operations"],
                    "parameters": [{
                        "name": "session_id", "in": "path", "required": True,
                        "description": "ID de la sesión del análisis MDU a consultar.",
                        "schema": {"type": "string", "example": "mdu_session_456"}
                    }],
                    "responses": {
                        "200": {"description": "Estado actual del análisis MDU.",
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MDUAnalysisStatusResponse"}}}},
                        "401": {"description": "No autorizado."},
                        "404": {"description": "Análisis no encontrado."}
                    },
                    "security": [{"mduBearerAuth": []}]
                }
            },
            "/mdu/token": {
                "post": {
                    "summary": "Obtener un token de acceso JWT para la API MDU",
                    "operationId": "mduRequestAccessToken",
                    "tags": ["MDU Authentication"],
                    "requestBody": {
                        "description": "Credenciales de usuario (formato x-www-form-urlencoded).",
                        "required": True,
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "username": {"type": "string", "example": "mdu_user"},
                                        "password": {"type": "string", "format": "password", "example":"mdu_pass"}
                                    },
                                    "required": ["username", "password"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Token de acceso generado.",
                                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MDUTokenResponse"}}}},
                        "400": {"description": "Credenciales incorrectas o solicitud malformada."}
                    }
                }
            }
            # Add /health endpoint if it's part of MDU API router and not a global one
        }

        return {
            "openapi": "3.0.3",
            "info": {
                "title": "MDU Cube - Domain Specific API",
                "version": self.app_version,
                "description": "API específica para las funcionalidades del MDU Cube System.",
                "contact": {"name": "MDU Cube API Team", "email": "mdu-api-dev@example.com"}
            },
            "servers": [ # Example server, should be configurable
                {"url": "/api/v1", "description": "Servidor principal de Aletheia (MDU API montada aquí)"}
            ],
            "paths": mdu_api_paths,
            "components": {
                "schemas": self._get_mdu_schemas(),
                "securitySchemes": {
                    "mduBearerAuth": { # Specific name for MDU auth
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "Autenticación JWT para los endpoints MDU. Obtener token de `/mdu/token`."
                    }
                }
            },
            "tags": [
                {"name": "MDU Analysis Operations", "description": "Endpoints para ejecutar y monitorear análisis MDU."},
                {"name": "MDU Authentication", "description": "Endpoints para la autenticación específica de MDU."}
            ]
        }
