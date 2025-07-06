"""
Temporary location for infrastructure (repository implementations) to make them
accessible to tests in this sandboxed environment.
"""
import uuid
from typing import Dict, List, Optional

# Import domain models from their temporary test location
from tests.domain.domain_for_test import ScientificConcept, DirectedRelationship

# If repository protocols were complex, we'd import them from a test-local ports file too.
# For now, these classes implicitly implement the (simple) structure expected.

class InMemoryConceptRepository:
    """
    An in-memory implementation of the ConceptRepository port.
    """
    def __init__(self):
        self._data: Dict[uuid.UUID, ScientificConcept] = {}

    def add(self, concept: ScientificConcept) -> None:
        self._data[concept.id] = concept

    def get_by_id(self, concept_id: uuid.UUID) -> Optional[ScientificConcept]:
        return self._data.get(concept_id)

    def list_all(self) -> List[ScientificConcept]:
        return list(self._data.values())


class InMemoryRelationshipRepository:
    """
    An in-memory implementation of the RelationshipRepository port.
    """
    def __init__(self):
        self._data: Dict[uuid.UUID, DirectedRelationship] = {}

    def add(self, relationship: DirectedRelationship) -> None:
        self._data[relationship.id] = relationship

    def get_by_id(self, relationship_id: uuid.UUID) -> Optional[DirectedRelationship]:
        return self._data.get(relationship_id)

    def find_by_concept_id(self, concept_id: uuid.UUID) -> List[DirectedRelationship]:
        return [
            rel for rel in self._data.values()
            if rel.source_concept_id == concept_id or rel.target_concept_id == concept_id
        ]
