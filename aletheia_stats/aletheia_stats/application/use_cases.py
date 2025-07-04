import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..domain.entities import Experiment, TTestResult
from ..domain.services import StatsService
from ..infrastructure.mlflow_tracker import (  # Assuming this path
    MLflowExperimentTracker,
)
from ..infrastructure.sqlalchemy_repository import StatsRepository  # Assuming this path

# Configure logging
logger = logging.getLogger(__name__)


class PerformTTestUseCase:
    """
    Use case for performing a t-test, logging it, and storing the results.
    Orchestrates domain services, repositories, and experiment trackers.
    """

    def __init__(
        self,
        stats_service: StatsService,
        stats_repository: StatsRepository,
        mlflow_tracker: Optional[MLflowExperimentTracker] = None,
    ):
        """
        Initializes the use case with necessary dependencies.

        Args:
            stats_service: Service for performing statistical calculations.
            stats_repository: Repository for persisting experiment data.
            mlflow_tracker: Optional tracker for logging experiments to MLflow.
        """
        self.stats_service = stats_service
        self.stats_repository = stats_repository
        self.mlflow_tracker = mlflow_tracker

    def execute(
        self,
        experiment_id: UUID,
        group_a_data: List[float],
        group_b_data: List[float],
        experiment_name: Optional[str] = "T-Test Experiment",
        experiment_description: Optional[
            str
        ] = "Independent two-sample t-test.",
        parameters: Optional[Dict[str, Any]] = None,
        alpha: float = 0.05,
    ) -> Experiment:
        """
        Executes the t-test analysis, logs it, and stores the results.

        Args:
            experiment_id: Pre-generated unique ID for this experiment.
            group_a_data: Data for group A.
            group_b_data: Data for group B.
            experiment_name: Optional name for the experiment.
            experiment_description: Optional description for the experiment.
            parameters: Additional parameters to log for the experiment.
            alpha: Significance level for the t-test and confidence interval.

        Returns:
            The Experiment object with results and metadata.

        Raises:
            ValueError: If input data is invalid for the statistical tests.
        """
        logger.info(
            f"Executing t-test use case for experiment ID: {experiment_id}"
        )

        current_parameters = {"alpha": alpha}
        if parameters:
            current_parameters.update(parameters)

        mlflow_run_id: Optional[str] = None
        # Initialize experiment entity early to collect potential tracking warnings
        experiment = Experiment(
            id=experiment_id,
            name=experiment_name,
            description=experiment_description,
            group_a_data=group_a_data,
            group_b_data=group_b_data,
            parameters=current_parameters,
            # result will be populated after analysis
            # mlflow_run_id will be populated after MLflow interaction
        )

        try:
            # Start MLflow run if tracker is available
            if self.mlflow_tracker:
                try:
                    mlflow_run_id = self.mlflow_tracker.start_run(
                        experiment.name
                        or "Default T-Test Experiments",  # Use experiment.name
                        run_name=f"Run_{experiment.id}",  # Use experiment.id
                    )
                    experiment.mlflow_run_id = (
                        mlflow_run_id  # Store it in the entity
                    )

                    self.mlflow_tracker.log_params(experiment.parameters or {})
                    self.mlflow_tracker.log_param(
                        "group_a_size", len(experiment.group_a_data)
                    )
                    self.mlflow_tracker.log_param(
                        "group_b_size", len(experiment.group_b_data)
                    )

                except Exception as e_mlflow_start:
                    err_msg = f"MLflow Error: Failed to start run or log initial parameters: {e_mlflow_start}"
                    logger.error(err_msg)
                    experiment.add_tracking_warning(err_msg)
                    # mlflow_run_id will remain None or its previous value if start_run failed partially

            # Perform statistical analysis
            logger.debug(
                f"Performing t-test analysis for experiment: {experiment.id}"
            )
            ttest_result: TTestResult = (
                self.stats_service.perform_t_test_analysis(
                    group_a=group_a_data, group_b=group_b_data, alpha=alpha
                )
            )
            logger.info(
                f"T-test analysis completed for experiment: {experiment.id}, p-value: {ttest_result.p_value:.4f}"
            )
            experiment.result = (
                ttest_result  # Assign result to the existing experiment entity
            )

            # Log results to MLflow if tracker and a valid run_id (experiment.mlflow_run_id) exist
            if self.mlflow_tracker and experiment.mlflow_run_id:
                try:
                    # Log all scalar attributes of ttest_result
                    for key, value in ttest_result.__dict__.items():
                        if isinstance(value, (int, float, bool)):
                            self.mlflow_tracker.log_metric(key, float(value))
                        elif (
                            key == "confidence_interval_95"
                            and isinstance(value, tuple)
                            and len(value) == 2
                        ):
                            self.mlflow_tracker.log_metric(
                                "ci_95_lower", value[0]
                            )
                            self.mlflow_tracker.log_metric(
                                "ci_95_upper", value[1]
                            )

                    self.mlflow_tracker.set_tag("status", "SUCCESS")
                    if ttest_result.comment:
                        self.mlflow_tracker.set_tag(
                            "analysis_comment", ttest_result.comment[:250]
                        )  # MLflow tag limit
                except Exception as e_mlflow_log:
                    err_msg = f"MLflow Error: Failed to log metrics/tags for run {experiment.mlflow_run_id}: {e_mlflow_log}"
                    logger.error(err_msg)
                    experiment.add_tracking_warning(err_msg)
            elif self.mlflow_tracker and not experiment.mlflow_run_id:
                experiment.add_tracking_warning(
                    "MLflow Warning: Skipping logging of results as MLflow run was not successfully started."
                )

            # Persist experiment data
            logger.debug(f"Saving experiment to repository: {experiment.id}")
            self.stats_repository.save(experiment)
            logger.info(f"Experiment {experiment_id} saved successfully.")

            return experiment

        except ValueError as ve:
            # No es necesario crear la entidad Experiment aquí, ya se hizo al principio.
            # Solo se actualiza con el resultado y mlflow_run_id.
            experiment.result = ttest_result
            # experiment.mlflow_run_id ya se asignó si el inicio del run fue exitoso.

            # Log results to MLflow if tracker and a valid run_id (experiment.mlflow_run_id) exist
            if self.mlflow_tracker and experiment.mlflow_run_id:
                try:
                    # Log all scalar attributes of ttest_result
                    for key, value in ttest_result.__dict__.items():
                        if isinstance(
                            value, (int, float, bool)
                        ):  # Check if value is directly loggable as metric
                            self.mlflow_tracker.log_metric(key, float(value))
                        elif (
                            key == "confidence_interval_95"
                            and isinstance(value, tuple)
                            and len(value) == 2
                        ):
                            self.mlflow_tracker.log_metric(
                                "ci_95_lower", value[0]
                            )
                            self.mlflow_tracker.log_metric(
                                "ci_95_upper", value[1]
                            )
                        # Consider logging other types as tags or params if appropriate

                    self.mlflow_tracker.set_tag("status", "SUCCESS")
                    if ttest_result.comment:
                        self.mlflow_tracker.set_tag(
                            "analysis_comment", ttest_result.comment[:250]
                        )  # MLflow tag limit
                except Exception as e_mlflow_log:
                    err_msg = f"MLflow Error: Failed to log metrics/tags for run {experiment.mlflow_run_id}: {e_mlflow_log}"
                    logger.error(err_msg)
                    experiment.add_tracking_warning(
                        err_msg
                    )  # Add warning to the experiment object
            elif (
                self.mlflow_tracker and not experiment.mlflow_run_id
            ):  # MLflow tracker exists, but run failed to start
                experiment.add_tracking_warning(
                    "MLflow Warning: Skipping logging of results as MLflow run was not successfully started."
                )

            # Persist experiment data
            logger.debug(f"Saving experiment to repository: {experiment.id}")
            self.stats_repository.save(
                experiment
            )  # Save includes tracking_warnings now
            logger.info(f"Experiment {experiment.id} saved successfully.")

            return experiment

        except ValueError as ve:
            logger.error(
                f"ValueError during t-test execution for {experiment.id}: {ve}"
            )
            if (
                self.mlflow_tracker and experiment.mlflow_run_id
            ):  # Use experiment.mlflow_run_id
                self.mlflow_tracker.set_tag("status", "FAILED_VALIDATION")
                self.mlflow_tracker.set_tag("error_type", "ValueError")
                self.mlflow_tracker.set_tag("error_message", str(ve)[:250])
            experiment.add_tracking_warning(f"Analysis ValueError: {ve}")
            self.stats_repository.save(
                experiment
            )  # Save experiment even if analysis failed, with warnings
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during t-test execution for {experiment.id}: {e}",
                exc_info=True,
            )
            if (
                self.mlflow_tracker and experiment.mlflow_run_id
            ):  # Use experiment.mlflow_run_id
                self.mlflow_tracker.set_tag(
                    "status", "CRITICAL_FAILURE_ANALYSIS"
                )
                self.mlflow_tracker.set_tag("error_type", e.__class__.__name__)
                self.mlflow_tracker.set_tag("error_message", str(e)[:250])
            experiment.add_tracking_warning(
                f"Unexpected Analysis Error: {e.__class__.__name__} - {e}"
            )
            self.stats_repository.save(
                experiment
            )  # Save experiment even if analysis failed, with warnings
            raise
        finally:
            # End MLflow run if tracker and a run was actually started
            if (
                self.mlflow_tracker and experiment.mlflow_run_id
            ):  # Check experiment.mlflow_run_id
                try:
                    self.mlflow_tracker.end_run()
                except Exception as e_mlflow_end:
                    err_msg = f"MLflow Error: Failed to end run {experiment.mlflow_run_id}: {e_mlflow_end}"
                    logger.error(err_msg)
                    # Note: If saving the experiment happens before this `finally` block,
                    # this specific warning might not be persisted if the use case re-raises immediately.
                    # However, the primary goal is to capture issues during the main try block.
                    # For robustness, one might save the experiment again here if this warning is critical to persist.
                    # experiment.add_tracking_warning(err_msg) # This warning might not be saved if error occurs during save itself
                    # self.stats_repository.save(experiment) # Potentially problematic if DB connection lost


# Example of how this use case might be instantiated and run (dependency injection)
# This would typically happen in the presentation layer (e.g., API endpoint handler)
# or a script.

# if __name__ == "__main__":
#     from uuid import uuid4
#     # This is a mock setup for demonstration.
#     # In a real app, these would be properly configured instances.

#     logging.basicConfig(level=logging.INFO)

#     # Mock StatsService
#     mock_stats_service = StatsService()

#     # Mock StatsRepository
#     class MockStatsRepository:
#         def __init__(self):
#             self._experiments = {}
#         def save(self, experiment: Experiment):
#             logger.info(f"MockRepo: Saving experiment {experiment.id}")
#             self._experiments[experiment.id] = experiment
#         def get(self, experiment_id: UUID) -> Optional[Experiment]:
#             return self._experiments.get(experiment_id)

#     mock_repo = MockStatsRepository()

#     # Mock MLflowTracker (optional)
#     class MockMLflowTracker:
#         def __init__(self, tracking_uri="mock_uri"):
#             self.tracking_uri = tracking_uri
#             self.active_run_id = None
#             logger.info(f"MockMLflowTracker initialized with URI: {self.tracking_uri}")

#         def start_run(self, experiment_name: str, run_name: Optional[str] = None) -> str:
#             self.active_run_id = f"mock_run_{uuid4()}"
#             logger.info(f"MockMLflow: Started run {self.active_run_id} for experiment '{experiment_name}' (run name: {run_name})")
#             return self.active_run_id

#         def log_param(self, key: str, value: Any):
#             logger.info(f"MockMLflow ({self.active_run_id}): Logging param {key}={value}")

#         def log_params(self, params: Dict[str, Any]):
#             for key, value in params.items():
#                 self.log_param(key, value)

#         def log_metric(self, key: str, value: float, step: Optional[int] = None):
#             logger.info(f"MockMLflow ({self.active_run_id}): Logging metric {key}={value} (step: {step})")

#         def set_tag(self, key: str, value: Any):
#             logger.info(f"MockMLflow ({self.active_run_id}): Setting tag {key}={value}")

#         def end_run(self):
#             logger.info(f"MockMLflow ({self.active_run_id}): Ending run.")
#             self.active_run_id = None

#     mock_mlflow = MockMLflowTracker()

#     # Instantiate Use Case
#     use_case = PerformTTestUseCase(
#         stats_service=mock_stats_service,
#         stats_repository=mock_repo,
#         mlflow_tracker=mock_mlflow # or None
#     )

#     # Example data
#     exp_id = uuid4()
#     g_a = [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
#     g_b = [1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6]

#     print(f"\n--- Running Use Case: {exp_id} ---")
#     try:
#         exp_result = use_case.execute(
#             experiment_id=exp_id,
#             group_a_data=g_a,
#             group_b_data=g_b,
#             experiment_name="CLI Test T-Test",
#             parameters={"source": "cli_example"}
#         )
#         print(f"Use Case Executed. Experiment Name: {exp_result.name}")
#         if exp_result.result:
#             print(f"P-value: {exp_result.result.p_value}")
#             print(f"Comment: {exp_result.result.comment}")
#         if exp_result.mlflow_run_id:
#             print(f"MLflow Run ID: {exp_result.mlflow_run_id}")

#         # Verify save
#         saved_exp = mock_repo.get(exp_id)
#         assert saved_exp is not None
#         assert saved_exp.name == "CLI Test T-Test"

#     except ValueError as e:
#         print(f"Use Case Error: {e}")
#     except Exception as e:
#         print(f"Unexpected Use Case Error: {e}")

#     print(f"\n--- Running Use Case with insufficient data (expect ValueError): ---")
#     exp_id_fail = uuid4()
#     g_c = [1.0, 2.0]
#     g_d = [3.0, 4.0]
#     try:
#         use_case.execute(
#             experiment_id=exp_id_fail,
#             group_a_data=g_c,
#             group_b_data=g_d,
#             experiment_name="Failure Test"
#         )
#     except ValueError as e:
#         print(f"Caught expected ValueError: {e}")
#         # Check if MLflow run was tagged as FAILED
#         # (This would require inspecting mock_mlflow's state or logs if it stored them)
#     print("--- Example execution finished ---")
