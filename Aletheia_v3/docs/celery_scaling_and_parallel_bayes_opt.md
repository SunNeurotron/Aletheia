# Celery Worker Scaling and Parallel Bayesian Optimization (Conceptual)

This document outlines conceptual approaches for scaling Celery workers within a Kubernetes environment and for parallelizing Bayesian optimization evaluations.

## Celery Worker Scaling in Kubernetes

Celery workers deployed in Kubernetes can be scaled using the **Horizontal Pod Autoscaler (HPA)**. The HPA automatically adjusts the number of worker pods based on observed metrics.

**Metrics for Scaling Celery Workers:**

1.  **CPU Utilization:** If Celery tasks are CPU-bound (like the current `intelligent_discovery_task` due to mathematical computations), scaling based on average CPU utilization across worker pods is effective.
    *   Example HPA Target: If average CPU utilization exceeds 70-80%, scale up.

2.  **Memory Utilization:** If tasks are memory-intensive, this can also be a scaling metric.

3.  **Queue Length (Custom Metric):** This is often the most direct metric for scaling task-based workers.
    *   Requires a custom metrics adapter in Kubernetes that can expose Redis/RabbitMQ queue lengths to the HPA.
    *   Tools like KEDA (Kubernetes Event-driven Autoscaling) are excellent for this, allowing scaling based on Redis list lengths (LLEN command for Celery queues).
    *   Example HPA Target with KEDA: If the `math_heavy` queue length exceeds a certain threshold (e.g., 10 tasks per current worker), scale up.

**Example HPA Configuration (Conceptual - `hpa.yaml`):**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aletheia-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aletheia-worker-deployment # Matches your worker Deployment name
  minReplicas: 2
  maxReplicas: 10 # Define appropriate max based on resources/needs
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75 # Target 75% CPU utilization
  # - type: External # Or Pods, if using a custom metrics server for queue length
  #   external:
  #     metric:
  #       name: redis_queue_length # Custom metric name
  #       selector: # Optional: match specific labels if metric server provides them
  #         matchLabels:
  #           queue: math_heavy
  #     target:
  #       type: AverageValue # Or Value
  #       averageValue: "5" # e.g., target 5 messages per worker pod on average
```

**Worker Specialization:**
With multiple queues (e.g., `default`, `math_heavy`, `math_light`), you can run different sets of worker pods, each consuming from specific queues.
*   Create separate Kubernetes Deployments for workers consuming from different queues.
*   Each Deployment would have its own HPA configuration tailored to the expected load and resource profile of tasks in its queue(s).
*   Command for starting workers would specify the queue:
    `celery -A ... worker -Q math_heavy,default -l info ...`
    `celery -A ... worker -Q math_light -l info ...`

## Parallelizing Bayesian Optimization Evaluations (Conceptual)

Standard `scikit-optimize.gp_minimize` is inherently sequential: it suggests one point, waits for evaluation, then suggests the next. True parallel Bayesian Optimization (Batch Bayesian Optimization) aims to suggest a *batch* of points to evaluate simultaneously.

**Strategies:**

1.  **Using Libraries Supporting Batch Acquisition:**
    *   Some advanced Bayesian optimization libraries (e.g., BoTorch, GPyOpt with specific acquisition functions, or custom implementations) support "batch" or "multi-point" acquisition functions like qEI (q-Expected Improvement) or qUCB. These functions suggest multiple points at once.
    *   If such a library were used, the `IntelligentSearchUseCase` would:
        1.  Call the library to get a batch of `k` candidate points.
        2.  Dispatch `k` Celery tasks, each evaluating one point using the `_objective_function`.
        3.  Collect results from all `k` tasks.
        4.  Tell the Bayesian optimization model about all `k` (points, results) pairs.
        5.  Repeat.

2.  **Approximating Parallelism with `scikit-optimize` (More Complex/Less Optimal):**
    *   This is harder and generally less effective than using a library designed for batch/parallel.
    *   One naive approach (often suboptimal) could be to run multiple independent `gp_minimize` instances with slightly different settings or random seeds and then combine their findings, but this doesn't share information effectively during the optimization process.
    *   A more sophisticated local parallelization within `_objective_function` (if the function itself was parallelizable, e.g., evaluating multiple sub-components) could be done with `joblib`, but `get_quality` is a single point evaluation.

**Conceptual Snippet for Batch Dispatch (if `ask_for_batch` existed):**

```python
# In Aletheia_v3/core/parallel_bayes_opt.py (Conceptual)
from celery import group
# from Aletheia_v3.infrastructure.celery_worker import celery_app # Assuming _objective_function_task is defined
# from some_parallel_bo_library import ParallelBayesianOptimizer

# @celery_app.task(name="objective_function_eval_task")
# def _objective_function_task(point_args_dict):
#     # Unpack point_args_dict and call the actual objective function logic
#     # (similar to how @use_named_args works for _objective_function in use_cases.py)
#     # Example: log_a = point_args_dict['log_a'], log_b = point_args_dict['log_b']
#     # return _objective_function_logic(log_a, log_b) # The core math part
#     pass


# class ParallelIntelligentSearchUseCase:
#     def search(self, n_total_evals: int, batch_size: int = 4):
#         # optimizer = ParallelBayesianOptimizer(search_space, acquisition_func='qEI')
#         # evaluated_points = []
#         # results_y = []

#         # for i in range(n_total_evals // batch_size):
#         #     # 1. Ask optimizer for a batch of points
#         #     # candidate_points_params = optimizer.ask(n_points=batch_size, X=evaluated_points, y=results_y)

#         #     # 2. Create a group of Celery tasks to evaluate these points in parallel
#         #     # tasks_to_run = []
#         #     # for point_param_dict in candidate_points_params: # Assuming point_param_dict is {'log_a': val1, 'log_b': val2}
#         #     #    tasks_to_run.append(_objective_function_task.s(point_param_dict))

#         #     # job_group = group(tasks_to_run)
#         #     # result_group = job_group.apply_async()

#         #     # 3. Wait for results (with timeout and error handling)
#         #     # result_group.join_native(timeout=3600) # Example timeout
#         #     # batch_results_y = [res for res in result_group.get() if isinstance(res, float)] # Filter out errors

#         #     # 4. Tell optimizer about the evaluated batch
#         #     # optimizer.tell(candidate_points_params_corresponding_to_batch_results_y, batch_results_y)
#         #     # evaluated_points.extend(candidate_points_params_corresponding_to_batch_results_y)
#         #     # results_y.extend(batch_results_y)

#         #     # Accumulate hits (_found_hits_during_search equivalent) based on batch_results_y
#         #     # ...

#         # return # Processed unique hits
#         pass
```

**Note:** The snippet above is highly conceptual as it depends on a hypothetical `ParallelBayesianOptimizer` and a taskified objective function. The main idea is to illustrate the pattern: ask for batch -> dispatch parallel tasks -> collect -> tell.

For the current Aletheia v3.0 using `scikit-optimize`, true parallel Bayesian optimization is not directly supported by `gp_minimize`. Scaling is primarily achieved by running more Celery workers that can pick up more *independent* search jobs (if multiple are submitted) or by running a single job that might take longer but is thoroughly explored sequentially by `gp_minimize`.
```
