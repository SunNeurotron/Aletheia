"""
Temporary location for use case definitions to make them accessible to tests
in this sandboxed environment.
"""
import uuid
from typing import List, Dict, Any, Optional # Added Optional
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
        concept_repo: ConceptRepository, # Uses the forward-declared class
        relationship_repo: RelationshipRepository # Uses the forward-declared class
    ):
        self.concept_repo = concept_repo
        self.relationship_repo = relationship_repo

    def create_concept(self, input_data: CreateConceptInput) -> ScientificConcept:
        """
        Creates a new scientific concept and persists it.
        """
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
        """
        Retrieves all scientific concepts.
        """
        return self.concept_repo.list_all()

    def get_concept_details(self, concept_id: uuid.UUID) -> ScientificConcept:
        """
        Retrieves a single concept by its ID.
        """
        concept = self.concept_repo.get_by_id(concept_id)
        if not concept:
            raise ValueError(f"Concept with ID {concept_id} not found.")
        return concept


# --- Use Cases for Eje Y (Progressive Construction) ---

class ExtractUCMsInput(BaseModel):
    document_text: str # Simplified input: raw text
    source_doi: str
    source_citation: str

class UCMExtractionResult(BaseModel):
    ucms_created: List[ScientificConcept]
    # Potential future fields: number_of_ucms, processing_time_ms

class ExtractUCMsUseCase:
    """
    Use case for extracting Unit Conceptual Mínimas (UCMs) from a document.
    """
    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo

    def execute(self, input_data: ExtractUCMsInput) -> UCMExtractionResult:
        """
        Simulates UCM extraction.
        In a real scenario, this would involve complex NLP.
        Here, we'll create a few dummy UCMs based on the input.
        """
        # Simplified/Simulated UCM extraction logic
        # Example: create one UCM for every 10 words, or find Nouns.
        # For now, let's just create a couple of placeholder UCMs.

        ucms = []
        placeholder_names = ["Simulated UCM 1 from " + input_data.source_doi,
                             "Simulated UCM 2 from " + input_data.source_doi]

        for i, name in enumerate(placeholder_names):
            # Simple hash simulation
            verification_hash = hex(hash(name + input_data.document_text[:10]))[2:]

            ucm = ScientificConcept(
                name=name,
                description=f"Placeholder UCM {i+1} extracted from '{input_data.document_text[:30]}...'",
                type=ConceptType.UCM,
                properties={"simulated_extraction": True, "source_length": len(input_data.document_text)},
                evidence_sources=[
                    Evidence(
                        source_doi=input_data.source_doi,
                        source_citation=input_data.source_citation,
                        snippet=input_data.document_text[:100], # Example snippet
                        confidence=0.75 # Simulated confidence
                    )
                ],
                verification_hash=verification_hash
            )
            self.concept_repo.add(ucm)
            ucms.append(ucm)

        return UCMExtractionResult(ucms_created=ucms)


class FormClusterInput(BaseModel):
    ucm_ids: List[uuid.UUID]
    cluster_name: Optional[str] = "Unnamed Cluster"
    cluster_description: Optional[str] = "A cluster formed from selected UCMs."

class ClusterFormationResult(BaseModel):
    cluster_created: ScientificConcept
    # Potential future fields: cohesion_score, silhouette_score

class FormClustersUseCase:
    """
    Use case for forming a conceptual cluster from a list of UCMs.
    """
    def __init__(self, concept_repo: ConceptRepository):
        self.concept_repo = concept_repo

    def execute(self, input_data: FormClusterInput) -> ClusterFormationResult:
        """
        Simulates cluster formation.
        Real logic would involve semantic analysis, graph algorithms, etc.
        """
        # Validate UCMs exist (simplified check)
        member_ucms = []
        for ucm_id in input_data.ucm_ids:
            ucm = self.concept_repo.get_by_id(ucm_id)
            if not ucm or ucm.type != ConceptType.UCM:
                raise ValueError(f"Invalid or non-UCM concept ID provided: {ucm_id}")
            member_ucms.append(ucm)

        if not member_ucms:
            raise ValueError("No UCMs provided to form a cluster.")

        # Simulated cluster properties
        # For example, derive properties from member UCMs
        avg_confidence = sum(e.confidence for ucm in member_ucms for e in ucm.evidence_sources) / \
                         sum(len(ucm.evidence_sources) for ucm in member_ucms) if \
                         sum(len(ucm.evidence_sources) for ucm in member_ucms) > 0 else 0

        # Ensure name and description are strings, using defaults from FormClusterInput if None was explicitly passed
        # Pydantic model defaults are used if fields are omitted, but client can pass explicit null.
        name_for_cluster = input_data.cluster_name if input_data.cluster_name is not None else FormClusterInput.model_fields["cluster_name"].default
        description_for_cluster = input_data.cluster_description if input_data.cluster_description is not None else FormClusterInput.model_fields["cluster_description"].default

        # The defaults in FormClusterInput are already strings, so if Pydantic populated them, they are strings.
        # The issue is if a client sends `null`.
        # A simpler way, relying on Pydantic defaults for omitted fields, and handling explicit None:
        final_name = input_data.cluster_name if input_data.cluster_name is not None else "Unnamed Cluster"
        final_description = input_data.cluster_description if input_data.cluster_description is not None else "A cluster formed from selected UCMs."


        cluster = ScientificConcept(
            name=final_name,
            description=final_description,
            type=ConceptType.CLUSTER,
            properties={"ucm_count": len(input_data.ucm_ids), "avg_member_confidence": avg_confidence},
            member_concept_ids=input_data.ucm_ids,
            # Evidence for a cluster could be the UCMs themselves or derived
            evidence_sources=[
                Evidence(
                    source_doi="internal_process:cluster_formation",
                    source_citation="Aletheia System",
                    snippet=f"Cluster formed from {len(input_data.ucm_ids)} UCMs.",
                    confidence=1.0
                )
            ]
        )
        self.concept_repo.add(cluster)
        return ClusterFormationResult(cluster_created=cluster)


class DerivePropositionInput(BaseModel):
    cluster_id: uuid.UUID
    proposition_text: Optional[str] = None # Could be auto-generated

class PropositionDerivationResult(BaseModel):
    proposition_created: ScientificConcept

class DerivePropositionsUseCase:
    """
    Use case for deriving a proposition from a conceptual cluster.
    """
    def __init__(self, concept_repo: ConceptRepository, relationship_repo: RelationshipRepository):
        self.concept_repo = concept_repo
        self.relationship_repo = relationship_repo # Might be used to link proposition to concepts

    def execute(self, input_data: DerivePropositionInput) -> PropositionDerivationResult:
        """
        Simulates proposition derivation.
        """
        cluster = self.concept_repo.get_by_id(input_data.cluster_id)
        if not cluster or cluster.type != ConceptType.CLUSTER:
            raise ValueError(f"Invalid or non-CLUSTER concept ID provided for proposition derivation: {input_data.cluster_id}")

        proposition_name = input_data.proposition_text or f"Proposition derived from Cluster {cluster.name[:20]}"

        # Simulated proposition logic
        # Example: "Concepts in Cluster X are strongly related."
        # Or, if the cluster has specific UCMs, try to form a statement.
        # For now, a generic proposition.

        description = f"This proposition, '{proposition_name}', summarizes or emerges from the conceptual cluster '{cluster.name}' (ID: {cluster.id})."
        if cluster.member_concept_ids:
            description += f" The cluster consists of {len(cluster.member_concept_ids)} member concepts."


        proposition = ScientificConcept(
            name=proposition_name,
            description=description,
            type=ConceptType.PROPOSITION,
            derived_from_cluster_id=input_data.cluster_id,
            properties={"derivation_method": "simulated_heuristic"},
            evidence_sources=[
                Evidence(
                    source_doi="internal_process:proposition_derivation",
                    source_citation="Aletheia System",
                    snippet=f"Proposition derived from cluster {cluster.id}.",
                    confidence=0.9
                )
            ]
        )
        self.concept_repo.add(proposition)

        # Optionally, create relationships from this proposition to concepts in the cluster
        # This would require more complex logic and use of relationship_repo

        return PropositionDerivationResult(proposition_created=proposition)
