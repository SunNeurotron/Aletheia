from typing import Dict, Any # Added Any
import hashlib # For fallback run_id
import json # For serializing complex params
import logging # For logging import status

# Attempt to import mlflow and set a flag
try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    mlflow = None # type: ignore
    MLFLOW_AVAILABLE = False
    # logging.getLogger(__name__).warning("mlflow could not be imported. MLflowTracker will be non-operational.")
    # Commenting out logging during import for safety, will print in __init__ if needed.

# Application port
from ..application.ports import IExperimentTracker

class MLflowTracker(IExperimentTracker):
    """Adaptador MLflow implementando IExperimentTracker."""
    def __init__(self, tracking_uri: str):
        self.active_run_id: str | None = None
        self.experiment_name: str | None = None # Initialize experiment_name
        if MLFLOW_AVAILABLE and mlflow is not None:
            try:
                mlflow.set_tracking_uri(tracking_uri)
                self.experiment_name = "mdu_cube_analysis" # As in mdu_cube_system.py
                experiment = mlflow.get_experiment_by_name(self.experiment_name)
                if experiment is None:
                    mlflow.create_experiment(self.experiment_name)
                mlflow.set_experiment(self.experiment_name)
                # print(f"MLflowTracker initialized. Tracking URI: '{tracking_uri}', Experiment: '{self.experiment_name}'.")
            except Exception as e:
                print(f"MLflowTracker: Error initializing with URI '{tracking_uri}': {e}. MLflow features might be disabled.")
                self.experiment_name = None # Indicate failure
        else:
            print("MLflowTracker: MLflow library not available. Tracker is non-operational.")

    def start_run(self, name: str) -> str:
        """Inicia run con configuración completa."""
        if not MLFLOW_AVAILABLE or not self.experiment_name or mlflow is None:
            # print("MLflowTracker: Not available or not initialized, cannot start run.")
            return f"mlflow_disabled_run_{hashlib.md5(name.encode()).hexdigest()[:6]}"
        try:
            run = mlflow.start_run(run_name=name)
            self.active_run_id = run.info.run_id
            return self.active_run_id
        except Exception as e:
            print(f"MLflowTracker: start_run failed for name '{name}': {e}")
            self.active_run_id = None
            return f"error_starting_mlflow_run_{hashlib.md5(name.encode()).hexdigest()[:6]}"

    def log_params(self, params: Dict[str, Any]) -> None:
        """Log de parámetros con validación."""
        if not MLFLOW_AVAILABLE or not self.active_run_id or mlflow is None:
            # print("MLflowTracker: Not available or no active run to log params.")
            return
        try:
            safe_params: Dict[str, Any] = {}
            for key, value in params.items():
                if isinstance(value, (str, int, float, bool)):
                    safe_params[key] = value
                elif isinstance(value, (list, dict)):
                    try:
                        str_value = json.dumps(value, sort_keys=True)
                        if len(str_value) > 240:
                             safe_params[key] = str_value[:240] + "..."
                        else:
                             safe_params[key] = str_value
                    except TypeError:
                         safe_params[key] = str(value)[:240] + "..."
                else:
                    safe_params[key] = str(value)[:240] + "..."
            mlflow.log_params(safe_params)
        except Exception as e:
            print(f"MLflowTracker: log_params failed: {e}")

    def log_metrics(self, metrics: Dict[str, float]) -> None: # Metrics should be float (or int)
        """Log de métricas con timestamp."""
        if not MLFLOW_AVAILABLE or not self.active_run_id or mlflow is None:
            # print("MLflowTracker: Not available or no active run to log metrics.")
            return
        try:
            valid_metrics: Dict[str, float] = {}
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    valid_metrics[key] = float(value)
                # else:
                    # print(f"MLflowTracker: Metric '{key}' with non-numeric value '{value}' (type: {type(value)}) skipped.")
            if valid_metrics:
                mlflow.log_metrics(valid_metrics)
        except Exception as e:
            print(f"MLflowTracker: log_metrics failed: {e}")

    def end_run(self) -> None:
        """Finaliza el run activo."""
        if not MLFLOW_AVAILABLE or not self.active_run_id or mlflow is None:
            self.active_run_id = None # Ensure it's cleared even if mlflow was not available
            return
        try:
            mlflow.end_run()
        except Exception as e:
            if "active run" in str(e).lower() and ("not found" in str(e).lower() or "already finished" in str(e).lower()):
                pass
            else:
                print(f"MLflowTracker: end_run failed: {e}")
        finally:
            self.active_run_id = None
