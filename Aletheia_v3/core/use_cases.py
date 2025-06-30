# core/use_cases.py
import math
from typing import List
from skopt import gp_minimize
from skopt.space import Real
from skopt.utils import use_named_args

# Assuming domain.py is in the same directory or accessible in PYTHONPATH
from .domain import get_quality, ABCQuality, ABCTriple

# Search space for Bayesian optimization
# Defines the ranges for log_a and log_b.
# 'log-uniform' prior is often suitable when parameters can span several orders of magnitude.
search_space = [
    Real(1, 15, name='log_a', prior='log-uniform'), # log_a will be roughly between e^1 and e^15
    Real(1, 15, name='log_b', prior='log-uniform')  # log_b will be roughly between e^1 and e^15
]

# This list will store ABCQuality objects found during a single optimization run.
# Note: In a multi-worker or more robust application, this state management would
# need to be handled differently (e.g., passed around, stored in a class instance, or database).
# For Celery tasks, global variables can be problematic due to process/thread models.
# However, for this specific structure where a Celery task calls this use case,
# it might be reset per task invocation if the module is re-imported or the variable is managed.
# For simplicity in this context, it's kept as is from the original structure.
_found_hits_during_search: List[ABCQuality] = []

@use_named_args(search_space)
def _objective_function(log_a: float, log_b: float) -> float:
    """
    Objective function for Bayesian optimization.

    It takes logarithm-transformed 'a' and 'b', converts them back,
    calculates the quality of the (a,b,c) triple, and returns the
    negative quality (since gp_minimize minimizes functions).

    @param log_a: Logarithm of the first term 'a'.
    @param log_b: Logarithm of the second term 'b'.
    @returns: Negative quality of the triple, or 0.0 if constraints are not met.
    """
    global _found_hits_during_search
    a = int(math.exp(log_a))
    b = int(math.exp(log_b))

    # The domain.get_quality function now handles a >= b, gcd checks etc.
    # We only call it once.
    quality = get_quality(a, b) # This now uses the refactored get_quality from domain.py

    if quality > 1.4: # Threshold for considering a "hit"
        # Ensure no duplicates based on the triple itself if somehow generated multiple times
        # though gp_minimize usually explores unique points.
        current_triple = ABCTriple(a=a, b=b, c=a + b)
        # This check might be redundant if _found_hits_during_search is properly reset
        # and unique_hits logic is applied later.
        # if not any(hit.triple == current_triple for hit in _found_hits_during_search):
        _found_hits_during_search.append(ABCQuality(triple=current_triple, quality=quality))

    # gp_minimize aims to find the minimum value of the objective function.
    # Since we want to maximize quality, we return its negative.
    return -quality if quality > 0 else 0.0


class IntelligentSearchUseCase:
    """
    Use case for performing an intelligent search for high-quality abc-triples
    using Bayesian optimization.
    """

    def search(self, n_calls: int, n_random_starts: int = 10, random_state: int = 42) -> List[ABCQuality]:
        """
        Performs the Bayesian optimization search.

        @param n_calls: Total number of evaluations of the objective function.
        @param n_random_starts: Number of initial random evaluations before Bayesian optimization starts.
        @param random_state: Seed for reproducibility.
        @returns: A list of unique ABCQuality objects found, sorted by quality in descending order.
        """
        global _found_hits_during_search
        _found_hits_during_search = [] # Reset for each new search execution

        # gp_minimize performs Bayesian optimization (Gaussian Process minimization).
        # It attempts to find the minimum of `_objective_function`.
        gp_minimize(
            func=_objective_function,
            dimensions=search_space,
            n_calls=n_calls,
            n_random_starts=n_random_starts, # Number of evaluations of `_objective_function` with random points before building the surrogate model.
            random_state=random_state        # For reproducibility.
        )

        # Ensure uniqueness of hits based on the ABCTriple, keeping the one with potentially
        # highest quality if somehow duplicates were generated (though unlikely with gp_minimize).
        # The original code used a simple dict comprehension which is fine.
        unique_hits_map = {hit.triple: hit for hit in _found_hits_during_search}
        unique_hits_list = list(unique_hits_map.values())

        # Sort hits by quality in descending order
        unique_hits_list.sort(key=lambda x: x.quality, reverse=True)

        return unique_hits_list

# Example usage (optional, for direct testing of this module if needed):
if __name__ == '__main__':
    use_case = IntelligentSearchUseCase()
    print("Starting intelligent search...")
    # Lower n_calls for quick test
    results = use_case.search(n_calls=25, n_random_starts=5)
    if results:
        print(f"Found {len(results)} unique high-quality hits:")
        for hit in results:
            print(f"  Triple: a={hit.triple.a}, b={hit.triple.b}, c={hit.triple.c}, Quality: {hit.quality:.4f}")
    else:
        print("No high-quality hits found in this run.")
