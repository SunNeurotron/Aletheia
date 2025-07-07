from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import datetime

# Asumiendo la necesidad de importar algunas entidades de dominio para los resultados,
# o al menos sus tipos para referencia.
# from ..core.domain_models import ScientificConcept, DirectedRelationship
# Por ahora, si un DTO debe devolver una entidad de dominio, usaré Any o un Pydantic model específico.

# --- DTOs para ExtractUCMsUseCase (Asumidos/Requeridos por IngestDocumentUseCase) ---

class UCMExtractionInput(BaseModel):
    """DTO de entrada para ExtractUCMsUseCase."""
    text_content: str = Field(..., description="El contenido textual completo del documento a procesar.")
    source_document_id: str = Field(..., description="ID del concepto ScientificConcept (DOCUMENT_SOURCE) que representa al documento fuente.")
    source_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadatos adicionales sobre la fuente o el proceso de extracción.")

class ExtractedUCMDTO(BaseModel): # DTO para representar un UCM extraído, podría ser similar a ScientificConcept
    id: str
    name: str
    description: Optional[str] = None
    concept_type: str # e.g., "GENERIC_CONCEPT", "METHODOLOGY", etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExtractedRelationshipDTO(BaseModel): # DTO para una relación extraída
    id: str
    source_ucm_id: str
    target_ucm_id: str
    type: str # e.g., "RELATES_TO", "USES_METHOD"
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UCMExtractionResult(BaseModel):
    """DTO de resultado para ExtractUCMsUseCase."""
    source_document_id: str
    extracted_concepts: List[ExtractedUCMDTO] = Field(default_factory=list)
    extracted_relationships: List[ExtractedRelationshipDTO] = Field(default_factory=list)
    processing_log: List[str] = Field(default_factory=list)


# --- DTOs para IngestDocumentUseCase ---

class IngestDocumentInput(BaseModel):
    """DTO de entrada para IngestDocumentUseCase."""
    document_text: str = Field(..., description="El contenido textual completo del documento.")
    source_doi: Optional[str] = Field(None, description="DOI del documento fuente.")
    source_citation: Optional[str] = Field(None, description="Citación bibliográfica del documento fuente.")
    # Podríamos añadir más metadatos específicos de la fuente aquí si es necesario
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales sobre el documento fuente (autor, año, etc.).")

class IngestDocumentResult(BaseModel):
    """DTO de resultado para IngestDocumentUseCase."""
    document_source_id: str = Field(..., description="ID del concepto ScientificConcept (DOCUMENT_SOURCE) creado para el documento.")
    ucm_extraction_result: UCMExtractionResult = Field(..., description="Resultado de la extracción de UCMs del documento.")


# --- DTOs para LinkConceptsUseCase ---

class LinkConceptsInput(BaseModel):
    """DTO de entrada para LinkConceptsUseCase."""
    source_concept_id: str = Field(..., description="ID del concepto de origen.")
    target_concept_id: str = Field(..., description="ID del concepto de destino.")
    relationship_type: str = Field(..., description="Tipo de la relación (ej. 'CAUSES', 'REFERENCES', 'USES').")
    description: Optional[str] = Field(None, description="Descripción opcional de la relación.")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Propiedades adicionales de la relación.")
    # created_by: Optional[str] = None # Podría añadirse si se rastrea quién crea la relación
    # created_at: Optional[datetime.datetime] = Field(default_factory=datetime.datetime.utcnow) # Se manejaría en la entidad

class RelationshipDTO(BaseModel): # Para devolver la relación creada
    id: str
    source_concept_id: str
    target_concept_id: str
    type: str
    description: Optional[str] = None
    properties: Dict[str, Any]
    created_at: datetime.datetime
    # Podríamos añadir más campos si la entidad DirectedRelationship los tiene y son relevantes para el DTO

class LinkConceptsResult(BaseModel):
    """DTO de resultado para LinkConceptsUseCase."""
    created_relationship: RelationshipDTO = Field(..., description="La relación que fue creada y guardada.")

# Nota: Los DTOs UCMExtractionInput y UCMExtractionResult son definidos aquí basados en la necesidad
# del IngestDocumentUseCase. Si ExtractUCMsUseCase ya existe y usa otros DTOs, estos deberían
# alinearse o adaptarse. Por ahora, se definen como se usarían idealmente.
# Los DTOs ExtractedUCMDTO y ExtractedRelationshipDTO son para los resultados de UCMExtractionResult,
# podrían mapear directamente a ScientificConcept y DirectedRelationship o ser un subconjunto.
```
