# Changelog

All notable changes to this project will be documented in this file.

## [4.1.0] - 2024-07-26

### Added
-   **Functional Knowledge Graph Core:**
    -   Implemented `ScientificConcept` and `DirectedRelationship` domain models.
    -   Introduced `SQLAlchemyConceptRepository` and `SQLAlchemyRelationshipRepository` for persistent storage of concepts and relationships in PostgreSQL.
    -   Configured Alembic migrations for new `scientific_concepts` and `directed_relationships` tables.
-   **Eje X - Functional Ingestion & Ontology Use Cases:**
    -   `IngestDocumentUseCase`: Processes document text, creates `DOCUMENT_SOURCE` concepts, and triggers UCM extraction.
    -   `ExtractUCMsUseCase`: Implemented with regex/keyword-based term extraction, persists UCMs, and creates `RELATED_TO_DOCUMENT_CONTEXT` relationships.
    -   `LinkConceptsUseCase`: Allows manual creation of relationships between concepts.
-   **Eje Y - Functional Knowledge Synthesis Use Cases:**
    -   `FormClustersUseCase`: Implements keyword-based clustering of UCMs, creating `CLUSTER` concepts.
    -   `DerivePropositionsUseCase`: Generates `PROPOSITION` concepts from clusters.
    -   Aggregation Use Cases (`MiniTheoryConstructionUseCase`, `ComprehensiveTheoriesUseCase`, `UnifiedModelsUseCase`): Create `MINI_THEORY`, `COMPREHENSIVE_THEORY`, and `UNIFIED_MODEL` concepts by aggregating lower-level entities.
    -   Enhanced `DomainService` and `TheoryBuilder` with more realistic (heuristic-based) synthesis logic.
-   **API Enhancements:**
    -   New API routers (`ontology_management_router.py`, `knowledge_synthesis_router.py`) exposing Eje X and Eje Y use cases.
    -   Endpoints for all Eje X and Eje Y use cases (e.g., `POST /eje-x/ingest-document`, `POST /eje-y/cluster-formation`).
    -   New GET endpoints for listing all concepts (`GET /eje-x/concepts/`) and relationships (`GET /eje-x/relationships/`).
    -   Functional API endpoints for knowledge graph visualization:
        -   `GET /eje-y/visualization/hierarchy_graph/{concept_id}`: Constructs and returns hierarchy data from the database.
        -   `GET /eje-y/visualization/synthesis_statistics`: Calculates and returns statistics from the database.
    -   Refined API schemas (`api/schemas.py`) for all new DTOs and responses.
    -   Updated API dependency injection (`api/dependencies.py`) to use SQLAlchemy repositories and functional use cases.
-   **Interactive Knowledge Graph Dashboard (`mdu_dashboard.py`):**
    -   New Streamlit dashboard for visualizing the knowledge graph.
    -   Features: Full graph explorer with filtering, node detail display, synthesis hierarchy viewer, and statistics display.
    -   Consumes data from the new functional API endpoints.
    -   Added as a new service in `docker-compose.yml` on port `8502`.
-   **Testing:**
    -   Added dedicated unit tests for `ExtractUCMsUseCase` (`test_ucm_extraction.py`).
    -   Significantly updated API tests (`test_api.py`) to cover new Eje X, Eje Y, and visualization endpoints, including database interaction for setup and verification.

### Changed
-   Refactored DTOs from `application/dtos.py` to `api/schemas.py` (and deleted `application/dtos.py`).
-   Updated `README.md` (root and `Aletheia_v3/`) to reflect new functionalities and system state.
-   Replaced placeholder implementations for Eje Y use cases and `ExtractUCMsUseCase` with functional logic.
-   Switched `IConceptRepository` and `IRelationshipRepository` dependencies from in-memory to SQLAlchemy implementations.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2024-07-15

### Key Enhancements in Aletheia v4.0 (Phases 1-4 Development)

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
