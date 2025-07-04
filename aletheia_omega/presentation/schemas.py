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

# aletheia_omega/presentation/schemas.py

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Any, Dict, Optional
import uuid

# Ajustando la importación para que sea relativa al directorio 'aletheia_omega'
from ..domain.entities import (
    ModelRepresentation,
    ModelMetrics,
    TrajectoryState,      # Nueva entidad de dominio
    TrajectoryStep,       # Nueva entidad de dominio (usada para TrajectoryStepSchema)
    TrajectoryAnalysis    # Nueva entidad de dominio (usada para TrajectoryAnalysisResponse)
)


# --- Schemas para Optimización de Modelo Individual (existentes) ---

class OptimizationRequest(BaseModel):
    lambda_param: float = Field(..., gt=0, description="Parámetro de regularización λ (lambda).")
    candidate_models: List[ModelRepresentation] = Field(..., min_length=1, description="Lista de modelos a evaluar.") # min_items -> min_length
    data_context: Dict[str, Any] = Field(..., description="Contexto de datos (serializable) para la evaluación.")
    optimization_parameters: Optional[Dict[str, Any]] = Field(default=None, description="Parámetros adicionales de la optimización.")

    model_config = ConfigDict(frozen=False, extra='forbid')


class OptimizationResultResponse(BaseModel):
    run_id: uuid.UUID # El ID del OptimizationRunDB creado para este paso/optimización
    status: str
    best_model: ModelRepresentation
    best_model_metrics: ModelMetrics
    search_space_size: int
    lambda_param_used: float
    optimization_parameters_stored: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# --- Schemas para Trayectorias (Fase 2) ---

class TrajectoryCreationRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255, description="Nombre descriptivo opcional para la trayectoria.")
    # Podríamos añadir parámetros iniciales para la trayectoria aquí si fuera necesario

    model_config = ConfigDict(extra='forbid')


class TrajectoryStepSchema(BaseModel):
    """Schema para representar un paso de la trayectoria en la API."""
    step_index: int
    model: ModelRepresentation
    metrics: ModelMetrics
    # Podríamos añadir el run_id (id del OptimizationRunDB) aquí si el cliente lo necesita.
    # optimization_run_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True) # Para mapear desde el dataclass TrajectoryStep


class TrajectoryResponse(BaseModel):
    """Schema para devolver información de una trayectoria, incluyendo sus pasos."""
    id: uuid.UUID
    name: Optional[str] = None
    created_at: datetime
    steps: List[TrajectoryStepSchema] = []

    model_config = ConfigDict(from_attributes=True) # Para mapear desde TrajectoryDB o Trajectory (dominio)


class EvolveTrajectoryRequest(BaseModel):
    """Schema para la petición de evolucionar una trayectoria."""
    # Los mismos parámetros que OptimizationRequest, ya que se usará FindOptimalModelUseCase
    lambda_param: float = Field(..., gt=0, description="Parámetro de regularización λ para este paso.")
    candidate_models: List[ModelRepresentation] = Field(..., min_length=1, description="Lista de modelos candidatos para este paso.")
    data_context: Dict[str, Any] = Field(..., description="Contexto de datos para este paso.")
    optimization_parameters: Optional[Dict[str, Any]] = Field(default=None, description="Parámetros adicionales para la optimización de este paso.")
    # El trajectory_id vendrá de la URL del path

    model_config = ConfigDict(extra='forbid')

# La respuesta a EvolveTrajectory podría ser la TrajectoryResponse completa actualizada
# o solo el TrajectoryStepSchema del nuevo paso añadido.
# Por consistencia con EvolveTrajectoryUseCase que devuelve la Trajectory actualizada:
# Usaremos TrajectoryResponse como respuesta para la evolución.


class TrajectoryAnalysisResponse(BaseModel):
    """Schema para devolver el resultado del análisis de una trayectoria."""
    trajectory_id: uuid.UUID
    state: TrajectoryState # El enum del dominio se puede usar directamente
    comment: str
    step_count: int

    model_config = ConfigDict(from_attributes=True) # Para mapear desde el dataclass TrajectoryAnalysis


# Schemas de utilidad que fueron eliminados o no son necesarios para las nuevas funcionalidades:
# OptimizationRunCreationResponse y OptimizationRunStatusResponse podrían ser útiles
# si la optimización/evolución fuera una tarea asíncrona de larga duración.
# Por ahora, los endpoints son síncronos.
# class OptimizationRunCreationResponse(BaseModel):
#     run_id: uuid.UUID
#     status: str
#     message: str

# class OptimizationRunStatusResponse(BaseModel):
#     run_id: uuid.UUID
#     status: str
#     created_at: datetime
#     completed_at: Optional[datetime] = None
#     best_model_identifier: Optional[str] = None
#     best_model_mdl_cost: Optional[float] = None
#     model_config = ConfigDict(from_attributes=True)
