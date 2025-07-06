"""
Integration tests for the API (presentation layer).

These tests verify the full flow from HTTP request through the API,
use cases, and down to the in-memory repository implementations.
"""
import uuid
import pytest
from fastapi.testclient import TestClient

# Due to sandbox import issues, we need to ensure the API instance 'app'
# is created using the temporarily relocated modules.
# This means aletheia.presentation.api.py itself might need to be
# adjusted or replicated similarly if its imports of 'aletheia.*' fail.

# Let's first try to import 'app' from its original intended location.
# that reconstructs the FastAPI app using the test-local use cases and domain models.

# Import the app_for_testing and reset function from api_for_test
from tests.presentation.api_for_test import app_for_testing, reset_test_repo_singletons

client = TestClient(app_for_testing)

# Fixture to reset in-memory repositories before each test
@pytest.fixture(autouse=True)
def reset_in_memory_repos_fixture():
    # Call the reset function from api_for_test.py
    reset_test_repo_singletons()
    yield


class TestConceptAPI:
    def test_create_new_concept_success(self):
        response = client.post(
            "/concepts/",
            json={
                "name": "API Test Concept",
                "description": "Created via API test.",
                "type": "PHENOMENON",
                "properties": {"source": "api_test"},
                "evidence_sources": [
                    {"source_doi": "api:test/123", "source_citation": "API Test 2024", "snippet": "test snippet", "confidence": 0.99}
                ]
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Concept"
        assert data["type"] == "PHENOMENON"
        assert data["properties"]["source"] == "api_test"
        assert len(data["evidence_sources"]) == 1
        assert data["evidence_sources"][0]["confidence"] == 0.99
        assert "id" in data

        # Store this id for subsequent tests if needed (though state should be reset)
        pytest.concept_id_created = data["id"]


    def test_create_new_concept_invalid_input_type(self):
        response = client.post(
            "/concepts/",
            json={
                "name": "Invalid Type",
                "description": "Trying to create with invalid type.",
                "type": "INVALID_CONCEPT_TYPE", # This should fail validation
            },
        )
        assert response.status_code == 422 # Unprocessable Entity for Pydantic validation errors

    def test_create_new_concept_missing_name(self):
        response = client.post(
            "/concepts/",
            json={
                # name is missing
                "description": "Missing name field.",
                "type": "SUBSTANCE",
            },
        )
        assert response.status_code == 422


    def test_list_all_concepts_empty(self):
        # Relies on reset_in_memory_repos_fixture to ensure it's empty
        response = client.get("/concepts/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_all_concepts_with_data(self):
        # Create a concept first
        concept_payload = {
            "name": "Concept A", "description": "Desc A", "type": "MECHANISM"
        }
        create_response = client.post("/concepts/", json=concept_payload)
        assert create_response.status_code == 201
        concept_a_id = create_response.json()["id"]

        concept_payload_b = {
            "name": "Concept B", "description": "Desc B", "type": "EVIDENCE"
        }
        create_response_b = client.post("/concepts/", json=concept_payload_b)
        assert create_response_b.status_code == 201

        # Now list them
        response = client.get("/concepts/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = {item["name"] for item in data}
        assert "Concept A" in names
        assert "Concept B" in names

    def test_get_single_concept_found(self):
        # Create a concept
        concept_payload = {
            "name": "FindMe Concept", "description": "Details of FindMe.", "type": "HYPOTHESIS"
        }
        create_response = client.post("/concepts/", json=concept_payload)
        assert create_response.status_code == 201
        concept_id = create_response.json()["id"]

        response = client.get(f"/concepts/{concept_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == concept_id
        assert data["name"] == "FindMe Concept"

    def test_get_single_concept_not_found(self):
        non_existent_id = uuid.uuid4()
        response = client.get(f"/concepts/{non_existent_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == f"Concept with ID {non_existent_id} not found."

    def test_get_single_concept_invalid_uuid_format(self):
        response = client.get("/concepts/this-is-not-a-uuid")
        assert response.status_code == 422 # FastAPI/Pydantic handles path param validation
