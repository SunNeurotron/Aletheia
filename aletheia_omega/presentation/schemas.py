# aletheia_omega/presentation/schemas.py

from datetime import datetime # Movido al principio
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Any, Dict, Optional
import uuid

# Ajustando la importación para que sea relativa al directorio 'aletheia_omega'
from ..domain.entities import ModelRepresentation, ModelMetrics


class OptimizationRequest(BaseModel):
    lambda_param: float = Field(..., gt=0, description="Parámetro de regularización λ (lambda).")
    candidate_models: List[ModelRepresentation] = Field(..., min_items=1, description="Lista de modelos a evaluar.")
    # data_context podría ser cualquier JSON que el LikelihoodService específico sepa interpretar.
    # Ej: {"type": "csv_s3", "bucket": "mi-bucket", "key": "datos/mis_datos.csv"}
    # O: {"type": "inline_list", "X": [[1],[2]], "y": [0,1]}
    data_context: Dict[str, Any] = Field(..., description="Contexto de datos (serializable) para la evaluación. El formato específico depende de la implementación del LikelihoodService.")
    optimization_parameters: Optional[Dict[str, Any]] = Field(default=None, description="Parámetros adicionales de la optimización que se guardarán y podrían ser usados por extensiones futuras.")

    model_config = ConfigDict(frozen=False) # Permitir la asignación a model_config

class OptimizationRunCreationResponse(BaseModel):
    run_id: uuid.UUID
    status: str
    message: str

class OptimizationRunStatusResponse(BaseModel):
    run_id: uuid.UUID
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    best_model_identifier: Optional[str] = None
    best_model_mdl_cost: Optional[float] = None

    model_config = ConfigDict(from_attributes=True) # Cambiado orm_mode a from_attributes para Pydantic v2

class OptimizationResultResponse(BaseModel): # Este es el que coincide con tu OptimizationResponse
    run_id: uuid.UUID
    status: str # Generalmente "COMPLETED"
    best_model: ModelRepresentation
    best_model_metrics: ModelMetrics
    search_space_size: int
    lambda_param_used: float # Para confirmar qué lambda se usó
    optimization_parameters_stored: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# Para mantener la compatibilidad con tu definición original de OptimizationResponse,
# la he renombrado a OptimizationResultResponse y he añadido algunos campos que podrían ser útiles.
# Si prefieres la versión más simple, podemos usarla:
# class OptimizationResponse(BaseModel):
#     run_id: uuid.UUID
#     status: str
#     best_model: ModelRepresentation
#     best_model_metrics: ModelMetrics
#     search_space_size: int
#
#     model_config = ConfigDict(from_attributes=True) # Anteriormente orm_mode = True

# La importación de datetime ya se movió al principio.
