"""
Temporary location for use case definitions to make them accessible to tests
in this sandboxed environment.
"""
import uuid
import re
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

from tests.domain.domain_for_test import (
    ScientificConcept,
    Evidence,
    ConceptType,
    TheoryIntegrationMethod,
    ModelArchitectureType
)
from tests.application.ports.ports_for_test import ConceptRepository, RelationshipRepository

# --- KnowledgeSynthesisUseCase (Basic Concept Management) ---
class CreateConceptInput(BaseModel):
    name: str
    description: str
    type: ConceptType
    properties: Dict[str, Any] = Field(default_factory=dict)
    evidence_sources: List[Evidence] = Field(default_factory=list)

class KnowledgeSynthesisUseCase:
    def __init__(self, concept_repo: ConceptRepository, relationship_repo: RelationshipRepository):
        self.concept_repo = concept_repo
        self.relationship_repo = relationship_repo
    def create_concept(self, input_data: CreateConceptInput) -> ScientificConcept:
        concept = ScientificConcept(
            name=input_data.name, description=input_data.description, type=input_data.type,
            properties=input_data.properties, evidence_sources=input_data.evidence_sources,
        )
        self.concept_repo.add(concept)
        return concept
    def get_all_concepts(self) -> List[ScientificConcept]:
        return self.concept_repo.list_all()
    def get_concept_details(self, concept_id: uuid.UUID) -> ScientificConcept:
        concept = self.concept_repo.get_by_id(concept_id)
        if not concept: raise ValueError(f"Concept with ID {concept_id} not found.")
        return concept

# --- Eje Y - Level 0: ExtractUCMsUseCase ---
class ExtractUCMsInput(BaseModel):
    document_text: str
    source_doi: str
    source_citation: str
class UCMExtractionResult(BaseModel): ucms_created: List[ScientificConcept]
class ExtractUCMsUseCase:
    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo
        self.stopwords = {"the", "is", "an", "a", "of", "to", "in", "and", "it", "this", "that",
                          "another", "later", "but", "also", "key", "factor", "was", "were", "has", "had",
                          "may", "can", "could", "should", "would", "might"}
    def _is_covered(self, word_cand:str, start_idx: int, end_idx: int, covered_spans: List[tuple[int, int]]) -> bool:
        for cs, ce in covered_spans:
            if cs <= start_idx and end_idx <= ce: return True
        return False
    def _clean_phrase(self, phrase: str) -> str:
        words = phrase.split()
        while words and words[0].lower() in self.stopwords: words.pop(0)
        while words and words[-1].lower() in self.stopwords: words.pop()
        cleaned_phrase = " ".join(words)
        if not cleaned_phrase or len(cleaned_phrase) < 3: return ""
        if cleaned_phrase.lower() in self.stopwords and len(cleaned_phrase.split()) == 1: return ""
        return cleaned_phrase
    def execute(self, input_data: ExtractUCMsInput) -> UCMExtractionResult:
        ucms_created = []
        sentences = re.split(r'(?<=[.!?])\s+', input_data.document_text)
        extracted_candidate_names = set()
        phrase_regex = r'\b(?:[A-Z][a-zA-Z0-9_"\'-]*\s+){1,5}[A-Z][a-zA-Z0-9_"\'-]*\b'
        single_word_regex = r'\b[A-Z][a-zA-Z0-9_"\'-]+\b'
        for sentence_idx, sentence in enumerate(sentences):
            if not sentence.strip(): continue
            current_sentence_covered_spans: List[tuple[int, int]] = []
            for match in re.finditer(phrase_regex, sentence):
                phrase_candidate = match.group(0).strip()
                cleaned_phrase = self._clean_phrase(phrase_candidate)
                if not cleaned_phrase: continue
                current_sentence_covered_spans.append(match.span())
                if cleaned_phrase not in extracted_candidate_names:
                    props = {"extraction_method": "regex_capitalized_multi_word_phrase_v4", "original_phrase": phrase_candidate, "original_sentence_index": sentence_idx}
                    evidence = [Evidence(source_doi=input_data.source_doi, source_citation=input_data.source_citation, snippet=sentence, confidence=0.70)]
                    ucm = ScientificConcept(name=cleaned_phrase, description=f"UCM (phrase) extracted from: '{sentence[:100]}...'", type=ConceptType.UCM, properties=props, evidence_sources=evidence, verification_hash=hex(hash(cleaned_phrase + input_data.source_doi))[2:])
                    self.concept_repo.add(ucm); ucms_created.append(ucm); extracted_candidate_names.add(cleaned_phrase)
            for match in re.finditer(single_word_regex, sentence):
                word_cand = match.group(0).strip()
                if self._is_covered(word_cand, match.start(), match.end(), current_sentence_covered_spans): continue
                cleaned_word = self._clean_phrase(word_cand)
                if not cleaned_word or len(cleaned_word) < 3 or cleaned_word.lower() in self.stopwords: continue
                if cleaned_word not in extracted_candidate_names:
                    props = {"extraction_method": "regex_capitalized_single_word_v4", "original_word": word_cand, "original_sentence_index": sentence_idx}
                    evidence = [Evidence(source_doi=input_data.source_doi, source_citation=input_data.source_citation, snippet=sentence, confidence=0.60)]
                    ucm = ScientificConcept(name=cleaned_word, description=f"UCM (single word) extracted from: '{sentence[:100]}...'", type=ConceptType.UCM, properties=props, evidence_sources=evidence, verification_hash=hex(hash(cleaned_word + input_data.source_doi))[2:])
                    self.concept_repo.add(ucm); ucms_created.append(ucm); extracted_candidate_names.add(cleaned_word)
        return UCMExtractionResult(ucms_created=ucms_created)

# --- Eje Y - Level 1: FormClustersUseCase & DerivePropositionsUseCase ---
class FormClusterInput(BaseModel):
    ucm_ids: List[uuid.UUID]
    cluster_name: Optional[str] = "Unnamed Cluster"
    cluster_description: Optional[str] = "A cluster formed from selected UCMs."
class ClusterFormationResult(BaseModel): cluster_created: ScientificConcept
class FormClustersUseCase:
    def __init__(self, concept_repo: ConceptRepository): self.concept_repo = concept_repo
    def execute(self, input_data: FormClusterInput) -> ClusterFormationResult:
        member_ucms = []
        for ucm_id_val in input_data.ucm_ids: # Renamed to avoid clash with ucm variable
            ucm = self.concept_repo.get_by_id(ucm_id_val)
            if not ucm or ucm.type != ConceptType.UCM:
                raise ValueError(f"Invalid or non-UCM concept ID provided: {ucm_id_val}")
            member_ucms.append(ucm)
        if not member_ucms: raise ValueError("No UCMs provided to form a cluster.") # Corrected this message for test
        all_keywords = []; stopwords_cluster = {"the", "a", "an", "is", "of", "to", "in", "and", "for", "with", "on", "it", "this", "that", "was", "were", "has", "had", "not", "but"}
        for ucm_item in member_ucms: # Renamed to avoid clash
            text = (ucm_item.name + " " + ucm_item.description).lower()
            words = re.findall(r'\b\w+\b', text)
            all_keywords.extend([w for w in words if w not in stopwords_cluster and len(w) > 2])
        common_keywords = [kw for kw, count in Counter(all_keywords).most_common(5)]
        final_cluster_name = input_data.cluster_name if input_data.cluster_name is not None and input_data.cluster_name != FormClusterInput.model_fields["cluster_name"].default else (f"Cluster: {', '.join(common_keywords[:3])}" if common_keywords else (f"Cluster of {len(member_ucms)} UCMs ({member_ucms[0].name[:20]}...)" if member_ucms else str(FormClusterInput.model_fields["cluster_name"].default)))
        final_cluster_description = input_data.cluster_description if input_data.cluster_description is not None and input_data.cluster_description != FormClusterInput.model_fields["cluster_description"].default else (f"Conceptual cluster related to: {', '.join(common_keywords)}. Contains {len(member_ucms)} UCMs." if common_keywords else (f"A conceptual cluster containing {len(member_ucms)} UCMs, including '{member_ucms[0].name}'." if member_ucms else str(FormClusterInput.model_fields["cluster_description"].default)))
        props = {"ucm_count": len(input_data.ucm_ids), "common_keywords": common_keywords, "formation_method": "basic_keyword_aggregation_v2"}
        evidence = [Evidence(source_doi="internal_process:cluster_formation_v2", source_citation="Aletheia System", snippet=f"Cluster formed from {len(input_data.ucm_ids)} UCMs.", confidence=0.65)]
        cluster = ScientificConcept(name=final_cluster_name, description=final_cluster_description, type=ConceptType.CLUSTER, properties=props, member_concept_ids=input_data.ucm_ids, evidence_sources=evidence)
        self.concept_repo.add(cluster); return ClusterFormationResult(cluster_created=cluster)

class DerivePropositionInput(BaseModel):
    cluster_id: uuid.UUID
    proposition_text: Optional[str] = None
class PropositionDerivationResult(BaseModel): proposition_created: ScientificConcept
class DerivePropositionsUseCase:
    def __init__(self, concept_repo: ConceptRepository, relationship_repo: RelationshipRepository):
        self.concept_repo = concept_repo; self.relationship_repo = relationship_repo
    def execute(self, input_data: DerivePropositionInput) -> PropositionDerivationResult:
        cluster = self.concept_repo.get_by_id(input_data.cluster_id)
        if not cluster or cluster.type != ConceptType.CLUSTER: raise ValueError(f"Invalid or non-CLUSTER concept ID provided for proposition derivation: {input_data.cluster_id}") # Corrected message
        member_ucms = [ucm for ucm_id in (cluster.member_concept_ids or []) if (ucm := self.concept_repo.get_by_id(ucm_id)) and ucm.type == ConceptType.UCM]
        derived_kws = []; stopwords_prop = {"the", "a", "an", "is", "of", "to", "in", "and", "for", "with", "on", "it", "this", "that", "was", "were", "has", "had", "not", "but"}
        if member_ucms:
            all_kws = [];
            for ucm in member_ucms:
                text = (ucm.name + " " + ucm.description).lower()
                words = re.findall(r'\b\w+\b', text)
                all_kws.extend([w for w in words if w not in stopwords_prop and len(w) > 2])
            derived_kws = [kw for kw, count in Counter(all_kws).most_common(3)]
        prop_name = input_data.proposition_text or (f"Hypothesized Link: {', '.join(derived_kws)} in {cluster.name}" if derived_kws else f"General Proposition regarding {cluster.name}")
        prop_name = prop_name[:250]
        desc = f"This proposition, '{prop_name}', emerges from cluster '{cluster.name}' (ID: {cluster.id})."
        if member_ucms: desc += f" Key UCMs: {', '.join([ucm.name for ucm in member_ucms[:3]])}..."
        elif cluster.member_concept_ids: desc += f" Associated with {len(cluster.member_concept_ids)} concept IDs."
        else: desc += " No specified member UCMs."
        props = {"derivation_method": "keyword_based_heuristic_v2", "key_cluster_keywords_for_prop": derived_kws}
        evidence = [Evidence(source_doi="internal_process:proposition_derivation_v2", source_citation="Aletheia System", snippet=f"Proposition from cluster {cluster.id}.", confidence=0.6)]
        proposition = ScientificConcept(name=prop_name, description=desc, type=ConceptType.PROPOSITION, derived_from_cluster_id=input_data.cluster_id, derived_from_ucm_ids=(cluster.member_concept_ids or []), properties=props, evidence_sources=evidence)
        self.concept_repo.add(proposition); return PropositionDerivationResult(proposition_created=proposition)

# --- Eje Y - Level 2: ConstructMiniTheoryUseCase ---
class ConstructMiniTheoryInput(BaseModel):
    proposition_ids: List[uuid.UUID]
    mini_theory_name: Optional[str] = None
    mini_theory_description: Optional[str] = "A synthesized mini-theory based on selected propositions."
    derivation_method_description: Optional[str] = "heuristic_proposition_grouping"
class MiniTheoryConstructionResult(BaseModel): mini_theory_created: ScientificConcept
class ConstructMiniTheoryUseCase:
    def __init__(self, concept_repo: ConceptRepository): self.concept_repo = concept_repo
    def execute(self, input_data: ConstructMiniTheoryInput) -> MiniTheoryConstructionResult:
        if not input_data.proposition_ids: raise ValueError("At least one proposition ID must be provided.")
        component_propositions = []
        for prop_id_val in input_data.proposition_ids: # Renamed to avoid clash
            proposition = self.concept_repo.get_by_id(prop_id_val)
            if not proposition or proposition.type != ConceptType.PROPOSITION:
                raise ValueError(f"Invalid or non-PROPOSITION concept ID provided: {prop_id_val}") # Corrected message
            component_propositions.append(proposition)
        name = input_data.mini_theory_name or (f"Mini-Theory on: {component_propositions[0].name.split(':')[0][:50]}..." if component_propositions else "Unnamed Mini-Theory")
        desc = input_data.mini_theory_description
        if desc == ConstructMiniTheoryInput.model_fields["mini_theory_description"].default and component_propositions:
            desc = f"A mini-theory synthesizing {len(component_propositions)} proposition(s), including insights like '{component_propositions[0].name[:70]}...'."
        final_desc = desc if desc is not None else "Synthesized mini-theory."
        props = {"derivation_method": input_data.derivation_method_description or "heuristic_proposition_grouping", "component_proposition_count": len(input_data.proposition_ids)}
        evidence = [Evidence(source_doi="internal_process:mini_theory_construction", source_citation="Aletheia System", snippet=f"Mini-theory from {len(input_data.proposition_ids)} propositions.", confidence=0.8)]
        mt = ScientificConcept(name=name, description=final_desc, type=ConceptType.MINI_THEORY, member_concept_ids=input_data.proposition_ids, properties=props, evidence_sources=evidence)
        self.concept_repo.add(mt); return MiniTheoryConstructionResult(mini_theory_created=mt)

# --- Eje Y - Level 3 Part 1: ConstructComprehensiveTheoryUseCase ---
class ConstructComprehensiveTheoryInput(BaseModel):
    mini_theory_ids: List[uuid.UUID] = Field(..., min_length=1, description="At least 1 mini-theory for synthesis")
    theory_name: Optional[str] = None; theory_description: Optional[str] = None
    integration_method: TheoryIntegrationMethod = TheoryIntegrationMethod.COMPLEMENTARY_SYNTHESIS
    integration_rationale: Optional[str] = None
class ComprehensiveTheoryResult(BaseModel):
    theory_created: ScientificConcept; integration_analysis: Optional[Dict[str, Any]] = None
class ConstructComprehensiveTheoryUseCase:
    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo
        self.stopwords = {"the","a","an","is","are","was","were","of","to","in","and","or","but","for","with","on","at","by","from"}
    def _retrieve_and_validate_mini_theories(self, mts_ids: List[uuid.UUID]) -> List[ScientificConcept]:
        mini_theories = []
        for mt_id_val in mts_ids: # Renamed
            concept = self.concept_repo.get_by_id(mt_id_val)
            if not concept or concept.type != ConceptType.MINI_THEORY:
                raise ValueError(f"Invalid or non-MINI_THEORY concept ID: {mt_id_val}") # Corrected message
            mini_theories.append(concept)
        return mini_theories
    def _extract_keywords_from_theory(self, th: ScientificConcept) -> List[str]:
        txt = f"{th.name} {th.description}".lower()
        if th.properties:
            if "common_keywords" in th.properties and isinstance(th.properties["common_keywords"], list): txt += " " + " ".join(th.properties["common_keywords"])
            if "key_cluster_keywords_for_prop" in th.properties and isinstance(th.properties["key_cluster_keywords_for_prop"], list): txt += " " + " ".join(th.properties["key_cluster_keywords_for_prop"])
        return list(set([w for w in re.findall(r'\b\w+\b', txt) if w not in self.stopwords and len(w) > 2]))
    def _extract_common_themes(self, mts: List[ScientificConcept]) -> List[str]:
        return [th for th, _ in Counter([kw for mt in mts for kw in self._extract_keywords_from_theory(mt)]).most_common(5)]
    def _analyze_theory_compatibility(self, mts: List[ScientificConcept]) -> Dict[str, Any]:
        if len(mts) < 2: return {"overall_compatibility": 1.0, "integration_feasibility": "high", "compatibility_matrix": {}, "shared_keywords": {}}
        comp_matrix = {}; shared_kw_counts = {};
        for i, mt1 in enumerate(mts):
            for j, mt2 in enumerate(mts[i+1:], start=i+1):
                k1,k2=set(self._extract_keywords_from_theory(mt1)),set(self._extract_keywords_from_theory(mt2))
                shared,total=k1.intersection(k2),k1.union(k2); comp_val = len(shared)/len(total) if total else 0
                key = f"{str(mt1.id)[:4]}_{str(mt2.id)[:4]}"; comp_matrix[key],shared_kw_counts[key] = comp_val,list(shared)
        overall = sum(comp_matrix.values())/len(comp_matrix) if comp_matrix else 0.0
        feas = "high" if overall > 0.6 else ("medium" if overall > 0.3 else "low")
        return {"compatibility_matrix":comp_matrix, "shared_keywords":shared_kw_counts, "overall_compatibility":overall, "integration_feasibility":feas}
    def _generate_theory_name(self, mts: List[ScientificConcept], themes: List[str]) -> str:
        return f"Comprehensive Theory of {', '.join(themes[:2]).title()}" if themes else (f"Integrated Theory from {mts[0].name[:30]}..." if mts else "Integrated Theory")
    def _generate_theory_description(self, mts: List[ScientificConcept], themes: List[str], comp: Optional[Dict[str, Any]]) -> str:
        desc = f"Integrates {len(mts)} mini-theories" + (f" on themes: {', '.join(themes[:3])}" if themes else "")
        if comp: desc += f". Feasibility: {comp['integration_feasibility']} (Score: {comp['overall_compatibility']:.2f})."
        mt_n = [mt.name[:25]+"..." if len(mt.name)>25 else mt.name for mt in mts[:2]]
        if mt_n: desc += f" Components: {', '.join(mt_n)}" + (f" +{len(mts)-2} others." if len(mts)>2 else ".")
        return desc
    def _generate_integration_rationale(self, comp: Optional[Dict[str,Any]], method: TheoryIntegrationMethod) -> str:
        feas = comp["integration_feasibility"] if comp and "integration_feasibility" in comp else "unknown"
        mval = method.value if isinstance(method, Enum) else method
        return f"Method: {mval}. Feasibility: {feas}."
    def _calculate_theoretical_coverage(self, mts: List[ScientificConcept]) -> Dict[str, int]:
        props = set(pid for mt in mts if mt.member_concept_ids for pid in mt.member_concept_ids)
        ucms = 0
        for pid in props:
            p = self.concept_repo.get_by_id(pid)
            if p:
                if p.derived_from_ucm_ids: ucms += len(p.derived_from_ucm_ids)
                elif p.derived_from_cluster_id:
                    clu = self.concept_repo.get_by_id(p.derived_from_cluster_id) # Renamed to clu
                    if clu and clu.member_concept_ids: ucms += len(clu.member_concept_ids)
        return {"proposition_count":len(props), "estimated_distinct_ucm_coverage":ucms}
    def execute(self, input_data: ConstructComprehensiveTheoryInput) -> ComprehensiveTheoryResult:
        if not input_data.mini_theory_ids: raise ValueError("At least one mini-theory ID must be provided.") # Corrected message
        mts = self._retrieve_and_validate_mini_theories(input_data.mini_theory_ids)
        comp_an = self._analyze_theory_compatibility(mts) if len(mts) > 1 else None
        themes = self._extract_common_themes(mts)
        name = input_data.theory_name or self._generate_theory_name(mts, themes)
        desc = input_data.theory_description or self._generate_theory_description(mts, themes, comp_an)
        integ_props = {"integration_method":input_data.integration_method.value, "integration_rationale":input_data.integration_rationale or (self._generate_integration_rationale(comp_an,input_data.integration_method) if comp_an else "N/A for single component"), "component_mini_theory_count":len(mts), "common_themes":themes, "compatibility_score":comp_an["overall_compatibility"] if comp_an else 1.0, "theoretical_coverage":self._calculate_theoretical_coverage(mts), "synthesis_timestamp":str(uuid.uuid4())[:12]}
        ct = ScientificConcept(name=name[:255],description=desc,type=ConceptType.COMPREHENSIVE_THEORY,member_concept_ids=input_data.mini_theory_ids,properties=integ_props,evidence_sources=[Evidence(source_doi="internal_process:ct_synthesis",source_citation="Aletheia L3",snippet=f"CT from {len(mts)} MTs via {input_data.integration_method.value}.",confidence=0.75)])
        self.concept_repo.add(ct); return ComprehensiveTheoryResult(theory_created=ct,integration_analysis=comp_an)

# --- Eje Y - Level 3 Part 2: ConstructUnifiedModelUseCase ---
class ConstructUnifiedModelInput(BaseModel):
    comprehensive_theory_ids: List[uuid.UUID] = Field(...,min_length=1,description="Min 1 CT required")
    model_name: Optional[str]=None; model_description: Optional[str]=None
    architecture_type: ModelArchitectureType=ModelArchitectureType.MODULAR
    formalization_level: str=Field(default="conceptual",description="Formalization: conceptual, semi-formal, formal")
class UnifiedModelResult(BaseModel):
    model_created: ScientificConcept; model_metrics: Dict[str,Any]; architecture_diagram: Dict[str,Any]
class ConstructUnifiedModelUseCase:
    def __init__(self, concept_repo: ConceptRepository): self.concept_repo=concept_repo
    def _retrieve_and_validate_theories(self, ct_ids: List[uuid.UUID]) -> List[ScientificConcept]:
        cts = []
        for ct_id_val in ct_ids: # Renamed
            concept = self.concept_repo.get_by_id(ct_id_val)
            if not concept or concept.type != ConceptType.COMPREHENSIVE_THEORY:
                raise ValueError(f"Invalid or non-COMPREHENSIVE_THEORY concept ID: {ct_id_val}") # Corrected message
            cts.append(concept)
        return cts
    def _analyze_theory_landscape(self, cts: List[ScientificConcept]) -> Dict[str,Any]:
        themes,methods = [],[]
        for t in cts:
            if t.properties: themes.extend(t.properties.get("common_themes",[])); methods.append(t.properties.get("integration_method",""))
        theme_clusts = defaultdict(list)
        for i,t in enumerate(cts):
            for th in (t.properties.get("common_themes",[]) if t.properties else []): theme_clusts[th].append(str(t.id))
        return {"dominant_themes":Counter(themes).most_common(5),"integration_methods_used":Counter(methods).most_common(),"theme_clusters":dict(theme_clusts),"theory_connectivity_by_theme":len([v for v in theme_clusts.values() if len(v)>1])}
    def _design_modular_architecture(self, cts: List[ScientificConcept], land: Dict[str,Any]) -> Dict[str,Any]:
        mods = []; dom_th = [t[0] for t in land.get("dominant_themes", [])]
        for i,t in enumerate(cts):
            mod_int = [f"I_{th[:10].replace(' ','_')}" for th in (t.properties.get("common_themes",[]) if t.properties else []) if th in dom_th]
            mods.append({"module_id":f"M{i+1}","theory_id":str(t.id),"name":t.name[:50],"interfaces":list(set(mod_int)),"dependencies":[]})
        return {"type":ModelArchitectureType.MODULAR.value,"modules":mods,"connectors":self._generate_module_connectors(mods),"core_interfaces":list(set([f"I_{t[0][:10].replace(' ','_')}" for t in dom_th[:3]]))}
    def _generate_module_connectors(self, mods: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
        conns = []
        for i,m1 in enumerate(mods):
            for j,m2 in enumerate(mods[i+1:]):
                if m1.get("interfaces") and m2.get("interfaces"):
                    shared = set(m1["interfaces"]) & set(m2["interfaces"])
                    if shared: conns.append({"from":m1["module_id"],"to":m2["module_id"],"via_interfaces":list(shared)})
        return conns
    def _design_layered_architecture(self, cts: List[ScientificConcept], land: Dict[str,Any]) -> Dict[str,Any]:
        layers:Dict[str,List[Dict[str,str]]] = {"foundational":[],"intermediate":[],"application":[]}
        for i,t in enumerate(cts): layers[list(layers.keys())[i%len(layers.keys())]].append({"theory_id":str(t.id),"name":t.name})
        return {"type":ModelArchitectureType.LAYERED.value,"layers":layers,"layer_dependencies":{"application":["intermediate"],"intermediate":["foundational"],"foundational":[]}}
    def _design_networked_architecture(self, cts: List[ScientificConcept], land: Dict[str,Any]) -> Dict[str,Any]:
        nodes=[{"id":str(t.id),"name":t.name[:30]} for t in cts]; edges=[]
        for th,ids in land.get("theme_clusters",{}).items():
            if len(ids)>1:
                for i in range(len(ids)):
                    for j in range(i+1,len(ids)): edges.append({"source":ids[i],"target":ids[j],"theme":th,"weight":0.5})
        return {"type":ModelArchitectureType.NETWORKED.value,"nodes":nodes,"edges":edges,"central_themes":[t[0] for t in land.get("dominant_themes",[])[:3]]}
    def _design_hierarchical_architecture(self, cts: List[ScientificConcept], land: Dict[str,Any]) -> Dict[str,Any]:
        if not cts: return {"type":ModelArchitectureType.HIERARCHICAL.value,"root":None,"tree":{}}
        root:Dict[str,Any]={"id":str(cts[0].id),"name":cts[0].name[:30],"children":[]}
        curr:Dict[str,Any]=root
        for i,t in enumerate(cts[1:]):
            child:Dict[str,Any]={"id":str(t.id),"name":t.name[:30],"children":[]}
            if i%2==0 and isinstance(curr.get("children"),list) and curr["children"]: curr=curr["children"][-1]
            if isinstance(curr.get("children"),list): curr["children"].append(child)
            else: curr["children"]=[child]
        return {"type":ModelArchitectureType.HIERARCHICAL.value,"root":root,"depth":3,"branching_factor":"variable"}
    def _design_hybrid_architecture(self, cts:List[ScientificConcept], land:Dict[str,Any])->Dict[str,Any]:
        core_th=cts[:len(cts)//2] if len(cts)>1 else cts; ext_th=cts[len(cts)//2:] if len(cts)>1 else []
        return {"type":ModelArchitectureType.HYBRID.value,"components":{"modular_core":self._design_modular_architecture(core_th,land) if core_th else None, "networked_extensions":self._design_networked_architecture(ext_th,land) if ext_th else None},"integration_points":[f"IP_{i+1}" for i in range(min(1,len(cts)))]}
    def _design_model_architecture(self, cts:List[ScientificConcept], arch_type:ModelArchitectureType, land:Dict[str,Any])->Dict[str,Any]:
        val=arch_type.value if isinstance(arch_type,Enum) else arch_type
        if val==ModelArchitectureType.MODULAR.value: return self._design_modular_architecture(cts,land)
        if val==ModelArchitectureType.LAYERED.value: return self._design_layered_architecture(cts,land)
        if val==ModelArchitectureType.NETWORKED.value: return self._design_networked_architecture(cts,land)
        if val==ModelArchitectureType.HIERARCHICAL.value: return self._design_hierarchical_architecture(cts,land)
        return self._design_hybrid_architecture(cts,land)
    def _calculate_architecture_complexity(self, arch:Dict[str,Any])->Dict[str,Any]:
        atype=arch.get("type")
        if atype==ModelArchitectureType.MODULAR.value:n_mod,n_con=len(arch.get("modules",[])),len(arch.get("connectors",[]));cyc=n_con-n_mod+1 if n_mod>0 else 0; return {"module_count":n_mod,"connector_count":n_con,"cyclomatic_complexity":cyc}
        if atype==ModelArchitectureType.NETWORKED.value:n_node,n_edge=len(arch.get("nodes",[])),len(arch.get("edges",[]));dens=(2*n_edge)/(n_node*(n_node-1)) if n_node>1 else 0; return {"node_count":n_node,"edge_count":n_edge,"network_density":round(dens,3)}
        if atype==ModelArchitectureType.LAYERED.value: return {"layer_count":len(arch.get("layers",{})),"dependencies_defined":len(arch.get("layer_dependencies",{}))}
        if atype==ModelArchitectureType.HIERARCHICAL.value: return {"root_defined":arch.get("root") is not None,"depth":arch.get("depth",0)}
        return {"type":atype,"complexity_score":"N/A"}
    def _calculate_integration_density(self, cts:List[ScientificConcept])->float:
        if not cts: return 0.0
        scores=[(t.properties.get("compatibility_score",0.5) if t.properties else 0.5) for t in cts]
        return sum(scores)/len(scores) if scores else 0.5
    def _estimate_coherence(self, cts:List[ScientificConcept])->float:
        if not cts: return 0.0
        land=self._analyze_theory_landscape(cts);dom_th_cov=len(land.get("dominant_themes",[]))/5.0 if land.get("dominant_themes") else 0.0
        return min(0.5+(dom_th_cov*0.5),1.0)
    def _calculate_total_coverage(self, cts:List[ScientificConcept])->Dict[str,int]:
        total_cov:Counter[str]=Counter()
        for t in cts:
            if t.properties and "theoretical_coverage" in t.properties and isinstance(t.properties["theoretical_coverage"],dict):
                total_cov.update(t.properties["theoretical_coverage"])
        return dict(total_cov)
    def _calculate_model_metrics(self, cts:List[ScientificConcept], arch:Dict[str,Any])->Dict[str,Any]:
        agg_mts=sum(t.properties.get("component_mini_theory_count",0) if t.properties else 0 for t in cts)
        agg_props=sum(t.properties.get("theoretical_coverage",{}).get("proposition_count",0) if t.properties else 0 for t in cts)
        agg_ucms=sum(t.properties.get("theoretical_coverage",{}).get("estimated_distinct_ucm_coverage",0) if t.properties else 0 for t in cts)
        return {"hierarchical_level":5,"component_comprehensive_theories":len(cts),"aggregated_mini_theories":agg_mts,"aggregated_propositions":agg_props,"aggregated_estimated_ucms":agg_ucms,"architecture_complexity_metrics":self._calculate_architecture_complexity(arch),"overall_integration_density":self._calculate_integration_density(cts),"overall_theoretical_coherence":self._estimate_coherence(cts)}
    def _generate_model_name(self, cts:List[ScientificConcept], arch:Dict[str,Any])->str:
        if not cts: return f"Generic Unified {str(arch.get('type','')).title()} Model"
        all_th = [th for t in cts if t.properties and "common_themes" in t.properties and isinstance(t.properties["common_themes"],list) for th in t.properties["common_themes"][:2]]
        top_th = [th for th,_ in Counter(all_th).most_common(2)]
        arch_name = str(arch.get('type','')).title()
        return f"Unified {arch_name} Model of {', '.join(t.title() for t in top_th)}" if top_th else f"Unified {arch_name} Model based on {(cts[0].name if cts[0].name else 'Unknown')[:30]}..."
    def _generate_model_description(self, cts:List[ScientificConcept], arch:Dict[str,Any], metrics:Dict[str,Any])->str:
        return f"Unified Model integrating {len(cts)} TCs via {arch.get('type','')} arch. Aggregates ~{metrics.get('aggregated_mini_theories',0)} MTs, ~{metrics.get('aggregated_propositions',0)} Props. Coherence: ~{metrics.get('overall_theoretical_coherence',0.0):.2f}, Density: ~{metrics.get('overall_integration_density',0.0):.2f}."
    def _create_formalization_structure(self, level:str, arch:Dict[str,Any], cts:List[ScientificConcept])->Dict[str,Any]:
        struct:Dict[str,Any]={"level":level,"components":[],"relations":[],"constraints":[],"notes":"Conceptual placeholder."}
        if level!="conceptual":
            comps:List[Dict[str,str]]=[{"id":f"TC{i+1}_{str(t.id)[:8]}","description":t.name,"formal_representation":"Details TBD."} for i,t in enumerate(cts)]
            struct["components"]=comps; struct["notes"]=str(struct.get("notes",""))+" Needs further formal work."
        return struct
    def execute(self, input_data: ConstructUnifiedModelInput) -> UnifiedModelResult:
        cts=self._retrieve_and_validate_theories(input_data.comprehensive_theory_ids)
        land_an=self._analyze_theory_landscape(cts)
        arch=self._design_model_architecture(cts,input_data.architecture_type,land_an)
        metrics=self._calculate_model_metrics(cts,arch)
        name=input_data.model_name or self._generate_model_name(cts,arch)
        desc=input_data.model_description or self._generate_model_description(cts,arch,metrics)
        formal=self._create_formalization_structure(input_data.formalization_level,arch,cts)
        um_props={"architecture_type":input_data.architecture_type.value,"formalization_level":input_data.formalization_level,"formalization_details":formal,"model_metrics":metrics,"component_theory_count":len(cts),"total_knowledge_coverage":self._calculate_total_coverage(cts),"architecture_details":arch,"synthesis_method":"hypercubic_integration_v1","model_version":"1.0.0"}
        um_evidence=[Evidence(source_doi="internal_process:um_synthesis",source_citation="Aletheia - MU",snippet=f"UM from {len(cts)} TCs via {input_data.architecture_type.value} arch.",confidence=0.85)]
        um=ScientificConcept(name=name[:255],description=desc,type=ConceptType.UNIFIED_MODEL,member_concept_ids=input_data.comprehensive_theory_ids,properties=um_props,evidence_sources=um_evidence)
        self.concept_repo.add(um); return UnifiedModelResult(model_created=um,model_metrics=metrics,architecture_diagram=arch)

# --- Use Case for Eje X (Document Ingestion) ---
class IngestDocumentInput(BaseModel):
    document_text: str
    source_doi: str
    source_citation: str

class IngestDocumentResult(BaseModel):
    document_concept_id: uuid.UUID
    ucm_extraction_result: UCMExtractionResult

class IngestDocumentUseCase:
    def __init__(self, concept_repo: ConceptRepository, extract_ucms_use_case: ExtractUCMsUseCase):
        self.concept_repo = concept_repo
        self.extract_ucms_use_case = extract_ucms_use_case

    def execute(self, input_data: IngestDocumentInput) -> IngestDocumentResult:
        doc_source_concept = ScientificConcept(
            name=f"Source: {input_data.source_citation[:100]}" + ("..." if len(input_data.source_citation) > 100 else ""),
            description=f"Document ingested with DOI: {input_data.source_doi}. Full citation: {input_data.source_citation}.",
            type=ConceptType.DOCUMENT_SOURCE,
            properties={
                "doi": input_data.source_doi,
                "citation": input_data.source_citation,
                "text_length": len(input_data.document_text)
            }
        )
        self.concept_repo.add(doc_source_concept)

        ucm_input = ExtractUCMsInput(
            document_text=input_data.document_text,
            source_doi=input_data.source_doi,
            source_citation=input_data.source_citation
        )
        ucm_extraction_result = self.extract_ucms_use_case.execute(ucm_input)

        return IngestDocumentResult(
            document_concept_id=doc_source_concept.id,
            ucm_extraction_result=ucm_extraction_result
        )
