"""
Temporary location for use case definitions to make them accessible to tests
in this sandboxed environment.
"""
import uuid
import re
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional
from enum import Enum # Added Enum
from pydantic import BaseModel, Field

# Adjust import for domain models from their temporary test location
from tests.domain.domain_for_test import (
    ScientificConcept,
    Evidence,
    ConceptType,
    TheoryIntegrationMethod,
    ModelArchitectureType
)

# Import repository protocols from their temporary test location
from tests.application.ports.ports_for_test import ConceptRepository, RelationshipRepository


class CreateConceptInput(BaseModel):
    name: str
    description: str
    type: ConceptType
    properties: Dict[str, Any] = {}
    evidence_sources: List[Evidence] = []


class KnowledgeSynthesisUseCase:
    """
    Orchestrates the creation and retrieval of knowledge graph components.
    """
    def __init__(
        self,
        concept_repo: ConceptRepository,
        relationship_repo: RelationshipRepository
    ):
        self.concept_repo = concept_repo
        self.relationship_repo = relationship_repo

    def create_concept(self, input_data: CreateConceptInput) -> ScientificConcept:
        concept = ScientificConcept(
            name=input_data.name,
            description=input_data.description,
            type=input_data.type,
            properties=input_data.properties,
            evidence_sources=input_data.evidence_sources,
        )
        self.concept_repo.add(concept)
        return concept

    def get_all_concepts(self) -> List[ScientificConcept]:
        return self.concept_repo.list_all()

    def get_concept_details(self, concept_id: uuid.UUID) -> ScientificConcept:
        concept = self.concept_repo.get_by_id(concept_id)
        if not concept:
            raise ValueError(f"Concept with ID {concept_id} not found.")
        return concept


# --- Use Cases for Eje Y (Progressive Construction) ---

class ExtractUCMsInput(BaseModel):
    document_text: str
    source_doi: str
    source_citation: str

class UCMExtractionResult(BaseModel):
    ucms_created: List[ScientificConcept]

class ExtractUCMsUseCase:
    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo
        self.stopwords = {"the", "is", "an", "a", "of", "to", "in", "and", "it", "this", "that",
                          "another", "later", "but", "also", "key", "factor", "was", "were", "has", "had",
                          "may", "can", "could", "should", "would", "might"}


    def _is_covered(self, word_cand:str, start_idx: int, end_idx: int, covered_spans: List[tuple[int, int]]) -> bool:
        for cs, ce in covered_spans:
            if cs <= start_idx and end_idx <= ce:
                 return True
        return False

    def _clean_phrase(self, phrase: str) -> str:
        words = phrase.split()
        while words and words[0].lower() in self.stopwords:
            words.pop(0)
        while words and words[-1].lower() in self.stopwords:
            words.pop()

        cleaned_phrase = " ".join(words)
        if not cleaned_phrase or len(cleaned_phrase) < 3:
            return ""
        if cleaned_phrase.lower() in self.stopwords and len(cleaned_phrase.split()) == 1:
            return ""
        return cleaned_phrase


    def execute(self, input_data: ExtractUCMsInput) -> UCMExtractionResult:
        ucms_created = []
        sentences = re.split(r'(?<=[.!?])\s+', input_data.document_text)
        extracted_candidate_names = set()

        phrase_regex = r'\b(?:[A-Z][a-zA-Z0-9_"\'-]*\s+){1,5}[A-Z][a-zA-Z0-9_"\'-]*\b'
        single_word_regex = r'\b[A-Z][a-zA-Z0-9_"\'-]+\b'

        for sentence_idx, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            current_sentence_covered_spans: List[tuple[int, int]] = []

            for match in re.finditer(phrase_regex, sentence):
                phrase_candidate = match.group(0).strip()
                cleaned_phrase = self._clean_phrase(phrase_candidate)

                if not cleaned_phrase: continue

                current_sentence_covered_spans.append(match.span())

                if cleaned_phrase not in extracted_candidate_names:
                    verification_hash = hex(hash(cleaned_phrase + input_data.source_doi))[2:]
                    description = f"UCM (phrase) extracted from: '{sentence[:100]}...'"
                    ucm = ScientificConcept(
                        name=cleaned_phrase, description=description, type=ConceptType.UCM,
                        properties={"extraction_method": "regex_capitalized_multi_word_phrase_v4", "original_phrase": phrase_candidate, "original_sentence_index": sentence_idx},
                        evidence_sources=[Evidence(source_doi=input_data.source_doi, source_citation=input_data.source_citation, snippet=sentence, confidence=0.70)],
                        verification_hash=verification_hash)
                    self.concept_repo.add(ucm)
                    ucms_created.append(ucm)
                    extracted_candidate_names.add(cleaned_phrase)

            for match in re.finditer(single_word_regex, sentence):
                word_cand = match.group(0).strip()

                if self._is_covered(word_cand, match.start(), match.end(), current_sentence_covered_spans):
                    continue

                cleaned_word = self._clean_phrase(word_cand)

                if not cleaned_word:
                    continue

                if len(cleaned_word) < 3 or cleaned_word.lower() in self.stopwords:
                    continue

                if cleaned_word not in extracted_candidate_names:
                    verification_hash = hex(hash(cleaned_word + input_data.source_doi))[2:]
                    description = f"UCM (single word) extracted from: '{sentence[:100]}...'"
                    ucm = ScientificConcept(
                        name=cleaned_word, description=description, type=ConceptType.UCM,
                        properties={"extraction_method": "regex_capitalized_single_word_v4", "original_word": word_cand, "original_sentence_index": sentence_idx},
                        evidence_sources=[Evidence(source_doi=input_data.source_doi, source_citation=input_data.source_citation, snippet=sentence, confidence=0.60)],
                        verification_hash=verification_hash)
                    self.concept_repo.add(ucm)
                    ucms_created.append(ucm)
                    extracted_candidate_names.add(cleaned_word)

        return UCMExtractionResult(ucms_created=ucms_created)


class FormClusterInput(BaseModel):
    ucm_ids: List[uuid.UUID]
    cluster_name: Optional[str] = "Unnamed Cluster"
    cluster_description: Optional[str] = "A cluster formed from selected UCMs."

class ClusterFormationResult(BaseModel):
    cluster_created: ScientificConcept

class FormClustersUseCase:
    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo

    def execute(self, input_data: FormClusterInput) -> ClusterFormationResult:
        member_ucms = []
        for ucm_id in input_data.ucm_ids:
            ucm = self.concept_repo.get_by_id(ucm_id)
            if not ucm or ucm.type != ConceptType.UCM:
                raise ValueError(f"Invalid or non-UCM concept ID provided: {ucm_id}")
            member_ucms.append(ucm)

        if not member_ucms:
            raise ValueError("No UCMs provided to form a cluster.")

        all_keywords = []
        stopwords_cluster = {"the", "a", "an", "is", "of", "to", "in", "and", "for", "with", "on", "it", "this", "that", "was", "were", "has", "had", "not", "but"}

        for ucm in member_ucms:
            text_to_process = (ucm.name + " " + ucm.description).lower()
            words = re.findall(r'\b\w+\b', text_to_process)
            keywords = [word for word in words if word not in stopwords_cluster and len(word) > 2]
            all_keywords.extend(keywords)

        common_keywords = [kw for kw, count in Counter(all_keywords).most_common(5)]

        default_name_from_model = FormClusterInput.model_fields["cluster_name"].default
        default_desc_from_model = FormClusterInput.model_fields["cluster_description"].default

        final_cluster_name = input_data.cluster_name
        if final_cluster_name is None or final_cluster_name == default_name_from_model:
            if common_keywords:
                final_cluster_name = f"Cluster: {', '.join(common_keywords[:3])}"
            elif member_ucms:
                 final_cluster_name = f"Cluster of {len(member_ucms)} UCMs ({member_ucms[0].name[:20]}...)"
            else:
                 final_cluster_name = str(default_name_from_model)

        final_cluster_description = input_data.cluster_description
        if final_cluster_description is None or final_cluster_description == default_desc_from_model:
            if common_keywords:
                final_cluster_description = f"Conceptual cluster related to: {', '.join(common_keywords)}. Contains {len(member_ucms)} UCMs."
            elif member_ucms:
                final_cluster_description = f"A conceptual cluster containing {len(member_ucms)} UCMs, including '{member_ucms[0].name}'."
            else:
                final_cluster_description = str(default_desc_from_model)

        cluster_properties = {
            "ucm_count": len(input_data.ucm_ids),
            "common_keywords": common_keywords,
            "formation_method": "basic_keyword_aggregation_v2"
        }

        cluster = ScientificConcept(
            name=final_cluster_name,
            description=final_cluster_description,
            type=ConceptType.CLUSTER,
            properties=cluster_properties,
            member_concept_ids=input_data.ucm_ids,
            evidence_sources=[
                Evidence(
                    source_doi="internal_process:cluster_formation_v2",
                    source_citation="Aletheia System",
                    snippet=f"Cluster formed from {len(input_data.ucm_ids)} UCMs based on keyword co-occurrence analysis (simulated).",
                    confidence=0.65
                )
            ]
        )
        self.concept_repo.add(cluster)
        return ClusterFormationResult(cluster_created=cluster)


class DerivePropositionInput(BaseModel):
    cluster_id: uuid.UUID
    proposition_text: Optional[str] = None

class PropositionDerivationResult(BaseModel):
    proposition_created: ScientificConcept

class DerivePropositionsUseCase:
    def __init__(self, concept_repo: ConceptRepository, relationship_repo: RelationshipRepository):
        self.concept_repo = concept_repo
        self.relationship_repo = relationship_repo

    def execute(self, input_data: DerivePropositionInput) -> PropositionDerivationResult:
        cluster = self.concept_repo.get_by_id(input_data.cluster_id)
        if not cluster or cluster.type != ConceptType.CLUSTER:
            raise ValueError(f"Invalid or non-CLUSTER concept ID provided for proposition derivation: {input_data.cluster_id}")

        member_ucms_for_prop = []
        if cluster.member_concept_ids:
            for ucm_id in cluster.member_concept_ids:
                ucm = self.concept_repo.get_by_id(ucm_id)
                if ucm and ucm.type == ConceptType.UCM:
                    member_ucms_for_prop.append(ucm)

        derived_keywords_for_prop = []
        if member_ucms_for_prop:
            all_prop_keywords = []
            stopwords_prop = {"the", "a", "an", "is", "of", "to", "in", "and", "for", "with", "on", "it", "this", "that", "was", "were", "has", "had", "not", "but"}
            for ucm_obj in member_ucms_for_prop:
                text_to_process = (ucm_obj.name + " " + ucm_obj.description).lower()
                words = re.findall(r'\b\w+\b', text_to_process)
                keywords = [word for word in words if word not in stopwords_prop and len(word) > 2]
                all_prop_keywords.extend(keywords)
            derived_keywords_for_prop = [kw for kw, count in Counter(all_prop_keywords).most_common(3)]

        proposition_name = input_data.proposition_text
        if proposition_name is None:
            if derived_keywords_for_prop:
                proposition_name = f"Hypothesized Link: {', '.join(derived_keywords_for_prop)} in {cluster.name}"
            else:
                proposition_name = f"General Proposition regarding {cluster.name}"

        proposition_name = proposition_name[:250]

        description = f"This proposition, '{proposition_name}', emerges from conceptual cluster '{cluster.name}' (ID: {cluster.id})."
        if member_ucms_for_prop:
            description += f" Key concepts from cluster members considered: {', '.join([ucm.name for ucm in member_ucms_for_prop[:3]])}..."
        elif cluster.member_concept_ids:
             description += f" The cluster is associated with {len(cluster.member_concept_ids)} concept ID(s)."
        else:
            description += " The cluster currently has no specified member UCMs."

        proposition = ScientificConcept(
            name=proposition_name,
            description=description,
            type=ConceptType.PROPOSITION,
            derived_from_cluster_id=input_data.cluster_id,
            derived_from_ucm_ids=cluster.member_concept_ids if cluster.member_concept_ids else [],
            properties={
                "derivation_method": "keyword_based_heuristic_v2",
                "key_cluster_keywords_for_prop": derived_keywords_for_prop
            },
            evidence_sources=[
                Evidence(
                    source_doi="internal_process:proposition_derivation_v2",
                    source_citation="Aletheia System",
                    snippet=f"Proposition heuristically derived from cluster {cluster.id} and its members.",
                    confidence=0.6
                )
            ]
        )
        self.concept_repo.add(proposition)
        return PropositionDerivationResult(proposition_created=proposition)


# --- Use Case for Mini-Theory Construction (Eje Y - Level 2) ---

class ConstructMiniTheoryInput(BaseModel):
    proposition_ids: List[uuid.UUID]
    mini_theory_name: Optional[str] = None
    mini_theory_description: Optional[str] = "A synthesized mini-theory based on selected propositions."
    derivation_method_description: Optional[str] = "heuristic_proposition_grouping"

class MiniTheoryConstructionResult(BaseModel):
    mini_theory_created: ScientificConcept

class ConstructMiniTheoryUseCase:
    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo
        self.stopwords = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "in",
                          "and", "or", "but", "for", "with", "on", "at", "by", "from"}

    def execute(self, input_data: ConstructMiniTheoryInput) -> MiniTheoryConstructionResult:
        if not input_data.proposition_ids:
             raise ValueError("At least one proposition ID must be provided.")

        component_propositions = []
        for prop_id in input_data.proposition_ids:
            proposition = self.concept_repo.get_by_id(prop_id)
            if not proposition or proposition.type != ConceptType.PROPOSITION:
                raise ValueError(f"Invalid or non-PROPOSITION concept ID provided: {prop_id}")
            component_propositions.append(proposition)

        name = input_data.mini_theory_name
        if name is None:
            if component_propositions:
                first_prop_name_part = component_propositions[0].name.split(':')[0]
                name = f"Mini-Theory on: {first_prop_name_part[:50]}..."
            else:
                name = "Unnamed Mini-Theory"

        description = input_data.mini_theory_description
        if description == ConstructMiniTheoryInput.model_fields["mini_theory_description"].default and component_propositions:
            description = f"A mini-theory synthesizing {len(component_propositions)} proposition(s), including insights like '{component_propositions[0].name[:70]}...'."

        final_description = description if description is not None else "Synthesized mini-theory."

        mini_theory = ScientificConcept(
            name=name,
            description=final_description,
            type=ConceptType.MINI_THEORY,
            member_concept_ids=input_data.proposition_ids,
            properties={
                "derivation_method": input_data.derivation_method_description or "heuristic_proposition_grouping",
                "component_proposition_count": len(input_data.proposition_ids)
            },
            evidence_sources=[
                Evidence(
                    source_doi="internal_process:mini_theory_construction",
                    source_citation="Aletheia System - Level 3 Synthesis", # Should be Level 2
                    snippet=f"Mini-theory constructed from {len(input_data.proposition_ids)} propositions.",
                    confidence=0.8
                )
            ]
        )
        self.concept_repo.add(mini_theory)
        return MiniTheoryConstructionResult(mini_theory_created=mini_theory)

# --- Use Case for Comprehensive Theory Construction (Eje Y - Level 3 Part 1) ---

class ConstructComprehensiveTheoryInput(BaseModel):
    """Input DTO for comprehensive theory construction."""
    mini_theory_ids: List[uuid.UUID] = Field(
        ...,
        min_length=1,
        description="At least 1 mini-theory is required for synthesis"
    )
    theory_name: Optional[str] = None
    theory_description: Optional[str] = None
    integration_method: TheoryIntegrationMethod = TheoryIntegrationMethod.COMPLEMENTARY_SYNTHESIS
    integration_rationale: Optional[str] = None


class ComprehensiveTheoryResult(BaseModel):
    """Result of comprehensive theory construction."""
    theory_created: ScientificConcept
    integration_analysis: Optional[Dict[str, Any]] = None


class ConstructComprehensiveTheoryUseCase:
    """
    Constructs a Comprehensive Theory (TC) by integrating multiple Mini-Theories.
    """

    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo
        self.stopwords = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "in",
                          "and", "or", "but", "for", "with", "on", "at", "by", "from"}

    def execute(self, input_data: ConstructComprehensiveTheoryInput) -> ComprehensiveTheoryResult:
        if not input_data.mini_theory_ids:
             raise ValueError("At least one mini-theory ID must be provided.")

        mini_theories = self._retrieve_and_validate_mini_theories(input_data.mini_theory_ids)

        compatibility_analysis = None
        if len(mini_theories) > 1:
            compatibility_analysis = self._analyze_theory_compatibility(mini_theories)

        common_themes = self._extract_common_themes(mini_theories)

        theory_name = input_data.theory_name or self._generate_theory_name(
            mini_theories, common_themes
        )
        theory_description = input_data.theory_description or self._generate_theory_description(
            mini_theories, common_themes, compatibility_analysis
        )

        integration_properties = {
            "integration_method": input_data.integration_method.value,
            "integration_rationale": input_data.integration_rationale or (self._generate_integration_rationale(
                compatibility_analysis, input_data.integration_method
            ) if compatibility_analysis else "N/A for single component"),
            "component_mini_theory_count": len(mini_theories),
            "common_themes": common_themes,
            "compatibility_score": compatibility_analysis["overall_compatibility"] if compatibility_analysis else 1.0,
            "theoretical_coverage": self._calculate_theoretical_coverage(mini_theories),
            "synthesis_timestamp": str(uuid.uuid4())[:12]
        }

        comprehensive_theory = ScientificConcept(
            name=theory_name[:255],
            description=theory_description,
            type=ConceptType.COMPREHENSIVE_THEORY,
            member_concept_ids=input_data.mini_theory_ids,
            properties=integration_properties,
            evidence_sources=[
                Evidence(
                    source_doi="internal_process:comprehensive_theory_synthesis",
                    source_citation="Aletheia System - Level 3 Synthesis",
                    snippet=f"Comprehensive theory synthesized from {len(mini_theories)} mini-theories using {input_data.integration_method.value} method.",
                    confidence=0.75
                )
            ]
        )

        self.concept_repo.add(comprehensive_theory)

        return ComprehensiveTheoryResult(
            theory_created=comprehensive_theory,
            integration_analysis=compatibility_analysis
        )

    def _retrieve_and_validate_mini_theories(
        self, mini_theory_ids: List[uuid.UUID]
    ) -> List[ScientificConcept]:
        mini_theories = []
        for mt_id in mini_theory_ids:
            concept = self.concept_repo.get_by_id(mt_id)
            if not concept or concept.type != ConceptType.MINI_THEORY:
                raise ValueError(f"Invalid or non-MINI_THEORY concept ID: {mt_id}")
            mini_theories.append(concept)
        return mini_theories

    def _analyze_theory_compatibility(
        self, mini_theories: List[ScientificConcept]
    ) -> Dict[str, Any]:
        if len(mini_theories) < 2:
            return {"overall_compatibility": 1.0, "integration_feasibility": "high", "compatibility_matrix": {}, "shared_keywords": {}}

        compatibility_matrix = {}
        shared_keywords_counts = {}

        for i, mt1 in enumerate(mini_theories):
            for j, mt2 in enumerate(mini_theories[i+1:], start=i+1):
                keywords1 = set(self._extract_keywords_from_theory(mt1))
                keywords2 = set(self._extract_keywords_from_theory(mt2))

                shared = keywords1.intersection(keywords2)
                total = keywords1.union(keywords2)
                compatibility = len(shared) / len(total) if total else 0

                key = f"{str(mt1.id)[:8]}_{str(mt2.id)[:8]}"
                compatibility_matrix[key] = compatibility
                shared_keywords_counts[key] = list(shared)

        overall_compatibility = (
            sum(compatibility_matrix.values()) / len(compatibility_matrix)
            if compatibility_matrix else 0.0
        )

        return {
            "compatibility_matrix": compatibility_matrix,
            "shared_keywords": shared_keywords_counts,
            "overall_compatibility": overall_compatibility,
            "integration_feasibility": "high" if overall_compatibility > 0.6 else (
                "medium" if overall_compatibility > 0.3 else "low"
            )
        }

    def _extract_keywords_from_theory(self, theory: ScientificConcept) -> List[str]:
        keywords = []
        text_content = f"{theory.name} {theory.description}".lower()

        if theory.properties:
            if "common_keywords" in theory.properties and isinstance(theory.properties["common_keywords"], list):
                text_content += " " + " ".join(theory.properties["common_keywords"])
            if "key_cluster_keywords_for_prop" in theory.properties and isinstance(theory.properties["key_cluster_keywords_for_prop"], list):
                 text_content += " " + " ".join(theory.properties["key_cluster_keywords_for_prop"])

        words = re.findall(r'\b\w+\b', text_content)
        keywords.extend([w for w in words if w not in self.stopwords and len(w) > 2])
        return list(set(keywords))

    def _extract_common_themes(
        self, mini_theories: List[ScientificConcept]
    ) -> List[str]:
        all_keywords = []
        for mt in mini_theories:
            all_keywords.extend(self._extract_keywords_from_theory(mt))
        return [theme for theme, _ in Counter(all_keywords).most_common(5)]

    def _generate_theory_name(
        self, mini_theories: List[ScientificConcept], common_themes: List[str]
    ) -> str:
        if common_themes:
            return f"Comprehensive Theory of {', '.join(common_themes[:2]).title()}"
        elif mini_theories:
            return f"Integrated Theory from {mini_theories[0].name[:30]}..."
        return "Integrated Theory"

    def _generate_theory_description(
        self,
        mini_theories: List[ScientificConcept],
        common_themes: List[str],
        compatibility_analysis: Optional[Dict[str, Any]]
    ) -> str:
        desc = f"This comprehensive theory integrates {len(mini_theories)} mini-theories"
        if common_themes:
            desc += f" addressing common themes of {', '.join(common_themes[:3])}"

        if compatibility_analysis:
            desc += f". The integration shows {compatibility_analysis['integration_feasibility']} feasibility"
            desc += f" with an overall compatibility score of {compatibility_analysis['overall_compatibility']:.2f}."

        mt_names = [mt.name[:30] + ("..." if len(mt.name)>30 else "") for mt in mini_theories[:2]]
        if mt_names:
            desc += f" Key components include: {', '.join(mt_names)}"
            if len(mini_theories) > 2:
                desc += f" and {len(mini_theories) - 2} other(s)."
        return desc

    def _generate_integration_rationale(
        self,
        compatibility_analysis: Optional[Dict[str, Any]],
        method: TheoryIntegrationMethod
    ) -> str:
        feasibility = compatibility_analysis["integration_feasibility"] if compatibility_analysis and "integration_feasibility" in compatibility_analysis else "unknown"

        method_value = method.value if isinstance(method, Enum) else method

        if method_value == TheoryIntegrationMethod.COMPLEMENTARY_SYNTHESIS.value:
            return f"Theories show {feasibility} compatibility and complement each other."
        elif method_value == TheoryIntegrationMethod.DIALECTICAL_SYNTHESIS.value:
            return f"Despite {feasibility} direct compatibility, dialectical synthesis resolves apparent contradictions."
        elif method_value == TheoryIntegrationMethod.SUBSUMPTION.value:
            return f"One theory subsumes others based on broader explanatory power."
        elif method_value == TheoryIntegrationMethod.HIERARCHICAL_INTEGRATION.value:
            return f"Theories are integrated hierarchically with {feasibility} structural compatibility."
        else:
            return f"Theories integrated using {method_value} based on {feasibility} feasibility."

    def _calculate_theoretical_coverage(
        self, mini_theories: List[ScientificConcept]
    ) -> Dict[str, int]:
        unique_propositions = set()
        for mt in mini_theories:
            if mt.member_concept_ids:
                unique_propositions.update(mt.member_concept_ids)

        estimated_ucm_count = 0
        for prop_id in unique_propositions:
            prop = self.concept_repo.get_by_id(prop_id)
            if prop:
                if prop.derived_from_ucm_ids:
                    estimated_ucm_count += len(prop.derived_from_ucm_ids)
                elif prop.derived_from_cluster_id:
                    cluster = self.concept_repo.get_by_id(prop.derived_from_cluster_id)
                    if cluster and cluster.member_concept_ids:
                        estimated_ucm_count += len(cluster.member_concept_ids)
        return {
            "proposition_count": len(unique_propositions),
            "estimated_distinct_ucm_coverage": estimated_ucm_count
        }

# --- Use Case for Unified Model Construction (Eje Y - Level 3 Part 2) ---

class ConstructUnifiedModelInput(BaseModel):
    """Input DTO for unified model construction."""
    comprehensive_theory_ids: List[uuid.UUID] = Field(
        ...,
        min_length=1,
        description="At least 1 comprehensive theory is required"
    )
    model_name: Optional[str] = None
    model_description: Optional[str] = None
    architecture_type: ModelArchitectureType = ModelArchitectureType.MODULAR
    formalization_level: str = Field(
        default="conceptual",
        description="Level of mathematical formalization: conceptual, semi-formal, formal"
    )

class UnifiedModelResult(BaseModel):
    """Result of unified model construction."""
    model_created: ScientificConcept
    model_metrics: Dict[str, Any]
    architecture_diagram: Dict[str, Any]


class ConstructUnifiedModelUseCase:
    """
    Constructs a Unified Model (MU) by integrating Comprehensive Theories.
    """

    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo

    def execute(self, input_data: ConstructUnifiedModelInput) -> UnifiedModelResult:
        comp_theories = self._retrieve_and_validate_theories(
            input_data.comprehensive_theory_ids
        )

        landscape_analysis = self._analyze_theory_landscape(comp_theories)

        architecture = self._design_model_architecture(
            comp_theories,
            input_data.architecture_type,
            landscape_analysis
        )

        model_metrics = self._calculate_model_metrics(comp_theories, architecture)

        model_name = input_data.model_name or self._generate_model_name(
            comp_theories, architecture
        )
        model_description = input_data.model_description or self._generate_model_description(
            comp_theories, architecture, model_metrics
        )

        formalization = self._create_formalization_structure(
            input_data.formalization_level,
            architecture,
            comp_theories
        )

        unified_model = ScientificConcept(
            name=model_name[:255],
            description=model_description,
            type=ConceptType.UNIFIED_MODEL,
            member_concept_ids=input_data.comprehensive_theory_ids,
            properties={
                "architecture_type": input_data.architecture_type.value,
                "formalization_level": input_data.formalization_level,
                "formalization_details": formalization,
                "model_metrics": model_metrics,
                "component_theory_count": len(comp_theories),
                "total_knowledge_coverage": self._calculate_total_coverage(comp_theories),
                "architecture_details": architecture,
                "synthesis_method": "hypercubic_integration_v1",
                "model_version": "1.0.0"
            },
            evidence_sources=[
                Evidence(
                    source_doi="internal_process:unified_model_synthesis",
                    source_citation="Aletheia System - Model Unification",
                    snippet=f"Unified model synthesized from {len(comp_theories)} comprehensive theories using {input_data.architecture_type.value} architecture.",
                    confidence=0.85
                )
            ]
        )

        self.concept_repo.add(unified_model)

        return UnifiedModelResult(
            model_created=unified_model,
            model_metrics=model_metrics,
            architecture_diagram=architecture
        )

    def _retrieve_and_validate_theories(
        self, theory_ids: List[uuid.UUID]
    ) -> List[ScientificConcept]:
        theories = []
        for theory_id in theory_ids:
            concept = self.concept_repo.get_by_id(theory_id)
            if not concept or concept.type != ConceptType.COMPREHENSIVE_THEORY:
                raise ValueError(
                    f"Invalid or non-COMPREHENSIVE_THEORY concept ID: {theory_id}"
                )
            theories.append(concept)
        return theories

    def _analyze_theory_landscape(
        self, theories: List[ScientificConcept]
    ) -> Dict[str, Any]:
        all_themes = []
        integration_methods = []

        for theory in theories:
            if theory.properties and "common_themes" in theory.properties:
                all_themes.extend(theory.properties["common_themes"])
            if theory.properties and "integration_method" in theory.properties:
                integration_methods.append(theory.properties["integration_method"])

        theme_clusters = defaultdict(list)
        for i, theory in enumerate(theories):
            theory_themes = theory.properties.get("common_themes", []) if theory.properties else []
            for theme in theory_themes:
                theme_clusters[theme].append(str(theory.id))

        return {
            "dominant_themes": [(theme, count) for theme, count in Counter(all_themes).most_common(5)],
            "integration_methods_used": [(method, count) for method, count in Counter(integration_methods).most_common()],
            "theme_clusters": dict(theme_clusters),
            "theory_connectivity_by_theme": len([v for v in theme_clusters.values() if len(v) > 1])
        }

    def _design_model_architecture(
        self,
        theories: List[ScientificConcept],
        architecture_type: ModelArchitectureType,
        landscape: Dict[str, Any]
    ) -> Dict[str, Any]:
        arch_type_value = architecture_type.value if isinstance(architecture_type, Enum) else architecture_type

        if arch_type_value == ModelArchitectureType.MODULAR.value:
            return self._design_modular_architecture(theories, landscape)
        elif arch_type_value == ModelArchitectureType.LAYERED.value:
            return self._design_layered_architecture(theories, landscape)
        elif arch_type_value == ModelArchitectureType.NETWORKED.value:
            return self._design_networked_architecture(theories, landscape)
        elif arch_type_value == ModelArchitectureType.HIERARCHICAL.value:
            return self._design_hierarchical_architecture(theories, landscape)
        else:
            return self._design_hybrid_architecture(theories, landscape)

    def _design_modular_architecture(
        self, theories: List[ScientificConcept], landscape: Dict[str, Any]
    ) -> Dict[str, Any]:
        modules = []
        dominant_themes_list = [theme_tuple[0] for theme_tuple in landscape.get("dominant_themes", [])]
        for i, theory in enumerate(theories):
            module_interfaces = []
            theory_themes = theory.properties.get("common_themes", []) if theory.properties else []
            for theme in theory_themes:
                if theme in dominant_themes_list:
                    module_interfaces.append(f"I_{theme[:10].replace(' ','_')}")

            modules.append({
                "module_id": f"M{i+1}", "theory_id": str(theory.id),
                "name": theory.name[:50], "interfaces": list(set(module_interfaces)), "dependencies": []
            })

        return {
            "type": ModelArchitectureType.MODULAR.value, "modules": modules,
            "connectors": self._generate_module_connectors(modules),
            "core_interfaces": list(set([f"I_{theme_tuple[0][:10].replace(' ','_')}" for theme_tuple in dominant_themes_list[:3]]))
        }

    def _design_layered_architecture(
        self, theories: List[ScientificConcept], landscape: Dict[str, Any]
    ) -> Dict[str, Any]:
        layers: Dict[str, List[Dict[str,str]]] = { "foundational": [], "intermediate": [], "application": [] }
        for i, theory in enumerate(theories):
            layer_keys = list(layers.keys())
            layers[layer_keys[i % len(layer_keys)]].append({"theory_id": str(theory.id), "name": theory.name})
        return {
            "type": ModelArchitectureType.LAYERED.value, "layers": layers,
            "layer_dependencies": {"application": ["intermediate"], "intermediate": ["foundational"], "foundational": []}
        }

    def _design_networked_architecture(
        self, theories: List[ScientificConcept], landscape: Dict[str, Any]
    ) -> Dict[str, Any]:
        nodes = [{"id": str(t.id), "name": t.name[:30]} for t in theories]
        edges = []
        theme_clusters = landscape.get("theme_clusters", {})
        for theme, theory_id_list_for_theme in theme_clusters.items():
            if len(theory_id_list_for_theme) > 1:
                for i in range(len(theory_id_list_for_theme)):
                    for j in range(i + 1, len(theory_id_list_for_theme)):
                        edges.append({
                            "source": theory_id_list_for_theme[i],
                            "target": theory_id_list_for_theme[j],
                            "theme": theme,
                            "weight": 0.5
                        })
        return {
            "type": ModelArchitectureType.NETWORKED.value, "nodes": nodes, "edges": edges,
            "central_themes": [t_name for t_name, t_count in landscape.get("dominant_themes", [])[:3]]
        }

    def _design_hierarchical_architecture(
        self, theories: List[ScientificConcept], landscape: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not theories: return {"type": ModelArchitectureType.HIERARCHICAL.value, "root": None, "tree": {}}

        root: Dict[str, Any] = {"id": str(theories[0].id), "name": theories[0].name[:30], "children": []}
        current_parent: Dict[str, Any] = root

        for i, theory in enumerate(theories[1:]):
            child_node: Dict[str, Any] = {"id": str(theory.id), "name": theory.name[:30], "children": []}
            if i % 2 == 0 and current_parent["children"]:
                current_parent = current_parent["children"][-1]
            # Ensure current_parent["children"] is treated as a list
            ((current_parent["children"] if isinstance(current_parent["children"], list) else [])).append(child_node)

        return {"type": ModelArchitectureType.HIERARCHICAL.value, "root": root, "depth": 3, "branching_factor": "variable"}

    def _design_hybrid_architecture(
        self, theories: List[ScientificConcept], landscape: Dict[str, Any]
    ) -> Dict[str, Any]:
        core_theories = theories[:len(theories)//2] if len(theories)>1 else theories
        extension_theories = theories[len(theories)//2:] if len(theories)>1 else []

        return {
            "type": ModelArchitectureType.HYBRID.value,
            "components": {
                "modular_core": self._design_modular_architecture(core_theories, landscape) if core_theories else None,
                "networked_extensions": self._design_networked_architecture(extension_theories, landscape) if extension_theories else None
            },
            "integration_points": [f"IP_{i+1}" for i in range(min(1, len(theories)))]
        }

    def _generate_module_connectors(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        connectors = []
        for i, mod1 in enumerate(modules):
            for j, mod2 in enumerate(modules[i+1:]):
                if mod1.get("interfaces") and mod2.get("interfaces"):
                    shared_interfaces = set(mod1["interfaces"]) & set(mod2["interfaces"])
                    if shared_interfaces:
                        connectors.append({
                            "from": mod1["module_id"], "to": mod2["module_id"],
                            "via_interfaces": list(shared_interfaces)
                        })
        return connectors

    def _calculate_model_metrics(
        self, theories: List[ScientificConcept], architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        total_mini_theories = sum(t.properties.get("component_mini_theory_count", 0) if t.properties else 0 for t in theories)
        total_propositions = sum(t.properties.get("theoretical_coverage", {}).get("proposition_count", 0) if t.properties else 0 for t in theories)
        estimated_ucms = sum(t.properties.get("theoretical_coverage", {}).get("estimated_distinct_ucm_coverage", 0) if t.properties else 0 for t in theories)

        complexity_metrics = self._calculate_architecture_complexity(architecture)

        return {
            "hierarchical_level": 5,
            "component_comprehensive_theories": len(theories),
            "aggregated_mini_theories": total_mini_theories,
            "aggregated_propositions": total_propositions,
            "aggregated_estimated_ucms": estimated_ucms,
            "architecture_complexity_metrics": complexity_metrics,
            "overall_integration_density": self._calculate_integration_density(theories),
            "overall_theoretical_coherence": self._estimate_coherence(theories)
        }

    def _calculate_architecture_complexity(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        arch_type = architecture.get("type")
        if arch_type == ModelArchitectureType.MODULAR.value:
            num_modules = len(architecture.get("modules", []))
            num_connectors = len(architecture.get("connectors", []))
            cyclomatic_complexity = num_connectors - num_modules + 1
            return {"module_count": num_modules, "connector_count": num_connectors, "cyclomatic_complexity": cyclomatic_complexity}
        elif arch_type == ModelArchitectureType.NETWORKED.value:
            num_nodes = len(architecture.get("nodes", []))
            num_edges = len(architecture.get("edges", []))
            density = (2 * num_edges) / (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0
            return {"node_count": num_nodes, "edge_count": num_edges, "network_density": round(density, 3)}
        elif arch_type == ModelArchitectureType.LAYERED.value:
            return {"layer_count": len(architecture.get("layers", {})), "dependencies_defined": len(architecture.get("layer_dependencies", {}))}
        elif arch_type == ModelArchitectureType.HIERARCHICAL.value:
            return {"root_defined": architecture.get("root") is not None, "depth": architecture.get("depth",0) }
        else:
            return {"type": arch_type, "complexity_score": "N/A"}

    def _calculate_integration_density(self, theories: List[ScientificConcept]) -> float:
        if not theories: return 0.0
        scores = [t.properties.get("compatibility_score", 0.5) if t.properties else 0.5 for t in theories]
        return sum(scores) / len(scores) if scores else 0.5

    def _estimate_coherence(self, theories: List[ScientificConcept]) -> float:
        if not theories: return 0.0
        landscape = self._analyze_theory_landscape(theories)
        dominant_theme_coverage = len(landscape.get("dominant_themes",[])) / 5.0
        return min(0.5 + (dominant_theme_coverage * 0.5), 1.0)

    def _calculate_total_coverage(self, theories: List[ScientificConcept]) -> Dict[str, int]:
        total_coverage: Counter[str] = Counter() # Ensure type for Counter
        for theory in theories:
            if theory.properties and "theoretical_coverage" in theory.properties:
                coverage_data = theory.properties["theoretical_coverage"]
                if isinstance(coverage_data, dict):
                    total_coverage.update(coverage_data)
        return dict(total_coverage)

    def _generate_model_name(
        self, theories: List[ScientificConcept], architecture: Dict[str, Any]
    ) -> str:
        if not theories: return f"Generic Unified {str(architecture.get('type','')).title()} Model"

        all_themes = []
        for theory in theories:
            if theory.properties and "common_themes" in theory.properties:
                all_themes.extend(theory.properties["common_themes"][:2])

        theme_counts = Counter(all_themes)
        top_themes = [theme for theme, _ in theme_counts.most_common(2)]

        arch_type_name = str(architecture.get('type','')).title()
        if top_themes:
            return f"Unified {arch_type_name} Model of {', '.join(t.title() for t in top_themes)}"
        else:
            # Ensure theories[0].name is a string before slicing
            first_theory_name = theories[0].name if theories[0].name is not None else "Unknown_Theory"
            return f"Unified {arch_type_name} Model based on {first_theory_name[:30]}..."


    def _generate_model_description(
        self, theories: List[ScientificConcept], architecture: Dict[str, Any], model_metrics: Dict[str, Any]
    ) -> str:
        desc = f"A Unified Model integrating {len(theories)} comprehensive theories using a {architecture.get('type','')} architecture."
        desc += f" It aggregates insights from approximately {model_metrics.get('aggregated_mini_theories',0)} mini-theories"
        desc += f" and {model_metrics.get('aggregated_propositions',0)} propositions."
        desc += f" Key metrics include: coherence ~{model_metrics.get('overall_theoretical_coherence',0.0):.2f}, integration density ~{model_metrics.get('overall_integration_density',0.0):.2f}."
        return desc

    def _create_formalization_structure(
        self, formalization_level: str, architecture: Dict[str, Any], theories: List[ScientificConcept]
    ) -> Dict[str, Any]:
        structure: Dict[str, Any] = { # Explicit type for structure
            "level": formalization_level,
            "components": [], # Explicitly List[Dict[str,str]] or List[Any]
            "relations": [],
            "constraints": [],
            "notes": "This is a conceptual placeholder for mathematical/logical formalization."
        }
        if formalization_level != "conceptual":
            components_list: List[Dict[str,str]] = []
            for i, theory in enumerate(theories):
                components_list.append({
                    "id": f"TC{i+1}_{str(theory.id)[:8]}",
                    "description": theory.name,
                    "formal_representation": "Awaiting detailed formalization."
                })
            structure["components"] = components_list
            current_notes = structure.get("notes", "") # Ensure notes is str
            structure["notes"] = str(current_notes) + " Further work needed for semi-formal or formal representation."
        return structure
