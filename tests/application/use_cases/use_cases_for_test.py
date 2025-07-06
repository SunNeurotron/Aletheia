"""
Temporary location for use case definitions to make them accessible to tests
in this sandboxed environment.
"""
import uuid
import re
from collections import Counter
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Adjust import for domain models from their temporary test location
from tests.domain.domain_for_test import ScientificConcept, Evidence, ConceptType

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
        # print(f"DEBUG: _is_covered: Checking word '{word_cand}' ({start_idx},{end_idx}) against spans: {covered_spans}")
        for cs, ce in covered_spans:
            if cs <= start_idx and end_idx <= ce:
                 # print(f"DEBUG: Word '{word_cand}' ({start_idx},{end_idx}) IS covered by span ({cs},{ce})")
                 return True
        # print(f"DEBUG: Word '{word_cand}' ({start_idx},{end_idx}) is NOT covered.")
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
        # print(f"\nDEBUG ExtractUCMs: Processing document: '{input_data.document_text}'")
        ucms_created = []
        sentences = re.split(r'(?<=[.!?])\s+', input_data.document_text)
        extracted_candidate_names = set()

        phrase_regex = r'\b(?:[A-Z][a-zA-Z0-9_"\'-]*\s+){1,5}[A-Z][a-zA-Z0-9_"\'-]*\b'
        single_word_regex = r'\b[A-Z][a-zA-Z0-9_"\'-]+\b'

        for sentence_idx, sentence in enumerate(sentences):
            # print(f"DEBUG ExtractUCMs: Sentence {sentence_idx}: '{sentence}'")
            if not sentence.strip():
                continue

            current_sentence_covered_spans: List[tuple[int, int]] = []

            # print(f"DEBUG ExtractUCMs: Looking for phrases...")
            for match in re.finditer(phrase_regex, sentence):
                phrase_candidate = match.group(0).strip()
                # print(f"DEBUG ExtractUCMs:  Found phrase candidate: '{phrase_candidate}' at span {match.span()}")
                cleaned_phrase = self._clean_phrase(phrase_candidate)
                # print(f"DEBUG ExtractUCMs:  Cleaned phrase: '{cleaned_phrase}'")

                if not cleaned_phrase: continue

                current_sentence_covered_spans.append(match.span())

                if cleaned_phrase not in extracted_candidate_names:
                    # print(f"DEBUG ExtractUCMs:   Adding PHRASE UCM: '{cleaned_phrase}'")
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
                # else:
                    # print(f"DEBUG ExtractUCMs:   Phrase UCM '{cleaned_phrase}' already extracted globally.")
            # print(f"DEBUG ExtractUCMs: Covered spans after phrases in sentence {sentence_idx}: {current_sentence_covered_spans}")

            # print(f"DEBUG ExtractUCMs: Looking for single words...")
            for match in re.finditer(single_word_regex, sentence):
                word_cand = match.group(0).strip()
                # print(f"DEBUG ExtractUCMs:  Found single word candidate: '{word_cand}' at span {match.span()}")

                if self._is_covered(word_cand, match.start(), match.end(), current_sentence_covered_spans):
                    # print(f"DEBUG ExtractUCMs:   Word '{word_cand}' is covered by a phrase in this sentence. Skipping.")
                    continue

                cleaned_word = self._clean_phrase(word_cand)
                # print(f"DEBUG ExtractUCMs:  Cleaned word: '{cleaned_word}'")

                if not cleaned_word:
                    # print(f"DEBUG ExtractUCMs:   Word '{word_cand}' cleaned to empty. Skipping.")
                    continue

                if len(cleaned_word) < 3 or cleaned_word.lower() in self.stopwords:
                    # print(f"DEBUG ExtractUCMs:   Cleaned word '{cleaned_word}' is too short or stopword. Skipping.")
                    continue

                if cleaned_word not in extracted_candidate_names:
                    # print(f"DEBUG ExtractUCMs:   Adding SINGLE WORD UCM: '{cleaned_word}'")
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
                # else:
                    # print(f"DEBUG ExtractUCMs:   Single word UCM '{cleaned_word}' already extracted globally.")

        # print(f"DEBUG ExtractUCMs: Final UCMs for this document: {[ucm.name for ucm in ucms_created]}")
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
    """
    Use case for constructing a mini-theory from a list of propositions.
    """
    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo

    def execute(self, input_data: ConstructMiniTheoryInput) -> MiniTheoryConstructionResult:
        if not input_data.proposition_ids:
            raise ValueError("At least one proposition ID must be provided to construct a mini-theory.")

        component_propositions = []
        for prop_id in input_data.proposition_ids:
            proposition = self.concept_repo.get_by_id(prop_id)
            if not proposition or proposition.type != ConceptType.PROPOSITION:
                raise ValueError(f"Invalid or non-PROPOSITION concept ID provided: {prop_id}")
            component_propositions.append(proposition)

        # Generate name if not provided
        name = input_data.mini_theory_name
        if name is None:
            if component_propositions:
                # Simple name generation: Use parts of the first proposition's name
                first_prop_name_part = component_propositions[0].name.split(':')[0] # Take part before colon if any
                name = f"Mini-Theory on: {first_prop_name_part[:50]}..."
            else: # Should not happen due to check above
                name = "Unnamed Mini-Theory"

        # Use provided description or keep the default from Pydantic model
        description = input_data.mini_theory_description
        if description == ConstructMiniTheoryInput.model_fields["mini_theory_description"].default and component_propositions:
            description = f"A mini-theory synthesizing {len(component_propositions)} proposition(s), including insights like '{component_propositions[0].name[:70]}...'."

        # Ensure description is a string
        final_description = description if description is not None else "Synthesized mini-theory."


        mini_theory = ScientificConcept(
            name=name,
            description=final_description,
            type=ConceptType.MINI_THEORY,
            member_concept_ids=input_data.proposition_ids, # Store IDs of component propositions
            properties={
                "derivation_method": input_data.derivation_method_description or "heuristic_proposition_grouping",
                "component_proposition_count": len(input_data.proposition_ids)
            },
            # Evidence for a mini-theory could be the propositions themselves or a system note
            evidence_sources=[
                Evidence(
                    source_doi="internal_process:mini_theory_construction",
                    source_citation="Aletheia System",
                    snippet=f"Mini-theory constructed from {len(input_data.proposition_ids)} propositions.",
                    confidence=0.8 # Confidence in this construction method
                )
            ]
            # derived_from_cluster_id could be set if all propositions come from one cluster
            # derived_from_ucm_ids could be a union of those from propositions if relevant
        )

        self.concept_repo.add(mini_theory)
        return MiniTheoryConstructionResult(mini_theory_created=mini_theory)
