# Tests for Aletheia v3 Module

This directory contains the automated tests for the `Aletheia_v3` module. Our testing strategy includes:

-   **Unit Tests**: Verifying individual components and functions in isolation.
    -   e.g., `test_domain.py` for core domain logic.
    -   e.g., `test_custom_acquisitions.py` for custom AI heuristics.
-   **Integration Tests**: Testing the interaction between different components, such as API endpoints and their underlying services or database interactions.
    -   e.g., `test_api.py` for FastAPI endpoints.
-   **Plugin System Tests**:
    -   e.g., `test_plugin_system.py` for verifying the plugin loading and execution mechanisms.

## Running Tests

Tests are written using the `pytest` framework.

1.  **From within the Docker environment (recommended for CI and consistency):**
    If the services are running via `docker-compose up`, you can execute tests within the `api` service container (or a dedicated test container if configured).
    Navigate to the `Aletheia_v3/` directory (or the project root if `docker-compose.yml` is there and paths are adjusted) and run:
    ```bash
    docker-compose exec api pytest /opt/aletheia/tests/
    ```
    (Adjust the path `/opt/aletheia/tests/` if the working directory or mount points in your Docker setup differ for the `Aletheia_v3` module's tests).

2.  **Locally (requires environment setup):**
    Ensure all dependencies from `Aletheia_v3/requirements.txt` (and any development/test specific dependencies) are installed in your local Python environment.
    Make sure necessary services (like a test database, Redis) are running and accessible, and environment variables (e.g., `ALETHEIA_V3_DATABASE_URL` for a test database) are correctly set.
    Navigate to the `Aletheia_v3/` directory or the project root and run:
    ```bash
    pytest tests/
    ```
    Or, from the project root:
    ```bash
    pytest Aletheia_v3/tests/
    ```

## Coverage

Test coverage is monitored to ensure a high quality standard. You can typically generate a coverage report by running:
```bash
pytest --cov=Aletheia_v3 --cov-report=html Aletheia_v3/tests/
```
(Adjust `--cov=Aletheia_v3` to point to the actual source code directory of the module if it's structured differently, e.g., `Aletheia_v3/src`). The HTML report will be generated in `htmlcov/`.

## Guidelines

-   New features should be accompanied by corresponding tests.
-   Bug fixes should include regression tests.
-   Aim for clear, concise, and maintainable test cases.
```
