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

# Aletheia_v3/api/schemas.py
import uuid as uuid_pkg
from datetime import datetime
from typing import List, Optional, Dict, Any # Added Dict, Any

from pydantic import (  # Pydantic's EmailStr can be used for email validation
    BaseModel,
    Field,
    validator,
)

# Potentially import Enum types from models if needed for validation here,
# though often validation against string choices is done in endpoints or via Pydantic's Literal
# from infrastructure.models import ContributionTypeEnum, ConjectureStatusEnum


# --- Job Schemas ---


class HitBase(BaseModel):
    """Base schema for a 'hit' (an abc-triple with its quality)."""

    a: int = Field(
        ..., gt=0, description="The 'a' component of the abc-triple."
    )
    b: int = Field(
        ..., gt=0, description="The 'b' component of the abc-triple."
    )
    c: int = Field(
        ..., gt=0, description="The 'c' component (a+b) of the abc-triple."
    )
    quality: float = Field(
        ..., description="The calculated quality 'q' of the triple."
    )

    @validator("c")
    def c_must_be_a_plus_b(cls, v, values):
        # This validator is mostly for conceptual clarity in the schema,
        # as the actual calculation c=a+b happens in the domain logic.
        # However, if c were directly provided, this would be crucial.
        if "a" in values and "b" in values and v != values["a"] + values["b"]:
            # In our current flow, 'c' is derived, so this might not be strictly necessary
            # if the input to this schema already has 'c' correctly calculated.
            # If 'c' is also an input field, this validation is important.
            # For now, let's assume 'c' is correctly populated based on 'a' and 'b'.
            pass  # Or raise ValueError('c must be equal to a + b') if c is also an input field
        return v


class HitResponse(HitBase):
    """Schema for representing a hit when returning data from the API."""

    id: Optional[int] = Field(
        None,
        description="Unique ID of the hit in the database, if applicable.",
    )  # From HitDB
    discovered_at: Optional[datetime] = Field(
        None, description="Timestamp when the hit was discovered."
    )  # From HitDB

    class Config:
        orm_mode = True  # Allows Pydantic to work with SQLAlchemy models


class JobBase(BaseModel):
    """Base schema for a discovery job."""

    n_calls: int = Field(
        ...,
        gt=10,
        le=1000,
        description="Number of Bayesian optimization calls for the job (budget). Max 1000.",
    )
    # Max 1000 is an example, can be adjusted based on typical runtimes / resource limits.


class JobCreateRequest(JobBase):
    """Schema for creating a new discovery job."""

    pass  # Inherits n_calls from JobBase


class JobResponse(JobBase):
    """Schema for representing a job when returning data from the API."""

    id: str = Field(..., description="Unique ID of the job.")
    status: str = Field(
        ...,
        description="Current status of the job (e.g., pending, processing, completed, failed).",
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the job was created."
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp when the job was last updated."
    )
    hits: List[HitResponse] = Field(
        [], description="List of high-quality hits found by this job."
    )

    class Config:
        orm_mode = True  # Allows Pydantic to work with SQLAlchemy models


# --- Token Schemas (for Authentication) ---


class Token(BaseModel):
    """Schema for the JWT access token."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for data embedded within the JWT token (the 'sub' field)."""

    username: Optional[str] = None


# --- User Schemas (for Authentication examples) ---
# These are simplified for the example. In a real app, you might have more fields.


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = (
        None  # EmailStr can be used for validation: from pydantic import EmailStr
    )
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=8, description="User's password (will be hashed)."
    )


class UserResponse(UserBase):
    """Schema for returning user information (without password)."""

    disabled: Optional[bool] = None

    class Config:
        orm_mode = True


# --- Health Check Schema ---
class HealthCheckResponse(BaseModel):
    status: str = "OK"
    message: str = "API is healthy"
    version: Optional[str] = None  # Could be dynamically populated
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# --- Researcher Schemas ---
class ResearcherBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    email: str = Field(
        ..., max_length=255
    )  # Should use EmailStr for validation: from pydantic import EmailStr
    orcid: Optional[str] = Field(
        None, max_length=50, description="ORCID iD, e.g., 0000-0000-0000-0000"
    )


class ResearcherCreate(ResearcherBase):
    password: str = Field(
        ...,
        min_length=8,
        description="Researcher's password (will be hashed upon creation)",
    )


class ResearcherUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)  # Should use EmailStr
    orcid: Optional[str] = Field(None, max_length=50)
    # Password updates would typically be handled by a separate endpoint/schema


class ResearcherResponse(ResearcherBase):
    id: uuid_pkg.UUID  # Using uuid directly from uuid_pkg for response
    created_at: datetime
    updated_at: datetime
    # submitted_jobs_count: Optional[int] = None # Example derived field
    # proposed_conjectures_count: Optional[int] = None # Example derived field

    class Config:
        orm_mode = True


# --- Discovery Attribution Schemas ---
class AttributionBase(BaseModel):
    hit_id: int = Field(
        ..., description="ID of the discovery hit being attributed."
    )
    researcher_id: uuid_pkg.UUID = Field(
        ..., description="ID of the researcher making the attribution."
    )
    contribution_type: str  # Should match ContributionTypeEnum values, validated by Enum in model or here
    details: Optional[str] = None


class AttributionCreate(AttributionBase):
    pass


class AttributionResponse(AttributionBase):
    id: int
    attributed_at: datetime
    researcher: Optional[ResearcherResponse] = (
        None  # Optionally nest researcher info
    )

    class Config:
        orm_mode = True


from pydantic import computed_field  # Import for Pydantic v2 computed_field


# --- Derived Conjecture Schemas ---
class ConjectureBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: str = Field(
        ...,
        min_length=20,
        description="Detailed description of the conjecture (can include LaTeX/Markdown).",
    )
    # status: Optional[str] = ConjectureStatusEnum.PROPOSED # Default set in model
    # proposer_id: Optional[uuid_pkg.UUID] = None # Set based on authenticated user usually


class ConjectureCreate(ConjectureBase):
    # proposer_id will be set from the authenticated user in the endpoint logic
    supporting_hit_ids: Optional[List[int]] = Field(
        [], description="List of HitDB IDs that support this conjecture."
    )


class ConjectureUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=500)
    description: Optional[str] = Field(None, min_length=20)
    status: Optional[str] = (
        None  # Validate against ConjectureStatusEnum values
    )
    supporting_hit_ids: Optional[List[int]] = Field(
        None, description="Replace existing list of supporting HitDB IDs."
    )


class ConjectureResponse(ConjectureBase):
    id: int
    proposer_id: uuid_pkg.UUID
    status: str  # From ConjectureStatusEnum
    created_at: datetime
    updated_at: datetime
    proposer: Optional[ResearcherResponse] = (
        None  # Optionally nest proposer info
    )
    # supporting_hits_count: Optional[int] = None # Replaced by computed_field
    # supporting_hits: List[HitResponse] = [] # Could also return full hit objects

    @computed_field
    @property
    def supporting_hits_count(self) -> int:
        # This assumes that when model_validate is called with a DerivedConjectureDB instance,
        # its 'supporting_hits' relationship is already loaded or can be loaded.
        # If 'supporting_hits' is a SQLAlchemy InstrumentedList, len() will trigger a load if not already loaded.
        # This might lead to N+1 queries if not handled carefully with eager loading in the endpoint.
        # However, for a single object, it's often acceptable.
        if (
            hasattr(self, "supporting_hits")
            and self.supporting_hits is not None
        ):
            return len(self.supporting_hits)
        return 0

    class Config:
        orm_mode = True
        # from_attributes = True # Alias for orm_mode in Pydantic v2, but orm_mode is still supported


# --- MDU Cube Specific Schemas ---

class AnalisisRequest(BaseModel):
    """Modelo de entrada validado para las solicitudes de análisis del Cubo MDU."""
    sesion_id: str = Field(..., example="mdu_session_456", description="Identificador único de la sesión de análisis MDU.")
    tipo_analisis: str = Field(..., example="multidimensional_exhaustive", description="Tipo de análisis MDU a realizar.")
    parametros: Dict[str, Any] = Field(..., example={"target_variable": "sales", "dimensions": ["time", "region"]}, description="Parámetros específicos para el tipo de análisis MDU.")
    nivel_profundidad: int = Field(default=3, example=3, ge=1, le=5, description="Nivel de profundidad del análisis MDU (1-5).")

class MDUAnalisisResponse(BaseModel): # Renamed to avoid conflict if a generic AnalisisResponse exists
    """Respuesta estándar para una solicitud de análisis MDU iniciada."""
    analysis_id: str = Field(..., example="mdu_analysis_ जीव_789", description="ID único del análisis MDU iniciado.") # Example with non-ascii
    status_message: str = Field(..., example="MDU Analysis successfully submitted and processing started.", description="Mensaje de estado.")
    estimated_completion_time: Optional[str] = Field(None, example="Approx. 15 minutes", description="Tiempo estimado de finalización para el análisis MDU.")
    details_url: Optional[str] = Field(None, example="/api/v1/mdu/status/mdu_analysis_ जीव_789", description="URL para consultar el estado del análisis MDU.")

class MDUAnalysisStatusResponse(BaseModel): # Renamed
    """Respuesta para el estado de un análisis MDU."""
    session_id: str = Field(..., description="ID de la sesión del análisis MDU.")
    current_status: str = Field(..., example="ROTATING_CUBE_PERSPECTIVE_TEMPORAL", description="Estado actual del análisis MDU.")
    progress_percent: float = Field(..., example=42.0, ge=0, le=100, description="Porcentaje de progreso del análisis MDU.")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales sobre el estado o resultados parciales.")
