"""
Integration tests for the API (presentation layer).

These tests verify the full flow from HTTP request through the API,
use cases, and down to the in-memory repository implementations.
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from tests.presentation.api_for_test import app_for_testing, reset_test_repo_singletons

client = TestClient(app_for_testing)

@pytest.fixture(autouse=True)
def reset_in_memory_repos_fixture():
    reset_test_repo_singletons()
    yield

class TestConceptAPI:
    def test_create_new_concept_success(self):
        response = client.post(
            "/concepts/",
            json={
                "name": "API Test Concept",
                "description": "Created via API test.",
                "type": "PHENOMENON", # Valid type
                "properties": {"source": "api_test"},
                "evidence_sources": [
                    {"source_doi": "api:test/123", "source_citation": "API Test 2024", "snippet": "test snippet", "confidence": 0.99}
                ]
            },
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["name"] == "API Test Concept"
        assert data["type"] == "PHENOMENON"
        assert data["properties"]["source"] == "api_test"
        assert len(data["evidence_sources"]) == 1
        assert data["evidence_sources"][0]["confidence"] == 0.99
        assert "id" in data

    def test_create_new_concept_invalid_input_type(self):
        response = client.post(
            "/concepts/",
            json={
                "name": "Invalid Type",
                "description": "Trying to create with invalid type.",
                "type": "INVALID_CONCEPT_TYPE",
            },
        )
        assert response.status_code == 422, response.text

    def test_create_new_concept_missing_name(self):
        response = client.post(
            "/concepts/",
            json={
                "description": "Missing name field.",
                "type": "SUBSTANCE", # Valid type
            },
        )
        assert response.status_code == 422, response.text

    def test_list_all_concepts_empty(self):
        response = client.get("/concepts/")
        assert response.status_code == 200, response.text
        assert response.json() == []

    def test_list_all_concepts_with_data(self):
        concept_payload_a = {
            "name": "Concept A", "description": "Desc A", "type": "MECHANISM" # Valid type
        }
        create_response_a = client.post("/concepts/", json=concept_payload_a)
        assert create_response_a.status_code == 201, create_response_a.text

        concept_payload_b = {
            "name": "Concept B", "description": "Desc B", "type": "EVIDENCE_UNIT" # Corrected valid type
        }
        create_response_b = client.post("/concepts/", json=concept_payload_b)
        assert create_response_b.status_code == 201, create_response_b.text

        response = client.get("/concepts/")
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 2
        names = {item["name"] for item in data}
        assert "Concept A" in names
        assert "Concept B" in names

    def test_get_single_concept_found(self):
        concept_payload = {
            "name": "FindMe Concept", "description": "Details of FindMe.", "type": "HYPOTHESIS" # Valid type
        }
        create_response = client.post("/concepts/", json=concept_payload)
        assert create_response.status_code == 201, create_response.text
        concept_id = create_response.json()["id"]

        response = client.get(f"/concepts/{concept_id}")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == concept_id
        assert data["name"] == "FindMe Concept"

    def test_get_single_concept_not_found(self):
        non_existent_id = uuid.uuid4()
        response = client.get(f"/concepts/{non_existent_id}")
        assert response.status_code == 404, response.text
        assert response.json()["detail"] == f"Concept with ID {non_existent_id} not found."

    def test_get_single_concept_invalid_uuid_format(self):
        response = client.get("/concepts/this-is-not-a-uuid")
        assert response.status_code == 422, response.text


class TestEjeYAPI:
    def test_extract_ucms_endpoint_success(self):
        payload = {
            "document_text": "Important Findings include P53 and Cancer. Also BRCA1 Gene.",
            "source_doi": "doi:10.1234/cancer.res.2024",
            "source_citation": "Smith et al. Cancer Research 2024"
        }
        response = client.post("/eje_y/ucm_extraction/", json=payload)
        assert response.status_code == 201, response.text
        data = response.json()
        assert "ucms_created" in data

        # Expected UCMs: "Important Findings", "P53", "Cancer", "BRCA1 Gene"
        # "Also" is a stopword.
        created_names = {ucm["name"] for ucm in data["ucms_created"]}
        expected_names = {"Important Findings", "P53", "Cancer", "BRCA1 Gene"}
        assert created_names == expected_names
        assert len(data["ucms_created"]) == 4

        for ucm in data["ucms_created"]:
            assert ucm["type"] == "UCM"
            assert ucm["verification_hash"] is not None
            assert ucm["evidence_sources"][0]["source_doi"] == payload["source_doi"]

    def test_form_cluster_endpoint_success(self):
        ucm_payloads = [
            {"name": "UCM A for Cluster", "description": "desc a", "type": "UCM", "evidence_sources": [{"source_doi":"d1","source_citation":"c1","snippet":"s1","confidence":0.9}]},
            {"name": "UCM B for Cluster", "description": "desc b", "type": "UCM", "evidence_sources": [{"source_doi":"d2","source_citation":"c2","snippet":"s2","confidence":0.8}]}
        ]
        ucm_ids = []
        for payload in ucm_payloads:
            resp = client.post("/concepts/", json=payload) # Create UCMs as concepts
            assert resp.status_code == 201, resp.text
            ucm_ids.append(resp.json()["id"])

        cluster_payload = {
            "ucm_ids": ucm_ids,
            "cluster_name": "BioCluster Alpha",
            "cluster_description": "A cluster of UCM A and UCM B."
        }
        response = client.post("/eje_y/cluster_formation/", json=cluster_payload)
        assert response.status_code == 201, response.text
        data = response.json()
        assert "cluster_created" in data
        cluster = data["cluster_created"]
        assert cluster["name"] == "BioCluster Alpha"
        assert cluster["type"] == "CLUSTER"
        assert sorted(cluster["member_concept_ids"]) == sorted(ucm_ids)
        assert cluster["properties"]["ucm_count"] == 2

        # Save cluster_id for the next test in a way that reset_fixture won't clear easily
        # This is generally not ideal for test independence but useful for simple sequences.
        # A better way would be to make tests fully independent or use pytest-dependency.
        # For now, we'll create the cluster within the proposition test.

    def test_form_cluster_endpoint_ucm_not_found(self):
        non_existent_ucm_id = str(uuid.uuid4())
        cluster_payload = {
            "ucm_ids": [non_existent_ucm_id],
            "cluster_name": "Bad Cluster"
        }
        response = client.post("/eje_y/cluster_formation/", json=cluster_payload)
        assert response.status_code == 400, response.text
        assert non_existent_ucm_id in response.json()["detail"]

    def test_derive_proposition_endpoint_success(self):
        # Create necessary UCMs and a Cluster for this test to be independent
        ucm_payload = {"name": "UCM for Prop Test", "description":"desc", "type":"UCM"}
        ucm_resp = client.post("/concepts/", json=ucm_payload)
        assert ucm_resp.status_code == 201, ucm_resp.text
        ucm_id = ucm_resp.json()["id"]

        cluster_payload = {"ucm_ids": [ucm_id], "cluster_name":"PropCluster Test"}
        cluster_resp = client.post("/eje_y/cluster_formation/", json=cluster_payload)
        assert cluster_resp.status_code == 201, cluster_resp.text
        cluster_id_for_prop = cluster_resp.json()["cluster_created"]["id"]

        proposition_payload = {
            "cluster_id": cluster_id_for_prop,
            "proposition_text": "Key insight from PropCluster Test."
        }
        response = client.post("/eje_y/proposition_derivation/", json=proposition_payload)
        assert response.status_code == 201, response.text # This was the failing assert
        data = response.json()
        assert "proposition_created" in data
        proposition = data["proposition_created"]
        assert proposition["name"] == "Key insight from PropCluster Test."
        assert proposition["type"] == "PROPOSITION"
        assert proposition["derived_from_cluster_id"] == cluster_id_for_prop

    def test_derive_proposition_endpoint_cluster_not_found(self):
        non_existent_cluster_id = str(uuid.uuid4())
        proposition_payload = {
            "cluster_id": non_existent_cluster_id,
            "proposition_text": "Insight from nowhere."
        }
        response = client.post("/eje_y/proposition_derivation/", json=proposition_payload)
        assert response.status_code == 400, response.text
        assert non_existent_cluster_id in response.json()["detail"]

    # --- Tests for Comprehensive Theory Construction Endpoint (added in this step) ---
    def test_construct_comprehensive_theory_endpoint_success(self):
        # 1. Create Propositions
        prop_ids = []
        for i in range(2):
            p_resp = client.post("/concepts/", json={"name": f"Prop MT{i+1}", "description": "desc", "type": "PROPOSITION"})
            assert p_resp.status_code == 201, p_resp.text
            prop_ids.append(p_resp.json()["id"])

        # 2. Create Mini-Theories from these propositions
        mt_ids = []
        for prop_id in prop_ids: # Create a simple MT for each prop for this test
            mt_resp = client.post("/eje_y/mini_theory_construction/", json={
                "proposition_ids": [prop_id],
                "mini_theory_name": f"MT for Prop {prop_id[:4]}"
            })
            assert mt_resp.status_code == 201, mt_resp.text
            mt_ids.append(mt_resp.json()["mini_theory_created"]["id"])

        assert len(mt_ids) == 2

        # 3. Construct a Comprehensive Theory
        ct_payload = {
            "mini_theory_ids": mt_ids,
            "theory_name": "API Comprehensive Theory",
            "integration_method": "HIERARCHICAL_INTEGRATION"
        }
        response = client.post("/eje_y/comprehensive_theories/", json=ct_payload)
        assert response.status_code == 201, response.text
        data = response.json()

        assert "theory_created" in data
        ct = data["theory_created"]
        assert ct["name"] == "API Comprehensive Theory"
        assert ct["type"] == "COMPREHENSIVE_THEORY"
        assert sorted(ct["member_concept_ids"]) == sorted(mt_ids)
        assert ct["properties"]["component_mini_theory_count"] == 2
        assert ct["properties"]["integration_method"] == "HIERARCHICAL_INTEGRATION"
        assert data["integration_analysis"] is not None # Since we have 2 MTs

    def test_construct_comprehensive_theory_endpoint_invalid_mt_id(self):
        non_existent_mt_id = str(uuid.uuid4())
        ct_payload = {"mini_theory_ids": [non_existent_mt_id]}
        response = client.post("/eje_y/comprehensive_theories/", json=ct_payload)
        assert response.status_code == 400, response.text
        assert non_existent_mt_id in response.json()["detail"]
        assert "non-MINI_THEORY" in response.json()["detail"]

    # --- Tests for Unified Model Construction Endpoint (added in this step) ---
    def test_construct_unified_model_endpoint_success(self):
        # 1. Create Propositions -> Mini-Theories -> Comprehensive Theories
        # For simplicity, create one CT
        prop_resp = client.post("/concepts/", json={"name": "Prop UM", "description": "desc", "type": "PROPOSITION"})
        prop_id = prop_resp.json()["id"]
        mt_resp = client.post("/eje_y/mini_theory_construction/", json={"proposition_ids": [prop_id], "mini_theory_name": "MT for UM"})
        mt_id = mt_resp.json()["mini_theory_created"]["id"]
        ct_resp = client.post("/eje_y/comprehensive_theories/", json={"mini_theory_ids": [mt_id], "theory_name": "CT for UM"})
        assert ct_resp.status_code == 201, ct_resp.text
        ct_id = ct_resp.json()["theory_created"]["id"]

        # 2. Construct Unified Model
        um_payload = {
            "comprehensive_theory_ids": [ct_id],
            "model_name": "API Unified Model",
            "architecture_type": "LAYERED"
        }
        response = client.post("/eje_y/unified_models/", json=um_payload)
        assert response.status_code == 201, response.text
        data = response.json()

        assert "model_created" in data
        um = data["model_created"]
        assert um["name"] == "API Unified Model"
        assert um["type"] == "UNIFIED_MODEL"
        assert um["member_concept_ids"] == [ct_id]
        assert um["properties"]["component_theory_count"] == 1
        assert um["properties"]["architecture_type"] == "LAYERED"
        assert "model_metrics" in um["properties"]
        assert "architecture_details" in um["properties"]
        assert data["model_metrics"] is not None
        assert data["architecture_diagram"] is not None

    def test_construct_unified_model_endpoint_invalid_ct_id(self):
        non_existent_ct_id = str(uuid.uuid4())
        um_payload = {"comprehensive_theory_ids": [non_existent_ct_id]}
        response = client.post("/eje_y/unified_models/", json=um_payload)
        assert response.status_code == 400, response.text
        assert non_existent_ct_id in response.json()["detail"]
        assert "non-COMPREHENSIVE_THEORY" in response.json()["detail"]


class TestEjeXAPI:
    def test_ingest_document_endpoint_success(self):
        payload = {
            "document_text": "This is a new Document for testing. It mentions Important Concept and Another One.",
            "source_doi": "doi:10.xxxx/ejeX.doc1",
            "source_citation": "EjeX Ingestion Test, 2024"
        }
        response = client.post("/eje_x/documents/ingest/", json=payload)
        assert response.status_code == 201, response.text
        data = response.json()

        assert "document_concept_id" in data
        assert uuid.UUID(data["document_concept_id"]) is not None # Check it's a valid UUID

        assert "ucm_extraction_result" in data
        ucm_result = data["ucm_extraction_result"]
        assert "ucms_created" in ucm_result

        # Check UCMs based on the current ExtractUCMsUseCase logic
        # Input: "This is a new Document for testing. It mentions Important Concept and Another One."
        # Stopwords: "this", "is", "a", "for", "it", "and", "another", "one" (if "one" is added or len<3 filter)
        # Phrase Regex: \b(?:[A-Z][\w"\'-]*\s+){1,5}[A-Z][\w"\'-]*\b (needs >=2 capitalized words)
        #   - "Important Concept"
        # Single Word Regex: \b[A-Z][\w"\'-]+\b
        #   - "Document"
        #   - "Important" (covered by "Important Concept")
        #   - "Concept" (covered by "Important Concept")
        #   - "Another" (stopword)
        #   - "One" (if len < 3, filtered. If "one" is stopword, filtered. Otherwise, potentially "One")
        # Let's assume "One" is filtered by length or stopword for now.
        # Expected UCMs: "Important Concept", "Document"

        created_ucm_names = {ucm["name"] for ucm in ucm_result["ucms_created"]}
        # This expectation depends heavily on the exact behavior of ExtractUCMsUseCase's regex & cleaning
        # For "Important Concept and Another One.":
        # Phrase: "Important Concept"
        # Single: "Another" (stopword), "One" (stopword or too short)
        # Expected from "This is a new Document for testing." -> "Document"
        # Expected from "It mentions Important Concept and Another One." -> "Important Concept"

        # Based on current ExtractUCMsUseCase_v4:
        # Sentence 1: "This is a new Document for testing." -> single "Document"
        # Sentence 2: "It mentions Important Concept and Another One." -> phrase "Important Concept"
        # Expected: {"Document", "Important Concept"}

        assert len(ucm_result["ucms_created"]) >= 1 # Should find at least "Document" or "Important Concept"
        assert "Document" in created_ucm_names or "Important Concept" in created_ucm_names # Be a bit flexible

        # To be more precise, let's use the example that worked in unit tests for ExtractUCMs
        payload_precise = {
            "document_text": "The Study focuses on Protein Alpha and its effects on Alzheimer's Disease. Another key factor is Beta-Catenin.",
            "source_doi": "doi:10.xxxx/ejeX.doc2",
            "source_citation": "EjeX Ingestion Test Precise, 2024"
        }
        response_precise = client.post("/eje_x/documents/ingest/", json=payload_precise)
        assert response_precise.status_code == 201, response_precise.text
        data_precise = response_precise.json()
        created_ucm_names_precise = {ucm["name"] for ucm in data_precise["ucm_extraction_result"]["ucms_created"]}
        expected_ucms_precise = {"Study", "Protein Alpha", "Alzheimer's Disease", "Beta-Catenin"}
        assert created_ucm_names_precise == expected_ucms_precise


    def test_ingest_document_endpoint_missing_text(self):
        payload = {
            # "document_text": "missing",
            "source_doi": "doi:10.xxxx/ejeX.doc_no_text",
            "source_citation": "No Text Test, 2024"
        }
        response = client.post("/eje_x/documents/ingest/", json=payload)
        assert response.status_code == 422, response.text # Pydantic validation error

    # --- Tests for Link Concepts Endpoint (Eje X - Ontology) ---
    def test_link_concepts_endpoint_success(self):
        # 1. Create source and target concepts
        source_payload = {"name": "Source Concept for Link", "description": "desc", "type": "UCM"}
        target_payload = {"name": "Target Concept for Link", "description": "desc", "type": "UCM"}

        source_resp = client.post("/concepts/", json=source_payload)
        assert source_resp.status_code == 201, source_resp.text
        source_id = source_resp.json()["id"]

        target_resp = client.post("/concepts/", json=target_payload)
        assert target_resp.status_code == 201, target_resp.text
        target_id = target_resp.json()["id"]

        # 2. Link them
        link_payload = {
            "source_concept_id": source_id,
            "target_concept_id": target_id,
            "relationship_type": "CAUSES", # Using string value of RelationshipType
            "description": "API Link: Source causes Target",
            "weight": 0.75,
            "evidence_sources": [{
                "source_doi": "api/link_test",
                "source_citation": "API Test Data 2024",
                "snippet": "Evidence for API link",
                "confidence": 0.9
            }]
        }
        response = client.post("/eje_x/relationships/", json=link_payload)
        assert response.status_code == 201, response.text
        data = response.json()

        assert "relationship_created" in data
        rel = data["relationship_created"]
        assert rel["source_concept_id"] == source_id
        assert rel["target_concept_id"] == target_id
        assert rel["type"] == "CAUSES"
        assert rel["description"] == "API Link: Source causes Target"
        assert rel["weight"] == 0.75
        assert len(rel["evidence_sources"]) == 1
        assert rel["evidence_sources"][0]["source_doi"] == "api/link_test"

    def test_link_concepts_endpoint_source_not_found(self):
        target_payload = {"name": "Target Only", "description": "desc", "type": "UCM"}
        target_resp = client.post("/concepts/", json=target_payload)
        assert target_resp.status_code == 201, target_resp.text
        target_id = target_resp.json()["id"]

        non_existent_source_id = str(uuid.uuid4())
        link_payload = {
            "source_concept_id": non_existent_source_id,
            "target_concept_id": target_id,
            "relationship_type": "RELATED_TO",
        }
        response = client.post("/eje_x/relationships/", json=link_payload)
        assert response.status_code == 404, response.text # Use case raises ValueError, API converts to 404
        assert non_existent_source_id in response.json()["detail"]
        assert "Source concept" in response.json()["detail"]

    def test_link_concepts_endpoint_target_not_found(self):
        source_payload = {"name": "Source Only", "description": "desc", "type": "UCM"}
        source_resp = client.post("/concepts/", json=source_payload)
        assert source_resp.status_code == 201, source_resp.text
        source_id = source_resp.json()["id"]

        non_existent_target_id = str(uuid.uuid4())
        link_payload = {
            "source_concept_id": source_id,
            "target_concept_id": non_existent_target_id,
            "relationship_type": "RELATED_TO",
        }
        response = client.post("/eje_x/relationships/", json=link_payload)
        assert response.status_code == 404, response.text
        assert non_existent_target_id in response.json()["detail"]
        assert "Target concept" in response.json()["detail"]

    def test_link_concepts_endpoint_missing_fields(self):
        # Missing target_concept_id and relationship_type
        link_payload = {"source_concept_id": str(uuid.uuid4())}
        response = client.post("/eje_x/relationships/", json=link_payload)
        assert response.status_code == 422, response.text # Pydantic validation error

    # --- Tests for Mini-Theory Construction Endpoint ---

    def test_construct_mini_theory_endpoint_success(self):
        # 1. Create some propositions first
        prop_payloads = [
            {"name": "Prop P1 for MT", "description": "Detail P1", "type": "PROPOSITION"},
            {"name": "Prop P2 for MT", "description": "Detail P2", "type": "PROPOSITION"}
        ]
        proposition_ids = []
        for payload in prop_payloads:
            resp = client.post("/concepts/", json=payload)
            assert resp.status_code == 201, resp.text
            proposition_ids.append(resp.json()["id"])

        assert len(proposition_ids) == 2

        # 2. Construct a mini-theory from these propositions
        mt_payload = {
            "proposition_ids": proposition_ids,
            "mini_theory_name": "API-Created Mini-Theory",
            "mini_theory_description": "Test MT via API.",
            "derivation_method_description": "api_test_grouping"
        }
        response = client.post("/eje_y/mini_theory_construction/", json=mt_payload)
        assert response.status_code == 201, response.text
        data = response.json()

        assert "mini_theory_created" in data
        mt = data["mini_theory_created"]
        assert mt["name"] == "API-Created Mini-Theory"
        assert mt["type"] == "MINI_THEORY"
        assert mt["description"] == "Test MT via API."
        assert sorted(mt["member_concept_ids"]) == sorted(proposition_ids)
        assert mt["properties"]["component_proposition_count"] == 2
        assert mt["properties"]["derivation_method"] == "api_test_grouping"

    def test_construct_mini_theory_endpoint_no_propositions(self):
        mt_payload = {"proposition_ids": []} # Empty list
        response = client.post("/eje_y/mini_theory_construction/", json=mt_payload)
        assert response.status_code == 400, response.text # Expecting ValueError from use case
        assert "one proposition ID must be provided" in response.json()["detail"]

    def test_construct_mini_theory_endpoint_proposition_not_found(self):
        prop1_payload = {"name": "Existing Prop for MT", "description": "...", "type": "PROPOSITION"}
        resp = client.post("/concepts/", json=prop1_payload)
        assert resp.status_code == 201, resp.text
        prop1_id = resp.json()["id"]

        non_existent_prop_id = str(uuid.uuid4())

        mt_payload = {
            "proposition_ids": [prop1_id, non_existent_prop_id],
            "mini_theory_name": "MT with invalid ID"
        }
        response = client.post("/eje_y/mini_theory_construction/", json=mt_payload)
        assert response.status_code == 400, response.text
        assert f"Invalid or non-PROPOSITION concept ID provided: {non_existent_prop_id}" in response.json()["detail"]

    def test_construct_mini_theory_endpoint_id_not_a_proposition(self):
        # Create a UCM (not a proposition)
        ucm_payload = {"name": "UCM not Prop", "description": "...", "type": "UCM"}
        resp = client.post("/concepts/", json=ucm_payload)
        assert resp.status_code == 201, resp.text
        ucm_id = resp.json()["id"]

        mt_payload = {
            "proposition_ids": [ucm_id],
            "mini_theory_name": "MT with non-prop ID"
        }
        response = client.post("/eje_y/mini_theory_construction/", json=mt_payload)
        assert response.status_code == 400, response.text
        assert f"Invalid or non-PROPOSITION concept ID provided: {ucm_id}" in response.json()["detail"]
