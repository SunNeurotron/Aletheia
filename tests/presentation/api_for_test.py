"""
Test-local FastAPI application setup.

This module creates a FastAPI app instance using components from their
test-local temporary locations to ensure they are importable in the sandbox.
"""
import uuid
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status

# Import components from their test-local temporary locations
from tests.application.use_cases.use_cases_for_test import (
    KnowledgeSynthesisUseCase,
    CreateConceptInput,
    ExtractUCMsUseCase,
    ExtractUCMsInput,
    UCMExtractionResult,
    FormClustersUseCase,
    FormClusterInput,
    ClusterFormationResult,
    DerivePropositionsUseCase,
    DerivePropositionInput,
    PropositionDerivationResult,
    ConstructMiniTheoryUseCase,
    ConstructMiniTheoryInput,
    MiniTheoryConstructionResult,
    ConstructComprehensiveTheoryUseCase, # Added
    ConstructComprehensiveTheoryInput,   # Added
    ComprehensiveTheoryResult,           # Added
    ConstructUnifiedModelUseCase,        # Added
    ConstructUnifiedModelInput,
    UnifiedModelResult,
    IngestDocumentUseCase,
    IngestDocumentInput,
    IngestDocumentResult,
    LinkConceptsUseCase, # Added
    LinkConceptsInput,   # Added
    LinkConceptsResult   # Added
)
from tests.application.ports.ports_for_test import (
    ConceptRepository as ConceptRepoProtocol,
    RelationshipRepository as RelationshipRepoProtocol,
)
from tests.domain.domain_for_test import ScientificConcept
from tests.infrastructure.database.repos_for_test import (
    InMemoryConceptRepository,
    InMemoryRelationshipRepository,
)

# Create singletons for the test app context
# These will be fresh for each test run if tests/presentation/test_api.py re-imports this module
# or if we explicitly reset them. The fixture in test_api.py will handle resetting.
_test_concept_repo_singleton = InMemoryConceptRepository()
_test_relationship_repo_singleton = InMemoryRelationshipRepository()


def get_test_concept_repo() -> ConceptRepoProtocol: # Hint with the (forward-declared) protocol
    return _test_concept_repo_singleton

def get_test_relationship_repo() -> RelationshipRepoProtocol: # Hint with the (forward-declared) protocol
    return _test_relationship_repo_singleton

def get_test_knowledge_synthesis_use_case(
    concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo),
    relationship_repo: RelationshipRepoProtocol = Depends(get_test_relationship_repo),
) -> KnowledgeSynthesisUseCase:
    return KnowledgeSynthesisUseCase(concept_repo, relationship_repo)

def get_extract_ucms_use_case(
    concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)
) -> ExtractUCMsUseCase:
    return ExtractUCMsUseCase(concept_repo=concept_repo)

def get_form_clusters_use_case(
    concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)
) -> FormClustersUseCase:
    return FormClustersUseCase(concept_repo=concept_repo)

def get_derive_propositions_use_case(
    concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo),
    relationship_repo: RelationshipRepoProtocol = Depends(get_test_relationship_repo)
) -> DerivePropositionsUseCase:
    return DerivePropositionsUseCase(concept_repo=concept_repo, relationship_repo=relationship_repo)

def get_construct_mini_theory_use_case(
    concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)
) -> ConstructMiniTheoryUseCase:
    return ConstructMiniTheoryUseCase(concept_repo=concept_repo)

def get_construct_comprehensive_theory_use_case(
    concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)
) -> ConstructComprehensiveTheoryUseCase:
    return ConstructComprehensiveTheoryUseCase(concept_repo=concept_repo)

def get_construct_unified_model_use_case(
    concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)
) -> ConstructUnifiedModelUseCase:
    return ConstructUnifiedModelUseCase(concept_repo=concept_repo)

# get_extract_ucms_use_case is already defined

def get_ingest_document_use_case(
    concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo),
    extract_ucms_uc: ExtractUCMsUseCase = Depends(get_extract_ucms_use_case)
) -> IngestDocumentUseCase:
    return IngestDocumentUseCase(concept_repo=concept_repo, extract_ucms_use_case=extract_ucms_uc)

def get_link_concepts_use_case(
    concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo),
    relationship_repo: RelationshipRepoProtocol = Depends(get_test_relationship_repo)
) -> LinkConceptsUseCase:
    return LinkConceptsUseCase(concept_repo=concept_repo, relationship_repo=relationship_repo)


def create_test_app() -> FastAPI:
    app = FastAPI(
        title="Aletheia Test API - Hypercubic Unified System",
        description="Test API for Scientific Discovery System.",
        version="0.1.0-test",
    )

    # --- Eje Z/Y Basic Concept Endpoints ---
    @app.post("/concepts/", response_model=ScientificConcept, status_code=status.HTTP_201_CREATED, tags=["Concepts"])
    def create_new_concept_endpoint(
        input_data: CreateConceptInput,
        use_case: KnowledgeSynthesisUseCase = Depends(get_test_knowledge_synthesis_use_case),
    ):
        return use_case.create_concept(input_data)

    @app.get("/concepts/", response_model=List[ScientificConcept], tags=["Concepts"])
    def list_all_concepts_endpoint(
        use_case: KnowledgeSynthesisUseCase = Depends(get_test_knowledge_synthesis_use_case),
    ):
        return use_case.get_all_concepts()

    @app.get("/concepts/{concept_id}", response_model=ScientificConcept, tags=["Concepts"])
    def get_single_concept_endpoint(
        concept_id: uuid.UUID,
        use_case: KnowledgeSynthesisUseCase = Depends(get_test_knowledge_synthesis_use_case),
    ):
        try:
            return use_case.get_concept_details(concept_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # --- Eje Y - Progressive Construction Endpoints ---
    @app.post("/eje_y/ucm_extraction/", response_model=UCMExtractionResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def extract_ucms_endpoint(
        input_data: ExtractUCMsInput,
        use_case: ExtractUCMsUseCase = Depends(get_extract_ucms_use_case),
    ):
        """Extracts Unit Conceptual Mínimas (UCMs) from document text."""
        return use_case.execute(input_data)

    @app.post("/eje_y/cluster_formation/", response_model=ClusterFormationResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def form_cluster_endpoint(
        input_data: FormClusterInput,
        use_case: FormClustersUseCase = Depends(get_form_clusters_use_case),
    ):
        """Forms a conceptual cluster from a list of UCM IDs."""
        try:
            return use_case.execute(input_data)
        except ValueError as e: # Catching potential ValueErrors from use case (e.g. UCM not found)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @app.post("/eje_y/proposition_derivation/", response_model=PropositionDerivationResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def derive_proposition_endpoint(
        input_data: DerivePropositionInput,
        use_case: DerivePropositionsUseCase = Depends(get_derive_propositions_use_case),
    ):
        """Derives a proposition from a given conceptual cluster ID."""
        try:
            return use_case.execute(input_data)
        except ValueError as e: # Catching potential ValueErrors from use case (e.g. Cluster not found)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @app.post("/eje_y/mini_theory_construction/", response_model=MiniTheoryConstructionResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def construct_mini_theory_endpoint(
        input_data: ConstructMiniTheoryInput,
        use_case: ConstructMiniTheoryUseCase = Depends(get_construct_mini_theory_use_case),
    ):
        """Constructs a mini-theory from a list of proposition IDs."""
        try:
            return use_case.execute(input_data)
        except ValueError as e: # Catching potential ValueErrors (e.g. proposition not found / not a proposition)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @app.post("/eje_y/comprehensive_theories/", response_model=ComprehensiveTheoryResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def construct_comprehensive_theory_endpoint(
        input_data: ConstructComprehensiveTheoryInput,
        use_case: ConstructComprehensiveTheoryUseCase = Depends(get_construct_comprehensive_theory_use_case),
    ):
        """Constructs a Comprehensive Theory from a list of Mini-Theory IDs."""
        try:
            return use_case.execute(input_data)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @app.post("/eje_y/unified_models/", response_model=UnifiedModelResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def construct_unified_model_endpoint(
        input_data: ConstructUnifiedModelInput,
        use_case: ConstructUnifiedModelUseCase = Depends(get_construct_unified_model_use_case),
    ):
        """Constructs a Unified Model from a list of Comprehensive Theory IDs."""
        try:
            return use_case.execute(input_data)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # --- Eje X - Document Ingestion Endpoint ---
    @app.post("/eje_x/documents/ingest/", response_model=IngestDocumentResult, status_code=status.HTTP_201_CREATED, tags=["Eje X - Ingestion"])
    def ingest_document_endpoint(
        input_data: IngestDocumentInput,
        use_case: IngestDocumentUseCase = Depends(get_ingest_document_use_case),
    ):
        """Ingests a document and extracts UCMs."""
        try:
            return use_case.execute(input_data)
        except Exception as e:
            # Log the exception e
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

    @app.post("/eje_x/relationships/", response_model=LinkConceptsResult, status_code=status.HTTP_201_CREATED, tags=["Eje X - Ontology"])
    def link_concepts_endpoint(
        input_data: LinkConceptsInput,
        use_case: LinkConceptsUseCase = Depends(get_link_concepts_use_case),
    ):
        """Creates a new directed relationship between two concepts."""
        try:
            return use_case.execute(input_data)
        except ValueError as e: # For concept not found
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            # Log the exception e
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

    return app

# This allows test_api.py to do: from tests.presentation.api_for_test import app_for_testing
app_for_testing = create_test_app()

# Function to reset singletons, callable from test_api.py's fixture
def reset_test_repo_singletons():
    global _test_concept_repo_singleton, _test_relationship_repo_singleton
    _test_concept_repo_singleton = InMemoryConceptRepository()
    _test_relationship_repo_singleton = InMemoryRelationshipRepository()
    # print("DEBUG: Test repo singletons have been reset in api_for_test.py")
