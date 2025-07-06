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


def create_test_app() -> FastAPI:
    app = FastAPI(
        title="Aletheia Test API - Hypercubic Unified System",
        description="Test API for Scientific Discovery System.",
        version="0.1.0-test",
    )

    @app.post("/concepts/", response_model=ScientificConcept, status_code=status.HTTP_201_CREATED)
    def create_new_concept_endpoint( # Renamed to avoid clash if original api.py is also imported
        input_data: CreateConceptInput,
        use_case: KnowledgeSynthesisUseCase = Depends(get_test_knowledge_synthesis_use_case),
    ):
        return use_case.create_concept(input_data)

    @app.get("/concepts/", response_model=List[ScientificConcept])
    def list_all_concepts_endpoint( # Renamed
        use_case: KnowledgeSynthesisUseCase = Depends(get_test_knowledge_synthesis_use_case),
    ):
        return use_case.get_all_concepts()

    @app.get("/concepts/{concept_id}", response_model=ScientificConcept)
    def get_single_concept_endpoint( # Renamed
        concept_id: uuid.UUID,
        use_case: KnowledgeSynthesisUseCase = Depends(get_test_knowledge_synthesis_use_case),
    ):
        try:
            return use_case.get_concept_details(concept_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return app

# This allows test_api.py to do: from tests.presentation.api_for_test import app_for_testing
app_for_testing = create_test_app()

# Function to reset singletons, callable from test_api.py's fixture
def reset_test_repo_singletons():
    global _test_concept_repo_singleton, _test_relationship_repo_singleton
    _test_concept_repo_singleton = InMemoryConceptRepository()
    _test_relationship_repo_singleton = InMemoryRelationshipRepository()
    # print("DEBUG: Test repo singletons have been reset in api_for_test.py")
