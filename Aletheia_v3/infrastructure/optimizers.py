from typing import Any, Callable, List, Dict, Optional # Added List, Dict, Optional
import numpy as np
import numba
from numba import jit, cuda
# import cupy as cp # Optional, requires cupy and CUDA toolkit
import functools
import hashlib
import asyncio # For profiler timing
import contextlib # For profiler contextmanager

# For DistributedCache
import aiocache
# from aiocache import cached # Not used directly here, but good to note for users
from aiocache.serializers import JsonSerializer


class JITOptimizer:
    """Optimizador Just-In-Time para operaciones críticas."""

    @staticmethod
    @jit(nopython=True, parallel=True, cache=True) # Added cache=True for Numba
    def calculate_similarity_matrix_numba(embeddings: np.ndarray) -> np.ndarray:
        """Calcula matriz de similitud optimizada con Numba."""
        n_samples, n_features = embeddings.shape
        similarity_out = np.zeros((n_samples, n_samples), dtype=np.float64) # Explicit dtype

        for i in numba.prange(n_samples): # Numba parallel range
            for j in range(i, n_samples): # Start j from i for symmetric matrix
                dot_prod = 0.0
                norm_i_sq = 0.0
                norm_j_sq = 0.0

                for k in range(n_features):
                    dot_prod += embeddings[i, k] * embeddings[j, k]
                    norm_i_sq += embeddings[i, k]**2
                    norm_j_sq += embeddings[j, k]**2

                if norm_i_sq < 1e-9 or norm_j_sq < 1e-9: # Avoid division by zero or tiny norms
                    sim_val = 0.0
                else:
                    sim_val = dot_prod / (np.sqrt(norm_i_sq) * np.sqrt(norm_j_sq))

                similarity_out[i, j] = sim_val
                similarity_out[j, i] = sim_val # Symmetric

        return similarity_out

    # @staticmethod
    # @cuda.jit # Requires numba.cuda and compatible GPU + toolkit
    # def process_wave_gpu(data_gpu, output_gpu, wave_params_gpu):
    #     """Procesamiento de onda en GPU con CUDA (Conceptual)."""
    #     idx = cuda.grid(1) # Get global thread index

    #     if idx < data_gpu.shape[0]: # Boundary check
    #         # Example operation, replace with actual wave processing logic
    #         # output_gpu[idx] = wave_params_gpu[0] * cp.sin(wave_params_gpu[1] * data_gpu[idx] + wave_params_gpu[2])
    #         # This would require data_gpu, output_gpu, wave_params_gpu to be cupy arrays or cuda device arrays
    #         output_gpu[idx] = data_gpu[idx] * wave_params_gpu[0] # Simplified placeholder
    #         pass


class LRUCache: # Basic LRU Cache implementation
    def __init__(self, maxsize: int = 128):
        self.cache: Dict[Any, Any] = {}
        self.maxsize = maxsize
        self.order: List[Any] = [] # Stores keys in access order (LRU at index 0)

    def __getitem__(self, key: Any) -> Any:
        value = self.cache[key] # Raises KeyError if not found, as expected
        # Move accessed item to the end of the order list (most recently used)
        self.order.remove(key)
        self.order.append(key)
        return value

    def __setitem__(self, key: Any, value: Any) -> None:
        if key in self.cache:
            self.order.remove(key) # Remove old position
        elif len(self.order) >= self.maxsize:
            if self.order: # Ensure order is not empty before popping
                lru_key = self.order.pop(0) # Remove least recently used
                del self.cache[lru_key]

        self.cache[key] = value
        self.order.append(key) # Add to end (most recently used)

    def __contains__(self, key: Any) -> bool:
        return key in self.cache

    def __len__(self) -> int:
        return len(self.cache)

class Profiler:
    """Basic profiler using contextlib."""
    last_duration: Dict[str, float] = {} # Store durations by name

    @contextlib.contextmanager
    def profile(self, name: str):
        loop = asyncio.get_event_loop() # Get current event loop
        start_time = loop.time()
        try:
            yield
        finally:
            duration = loop.time() - start_time
            Profiler.last_duration[name] = duration # Store duration
            # print(f"Profiler: '{name}' took {duration:.4f}s") # Can be noisy

class PerformanceOptimizer:
    """Optimizador general de rendimiento."""
    def __init__(self):
        self.jit_optimizer = JITOptimizer()
        self.cache = LRUCache(maxsize=100)
        self.profiler = Profiler()

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        # Create a string representation of args and sorted kwargs
        key_parts = [func_name]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return hashlib.md5("_".join(key_parts).encode('utf-8')).hexdigest()

    def _is_gpu_suitable(self, args: tuple) -> bool: # Placeholder
        if cuda.is_available(): # Check if CUDA runtime is found by Numba
            for arg in args:
                if isinstance(arg, np.ndarray) and arg.size > 10000: # Example: large arrays
                    return True
        return False

    async def _gpu_execute(self, func: Callable, args: tuple, kwargs: dict) -> Any: # Placeholder
        # print(f"PerformanceOptimizer: Attempting GPU execution for {func.__name__} (conceptual).")
        # This would involve:
        # 1. Checking if a GPU version of 'func' exists (e.g., self.jit_optimizer.process_wave_gpu)
        # 2. Moving data from args/kwargs (numpy arrays) to GPU (cupy arrays)
        # 3. Calling the GPU kernel
        # 4. Moving results back from GPU to CPU (numpy arrays)
        # For now, falls back to CPU execution by calling the original async function
        return await func(*args, **kwargs)

    def optimize_computation(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorador para optimizar funciones computacionalmente intensivas."""

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = self._generate_cache_key(func.__name__, args, kwargs)
            if cache_key in self.cache:
                return self.cache[cache_key]

            with self.profiler.profile(func.__name__):
                # Conceptual GPU path:
                # if self._is_gpu_suitable(args) and hasattr(self.jit_optimizer, func.__name__ + "_gpu"):
                #    gpu_func_version = getattr(self.jit_optimizer, func.__name__ + "_gpu")
                #    # This would need data transfer to/from GPU via cp.asarray and cp.asnumpy
                #    # and careful handling of args/kwargs for the GPU kernel.
                #    # result = await self._gpu_execute(gpu_func_version, args, kwargs) # If gpu_func is async
                #    # Or if it's a sync numba.cuda.jit kernel, need to launch differently.
                #    result = await func(*args, **kwargs) # Fallback for placeholder GPU
                # else:
                #    result = await func(*args, **kwargs)

                # Simpler path for now: just call the original (potentially async) function
                result = await func(*args, **kwargs)

            self.cache[cache_key] = result
            return result
        return wrapper

class DistributedCache:
    """Sistema de caché distribuido para el cubo usando aiocache."""
    def __init__(self, redis_endpoints: Optional[List[Dict[str, Any]]] = None, default_redis_host: str = 'localhost', default_redis_port: int = 6379):
        # Example redis_endpoints: [{'endpoint': 'host1', 'port': 6379}, {'endpoint': 'host2', 'port': 6379}]
        # For simplicity, if redis_endpoints is None, use a single default Redis instance.

        self.cache_instance: Optional[aiocache.Cache] = None # To hold the aiocache instance
        self.is_cluster = False # Flag if using Redis cluster (not fully supported by this simple setup)

        if redis_endpoints and len(redis_endpoints) > 1:
            # Aiocache supports Redis cluster via `aiocache.Cache.REDIS_CLUSTER`
            # This requires `redis-py-cluster` and specific setup.
            # For now, this example will use the first endpoint if multiple are given,
            # or you can adapt it for true sharding/clustering if needed.
            # print(f"DistributedCache: Multiple Redis endpoints provided. Using first for simple cache: {redis_endpoints[0]}. For cluster, use REDIS_CLUSTER type.")
            # For simplicity, we'll just use the first endpoint if a list is provided.
            # True sharding or cluster setup is more involved.
            # endpoint_config = redis_endpoints[0]
            # host = endpoint_config.get('endpoint', default_redis_host)
            # port = endpoint_config.get('port', default_redis_port)
            # This part is simplified. Aiocache has settings for cluster if you use Cache.REDIS_CLUSTER
            # For now, let's assume a single primary endpoint for Cache.REDIS
            # If `redis_endpoints` is meant for sharding, that logic needs to be added here.
            # The original code had `self.shards` which is not standard for aiocache Cache.REDIS.
            # The `_get_shard` logic implied manual sharding.
            # For now, we'll use a single aiocache instance. Manual sharding can be added if required.
             print("DistributedCache: Multiple endpoints given, but current simple setup uses one. For clustering/sharding, extend this.")
             ep = redis_endpoints[0]
             host, port = ep.get('endpoint', default_redis_host), ep.get('port', default_redis_port)

        elif redis_endpoints and len(redis_endpoints) == 1:
            ep = redis_endpoints[0]
            host, port = ep.get('endpoint', default_redis_host), ep.get('port', default_redis_port)
        else: # Default to single localhost
            host, port = default_redis_host, default_redis_port

        try:
            self.cache_instance = aiocache.Cache(
                aiocache.Cache.REDIS, # Use simple Redis connection
                endpoint=host,
                port=port,
                serializer=JsonSerializer(),
                namespace="mdu_dist_cache" # Namespace for keys
            )
            # print(f"DistributedCache initialized with Redis at {host}:{port}, namespace 'mdu_dist_cache'.")
        except Exception as e:
            print(f"DistributedCache: Failed to initialize (Redis at {host}:{port}): {e}. Cache will be non-operational.")
            self.cache_instance = None

    async def get(self, key: str) -> Optional[Any]:
        if not self.cache_instance: return None
        try:
            return await self.cache_instance.get(key)
        except Exception as e:
            # print(f"DistributedCache GET error for key '{key}': {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = 3600) -> bool:
        if not self.cache_instance: return False
        try:
            await self.cache_instance.set(key, value, ttl=ttl)
            return True
        except Exception as e:
            # print(f"DistributedCache SET error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        if not self.cache_instance: return False
        try:
            deleted_count = await self.cache_instance.delete(key) # delete returns num keys deleted
            return deleted_count > 0
        except Exception as e:
            # print(f"DistributedCache DELETE error for key '{key}': {e}")
            return False

    async def clear_namespace(self) -> bool: # To clear all keys in namespace
        if not self.cache_instance: return False
        try:
            # For RedisCache, clear() with namespace should delete keys matching namespace:*
            await self.cache_instance.clear()
            return True
        except Exception as e:
            # print(f"DistributedCache CLEAR error: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidates keys matching pattern (namespace + pattern). Returns count."""
        if not self.cache_instance or not hasattr(self.cache_instance, 'raw'):
            # print("DistributedCache: invalidate_pattern requires raw client access, not available or cache not init.")
            return 0

        # Construct full pattern including namespace
        # aiocache prepends namespace automatically for most operations,
        # but for raw SCAN, we might need to specify it.
        # The `self.cache_instance.namespace` attribute holds the namespace.
        full_pattern = f"{self.cache_instance.namespace}:{pattern}"

        count = 0
        # `aiocache.backends.redis.RedisCache` has `raw` method for commands like 'scan_iter'
        # This is an example assuming the underlying client supports async iteration for scan.
        # The actual method might vary based on aiocache version and its Redis client wrapper.
        try:
            # This is a conceptual loop. The exact `raw` command and iteration might differ.
            # Check aiocache documentation for the correct way to use SCAN with its Redis backend.
            # For simplicity, this part remains conceptual for pattern deletion.
            # A more robust way is often a Lua script on Redis side if complex patterns are needed.
            # cursor = '0'
            # while True:
            #    cursor, keys = await self.cache_instance.raw('scan', cursor, match=full_pattern, count=100)
            #    if keys:
            #        # Keys from SCAN might include namespace, aiocache's delete expects key without namespace
            #        keys_to_delete = [k.decode().replace(f"{self.cache_instance.namespace}:", "", 1) for k in keys]
            #        if keys_to_delete:
            #             deleted_count = await self.cache_instance.delete(*keys_to_delete) # if delete supports multiple keys
            #             count += len(keys_to_delete) # Assuming all were deleted if no error
            #    if cursor == b'0': break
            print(f"DistributedCache: invalidate_pattern '{pattern}' is conceptual. SCAN+DEL loop not fully implemented here.")
        except Exception as e:
            print(f"DistributedCache: Error during invalidate_pattern for '{pattern}': {e}")
        return count
