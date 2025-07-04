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

# core/use_cases.py
import math
from typing import Any, Dict, List, Optional

from skopt import gp_minimize
from skopt.space import Real
from skopt.utils import use_named_args

# Plugin system integration
from Aletheia_v3.plugins import (
    manager as plugin_manager,  # Assuming manager.py is in plugins dir
)
from Aletheia_v3.plugins.plugin_interfaces import QualityEvaluatorPlugin

from .custom_acquisitions import get_structural_bonus  # Import the new bonus function

# Assuming domain.py is in the same directory or accessible in PYTHONPATH
from .domain import ABCQuality, ABCTriple
from .domain import get_quality as default_get_quality  # Renamed default_get_quality

# Search space for Bayesian optimization
# Defines the ranges for log_a and log_b.
# 'log-uniform' prior is often suitable when parameters can span several orders of magnitude.
search_space = [
    Real(
        1, 15, name="log_a", prior="log-uniform"
    ),  # log_a will be roughly between e^1 and e^15
    Real(
        1, 15, name="log_b", prior="log-uniform"
    ),  # log_b will be roughly between e^1 and e^15
]

# This list will store ABCQuality objects found during a single optimization run.
# Note: In a multi-worker or more robust application, this state management would
# need to be handled differently (e.g., passed around, stored in a class instance, or database).
# For Celery tasks, global variables can be problematic due to process/thread models.
# However, for this specific structure where a Celery task calls this use case,
# it might be reset per task invocation if the module is re-imported or the variable is managed.
# For simplicity in this context, it's kept as is from the original structure.
_found_hits_during_search: List[ABCQuality] = (
    []
)  # Stores hits from a single run
_active_quality_evaluator_plugin: Optional[QualityEvaluatorPlugin] = (
    None  # Holds active plugin instance
)


@use_named_args(search_space)
def _objective_function(log_a: float, log_b: float) -> float:
    """
    Objective function for Bayesian optimization.

    It takes logarithm-transformed 'a' and 'b', converts them back,
    calculates the quality of the (a,b,c) triple (potentially using a plugin),
    adds a structural bonus, and returns the negative of this combined score
    (since gp_minimize minimizes functions).

    @param log_a: Logarithm of the first term 'a'.
    @param log_b: Logarithm of the second term 'b'.
    @returns: Negative of (quality + bonus), or 0.0 if constraints are not met.
    """
    global _found_hits_during_search, _active_quality_evaluator_plugin
    a = int(math.exp(log_a))
    b = int(math.exp(log_b))

    # Use plugin for quality evaluation if one is active, otherwise use default.
    if _active_quality_evaluator_plugin:
        quality = _active_quality_evaluator_plugin.evaluate_quality(a, b)
    else:
        quality = default_get_quality(
            a, b
        )  # This now uses the refactored get_quality from domain.py

    # Calculate structural bonus for a and b
    # Tunable bonus_weight_factor: how much this heuristic influences the objective.
    # If quality scores are typically around 0-2, a bonus_weight_factor of 0.1-0.5 might be reasonable.
    bonus_weight_factor = 0.2
    structural_bonus_a = get_structural_bonus(a)
    structural_bonus_b = get_structural_bonus(b)
    total_structural_bonus = (
        structural_bonus_a + structural_bonus_b
    ) * bonus_weight_factor

    # The modified objective is the quality plus the structural bonus.
    # We want to maximize this sum.
    modified_objective_value = quality + total_structural_bonus

    if (
        quality > 1.4
    ):  # Threshold for considering a "hit" based on original quality
        # Ensure no duplicates based on the triple itself if somehow generated multiple times
        # though gp_minimize usually explores unique points.
        current_triple = ABCTriple(a=a, b=b, c=a + b)
        # This check might be redundant if _found_hits_during_search is properly reset
        # and unique_hits logic is applied later.
        # if not any(hit.triple == current_triple for hit in _found_hits_during_search):
        _found_hits_during_search.append(
            ABCQuality(triple=current_triple, quality=quality)
        )

    # gp_minimize aims to find the minimum value of the objective function.
    # Since we want to maximize the modified_objective_value (quality + bonus), we return its negative.
    return -modified_objective_value if modified_objective_value > 0 else 0.0


class IntelligentSearchUseCase:
    """
    Use case for performing an intelligent search for high-quality abc-triples
    using Bayesian optimization.
    """

    def search(
        self,
        n_calls: int,
        n_random_starts: int = 10,
        random_state: int = 42,
        quality_evaluator_plugin_id: Optional[str] = None,
        plugin_config: Optional[Dict[str, Any]] = None,
    ) -> List[ABCQuality]:
        """
        Performs the Bayesian optimization search.
        Can optionally use a QualityEvaluatorPlugin if specified.

        @param n_calls: Total number of evaluations of the objective function.
        @param n_random_starts: Number of initial random evaluations before Bayesian optimization starts.
        @param random_state: Seed for reproducibility.
        @param quality_evaluator_plugin_id: Optional ID of a quality evaluator plugin to use.
        @param plugin_config: Optional configuration for the plugin.
        @returns: A list of unique ABCQuality objects found, sorted by quality in descending order.
        """
        global _found_hits_during_search, _active_quality_evaluator_plugin
        _found_hits_during_search = []  # Reset for each new search execution
        _active_quality_evaluator_plugin = None  # Reset active plugin

        if quality_evaluator_plugin_id:
            # Attempt to load and activate the plugin
            # Ensure plugin discovery has run (e.g., at app startup or first use)
            # For simplicity, let's assume discover_plugins() has been called elsewhere.
            # If not, it should be called here or plugin_manager needs to be initialized.
            if (
                not plugin_manager.list_available_plugin_classes()
            ):  # Check if discovery might be needed
                print(
                    "Warning: No plugin classes found in registry. Attempting discovery..."
                )
                plugin_manager.discover_plugins()  # Ensure plugins are discoverable

            instance = plugin_manager.get_active_plugin_instance(
                quality_evaluator_plugin_id,
                config=plugin_config,
                force_reload=True,  # Get a fresh instance for this search run
            )
            if isinstance(instance, QualityEvaluatorPlugin):
                _active_quality_evaluator_plugin = instance
                print(
                    f"Using QualityEvaluatorPlugin: {quality_evaluator_plugin_id}"
                )
            elif instance:  # Found something but not the right type
                print(
                    f"Warning: Plugin '{quality_evaluator_plugin_id}' found but is not a QualityEvaluatorPlugin. Using default."
                )
            else:  # Plugin not found
                print(
                    f"Warning: QualityEvaluatorPlugin '{quality_evaluator_plugin_id}' not found. Using default quality evaluation."
                )

        # gp_minimize performs Bayesian optimization (Gaussian Process minimization).
        # It attempts to find the minimum of `_objective_function`.
        gp_minimize(
            func=_objective_function,
            dimensions=search_space,
            n_calls=n_calls,
            n_random_starts=n_random_starts,  # Number of evaluations of `_objective_function` with random points before building the surrogate model.
            random_state=random_state,  # For reproducibility.
        )

        # Ensure uniqueness of hits based on the ABCTriple, keeping the one with potentially
        # highest quality if somehow duplicates were generated (though unlikely with gp_minimize).
        # The original code used a simple dict comprehension which is fine.
        unique_hits_map = {
            hit.triple: hit for hit in _found_hits_during_search
        }
        unique_hits_list = list(unique_hits_map.values())

        # Sort hits by quality in descending order
        unique_hits_list.sort(key=lambda x: x.quality, reverse=True)

        return unique_hits_list


# Example usage (optional, for direct testing of this module if needed):
if __name__ == "__main__":
    use_case = IntelligentSearchUseCase()
    print("Starting intelligent search...")
    # Lower n_calls for quick test
    results = use_case.search(n_calls=25, n_random_starts=5)
    if results:
        print(f"Found {len(results)} unique high-quality hits:")
        for hit in results:
            print(
                f"  Triple: a={hit.triple.a}, b={hit.triple.b}, c={hit.triple.c}, Quality: {hit.quality:.4f}"
            )
    else:
        print("No high-quality hits found in this run.")
