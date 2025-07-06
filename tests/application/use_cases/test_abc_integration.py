"""
Unit tests for ABC Integration components: ABCToUCMMapper and SynthesisGuidedSearchStrategy.
"""
import uuid
from unittest.mock import MagicMock, call, patch

import pytest

from tests.application.use_cases.abc_integration_for_test import (
    ABCToUCMMapper,
    SynthesisGuidedSearchStrategy,
    ABCInsightExtractionInput,
)
from tests.domain.domain_for_test import ScientificConcept, ConceptType, Evidence, ModelArchitectureType, TheoryIntegrationMethod
from tests.application.ports.ports_for_test import ConceptRepository


@pytest.fixture
def mock_concept_repo() -> MagicMock:
    """Fixture for a mocked ConceptRepository."""
    repo = MagicMock(spec=ConceptRepository)
    repo.add = MagicMock()
    repo.get_by_id = MagicMock()
    repo.list_all = MagicMock(return_value=[])
    return repo


class TestABCToUCMMapper:
    """Tests for ABCToUCMMapper."""

    def test_extract_ucms_from_prime_power_pattern(self, mock_concept_repo: MagicMock):
        mapper = ABCToUCMMapper(mock_concept_repo)
        input_data = ABCInsightExtractionInput(
            abc_hits=[
                {"a": 8, "b": 9, "c": 17, "quality": 600, "rad_abc": 2*3*17},
                {"a": 25, "b": 2, "c": 27, "quality": 700, "rad_abc": 5*2*3},
                {"a": 4, "b": 11, "c": 15, "quality": 800, "rad_abc": 2*11*3*5},
                {"a": 7, "b": 13, "c": 20, "quality": 400}, # 7 and 13 are prime powers (7^1, 13^1)
            ],
            search_parameters={"param1": "value1"},
            experiment_id="exp_prime_power",
            min_quality_threshold=500.0
        )

        created_ucms = mapper.extract_ucms_from_abc_results(input_data)

        assert len(created_ucms) >= 1
        mock_concept_repo.add.assert_called()

        prime_power_ucm_found = any(
            ucm.properties.get("pattern_type") == "prime_power_pattern" for ucm in created_ucms
        )
        assert prime_power_ucm_found
        for ucm in created_ucms:
            if ucm.properties.get("pattern_type") == "prime_power_pattern":
                # Corrected assertion: all 4 hits match the prime_power_pattern
                assert ucm.properties["support_count"] == 4

    def test_extract_ucms_from_consecutive_pattern(self, mock_concept_repo: MagicMock):
        mapper = ABCToUCMMapper(mock_concept_repo)
        input_data = ABCInsightExtractionInput(
            abc_hits=[
                {"a": 5, "b": 6, "c": 11, "quality": 600},
                {"a": 10, "b": 12, "c": 11, "quality": 700},
                {"a": 1, "b": 3, "c": 2, "quality": 800},
                {"a": 20, "b": 25, "c": 30, "quality": 400},
            ],
            search_parameters={},
            experiment_id="exp_consecutive",
            min_quality_threshold=500.0
        )
        created_ucms = mapper.extract_ucms_from_abc_results(input_data)

        assert len(created_ucms) >= 1
        consecutive_ucm_found = any(
            ucm.properties.get("pattern_type") == "consecutive_pattern" for ucm in created_ucms
        )
        assert consecutive_ucm_found
        for ucm in created_ucms:
            if ucm.properties.get("pattern_type") == "consecutive_pattern":
                 assert ucm.properties["support_count"] == 3

    def test_extract_ucms_from_high_quality_pattern(self, mock_concept_repo: MagicMock):
        mapper = ABCToUCMMapper(mock_concept_repo)
        input_data = ABCInsightExtractionInput(
            abc_hits=[
                {"a": 1, "b": 1, "c": 2, "quality": 1200},
                {"a": 2, "b": 2, "c": 4, "quality": 1500},
                {"a": 3, "b": 3, "c": 6, "quality": 1100},
                {"a": 4, "b": 4, "c": 8, "quality": 800},
            ],
            search_parameters={},
            experiment_id="exp_high_quality",
            min_quality_threshold=500.0
        )
        created_ucms = mapper.extract_ucms_from_abc_results(input_data)

        high_quality_ucm_found = any(
            ucm.properties.get("pattern_type") == "high_quality_pattern" for ucm in created_ucms
        )
        assert high_quality_ucm_found # This pattern should be created

        ucm_added_count = 0
        for ucm in created_ucms:
            if ucm.properties.get("pattern_type") == "high_quality_pattern":
                assert ucm.properties["support_count"] == 3
                ucm_added_count +=1
        assert ucm_added_count > 0 # Make sure UCM for this pattern was indeed added

    def test_extract_ucms_from_strong_abc_pattern(self, mock_concept_repo: MagicMock):
        mapper = ABCToUCMMapper(mock_concept_repo)
        input_data = ABCInsightExtractionInput(
            abc_hits=[
                {"a": 1, "b": 8, "c": 9, "quality": 600, "rad_abc": 6.0},
                {"a": 1, "b": 1, "c": 1000, "quality": 1100, "rad_abc": 10.0},
                {"a": 2, "b": 2, "c": 2000, "quality": 1200, "rad_abc": 15.0},
                {"a": 3, "b": 3, "c": 3000, "quality": 1300, "rad_abc": 20.0},
            ],
            search_parameters={},
            experiment_id="exp_strong_abc",
            min_quality_threshold=500.0
        )
        created_ucms = mapper.extract_ucms_from_abc_results(input_data)

        strong_abc_ucm_found = any(
            ucm.properties.get("pattern_type") == "strong_abc_pattern" for ucm in created_ucms
        )
        assert strong_abc_ucm_found # This pattern should be created

        ucm_added_count = 0
        for ucm in created_ucms:
            if ucm.properties.get("pattern_type") == "strong_abc_pattern":
                assert ucm.properties["support_count"] == 3
                ucm_added_count +=1
        assert ucm_added_count > 0


    def test_no_pattern_ucm_if_low_support(self, mock_concept_repo: MagicMock):
        mapper = ABCToUCMMapper(mock_concept_repo)
        input_data = ABCInsightExtractionInput(
            abc_hits=[{"a": 8, "b": 9, "c": 17, "quality": 600}],
            search_parameters={},
            experiment_id="exp_low_support",
            min_quality_threshold=500.0
        )
        with patch.object(mapper, '_is_prime_power', side_effect=lambda n: n in [8, 9]):
            created_ucms = mapper.extract_ucms_from_abc_results(input_data)

        pattern_ucm_found = any(
            "pattern_type" in ucm.properties for ucm in created_ucms if ucm.properties # check if properties exist
        )
        assert not pattern_ucm_found

    def test_extract_ucms_from_search_parameters(self, mock_concept_repo: MagicMock):
        mapper = ABCToUCMMapper(mock_concept_repo)
        input_data = ABCInsightExtractionInput(
            abc_hits=[],
            search_parameters={"use_custom_acquisition": True, "quality_found": 600},
            experiment_id="exp_params",
            min_quality_threshold=500.0
        )
        created_ucms = mapper.extract_ucms_from_abc_results(input_data)

        assert len(created_ucms) == 1
        param_ucm = created_ucms[0]
        assert param_ucm.name == "Effective Search Strategy: Structural Bonus"
        assert param_ucm.properties["strategy_type"] == "custom_acquisition"
        mock_concept_repo.add.assert_called_once_with(param_ucm)

    def test_is_prime_power_logic(self, mock_concept_repo: MagicMock):
        mapper = ABCToUCMMapper(mock_concept_repo)
        assert mapper._is_prime_power(2) == True
        assert mapper._is_prime_power(3) == True
        assert mapper._is_prime_power(4) == True
        assert mapper._is_prime_power(27) == True
        assert mapper._is_prime_power(7) == True
        assert mapper._is_prime_power(1) == False
        assert mapper._is_prime_power(6) == False
        assert mapper._is_prime_power(10) == False
        assert mapper._is_prime_power(12) == False
        assert mapper._is_prime_power(49) == True
        assert mapper._is_prime_power(121) == True
        assert mapper._is_prime_power(0) == False
        assert mapper._is_prime_power(99) == False

    def test_empty_hits_and_params(self, mock_concept_repo: MagicMock):
        mapper = ABCToUCMMapper(mock_concept_repo)
        input_data = ABCInsightExtractionInput(
            abc_hits=[],
            search_parameters={},
            experiment_id="exp_empty",
            min_quality_threshold=500.0
        )
        created_ucms = mapper.extract_ucms_from_abc_results(input_data)
        assert len(created_ucms) == 0
        mock_concept_repo.add.assert_not_called()


class TestSynthesisGuidedSearchStrategy:
    """Tests for SynthesisGuidedSearchStrategy."""

    def test_get_recommendations_no_high_level_concepts(self, mock_concept_repo: MagicMock):
        mock_concept_repo.list_all.return_value = []
        strategy = SynthesisGuidedSearchStrategy(mock_concept_repo)
        recommendations = strategy.get_search_recommendations()
        assert recommendations["parameter_suggestions"] == {}
        assert recommendations["focus_areas"] == []
        assert recommendations["avoid_areas"] == []

    def test_get_recommendations_from_unified_model_properties(self, mock_concept_repo: MagicMock):
        model_id = uuid.uuid4()
        unified_model = ScientificConcept(
            id=model_id,
            name="Test Unified Model",
            description="A test unified model.", # Added description
            type=ConceptType.UNIFIED_MODEL,
            properties={
                "architecture_details": {"detail": "some_info"},
                "total_coverage": {"estimated_ucms": 60},
                "architecture_type": ModelArchitectureType.NETWORKED.value
            },
            member_concept_ids=[]
        )
        mock_concept_repo.list_all.return_value = [unified_model]
        strategy = SynthesisGuidedSearchStrategy(mock_concept_repo)
        recommendations = strategy.get_search_recommendations()
        assert recommendations["parameter_suggestions"]["n_trials"] == 10000
        assert recommendations["parameter_suggestions"]["exploration_factor"] == 0.3
        assert recommendations["parameter_suggestions"]["n_iterations_bayes_opt"] == 100

    def test_get_recommendations_from_high_quality_pattern_ucm(self, mock_concept_repo: MagicMock):
        ucm_id = uuid.uuid4()
        pattern_ucm = ScientificConcept(
            id=ucm_id,
            name="High Quality ABC Pattern UCM",
            description="A UCM from a high quality pattern.", # Added description
            type=ConceptType.UCM,
            properties={
                "pattern_type": "super_strong_pattern",
                "average_quality": 1500.0
            }
        )
        mock_concept_repo.list_all.return_value = [pattern_ucm]
        strategy = SynthesisGuidedSearchStrategy(mock_concept_repo)
        recommendations = strategy.get_search_recommendations()
        assert len(recommendations["focus_areas"]) == 1
        focus_area = recommendations["focus_areas"][0]
        assert focus_area["pattern"] == "super_strong_pattern"
        assert "High average quality: 1500.0" in focus_area["reasoning"]

    def test_get_recommendations_from_dialectical_synthesis_in_theory(self, mock_concept_repo: MagicMock):
        theory_id = uuid.uuid4()
        model_id = uuid.uuid4()
        comp_theory = ScientificConcept(
            id=theory_id,
            name="Dialectical Comp Theory",
            description="A comprehensive theory using dialectical synthesis.", # Added description
            type=ConceptType.COMPREHENSIVE_THEORY,
            properties={"integration_method": TheoryIntegrationMethod.DIALECTICAL_SYNTHESIS.value}
        )
        unified_model = ScientificConcept(
            id=model_id,
            name="Model with Dialectical Theory",
            description="A unified model incorporating a dialectical theory.", # Added description
            type=ConceptType.UNIFIED_MODEL,
            member_concept_ids=[theory_id],
            properties={"architecture_details": {}}
        )

        def get_by_id_side_effect(concept_id_to_get):
            if concept_id_to_get == theory_id:
                return comp_theory
            return None # Simplified: only return the theory for this test

        mock_concept_repo.get_by_id.side_effect = get_by_id_side_effect
        mock_concept_repo.list_all.return_value = [unified_model, comp_theory]

        strategy = SynthesisGuidedSearchStrategy(mock_concept_repo)
        recommendations = strategy.get_search_recommendations()

        mock_concept_repo.get_by_id.assert_any_call(theory_id)
        assert recommendations["parameter_suggestions"]["novelty_weight"] == 0.75

    def test_get_recommendations_model_with_high_quality_pattern_in_name(self, mock_concept_repo: MagicMock):
        model_id = uuid.uuid4()
        unified_model = ScientificConcept(
            id=model_id,
            name="Model showcasing high_quality_pattern",
            description="A model whose name suggests high quality patterns.", # Added description
            type=ConceptType.UNIFIED_MODEL,
            properties={"architecture_details": {}},
            member_concept_ids=[]
        )
        mock_concept_repo.list_all.return_value = [unified_model]
        strategy = SynthesisGuidedSearchStrategy(mock_concept_repo)
        recommendations = strategy.get_search_recommendations()
        assert recommendations["parameter_suggestions"]["use_custom_acquisition"] is True

    def test_no_recommendations_if_ucm_quality_low(self, mock_concept_repo: MagicMock):
        ucm_id = uuid.uuid4()
        pattern_ucm = ScientificConcept(
            id=ucm_id,
            name="Low Quality ABC Pattern UCM",
            description="A UCM from a low quality pattern.", # Added description
            type=ConceptType.UCM,
            properties={
                "pattern_type": "weak_pattern",
                "average_quality": 200.0
            }
        )
        mock_concept_repo.list_all.return_value = [pattern_ucm]
        strategy = SynthesisGuidedSearchStrategy(mock_concept_repo)
        recommendations = strategy.get_search_recommendations()
        assert len(recommendations["focus_areas"]) == 0
        assert recommendations["parameter_suggestions"] == {}
