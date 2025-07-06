"""
Temporary location for domain models to make them accessible to tests
in this sandboxed environment. In a real project structure, these would be
in aletheia.domain.models.
"""
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field


class ConceptType(str, Enum):
    """Enumeration of the types of scientific concepts."""
    SUBSTANCE = "SUBSTANCE"
    MECHANISM = "MECHANISM"
    PHENOMENON = "PHENOMENON"
    HYPOTHESIS = "HYPOTHESIS"
    EVIDENCE_UNIT = "EVIDENCE_UNIT"
    UCM = "UCM"
    CLUSTER = "CLUSTER"
    PROPOSITION = "PROPOSITION"
    MINI_THEORY = "MINI_THEORY"
    COMPREHENSIVE_THEORY = "COMPREHENSIVE_THEORY"
    UNIFIED_MODEL = "UNIFIED_MODEL"
    DOCUMENT_SOURCE = "DOCUMENT_SOURCE"


class TheoryIntegrationMethod(str, Enum):
    """Methods for integrating theories."""
    COMPLEMENTARY_SYNTHESIS = "COMPLEMENTARY_SYNTHESIS"
    DIALECTICAL_SYNTHESIS = "DIALECTICAL_SYNTHESIS"
    SUBSUMPTION = "SUBSUMPTION"
    PARALLEL_COEXISTENCE = "PARALLEL_COEXISTENCE"
    HIERARCHICAL_INTEGRATION = "HIERARCHICAL_INTEGRATION"


class ModelArchitectureType(str, Enum):
    """Types of unified model architectures."""
    MODULAR = "MODULAR"
    LAYERED = "LAYERED"
    NETWORKED = "NETWORKED"
    HIERARCHICAL = "HIERARCHICAL"
    HYBRID = "HYBRID"


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
    verification_hash: Optional[str] = None
    member_concept_ids: Optional[List[uuid.UUID]] = None
    derived_from_cluster_id: Optional[uuid.UUID] = None
    derived_from_ucm_ids: Optional[List[uuid.UUID]] = None

    model_config = {"frozen": True}


class RelationshipType(str, Enum):
    """Enumeration of relationship types between scientific concepts."""
    # General Semantic / Ontological
    IS_A = "IS_A"                        # Replaces SUBCLASS_OF for clarity, taxonomic (hypernymy/hyponymy)
    PART_OF = "PART_OF"                  # Meronymy/holonymy
    HAS_PROPERTY = "HAS_PROPERTY"        # e.g., Substance HAS_PROPERTY ColorRed
    DEFINES = "DEFINES"                  # e.g., Paper DEFINES TermX
    EXAMPLE_OF = "EXAMPLE_OF"            # e.g., Apple EXAMPLE_OF Fruit
    EQUIVALENT_TO = "EQUIVALENT_TO"      # Synonymy or semantic equivalence

    # Causal / Influence
    CAUSES = "CAUSES"                    # Direct causation
    INHIBITS = "INHIBITS"                # Direct inhibition
    ENABLES = "ENABLES"                  # Makes possible or facilitates
    PREVENTS = "PREVENTS"                # Stops from happening
    INFLUENCES = "INFLUENCES"            # Broader, non-specific effect (positive, negative, or unknown direction)
    PREDISPOSES_TO = "PREDISPOSES_TO"    # Increases likelihood of
    CONTRIBUTES_TO = "CONTRIBUTES_TO"    # Is one factor among others leading to an outcome

    # Argumentation / Discourse
    SUPPORTS = "SUPPORTS"                # e.g., Evidence SUPPORTS Hypothesis
    REFUTES = "REFUTES"                  # e.g., Evidence REFUTES Hypothesis (stronger than contradicts)
    CONTRADICTS = "CONTRADICTS"          # e.g., StatementA CONTRADICTS StatementB
    IMPLIES = "IMPLIES"                  # Logical implication
    EXPLAINS = "EXPLAINS"                # e.g., Mechanism EXPLAINS Phenomenon
    ADDRESSES = "ADDRESSES"              # e.g., Paper ADDRESSES Question/Problem

    # Research Context
    REFERENCES_CONCEPT = "REFERENCES_CONCEPT" # e.g., Paper REFERENCES_CONCEPT TheoryY
    USES_METHOD = "USES_METHOD"          # e.g., Study USES_METHOD PCR
    STUDIES = "STUDIES"                  # e.g., Paper STUDIES PhenomenonZ
    PRODUCES = "PRODUCES"                # e.g., Experiment PRODUCES Dataset

    # Comparative / Associative
    ASSOCIATED_WITH = "ASSOCIATED_WITH"  # General, non-causal statistical or conceptual link
    COMPARES_WITH = "COMPARES_WITH"      # Explicit comparison
    SIMILAR_TO = "SIMILAR_TO"
    DIFFERENT_FROM = "DIFFERENT_FROM"

    # Temporal
    PRECEDES = "PRECEDES"
    FOLLOWS = "FOLLOWS"
    COOCCURS_WITH = "COOCCURS_WITH"      # Appears together, not necessarily causally

    # Default / Generic
    RELATED_TO = "RELATED_TO"            # Catch-all if no other type fits well


class DirectedRelationship(BaseModel):
    """
    Represents a directed, typed relationship between two scientific concepts.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_concept_id: uuid.UUID
    target_concept_id: uuid.UUID
    type: RelationshipType
    description: str # Could be auto-generated based on type and concepts, or user-provided
    weight: float = Field(default=1.0, ge=0.0) # Represents strength, confidence, or probability
    evidence_sources: List[Evidence] = Field(default_factory=list)

    model_config = {"frozen": True}
