# Copyright 2025 Alant
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# import os
# import logging
# from fastapi import FastAPI
# import uvicorn

# # Import the API router from the presentation layer
# from .presentation.api import api_router as module_api_router
# # from .presentation.dependencies import configure_dependencies # If you have a DI setup function

# # --- Logging Configuration ---
# # LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
# # logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# # logger = logging.getLogger(__name__)

# # --- FastAPI Application Instantiation ---
# app = FastAPI(
#     title="[Module Name] API",
#     version="0.1.0", # os.getenv("MODULE_API_VERSION", "0.1.0"),
#     description="API for [Module Name] module, part of Aletheia ecosystem.",
#     # openapi_url="/module_api_v1/openapi.json", # Ensure prefix matches router
#     # docs_url="/docs", # Or prefix with module name if served standalone
#     # redoc_url="/redoc"
# )

# # --- CORS Middleware (if applicable) ---
# # from fastapi.middleware.cors import CORSMiddleware
# # origins = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=origins,
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # --- Event Handlers (Startup and Shutdown) ---
# @app.on_event("startup")
# async def startup_event():
#     # logger.info("[Module Name] API application startup...")
#     # configure_dependencies(app) # Example: If you have a DI setup function
#     # logger.info("[Module Name] API startup complete.")
#     pass

# @app.on_event("shutdown")
# async def shutdown_event():
#     # logger.info("[Module Name] API application shutting down...")
#     pass

# # --- Include API Routers ---
# # The router prefix in api.py is "/module_api_v1"
# # If this main.py serves ONLY this module, you can include router at root "/"
# # or keep the prefix if it's intended to be path-based under a larger gateway.
# app.include_router(module_api_router) # Default prefix from api_router will be used
# # Or: app.include_router(module_api_router, prefix="/specific_mount_for_module")


# # --- Root Endpoint (Optional) ---
# @app.get("/")
# async def read_root_module():
#     return {
#         "message": "Welcome to [Module Name] API",
#         "version": app.version,
#         # "docs_url": app.docs_url # if served standalone
#     }

# # --- Main execution (for running with uvicorn directly) ---
# # if __name__ == "__main__":
#     # MODULE_API_HOST = os.getenv("MODULE_API_HOST", "0.0.0.0")
#     # MODULE_API_PORT = int(os.getenv("MODULE_API_PORT", "800X")) # Choose a unique port
#     # LOG_LEVEL_UVICORN = os.getenv("LOG_LEVEL_UVICORN", "info").lower()

#     # logger.info(f"Starting [Module Name] Uvicorn server on {MODULE_API_HOST}:{MODULE_API_PORT}")

#     # uvicorn.run(
#     #     "module_name.main:app", # Path to this app instance
#     #     host=MODULE_API_HOST,
#     #     port=MODULE_API_PORT,
#     #     log_level=LOG_LEVEL_UVICORN,
#     #     reload=True # For development
#     # )
# print("Placeholder for Module Main Application (FastAPI)")
