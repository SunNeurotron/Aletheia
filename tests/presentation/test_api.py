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
            "document_text": "Key protein P53 is often mutated in cancer. This affects cell cycle.",
            "source_doi": "doi:10.1234/cancer.res.2024",
            "source_citation": "Smith et al. Cancer Research 2024"
        }
        response = client.post("/eje_y/ucm_extraction/", json=payload)
        assert response.status_code == 201, response.text
        data = response.json()
        assert "ucms_created" in data
        assert len(data["ucms_created"]) == 2
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
