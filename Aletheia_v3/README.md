# Aletheia v4.0 (Conceptual Development): AI-Guided Scientific Discovery Platform

Aletheia is an evolving end-to-end scientific discovery platform, meticulously engineered for investigating complex mathematical problems like the ABC Conjecture. This conceptual v4.0 represents a significant advancement, building upon the **Unified Development Framework (MDU)** by incorporating enhanced mathematical engines, scalability features, advanced AI techniques, and collaborative functionalities.

![Conceptual Diagram of Aletheia interacting with Math Universe](https://i.imgur.com/mY5L4sW.png)
*(Conceptual: Aletheia platform using AI to find mathematical "gold" (abc-hits) in the universe of numbers.)*

## Key Enhancements in Aletheia v4.0 (Phases 1-4 Development)

This version integrates features developed across several focused phases, transforming the platform's capabilities:

**1. Core Mathematical Engine & Foundational Performance (Phase 1):**
*   **PARI/GP Integration:** The mathematical core (`core/domain.py`) now leverages the power of PARI/GP (via `cypari2`) for high-precision arithmetic, efficient GCD calculations, and advanced prime factorization in the `_radical` function. This significantly boosts performance and numerical accuracy for large number computations.
*   **Optimized Computations:** Implemented caching (`lru_cache`) for radical computations to reduce redundant calculations.
*   **Enhanced Domain Tests:** Expanded `tests/test_domain.py` to include rigorous testing for PARI/GP integration, large number handling, and caching.
*   *(Numba JIT compilation was considered but deferred as PARI/GP addressed primary bottlenecks).*

**2. Distributed Computing & Scalability (Phase 2 - Conceptual Designs & Initial Configs):**
*   **Kubernetes Readiness:** Kubernetes deployment and service configurations in the `kubernetes/` directory have been refined for increased robustness (e.g., explicit command arguments for containers, verified environment variable sourcing, appropriate probes). A conceptual `ingress.yaml` has been added to illustrate how services would be exposed externally. These provide a more detailed blueprint for orchestrated, scalable deployments.
*   **Advanced Celery Worker Management:** Implemented task routing in `infrastructure/celery_worker.py` (e.g., to `math_heavy` queue). Conceptual designs for worker scaling using Kubernetes HPAs and KEDA are documented in `docs/celery_scaling_and_parallel_bayes_opt.md`. Worker Kubernetes deployment (`kubernetes/worker-deployment.yaml`) now includes explicit command arguments and a basic liveness probe.
*   **Database Scalability Strategies:** `infrastructure/db_optimizations.sql` provides SQL examples for PostgreSQL optimizations like table partitioning and specialized indexing, crucial for managing massive datasets of mathematical results. Kubernetes configurations for the database (`kubernetes/db-*.yaml`) have been reviewed for correctness.
*   **HPC Adaptation Concepts:** `docs/HPC_ADAPTATION.md` includes example SLURM scripts and MPI (`mpi4py`) code snippets, illustrating how Aletheia's core could be adapted for traditional High-Performance Computing environments.

**3. Advanced AI & Extensibility (Phase 3):**
*   **Custom Acquisition Function Heuristics:** Developed `core/custom_acquisitions.py` with a `get_structural_bonus` function. This heuristic, integrated into the Bayesian optimization objective in `core/use_cases.py`, guides the search towards numbers with potentially simpler structures (e.g., powers of small primes).
*   **Plugin Architecture:** Introduced a flexible plugin system. Interfaces are defined in `plugins/plugin_interfaces.py` (e.g., for search strategies, quality evaluators, data postprocessors). A basic plugin manager (`plugins/manager.py`) handles discovery and loading from `plugins/available/`. An `example_quality_evaluator.py` demonstrates its usage.
*   **Dask Integration Concepts:** `docs/DASK_INTEGRATION.md` explores using Dask for large-scale parallel data processing, complete with illustrative examples.

**4. Enhanced User Experience & Collaboration (Phase 4):**
*   **Advanced Dashboard Visualizations:** The Streamlit dashboard (`dashboard/dashboard.py`) now features 3D scatter plots of (a,b,c) hits colored by quality, enhancing data exploration. A placeholder for "Factor Analysis" outlines future analytical displays.
*   **Collaborative Data Model & API:**
    *   Extended the database schema (`infrastructure/models.py`) with `ResearcherDB`, `DiscoveryAttributionDB`, and `DerivedConjectureDB` models to support multi-user interactions.
    *   Added corresponding Pydantic schemas (`api/schemas.py`) and new CRUD API endpoints (`api/api_server.py`) for managing researchers and derived conjectures, along with a basic endpoint for attributions.
*   **Refined Security (Conceptual Designs):**
    *   `docs/RBAC_MLFLOW.md` discusses strategies for Role-Based Access Control for MLflow experiments.
    *   `docs/API_SCOPES.md` outlines a design for OAuth2 scopes for granular API authorization.

**Foundational Features (from initial MDU setup, integrated into v4.0):**
-   **Modular & Layered Architecture:** `core`, `infrastructure`, `api`, `dashboard`, `tests`.
-   **AI-Powered Intelligent Search Core:** Bayesian Optimization with `scikit-optimize`.
-   **Comprehensive Testing Suite (`pytest`):** Unit and integration tests, including tests for authentication and authorization logic.
-   **Secure API with JWT Authentication and Role-Based Authorization:** Utilizes FastAPI and `python-jose` for JWTs. Implements role-based access control (RBAC) with roles such as "researcher" and "admin" to protect sensitive endpoints and operations. User authentication is handled against the `ResearcherDB`.
-   **Scientific Experiment Tracking (`MLflow`):** Integrated into Celery workers.
-   **Containerized Deployment (`Docker`, `docker-compose.yml`):** For reproducible local/dev execution.

## System Architecture Diagram (Conceptual)

```mermaid
graph TD
    User[<img src='https://img.icons8.com/ios-filled/50/000000/user.png' width='20'/> User] -->|Interacts via Browser| Dashboard[🔬 Streamlit Dashboard]

    subgraph "Aletheia Platform (Dockerized Services)"
        Dashboard -- HTTP Request --> API[🚀 FastAPI API Server]
        API -- Stores/Retrieves Job Data --> DB[(🐘 PostgreSQL DB)]
        API -- Enqueues Task --> MQ[🏎️ Redis Message Queue]

        Worker[⚙️ Celery Worker] -- Picks Task --> MQ
        Worker -- Executes --> AISearch[🧠 AI Search Use Case (core.use_cases)]
        AISearch -- Uses --> DomainLogic[📚 Domain Logic (core.domain)]
        Worker -- Stores Results --> DB
        Worker -- Logs Experiment --> MLflowServer[📈 MLflow Tracking Server]

        MLflowServer -- Stores Metadata --> DB
        MLflowServer -- Stores Artifacts (Optional) --> ArtifactStore[(📦 Artifact Store e.g. S3/MinIO)]
    end

    User -->|Views Experiments| MLflowUI[<img src='https://www.mlflow.org/docs/latest/_static/MLflow-logo-final-black.png' width='60'/> MLflow UI]
    MLflowUI -- Reads Data --> MLflowServer

    style User fill:#fff,stroke:#333,stroke-width:2px
    style Dashboard fill:#f9f,stroke:#333,stroke-width:2px
    style API fill:#ccf,stroke:#333,stroke-width:2px
    style DB fill:#cff,stroke:#333,stroke-width:2px
    style MQ fill:#ffc,stroke:#333,stroke-width:2px
    style Worker fill:#fcf,stroke:#333,stroke-width:2px
    style AISearch fill:#ddf,stroke:#333,stroke-width:2px
    style DomainLogic fill:#eef,stroke:#333,stroke-width:2px
    style MLflowServer fill:#cfc,stroke:#333,stroke-width:2px
    style MLflowUI fill:#fff,stroke:#333,stroke-width:2px
    style ArtifactStore fill:#eee,stroke:#333,stroke-width:2px
```
*(To view the diagram, copy the MermaidJS code into a compatible renderer like the Mermaid Live Editor or integrated IDE plugins.)*

## Prerequisites

-   Docker Engine (latest version recommended)
-   Docker Compose (latest version recommended)

## How to Run the Platform

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd Aletheia_v3
    ```

2.  **Review Documentation:**
    *   Before running, it's highly recommended to review the **[End-to-End Use Case Example](docs/END_TO_END_USE_CASE.md)** to understand the platform's workflow and capabilities.
    *   Detailed documents on specific features (Kubernetes, Celery Scaling, Database Optimizations, HPC Adaptation, Plugins, Security Concepts, Dask) are available in the `docs/` and `kubernetes/` directories.

3.  **Build and Start Services:**
    From the `Aletheia_v3` root directory, execute:
    ```bash
    docker-compose up --build
    ```
    The first build may take several minutes as it downloads base images and installs dependencies. Subsequent starts will be faster.

3.  **Access Services:**
    Once all containers are running, access the services via your web browser:
    -   **🔬 Interactive Dashboard:** [http://localhost:8501](http://localhost:8501)
    -   **📄 API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
    -   **📈 MLflow Experiments UI:** [http://localhost:5000](http://localhost:5000)

4.  **Using the Platform:**
    -   Navigate to the **Dashboard** to submit new "Intelligent Search Jobs."
    -   Monitor job progress (Pending -> Processing -> Completed/Failed).
    -   View results and visualizations for completed jobs directly on the dashboard.
    -   Explore detailed experiment logs, parameters, and metrics in the **MLflow UI**.
    -   Interact with the **API** programmatically via its documented endpoints (e.g., using `curl` or a tool like Postman). Obtain a JWT token from the `/token` endpoint for protected routes.

5.  **Running Tests (Optional):**
    To execute the `pytest` suite within the API service container:
    Open a new terminal window, navigate to the `Aletheia_v3` root directory, and run:
    ```bash
    docker-compose exec api pytest tests/
    ```
    This command executes the tests located in the `tests/` directory inside the `api` container.

6.  **Stopping the Platform:**
    To stop all services, press `Ctrl+C` in the terminal where `docker-compose up` is running, then execute:
    ```bash
    docker-compose down
    ```
    This will stop and remove the containers. Data in the PostgreSQL database and MLflow (if configured with a volume or external backend) will persist across sessions due to Docker volumes.

## Advanced Deployment & Scalability (Phase 2 Concepts)

The platform is designed with scalability in mind. The following concepts and configurations are part of ongoing or planned enhancements for large-scale deployment:

*   **Kubernetes:** Basic deployment configurations for running Aletheia services (API, Celery Workers, Dashboard, Database, Redis, MLflow) on Kubernetes can be found in the `kubernetes/` directory. These provide a starting point for scalable, orchestrated deployments.
*   **Celery Worker Scaling:** Strategies for scaling Celery workers, including task routing to specialized queues (e.g., `math_heavy`) and conceptual use of Kubernetes Horizontal Pod Autoscalers (HPAs), are outlined in `docs/celery_scaling_and_parallel_bayes_opt.md`.
*   **Database Optimization:** For handling massive datasets of mathematical results, advanced PostgreSQL optimizations such as table partitioning and specialized indexing are crucial. Example SQL commands and strategies are documented in `infrastructure/db_optimizations.sql`.
These enhancements, built upon the initial MDU structure, significantly advance Aletheia's capabilities for sophisticated mathematical exploration and collaborative research. Refer to the respective module/document paths for detailed information on each feature.

## Database Migrations (Alembic)

This project now uses [Alembic](https://alembic.sqlalchemy.org/) to manage database schema migrations for the main Aletheia_v3 application. This replaces the previous automatic table creation using `SQLAlchemy.Base.metadata.create_all()`.

### Applying Migrations

When you start the application using `docker-compose up`, a service named `alembic_migrate` will automatically run. This service waits for the database to be ready and then applies any pending migrations by executing `alembic upgrade head`. This ensures your database schema is up-to-date before the API and worker services start fully.

### Generating New Migrations

If you make changes to the SQLAlchemy models in `Aletheia_v3/infrastructure/models.py`, you will need to generate a new migration script.

1.  **Ensure your development environment is set up:**
    *   Have the `ALETHEIA_V3_DATABASE_URL` environment variable correctly pointing to your development database.
    *   Make sure you have `alembic` installed in your Python environment (`pip install -r requirements.txt`).

2.  **Generate the migration script:**
    Navigate to the `Aletheia_v3` directory (the one containing `alembic.ini`) in your terminal and run:
    ```bash
    alembic revision -m "short_description_of_changes"
    ```
    For example:
    ```bash
    alembic revision -m "add_new_field_to_jobdb"
    ```

3.  **Edit the generated script:**
    Alembic will create a new file in `Aletheia_v3/alembic/versions/`. Review this script.
    *   **Autogenerate (Optional but Recommended for Review):** If your `alembic/env.py` is correctly configured with `target_metadata`, Alembic can attempt to autogenerate the migration operations based on the difference between your models and the current database state (or an empty DB if generating from scratch for autogenerate). To use autogenerate for the content of the script, you can run:
        ```bash
        alembic revision -m "short_description_of_changes" --autogenerate
        ```
        **Always carefully review autogenerated scripts before applying them.**
    *   You will need to fill in the `upgrade()` and `downgrade()` functions with the appropriate `op.` commands (e.g., `op.add_column()`, `op.create_table()`, `op.drop_column()`, etc.).

4.  **Test the migration (optional but good practice):**
    *   Apply the migration to your development database:
        ```bash
        alembic upgrade head
        ```
    *   Test your application to ensure the changes work as expected.
    *   Test the downgrade (if applicable and non-destructive):
        ```bash
        alembic downgrade -1 # Downgrade one revision
        alembic upgrade head # Upgrade again
        ```

5.  **Commit the migration script:**
    Add the new migration script from the `alembic/versions/` directory to your Git commit.

### Troubleshooting Migrations
*   **Ensure `ALETHEIA_V3_DATABASE_URL` is set correctly** in your environment where you run `alembic` commands, or that `alembic.ini` has a fallback if needed (though env var is preferred).
*   **Check `alembic/env.py`** to ensure `target_metadata` points to the `Base.metadata` of your SQLAlchemy models from `Aletheia_v3.infrastructure.models`.
*   If `alembic current` shows no revision or an unexpected one, ensure your database contains the `alembic_version` table and it reflects the correct state. `alembic stamp head` can be used to mark the current DB state as matching the latest migration if they are out of sync manually.

---

## License and Disclaimer

This project is distributed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
Please also review the [DISCLAIMER.md](DISCLAIMER.md) file for important limitations and responsibilities associated with the use of this software.

*(Note: The `LICENSE` and `DISCLAIMER.md` files are expected to be in the `Aletheia_v3` root, carried over from the previous version or added if missing).*

---
Author: Alant - 01/07/2025
