"""
Temporary location for Application Port (Interface) definitions
to make them accessible to tests in this sandboxed environment.
"""
from typing import Protocol, List, Optional
import uuid

# Import domain models from their temporary test location
from tests.domain.domain_for_test import ScientificConcept, DirectedRelationship


class ConceptRepository(Protocol):
    """
    An interface for storing and retrieving ScientificConcepts.
    """
    def add(self, concept: ScientificConcept) -> None:
        """Adds a new concept to the repository."""
        ...

    def get_by_id(self, concept_id: uuid.UUID) -> Optional[ScientificConcept]:
        """Retrieves a concept by its unique ID."""
        ...

    def list_all(self) -> List[ScientificConcept]:
        """Lists all concepts in the repository."""
        ...


class RelationshipRepository(Protocol):
    """
    An interface for storing and retrieving DirectedRelationships.
    """
    def add(self, relationship: DirectedRelationship) -> None:
        """Adds a new relationship to the repository."""
        ...

    def get_by_id(self, relationship_id: uuid.UUID) -> Optional[DirectedRelationship]:
        """Retrieves a relationship by its unique ID."""
        ...

    def find_by_concept_id(self, concept_id: uuid.UUID) -> List[DirectedRelationship]:
        """Finds all relationships connected to a given concept."""
        ...
