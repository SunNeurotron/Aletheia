# Aletheia v3.0: AI-Guided Scientific Discovery Platform (MDU Edition)

Aletheia is an end-to-end scientific discovery platform, meticulously engineered for investigating the ABC Conjecture. This version (v3.0) epitomizes the **Unified Development Framework (MDU)**, seamlessly integrating production-grade software engineering principles with the exacting rigor of scientific research.

![Conceptual Diagram of Aletheia interacting with Math Universe](https://i.imgur.com/mY5L4sW.png)
*(Conceptual: Aletheia platform using AI to find mathematical "gold" (abc-hits) in the universe of numbers.)*

## Key Features of the MDU Edition (v3.0)

-   **Modular & Layered Architecture:** The codebase is strictly organized into `core` (domain logic), `infrastructure` (database, Celery, external services), `api` (FastAPI interface), and `dashboard` (Streamlit UI) layers. This promotes high cohesion, low coupling, and enhanced maintainability.
-   **AI-Powered Intelligent Search:** Leverages Bayesian Optimization (`scikit-optimize`) via the `core.use_cases.IntelligentSearchUseCase` to efficiently explore the vast parameter space of the ABC conjecture and identify high-quality "hits."
-   **Comprehensive Testing Suite (`pytest`):** Includes unit tests for core domain logic (`tests/test_domain.py`) and integration tests for API endpoints (`tests/test_api.py`), ensuring code reliability and correctness ("Doble Validación" principle).
-   **Secure API with JWT Authentication:** The FastAPI backend (`api/api_server.py`) implements JWT-based authentication (`api/auth.py`) for protected endpoints, adhering to the "Seguridad por Defecto" principle. A `/token` endpoint provides access tokens.
-   **Scientific Experiment Tracking (`MLflow`):** Each AI search execution initiated via Celery (`infrastructure/celery_worker.py`) is logged as a distinct experiment in MLflow. This captures parameters, metrics (like best quality found, number of hits), and tags, ensuring full "Trazabilidad" and reproducibility of scientific findings.
-   **Enriched Scientific Documentation:** Core domain logic, particularly `core/domain.py`, features detailed docstrings incorporating LaTeX equations for mathematical clarity and references to seminal papers, fulfilling the MDU's documentation standards.
-   **Persistent Data Storage:** Utilizes PostgreSQL (`infrastructure/database.py`, `infrastructure/models.py`) for storing job details and discovered abc-hits, ensuring data integrity and persistence across sessions.
-   **Asynchronous Task Processing:** Employs Celery with a Redis broker for offloading computationally intensive AI search tasks, ensuring the API remains responsive.
-   **Interactive Dashboard:** A Streamlit application (`dashboard/dashboard.py`) provides a user-friendly interface for submitting search jobs and monitoring their progress and results.
-   **Containerized Deployment (`Docker`):** The entire platform, including all services (API, worker, dashboard, database, Redis, MLflow), is containerized using Docker and orchestrated with `docker-compose.yml` for easy, reproducible, one-command deployment.

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

## License and Disclaimer

This project is distributed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
Please also review the [DISCLAIMER.md](DISCLAIMER.md) file for important limitations and responsibilities associated with the use of this software.

*(Note: The `LICENSE` and `DISCLAIMER.md` files are expected to be in the `Aletheia_v3` root, carried over from the previous version or added if missing).*
