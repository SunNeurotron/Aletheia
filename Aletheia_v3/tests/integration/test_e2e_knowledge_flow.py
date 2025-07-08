# Aletheia_v3/tests/integration/test_e2e_knowledge_flow.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
import uuid # For generating unique names/IDs if needed in test data

# Assuming common fixtures might be moved to a conftest.py or are accessible.
# For now, let's try to import from where they are defined if possible,
# or redefine simplified versions if necessary for this E2E test.

# Attempt to import necessary items from existing test setup
# This path might need adjustment if conftest.py is created at tests/ level
from ..test_api import app, override_get_db_session, SQLALCHEMY_DATABASE_URL_TEST, engine_test, SessionLocalTest
from Aletheia_v3.infrastructure.database import Base, get_db_session
from Aletheia_v3.api.auth import get_password_hash # For creating test user if not using fixture
from Aletheia_v3.infrastructure.models import ResearcherDB # For creating test user
from aletheia_common.auth.jwt_handler import UserInDB, get_user_retriever_dependency_placeholder # For overriding auth
from Aletheia_v3.api.auth import get_researcher_for_auth as get_aletheia_v3_user_retriever

# Import schemas for request/response validation
from Aletheia_v3.api.schemas import (
    IngestDocumentRequest, IngestDocumentResponse,
    FormClusterInputSchema, FormClusterResponseSchema, ConceptInfoSchema,
    PropositionDerivationInputSchema, PropositionDerivationResponseSchema,
    MiniTheoryConstructionInputSchema, MiniTheoryConstructionResponseSchema,
    ComprehensiveTheoriesInputSchema, ComprehensiveTheoriesResponseSchema,
    UnifiedModelsInputSchema, UnifiedModelsResponseSchema,
    ScientificConceptSchema # For validating concepts from /eje-x/concepts
)
from Aletheia_v3.core.domain_models import ConceptType # For asserting concept types

# --- Fixture for a clean database state for each test function ---
@pytest_asyncio.fixture(scope="function")
async def clean_test_db_session():
    # Create tables for each test run if they don't exist or after dropping
    Base.metadata.drop_all(bind=engine_test) # Drop all tables
    Base.metadata.create_all(bind=engine_test) # Create all tables

    # Override the app's DB session dependency
    app.dependency_overrides[get_db_session] = override_get_db_session

    # Override user retriever to use the test DB session
    # (This is similar to test_api.py, ensure it's correctly applied)
    async def get_researcher_for_auth_e2e_db(username: str, db = Depends(override_get_db_session)):
        researcher = db.query(ResearcherDB).filter(ResearcherDB.username == username).first()
        if researcher:
            return UserInDB(
                username=researcher.username, email=researcher.email, full_name=researcher.full_name,
                hashed_password=researcher.hashed_password, roles=["researcher"] + (["admin"] if researcher.is_admin else []),
                disabled=researcher.disabled
            )
        return None

    app.dependency_overrides[get_user_retriever_dependency_placeholder] = lambda: get_researcher_for_auth_e2e_db
    # This also implies that Aletheia_v3.api.auth.authenticate_user will use the overridden get_db_session

    db = SessionLocalTest()
    try:
        yield db # Provides the session to the test
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine_test) # Clean up after test
        # Clear overrides after test session to not affect other test files
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def e2e_test_client(clean_test_db_session) -> AsyncClient: # Depends on clean_test_db_session
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(scope="function")
async def e2e_researcher_token(e2e_test_client: AsyncClient, clean_test_db_session) -> str:
    # Create a test researcher directly in the DB for this E2E test
    db = clean_test_db_session # Get the session from the fixture

    username = "e2e_researcher"
    password = "e2e_password"

    existing_user = db.query(ResearcherDB).filter(ResearcherDB.username == username).first()
    if not existing_user:
        researcher = ResearcherDB(
            username=username,
            full_name="E2E Test Researcher",
            email="e2e_researcher@example.com",
            hashed_password=get_password_hash(password),
            is_admin=False,
            disabled=False
        )
        db.add(researcher)
        db.commit()

    # Login to get token
    login_data = {"username": username, "password": password}
    response = await e2e_test_client.post("/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK, f"E2E Token generation failed: {response.text}"
    return response.json()["access_token"]


@pytest.mark.asyncio
class TestE2EKnowledgeFlow:

    async def test_full_knowledge_pipeline(self, e2e_test_client: AsyncClient, e2e_researcher_token: str):
        client = e2e_test_client
        headers = {"Authorization": f"Bearer {e2e_researcher_token}"}

        # Rich text for ingestion
        ingest_text = (
            "Dr. Eleanor Vance, a leading astrophysicist at the Cygnus X-1 Institute, "
            "published her findings on dark energy. The study, supported by Project Chimera, "
            "suggests that dark energy's influence is not constant, challenging the Lambda-CDM model. "
            "Her work utilizes data from the Hubble Space Telescope, analyzed in London, UK."
        )

        # --- 1. Ingest Document (Eje X) ---
        ingest_payload = IngestDocumentRequest(
            document_text=ingest_text,
            source_doi=f"10.1234/e2e.{uuid.uuid4()}",
            source_citation="Vance, E. (2024). Fluctuations in Dark Energy. Journal of Cosmic Mysteries.",
            source_metadata={"keywords": ["dark energy", "cosmology", "Lambda-CDM"], "year": 2024}
        )
        response = await client.post("/api/v1/eje-x/ingest-document", json=ingest_payload.model_dump(), headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        ingest_response_data = IngestDocumentResponse(**response.json())

        document_source_id = ingest_response_data.document_source_id
        assert document_source_id is not None

        ucm_extraction_result = ingest_response_data.ucm_extraction_result
        assert ucm_extraction_result is not None
        ucm_ids = [ucm.id for ucm in ucm_extraction_result.extracted_concepts]
        # Expecting NER to find entities like "Eleanor Vance", "Cygnus X-1 Institute", "dark energy", "Lambda-CDM", "Hubble Space Telescope", "London"
        assert len(ucm_ids) > 3, f"Expected several UCMs from NER, got {len(ucm_ids)}"
        print(f"Ingested document {document_source_id}, extracted {len(ucm_ids)} UCMs: {ucm_ids}")

        # --- 2. List and Verify Concepts (Eje X) ---
        response = await client.get("/api/v1/eje-x/concepts", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        concepts_list = [ScientificConceptSchema(**item) for item in response.json()]

        found_doc_source = any(str(c.id) == document_source_id and c.concept_type == ConceptType.DOCUMENT_SOURCE.value for c in concepts_list)
        assert found_doc_source, f"Document source ID {document_source_id} not found or wrong type."

        found_ucms_count = sum(1 for c in concepts_list if str(c.id) in ucm_ids and c.concept_type == ConceptType.UCM.value)
        assert found_ucms_count == len(ucm_ids), "Not all extracted UCMs found or wrong type."
        print(f"Verified {found_ucms_count + 1} initial concepts via API.")

        # --- 3. Cluster Formation (Eje Y - Level 1) ---
        cluster_id = None
        if ucm_ids:
            cluster_payload = FormClusterInputSchema(ucm_ids=ucm_ids)
            response = await client.post("/api/v1/eje-y/cluster-formation", json=cluster_payload.model_dump(), headers=headers)
            assert response.status_code == status.HTTP_201_CREATED, f"Cluster formation failed: {response.text}"
            cluster_response_data = FormClusterResponseSchema(**response.json())
            assert len(cluster_response_data.created_clusters) >= 1, "Expected at least one cluster to be formed."
            cluster_id = cluster_response_data.created_clusters[0].id
            assert cluster_id is not None
            print(f"Formed cluster: {cluster_id}")
        else:
            pytest.skip("Skipping cluster formation as no UCMs were extracted.")

        # --- 4. Derive Propositions (Eje Y - Level 2) ---
        proposition_id = None
        if cluster_id:
            proposition_payload = PropositionDerivationInputSchema(cluster_ids=[cluster_id])
            response = await client.post("/api/v1/eje-y/proposition-derivation", json=proposition_payload.model_dump(), headers=headers)
            assert response.status_code == status.HTTP_201_CREATED, f"Proposition derivation failed: {response.text}"
            proposition_response_data = PropositionDerivationResponseSchema(**response.json())
            assert len(proposition_response_data.created_propositions) >= 1
            proposition_id = proposition_response_data.created_propositions[0].id
            assert proposition_id is not None
            print(f"Derived proposition: {proposition_id}")
        else:
            pytest.skip("Skipping proposition derivation as no cluster was formed.")

        # --- 5. Construct Mini-Theory (Eje Y - Level 3) ---
        mini_theory_id = None
        if proposition_id:
            mini_theory_payload = MiniTheoryConstructionInputSchema(proposition_ids=[proposition_id], name="E2E Mini Theory")
            response = await client.post("/api/v1/eje-y/mini-theory-construction", json=mini_theory_payload.model_dump(), headers=headers)
            assert response.status_code == status.HTTP_201_CREATED, f"Mini-theory construction failed: {response.text}"
            mini_theory_response_data = MiniTheoryConstructionResponseSchema(**response.json())
            assert mini_theory_response_data.created_mini_theory is not None
            mini_theory_id = mini_theory_response_data.created_mini_theory.id
            assert mini_theory_id is not None
            print(f"Constructed mini-theory: {mini_theory_id}")
        else:
            pytest.skip("Skipping mini-theory construction as no proposition was derived.")

        # --- 6. (Optional) Comprehensive Theory ---
        comp_theory_id = None
        if mini_theory_id:
            comp_theory_payload = ComprehensiveTheoriesInputSchema(mini_theory_ids=[mini_theory_id], name="E2E Comprehensive Theory")
            response = await client.post("/api/v1/eje-y/comprehensive-theories", json=comp_theory_payload.model_dump(), headers=headers)
            assert response.status_code == status.HTTP_201_CREATED, f"Comprehensive theory construction failed: {response.text}"
            comp_theory_response_data = ComprehensiveTheoriesResponseSchema(**response.json())
            assert comp_theory_response_data.created_comprehensive_theory is not None
            comp_theory_id = comp_theory_response_data.created_comprehensive_theory.id
            assert comp_theory_id is not None
            print(f"Constructed comprehensive theory: {comp_theory_id}")
        else:
            pytest.skip("Skipping comprehensive theory construction.")

        # --- (Optional) Unified Model ---
        unified_model_id = None
        if comp_theory_id:
            unified_model_payload = UnifiedModelsInputSchema(comprehensive_theory_ids=[comp_theory_id], name="E2E Unified Model")
            response = await client.post("/api/v1/eje-y/unified-models", json=unified_model_payload.model_dump(), headers=headers)
            assert response.status_code == status.HTTP_201_CREATED, f"Unified model synthesis failed: {response.text}"
            unified_model_response_data = UnifiedModelsResponseSchema(**response.json())
            assert unified_model_response_data.created_unified_model is not None
            unified_model_id = unified_model_response_data.created_unified_model.id
            assert unified_model_id is not None
            print(f"Synthesized unified model: {unified_model_id}")
        else:
            pytest.skip("Skipping unified model synthesis.")

        # --- 7. Final Verification ---
        response = await client.get("/api/v1/eje-x/concepts", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        final_concepts_list = [ScientificConceptSchema(**item) for item in response.json()]

        final_concept_map = {str(c.id): c for c in final_concepts_list}

        assert document_source_id in final_concept_map
        for ucm_id_str in ucm_ids:
            assert ucm_id_str in final_concept_map
            assert final_concept_map[ucm_id_str].concept_type == ConceptType.UCM.value

        if cluster_id:
            assert cluster_id in final_concept_map
            assert final_concept_map[cluster_id].concept_type == ConceptType.CLUSTER.value
            assert "member_ucm_ids" in final_concept_map[cluster_id].properties
        if proposition_id:
            assert proposition_id in final_concept_map
            assert final_concept_map[proposition_id].concept_type == ConceptType.PROPOSITION.value
            assert "based_on_cluster_id" in final_concept_map[proposition_id].properties
        if mini_theory_id:
            assert mini_theory_id in final_concept_map
            assert final_concept_map[mini_theory_id].concept_type == ConceptType.MINI_THEORY.value
            assert "member_proposition_ids" in final_concept_map[mini_theory_id].properties
        if comp_theory_id:
            assert comp_theory_id in final_concept_map
            assert final_concept_map[comp_theory_id].concept_type == ConceptType.COMPREHENSIVE_THEORY.value
        if unified_model_id:
            assert unified_model_id in final_concept_map
            assert final_concept_map[unified_model_id].concept_type == ConceptType.UNIFIED_MODEL.value

        print("E2E knowledge flow test completed successfully up to implemented stages.")
