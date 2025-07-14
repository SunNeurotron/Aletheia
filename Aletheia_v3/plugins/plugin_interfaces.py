# Copyright 2025 Alant
#
# Licensed under the Aletheia Unificada Ethical Public License (AUEPL);
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

# Aletheia_v3/plugins/plugin_interfaces.py

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List

# Import types from the core application if needed for method signatures.
# Use TYPE_CHECKING to avoid circular imports at runtime but allow type hints.
if TYPE_CHECKING:
    from Aletheia_v3.core.domain import ABCQuality, ABCTriple

    # from skopt.space import Space # If search_space object is passed


class AletheiaPluginBase(ABC):
    """
    Base class for all Aletheia plugins.
    Provides common attributes like name and version.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """A unique name for the plugin."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """The version of the plugin."""
        pass

    def initialize(self, config: Dict[str, Any] = None):
        """
        Optional method to initialize the plugin with configuration.
        Called by the plugin manager after loading.
        """
        if config:
            print(
                f"Plugin {self.name} v{self.version} initialized with config: {config}"
            )
        else:
            print(f"Plugin {self.name} v{self.version} initialized.")

    def terminate(self):
        """
        Optional method for cleanup when the plugin is unloaded or application shuts down.
        """
        print(f"Plugin {self.name} v{self.version} terminated.")


class SearchStrategyPlugin(AletheiaPluginBase):
    """
    Interface for plugins that define or modify the search strategy
    in Bayesian Optimization or other search algorithms.
    """

    @abstractmethod
    def suggest_candidates(
        self,
        history_X: List[
            List[float]
        ] = None,  # List of previously evaluated parameter sets
        history_y: List[
            float
        ] = None,  # List of corresponding objective values
        n_suggestions: int = 1,
        search_space_dimensions=None,  # skopt.space.Space object or similar
        optimizer_state: Any = None,  # e.g., the GaussianProcessRegressor model from skopt
    ) -> List[List[float]]:  # List of new candidate parameter sets
        """
        Suggests a new batch of candidate points to evaluate.

        @param history_X: Previously evaluated points.
        @param history_y: Objective values for previously evaluated points.
        @param n_suggestions: Number of new candidates to suggest.
        @param search_space_dimensions: The defined search space.
        @param optimizer_state: Current state of the optimizer (e.g., GP model).
        @returns: A list of new candidate points (parameter sets).
        """
        pass

    # report_results might be handled by the main BO loop telling the optimizer.
    # This interface is more about suggesting where to look next.


class QualityEvaluatorPlugin(AletheiaPluginBase):
    """
    Interface for plugins that provide custom evaluation of the 'quality'
    of an ABC triple, potentially replacing or augmenting the default get_quality.
    """

    @abstractmethod
    def evaluate_quality(self, a: int, b: int) -> float:
        """
        Calculates the quality 'q' for a potential abc-triple (a, b, c=a+b).

        @param a: The first term.
        @param b: The second term.
        @returns: The calculated quality 'q'.
        """
        pass

    def get_domain_constraints(self) -> Dict[str, Any]:
        """
        Optional: Allows plugin to specify if it imposes different constraints
        than the default (e.g., different gcd requirements, a < b, etc.).
        """
        return {}


class DataPostprocessorPlugin(AletheiaPluginBase):
    """
    Interface for plugins that perform custom post-processing on
    discovered hits or job results.
    """

    @abstractmethod
    def process_hits(
        self, hits: List["ABCQuality"], job_metadata: Dict[str, Any] = None
    ) -> Any:
        """
        Processes a list of discovered ABCQuality objects.
        Can be used for custom filtering, analysis, visualization data prep, or external logging.

        @param hits: A list of ABCQuality objects.
        @param job_metadata: Optional metadata about the job that produced these hits.
        @returns: Any processed result (e.g., a modified list, a summary, a path to a saved file).
        """
        pass


class ParameterSpaceModifierPlugin(AletheiaPluginBase):
    """
    Interface for plugins that can dynamically modify the search space
    during optimization, or suggest entirely new search spaces.
    """

    @abstractmethod
    def modify_search_space(
        self, current_search_space, history_X=None, history_y=None
    ):
        """
        Allows modification of the search space dimensions or bounds.
        This is an advanced feature.

        @param current_search_space: The current skopt.space.Space object.
        @param history_X: Previously evaluated points.
        @param history_y: Objective values.
        @returns: A new or modified skopt.space.Space object.
        """
        pass


# Example of how a plugin might look (not a plugin itself, but for thought):
# class MyCustomSearch(SearchStrategyPlugin):
#     name = "MySearch"
#     version = "0.1.0"
#     def suggest_candidates(self, ...):
#         # ... custom logic ...
#         return [[new_log_a, new_log_b]]

# This set of interfaces provides a starting point for various extensibility points.
# More interfaces can be added as needed (e.g., for UI components, data storage backends).
