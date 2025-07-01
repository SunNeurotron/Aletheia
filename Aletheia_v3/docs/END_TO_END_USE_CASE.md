# Aletheia v4.0: End-to-End Use Case Example

## Introduction

This document provides an end-to-end example walkthrough of using the Aletheia v4.0 platform for a hypothetical research task related to the ABC Conjecture. We will follow Dr. Eva Rostova, a number theorist, as she utilizes various features of the platform, from submitting a search job to analyzing results and proposing a derived conjecture.

This use case aims to illustrate:
*   Interacting with both the web-based Dashboard and the REST API.
*   The flow of an intelligent search job.
*   Reviewing results using integrated visualization and experiment tracking tools.
*   Leveraging the platform's (emerging) collaborative features.

## Scenario Overview

**Researcher:** Dr. Eva Rostova
**Goal:** To explore a specific parameter subspace of the ABC conjecture, focusing on triples (a,b,c) where 'a' or 'b' might have simple prime structures. She wants to see if the platform's heuristic for structural simplicity (integrated into the Bayesian Optimization objective) helps uncover interesting patterns, even if not always leading to record-breaking 'q' values. She then plans to document any notable observations as a "derived conjecture" linked to supporting data.

## Prerequisites

1.  **Aletheia Platform Running:** Ensure all Aletheia v4.0 services (API, Celery Worker(s), Dashboard, PostgreSQL Database, Redis, MLflow Server) are running. This is typically achieved by executing `docker-compose up --build` from the `Aletheia_v3` project root directory.
    *   Dashboard: `http://localhost:8501`
    *   API Docs: `http://localhost:8000/docs`
    *   MLflow UI: `http://localhost:5000`

2.  **User Account & Authentication:**
    *   For API interactions, Dr. Rostova needs an access token. Aletheia v4.0 uses JWT authentication.
    *   The platform's authentication system (`Aletheia_v3/api/auth.py`) currently uses a `MOCK_USERS_DB` for simplicity in development. The default test user is `testuser` with password `testpassword`.
    *   In a production system with the full `ResearcherDB` model active for authentication, Dr. Rostova would register via a `/researchers` endpoint (if open) or be created by an administrator.
    *   **For this example, we will use the `testuser` credentials to obtain an API access token.**

### Obtaining an API Access Token

To interact with protected API endpoints, Dr. Rostova first needs to obtain a JWT access token. She can do this by sending a POST request to the `/token` endpoint with her username and password.

**Example using `curl`:**
```bash
curl -X POST "http://localhost:8000/token" \
-H "accept: application/json" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=testuser&password=testpassword"
```

**Expected Response (example):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY3NzAwODAwMH0.xxxxxxxxxxxx",
  "token_type": "bearer"
}
```
Dr. Rostova should copy the `access_token` value (the long string). This token will be included in the `Authorization` header for subsequent API calls (e.g., `Authorization: Bearer <copied_token>`). The token typically expires after a configured duration (e.g., 30 minutes).

With the platform running and an access token obtained, Dr. Rostova is ready to begin her research workflow.

## Submitting an Intelligent Search Job

Dr. Rostova wants to initiate an intelligent search for ABC triples. Aletheia's `IntelligentSearchUseCase` employs Bayesian Optimization, and its objective function has been enhanced with a `get_structural_bonus` heuristic that subtly favors numbers `a` and `b` that are powers of small primes or close to them. This aligns with her interest in exploring triples with structurally simple components.

She has two primary ways to submit a job: via the Dashboard or the API.

### Option 1: Submitting via the Streamlit Dashboard

1.  **Navigate to the Dashboard:** Dr. Rostova opens `http://localhost:8501` in her web browser.
2.  **Configure Job:** In the sidebar under "🚀 Submit New Intelligent Job", she uses the slider for "Search Budget (AI evaluations)" to set the number of Bayesian optimization calls (e.g., `n_calls = 100`).
    ![Dashboard Job Submission](https://i.imgur.com/your-dashboard-submit-image.png) *(Placeholder: Image of the dashboard submission form)*
3.  **Submit:** She clicks the "Start Intelligent Discovery" button.
4.  **Confirmation:** A success message appears in the sidebar confirming the job submission and providing a Job ID (e.g., `Job 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' submitted successfully! Status: pending.`).

*(**Note on Plugin Usage via Dashboard:** The current dashboard UI does not have an explicit option to select different Quality Evaluator plugins or provide plugin configurations. The search will use the default objective function, which already incorporates the `get_structural_bonus` heuristic.)*

### Option 2: Submitting via the API

For more programmatic control or batch submissions, Dr. Rostova can use the `POST /searches` API endpoint. She will need her access token obtained earlier.

**Example using `curl`:**
Let's assume her access token is `YOUR_ACCESS_TOKEN`.

```bash
curl -X POST "http://localhost:8000/searches" \
-H "accept: application/json" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "n_calls": 100
}'
```

**Expected Response (example):**
```json
{
  "n_calls": 100,
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "pending",
  "created_at": "2025-07-01T10:00:00.000Z",
  "updated_at": "2025-07-01T10:00:00.000Z",
  "hits": []
}
```
This response confirms the job creation with its ID, initial status, and the requested `n_calls`.

**Conceptual: Using a Quality Evaluator Plugin via API**

The `IntelligentSearchUseCase` in `core/use_cases.py` is designed to potentially accept a `quality_evaluator_plugin_id` and `plugin_config`. If the `POST /searches` API endpoint were extended to accept these parameters in its request body, Dr. Rostova could activate a specific plugin.

For instance, to use the `SimpleBonusQualityEvaluator` (plugin ID: `available.example_quality_evaluator.SimpleBonusQualityEvaluator`):

*Hypothetical API Request Body (if API supported plugin selection):*
```json
{
  "n_calls": 100,
  "quality_evaluator_plugin_id": "available.example_quality_evaluator.SimpleBonusQualityEvaluator",
  "plugin_config": {
    "bonus_amount": 0.05,
    "use_default_base_quality": true
  }
}
```
For this current use case walkthrough, we assume the default behavior where the `get_structural_bonus` is already part of the main objective function, so no explicit plugin selection is demonstrated for job submission. The platform's plugin manager would need to have discovered the `example_quality_evaluator` for this to work if invoked. The `plugins/manager.py` has a `discover_plugins()` function that could be called at API startup.

## Monitoring the Job

Once the job is submitted (let's say its ID is `a1b2c3d4-e5f6-7890-1234-567890abcdef`), Dr. Rostova can monitor its progress.

### Via the Dashboard

*   The submitted job ID will appear in the "📊 Job Monitoring & Results" section of the dashboard.
*   She can click the "🔄 Refresh All Job Statuses" button or wait for the dashboard's periodic refresh (if implemented, though manual refresh is current default).
*   The job's entry will show its status:
    *   **PENDING:** The job is in the queue waiting for a Celery worker to pick it up.
    *   **PROCESSING:** A worker has started executing the Bayesian Optimization search.
    *   **COMPLETED:** The search has finished. Results (if any) will be available.
    *   **FAILED:** An error occurred during job execution.

### Via the API

Dr. Rostova can programmatically check the job status by making a GET request to the `/searches/{job_id}` endpoint.

**Example using `curl` (replace `YOUR_ACCESS_TOKEN` and `YOUR_JOB_ID`):**
```bash
JOB_ID="a1b2c3d4-e5f6-7890-1234-567890abcdef" # Use the actual ID from submission
curl -X GET "http://localhost:8000/searches/${JOB_ID}" \
-H "accept: application/json" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Example Response (while processing):**
```json
{
  "n_calls": 100,
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "processing",
  "created_at": "2025-07-01T10:00:00.000Z",
  "updated_at": "2025-07-01T10:00:05.000Z", // updated_at changes
  "hits": [] // Hits populate upon completion
}
```

**Example Response (when completed):**
```json
{
  "n_calls": 100,
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "completed",
  "created_at": "2025-07-01T10:00:00.000Z",
  "updated_at": "2025-07-01T10:05:00.000Z",
  "hits": [
    {
      "a": 3,
      "b": 125,
      "c": 128,
      "quality": 1.42657,
      "id": 1, // HitDB ID
      "discovered_at": "2025-07-01T10:04:30.000Z"
    }
    // ... other hits ...
  ]
}
```
She would poll this endpoint until the status changes to "COMPLETED" or "FAILED".

## Reviewing Results and Visualizations

Once the job status is "COMPLETED", Dr. Rostova can analyze the discovered ABC triples.

### Via the Dashboard

The Dashboard is the primary tool for visual analysis:

1.  **Navigate to Job Details:** In the "📊 Job Monitoring & Results" section, Dr. Rostova finds her completed job ID. The expander for the job will show its details.
2.  **Table of Hits:** A table lists all discovered hits, showing their `a`, `b`, `c` components and calculated `quality (q)`.
    ![Dashboard Hits Table](https://i.imgur.com/your-dashboard-table-image.png) *(Placeholder: Image of the hits table)*
3.  **2D Scatter Plot:** A Plotly scatter plot visualizes "Quality (q) vs. Magnitude (log10(c))". This helps identify high-quality hits relative to the size of `c`. Hovering over points reveals details of the triple.
    ![Dashboard 2D Plot](https://i.imgur.com/your-dashboard-2dplot-image.png) *(Placeholder: Image of the 2D scatter plot)*
4.  **3D Scatter Plot:** A new 3D scatter plot shows hits in the (a, b, c) space, with points colored by their quality `q`. This can help identify clusters or geometric patterns in the distribution of hits.
    ![Dashboard 3D Plot](https://i.imgur.com/your-dashboard-3dplot-image.png) *(Placeholder: Image of the 3D scatter plot)*
5.  **Factor Analysis (Conceptual):** Dr. Rostova notes the "Factor Analysis (Conceptual)" section on the dashboard. While not yet fully implemented with detailed plots, it reminds her that future versions might provide deeper insights into the prime factorization of the components `a, b, c` for the discovered hits. This is relevant to her interest in structurally simple numbers.

### Via the API Response

The JSON response from `GET /searches/{job_id}` for a completed job already contains the list of hits, as shown in the monitoring section. Dr. Rostova could parse this JSON data for custom analysis or scripting if needed.

### Via MLflow UI

For reproducibility and detailed experiment tracking, Dr. Rostova navigates to the MLflow UI at `http://localhost:5000`.

1.  **Find Experiment:** She looks for an experiment, potentially named based on her username (e.g., `user_testuser_abc_research`) or the default experiment name (e.g., "ABC Conjecture Research").
    *(Note: The Celery worker in `infrastructure/celery_worker.py` sets the experiment name. If it's dynamic based on user, this should be noted in Aletheia's main documentation).*
2.  **Select Run:** Within the experiment, she finds the run corresponding to her `job_id` (MLflow logs `job_id` as a parameter, and the run might be named `job_{job_id}`).
3.  **Review Run Details:**
    *   **Parameters:** She verifies logged parameters like `job_id` and `n_calls_requested`.
    *   **Metrics:** She examines metrics such as `hits_found_count`, `hits_saved_db_count`, and `best_quality_found`. The `get_structural_bonus` heuristic's parameters (e.g., `bonus_weight_factor`) might also be logged here if the use case were extended to pass them.
    *   **Tags:** Tags like `status` (e.g., "completed") or `celery_task_id` can provide additional context.
    *   **Artifacts:** (If any were logged, e.g., a CSV of hits, though not currently implemented in the Celery task).

This multi-faceted review process allows Dr. Rostova to understand both the results (hits) and the process of obtaining them (MLflow tracking).

## Interacting with Collaborative Features

Aletheia v4.0 introduces foundational features for collaboration, allowing researchers to formally document their observations and attribute findings.

### Researcher Profile (Conceptual Background)

For this use case, we've used the generic `testuser` for API authentication. In a complete collaborative environment:
*   Dr. Rostova would have her own account in the `researchers` table, likely created via an admin process or a (currently not fully implemented) self-registration endpoint `POST /researchers`.
*   Her unique `researcher_id` (a UUID) would be associated with her submitted jobs (via `JobDB.submitter_id`) and any conjectures she proposes.

### Proposing a Derived Conjecture

Based on her analysis, Dr. Rostova observes a pattern: triples where `a` is a small prime number (e.g., 2, 3, 5, 7) and `b` is a power of another small prime seem to appear frequently, sometimes with qualities around 1.3-1.4, particularly when the `get_structural_bonus` heuristic was active during the search. She wants to formally propose this as a preliminary observation or "derived conjecture" for further investigation by herself or others.

She decides to pick a few representative hits from her latest job (e.g., hit IDs `101`, `105`, `123`) as initial supporting evidence.

**Using the API (`POST /conjectures`):**
Dr. Rostova (as `testuser` with `YOUR_ACCESS_TOKEN`) makes the following API call:

```bash
curl -X POST "http://localhost:8000/conjectures" \
-H "accept: application/json" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "title": "Observations on ABC Triples with Small Prime ''a'' and Prime Power ''b'' Components",
  "description": "Preliminary investigation suggests that ABC triples where ''a'' is a small prime (e.g., 2, 3, 5, 7) and ''b'' is a significant power of another small prime (e.g., p_2^k, k > 4) may exhibit interesting quality characteristics, often appearing with q values between 1.2 and 1.45 when structural heuristics are applied during search. This warrants further systematic study. LaTeX example: $q(a,b,c) = \\frac{\\log c}{\\log \\mathrm{rad}(abc)}$",
  "supporting_hit_ids": [101, 105, 123]
}'
```

**Expected Response:**
```json
{
  "title": "Observations on ABC Triples with Small Prime 'a' and Prime Power 'b' Components",
  "description": "Preliminary investigation suggests that ABC triples where 'a' is a small prime (e.g., 2, 3, 5, 7) and 'b' is a significant power of another small prime (e.g., p_2^k, k > 4) may exhibit interesting quality characteristics...",
  "id": 1, // New conjecture ID
  "proposer_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", // UUID of 'testuser' (as ResearcherDB ID)
  "status": "proposed",
  "created_at": "2025-07-01T11:00:00.000Z",
  "updated_at": "2025-07-01T11:00:00.000Z",
  "proposer": { // Populated by the API endpoint logic
    "username": "testuser",
    "full_name": "Test User", // Or actual name if ResearcherDB profile is filled
    "email": "testuser@example.com",
    "orcid": null, // Or actual ORCID
    "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "created_at": "2025-07-01T09:00:00.000Z", // Proposer's creation time
    "updated_at": "2025-07-01T09:00:00.000Z"
  },
  "supporting_hits_count": 3
}
```
Her conjecture is now logged in the system, linked to her profile and the specific hits she identified. Other researchers (if the system had multiple users and UIs for browsing conjectures) could then view, discuss, or build upon this.

### Adding an Attribution (Brief Example)

Suppose Dr. Rostova later manually verifies the mathematical details of Hit ID `101` and wants to record this.

**Using the API (`POST /hits/{hit_id}/attributions`):**
```bash
HIT_ID_TO_VERIFY=101
curl -X POST "http://localhost:8000/hits/${HIT_ID_TO_VERIFY}/attributions" \
-H "accept: application/json" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "contribution_type": "verified_by_user",
  "details": "Manually verified coprimality and radical calculation for hit 101. Confirmed quality calculation."
}'
```
This would create an attribution record linking Dr. Rostova (via her token) to Hit `101` with the type "verified_by_user".
*(Note: The `AttributionCreate` schema currently also expects `hit_id` and `researcher_id` in the payload, which is slightly redundant given the URL and token. The API endpoint handles sourcing these correctly, but the schema could be refined for this specific POST context in a future iteration.)*

## Conclusion of Use Case & Further Actions

In this walkthrough, Dr. Rostova has successfully:
1.  Obtained an API access token.
2.  Submitted an intelligent search job to Aletheia using both the Dashboard and (conceptually) the API. The search benefited from an integrated heuristic (`get_structural_bonus`) favoring structurally simple numbers.
3.  Monitored the job's progress.
4.  Reviewed the discovered hits using the Dashboard's tabular and graphical (2D, 3D scatter plots) displays.
5.  Consulted MLflow for detailed experiment parameters and metrics, ensuring reproducibility.
6.  Leveraged the new collaborative features by proposing a "derived conjecture" based on her findings and linking it to supporting data via the API.
7.  Conceptually understood how to attribute specific actions (like verification) to hits.

**Further actions Dr. Rostova or other researchers might take include:**

*   **Refining Searches:** Submitting new jobs with different `n_calls`, or exploring different search spaces if the platform were extended to allow modification of `search_space` parameters.
*   **Using Custom Plugins:** If more plugins (e.g., for different search strategies or quality evaluations) become available and the API/UI supports their selection, she could experiment with those.
*   **Expanding Conjectures:** Updating her derived conjecture with more evidence (more hit IDs) or a refined description as her research progresses (`PUT /conjectures/{conjecture_id}`).
*   **Collaborating on Conjectures:** Other researchers could (if UI/permissions allow) view her conjecture, try to find more supporting or refuting evidence, and discuss it (collaboration features like commenting on conjectures are future enhancements).
*   **Detailed Factor Analysis:** Manually performing or scripting deeper prime factorization analysis on the most interesting hits, as the dashboard's "Factor Analysis" section is currently conceptual.
*   **Programmatic Analysis:** Using the API to fetch large sets of hits for offline analysis in tools like Python (with Pandas, SymPy, PARI/GP) or other mathematical software.
*   **Contributing to the Platform:** If Dr. Rostova develops a novel heuristic or quality metric, she could potentially package it as a plugin for Aletheia (as per the Phase 3 plugin architecture).

This end-to-end example demonstrates the core workflow of Aletheia v4.0 as a platform for AI-assisted mathematical discovery, with emerging capabilities for collaboration and extensibility.
```
