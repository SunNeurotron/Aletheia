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


# --- Health Check Schema ---
class HealthCheckResponse(BaseModel):
    status: str = "OK"
    message: str = "API is healthy"
    version: Optional[str] = None  # Could be dynamically populated
    timestamp: datetime = Field(default_factory=datetime.utcnow)


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


# --- Schemas para Eje X (Ingesta y Ontología) y Eje Y (Síntesis de Conocimiento) ---

# Schemas para ExtractUCMsUseCase
class UCMExtractionRequestSchema(BaseModel):
    """Schema de entrada para la extracción de Unidades Conceptuales Mínimas (UCMs)."""
    text_content: str = Field(..., description="El contenido textual completo del documento a procesar.")
    source_document_id: str = Field(..., description="ID del concepto ScientificConcept (DOCUMENT_SOURCE) que representa al documento fuente.")
    source_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadatos adicionales sobre la fuente o el proceso de extracción.")

class ExtractedUCMSchema(BaseModel):
    """Schema para una Unidad Conceptual Mínima (UCM) extraída."""
    id: str = Field(..., description="ID único de la UCM.")
    name: str = Field(..., description="Nombre o etiqueta principal de la UCM.")
    description: Optional[str] = Field(None, description="Descripción detallada de la UCM.")
    concept_type: str = Field(..., description="Tipo de concepto (ej. 'GENERIC_CONCEPT', 'METHODOLOGY').")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos asociados a la UCM.")

class ExtractedRelationshipSchema(BaseModel):
    """Schema para una relación extraída entre UCMs."""
    id: str = Field(..., description="ID único de la relación.")
    source_ucm_id: str = Field(..., description="ID de la UCM origen.")
    target_ucm_id: str = Field(..., description="ID de la UCM destino.")
    type: str = Field(..., description="Tipo de relación (ej. 'RELATES_TO', 'USES_METHOD').")
    description: Optional[str] = Field(None, description="Descripción de la relación.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos asociados a la relación.")

class UCMExtractionResponseSchema(BaseModel):
    """Schema de respuesta para la extracción de UCMs."""
    source_document_id: str = Field(..., description="ID del documento fuente procesado.")
    extracted_concepts: List[ExtractedUCMSchema] = Field(default_factory=list, description="Lista de UCMs extraídas.")
    extracted_relationships: List[ExtractedRelationshipSchema] = Field(default_factory=list, description="Lista de relaciones extraídas entre UCMs.")
    processing_log: List[str] = Field(default_factory=list, description="Registro del proceso de extracción.")

# Schemas para IngestDocumentUseCase
class IngestDocumentRequest(BaseModel):
    """Schema de solicitud para la ingesta de un documento."""
    document_text: str = Field(..., description="El contenido textual completo del documento.")
    source_doi: Optional[str] = Field(None, description="DOI del documento fuente.")
    source_citation: Optional[str] = Field(None, description="Citación bibliográfica del documento fuente.")
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales sobre el documento fuente (autor, año, etc.).")

class IngestDocumentResponse(BaseModel):
    """Schema de respuesta para la ingesta de un documento."""
    document_source_id: str = Field(..., description="ID del concepto ScientificConcept (DOCUMENT_SOURCE) creado para el documento.")
    ucm_extraction_result: UCMExtractionResponseSchema = Field(..., description="Resultado de la extracción de UCMs del documento.")

# Schemas para LinkConceptsUseCase
class LinkConceptsRequest(BaseModel):
    """Schema de solicitud para vincular dos conceptos."""
    source_concept_id: str = Field(..., description="ID del concepto de origen.")
    target_concept_id: str = Field(..., description="ID del concepto de destino.")
    relationship_type: str = Field(..., description="Tipo de la relación (ej. 'CAUSES', 'REFERENCES', 'USES').")
    description: Optional[str] = Field(None, description="Descripción opcional de la relación.")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Propiedades adicionales de la relación.")

class RelationshipSchema(BaseModel):
    """Schema para representar una relación dirigida entre conceptos."""
    id: str = Field(..., description="ID único de la relación.")
    source_concept_id: str = Field(..., description="ID del concepto origen.")
    target_concept_id: str = Field(..., description="ID del concepto destino.")
    type: str = Field(..., description="Tipo de relación.")
    description: Optional[str] = Field(None, description="Descripción de la relación.")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Propiedades de la relación.")
    created_at: datetime = Field(..., description="Fecha y hora de creación de la relación.")

class LinkConceptsResponse(BaseModel):
    """Schema de respuesta para la vinculación de conceptos."""
    created_relationship: RelationshipSchema = Field(..., description="La relación que fue creada y guardada.")

# --- Schema para ScientificConcept (usado en listados, etc.) ---
# from ..core.domain_models import ConceptType # Importar si se quiere usar el Enum directamente

class ScientificConceptSchema(BaseModel):
    """Schema para representar un concepto científico en respuestas de API."""
    id: str = Field(..., description="ID único del concepto.")
    name: str = Field(..., description="Nombre o etiqueta del concepto.")
    description: Optional[str] = Field(None, description="Descripción detallada del concepto.")
    concept_type: str = Field(..., description="Tipo de concepto (valor del Enum ConceptType).")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Metadatos y propiedades adicionales.")
    created_at: datetime = Field(..., description="Fecha y hora de creación.")
    updated_at: datetime = Field(..., description="Fecha y hora de última actualización.")

    class Config:
        orm_mode = True # Para permitir la creación desde modelos ORM si es necesario en el futuro


# --- Schemas Placeholder para otros Casos de Uso del Eje Y (Refinados) ---

class ConceptInfoSchema(BaseModel):
    """Schema base para información resumida de un concepto científico."""
    id: str = Field(..., description="ID único del concepto.")
    name: str = Field(..., description="Nombre o etiqueta del concepto.")
    concept_type: str = Field(..., description="Tipo de concepto (valor del Enum ConceptType).")
    # Podríamos añadir 'description' si fuera breve y útil aquí.

class FormClusterInputSchema(BaseModel):
    """Schema de entrada para la formación de clústeres."""
    ucm_ids: List[str] = Field(..., description="Lista de IDs de UCMs (conceptos) para formar clústeres.")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parámetros adicionales para el algoritmo de clustering.")
class FormClusterResponseSchema(BaseModel): # Renombrado de Result a Response
    """Schema de respuesta para la formación de clústeres."""
    created_clusters: List[ConceptInfoSchema] = Field(default_factory=list, description="Lista de información de los clústeres creados.")
    message: Optional[str] = Field(None, description="Mensaje sobre el resultado del proceso.")

class PropositionDerivationInputSchema(BaseModel):
    """Schema de entrada para la derivación de proposiciones."""
    cluster_ids: List[str] = Field(..., description="Lista de IDs de clústeres a partir de los cuales derivar proposiciones.")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parámetros adicionales para la derivación.")
class PropositionDerivationResponseSchema(BaseModel): # Renombrado
    """Schema de respuesta para la derivación de proposiciones."""
    created_propositions: List[ConceptInfoSchema] = Field(default_factory=list, description="Lista de información de las proposiciones creadas.")
    message: Optional[str] = Field(None, description="Mensaje sobre el resultado del proceso.")

class MiniTheoryConstructionInputSchema(BaseModel):
    """Schema de entrada para la construcción de mini-teorías."""
    proposition_ids: List[str] = Field(..., description="Lista de IDs de proposiciones para construir una mini-teoría.")
    name: Optional[str] = Field(None, description="Nombre opcional para la mini-teoría a crear.")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parámetros adicionales.")
class MiniTheoryConstructionResponseSchema(BaseModel): # Renombrado
    """Schema de respuesta para la construcción de mini-teorías."""
    created_mini_theory: Optional[ConceptInfoSchema] = Field(None, description="Información de la mini-teoría creada.")
    message: Optional[str] = Field(None, description="Mensaje sobre el resultado del proceso.")

class ComprehensiveTheoriesInputSchema(BaseModel):
    """Schema de entrada para la construcción de teorías comprehensivas."""
    mini_theory_ids: List[str] = Field(..., description="Lista de IDs de mini-teorías a agregar.")
    name: Optional[str] = Field(None, description="Nombre opcional para la teoría comprehensiva.")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)
class ComprehensiveTheoriesResponseSchema(BaseModel): # Renombrado
    """Schema de respuesta para la construcción de teorías comprehensivas."""
    created_comprehensive_theory: Optional[ConceptInfoSchema] = Field(None, description="Información de la teoría comprehensiva creada.")
    message: Optional[str] = Field(None, description="Mensaje sobre el resultado del proceso.")

class UnifiedModelsInputSchema(BaseModel):
    """Schema de entrada para la síntesis de modelos unificados."""
    comprehensive_theory_ids: List[str] = Field(..., description="Lista de IDs de teorías comprehensivas a unificar.")
    name: Optional[str] = Field(None, description="Nombre opcional para el modelo unificado.")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)
class UnifiedModelsResponseSchema(BaseModel): # Renombrado
    """Schema de respuesta para la síntesis de modelos unificados."""
    created_unified_model: Optional[ConceptInfoSchema] = Field(None, description="Información del modelo unificado creado.")
    message: Optional[str] = Field(None, description="Mensaje sobre el resultado del proceso.")


# --- Schemas para Endpoints de Visualización del Eje Y ---

class HierarchyGraphNodeSchema(BaseModel):
    """Schema para un nodo en un grafo de jerarquía."""
    id: str = Field(..., description="ID del concepto/nodo.")
    label: str = Field(..., description="Etiqueta visible del nodo.")
    title: Optional[str] = Field(None, description="Tooltip o información adicional al pasar el mouse.")
    type: str = Field(..., description="Tipo de concepto (ej. UNIFIED_MODEL, CLUSTER).")
    level: Optional[int] = Field(None, description="Nivel en la jerarquía para el layout.")

class HierarchyGraphEdgeSchema(BaseModel):
    """Schema para una arista en un grafo de jerarquía."""
    from_node: str = Field(..., alias="from", description="ID del nodo origen.")
    to_node: str = Field(..., alias="to", description="ID del nodo destino.")
    label: Optional[str] = Field(None, description="Etiqueta opcional para la arista.")

class HierarchyGraphResponseSchema(BaseModel):
    """Schema de respuesta para el grafo de jerarquía de un concepto."""
    nodes: List[HierarchyGraphNodeSchema] = Field(default_factory=list)
    edges: List[HierarchyGraphEdgeSchema] = Field(default_factory=list)

class SynthesisStatisticItemSchema(BaseModel):
    """Schema para un item individual de estadística."""
    name: str = Field(..., description="Nombre de la métrica o estadística.")
    value: Any = Field(..., description="Valor de la métrica.")
    unit: Optional[str] = Field(None, description="Unidad de la métrica, si aplica.")

class SynthesisStatisticsResponseSchema(BaseModel):
    """Schema de respuesta para las estadísticas de síntesis del grafo de conocimiento."""
    overall_stats: List[SynthesisStatisticItemSchema] = Field(default_factory=list, description="Estadísticas generales.")
    type_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribución de conceptos por tipo.")
    # Se podrían añadir más campos estructurados para otras estadísticas.
