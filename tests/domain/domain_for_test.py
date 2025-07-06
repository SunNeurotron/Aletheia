"""
Temporary location for domain models to make them accessible to tests
in this sandboxed environment. In a real project structure, these would be
in aletheia.domain.models.
"""
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional # Added Optional

from pydantic import BaseModel, Field


class ConceptType(str, Enum):
    """Enumeration of the types of scientific concepts."""
    SUBSTANCE = "SUBSTANCE"
    MECHANISM = "MECHANISM"
    PHENOMENON = "PHENOMENON"
    HYPOTHESIS = "HYPOTHESIS"
    EVIDENCE_UNIT = "EVIDENCE_UNIT" # Renamed from EVIDENCE to avoid clash with Evidence model
    UCM = "UCM" # Unit Conceptual Mínima
    CLUSTER = "CLUSTER" # Cluster Conceptual
    PROPOSITION = "PROPOSITION" # Proposición Emergente


class Evidence(BaseModel):
    """
    Represents a piece of evidence extracted from a source document.

    Attributes:
        source_doi: The Digital Object Identifier of the source document.
        source_citation: A human-readable citation for the source.
        snippet: The exact text snippet from the source providing the evidence.
        confidence: The system's confidence in the extraction (0.0 to 1.0).
    """
    source_doi: str
    source_citation: str
    snippet: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ScientificConcept(BaseModel):
    """
    Represents a Unit Conceptual Mínima (UCM) or a synthesized concept.

    Represents a Unit Conceptual Mínima (UCM) or a synthesized concept.

    This is the core building block of the knowledge graph.

    Attributes:
        id: Unique identifier for the concept.
        name: Human-readable name of the concept.
        description: Detailed description of the concept.
        type: The ConceptType enumeration.
        properties: A dictionary for storing arbitrary key-value pairs.
        evidence_sources: A list of Evidence objects supporting this concept.

    Equations:
        The relevance of a concept `C` can be modeled as a function of its
        centrality `deg(C)` and the aggregated confidence of its evidence `E`.
        R(C) = '\\alpha \\cdot \\text{deg}(C) + \\beta \\cdot \\sum_{i \\in E_C} \\text{conf}(i)'

    References:
        [1] A foundational paper on knowledge representation.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    description: str
    type: ConceptType
    properties: Dict[str, Any] = Field(default_factory=dict)
    evidence_sources: List[Evidence] = Field(default_factory=list)
    # Fields for Eje Y
    verification_hash: Optional[str] = None
    member_concept_ids: Optional[List[uuid.UUID]] = None # For CLUSTER type
    derived_from_cluster_id: Optional[uuid.UUID] = None # For PROPOSITION derived from a cluster
    derived_from_ucm_ids: Optional[List[uuid.UUID]] = None # For PROPOSITION derived from UCMs

    model_config = {"frozen": True} # Domain models should be immutable


class RelationshipType(str, Enum):
    """Enumeration of relationship types between scientific concepts."""
    CAUSES = "CAUSES"
    INHIBITS = "INHIBITS"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    SUBCLASS_OF = "SUBCLASS_OF"
    PART_OF = "PART_OF"


class DirectedRelationship(BaseModel):
    """
    Represents a directed, typed relationship between two scientific concepts.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_concept_id: uuid.UUID
    target_concept_id: uuid.UUID
    type: RelationshipType
    description: str
    weight: float = Field(default=1.0, ge=0.0)
    evidence_sources: List[Evidence] = Field(default_factory=list)

    model_config = {"frozen": True}
