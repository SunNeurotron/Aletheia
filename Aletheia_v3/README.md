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
*   **Kubernetes Readiness:** Initial Kubernetes deployment and service configurations (`kubernetes/`) created for all platform components (API, Celery Workers, Dashboard, DB, Redis, MLflow), providing a blueprint for orchestrated, scalable deployments.
*   **Advanced Celery Worker Management:** Implemented task routing in `infrastructure/celery_worker.py` (e.g., to `math_heavy` queue). Conceptual designs for worker scaling using Kubernetes HPAs and KEDA are documented in `docs/celery_scaling_and_parallel_bayes_opt.md`.
*   **Database Scalability Strategies:** `infrastructure/db_optimizations.sql` provides SQL examples for PostgreSQL optimizations like table partitioning and specialized indexing, crucial for managing massive datasets of mathematical results.
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
-   **Comprehensive Testing Suite (`pytest`):** Unit and basic integration tests.
-   **Secure API with JWT Authentication:** Using FastAPI and `python-jose`.
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

2.  **Build and Start Services:**
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

## License and Disclaimer

This project is distributed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
Please also review the [DISCLAIMER.md](DISCLAIMER.md) file for important limitations and responsibilities associated with the use of this software.

*(Note: The `LICENSE` and `DISCLAIMER.md` files are expected to be in the `Aletheia_v3` root, carried over from the previous version or added if missing).*

---
Author: Alant - 01/07/2025
