import pytest
from unittest.mock import AsyncMock, MagicMock # AsyncMock para métodos de repo
import uuid
from datetime import datetime, timezone

from Aletheia_v3.application.use_cases import ExtractUCMsUseCase
from Aletheia_v3.application.ports import IConceptRepository, IRelationshipRepository
from Aletheia_v3.api.schemas import ( # Usar los schemas de API como DTOs de entrada/salida para el UC
    UCMExtractionRequestSchema as UCMExtractionInput,
    UCMExtractionResponseSchema,
    ExtractedUCMSchema,
    ExtractedRelationshipSchema
)
from Aletheia_v3.core.domain_models import ScientificConcept, ConceptType, DirectedRelationship

# --- Fixtures ---

@pytest_asyncio.fixture
async def mock_concept_repo() -> AsyncMock:
    return AsyncMock(spec=IConceptRepository)

@pytest_asyncio.fixture
async def mock_relationship_repo() -> AsyncMock:
    return AsyncMock(spec=IRelationshipRepository)

@pytest.fixture
def extract_ucms_use_case(mock_concept_repo: AsyncMock, mock_relationship_repo: AsyncMock) -> ExtractUCMsUseCase:
    return ExtractUCMsUseCase(concept_repo=mock_concept_repo, relationship_repo=mock_relationship_repo)

# --- Tests para _extract_terms_from_text ---

class TestExtractTermsFromText:

    def test_extracts_capitalized_phrases(self, extract_ucms_use_case: ExtractUCMsUseCase):
        text = "This paper discusses Advanced AI Techniques. We also look at Machine Learning Models. Python is a language."
        # Esperado: "Advanced AI Techniques", "Machine Learning Models"
        # "Python" podría ser capturado por single_word si las frases son pocas.
        terms = extract_ucms_use_case._extract_terms_from_text(text, min_freq=1) # min_freq=1 para capturar todas las frases
        assert "Advanced AI Techniques" in terms
        assert "Machine Learning Models" in terms
        # assert "Python" not in terms # Si la lógica prioriza frases y hay suficientes

    def test_extracts_frequent_single_words_if_few_phrases(self, extract_ucms_use_case: ExtractUCMsUseCase):
        text = "An analysis of data and its subsequent data processing. The data was clean."
        # Esperado (con min_freq=2): "data" -> Data
        # "analysis", "processing" aparecen 1 vez.
        terms = extract_ucms_use_case._extract_terms_from_text(text, min_freq=2)
        assert "Data" in terms # Capitalizado
        assert "analysis" not in terms # Freq 1
        assert "processing" not in terms # Freq 1

    def test_no_terms_extracted_from_empty_or_stopwords_only_text(self, extract_ucms_use_case: ExtractUCMsUseCase):
        assert extract_ucms_use_case._extract_terms_from_text("") == []
        assert extract_ucms_use_case._extract_terms_from_text("is the and of for") == []

    def test_stopwords_are_ignored(self, extract_ucms_use_case: ExtractUCMsUseCase):
        text = "The quick brown fox and the lazy dog. The Fox is a name."
        # Esperado (min_freq=1): "quick brown fox", "lazy dog", "Fox" (si las frases son pocas)
        # O si min_freq=2 para palabras: "Fox" (si "The Fox" no se toma como frase)
        terms_mf1 = extract_ucms_use_case._extract_terms_from_text(text, min_freq=1)
        # La lógica actual prioriza frases, "The Fox" es una frase capitalizada
        assert "The Fox" in terms_mf1
        assert "quick brown fox" not in terms_mf1 # No capitalizada
        assert "lazy dog" not in terms_mf1 # No capitalizada

        # Para que "Fox" salga como palabra individual, necesitaríamos que no haya frases o pocas.
        text_simple_fox = "A fox and a fox. The fox."
        terms_simple_fox_mf2 = extract_ucms_use_case._extract_terms_from_text(text_simple_fox, min_freq=2)
        assert "Fox" in terms_simple_fox_mf2 # "fox" aparece 3 veces, se capitaliza.

    def test_phrase_length_limit(self, extract_ucms_use_case: ExtractUCMsUseCase):
        text = "This Is A Very Long Capitalized Phrase Of More Than Five Words. Short Phrase."
        terms = extract_ucms_use_case._extract_terms_from_text(text, min_freq=1)
        assert "Short Phrase" in terms
        assert "This Is A Very Long Capitalized Phrase Of More Than Five Words" not in terms

    def test_single_word_length_and_freq(self, extract_ucms_use_case: ExtractUCMsUseCase):
        text = "abc abc def def def ghi jk lmno pqrst uvwxyz. AI AI." # AI es < 3 letras
        terms = extract_ucms_use_case._extract_terms_from_text(text, min_freq=2)
        assert "Abc" in terms # Freq 2, len 3
        assert "Def" in terms # Freq 3, len 3
        assert "ghi" not in terms # Freq 1
        assert "Lmno" in terms # Freq 1, pero si no hay frases, podría entrar si es de los N mas comunes. La logica actual toma top 15 si freq >= min_freq
        # La lógica actual toma top 15 si freq >= min_freq y no hay frases.
        # Si min_freq=2, Lmno no entra.
        assert "Lmno" not in terms # Freq 1, no cumple min_freq=2
        assert "Pqrst" not in terms # Freq 1
        assert "Uvwxyz" not in terms # Freq 1
        assert "AI" not in terms # len < 3

# --- Tests para el método execute ---
@pytest.mark.asyncio
class TestExtractUCMsUseCaseExecute:

    async def test_execute_extracts_and_persists_ucms_and_relations(
        self, extract_ucms_use_case: ExtractUCMsUseCase,
        mock_concept_repo: AsyncMock,
        mock_relationship_repo: AsyncMock
    ):
        test_text = "Important Concept A is related to Key Phrase B. Concept A again."
        source_doc_id = "doc_123"
        input_data = UCMExtractionInput(
            text_content=test_text,
            source_document_id=source_doc_id,
            source_metadata={"year": 2024}
        )

        # _extract_terms_from_text con min_freq=2 debería encontrar "Important Concept A" y "Key Phrase B"
        # (asumiendo que "Concept A" no se toma como frase separada y "Important Concept A" tiene freq 1)
        # Vamos a mockear _extract_terms_from_text para controlar la salida para este test
        extracted_terms_mock = ["Important Concept A", "Key Phrase B"]
        extract_ucms_use_case._extract_terms_from_text = MagicMock(return_value=extracted_terms_mock)

        response = await extract_ucms_use_case.execute(input_data)

        assert mock_concept_repo.add.call_count == 2
        # Verificar los conceptos añadidos
        added_concepts_domain = [call_args[0][0] for call_args in mock_concept_repo.add.call_args_list]

        assert added_concepts_domain[0].name == "Important Concept A"
        assert added_concepts_domain[0].concept_type == ConceptType.UCM
        assert added_concepts_domain[0].properties["source_document_id"] == source_doc_id

        assert added_concepts_domain[1].name == "Key Phrase B"
        assert added_concepts_domain[1].concept_type == ConceptType.UCM

        # Debería crearse 1 relación entre los 2 UCMs
        assert mock_relationship_repo.add.call_count == 1
        added_relation_domain: DirectedRelationship = mock_relationship_repo.add.call_args[0][0]
        assert added_relation_domain.type == "RELATED_TO_DOCUMENT_CONTEXT"
        assert {added_relation_domain.source_concept_id, added_relation_domain.target_concept_id} == \
               {added_concepts_domain[0].id, added_concepts_domain[1].id}

        assert isinstance(response, UCMExtractionResponseSchema)
        assert response.source_document_id == source_doc_id
        assert len(response.extracted_concepts) == 2
        assert response.extracted_concepts[0].name == "Important Concept A"
        assert response.extracted_concepts[1].name == "Key Phrase B"
        assert len(response.extracted_relationships) == 1
        assert response.extracted_relationships[0].type == "RELATED_TO_DOCUMENT_CONTEXT"
        assert "Persistidos 2 UCMs." in response.processing_log
        assert "Creadas 1 relaciones entre UCMs." in response.processing_log


    async def test_execute_no_terms_extracted(
        self, extract_ucms_use_case: ExtractUCMsUseCase,
        mock_concept_repo: AsyncMock,
        mock_relationship_repo: AsyncMock
    ):
        input_data = UCMExtractionInput(text_content="the of and is", source_document_id="doc_empty")

        # _extract_terms_from_text devolverá lista vacía
        extract_ucms_use_case._extract_terms_from_text = MagicMock(return_value=[])

        response = await extract_ucms_use_case.execute(input_data)

        mock_concept_repo.add.assert_not_called()
        mock_relationship_repo.add.assert_not_called()

        assert response.source_document_id == "doc_empty"
        assert len(response.extracted_concepts) == 0
        assert len(response.extracted_relationships) == 0
        assert "No se extrajeron términos/UCMs significativos." in response.processing_log

```
