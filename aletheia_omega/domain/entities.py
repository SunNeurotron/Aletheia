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

# aletheia_omega/domain/entities.py

import uuid
import enum # Necesario para TrajectoryState
from dataclasses import dataclass, field
from typing import Any, List, Optional # Tuple ya no es necesario, Optional sí por si acaso

from pydantic import BaseModel, Field as PydanticField


class ModelRepresentation(BaseModel):
    """
    Representa un modelo algorítmicamente descriptible (M) del espacio M_S.
    Su contenido puede ser cualquier objeto serializable que represente el modelo.
    """
    identifier: str = PydanticField(
        ..., description="Un identificador único para el modelo, ej: 'Polynomial_Deg3'."
    )
    content: bytes = PydanticField(
        ..., description="La representación serializada del modelo (ej. pickle, JSON)."
    )

    class Config:
        frozen = True


class ModelMetrics(BaseModel):
    """
    Almacena las métricas calculadas para un único modelo, incluyendo el coste MDL.
    """
    complexity: float = PydanticField(..., description="Proxy de la Complejidad de Kolmogorov, K(M).")
    log_likelihood: float = PydanticField(..., description="Log-verosimilitud del modelo dados los datos, L(D|M).")
    mdl_cost: float = PydanticField(..., description="Coste total según el Principio de Mínima Descripción (MDL).")

    class Config:
        frozen = True


class OptimizationResult(BaseModel):
    """
    Encapsula el resultado de una ejecución del FindOptimalModelUseCase.
    """
    best_model: ModelRepresentation
    best_model_metrics: ModelMetrics
    search_space_size: int
    parameters: dict[str, Any]


# --- Entidades para la Fase 2: Trayectorias ---

class TrajectoryState(str, enum.Enum):
    """Clasificación dinámica de una trayectoria según el Axioma 3."""
    STATIONARY = "Estacionaria"
    OSCILLATORY = "Oscilatoria"
    PROGRESSIVE = "Progresiva"
    UNDEFINED = "Indefinida" # Para trayectorias demasiado cortas para analizar

@dataclass
class TrajectoryStep:
    """Representa un único paso (un modelo M*ᵢ) en la trayectoria."""
    step_index: int
    model: ModelRepresentation # El modelo óptimo para este paso
    metrics: ModelMetrics      # Las métricas de ese modelo en este paso
    # Podríamos añadir aquí el run_id del OptimizationRunDB si fuera necesario
    # para trazarlo directamente al registro de BD, aunque el repositorio lo manejará.

@dataclass
class Trajectory:
    """Representa la trayectoria completa de modelos Θ."""
    id: uuid.UUID # ID único de la trayectoria
    name: str     # Un nombre descriptivo opcional para la trayectoria
    steps: List[TrajectoryStep] = field(default_factory=list)
    # Podríamos añadir metadata adicional como fecha de creación, descripción, etc.

    def add_step(self, model: ModelRepresentation, metrics: ModelMetrics) -> TrajectoryStep:
        """Añade un nuevo paso a la trayectoria y lo devuelve."""
        new_step_index = len(self.steps)
        new_step = TrajectoryStep(
            step_index=new_step_index,
            model=model,
            metrics=metrics
        )
        self.steps.append(new_step)
        return new_step

@dataclass(frozen=True) # frozen=True porque es un resultado de análisis inmutable
class TrajectoryAnalysis:
    """El resultado del análisis de una trayectoria."""
    trajectory_id: uuid.UUID
    state: TrajectoryState
    comment: str
    step_count: int
    # Podríamos añadir más detalles del análisis, como las métricas que llevaron a la clasificación.
