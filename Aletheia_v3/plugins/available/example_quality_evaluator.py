# Aletheia_v3/plugins/available/example_quality_evaluator.py

from Aletheia_v3.plugins.plugin_interfaces import QualityEvaluatorPlugin
from Aletheia_v3.core.domain import get_quality as default_get_quality # Import default for comparison or fallback

class SimpleBonusQualityEvaluator(QualityEvaluatorPlugin):
    """
    An example QualityEvaluatorPlugin that adds a small constant bonus
    to the default quality score, or implements a slightly different logic.
    """

    CONFIG_KEY_BONUS_AMOUNT = "bonus_amount"
    CONFIG_KEY_USE_DEFAULT_BASE = "use_default_base_quality"

    def __init__(self):
        self._bonus_amount = 0.01 # Default bonus
        self._use_default_base = True
        print(f"Plugin '{self.name}' instance created.")

    @property
    def name(self) -> str:
        return "SimpleBonusQuality"

    @property
    def version(self) -> str:
        return "0.1.0"

    def initialize(self, config=None):
        super().initialize(config) # Call base class initialize
        if config:
            self._bonus_amount = config.get(self.CONFIG_KEY_BONUS_AMOUNT, self._bonus_amount)
            self._use_default_base = config.get(self.CONFIG_KEY_USE_DEFAULT_BASE, self._use_default_base)
        print(f"'{self.name}' configured: Bonus Amount = {self._bonus_amount}, Use Default Base = {self._use_default_base}")


    def evaluate_quality(self, a: int, b: int) -> float:
        """
        Calculates quality by taking the default quality and adding a configured bonus.
        Or, it could implement an entirely different quality metric.
        """
        if self._use_default_base:
            base_quality = default_get_quality(a, b)
            # Add bonus only if the base quality is already somewhat promising (e.g., > 0)
            # to avoid promoting clearly bad triples.
            plugin_modified_quality = base_quality + self._bonus_amount if base_quality > 0 else base_quality
            # print(f"Plugin '{self.name}': a={a}, b={b}, base_q={base_quality:.4f}, bonus={self._bonus_amount if base_quality > 0 else 0}, final_q={plugin_modified_quality:.4f}")
        else:
            # Example of a completely different, simplistic quality metric for demonstration
            # This is NOT a good actual quality metric for ABC.
            # It's just to show plugin can override fully.
            # Let's make it something that prefers smaller 'a' and larger 'b'
            if a == 0: return 0.0
            plugin_modified_quality = (b / a) * 0.001 # Arbitrary alternate logic
            # print(f"Plugin '{self.name}' (custom logic): a={a}, b={b}, final_q={plugin_modified_quality:.4f}")


        # Ensure quality is not negative, as objective function expects non-negative from underlying quality funcs
        return max(0.0, plugin_modified_quality)

# To make this plugin discoverable by the plugin manager,
# it should be placed in a directory that the manager scans (e.g., `plugins/available/`).
# The plugin manager (manager.py) would then be responsible for finding and loading it.

# Self-registration example (optional, depends on plugin manager design)
# from Aletheia_v3.plugins import register_plugin
# if __name__ != '__main__': # Avoid registration if script is run directly
#    try:
#        register_plugin(SimpleBonusQualityEvaluator.name, SimpleBonusQualityEvaluator())
#    except Exception as e:
#        print(f"Error self-registering SimpleBonusQualityEvaluator: {e}")
```
