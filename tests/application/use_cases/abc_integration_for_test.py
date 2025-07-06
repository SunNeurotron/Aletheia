"""
Integration between the synthesis hierarchy and ABC conjecture search.
This connects Eje Y (knowledge synthesis) with the main Aletheia system.
"""
import uuid
from typing import List, Dict, Any, Optional
from collections import defaultdict
import math

from pydantic import BaseModel, Field

# Adjusted imports to be potentially resolvable from project root if 'tests' is on PYTHONPATH
# or if pytest runs from a context where 'tests' is a top-level package.
# This is an attempt to fix ImportError.
from tests.domain.domain_for_test import ScientificConcept, ConceptType, Evidence, ModelArchitectureType, TheoryIntegrationMethod
from tests.application.ports.ports_for_test import ConceptRepository


class ABCInsightExtractionInput(BaseModel):
    """Input for extracting insights from ABC search results."""
    abc_hits: List[Dict[str, Any]]
    search_parameters: Dict[str, Any]
    experiment_id: str
    min_quality_threshold: float = 500.0


class ABCToUCMMapper:
    """
    Maps ABC conjecture search results to UCMs for integration
    into the knowledge synthesis hierarchy.
    """

    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo

    def extract_ucms_from_abc_results(
        self, input_data: ABCInsightExtractionInput
    ) -> List[ScientificConcept]:
        ucms_created: List[ScientificConcept] = []
        pattern_groups = self._identify_patterns(input_data.abc_hits)

        for pattern_name, hits in pattern_groups.items():
            if len(hits) >= 3:
                ucm = self._create_pattern_ucm(pattern_name, hits, input_data)
                self.concept_repo.add(ucm)
                ucms_created.append(ucm)

        param_ucms = self._extract_parameter_insights(
            input_data.search_parameters,
            input_data.experiment_id
        )
        for ucm in param_ucms:
            self.concept_repo.add(ucm)
            ucms_created.append(ucm)
        return ucms_created

    def _identify_patterns(self, abc_hits: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for hit in abc_hits:
            a_orig, b_orig, c_orig = hit.get('a'), hit.get('b'), hit.get('c')

            try:
                # Ensure conversion to int, handle None by skipping the hit
                if a_orig is None or b_orig is None or c_orig is None:
                    continue
                a = int(a_orig)
                b = int(b_orig)
                c = int(c_orig)
            except (ValueError, TypeError):
                continue

            quality_orig = hit.get('quality', 0.0)
            quality = float(quality_orig) if isinstance(quality_orig, (int, float)) else 0.0

            if self._is_prime_power(a) or self._is_prime_power(b):
                patterns['prime_power_pattern'].append(hit)

            if abs(a - b) == 1 or abs(b - c) == 1 or abs(a-c) == 1:
                patterns['consecutive_pattern'].append(hit)

            if quality > 1000:
                patterns['high_quality_pattern'].append(hit)

            rad_abc_orig = hit.get('rad_abc')
            if rad_abc_orig is not None:
                try:
                    rad_abc = float(rad_abc_orig)
                    if c > rad_abc ** 1.5:
                        patterns['strong_abc_pattern'].append(hit)
                except (ValueError, TypeError):
                    pass
        return dict(patterns)

    def _create_pattern_ucm(
        self, pattern_name: str, hits: List[Dict[str, Any]], input_data: ABCInsightExtractionInput
    ) -> ScientificConcept:
        description = f"Pattern discovered in ABC search: {pattern_name}. "
        description += f"Found in {len(hits)} hits "

        avg_quality = 0.0
        if hits:
            valid_qualities = [h.get('quality', 0.0) for h in hits if isinstance(h.get('quality', 0.0), (int, float))]
            if valid_qualities:
                avg_quality = sum(valid_qualities) / len(valid_qualities)
        description += f"with average quality {avg_quality:.2f}."

        example_hits_data = hits[:3]
        snippet_examples = []
        for h_ex in example_hits_data:
            a_disp, b_disp, c_disp = h_ex.get('a', '?'), h_ex.get('b', '?'), h_ex.get('c', '?')
            snippet_examples.append(f"({a_disp}, {b_disp}, {c_disp})")

        snippet = f"Examples: {', '.join(snippet_examples)}" if snippet_examples else "No displayable examples."

        return ScientificConcept(
            name=f"ABC Pattern: {pattern_name.replace('_', ' ').title()}",
            description=description,
            type=ConceptType.UCM,
            properties={
                "pattern_type": pattern_name,
                "support_count": len(hits),
                "average_quality": avg_quality,
                "experiment_id": input_data.experiment_id,
                "extraction_method": "abc_pattern_analysis"
            },
            evidence_sources=[
                Evidence(
                    source_doi=f"aletheia:experiment/{input_data.experiment_id}",
                    source_citation=f"Aletheia ABC Search Experiment {input_data.experiment_id}",
                    snippet=snippet,
                    confidence=min(0.9, len(hits) / 10.0)
                )
            ],
            verification_hash=hex(hash(pattern_name + str(input_data.experiment_id)))[2:12]
        )

    def _extract_parameter_insights(
        self, parameters: Dict[str, Any], experiment_id: str
    ) -> List[ScientificConcept]:
        insights: List[ScientificConcept] = []
        quality_found_orig = parameters.get('quality_found', 0.0)
        quality_found = float(quality_found_orig) if isinstance(quality_found_orig, (int, float)) else 0.0

        if parameters.get('use_custom_acquisition') and quality_found > 500:
            insight = ScientificConcept(
                name="Effective Search Strategy: Structural Bonus",
                description=f"Custom acquisition function with structural bonus yielded high-quality results in experiment {experiment_id}",
                type=ConceptType.UCM,
                properties={
                    "strategy_type": "custom_acquisition",
                    "effectiveness": quality_found / 100.0,
                    "experiment_id": experiment_id
                },
                evidence_sources=[
                    Evidence(
                        source_doi=f"aletheia:experiment/{experiment_id}",
                        source_citation=f"Search strategy analysis from experiment {experiment_id}",
                        snippet=f"Quality achieved: {quality_found}",
                        confidence=0.8
                    )
                ],
                verification_hash=hex(hash("structural_bonus_strategy" + str(experiment_id)))[2:12]
            )
            insights.append(insight)
        return insights

    def _is_prime(self, num: int) -> bool:
        if num < 2: return False
        for i in range(2, int(math.sqrt(num)) + 1):
            if num % i == 0: return False
        return True

    def _is_prime_power(self, n: int) -> bool:
        if not isinstance(n, int) or n < 2: return False
        if self._is_prime(n): return True
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                if self._is_prime(i):
                    temp = n
                    while temp > 0 and temp % i == 0: # ensure temp > 0
                        temp //= i
                    if temp == 1: return True
        return False


class SynthesisGuidedSearchStrategy:
    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo

    def get_search_recommendations(self) -> Dict[str, Any]:
        recommendations: Dict[str, Any] = {"parameter_suggestions": {}, "focus_areas": [], "avoid_areas": []}
        all_concepts = self.concept_repo.list_all()
        unified_models = [c for c in all_concepts if c.type == ConceptType.UNIFIED_MODEL]

        for model in unified_models: # Iterate directly, no need for if unified_models check before loop
            if model.properties and "architecture_details" in model.properties:
                self._extract_parameter_recommendations(model, recommendations)

        pattern_ucms = [
            c for c in all_concepts
            if c.type == ConceptType.UCM and c.properties and "pattern_type" in c.properties
        ]
        for ucm in pattern_ucms:
            avg_quality_orig = ucm.properties.get("average_quality", 0.0)
            avg_quality = float(avg_quality_orig) if isinstance(avg_quality_orig, (int, float)) else 0.0
            if avg_quality > 1000:
                recommendations["focus_areas"].append({
                    "pattern": ucm.properties["pattern_type"],
                    "reasoning": f"High average quality: {avg_quality}"
                })
        return recommendations

    def _extract_parameter_recommendations(
        self, model: ScientificConcept, recommendations: Dict[str, Any]
    ):
        if not model.properties: return

        total_coverage = model.properties.get("total_coverage", {})
        estimated_ucms_orig = total_coverage.get("estimated_ucms", 0)
        estimated_ucms = int(estimated_ucms_orig) if isinstance(estimated_ucms_orig, (int, float)) else 0

        if estimated_ucms > 50:
            recommendations["parameter_suggestions"]["n_trials"] = recommendations["parameter_suggestions"].get("n_trials", 10000)
            recommendations["parameter_suggestions"]["exploration_factor"] = recommendations["parameter_suggestions"].get("exploration_factor", 0.3)

        model_content_str = str(model.name) + str(model.description) + str(model.properties)
        if "high_quality_pattern" in model_content_str:
             recommendations["parameter_suggestions"]["use_custom_acquisition"] = recommendations["parameter_suggestions"].get("use_custom_acquisition", True)

        architecture_type_val = model.properties.get("architecture_type")
        if architecture_type_val in [ModelArchitectureType.NETWORKED.value, ModelArchitectureType.HYBRID.value]: # Check against .value
            recommendations["parameter_suggestions"]["n_iterations_bayes_opt"] = recommendations["parameter_suggestions"].get("n_iterations_bayes_opt", 100)

        if model.member_concept_ids:
            for theory_id_uuid in model.member_concept_ids:
                theory = self.concept_repo.get_by_id(theory_id_uuid)
                if theory and theory.properties and \
                   theory.properties.get("integration_method") == TheoryIntegrationMethod.DIALECTICAL_SYNTHESIS.value: # Check against .value
                    recommendations["parameter_suggestions"]["novelty_weight"] = recommendations["parameter_suggestions"].get("novelty_weight", 0.75)
                    break
