# Aletheia Project - Root Test Suite

This directory (`tests/`) at the root of the Aletheia project contains tests that may cover broader aspects of the platform, such as:

-   **End-to-End (E2E) Tests**: Verifying complete user workflows or interactions across multiple services.
-   **Integration Tests for Shared Components**: Testing components or utilities that are shared across different modules but whose tests don't fit neatly into a single module's test suite.
-   **Application-Level Tests**: Focusing on specific application behaviors or use cases that might span across internal modules or layers. Examples from the current structure:
    -   `tests/application/use_cases/test_abc_integration.py`
    -   `tests/application/use_cases/test_knowledge_synthesis.py`
-   **Domain Model Tests**:
    -   `tests/domain/test_models.py`
-   **Presentation Layer Tests**:
    -   `tests/presentation/test_api.py` (This might be for a root-level API or specific cross-cutting API concerns).

The exact scope of tests in this directory should be clarified and potentially reorganized if they belong more appropriately to specific modules like `Aletheia_v3`.

## Running Tests

Tests are expected to be written using `pytest`.

1.  **Environment Setup**:
    -   Ensure all necessary dependencies are installed. This might involve dependencies from the root `requirements.txt` or a combination of requirements from various modules if these tests are integrative.
    -   A complete running environment (all services from `Aletheia_v3/docker-compose.yml` or a similar setup) might be required for some of these tests, especially if they are E2E tests.
    -   Set up all required environment variables for the Aletheia platform.

2.  **Execution**:
    -   Navigate to the root of the Aletheia project and run:
        ```bash
        pytest tests/
        ```

## Coverage

Generating a meaningful, aggregated coverage report for tests in this directory can be complex if they touch code from multiple modules. It's generally recommended to run coverage reports from within each module for the code that module owns.

If you wish to attempt coverage for code touched by these root tests:
```bash
pytest --cov=Aletheia_v3 --cov=aletheia_common --cov-append tests/
```
(This is an example, you'd need to list all relevant source directories with `--cov=` and use `--cov-append` if combining with other coverage runs).

## Guidelines and Considerations

-   **Clarity of Scope**: It's important that tests in this directory have a clearly defined scope that doesn't unnecessarily overlap with tests within individual modules (`Aletheia_v3/tests/`, `aletheia_stats/tests/`, etc.).
-   **Reorganization**: Consider if some tests currently in this root `tests/` directory would be better placed within the `tests/` directory of the specific module they are most closely related to (e.g., if `tests/application/` primarily tests `Aletheia_v3`'s application layer, those tests might belong in `Aletheia_v3/tests/application/`).
-   **Test Data**: Manage test data carefully, especially for E2E tests.
-   **Maintainability**: Ensure these tests are maintainable, especially if they depend on multiple running services.
```
