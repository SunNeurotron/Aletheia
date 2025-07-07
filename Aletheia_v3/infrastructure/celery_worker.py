# Copyright 2025 Alant
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Celery worker configuration and task definitions for Aletheia_v3.

This module initializes the Celery application, configures it with a broker
(Redis) and result backend, sets up MLflow for experiment tracking, defines
task queues, and includes the primary asynchronous task for intelligent
discovery of abc-triples (`intelligent_discovery_task`).
"""

# infrastructure/celery_worker.py
import os
import time  # For potential delays or retries
import logging # For logging import status
from typing import Any # Added for type hinting db_session_factory

# Attempt to import mlflow and set a flag
try:
    import mlflow
    MLFLOW_AVAILABLE_CELERY = True # Use a different name to avoid conflict if this file is imported elsewhere
except ImportError:
    mlflow = None # type: ignore
    MLFLOW_AVAILABLE_CELERY = False
    logging.getLogger(__name__).warning("mlflow could not be imported for celery_worker. MLflow tracking in tasks will be disabled.")

from celery import Celery
# Ensure core.domain and core.use_cases are correctly imported based on Aletheia_v3 structure
# These should be absolute imports from the Aletheia_v3 package root if worker is run from project root.
# Or relative if this module is part of a larger structure recognized by Celery.
# Assuming celery worker is run from a context where Aletheia_v3 is importable:
from Aletheia_v3.core.domain import ABCQuality
from Aletheia_v3.core.use_cases import IntelligentSearchUseCase
# from core.domain import ABCQuality  # For type hinting if necessary # Original
# from core.use_cases import IntelligentSearchUseCase # Original

# Import the core use case
# from core.use_cases import IntelligentSearchUseCase # This line is redundant and incorrect
from sqlalchemy.orm import Session

# Import database session and models from the local infrastructure package
from .database import SessionLocal
from .database import (
    engine as db_engine,  # db_engine might be needed for direct operations or checks
)
from .models import HitDB, JobDB

# Configure Celery
CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
"""URL for the Celery message broker (Redis). Loaded from environment variable."""

CELERY_RESULT_BACKEND: str = os.getenv(
    "CELERY_RESULT_BACKEND", "redis://redis:6379/0"
)
"""URL for the Celery result backend (Redis). Loaded from environment variable."""

celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)
"""The Celery application instance, configured with broker and backend.
Name 'tasks' is conventional for the main application module.
"""

# MLflow Configuration
MLFLOW_TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MLFLOW_EXPERIMENT_NAME: str = os.getenv("MLFLOW_EXPERIMENT_NAME", "ABC Conjecture Research")

if MLFLOW_AVAILABLE_CELERY and mlflow is not None:
    """URI for the MLflow tracking server. Loaded from environment variable."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    """Name of the MLflow experiment to use for logging runs. Loaded from environment variable."""
    try:
        experiment = mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME)
        if experiment is None:
            mlflow.create_experiment(MLFLOW_EXPERIMENT_NAME)
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to set MLflow experiment: {e}")
else:
    logging.getLogger(__name__).warning("MLflow is not available. Skipping MLflow configuration in celery_worker.")


from kombu import Exchange, Queue

# Optional Celery configuration (can also be in a separate celeryconfig.py)
# Define default and example custom queues
default_exchange = Exchange("default", type="direct")
"""Default Celery exchange."""
math_exchange = Exchange("math_ops", type="direct")
"""Custom Celery exchange for math-related operations."""

CELERY_TASK_QUEUES: tuple = (
    Queue("default", default_exchange, routing_key="default"),
    Queue("math_heavy", math_exchange, routing_key="math.heavy"),
    Queue("math_light", math_exchange, routing_key="math.light"),
)
"""Tuple defining available Celery task queues and their bindings."""

CELERY_TASK_DEFAULT_QUEUE: str = "default"
"""Default queue for tasks if not specified otherwise."""
CELERY_TASK_DEFAULT_EXCHANGE: str = "default"
"""Default exchange for tasks."""
CELERY_TASK_DEFAULT_ROUTING_KEY: str = "default"
"""Default routing key for tasks."""

# Update Celery app configuration
celery_app.conf.update(
    task_serializer="json",  # Use JSON for task serialization
    accept_content=["json"],  # Ensure tasks accept JSON content
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_queues=CELERY_TASK_QUEUES,
    task_default_queue=CELERY_TASK_DEFAULT_QUEUE,
    task_default_exchange=CELERY_TASK_DEFAULT_EXCHANGE,
    task_default_routing_key=CELERY_TASK_DEFAULT_ROUTING_KEY,
    # Example: Route specific tasks if not specified in @task decorator
    # task_routes={
    #     'Aletheia_v3.infrastructure.celery_worker.new_example_task': {'queue': 'math_light'}
    # },
)


@celery_app.task(
    name="intelligent_discovery_task", queue="math_heavy"
)  # Route this to math_heavy queue
def intelligent_discovery_task(job_id: str, n_calls: int):
    """
    Celery task to perform intelligent discovery for abc-triples.

    This asynchronous task is triggered by an API request. It performs the
    computationally intensive search for abc-triples using Bayesian optimization,
    updates the job status in the database, records any found hits, and logs
    experiment parameters, metrics, and tags to MLflow.

    The task is routed to the 'math_heavy' queue due to its potentially
    long-running and CPU-intensive nature.

    :param job_id: The unique identifier of the job, used for tracking and
                   database updates.
    :type job_id: str
    :param n_calls: The number of evaluations (budget) for the Bayesian
                    optimization search.
    :type n_calls: int
    :return: A dictionary containing the status of the task, job ID,
             number of hits found, and the best quality score.
    :rtype: dict
    :raises Exception: Propagates exceptions occurring during task execution,
                       allowing Celery to mark the task as failed.
    """
    print(
        f"[{job_id}] Task received. n_calls: {n_calls}. MLflow available: {MLFLOW_AVAILABLE_CELERY}"
    )

    if MLFLOW_AVAILABLE_CELERY and mlflow:
        with mlflow.start_run(run_name=f"job_{job_id}") as run:
            mlflow.log_param("job_id", job_id)
            mlflow.log_param("n_calls_requested", n_calls)
            run_id_value = run.info.run_id # type: ignore
            mlflow.set_tag("celery_task_id", intelligent_discovery_task.request.id) # type: ignore
            print(f"[{job_id}] MLflow run started: {run_id_value}")

            return _execute_discovery_logic(job_id, n_calls, SessionLocal, mlflow_is_active=True, current_run_id=run_id_value)
    else:
        print(f"[{job_id}] MLflow not available. Running task without MLflow tracking.")
        run_id_value = f"local_run_{job_id}"
        return _execute_discovery_logic(job_id, n_calls, SessionLocal, mlflow_is_active=False, current_run_id=run_id_value)

def _execute_discovery_logic(job_id: str, n_calls: int, db_session_factory: Any, mlflow_is_active: bool, current_run_id: str):
    """Helper function containing the core logic of the discovery task."""
    # Ensure Session type is available if using it for db type hint
    # from sqlalchemy.orm import Session # Can be here or at top of file
    db: Session = db_session_factory()
    try:
        job = db.query(JobDB).filter(JobDB.id == job_id).first()
        if not job:
            print(f"[{job_id}] Error: Job not found in database.")
            if mlflow_is_active and mlflow:
                mlflow.log_metric("task_status", 0)
                mlflow.set_tag("status", "error_job_not_found")
            return {"status": "error", "message": "Job not found", "run_id": current_run_id}

        job.status = "processing"
        db.commit()
        print(f"[{job_id}] Status updated to 'processing'.")
        if mlflow_is_active and mlflow:
            mlflow.set_tag("status", "processing")

        # Instantiate the use case from the core layer
        use_case = IntelligentSearchUseCase()

        # Execute the search. This is the computationally intensive part.
        print(f"[{job_id}] Starting intelligent search via use case...")
        hits: list[ABCQuality] = use_case.search(n_calls=n_calls)
        print(
            f"[{job_id}] Search completed. Found {len(hits)} potential hits."
        )

        # Process and save the hits to the database
        saved_hits_count = 0
        best_quality_found = 0.0
        if hits:
            for hit_quality_obj in hits:
                db_hit = HitDB(
                    job_id=job_id,
                    a=hit_quality_obj.triple.a,
                    b=hit_quality_obj.triple.b,
                    c=hit_quality_obj.triple.c,
                    quality=hit_quality_obj.quality,
                )
                db.add(db_hit)
                saved_hits_count += 1
                if hit_quality_obj.quality > best_quality_found:
                    best_quality_found = hit_quality_obj.quality
            db.commit()
            print(f"[{job_id}] Saved {saved_hits_count} hits to database.")

        job.status = "completed"
        db.commit()
        print(f"[{job_id}] Status updated to 'completed'.")

        if mlflow_is_active and mlflow:
            mlflow.log_metric("hits_found_count", len(hits))
            mlflow.log_metric("hits_saved_db_count", saved_hits_count)
            mlflow.log_metric("best_quality_found", best_quality_found)
            mlflow.log_metric("task_status", 1)  # 1 for success
            mlflow.set_tag("status", "completed")

        return {
            "status": "completed",
            "job_id": job_id,
            "hits_found": len(hits),
            "best_quality": best_quality_found,
            "run_id": current_run_id
        }
    except Exception as e:
        print(f"[{job_id}] Error during task execution: {e}")
        if mlflow_is_active and mlflow:
            mlflow.log_metric("task_status", 0)  # 0 for failure
            mlflow.set_tag("status", "error_task_exception")
            mlflow.log_param("error_message", str(e)) # type: ignore
        if db.is_active:
            db.rollback()
        job_in_error = db.query(JobDB).filter(JobDB.id == job_id).first()
        if job_in_error:
            job_in_error.status = "failed"
            db.commit()
        raise
    finally:
        if db:
            db.close()
        print(f"[{job_id}] Task finished. MLflow run ID (if used): {current_run_id}")


# To run the worker (typically from the project root or where celery_app is discoverable):
# celery -A Aletheia_v3.infrastructure.celery_worker.celery_app worker -l info -P eventlet (or gevent for concurrency)
# The -A flag points to the Celery application instance.
# The -l info sets the logging level.
# -P eventlet or -P gevent can be used for I/O-bound tasks if there are many concurrent tasks.
# For CPU-bound tasks like this, the default prefork pool might be fine, adjusted with --concurrency.

if __name__ == "__main__":
    # This part is for direct invocation if needed, but typically Celery workers are started via CLI
    # For example, to test the MLflow connection:
    print(f"MLflow Tracking URI: {mlflow.get_tracking_uri()}")
    print(f"MLflow Experiment Name: {MLFLOW_EXPERIMENT_NAME}")
    # You could also enqueue a test task here if Redis is running
    # from celery.result import AsyncResult
    # task = intelligent_discovery_task.delay("test_job_001", 20)
    # print(f"Test task enqueued with ID: {task.id}")
    # result = AsyncResult(task.id, app=celery_app)
    # print(f"Task state: {result.state}, Info: {result.info}")
