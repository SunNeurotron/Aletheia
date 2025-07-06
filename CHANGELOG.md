# Changelog

All notable changes to this project will be documented in this file.

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
