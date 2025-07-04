# aletheia_omega/domain/entities.py

import uuid
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

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
