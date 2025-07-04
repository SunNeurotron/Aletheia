import json
import os
from typing import Any, Dict, Optional

import requests  # To make HTTP requests

# --- Configuration ---
# Base URL for the Aletheia-Stats API.
# Assumes the API is running locally on port 8000 (default from docker-compose.yml).
# If your API_PORT_HOST in .env for docker-compose is different, change it here.
API_BASE_URL = os.getenv("DEMO_API_BASE_URL", "http://localhost:8000/api/v1")

# Credentials for mock authentication (should match what's in presentation/api.py MOCK_USERS_DB)
USERNAME = os.getenv("DEMO_USERNAME", "testuser")
PASSWORD = os.getenv(
    "DEMO_PASSWORD", "testpassword"
)  # Ensure this matches the mock password

# Global session for requests, can store the token
session = requests.Session()


# --- Helper Functions ---
def print_json(data: Any, indent: int = 2) -> None:
    """Prints JSON data in a readable format."""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def get_auth_token() -> Optional[str]:
    """Authenticates with the API and retrieves a JWT token."""
    token_url = f"{API_BASE_URL}/token"
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    print(
        f"Attempting to get auth token from: {token_url} for user: {USERNAME}"
    )
    try:
        response = requests.post(token_url, data=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        token_data = response.json()
        access_token = token_data.get("access_token")
        if access_token:
            print("Successfully authenticated. Token received.")
            session.headers.update({"Authorization": f"Bearer {access_token}"})
            return access_token
        else:
            print(
                "Authentication failed: 'access_token' not found in response."
            )
            print("Response content:")
            print_json(response.json())
            return None
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error during authentication: {http_err}")
        print(f"Response status code: {http_err.response.status_code}")
        try:
            print("Response content:")
            print_json(http_err.response.json())
        except json.JSONDecodeError:
            print(f"Response content (non-JSON): {http_err.response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error during authentication: {req_err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during authentication: {e}")
        return None


def perform_ttest_analysis(
    payload: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Sends a request to the /analyze/ttest endpoint.
    Assumes token is already in session.headers.
    """
    analyze_url = f"{API_BASE_URL}/analyze/ttest"
    print(f"\nPerforming t-test analysis via: {analyze_url}")
    print("Request payload:")
    print_json(payload)

    try:
        response = session.post(analyze_url, json=payload)
        response.raise_for_status()
        print("\nT-test analysis successful. Response:")
        result_data = response.json()
        print_json(result_data)
        return result_data
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error during t-test analysis: {http_err}")
        print(f"Response status code: {http_err.response.status_code}")
        try:
            print("Response content:")
            print_json(http_err.response.json())
        except json.JSONDecodeError:
            print(f"Response content (non-JSON): {http_err.response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error during t-test analysis: {req_err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during t-test analysis: {e}")
        return None


def get_experiment_details(experiment_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves details for a specific experiment."""
    exp_url = f"{API_BASE_URL}/experiments/{experiment_id}"
    print(f"\nRetrieving experiment details from: {exp_url}")
    try:
        response = session.get(exp_url)
        response.raise_for_status()
        print("\nExperiment details retrieved successfully. Response:")
        exp_data = response.json()
        print_json(exp_data)
        return exp_data
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error retrieving experiment {experiment_id}: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(
            f"Request error retrieving experiment {experiment_id}: {req_err}"
        )
        return None


# --- Main Demo Logic ---
def run_demo():
    """Runs the demonstration script."""
    print("--- Aletheia-Stats API Demo Script ---")

    # 1. Authenticate and get token
    token = get_auth_token()
    if not token:
        print("\nDemo cannot continue without authentication. Exiting.")
        return

    # 2. Perform a t-test analysis
    ttest_payload_1 = {
        "group_a": [1.0, 1.5, 2.0, 2.5, 3.0, 1.8, 2.2],
        "group_b": [2.8, 3.0, 3.2, 3.5, 3.8, 2.9, 3.1],
        "experiment_name": "Demo T-Test (Significant)",
        "experiment_description": "A t-test performed by the demo script, expecting significance.",
        "alpha": 0.05,
        "additional_parameters": {
            "source": "demo_script_v1.0",
            "dataset": "synthetic_set_A",
        },
    }
    analysis_result_1 = perform_ttest_analysis(ttest_payload_1)

    experiment_id_1: Optional[str] = None
    if analysis_result_1 and "id" in analysis_result_1:
        experiment_id_1 = analysis_result_1["id"]
        print(f"\nExperiment created with ID: {experiment_id_1}")
        if analysis_result_1.get("mlflow_run_id"):
            print(f"MLflow Run ID: {analysis_result_1['mlflow_run_id']}")

    # 3. Perform another t-test (e.g., non-significant or different parameters)
    ttest_payload_2 = {
        "group_a": [10, 11, 12, 10.5, 11.5, 10.8, 11.2],
        "group_b": [10.2, 11.1, 11.8, 10.7, 11.3, 10.9, 11.5],
        "experiment_name": "Demo T-Test (Non-Significant)",
        "alpha": 0.01,  # Using a stricter alpha
        "additional_parameters": {
            "source": "demo_script_v1.0",
            "dataset": "synthetic_set_B",
        },
    }
    analysis_result_2 = perform_ttest_analysis(ttest_payload_2)
    if (
        analysis_result_2
        and analysis_result_2.get("result", {}).get("is_significant_05")
        is False
    ):
        print(
            "\nAs expected (with alpha=0.05 default for flag), this test was likely not significant at 0.05."
        )
    elif analysis_result_2:
        print(
            "\nNote: The significance flag 'is_significant_05' is based on alpha=0.05 hardcoded in TTestResult, not the input alpha for the test itself."
        )

    # 4. Retrieve details of the first experiment (if created)
    if experiment_id_1:
        get_experiment_details(experiment_id_1)

    # 5. Example of a request that might fail validation (e.g., insufficient data)
    ttest_payload_fail = {
        "group_a": [1.0, 2.0],  # Too few samples
        "group_b": [3.0, 4.0, 5.0],
        "experiment_name": "Demo T-Test (Validation Fail)",
    }
    print(
        "\n--- Attempting a request expected to fail server-side validation ---"
    )
    perform_ttest_analysis(ttest_payload_fail)

    print("\n--- Demo Script Finished ---")
    print(
        f"To see detailed API docs, visit: {API_BASE_URL.replace('/api/v1', '')}/api/docs"
    )
    if os.getenv("MLFLOW_TRACKING_URI"):
        print(
            f"To see MLflow runs, visit your MLflow UI (e.g., {os.getenv('MLFLOW_TRACKING_URI')})"
        )
    else:  # Try to guess from docker-compose default
        mlflow_host_port = os.getenv("MLFLOW_PORT_HOST", "5001")
        print(
            f"To see MLflow runs, visit your MLflow UI (e.g., http://localhost:{mlflow_host_port})"
        )


if __name__ == "__main__":
    print("Starting Aletheia-Stats API Demo...")
    print(f"Targeting API at: {API_BASE_URL}")
    print(f"Using credentials: User='{USERNAME}'")

    # Check if API is accessible before starting
    try:
        # A simple check, like the health endpoint
        health_url = API_BASE_URL.replace("/api/v1", "/health")
        print(f"Pinging health endpoint at {health_url}...")
        response = requests.get(health_url, timeout=5)
        response.raise_for_status()
        if response.json().get("status") == "ok":
            print("API health check successful.")
            run_demo()
        else:
            print(f"API health check reported an issue: {response.text}")
            print(
                "Please ensure the Aletheia-Stats API is running (e.g., via docker-compose up)."
            )
    except requests.exceptions.ConnectionError:
        print(
            f"ConnectionError: Could not connect to the API at {API_BASE_URL}."
        )
        print(
            "Please ensure the Aletheia-Stats API is running (e.g., via `cd aletheia_stats && docker-compose up --build`)."
        )
    except requests.exceptions.RequestException as e:
        print(f"An error occurred trying to reach the API: {e}")
        print("Please ensure the Aletheia-Stats API is running.")
    except Exception as e:
        print(f"An unexpected error occurred before demo run: {e}")
