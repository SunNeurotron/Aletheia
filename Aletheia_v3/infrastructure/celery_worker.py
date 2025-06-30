# infrastructure/celery_worker.py
import os
import time # For potential delays or retries
from celery import Celery
from sqlalchemy.orm import Session
import mlflow # MLflow for experiment tracking

# Import database session and models from the local infrastructure package
from .database import SessionLocal, engine as db_engine # db_engine might be needed for direct operations or checks
from .models import JobDB, HitDB

# Import the core use case
from core.use_cases import IntelligentSearchUseCase
from core.domain import ABCQuality # For type hinting if necessary

# Configure Celery
# The broker URL points to the Redis service defined in docker-compose.yml.
# The backend URL also points to Redis, used for storing task results (if needed).
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

celery_app = Celery(
    'tasks', # Name of the Celery application
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# MLflow Tracking URI - points to the MLflow service in docker-compose.yml
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
# Optionally, set an experiment name. If it doesn't exist, MLflow creates it.
MLFLOW_EXPERIMENT_NAME = os.getenv('MLFLOW_EXPERIMENT_NAME', "ABC Conjecture Research")
experiment = mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME)
if experiment is None:
    mlflow.create_experiment(MLFLOW_EXPERIMENT_NAME)
mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)


# Optional Celery configuration (can also be in a separate celeryconfig.py)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ensure tasks accept JSON content
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # More advanced settings can be added here, e.g., task routing, rate limits.
)

@celery_app.task(name="intelligent_discovery_task") # Explicit task name
def intelligent_discovery_task(job_id: str, n_calls: int):
    """
    Celery task to perform intelligent discovery for abc-triples.
    This task is triggered by the API server.

    It updates job status, runs the search, records hits, and logs to MLflow.
    """
    print(f"[{job_id}] Task received. n_calls: {n_calls}. Connecting to MLflow: {MLFLOW_TRACKING_URI}")

    # Start an MLflow run for this task. All logs and metrics will be under this run.
    with mlflow.start_run(run_name=f"job_{job_id}") as run:
        mlflow.log_param("job_id", job_id)
        mlflow.log_param("n_calls_requested", n_calls)
        run_id = run.info.run_id
        mlflow.set_tag("celery_task_id", intelligent_discovery_task.request.id) # Log Celery task ID
        print(f"[{job_id}] MLflow run started: {run_id}")

        db: Session = SessionLocal()
        try:
            job = db.query(JobDB).filter(JobDB.id == job_id).first()
            if not job:
                print(f"[{job_id}] Error: Job not found in database.")
                mlflow.log_metric("task_status", 0) # 0 for failure
                mlflow.set_tag("status", "error_job_not_found")
                # Optionally raise an error or return a specific status
                return {"status": "error", "message": "Job not found"}

            job.status = "processing"
            db.commit()
            print(f"[{job_id}] Status updated to 'processing'.")
            mlflow.set_tag("status", "processing")

            # Instantiate the use case from the core layer
            use_case = IntelligentSearchUseCase()

            # Execute the search. This is the computationally intensive part.
            # The search method in use_cases.py handles the Bayesian optimization.
            print(f"[{job_id}] Starting intelligent search via use case...")
            hits: list[ABCQuality] = use_case.search(n_calls=n_calls)
            print(f"[{job_id}] Search completed. Found {len(hits)} potential hits.")

            # Process and save the hits to the database
            saved_hits_count = 0
            best_quality_found = 0.0
            if hits:
                for hit_quality_obj in hits:
                    # Create a HitDB record for each found hit
                    db_hit = HitDB(
                        job_id=job_id,
                        a=hit_quality_obj.triple.a,
                        b=hit_quality_obj.triple.b,
                        c=hit_quality_obj.triple.c,
                        quality=hit_quality_obj.quality
                    )
                    db.add(db_hit)
                    saved_hits_count += 1
                    if hit_quality_obj.quality > best_quality_found:
                        best_quality_found = hit_quality_obj.quality

                db.commit() # Commit all hits for this job
                print(f"[{job_id}] Saved {saved_hits_count} hits to database.")

            # Update job status to "completed"
            job.status = "completed"
            db.commit()
            print(f"[{job_id}] Status updated to 'completed'.")

            # Log metrics to MLflow
            mlflow.log_metric("hits_found_count", len(hits)) # Number of hits from search
            mlflow.log_metric("hits_saved_db_count", saved_hits_count) # Number actually saved
            mlflow.log_metric("best_quality_found", best_quality_found)
            mlflow.log_metric("task_status", 1) # 1 for success
            mlflow.set_tag("status", "completed")

            return {"status": "completed", "job_id": job_id, "hits_found": len(hits), "best_quality": best_quality_found}

        except Exception as e:
            print(f"[{job_id}] Error during task execution: {e}")
            mlflow.log_metric("task_status", 0) # 0 for failure
            mlflow.set_tag("status", "error_task_exception")
            mlflow.log_param("error_message", str(e))
            # Rollback database changes if an error occurs mid-transaction
            if db.is_active:
                db.rollback()
            # Update job status to "failed" if possible
            job_in_error = db.query(JobDB).filter(JobDB.id == job_id).first()
            if job_in_error:
                job_in_error.status = "failed"
                db.commit()
            # Re-raise the exception so Celery can mark the task as failed
            raise
        finally:
            # Always close the database session
            if db:
                db.close()
            print(f"[{job_id}] Task finished. MLflow run: {run_id}")

# To run the worker (typically from the project root or where celery_app is discoverable):
# celery -A Aletheia_v3.infrastructure.celery_worker.celery_app worker -l info -P eventlet (or gevent for concurrency)
# The -A flag points to the Celery application instance.
# The -l info sets the logging level.
# -P eventlet or -P gevent can be used for I/O-bound tasks if there are many concurrent tasks.
# For CPU-bound tasks like this, the default prefork pool might be fine, adjusted with --concurrency.

if __name__ == '__main__':
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
