from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

# --- Schemas para Autenticación ---
# Reutilizando la estructura general, podrían estar en aletheia_common si son idénticos
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    # scopes: List[str] = [] # Si se usan scopes/roles en el token

# --- Schemas para T-Test ---

class TTestInputData(BaseModel):
    group_a_data: List[float] = Field(..., min_items=3, description="Data for group A, minimum 3 data points.")
    group_b_data: List[float] = Field(..., min_items=3, description="Data for group B, minimum 3 data points.")
    alpha: float = Field(0.05, gt=0, lt=1, description="Significance level for the t-test.")

class TTestRequest(TTestInputData):
    experiment_name: Optional[str] = Field(None, description="Name for the experiment.")
    experiment_description: Optional[str] = Field(None, description="Description for the experiment.")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional parameters to log.")


class TTestResultSchema(BaseModel):
    statistic: float
    p_value: float
    degrees_freedom: float
    mean_group_a: float
    variance_group_a: float
    mean_group_b: float
    variance_group_b: float
    confidence_interval_95: List[float]
    is_significant_05: bool
    normality_p_value_group_a: Optional[float] = None
    normality_p_value_group_b: Optional[float] = None
    comment: Optional[str] = None

    class Config:
        orm_mode = True


class ExperimentResponse(BaseModel):
    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    group_a_data_summary: Dict[str, Any] # e.g., {"count": len, "mean": np.mean(data)} - Simplificado aquí
    group_b_data_summary: Dict[str, Any] # Para no devolver toda la data en cada listado
    parameters: Optional[Dict[str, Any]] = None
    result: Optional[TTestResultSchema] = None # Puede ser None si el experimento aún no se ha procesado
    mlflow_run_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PaginatedExperimentResponse(BaseModel):
    total: int
    items: List[ExperimentResponse]

# --- Schema para Usuario ---
# Similar a aletheia_common.auth.UserAuth, pero definido aquí para independencia si es necesario
# o podría importarse directamente si aletheia_common es una dependencia instalable.
class UserSchema(BaseModel):
    username: str
    roles: List[str] = []
    # email: Optional[str] = None # Ajustar según lo que devuelva get_current_active_user
    # full_name: Optional[str] = None

    class Config:
        orm_mode = True

# --- Schema para Health Check ---
class HealthCheckResponse(BaseModel):
    status: str = "OK"
    module: str = "Aletheia-Stats"
    version: Optional[str] = None # Podría leerse de una variable de entorno o un archivo
