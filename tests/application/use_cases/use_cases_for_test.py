"""
Temporary location for use case definitions to make them accessible to tests
in this sandboxed environment.
"""
import uuid
from typing import List, Dict, Any
from pydantic import BaseModel

# Adjust import for domain models from their temporary test location
from tests.domain.domain_for_test import ScientificConcept, Evidence, ConceptType

# Import repository protocols from their temporary test location
from tests.application.ports.ports_for_test import ConceptRepository, RelationshipRepository


class CreateConceptInput(BaseModel):
    name: str
    description: str
    type: ConceptType
    properties: Dict[str, Any] = {}
    evidence_sources: List[Evidence] = []


class KnowledgeSynthesisUseCase:
    """
    Orchestrates the creation and retrieval of knowledge graph components.
    """
    def __init__(
        self,
        concept_repo: ConceptRepository, # Uses the forward-declared class
        relationship_repo: RelationshipRepository # Uses the forward-declared class
    ):
        self.concept_repo = concept_repo
        self.relationship_repo = relationship_repo

    def create_concept(self, input_data: CreateConceptInput) -> ScientificConcept:
        """
        Creates a new scientific concept and persists it.
        """
        concept = ScientificConcept(
            name=input_data.name,
            description=input_data.description,
            type=input_data.type,
            properties=input_data.properties,
            evidence_sources=input_data.evidence_sources,
        )
        self.concept_repo.add(concept)
        return concept

    def get_all_concepts(self) -> List[ScientificConcept]:
        """
        Retrieves all scientific concepts.
        """
        return self.concept_repo.list_all()

    def get_concept_details(self, concept_id: uuid.UUID) -> ScientificConcept:
        """
        Retrieves a single concept by its ID.
        """
        concept = self.concept_repo.get_by_id(concept_id)
        if not concept:
            raise ValueError(f"Concept with ID {concept_id} not found.")
        return concept
