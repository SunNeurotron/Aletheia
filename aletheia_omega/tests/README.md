# Tests for Aletheia-Omega Module

This directory contains the automated tests for the `aletheia_omega` module. The testing strategy for this module includes:

-   **Unit Tests (`tests/unit/`)**: These tests focus on individual components of the Omega module, such as domain services or specific utility functions, ensuring they work correctly in isolation.
    -   Example: `test_domain_services.py`.

-   **Integration Tests (`tests/integration/`)**: These tests verify the interactions between different parts of the Omega module. This can include testing API endpoints, their connection to application use cases, and interactions with the database or other services.
    -   Examples: `test_api.py`, `test_application_use_cases.py`.

## Running Tests

Tests are written using the `pytest` framework.

1.  **Environment Setup**:
    -   Install all dependencies listed in `aletheia_omega/requirements.txt`.
    -   Ensure any necessary environment variables are set (e.g., `ALETHEIA_OMEGA_DATABASE_URL` pointing to a test database if your integration tests require database access).
    -   For integration tests, ensure any required backing services (like a PostgreSQL instance for testing) are running and accessible.

2.  **Execution**:
    -   To run all tests for the `aletheia_omega` module, navigate to the `aletheia_omega/` directory (or its parent) and execute:
        ```bash
        pytest tests/
        ```
    -   Alternatively, from the root of the Aletheia project:
        ```bash
        pytest aletheia_omega/tests/
        ```

## Coverage

To generate a test coverage report for the `aletheia_omega` module (assuming the source code is primarily within an `aletheia_omega` sub-package like `aletheia_omega/application`, `aletheia_omega/domain`, etc.):
```bash
# From the aletheia_omega/ directory
pytest --cov=aletheia_omega --cov-report=html tests/
```
(Adjust the `--cov=aletheia_omega` path if your main source code resides in a differently named sub-directory within the module, e.g., `--cov=src`). An HTML report will typically be generated in `aletheia_omega/htmlcov/`.

## Guidelines

-   New functionalities should be accompanied by relevant unit and/or integration tests.
-   Aim for tests that are easy to understand and maintain.
-   Ensure tests are reliable and provide consistent results.
```
