"""
Unit tests for the KnowledgeSynthesisUseCase.
"""
import uuid
import pytest
from unittest.mock import Mock, MagicMock

# Adjust import path for the sandboxed environment
from tests.domain.domain_for_test import ScientificConcept, ConceptType, Evidence
from tests.application.use_cases.use_cases_for_test import (
    KnowledgeSynthesisUseCase,
    CreateConceptInput,
)

# For ConceptRepository and RelationshipRepository, we rely on mocking.
# The use_cases_for_test.py file includes minimal forward declarations for these
# to satisfy type hints within KnowledgeSynthesisUseCase itself.

@pytest.fixture
def mock_concept_repo():
    """Fixture for a mocked ConceptRepository."""
    repo = MagicMock() # Using MagicMock to handle attribute access and method calls
    # If we had the Protocol, we could do: repo = Mock(spec=ConceptRepository)
    return repo

@pytest.fixture
def mock_relationship_repo():
    """Fixture for a mocked RelationshipRepository."""
    repo = MagicMock()
    # If we had the Protocol, we could do: repo = Mock(spec=RelationshipRepository)
    return repo

@pytest.fixture
def use_case(mock_concept_repo, mock_relationship_repo):
    """Fixture for the KnowledgeSynthesisUseCase with mocked repositories."""
    return KnowledgeSynthesisUseCase(
        concept_repo=mock_concept_repo,
        relationship_repo=mock_relationship_repo
    )

class TestKnowledgeSynthesisUseCase:

    def test_create_concept_success(self, use_case, mock_concept_repo):
        input_data = CreateConceptInput(
            name="Test Concept Alpha",
            description="Description for alpha.",
            type=ConceptType.SUBSTANCE,
            properties={"color": "blue"},
            evidence_sources=[
                Evidence(source_doi="doi:123", source_citation="Test 2024", snippet="s", confidence=1.0)
            ]
        )

        # The actual ScientificConcept instance will be created inside the use case
        # We need to capture it or verify its properties.
        # mock_concept_repo.add will be called with this instance.

        created_concept_instance = use_case.create_concept(input_data)

        # 1. Assert the returned concept has the correct data and a generated ID
        assert isinstance(created_concept_instance.id, uuid.UUID)
        assert created_concept_instance.name == input_data.name
        assert created_concept_instance.description == input_data.description
        assert created_concept_instance.type == input_data.type
        assert created_concept_instance.properties == input_data.properties
        assert created_concept_instance.evidence_sources == input_data.evidence_sources

        # 2. Assert that the repository's add method was called once with the created concept
        mock_concept_repo.add.assert_called_once()
        args, _ = mock_concept_repo.add.call_args
        added_concept_to_repo = args[0]

        assert isinstance(added_concept_to_repo, ScientificConcept)
        assert added_concept_to_repo.id == created_concept_instance.id # Important: same instance or at least same ID
        assert added_concept_to_repo.name == input_data.name
        assert added_concept_to_repo.description == input_data.description
        assert added_concept_to_repo.type == input_data.type
        assert added_concept_to_repo.properties == input_data.properties
        assert added_concept_to_repo.evidence_sources == input_data.evidence_sources


    def test_get_all_concepts_empty(self, use_case, mock_concept_repo):
        mock_concept_repo.list_all.return_value = []

        concepts = use_case.get_all_concepts()

        assert concepts == []
        mock_concept_repo.list_all.assert_called_once()

    def test_get_all_concepts_with_data(self, use_case, mock_concept_repo):
        concept1_data = {
            "id": uuid.uuid4(), "name": "Concept 1", "description": "Desc 1",
            "type": ConceptType.PHENOMENON, "properties": {}, "evidence_sources": []
        }
        concept2_data = {
            "id": uuid.uuid4(), "name": "Concept 2", "description": "Desc 2",
            "type": ConceptType.MECHANISM,"properties": {}, "evidence_sources": []
        }
        concept1 = ScientificConcept(**concept1_data)
        concept2 = ScientificConcept(**concept2_data)

        mock_concept_repo.list_all.return_value = [concept1, concept2]

        retrieved_concepts = use_case.get_all_concepts()

        assert len(retrieved_concepts) == 2
        assert concept1 in retrieved_concepts
        assert concept2 in retrieved_concepts
        mock_concept_repo.list_all.assert_called_once()

    def test_get_concept_details_found(self, use_case, mock_concept_repo):
        concept_id = uuid.uuid4()
        concept_data = {
            "id": concept_id, "name": "Detailed Concept", "description": "Details here.",
            "type": ConceptType.HYPOTHESIS, "properties": {}, "evidence_sources": []
        }
        expected_concept = ScientificConcept(**concept_data)

        mock_concept_repo.get_by_id.return_value = expected_concept

        retrieved_concept = use_case.get_concept_details(concept_id)

        assert retrieved_concept == expected_concept
        mock_concept_repo.get_by_id.assert_called_once_with(concept_id)

    def test_get_concept_details_not_found(self, use_case, mock_concept_repo):
        concept_id = uuid.uuid4()
        mock_concept_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match=f"Concept with ID {concept_id} not found."):
            use_case.get_concept_details(concept_id)

        mock_concept_repo.get_by_id.assert_called_once_with(concept_id)

    # We would add tests for relationship-related methods here
    # once they are implemented in the KnowledgeSynthesisUseCase.
    # For example:
    # def test_create_relationship_success(self, use_case, mock_relationship_repo):
    #     pass
    # def test_get_relationships_for_concept(self, use_case, mock_relationship_repo):
    #     pass
