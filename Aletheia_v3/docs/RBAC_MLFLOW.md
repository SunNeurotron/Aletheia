# Role-Based Access Control (RBAC) for MLflow Experiments (Conceptual Design)

This document outlines conceptual strategies for implementing Role-Based Access Control (RBAC) for MLflow experiments within the Aletheia platform. MLflow's open-source version has limited built-in RBAC for experiments, especially fine-grained permissions. More advanced features are often part of managed/enterprise MLflow offerings or require custom solutions.

## Goals for MLflow RBAC in Aletheia

1.  **Experiment Isolation:** Prevent users/teams from accidentally or intentionally interfering with each other's experiments if the MLflow instance is shared.
2.  **Controlled Access:** Allow specific users or groups to have read-only, write (log metrics/params), or manage (delete experiment, change settings) permissions on experiments.
3.  **Auditability:** (Related) Have a clear trail of who did what, although this is more about logging than RBAC itself.

## Conceptual Strategies

### 1. Authenticating Proxy in Front of MLflow UI/API

*   **Concept:** Place a reverse proxy (e.g., Nginx, Traefik, or a custom FastAPI app) in front of the MLflow server. This proxy handles user authentication (e.g., using the Aletheia platform's existing JWT authentication or another IdP).
*   **Authorization Logic:**
    *   The proxy, after authenticating the user, would consult an Access Control List (ACL) or a policy engine to determine what the user is allowed to do with MLflow.
    *   ACLs could map (user/role, experiment_id/name, permission_level).
    *   For API calls to MLflow (e.g., `mlflow.log_param`), the proxy would need to:
        *   Intercept the call.
        *   Verify user's permission for the target experiment and action.
        *   Forward the call to the MLflow server if allowed, potentially injecting user identity for auditing if MLflow supports it via headers.
        *   Block or modify calls if not allowed.
*   **Pros:**
    *   Can implement very fine-grained, custom logic.
    *   Leverages existing authentication systems.
*   **Cons:**
    *   Complex to build and maintain.
    *   Proxy becomes a bottleneck and single point of failure if not HA.
    *   Requires deep understanding of MLflow API calls to intercept and authorize correctly.
    *   The MLflow client (used in `celery_worker.py`) would need to be configured to go through this proxy, or the worker itself would need to pass user context for the proxy to make decisions.

### 2. Leveraging MLflow Server with Basic Auth and Experiment Permissions (If Available)

*   **Concept:** Some MLflow server setups (especially with certain backends or when using Databricks MLflow) offer more robust authentication and some level of experiment permissions.
*   **MLflow `--serve-artifacts` and Artifact Store Permissions:** If artifacts are stored in S3, Azure Blob, etc., permissions on the artifact store itself can provide some level of read/write control over artifacts, though not for metadata logging.
*   **MLflow Tracking Server Authentication (Version 2.0+):**
    *   MLflow 2.0 introduced basic authentication for the tracking server (`--app-name basic-auth` and environment variables for username/password). This is a global credential for the server, not per-user RBAC for experiments.
    *   It's possible to run multiple MLflow tracking servers, each with different auth, pointing to different backend stores or experiments, effectively namespacing, but this is cumbersome.
*   **Database-Level Permissions (If Backend Store Allows):**
    *   If the MLflow backend store is PostgreSQL, it might be theoretically possible to use PostgreSQL roles and row-level security (RLS) to control access to experiment metadata tables.
    *   This is extremely complex to set up correctly with MLflow's schema and would likely break with MLflow updates. Not recommended.
*   **Pros:**
    *   Uses MLflow's own mechanisms if they fit the need.
*   **Cons:**
    *   Open-source MLflow has limited fine-grained RBAC for experiments.
    *   Database-level permissions are usually too brittle.

### 3. Namespace-Based Approach (Simplified Isolation)

*   **Concept:** Use MLflow experiment naming conventions or tags to associate experiments with users or teams.
    *   Example Experiment Name: `user_alice_abc_runs`, `team_gamma_optimization_studies`.
*   **Celery Worker Modification:** When `celery_worker.py` logs to MLflow, it would need to know the "owner" or context of the job to select or create the correct experiment name.
    *   If `JobDB` has a `submitter_id` linking to `ResearcherDB`, the worker could use `researcher.username` to form the experiment name.
    *   `mlflow.set_experiment(f"researcher_{researcher_username}_experiments")`
*   **Access Control:** This is more of a convention than strict RBAC.
    *   The MLflow UI would show all experiments unless a proxy filters them.
    *   Users would need to be disciplined about logging to their "namespace."
*   **Pros:**
    *   Relatively simple to implement the naming convention.
*   **Cons:**
    *   Not true RBAC; relies on convention and user behavior.
    *   Doesn't prevent users from viewing or logging to other experiments if they know the names.

### 4. Using a Managed MLflow Service

*   **Concept:** Services like Databricks Managed MLflow, Azure ML, AWS SageMaker Experiments often provide built-in, robust RBAC and integration with the cloud provider's IAM system.
*   **Pros:**
    *   Handles security, scalability, and MLOps features effectively.
    *   Reduces operational burden.
*   **Cons:**
    *   Vendor lock-in.
    *   Cost.
    *   Requires integrating Aletheia with these external services.

## Recommended Approach for Aletheia (Conceptual for Current Phase)

Given Aletheia's self-hosted nature in this project:

1.  **Short-Term (Namespace Convention - Current Phase):**
    *   Modify `infrastructure/celery_worker.py` to set the MLflow experiment name based on the job's submitter (if `JobDB.submitter_id` is implemented and populated).
        *   `researcher = db.query(ResearcherDB).filter(ResearcherDB.id == job.submitter_id).first()`
        *   `experiment_name = f"user_{researcher.username}_abc_research"`
        *   `mlflow.set_experiment(experiment_name)`
    *   This provides basic organization. It's not secure RBAC.
    *   The MLflow UI will still show all experiments to anyone who can access it.

2.  **Medium-Term (Authenticating Proxy - Future Phase):**
    *   If stricter RBAC is needed, designing and implementing an authenticating proxy (Strategy 1) would be the most flexible custom solution.
    *   The proxy would authenticate Aletheia users and then apply rules about which experiments they can access or modify via the MLflow UI or API.
    *   This proxy could also filter the list of experiments shown in the UI based on user permissions.

**Security for MLflow Server Access:**
*   The MLflow server itself (port 5000) should be protected, e.g., within a private network or via firewall rules, and not exposed directly to the internet without an authentication layer in front.
*   The `docker-compose.yml` and Kubernetes service for MLflow expose it. In a production K8s setup, an Ingress controller with authentication would typically protect it.

This document serves as a conceptual guide. Actual implementation of strong RBAC for a self-hosted MLflow requires significant effort or leveraging enterprise features/products.
```
