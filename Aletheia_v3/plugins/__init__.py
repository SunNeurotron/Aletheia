# Aletheia_v3/plugins/__init__.py

# This file makes the 'plugins' directory a Python package.
# It can also be used for managing plugin registration or providing convenience imports.

# For now, it's kept simple. Plugin loading logic might go into a `manager.py`
# or could be initiated from here if desired.

PLUGIN_REGISTRY = {} # A simple global registry for loaded plugins

def register_plugin(name, plugin_instance):
    """Registers a plugin instance."""
    # Could add checks for interface compliance here if desired,
    # though type hinting and ABCs handle some of this.
    if name in PLUGIN_REGISTRY:
        print(f"Warning: Plugin with name '{name}' is being overwritten.")
    PLUGIN_REGISTRY[name] = plugin_instance
    print(f"Plugin '{name}' registered of type {type(plugin_instance).__name__}.")

def get_plugin(name):
    """Retrieves a registered plugin by name."""
    return PLUGIN_REGISTRY.get(name)

def list_plugins():
    """Lists all registered plugins."""
    return list(PLUGIN_REGISTRY.keys())

# More sophisticated plugin loading (e.g., from directories or entry points)
# would typically reside in a dedicated plugin manager module.
# For now, plugins might register themselves by calling `register_plugin` upon import.

print("Aletheia Plugin Subsystem Initialized.")
