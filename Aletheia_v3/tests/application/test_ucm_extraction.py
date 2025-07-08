import pytest
import pytest_asyncio # For async fixtures
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime, timezone

# Module to test
from Aletheia_v3.application.use_cases import ExtractUCMsUseCase
# Dependencies to mock
from Aletheia_v3.application.ports import IConceptRepository, IRelationshipRepository
# DTOs
from Aletheia_v3.api.schemas import (
    UCMExtractionRequestSchema as UCMExtractionInput,
    UCMExtractionResponseSchema,
    # ExtractedUCMSchema, # These will be part of the response, implicitly tested
    # ExtractedRelationshipSchema
)
# Domain models
from Aletheia_v3.core.domain_models import ScientificConcept, ConceptType, DirectedRelationship

# --- Mock spaCy components ---
class MockSpacySpan:
    def __init__(self, text, label_, start_char, end_char):
        self.text = text
        self.label_ = label_
        self.start_char = start_char
        self.end_char = end_char

class MockSpacyDoc:
    def __init__(self, ents):
        self.ents = ents

class MockSpacyNLP:
    def __init__(self, mock_entities_data):
        # mock_entities_data: list of tuples (text, label, start, end)
        self.mock_entities_data = mock_entities_data

    def __call__(self, text_content):
        # Create MockSpacySpan objects from the mock_entities_data
        mock_spans = [
            MockSpacySpan(text=data[0], label_=data[1], start_char=data[2], end_char=data[3])
            for data in self.mock_entities_data
        ]
        return MockSpacyDoc(ents=mock_spans)

# --- Fixtures ---

@pytest_asyncio.fixture
async def mock_concept_repo() -> AsyncMock:
    return AsyncMock(spec=IConceptRepository)

@pytest_asyncio.fixture
async def mock_relationship_repo() -> AsyncMock:
    return AsyncMock(spec=IRelationshipRepository)

# Fixture for ExtractUCMsUseCase with mocked spaCy
@pytest.fixture
def extract_ucms_use_case_ner(
    mock_concept_repo: AsyncMock,
    mock_relationship_repo: AsyncMock,
    mock_spacy_nlp_object: MockSpacyNLP # This fixture will be parameterized in tests
) -> ExtractUCMsUseCase:
    # Patch spacy.load for the duration of this use case's instantiation
    with patch('Aletheia_v3.application.use_cases.spacy.load') as mock_spacy_load:
        mock_spacy_load.return_value = mock_spacy_nlp_object
        use_case = ExtractUCMsUseCase(
            concept_repo=mock_concept_repo,
            relationship_repo=mock_relationship_repo
        )
        # Ensure the nlp object was set using the mock
        assert use_case.nlp == mock_spacy_nlp_object, "spaCy model not mocked correctly in use case"
        return use_case

# --- Tests for NER-based execute method ---
@pytest.mark.asyncio
class TestExtractUCMsUseCaseExecuteNER:

    @pytest.mark.parametrize("mock_spacy_nlp_object, test_text, expected_entities_count, expected_relations_count, expected_log_messages", [
        (
            MockSpacyNLP([("Apple Inc.", "ORG", 0, 10), ("Tim Cook", "PERSON", 15, 23)]),
            "Apple Inc. and Tim Cook are famous.",
            2, 1,
            ["Processed text with spaCy NER. Found 2 entities.", "Persisted 2 UCMs from NER.", "Creadas 1 relaciones entre UCMs."]
        ),
        (
            MockSpacyNLP([]), # No entities found by NER
            "Some generic text without entities.",
            0, 0,
            ["Processed text with spaCy NER. Found 0 entities.", "No UCMs were extracted from the document."]
        ),
        (
            MockSpacyNLP([("London", "GPE", 5, 11)]),
            "I live in London.",
            1, 0, # Only one UCM, so no relationships
            ["Processed text with spaCy NER. Found 1 entities.", "Persisted 1 UCMs from NER."]
        )
    ])
    async def test_execute_with_ner_entities(
        self, extract_ucms_use_case_ner: ExtractUCMsUseCase, # Uses the fixture that receives mock_spacy_nlp_object
        mock_concept_repo: AsyncMock,
        mock_relationship_repo: AsyncMock,
        test_text: str,
        expected_entities_count: int,
        expected_relations_count: int,
        expected_log_messages: List[str]
        # mock_spacy_nlp_object is implicitly used by extract_ucms_use_case_ner fixture
    ):
        source_doc_id = f"doc_{uuid.uuid4()}"
        input_data = UCMExtractionInput(
            text_content=test_text,
            source_document_id=source_doc_id,
            source_metadata={"test_run": True}
        )

        # The use case already has the mocked nlp object from the fixture
        response = await extract_ucms_use_case_ner.execute(input_data)

        assert mock_concept_repo.add.call_count == expected_entities_count

        if expected_entities_count > 0:
            added_concepts_domain = [call.args[0] for call in mock_concept_repo.add.call_args_list]
            # Example check for the first concept if entities were expected
            # This assumes mock_spacy_nlp_object.mock_entities_data is accessible if needed for deep validation
            # For now, we check properties based on the mocked spaCy behavior
            first_mock_entity_data = extract_ucms_use_case_ner.nlp.mock_entities_data[0] if extract_ucms_use_case_ner.nlp.mock_entities_data else None
            if first_mock_entity_data:
                assert added_concepts_domain[0].name == first_mock_entity_data[0]
                assert added_concepts_domain[0].properties["ner_label"] == first_mock_entity_data[1]
                assert added_concepts_domain[0].properties["extraction_method"] == "spacy_ner_en_core_web_sm"

        assert mock_relationship_repo.add.call_count == expected_relations_count

        assert isinstance(response, UCMExtractionResponseSchema)
        assert response.source_document_id == source_doc_id
        assert len(response.extracted_concepts) == expected_entities_count
        assert len(response.extracted_relationships) == expected_relations_count

        for log_msg in expected_log_messages:
            assert log_msg in response.processing_log

    async def test_execute_spacy_model_not_loaded(
        self, mock_concept_repo: AsyncMock, mock_relationship_repo: AsyncMock
    ):
        # Test behavior when spaCy model fails to load in __init__
        with patch('Aletheia_v3.application.use_cases.spacy.load') as mock_spacy_load:
            mock_spacy_load.side_effect = OSError("Simulated model not found")
            use_case = ExtractUCMsUseCase(
                concept_repo=mock_concept_repo,
                relationship_repo=mock_relationship_repo
            )
            assert use_case.nlp is None

            input_data = UCMExtractionInput(text_content="Some text", source_document_id="doc_no_nlp")
            response = await use_case.execute(input_data)

            mock_concept_repo.add.assert_not_called()
            mock_relationship_repo.add.assert_not_called()
            assert "spaCy NLP model not available. NER extraction skipped." in response.processing_log
            assert "No UCMs were extracted from the document." in response.processing_log

# --- Tests for _extract_terms_via_regex (if kept and used) ---
# These tests would be similar to the old TestExtractTermsFromText if that logic is retained.
# For now, as it's a stub, no new tests for it.
# class TestExtractTermsViaRegex:
#     ...

# Note: The original tests for _extract_terms_from_text are now less relevant as the primary
# extraction mechanism has changed. They could be adapted for _extract_terms_via_regex
# if that method is fully implemented and used as a fallback.
# For this refactoring, the focus is on testing the new NER path.

```
