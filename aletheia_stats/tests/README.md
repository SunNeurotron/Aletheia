# Tests for Aletheia-Stats Module

This directory contains the automated tests for the `aletheia_stats` module. We employ a multi-layered testing approach:

-   **Unit Tests (`tests/unit/`)**: Focus on individual functions and classes, ensuring the correctness of core domain logic (e.g., statistical calculations in `StatsService`) and infrastructure components in isolation.
-   **Integration Tests (`tests/integration/`)**: Verify the interaction between different parts of the module, such as API endpoints with application services and database persistence. For example, `test_api.py` checks the FastAPI endpoints.
-   **Property-Based Tests (`tests/property/`)**: Utilize libraries like Hypothesis to generate a wide range of test data, helping to uncover edge cases in statistical functions and data validation. Example: `test_stats_properties.py`.

## Running Tests

Tests are written using `pytest`.

1.  **From within the Docker environment (if a `docker-compose.yml` for `aletheia_stats` sets up a testable environment):**
    If the `aletheia_stats/docker-compose.yml` is running (which sets up its own DB, etc.), you might execute tests inside the service container:
    ```bash
    # From the aletheia_stats/ directory
    docker-compose exec stats_api pytest /app/tests/ # Path inside container
    ```
    (The service name `stats_api` and path `/app/tests/` are examples; adjust based on your `docker-compose.yml` and `Dockerfile` for `aletheia_stats`).

2.  **Locally (requires environment setup):**
    -   Ensure all dependencies from `aletheia_stats/requirements.txt` are installed.
    -   Set up necessary environment variables (e.g., `STATS_DATABASE_URL` pointing to a test database, `MLFLOW_TRACKING_URI` if tests interact with MLflow).
    -   Navigate to the `aletheia_stats/` directory and run:
        ```bash
        pytest
        ```
    -   Or from the project root:
        ```bash
        pytest aletheia_stats/tests/
        ```

## Coverage

To generate a test coverage report:
```bash
# From the aletheia_stats/ directory
pytest --cov=aletheia_stats --cov-report=html tests/
```
(This assumes your source code for the module is directly within `aletheia_stats/aletheia_stats/`. Adjust the `--cov` path if needed). The HTML report will be in `aletheia_stats/htmlcov/`.

## Guidelines

-   Strive for comprehensive test coverage for all critical components.
-   Follow MDU principles for test clarity and maintainability.
-   Ensure tests are independent and can be run in any order.
```
