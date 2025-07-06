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
    ExtractUCMsUseCase, # Added
    ExtractUCMsInput,   # Added
    UCMExtractionResult, # Added
    FormClustersUseCase, # Added
    FormClusterInput,    # Added
    ClusterFormationResult, # Added
    DerivePropositionsUseCase, # Added
    DerivePropositionInput,    # Added
    PropositionDerivationResult # Added
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


class TestEjeYUseCases:

    def test_extract_ucms_use_case_success(self, mock_concept_repo):
        use_case = ExtractUCMsUseCase(concept_repo=mock_concept_repo)
        input_data = ExtractUCMsInput(
            document_text="This is a sample document about protein X and disease Y.",
            source_doi="doi:test/ejeY.1",
            source_citation="EjeY Tester, 2024"
        )

        result = use_case.execute(input_data)

        assert len(result.ucms_created) == 2 # Based on current simulated logic
        for ucm in result.ucms_created:
            assert ucm.type == ConceptType.UCM
            assert ucm.properties["simulated_extraction"] is True
            assert ucm.verification_hash is not None
            assert len(ucm.evidence_sources) == 1
            assert ucm.evidence_sources[0].source_doi == input_data.source_doi

        # Check that add was called for each UCM
        assert mock_concept_repo.add.call_count == 2
        # Further checks on what was added could be done if needed

    def test_form_clusters_use_case_success(self, mock_concept_repo):
        use_case = FormClustersUseCase(concept_repo=mock_concept_repo)

        ucm1_id = uuid.uuid4()
        ucm2_id = uuid.uuid4()
        ucm1 = ScientificConcept(id=ucm1_id, name="UCM1", description="ucm1 desc", type=ConceptType.UCM, evidence_sources=[Evidence(source_doi="d",source_citation="c",snippet="s",confidence=0.8)])
        ucm2 = ScientificConcept(id=ucm2_id, name="UCM2", description="ucm2 desc", type=ConceptType.UCM, evidence_sources=[Evidence(source_doi="d",source_citation="c",snippet="s",confidence=0.9)])

        mock_concept_repo.get_by_id.side_effect = lambda id_val: ucm1 if id_val == ucm1_id else (ucm2 if id_val == ucm2_id else None)

        input_data = FormClusterInput(
            ucm_ids=[ucm1_id, ucm2_id],
            cluster_name="Test Cluster Alpha",
            cluster_description="A cluster for testing."
        )

        result = use_case.execute(input_data)

        created_cluster = result.cluster_created
        assert created_cluster.type == ConceptType.CLUSTER
        assert created_cluster.name == "Test Cluster Alpha"
        assert created_cluster.member_concept_ids == [ucm1_id, ucm2_id]
        assert created_cluster.properties["ucm_count"] == 2
        assert created_cluster.properties["avg_member_confidence"] == pytest.approx(0.85)

        mock_concept_repo.add.assert_called_once_with(created_cluster)

    def test_form_clusters_use_case_no_ucms(self, mock_concept_repo):
        use_case = FormClustersUseCase(concept_repo=mock_concept_repo)
        input_data = FormClusterInput(ucm_ids=[])
        with pytest.raises(ValueError, match="No UCMs provided to form a cluster."):
            use_case.execute(input_data)

    def test_form_clusters_use_case_invalid_ucm_id(self, mock_concept_repo):
        use_case = FormClustersUseCase(concept_repo=mock_concept_repo)
        valid_ucm_id = uuid.uuid4()
        invalid_ucm_id = uuid.uuid4()

        ucm_valid = ScientificConcept(id=valid_ucm_id, name="Valid UCM", description="...", type=ConceptType.UCM)

        # Simulate finding the valid UCM but not the invalid one
        mock_concept_repo.get_by_id.side_effect = lambda id_val: ucm_valid if id_val == valid_ucm_id else None

        input_data = FormClusterInput(ucm_ids=[valid_ucm_id, invalid_ucm_id])

        with pytest.raises(ValueError, match=f"Invalid or non-UCM concept ID provided: {invalid_ucm_id}"):
            use_case.execute(input_data)

    def test_derive_propositions_use_case_success(self, mock_concept_repo, mock_relationship_repo):
        use_case = DerivePropositionsUseCase(concept_repo=mock_concept_repo, relationship_repo=mock_relationship_repo)

        cluster_id = uuid.uuid4()
        cluster = ScientificConcept(
            id=cluster_id,
            name="Source Cluster",
            description="...",
            type=ConceptType.CLUSTER,
            member_concept_ids=[uuid.uuid4(), uuid.uuid4()] # Add some member ids
        )
        mock_concept_repo.get_by_id.return_value = cluster

        input_data = DerivePropositionInput(
            cluster_id=cluster_id,
            proposition_text="Derived Test Proposition"
        )

        result = use_case.execute(input_data)

        created_proposition = result.proposition_created
        assert created_proposition.type == ConceptType.PROPOSITION
        assert created_proposition.name == "Derived Test Proposition"
        assert created_proposition.derived_from_cluster_id == cluster_id
        assert "derivation_method" in created_proposition.properties

        mock_concept_repo.add.assert_called_once_with(created_proposition)
        # mock_relationship_repo.add was not called in the simple simulation

    def test_derive_propositions_use_case_invalid_cluster_id(self, mock_concept_repo, mock_relationship_repo):
        use_case = DerivePropositionsUseCase(concept_repo=mock_concept_repo, relationship_repo=mock_relationship_repo)
        invalid_cluster_id = uuid.uuid4()
        mock_concept_repo.get_by_id.return_value = None # Simulate cluster not found

        input_data = DerivePropositionInput(cluster_id=invalid_cluster_id)

        with pytest.raises(ValueError, match=f"Invalid or non-CLUSTER concept ID provided for proposition derivation: {invalid_cluster_id}"):
            use_case.execute(input_data)

    def test_derive_propositions_use_case_not_a_cluster(self, mock_concept_repo, mock_relationship_repo):
        use_case = DerivePropositionsUseCase(concept_repo=mock_concept_repo, relationship_repo=mock_relationship_repo)

        not_a_cluster_id = uuid.uuid4()
        not_a_cluster = ScientificConcept(id=not_a_cluster_id, name="Not A Cluster", description="...", type=ConceptType.UCM)
        mock_concept_repo.get_by_id.return_value = not_a_cluster

        input_data = DerivePropositionInput(cluster_id=not_a_cluster_id)

        with pytest.raises(ValueError, match=f"Invalid or non-CLUSTER concept ID provided for proposition derivation: {not_a_cluster_id}"):
            use_case.execute(input_data)
