# Aletheia_v3/plugins/manager.py

import os
import importlib
import inspect
from typing import Dict, Type, List, Optional
from .plugin_interfaces import AletheiaPluginBase

# Global registry for loaded plugin classes (not instances)
# { 'plugin_name_version': PluginClass }
_PLUGIN_CLASS_REGISTRY: Dict[str, Type[AletheiaPluginBase]] = {}
# Global registry for active plugin instances
# { 'plugin_name_version': plugin_instance }
_ACTIVE_PLUGIN_INSTANCES: Dict[str, AletheiaPluginBase] = {}

# Default directory to scan for plugins relative to this manager.py file or Aletheia_v3 root.
# For simplicity, let's assume a subdirectory `available` within `plugins` for discoverable plugins.
DEFAULT_PLUGIN_DIRS = [os.path.join(os.path.dirname(__file__), "available")]

def discover_plugins(plugin_dirs: Optional[List[str]] = None) -> None:
    """
    Discovers and loads plugin classes from specified directories.
    A plugin is a Python module containing classes that inherit from AletheiaPluginBase.
    """
    if plugin_dirs is None:
        plugin_dirs = DEFAULT_PLUGIN_DIRS

    _PLUGIN_CLASS_REGISTRY.clear() # Clear previous discoveries if re-discovering

    for plugin_dir in plugin_dirs:
        if not os.path.isdir(plugin_dir):
            print(f"Plugin directory not found or not a directory: {plugin_dir}")
            continue

        print(f"Scanning for plugins in: {plugin_dir}")
        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                # Construct module path relative to the 'plugins' package for importlib
                # Assuming plugin_dir is like ".../Aletheia_v3/plugins/available"
                # and plugins package is Aletheia_v3.plugins
                # Module path would be "Aletheia_v3.plugins.available.{module_name}"

                # Simplified module path construction for this example:
                # This requires 'available' to be a package itself (with __init__.py)
                # or for plugin_dir to be added to sys.path temporarily.
                # For now, let's assume 'Aletheia_v3.plugins.available' is the base path.
                # This needs careful handling of Python's import system.

                # A more robust way if plugin_dir is absolute or relative to project root:
                # spec = importlib.util.spec_from_file_location(f"aletheia_plugins_dynamic.{module_name}", os.path.join(plugin_dir, filename))
                # if spec and spec.loader:
                #    module = importlib.util.module_from_spec(spec)
                #    spec.loader.exec_module(module)
                # else:
                #    print(f"Could not load module spec for {filename}")
                #    continue

                # Simpler approach assuming 'Aletheia_v3.plugins.available' is a valid package path:
                try:
                    # Example: module_import_path = "Aletheia_v3.plugins.available.my_plugin_module"
                    # This structure assumes plugins/available/ is a package.
                    # If plugin_dir is plugins/available, then the package is .available
                    relative_module_path = f".available.{module_name}" # Relative to 'plugins' package
                    module = importlib.import_module(relative_module_path, package="Aletheia_v3.plugins")
                except ImportError as e:
                    print(f"Error importing plugin module {module_name} from {plugin_dir}: {e}")
                    continue

                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if inspect.isclass(item) and \
                       issubclass(item, AletheiaPluginBase) and \
                       item is not AletheiaPluginBase and \
                       not inspect.isabstract(item): # Do not load abstract classes or the base itself

                        try:
                            # Instantiate to get name and version for registry key
                            # This assumes plugins can be instantiated without args for this check
                            # Or that name/version are class attributes. Let's assume they are properties for now.
                            # For simplicity, we'll register the class, not an instance here.
                            # Instantiation will happen when activating/getting a plugin.

                            # To get name/version for key, we might need to temporarily instantiate or use class vars
                            # temp_instance_for_props = item() # This might fail if __init__ needs args
                            # plugin_id = f"{temp_instance_for_props.name}_v{temp_instance_for_props.version}"

                            # Simpler: Use class name as part of ID if name/version are instance properties
                            # This means multiple plugins with same class name would conflict if not careful.
                            # A better ID might be module_name.ClassName
                            plugin_id = f"{module_name}.{item.__name__}"

                            if plugin_id in _PLUGIN_CLASS_REGISTRY:
                                print(f"Warning: Plugin class '{plugin_id}' already registered. Overwriting.")
                            _PLUGIN_CLASS_REGISTRY[plugin_id] = item
                            print(f"Discovered plugin class: '{plugin_id}' from {filename}")
                        except Exception as e:
                            print(f"Error processing class {item_name} in {filename}: {e}")

    print(f"Plugin discovery complete. Found {len(_PLUGIN_CLASS_REGISTRY)} plugin classes.")


def get_plugin_class(plugin_id: str) -> Optional[Type[AletheiaPluginBase]]:
    """Retrieves a loaded plugin class by its ID."""
    return _PLUGIN_CLASS_REGISTRY.get(plugin_id)

def get_active_plugin_instance(plugin_id: str, config: Dict[str, Any] = None, force_reload: bool = False) -> Optional[AletheiaPluginBase]:
    """
    Retrieves an active instance of a plugin.
    If not already instantiated, it creates an instance.
    If force_reload is True, it creates a new instance.
    """
    if not force_reload and plugin_id in _ACTIVE_PLUGIN_INSTANCES:
        return _ACTIVE_PLUGIN_INSTANCES[plugin_id]

    PluginClass = get_plugin_class(plugin_id)
    if PluginClass:
        try:
            instance = PluginClass() # Assumes constructor takes no args or uses defaults
            instance.initialize(config) # Call initialize method
            _ACTIVE_PLUGIN_INSTANCES[plugin_id] = instance
            print(f"Activated plugin instance: {plugin_id}")
            return instance
        except Exception as e:
            print(f"Error instantiating or initializing plugin {plugin_id}: {e}")
            return None
    else:
        print(f"Plugin class with ID '{plugin_id}' not found in registry.")
        return None

def list_available_plugin_classes() -> List[str]:
    """Lists the IDs of all discovered plugin classes."""
    return list(_PLUGIN_CLASS_REGISTRY.keys())

def list_active_plugin_instances() -> List[str]:
    """Lists the IDs of all currently active plugin instances."""
    return list(_ACTIVE_PLUGIN_INSTANCES.keys())

def shutdown_all_plugins():
    """Calls terminate() on all active plugin instances and clears them."""
    print("Shutting down all active plugins...")
    for plugin_id, instance in list(_ACTIVE_PLUGIN_INSTANCES.items()): # Iterate over a copy
        try:
            instance.terminate()
        except Exception as e:
            print(f"Error terminating plugin {plugin_id}: {e}")
    _ACTIVE_PLUGIN_INSTANCES.clear()
    print("All active plugins shut down and cleared.")


# Example: Discover plugins on import of this manager, or call explicitly from app startup.
# To make plugins discoverable, create an 'available' subdirectory in 'plugins'
# and put plugin modules there. Also, `plugins/available/__init__.py` should exist.
# discover_plugins()
# The above line would run discovery when manager.py is imported.
# It's often better to call discover_plugins() explicitly at application startup.

if __name__ == '__main__':
    # Example usage (requires dummy plugins in plugins/available/)

    # Create dummy structure for testing:
    # Aletheia_v3/plugins/available/__init__.py (empty)
    # Aletheia_v3/plugins/available/dummy_plugin.py
    #   from ..plugin_interfaces import QualityEvaluatorPlugin
    #   class MyDummyEvaluator(QualityEvaluatorPlugin):
    #       @property
    #       def name(self): return "DummyQuality"
    #       @property
    #       def version(self): return "0.1"
    #       def evaluate_quality(self, a, b): return 0.01 * (a+b)

    # Create the 'available' directory if it doesn't exist for the example
    example_plugin_dir = os.path.join(os.path.dirname(__file__), "available")
    if not os.path.exists(example_plugin_dir):
        os.makedirs(example_plugin_dir)
        with open(os.path.join(example_plugin_dir, "__init__.py"), "w") as f:
            f.write("# Makes 'available' a package\n")
        with open(os.path.join(example_plugin_dir, "dummy_eval_plugin.py"), "w") as f:
            f.write("from Aletheia_v3.plugins.plugin_interfaces import QualityEvaluatorPlugin\n\n"
                    "class DummyEvaluator(QualityEvaluatorPlugin):\n"
                    "    @property\n"
                    "    def name(self):\n        return 'DummyQualityEval'\n"
                    "    @property\n"
                    "    def version(self):\n        return '1.0'\n"
                    "    def evaluate_quality(self, a: int, b: int) -> float:\n"
                    "        return 0.05 * (a + b - 10) # Arbitrary logic\n")

    print("Running plugin manager example...")
    discover_plugins()
    print(f"Available plugin classes: {list_available_plugin_classes()}")

    if list_available_plugin_classes():
        plugin_id_to_test = list_available_plugin_classes()[0]
        print(f"\nActivating plugin: {plugin_id_to_test}")
        instance = get_active_plugin_instance(plugin_id_to_test, config={"setting": "value"})
        if instance:
            print(f"Instance type: {type(instance)}")
            if hasattr(instance, "evaluate_quality"): # Check if it's a QualityEvaluatorPlugin
                print(f"Dummy quality for (20,30) from plugin: {instance.evaluate_quality(20,30)}")

        print(f"Active plugin instances: {list_active_plugin_instances()}")
        shutdown_all_plugins()
        print(f"Active plugin instances after shutdown: {list_active_plugin_instances()}")
    else:
        print("No plugins found to test.")

    # Cleanup dummy files for example
    # (In a real test, this would be handled by test fixtures and teardown)
    # os.remove(os.path.join(example_plugin_dir, "dummy_eval_plugin.py"))
    # os.remove(os.path.join(example_plugin_dir, "__init__.py"))
    # if not os.listdir(example_plugin_dir): # Only remove if empty
    #    os.rmdir(example_plugin_dir)

```

**To make this runnable and testable in the current environment, I also need to create the `Aletheia_v3/plugins/available/__init__.py` file.**
