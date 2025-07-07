from typing import Dict, Any, Optional
from celery import Celery
import asyncio # For simulating async work in task if needed, though Celery tasks are often sync
import time # For actual sleep in sync Celery task

# Application port
from ..application.ports import ITaskQueue

class CeleryTaskQueue(ITaskQueue):
    """Cola de tareas con Celery y Redis."""
    def __init__(self, broker_url: str, backend_url: Optional[str] = None):
        self.app = Celery('mdu_tasks', broker=broker_url, backend=backend_url or broker_url)
        self.app.conf.update(
            task_serializer='json',
            result_serializer='json',
            accept_content=['json'],
            timezone='UTC', # Standardize on UTC
            enable_utc=True,
            result_expires=3600, # Results expire after 1 hour
            # task_acks_late=True, # Example: for tasks that must not be lost if worker dies
            # worker_prefetch_multiplier=1, # Example: for long running tasks
        )
        self._register_tasks()
        self.process_analysis_level_task = self.app.tasks['mdu_tasks.process_analysis_level']


    def _register_tasks(self):
        """Registra tareas de procesamiento."""
        # Note: `self` in task signature is the task instance, not CeleryTaskQueue instance.
        @self.app.task(bind=True, max_retries=3, name='mdu_tasks.process_analysis_level')
        def process_analysis_level(task_self: Celery.Task, level_data: Dict[str, Any]): # Added type for task_self
            try:
                # print(f"Celery Task [{task_self.request.id}]: Processing analysis level with data: {level_data}")
                # Simulate some synchronous work for a standard Celery task
                time.sleep(0.1) # Simulate I/O or CPU bound work
                # If this task needed to call async code, it would be more complex,
                # potentially using asyncio.run() or specific Celery async task patterns.
                return {"status": "completed_from_celery_task", "result_payload": level_data}
            except Exception as exc:
                # print(f"Celery Task [{task_self.request.id}]: Error processing: {exc}")
                # Retry with exponential backoff (default Celery behavior with retry)
                raise task_self.retry(exc=exc, countdown=int(2 ** task_self.request.retries))

        # Make the task accessible if needed, though usually called via .delay or .apply_async
        # self.process_analysis_level_task = process_analysis_level
        # This is better done by looking up from self.app.tasks after registration.

    async def enqueue_task(self, task_name: str, params: Dict[str, Any]) -> str:
        """Enqueues a task. Returns task_id."""
        if task_name == "process_analysis_level":
            if self.process_analysis_level_task:
                # .delay(*args, **kwargs) is a shortcut for .apply_async(args, kwargs)
                task_result = self.process_analysis_level_task.delay(level_data=params)
                return task_result.id
            else:
                # This should ideally not happen if _register_tasks worked
                print(f"CeleryTaskQueue: Task 'process_analysis_level' not found in registered tasks.")
                return "error_task_not_registered"
        else:
            print(f"CeleryTaskQueue: Unknown task name '{task_name}' for enqueue.")
            return f"error_unknown_task_{task_name}"

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Gets the status of a task using Celery's result backend."""
        if not self.app.conf.result_backend:
            return {"task_id": task_id, "status": "UNKNOWN", "error_message": "Celery result backend not configured."}

        try:
            # AsyncResult is a synchronous object that polls the backend.
            # For a truly async status check, one might need a different pattern or library
            # that integrates Celery results with asyncio event loop.
            # However, AsyncResult is the standard way.
            result_obj = self.app.AsyncResult(task_id) # Celery's AsyncResult, not an awaitable

            if result_obj.ready():
                if result_obj.successful():
                    return {"task_id": task_id, "status": "SUCCESS", "result": result_obj.get(timeout=1.0)}
                else: # Task failed
                    return {
                        "task_id": task_id,
                        "status": "FAILURE",
                        "error_message": str(result_obj.info), # Exception info
                        "traceback": result_obj.traceback
                    }
            else: # Task not ready (e.g., PENDING, STARTED, RETRY)
                return {"task_id": task_id, "status": result_obj.state}
        except Exception as e: # Catch other errors during status check
            # print(f"CeleryTaskQueue: Error checking status for task_id '{task_id}': {e}")
            return {"task_id": task_id, "status": "ERROR_CHECKING_STATUS", "error_message": str(e)}
