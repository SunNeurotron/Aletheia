import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock
import uuid
from datetime import datetime, timezone

from Aletheia_v3.application.use_cases import IngestDocumentUseCase, LinkConceptsUseCase
from Aletheia_v3.application.ports import IConceptRepository, IRelationshipRepository
from Aletheia_v3.application.dtos import (
    IngestDocumentInput, IngestDocumentResult,
    LinkConceptsInput, LinkConceptsResult, RelationshipDTO,
    UCMExtractionInput, UCMExtractionResult, ExtractedUCMDTO, ExtractedRelationshipDTO
)
from Aletheia_v3.core.domain_models import ScientificConcept, ConceptType, DirectedRelationship
from Aletheia_v3.application.use_cases import ExtractUCMsUseCase # Protocol definition

# --- Fixtures ---

@pytest_asyncio.fixture
async def mock_concept_repo() -> AsyncMock:
    return AsyncMock(spec=IConceptRepository)

@pytest_asyncio.fixture
async def mock_relationship_repo() -> AsyncMock:
    return AsyncMock(spec=IRelationshipRepository)

@pytest_asyncio.fixture
async def mock_extract_ucms_use_case() -> AsyncMock:
    mock_ucm_uc = AsyncMock(spec=ExtractUCMsUseCase)
    # Configurar un valor de retorno por defecto para .execute()
    mock_ucm_uc.execute.return_value = UCMExtractionResult(
        source_document_id="docsrc_test_id",
        extracted_concepts=[],
        extracted_relationships=[],
        processing_log=["Mock UCM extraction successful"]
    )
    return mock_ucm_uc

@pytest.fixture
def ingest_document_use_case_instance(mock_concept_repo, mock_extract_ucms_use_case) -> IngestDocumentUseCase:
    return IngestDocumentUseCase(
        concept_repo=mock_concept_repo,
        extract_ucms_use_case=mock_extract_ucms_use_case
    )

@pytest.fixture
def link_concepts_use_case_instance(mock_concept_repo, mock_relationship_repo) -> LinkConceptsUseCase:
    return LinkConceptsUseCase(
        concept_repo=mock_concept_repo,
        relationship_repo=mock_relationship_repo
    )

# --- Test Class ---

@pytest.mark.asyncio
class TestEjeXUseCases:

    async def test_ingest_document_success(self, ingest_document_use_case_instance: IngestDocumentUseCase, mock_concept_repo: AsyncMock, mock_extract_ucms_use_case: AsyncMock):
        input_data = IngestDocumentInput(
            document_text="This is a test document about AI.",
            source_doi="10.1234/test.doi",
            source_citation="Test Author, Test Journal, 2023",
            source_metadata={"year": 2023, "keywords": ["AI", "testing"]}
        )

        # Configurar el resultado esperado de la extracción de UCMs
        expected_ucm_result = UCMExtractionResult(
            source_document_id="some_doc_id", # Esto será sobrescrito por el ID real del doc source
            extracted_concepts=[ExtractedUCMDTO(id="ucm1", name="AI Concept", concept_type="GENERIC_CONCEPT")],
            extracted_relationships=[],
            processing_log=["UCMs extracted."]
        )
        mock_extract_ucms_use_case.execute.return_value = expected_ucm_result

        result = await ingest_document_use_case_instance.execute(input_data)

        # Verificar llamada a concept_repo.add para el DOCUMENT_SOURCE
        mock_concept_repo.add.assert_called_once()
        added_concept: ScientificConcept = mock_concept_repo.add.call_args[0][0]

        assert isinstance(added_concept, ScientificConcept)
        assert added_concept.concept_type == ConceptType.DOCUMENT_SOURCE
        assert added_concept.name == input_data.source_doi # o la lógica de nombre que se implementó
        assert added_concept.properties["doi"] == input_data.source_doi
        assert added_concept.properties["citation"] == input_data.source_citation
        assert added_concept.properties["year"] == 2023

        # Verificar llamada a extract_ucms_use_case.execute
        mock_extract_ucms_use_case.execute.assert_called_once()
        ucm_input_call: UCMExtractionInput = mock_extract_ucms_use_case.execute.call_args[0][0]
        assert ucm_input_call.text_content == input_data.document_text
        assert ucm_input_call.source_document_id == added_concept.id # El ID generado para el doc source
        assert ucm_input_call.source_metadata == input_data.source_metadata

        # Verificar el resultado de IngestDocumentUseCase
        assert isinstance(result, IngestDocumentResult)
        assert result.document_source_id == added_concept.id
        # El source_document_id en ucm_extraction_result es el mismo que el del doc source
        expected_ucm_result.source_document_id = added_concept.id
        assert result.ucm_extraction_result == expected_ucm_result


    async def test_link_concepts_success(self, link_concepts_use_case_instance: LinkConceptsUseCase, mock_concept_repo: AsyncMock, mock_relationship_repo: AsyncMock):
        source_id = f"concept_{uuid.uuid4().hex}"
        target_id = f"concept_{uuid.uuid4().hex}"

        mock_source_concept = ScientificConcept(id=source_id, name="Source Concept", concept_type=ConceptType.GENERIC_CONCEPT)
        mock_target_concept = ScientificConcept(id=target_id, name="Target Concept", concept_type=ConceptType.GENERIC_CONCEPT)

        # Configurar get_by_id para devolver los conceptos
        mock_concept_repo.get_by_id.side_effect = lambda cid: mock_source_concept if cid == source_id else mock_target_concept if cid == target_id else None

        input_data = LinkConceptsInput(
            source_concept_id=source_id,
            target_concept_id=target_id,
            relationship_type="RELATES_TO",
            description="Source relates to target.",
            properties={"weight": 0.8, "context": "test_linking"}
        )

        result = await link_concepts_use_case_instance.execute(input_data)

        # Verificar llamada a relationship_repo.add
        mock_relationship_repo.add.assert_called_once()
        added_relationship: DirectedRelationship = mock_relationship_repo.add.call_args[0][0]

        assert isinstance(added_relationship, DirectedRelationship)
        assert added_relationship.source_concept_id == source_id
        assert added_relationship.target_concept_id == target_id
        assert added_relationship.type == input_data.relationship_type
        assert added_relationship.description == input_data.description
        assert added_relationship.properties == input_data.properties

        # Verificar el resultado de LinkConceptsUseCase
        assert isinstance(result, LinkConceptsResult)
        assert result.created_relationship.id == added_relationship.id
        assert result.created_relationship.source_concept_id == source_id
        assert result.created_relationship.target_concept_id == target_id
        assert result.created_relationship.type == input_data.relationship_type
        assert result.created_relationship.description == input_data.description

    async def test_link_concepts_description_generation(self, link_concepts_use_case_instance: LinkConceptsUseCase, mock_concept_repo: AsyncMock, mock_relationship_repo: AsyncMock):
        source_id = f"concept_{uuid.uuid4().hex}"
        target_id = f"concept_{uuid.uuid4().hex}"

        mock_source_concept = ScientificConcept(id=source_id, name="Source Name", concept_type=ConceptType.UCM)
        mock_target_concept = ScientificConcept(id=target_id, name="Target Name", concept_type=ConceptType.UCM)
        mock_concept_repo.get_by_id.side_effect = lambda cid: mock_source_concept if cid == source_id else mock_target_concept if cid == target_id else None

        input_data = LinkConceptsInput(
            source_concept_id=source_id,
            target_concept_id=target_id,
            relationship_type="CAUSES"
            # No description provided
        )

        await link_concepts_use_case_instance.execute(input_data)

        added_relationship: DirectedRelationship = mock_relationship_repo.add.call_args[0][0]
        expected_description = "Source Name CAUSES Target Name."
        assert added_relationship.description == expected_description

    async def test_link_concepts_source_not_found(self, link_concepts_use_case_instance: LinkConceptsUseCase, mock_concept_repo: AsyncMock):
        mock_concept_repo.get_by_id.return_value = None # Simular que el primer get_by_id (source) falla

        input_data = LinkConceptsInput(
            source_concept_id="non_existent_source",
            target_concept_id="existent_target", # Este no se llegará a comprobar
            relationship_type="LINKS_TO"
        )

        with pytest.raises(ValueError, match="Source concept with ID 'non_existent_source' not found."):
            await link_concepts_use_case_instance.execute(input_data)

    async def test_link_concepts_target_not_found(self, link_concepts_use_case_instance: LinkConceptsUseCase, mock_concept_repo: AsyncMock):
        source_id = f"concept_{uuid.uuid4().hex}"
        mock_source_concept = ScientificConcept(id=source_id, name="Source Exists", concept_type=ConceptType.GENERIC_CONCEPT)

        # Primero devuelve el source, luego None para el target
        mock_concept_repo.get_by_id.side_effect = [mock_source_concept, None]

        input_data = LinkConceptsInput(
            source_concept_id=source_id,
            target_concept_id="non_existent_target",
            relationship_type="LINKS_TO"
        )

        with pytest.raises(ValueError, match="Target concept with ID 'non_existent_target' not found."):
            await link_concepts_use_case_instance.execute(input_data)

```
