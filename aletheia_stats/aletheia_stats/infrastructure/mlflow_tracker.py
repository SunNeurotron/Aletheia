import logging
from typing import Any, Dict, List, Optional

import mlflow

logger = logging.getLogger(__name__)


class MLflowExperimentTracker:
    """
    A wrapper around MLflow to handle experiment tracking functionalities.
    """

    def __init__(self, tracking_uri: str):
        """
        Initializes the MLflowExperimentTracker.

        Args:
            tracking_uri: The URI for the MLflow tracking server.
        """
        if not tracking_uri:
            raise ValueError("MLflow tracking URI cannot be empty.")
        self.tracking_uri = tracking_uri
        mlflow.set_tracking_uri(self.tracking_uri)
        self._active_run_id: Optional[str] = None
        logger.info(
            f"MLflowExperimentTracker initialized with tracking URI: {self.tracking_uri}"
        )

    def start_run(
        self,
        experiment_name: str,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Starts a new MLflow run or resumes an active one if run_id is provided in tags.

        Args:
            experiment_name: The name of the experiment. If it doesn't exist, it will be created.
            run_name: Optional name for the run.
            tags: Optional dictionary of tags to set for the run.
                  If 'mlflow_run_id' is in tags, it attempts to resume that run.

        Returns:
            The ID of the active MLflow run.

        Raises:
            Exception: If MLflow fails to start or set up the experiment/run.
        """
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                logger.info(
                    f"Experiment '{experiment_name}' not found. Creating new experiment."
                )
                experiment_id = mlflow.create_experiment(experiment_name)
                logger.info(
                    f"Experiment '{experiment_name}' created with ID: {experiment_id}."
                )
            else:
                experiment_id = experiment.experiment_id
                logger.debug(
                    f"Using existing experiment '{experiment_name}' with ID: {experiment_id}."
                )

            # Check if resuming a run
            existing_run_id = tags.get("mlflow_run_id") if tags else None

            if existing_run_id:
                logger.info(
                    f"Attempting to resume existing MLflow run: {existing_run_id}"
                )
                # mlflow.start_run validates if run_id exists. If not, it creates a new run.
                # To strictly resume or fail, one might need to check run existence via MlflowClient.
                active_run = mlflow.start_run(
                    run_id=existing_run_id,
                    experiment_id=experiment_id,
                    run_name=run_name,
                    nested=True,
                )

            else:
                logger.info(
                    f"Starting a new MLflow run for experiment ID: {experiment_id}"
                )
                active_run = mlflow.start_run(
                    experiment_id=experiment_id, run_name=run_name, nested=True
                )

            self._active_run_id = active_run.info.run_id
            logger.info(
                f"MLflow run started successfully. Run ID: {self._active_run_id}"
            )

            if tags:
                self.set_tags(tags)

            return self._active_run_id
        except Exception as e:
            logger.error(
                f"Failed to start MLflow run for experiment '{experiment_name}': {e}",
                exc_info=True,
            )
            raise

    def end_run(self, status: str = "FINISHED") -> None:
        """
        Ends the active MLflow run.

        Args:
            status: The status to set for the run when ending it.
                    Common values: "FINISHED", "FAILED", "KILLED".
        """
        if self._active_run_id and mlflow.active_run():
            current_run_id = mlflow.active_run().info.run_id
            if current_run_id == self._active_run_id:
                mlflow.end_run(status=status)
                logger.info(
                    f"MLflow run {self._active_run_id} ended with status: {status}."
                )
            else:
                # This case should ideally not happen if start_run and end_run are managed well.
                logger.warning(
                    f"Attempted to end run {self._active_run_id}, but active run is {current_run_id}. Ending current active run."
                )
                mlflow.end_run(status=status)
            self._active_run_id = None
        elif self._active_run_id:
            logger.warning(
                f"No active MLflow run found by mlflow.active_run(), but tracker has active_run_id {self._active_run_id}. Cannot end run explicitly by status. It might have been ended elsewhere or implicitly."
            )
            self._active_run_id = None  # Clear it as we can't manage it.
        else:
            logger.debug("No active MLflow run to end.")

    def log_param(self, key: str, value: Any) -> None:
        """Logs a single parameter for the active MLflow run."""
        if not self._active_run_id or not mlflow.active_run():
            logger.warning(
                "No active MLflow run to log parameter. Start a run first."
            )
            return
        try:
            mlflow.log_param(key, value)
            logger.debug(
                f"Logged param '{key}': {value} to run {self.active_run_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to log param '{key}' to MLflow run {self.active_run_id}: {e}",
                exc_info=True,
            )

    def log_params(self, params: Dict[str, Any]) -> None:
        """Logs multiple parameters for the active MLflow run."""
        if not self._active_run_id or not mlflow.active_run():
            logger.warning(
                "No active MLflow run to log parameters. Start a run first."
            )
            return
        try:
            mlflow.log_params(params)
            logger.debug(
                f"Logged params: {params} to run {self.active_run_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to log params to MLflow run {self.active_run_id}: {e}",
                exc_info=True,
            )

    def log_metric(
        self, key: str, value: float, step: Optional[int] = None
    ) -> None:
        """Logs a single metric for the active MLflow run."""
        if not self._active_run_id or not mlflow.active_run():
            logger.warning(
                "No active MLflow run to log metric. Start a run first."
            )
            return
        try:
            mlflow.log_metric(key, value, step=step)
            logger.debug(
                f"Logged metric '{key}': {value} (step: {step}) to run {self.active_run_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to log metric '{key}' to MLflow run {self.active_run_id}: {e}",
                exc_info=True,
            )

    def log_metrics(
        self, metrics: Dict[str, float], step: Optional[int] = None
    ) -> None:
        """Logs multiple metrics for the active MLflow run."""
        if not self._active_run_id or not mlflow.active_run():
            logger.warning(
                "No active MLflow run to log metrics. Start a run first."
            )
            return
        try:
            mlflow.log_metrics(metrics, step=step)
            logger.debug(
                f"Logged metrics: {metrics} (step: {step}) to run {self.active_run_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to log metrics to MLflow run {self.active_run_id}: {e}",
                exc_info=True,
            )

    def set_tag(self, key: str, value: Any) -> None:
        """Sets a tag for the active MLflow run."""
        if not self._active_run_id or not mlflow.active_run():
            logger.warning(
                "No active MLflow run to set tag. Start a run first."
            )
            return
        try:
            mlflow.set_tag(key, value)
            logger.debug(
                f"Set tag '{key}': {value} for run {self.active_run_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to set tag '{key}' for MLflow run {self.active_run_id}: {e}",
                exc_info=True,
            )

    def set_tags(self, tags: Dict[str, Any]) -> None:
        """Sets multiple tags for the active MLflow run."""
        if not self._active_run_id or not mlflow.active_run():
            logger.warning(
                "No active MLflow run to set tags. Start a run first."
            )
            return
        try:
            mlflow.set_tags(tags)
            logger.debug(f"Set tags: {tags} for run {self.active_run_id}")
        except Exception as e:
            logger.error(
                f"Failed to set tags for MLflow run {self.active_run_id}: {e}",
                exc_info=True,
            )

    @property
    def active_run_id(self) -> Optional[str]:
        """Returns the ID of the currently active MLflow run, if any."""
        if mlflow.active_run():
            # Update internal state if mlflow's active run is different
            # This could happen if mlflow.start_run was called outside this class instance
            current_mlflow_run_id = mlflow.active_run().info.run_id
            if self._active_run_id != current_mlflow_run_id:
                logger.warning(
                    f"Internal active_run_id '{self._active_run_id}' differs from mlflow.active_run() '{current_mlflow_run_id}'. Updating to current."
                )
                self._active_run_id = current_mlflow_run_id
            return self._active_run_id
        self._active_run_id = None  # No active run in mlflow context
        return None


# Example Usage (for demonstration or direct testing)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Ensure MLflow server is running at this URI or change to a local file path like "file:./mlruns"
    # For example, run: mlflow server --host 127.0.0.1 --port 5001
    # or use a local directory:
    # MOCK_MLFLOW_URI = "file:./mlruns_test_tracker"
    # import os, shutil
    # if os.path.exists("./mlruns_test_tracker"): shutil.rmtree("./mlruns_test_tracker")

    MOCK_MLFLOW_URI = "http://localhost:5001"  # Default if you have a server

    logger.info(f"Attempting to connect to MLflow at: {MOCK_MLFLOW_URI}")

    try:
        tracker = MLflowExperimentTracker(tracking_uri=MOCK_MLFLOW_URI)
        exp_name = "My Tracker Test Experiment"

        logger.info(f"Starting run for experiment: {exp_name}")
        run_id = tracker.start_run(
            experiment_name=exp_name,
            run_name="TestRun_123",
            tags={"user": "test_user", "version": "0.1"},
        )
        logger.info(f"Run started with ID: {run_id}")
        assert tracker.active_run_id == run_id

        tracker.log_param("learning_rate", 0.01)
        tracker.log_params({"epochs": 100, "batch_size": 32})
        tracker.log_metric("accuracy", 0.95, step=1)
        tracker.log_metrics({"loss": 0.12, "precision": 0.92}, step=1)
        tracker.set_tag("data_source", "synthetic")

        logger.info("Simulating some work...")

        tracker.end_run(status="FINISHED")
        logger.info("Run ended.")
        assert tracker.active_run_id is None  # Should be None after ending

        # Test resuming a run (MLflow doesn't truly "resume" a finished run to add more data,
        # but start_run with an existing run_id will reactivate it if it's not terminated or create a new one).
        # For this example, we'll just start a new run with the same name to show experiment reuse.
        logger.info(f"Starting another run in experiment: {exp_name}")
        run_id_2 = tracker.start_run(
            experiment_name=exp_name, run_name="TestRun_456"
        )
        tracker.log_param("another_param", "value")
        tracker.end_run()
        logger.info("Second run ended.")

        logger.info("MLflowExperimentTracker test completed successfully.")

    except Exception as e:
        logger.error(
            f"An error occurred during MLflowExperimentTracker test: {e}",
            exc_info=True,
        )
        logger.error(
            "Please ensure an MLflow tracking server is running at the specified URI if using http."
        )
        logger.error(
            "Alternatively, for local file-based tracking, use a URI like 'file:./mlruns_test'"
        )

    # Cleanup local test mlruns directory if created
    # if MOCK_MLFLOW_URI == "file:./mlruns_test_tracker" and os.path.exists("./mlruns_test_tracker"):
    #     shutil.rmtree("./mlruns_test_tracker")
    #     logger.info("Cleaned up local test mlruns directory.")
