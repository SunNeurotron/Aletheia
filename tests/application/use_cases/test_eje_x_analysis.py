"""
Unit tests for Eje X Analysis use cases:
- PropositionTypeExtractorUseCase
- EvidenceQualityEvaluatorUseCase
- EnhancedExtractUCMsAndPropositionsUseCase
"""
import re # Added import for re module
import uuid
from unittest.mock import MagicMock, call

import pytest

from tests.application.use_cases.eje_x_analysis_for_test import (
    PropositionTypeExtractorUseCase,
    TypedPropositionOutput,
    EvidenceQualityEvaluatorUseCase,
    EvidenceQualityMetrics,
    EnhancedExtractUCMsAndPropositionsUseCase,
    EnhancedExtractionResult
)
from tests.application.use_cases.use_cases_for_test import ExtractUCMsUseCase, ExtractUCMsInput, UCMExtractionResult
from tests.domain.domain_for_test import PropositionType, EvidenceStrength, ScientificConcept, ConceptType, Evidence
from tests.application.ports.ports_for_test import ConceptRepository


@pytest.fixture
def mock_concept_repo() -> MagicMock:
    """Fixture for a mocked ConceptRepository."""
    repo = MagicMock(spec=ConceptRepository)
    repo.add = MagicMock()
    repo.get_by_id = MagicMock()
    repo.list_all = MagicMock(return_value=[])
    return repo

@pytest.fixture
def mock_ucm_extractor(mock_concept_repo: MagicMock) -> MagicMock: # Added mock_concept_repo dependency
    """Fixture for a mocked ExtractUCMsUseCase."""
    # uc_result = UCMExtractionResult(ucms_created=[], document_concept_id=uuid.uuid4())
    # extractor = MagicMock(spec=ExtractUCMsUseCase, return_value=uc_result)
    # Corrected: __init__ needs concept_repo
    extractor_instance = ExtractUCMsUseCase(concept_repo=mock_concept_repo)
    mocked_extractor = MagicMock(wraps=extractor_instance) # Wraps instance to allow some real method calls if needed, or mock specific ones
    mocked_extractor.execute = MagicMock() # Mock the execute method
    return mocked_extractor


@pytest.fixture
def proposition_extractor() -> PropositionTypeExtractorUseCase:
    """Fixture for PropositionTypeExtractorUseCase."""
    return PropositionTypeExtractorUseCase()

@pytest.fixture
def evidence_evaluator() -> EvidenceQualityEvaluatorUseCase:
    """Fixture for EvidenceQualityEvaluatorUseCase."""
    return EvidenceQualityEvaluatorUseCase()


class TestPropositionTypeExtractorUseCase:
    """Tests for PropositionTypeExtractorUseCase."""

    def test_extract_causal_propositions(self, proposition_extractor: PropositionTypeExtractorUseCase):
        text = "Smoking causes lung cancer. Exercise leads to better health. High sugar intake results in weight gain."
        source_info = {"doi": "test/causal", "citation": "Causal Test 2024"}

        propositions = proposition_extractor.extract_typed_propositions(text, source_info)

        assert len(propositions) == 3
        assert all(p.proposition_type == PropositionType.CAUSAL for p in propositions)

        # Check first proposition details
        # Corrected Mypy issue: ensure p.subject is not None before 'in'
        prop1 = next(p for p in propositions if p.subject and "Smoking" in p.subject)
        assert prop1.subject == "Smoking"
        assert prop1.object_or_predicate == "lung cancer"
        assert prop1.source_info == source_info
        assert prop1.confidence_score >= 0.5

        prop2 = next(p for p in propositions if p.subject and "Exercise" in p.subject)
        assert prop2.subject == "Exercise"
        assert prop2.object_or_predicate == "better health"

    def test_extract_correlational_propositions(self, proposition_extractor: PropositionTypeExtractorUseCase):
        text = "Height correlates with weight. A strong association between income and education was found. The study relates diet to heart disease."
        source_info = {"doi": "test/correlational", "citation": "Correlational Test 2024"}

        propositions = proposition_extractor.extract_typed_propositions(text, source_info)

        assert len(propositions) == 3
        assert all(p.proposition_type == PropositionType.CORRELATIONAL for p in propositions)

        # Corrected Mypy issue
        prop1 = next(p for p in propositions if p.subject and "Height" in p.subject)
        assert prop1.subject == "Height"
        assert prop1.object_or_predicate == "weight"

    def test_extract_definitional_propositions(self, proposition_extractor: PropositionTypeExtractorUseCase):
        text = "A UCM is defined as a Unit Conceptual Minima. Photosynthesis refers to the process plants use to make food."
        source_info = {"doi": "test/definitional", "citation": "Definitional Test 2024"}

        propositions = proposition_extractor.extract_typed_propositions(text, source_info)

        assert len(propositions) == 2
        assert all(p.proposition_type == PropositionType.DEFINITIONAL for p in propositions)

        # Corrected Mypy issue
        prop1 = next(p for p in propositions if p.subject and "UCM" in p.subject)
        assert prop1.subject == "A UCM" # This will be subject to _clean_component logic. If "A " is stripped, this needs to be "UCM"
        assert prop1.object_or_predicate == "a Unit Conceptual Minima" # Same here for "a "

    def test_no_propositions_found(self, proposition_extractor: PropositionTypeExtractorUseCase):
        text = "This sentence contains no clear patterns for the configured types."
        source_info = {"doi": "test/none", "citation": "None Test 2024"}
        propositions = proposition_extractor.extract_typed_propositions(text, source_info)
        assert len(propositions) == 0

    def test_mixed_proposition_types(self, proposition_extractor: PropositionTypeExtractorUseCase):
        text = "Stress causes headaches. Happiness is associated with longevity. Water is defined as H2O."
        source_info = {"doi": "test/mixed", "citation": "Mixed Test 2024"}
        propositions = proposition_extractor.extract_typed_propositions(text, source_info)

        assert len(propositions) == 3
        types_found = {p.proposition_type for p in propositions}
        assert PropositionType.CAUSAL in types_found
        assert PropositionType.CORRELATIONAL in types_found
        assert PropositionType.DEFINITIONAL in types_found

    def test_component_cleaning(self, proposition_extractor: PropositionTypeExtractorUseCase):
        # Test the internal _clean_component method via its usage in _create_typed_proposition
        text = "The active learning causes an improved understanding." # "The", "an", "." should be cleaned
        source_info = {"doi": "test/clean", "citation": "Clean Test 2024"}

        # Manually create a match object to test _create_typed_proposition
        pattern = re.compile(r"(.+?)\s+causes\s+(.+)", re.IGNORECASE)
        match = pattern.search(text)
        assert match is not None

        if match: # Mypy check
            prop = proposition_extractor._create_typed_proposition(
                match, text, PropositionType.CAUSAL, source_info, (1,2)
            )
            assert prop.subject == "active learning"
            assert prop.object_or_predicate == "improved understanding"


class TestEvidenceQualityEvaluatorUseCase:
    """Tests for EvidenceQualityEvaluatorUseCase."""

    def test_evaluate_high_quality_evidence(self, evidence_evaluator: EvidenceQualityEvaluatorUseCase):
        snippet = "A randomized controlled trial published in Nature (2023) showed significant results."
        # Provide more complete metadata for better testing of helpers
        doc_metadata = {
            "doi": "10.1038/nature123",
            "citation": "Nature Author et al. 2023",
            "year": 2023,
            "journal": "Nature" # Match a high-rank journal
        }
        existing_confidence = 0.9 # High consensus

        metrics = evidence_evaluator.evaluate_evidence(snippet, doc_metadata, existing_confidence)

        assert metrics.source_reliability_score == pytest.approx(0.95) # nature score / 10
        assert metrics.citation_impact_factor == pytest.approx(9.5) # Raw IF for Nature
        assert metrics.temporal_relevance == pytest.approx(1.0) # year 2023 -> age 1 (current_year 2024)
        assert metrics.methodological_rigor == pytest.approx(0.9) # "randomized controlled trial"
        assert metrics.consensus_level == pytest.approx(existing_confidence)

        # Check overall score based on weights (approximate due to potential float issues)
        # reliability: 0.25 * 0.95 = 0.2375
        # impact (normalized): 0.20 * min(9.5/10, 1.0) = 0.20 * 0.95 = 0.19
        # temporal: 0.15 * 1.0 = 0.15
        # methodology: 0.30 * 0.9 = 0.27
        # consensus: 0.10 * 0.9 = 0.09
        # Total = 0.2375 + 0.19 + 0.15 + 0.27 + 0.09 = 0.9375
        assert metrics.overall_quality_score == pytest.approx(0.938, abs=1e-3)


    def test_evaluate_low_quality_evidence(self, evidence_evaluator: EvidenceQualityEvaluatorUseCase):
        snippet = "An opinion piece from a blog suggested a link based on anecdotal evidence."
        doc_metadata = {
            "doi": "blog/post1",
            "citation": "My Personal Blog Post, 2018",
            "year": 2018,
            "journal": "myblog" # Not in rankings, gets default
        }
        existing_confidence = 0.2

        metrics = evidence_evaluator.evaluate_evidence(snippet, doc_metadata, existing_confidence)

        assert metrics.source_reliability_score == pytest.approx(evidence_evaluator.journal_rankings["default_journal"] / 10.0) # default_journal / 10
        assert metrics.citation_impact_factor == pytest.approx(1.0) # Default IF
        assert metrics.temporal_relevance == pytest.approx(0.6) # 2024 - 2018 = 6 years old
        assert metrics.methodological_rigor == pytest.approx(0.3) # "opinion piece", "anecdotal"
        assert metrics.consensus_level == pytest.approx(existing_confidence)

        # reliability: 0.25 * 0.5 = 0.125
        # impact: 0.20 * min(1.0/10, 1.0) = 0.20 * 0.1 = 0.02
        # temporal: 0.15 * 0.6 = 0.09
        # methodology: 0.30 * 0.3 = 0.09
        # consensus: 0.10 * 0.2 = 0.02
        # Total = 0.125 + 0.02 + 0.09 + 0.09 + 0.02 = 0.345
        assert metrics.overall_quality_score == pytest.approx(0.345, abs=1e-3)

    def test_temporal_relevance_various_years(self, evidence_evaluator: EvidenceQualityEvaluatorUseCase):
        evaluator = evidence_evaluator # Use the fixture
        evaluator.current_year = 2024
        assert evaluator._calculate_temporal_relevance({"year": 2024}) == 1.0 # Current year
        assert evaluator._calculate_temporal_relevance({"year": "2023"}) == 1.0 # 1 year old
        assert evaluator._calculate_temporal_relevance({"year": 2020}) == 0.8  # 4 years old
        assert evaluator._calculate_temporal_relevance({"year": 2014}) == 0.6  # 10 years old
        assert evaluator._calculate_temporal_relevance({"year": 2005}) == 0.4  # 19 years old
        assert evaluator._calculate_temporal_relevance({"year": 2000}) == 0.2  # 24 years old
        assert evaluator._calculate_temporal_relevance({"year": "ancient"}) == 0.3 # Unparsable
        assert evaluator._calculate_temporal_relevance({}) == 0.3 # No year info
        assert evaluator._calculate_temporal_relevance({"year": 2025}) == 1.0 # Future year

    def test_methodological_rigor_keywords(self, evidence_evaluator: EvidenceQualityEvaluatorUseCase):
        evaluator = evidence_evaluator
        assert evaluator._assess_methodology("This randomized controlled trial...") == 0.9
        assert evaluator._assess_methodology("A cohort study was performed...") == 0.65
        assert evaluator._assess_methodology("This is a case report...") == 0.3
        assert evaluator._assess_methodology("The authors' opinion is that...") == 0.3
        assert evaluator._assess_methodology("No specific study type mentioned.") == 0.5 # Default

    def test_source_reliability_keywords(self, evidence_evaluator: EvidenceQualityEvaluatorUseCase):
        evaluator = evidence_evaluator
        assert evaluator._calculate_source_reliability("Published in Nature.") == pytest.approx(0.95)
        assert evaluator._calculate_source_reliability("From arXiv pre-print server.") == pytest.approx(0.4)
        assert evaluator._calculate_source_reliability("Unknown journal.") == pytest.approx(0.5) # default_journal
        assert evaluator._calculate_source_reliability(None) == pytest.approx(0.3)


class TestEnhancedExtractUCMsAndPropositionsUseCase:
    """Tests for EnhancedExtractUCMsAndPropositionsUseCase."""

    def test_execute_success_flow(
        self,
        mock_concept_repo: MagicMock,
        mock_ucm_extractor: MagicMock, # Use the new fixture
        proposition_extractor: PropositionTypeExtractorUseCase, # Real instance for this part
        evidence_evaluator: EvidenceQualityEvaluatorUseCase # Real instance for this part
    ):
        # --- Arrange ---
        # 1. Mock ExtractUCMsUseCase response
        doc_id = uuid.uuid4()
        ucm1_id = uuid.uuid4()
        # Ensuring the snippet *exactly* matches a high-rigor keyword for the test
        ucm1_evidence_snippet = "This text contains randomized controlled trial explicitly."
        ucm1 = ScientificConcept(
            id=ucm1_id, name="UCM1", description="Desc1", type=ConceptType.UCM,
            evidence_sources=[
                Evidence(source_doi="doi1", source_citation="cite1", snippet=ucm1_evidence_snippet, confidence=0.8)
            ]
        )
        mock_ucm_extractor.execute.return_value = UCMExtractionResult(
            ucms_created=[ucm1] # Return a list containing the concept
            # document_concept_id=doc_id # This field does not exist on UCMExtractionResult
        )
        # Mock concept_repo.get_by_id to return the UCM when Enhanced use case fetches it
        mock_concept_repo.get_by_id.return_value = ucm1

        # 2. Setup PropositionExtractor behavior (it's real, so it will run on text)
        # (No specific mocking needed if we provide text that generates propositions)

        # 3. Setup EvidenceEvaluator behavior (it's real)
        # (No specific mocking needed, it will use its internal logic)

        use_case = EnhancedExtractUCMsAndPropositionsUseCase(
            concept_repo=mock_concept_repo,
            ucm_extractor=mock_ucm_extractor,
            proposition_extractor=proposition_extractor,
            evidence_evaluator=evidence_evaluator
        )

        input_text = "DrugA causes EffectX. This randomized controlled trial was published in Nature, 2023."
        extract_input = ExtractUCMsInput(
            document_text=input_text,
            source_doi="10.123/nature.doc",
            source_citation="Nature Document 2023"
            # We'd need to ensure ucm1_evidence_snippet is part of input_text if ucm_extractor was real
            # For mocked ucm_extractor, ucm1 is directly returned with its own snippet.
        )

        # --- Act ---
        result = use_case.execute(extract_input)

        # --- Assert ---
        # 1. UCM Extractor was called
        mock_ucm_extractor.execute.assert_called_once_with(extract_input)

        # 2. UCMs returned and evidence evaluated
        assert len(result.ucms_created) == 1
        enhanced_ucm1 = result.ucms_created[0]
        assert enhanced_ucm1.id == ucm1_id
        assert len(enhanced_ucm1.evidence_sources) == 1
        evidence_item = enhanced_ucm1.evidence_sources[0]

        # Check that evidence_strength and assessment_rationale were set
        assert evidence_item.evidence_strength is not None
        assert evidence_item.assessment_rationale is not None
        assert "OverallScore:" in evidence_item.assessment_rationale
        # Example check for strength based on "randomized trial" in ucm1_evidence_snippet
        # This depends on the simplified mapping in EnhancedExtractUCMsAndPropositionsUseCase
        # For "randomized trial", method_rigor = 0.9.
        # If other scores are high enough, it could be STRONG.
        # The current mapping is: (0.9 > 0.7 and reliability > 0.7 and temp > 0.7 and consensus > 0.7)
        # Let's check the rationale includes a high method rigor score
        assert "MethodRigor: 0.90" in evidence_item.assessment_rationale


        # 3. Proposition Extractor was called (implicitly, check results)
        assert len(result.typed_propositions) > 0 # Expect "DrugA causes EffectX"
        causal_prop_found = any(p.proposition_type == PropositionType.CAUSAL and p.subject == "DrugA" for p in result.typed_propositions)
        assert causal_prop_found

        # 4. Document level quality score (optional, might be None if no scores)
        # Based on _calculate_simple_avg_quality, it will parse OverallScore from rationale
        assert result.document_level_quality_score is not None
        assert 0.0 <= result.document_level_quality_score <= 1.0

        # 5. Verify that the UCM object in the repository (if it were a separate instance) would reflect changes.
        # Since InMemoryRepo returns references, ucm1 object IS enhanced_ucm1.
        # No specific repo.add or update call is made in the current use case for UCMs after evidence update.
        # If repo made copies, we'd need to assert repo.add(enhanced_ucm1) was called.

    def test_execute_no_ucms_found(
        self,
        mock_concept_repo: MagicMock,
        mock_ucm_extractor: MagicMock,
        proposition_extractor: PropositionTypeExtractorUseCase,
        evidence_evaluator: EvidenceQualityEvaluatorUseCase
    ):
        mock_ucm_extractor.execute.return_value = UCMExtractionResult(ucms_created=[]) # No document_concept_id here
        mock_concept_repo.get_by_id.return_value = None # If UCMs not found

        use_case = EnhancedExtractUCMsAndPropositionsUseCase(
            concept_repo=mock_concept_repo,
            ucm_extractor=mock_ucm_extractor,
            proposition_extractor=proposition_extractor,
            evidence_evaluator=evidence_evaluator
        )
        extract_input = ExtractUCMsInput(document_text="No UCMs here, but DrugX causes EffectY.", source_doi="d", source_citation="c")

        result = use_case.execute(extract_input)

        assert len(result.ucms_created) == 0
        assert len(result.typed_propositions) == 1 # Proposition should still be extracted
        assert result.typed_propositions[0].proposition_type == PropositionType.CAUSAL
        assert result.document_level_quality_score is None
