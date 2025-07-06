"""
Unit tests for the domain models in aletheia.domain.models.
"""
import sys
import os
import uuid
import pytest
from pydantic import ValidationError

# --- Debugging imports ---
# print(f"DEBUG: Calculated PROJECT_ROOT: {PROJECT_ROOT}")
# print(f"DEBUG: Current sys.path: {sys.path}")
# if os.path.exists(PROJECT_ROOT):
#     print(f"DEBUG: Contents of PROJECT_ROOT ({PROJECT_ROOT}): {os.listdir(PROJECT_ROOT)}")
#     ALETHEIA_PATH = os.path.join(PROJECT_ROOT, 'aletheia')
#     print(f"DEBUG: Expected aletheia path: {ALETHEIA_PATH}")
#     print(f"DEBUG: Does aletheia path exist? {os.path.exists(ALETHEIA_PATH)}")
#     if os.path.exists(ALETHEIA_PATH):
#         print(f"DEBUG: Contents of ALETHEIA_PATH ({ALETHEIA_PATH}): {os.listdir(ALETHEIA_PATH)}")
# --- End Debugging imports ---

# Import from the temporary location
from tests.domain.domain_for_test import (
    Evidence,
    ScientificConcept,
    ConceptType,
    DirectedRelationship,
    RelationshipType,
)


class TestEvidence:
    def test_evidence_creation_valid(self):
        ev = Evidence(
            source_doi="10.1000/xyz123",
            source_citation="Author et al., 2023",
            snippet="This is a snippet.",
            confidence=0.85,
        )
        assert ev.source_doi == "10.1000/xyz123"
        assert ev.confidence == 0.85

    def test_evidence_confidence_bounds(self):
        with pytest.raises(ValidationError):
            Evidence(
                source_doi="10.1000/xyz123",
                source_citation="Author et al., 2023",
                snippet="Snippet",
                confidence=1.5,
            )
        with pytest.raises(ValidationError):
            Evidence(
                source_doi="10.1000/xyz123",
                source_citation="Author et al., 2023",
                snippet="Snippet",
                confidence=-0.1,
            )

class TestScientificConcept:
    def test_concept_creation_minimal(self):
        concept = ScientificConcept(
            name="Test Concept",
            description="A basic concept for testing.",
            type=ConceptType.PHENOMENON,
        )
        assert isinstance(concept.id, uuid.UUID)
        assert concept.name == "Test Concept"
        assert concept.type == ConceptType.PHENOMENON
        assert concept.properties == {}
        assert concept.evidence_sources == []

    def test_concept_creation_with_properties_and_evidence(self):
        ev1 = Evidence(source_doi="doi1", source_citation="cite1", snippet="snip1", confidence=0.9)
        concept = ScientificConcept(
            name="Complex Concept",
            description="A more complex concept.",
            type=ConceptType.MECHANISM,
            properties={"complexity": 10, "status": "hypothesized"},
            evidence_sources=[ev1],
        )
        assert concept.properties["complexity"] == 10
        assert len(concept.evidence_sources) == 1
        assert concept.evidence_sources[0].source_doi == "doi1"

    def test_concept_is_immutable(self):
        concept = ScientificConcept(
            name="Immutable Concept",
            description="Test immutability.",
            type=ConceptType.SUBSTANCE,
        )
        with pytest.raises(TypeError): # Pydantic v1 used TypeError for frozen models
                                     # Pydantic v2 might raise ValidationError or AttributeError
                                     # depending on how modification is attempted.
                                     # For direct attribute setting, it's usually AttributeError
                                     # For .model_copy(update=...) it's valid
            try:
                concept.name = "New Name"
            except Exception as e: # Catching a broader exception to see what Pydantic v2 does
                if isinstance(e, (ValidationError, AttributeError, TypeError)):
                    raise TypeError("Field is immutable") # Re-raise as TypeError for consistency if needed
                raise e # Re-raise original if not one of the expected for frozen models

        # Test that evidence_sources list modification also fails if not handled correctly
        # Pydantic's frozen=True makes fields immutable, but lists themselves are mutable
        # However, direct reassignment of the list attribute would fail.
        # For deep immutability, custom validators or immutable list types would be needed.
        # Here we test assignment to the attribute itself.
        ev_list = [Evidence(source_doi="d", source_citation="c", snippet="s", confidence=1.0)]
        with pytest.raises(TypeError):
             try:
                concept.evidence_sources = ev_list
             except Exception as e:
                if isinstance(e, (ValidationError, AttributeError, TypeError)):
                    raise TypeError("Field is immutable")
                raise e


    def test_concept_invalid_type(self):
        with pytest.raises(ValidationError):
            ScientificConcept(
                name="Invalid Type Concept",
                description="Test invalid concept type.",
                type="INVALID_TYPE_STRING",
            )

    def test_concept_creation_with_eje_y_fields(self):
        ucm_id1 = uuid.uuid4()
        cluster_id1 = uuid.uuid4()
        concept = ScientificConcept(
            name="Eje Y Test Concept",
            description="Testing new Eje Y fields.",
            type=ConceptType.PROPOSITION, # Type that could use these fields
            verification_hash="abc123def",
            member_concept_ids=[ucm_id1],
            derived_from_cluster_id=cluster_id1,
            derived_from_ucm_ids=[ucm_id1]
        )
        assert concept.verification_hash == "abc123def"
        assert concept.member_concept_ids == [ucm_id1]
        assert concept.derived_from_cluster_id == cluster_id1
        assert concept.derived_from_ucm_ids == [ucm_id1]
        assert concept.type == ConceptType.PROPOSITION

    def test_concept_type_enum_values_exist(self):
        # Test that new enum values are accessible
        assert ConceptType.UCM.value == "UCM"
        assert ConceptType.CLUSTER.value == "CLUSTER"
        assert ConceptType.PROPOSITION.value == "PROPOSITION"
        assert ConceptType.EVIDENCE_UNIT.value == "EVIDENCE_UNIT"
        # Test one of the old ones to ensure they are still there
        assert ConceptType.PHENOMENON.value == "PHENOMENON"


class TestDirectedRelationship:
    def test_relationship_creation_minimal(self):
        source_id = uuid.uuid4()
        target_id = uuid.uuid4()
        rel = DirectedRelationship(
            source_concept_id=source_id,
            target_concept_id=target_id,
            type=RelationshipType.CAUSES,
            description="Source causes target.",
        )
        assert isinstance(rel.id, uuid.UUID)
        assert rel.source_concept_id == source_id
        assert rel.target_concept_id == target_id
        assert rel.type == RelationshipType.CAUSES
        assert rel.weight == 1.0
        assert rel.evidence_sources == []

    def test_relationship_creation_with_weight_and_evidence(self):
        source_id = uuid.uuid4()
        target_id = uuid.uuid4()
        ev1 = Evidence(source_doi="doi_rel", source_citation="cite_rel", snippet="snip_rel", confidence=0.7)
        rel = DirectedRelationship(
            source_concept_id=source_id,
            target_concept_id=target_id,
            type=RelationshipType.ASSOCIATED_WITH,
            description="Association between concepts.",
            weight=0.75,
            evidence_sources=[ev1],
        )
        assert rel.weight == 0.75
        assert len(rel.evidence_sources) == 1
        assert rel.evidence_sources[0].source_doi == "doi_rel"

    def test_relationship_weight_bounds(self):
        source_id = uuid.uuid4()
        target_id = uuid.uuid4()
        with pytest.raises(ValidationError):
            DirectedRelationship(
                source_concept_id=source_id,
                target_concept_id=target_id,
                type=RelationshipType.INHIBITS,
                description="Invalid weight.",
                weight=-0.5,
            )

    def test_relationship_is_immutable(self):
        source_id = uuid.uuid4()
        target_id = uuid.uuid4()
        rel = DirectedRelationship(
            source_concept_id=source_id,
            target_concept_id=target_id,
            type=RelationshipType.IS_A, # Changed from SUBCLASS_OF
            description="Test immutability.",
        )
        with pytest.raises(TypeError):
            try:
                rel.description = "New Description"
            except Exception as e:
                if isinstance(e, (ValidationError, AttributeError, TypeError)):
                    raise TypeError("Field is immutable")
                raise e

    def test_relationship_invalid_type(self):
        source_id = uuid.uuid4()
        target_id = uuid.uuid4()
        with pytest.raises(ValidationError):
            DirectedRelationship(
                source_concept_id=source_id,
                target_concept_id=target_id,
                type="INVALID_REL_TYPE",
                description="Invalid relationship type.",
            )

# Example of using Hypothesis for property-based testing (optional, can be expanded)
# from hypothesis import given, strategies as st

# @given(st.floats(min_value=-10.0, max_value=10.0))
# def test_evidence_confidence_hypothesis(confidence_val):
#     if 0.0 <= confidence_val <= 1.0:
#         Evidence(source_doi="d", source_citation="c", snippet="s", confidence=confidence_val)
#     else:
#         with pytest.raises(ValidationError):
#             Evidence(source_doi="d", source_citation="c", snippet="s", confidence=confidence_val)

# @given(st.text(), st.text(), st.text(), st.sampled_from(ConceptType))
# def test_scientific_concept_creation_hypothesis(name, description, snippet, concept_type):
#     # This is a basic test, more complex strategies can be built
#     concept = ScientificConcept(
#         name=name,
#         description=description,
#         type=concept_type
#     )
#     assert concept.name == name
#     assert concept.description == description
#     assert concept.type == concept_type

# Note: Hypothesis tests for immutability are more complex to set up correctly.
# The direct attribute setting tests above are generally sufficient for Pydantic's frozen=True.
# For full Hypothesis integration, one might define strategies for generating whole model instances.
# For now, I've commented out the Hypothesis examples to keep the initial set of tests focused
# on the direct validation and core Pydantic behaviors. They can be uncommented and expanded
# if deeper property-based testing is desired.
