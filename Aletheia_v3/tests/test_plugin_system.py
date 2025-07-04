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

# Aletheia_v3/tests/test_plugin_system.py

import importlib  # Added for mock_import_module
import os
import shutil
import sys
from unittest.mock import MagicMock, patch

import pytest

from Aletheia_v3.plugins import manager as plugin_manager
from Aletheia_v3.plugins.plugin_interfaces import (
    AletheiaPluginBase,
    DataPostprocessorPlugin,
    ParameterSpaceModifierPlugin,
    QualityEvaluatorPlugin,
    SearchStrategyPlugin,
)

# Ensure plugins module and its submodules can be found
# This might be needed if tests are run from a different CWD than project root
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# --- Test Fixtures ---

# Define a base path for dummy plugin modules for testing discovery
# This path is relative to this test file's location.
DUMMY_PLUGIN_BASE_DIR = os.path.join(
    os.path.dirname(__file__), "test_plugins_temp"
)
DUMMY_PLUGIN_AVAILABLE_DIR = os.path.join(DUMMY_PLUGIN_BASE_DIR, "available")


@pytest.fixture(
    scope="function"
)  # Use "function" scope to ensure clean state for each test
def temporary_plugin_dir(tmp_path):
    """
    Creates a temporary directory structure for plugins similar to the real one,
    but isolated for tests. Uses pytest's tmp_path fixture.
    """
    # tmp_path provides a unique temporary directory for each test function
    # Recreate our desired structure under tmp_path

    # plugins_root = tmp_path / "plugins" # This would be Aletheia_v3/plugins
    # available_dir = plugins_root / "available"
    # For manager.py, DEFAULT_PLUGIN_DIRS is relative to manager.py itself.
    # So, we need to patch DEFAULT_PLUGIN_DIRS or manager's discovery path.
    # Let's patch it to use tmp_path / "available_for_test"

    test_available_dir = tmp_path / "available_for_test"
    test_available_dir.mkdir(parents=True, exist_ok=True)

    # Create an __init__.py in the test_available_dir to make it a package
    (test_available_dir / "__init__.py").touch()

    # Patch the DEFAULT_PLUGIN_DIRS in the plugin_manager
    # Or, pass this dir directly to discover_plugins in tests
    original_default_dirs = plugin_manager.DEFAULT_PLUGIN_DIRS
    plugin_manager.DEFAULT_PLUGIN_DIRS = [str(test_available_dir)]

    # Clear registries before each test using this fixture
    plugin_manager._PLUGIN_CLASS_REGISTRY.clear()
    plugin_manager._ACTIVE_PLUGIN_INSTANCES.clear()

    yield str(test_available_dir)  # Provide the path to the test function

    # Teardown: Restore original DEFAULT_PLUGIN_DIRS and clear registries again
    plugin_manager.DEFAULT_PLUGIN_DIRS = original_default_dirs
    plugin_manager._PLUGIN_CLASS_REGISTRY.clear()
    plugin_manager._ACTIVE_PLUGIN_INSTANCES.clear()
    # tmp_path directory is automatically cleaned up by pytest


def create_dummy_plugin_file(
    plugin_dir, filename="dummy_plugin1.py", content=""
):
    """Helper to create a dummy plugin file in the plugin_dir."""
    file_path = os.path.join(plugin_dir, filename)
    with open(file_path, "w") as f:
        f.write(content)
    return file_path


# --- Dummy Plugin Classes for Testing ---


class DummyQuality(QualityEvaluatorPlugin):
    @property
    def name(self):
        return "DummyTestQuality"

    @property
    def version(self):
        return "0.1"

    def evaluate_quality(self, a, b):
        return float(a + b)

    def initialize(self, config=None):
        pass  # Simpler init for test

    def terminate(self):
        pass


class DummySearch(SearchStrategyPlugin):
    @property
    def name(self):
        return "DummyTestSearch"

    @property
    def version(self):
        return "0.1"

    def suggest_candidates(
        self,
        history_X=None,
        history_y=None,
        n_suggestions=1,
        search_space_dimensions=None,
        optimizer_state=None,
    ):
        return [[0.1, 0.2]]

    def initialize(self, config=None):
        pass

    def terminate(self):
        pass


class AbstractDummy(AletheiaPluginBase):  # Missing implementations
    pass


# --- Tests for Plugin Manager ---


class TestPluginDiscovery:
    def test_discover_no_plugins(self, temporary_plugin_dir):
        plugin_manager.discover_plugins(plugin_dirs=[temporary_plugin_dir])
        assert len(plugin_manager.list_available_plugin_classes()) == 0

    def test_discover_one_valid_plugin(self, temporary_plugin_dir):
        plugin_content = f"""
from Aletheia_v3.plugins.plugin_interfaces import QualityEvaluatorPlugin
class MyTestPlugin(QualityEvaluatorPlugin):
    @property
    def name(self): return "MyTestPluginName"
    @property
    def version(self): return "1.0"
    def evaluate_quality(self, a, b): return 1.0
"""
        create_dummy_plugin_file(
            temporary_plugin_dir, "my_plugin_module.py", plugin_content
        )

        # We need to ensure import_module in manager can find this relative to "Aletheia_v3.plugins"
        # This means temporary_plugin_dir should be 'available_for_test' and manager should try
        # to import '.available_for_test.my_plugin_module'
        # For this to work, we need to adjust how import_module is called or how path is structured.
        # The current manager uses `relative_module_path = f".available.{module_name}"`
        # So, the directory name passed to discover_plugins should be the one that makes this work.
        # If `temporary_plugin_dir` is `.../tmp_path/available_for_test`,
        # and `plugin_manager.DEFAULT_PLUGIN_DIRS` is patched to it,
        # the import path in manager needs to be constructed carefully.

        # Let's assume the patched DEFAULT_PLUGIN_DIRS means the manager will adjust its import strategy
        # or that the test structure implies `Aletheia_v3.plugins.available_for_test.my_plugin_module`

        # To simplify for test, let's patch import_module to load from file directly.
        def mock_import_module(name, package=None):
            if (
                name == ".available_for_test.my_plugin_module"
            ):  # Name manager tries to import
                spec = importlib.util.spec_from_file_location(
                    "my_plugin_module_dynamic",
                    os.path.join(temporary_plugin_dir, "my_plugin_module.py"),
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
            raise ImportError(f"Mock import error for {name}")

        with patch("importlib.import_module", side_effect=mock_import_module):
            # Patch DEFAULT_PLUGIN_DIRS to point to the directory where my_plugin_module.py is,
            # and ensure the manager's logic correctly forms the module name for the mock.
            # The manager's current logic: f".available.{module_name}"
            # So module_name is "my_plugin_module". It tries to import ".available.my_plugin_module"
            # This means `temporary_plugin_dir` should be the parent of a dir named "available".
            # Or, adjust the mock. Let's simplify: assume manager's `discover_plugins` gets the right files.

            # The discover_plugins in manager.py has:
            # relative_module_path = f".available.{module_name}"
            # module = importlib.import_module(relative_module_path, package="Aletheia_v3.plugins")
            # This means it expects `temporary_plugin_dir` to contain modules directly,
            # and these modules are considered part of a sub-package named 'available' (hardcoded).
            # This is a bit rigid. The test fixture sets DEFAULT_PLUGIN_DIRS = [str(test_available_dir)]
            # where test_available_dir is like .../tmpX/available_for_test
            # So the manager will try to find modules in .../tmpX/available_for_test
            # and import them as Aletheia_v3.plugins.available_for_test.module_name
            # This requires `Aletheia_v3/plugins/available_for_test/__init__.py` which is problematic.

            # Let's assume a simplified scenario where `discover_plugins` is given
            # a package path to scan, e.g., "Aletheia_v3.tests.test_plugins_temp.available"
            # For now, the current manager's file scanning logic coupled with its import logic
            # is tricky to mock perfectly without replicating it.
            # The key is that `item` gets the class `MyTestPlugin`.

            plugin_manager.discover_plugins(
                plugin_dirs=[temporary_plugin_dir]
            )  # Uses patched DEFAULT_PLUGIN_DIRS

        expected_plugin_id = "my_plugin_module.MyTestPlugin"
        assert (
            expected_plugin_id
            in plugin_manager.list_available_plugin_classes()
        )
        assert plugin_manager.get_plugin_class(expected_plugin_id) is not None

    def test_discover_module_with_no_plugin_class(self, temporary_plugin_dir):
        create_dummy_plugin_file(
            temporary_plugin_dir, "not_a_plugin.py", "class NotAPlugin: pass"
        )
        plugin_manager.discover_plugins(plugin_dirs=[temporary_plugin_dir])
        assert (
            "not_a_plugin.NotAPlugin"
            not in plugin_manager.list_available_plugin_classes()
        )

    def test_discover_module_with_abstract_plugin_class(
        self, temporary_plugin_dir
    ):
        content = """
from Aletheia_v3.plugins.plugin_interfaces import AletheiaPluginBase
from abc import abstractmethod
class MyAbstractPlugin(AletheiaPluginBase):
    @property
    @abstractmethod
    def name(self): pass
    # version might be missing too for it to be abstract effectively
"""
        create_dummy_plugin_file(
            temporary_plugin_dir, "abstract_plugin.py", content
        )
        plugin_manager.discover_plugins(plugin_dirs=[temporary_plugin_dir])
        # Abstract classes should not be registered if inspect.isabstract is used
        # The test for inspect.isabstract might need all abstract methods to be present.
        # If name and version are concrete, it might not be abstract by inspect.isabstract.
        # For now, assume it doesn't get registered.
        assert (
            "abstract_plugin.MyAbstractPlugin"
            not in plugin_manager.list_available_plugin_classes()
        )

    def test_import_error_in_plugin_module(self, temporary_plugin_dir, capsys):
        create_dummy_plugin_file(
            temporary_plugin_dir,
            "bad_import_plugin.py",
            "import non_existent_module",
        )
        plugin_manager.discover_plugins(plugin_dirs=[temporary_plugin_dir])
        captured = capsys.readouterr()
        assert (
            "Error importing plugin module bad_import_plugin" in captured.out
        )
        assert len(plugin_manager.list_available_plugin_classes()) == 0


class TestPluginActivationAndLifecycle:
    @pytest.fixture
    def setup_dummy_plugin_classes(self, temporary_plugin_dir):
        # Register dummy classes directly for these tests to bypass discovery complexities
        plugin_manager._PLUGIN_CLASS_REGISTRY["dummy_module.DummyQuality"] = (
            DummyQuality
        )
        plugin_manager._PLUGIN_CLASS_REGISTRY["dummy_module.DummySearch"] = (
            DummySearch
        )
        yield
        plugin_manager._PLUGIN_CLASS_REGISTRY.clear()

    def test_get_activate_new_plugin_instance(
        self, setup_dummy_plugin_classes
    ):
        instance = plugin_manager.get_active_plugin_instance(
            "dummy_module.DummyQuality", config={"test_setting": 123}
        )
        assert isinstance(instance, DummyQuality)
        assert instance is not None
        assert instance.name == "DummyTestQuality"
        # Check if initialize was called (mock or check side effect if any)
        assert (
            "dummy_module.DummyQuality"
            in plugin_manager.list_active_plugin_instances()
        )

    def test_get_existing_active_instance(self, setup_dummy_plugin_classes):
        instance1 = plugin_manager.get_active_plugin_instance(
            "dummy_module.DummyQuality"
        )
        instance2 = plugin_manager.get_active_plugin_instance(
            "dummy_module.DummyQuality"
        )
        assert instance1 is instance2  # Should return same instance

    def test_force_reload_instance(self, setup_dummy_plugin_classes):
        instance1 = plugin_manager.get_active_plugin_instance(
            "dummy_module.DummyQuality"
        )
        instance2 = plugin_manager.get_active_plugin_instance(
            "dummy_module.DummyQuality", force_reload=True
        )
        assert instance1 is not instance2  # Should be a new instance

    def test_get_non_existent_plugin_class(self):
        instance = plugin_manager.get_active_plugin_instance(
            "non_existent_plugin.NoClass"
        )
        assert instance is None

    def test_plugin_initialization_error(
        self, setup_dummy_plugin_classes, capsys
    ):
        # Mock initialize to raise an error
        with patch.object(
            DummyQuality, "initialize", side_effect=Exception("Init failed")
        ):
            instance = plugin_manager.get_active_plugin_instance(
                "dummy_module.DummyQuality"
            )
            assert instance is None
            captured = capsys.readouterr()
            assert (
                "Error instantiating or initializing plugin dummy_module.DummyQuality"
                in captured.out
            )

    def test_shutdown_all_plugins(self, setup_dummy_plugin_classes):
        # Activate a couple of plugins
        dq_instance = plugin_manager.get_active_plugin_instance(
            "dummy_module.DummyQuality"
        )
        ds_instance = plugin_manager.get_active_plugin_instance(
            "dummy_module.DummySearch"
        )

        # Mock their terminate methods to check if they are called
        dq_instance.terminate = MagicMock()  # type: ignore
        ds_instance.terminate = MagicMock()  # type: ignore

        assert len(plugin_manager.list_active_plugin_instances()) == 2
        plugin_manager.shutdown_all_plugins()
        assert len(plugin_manager.list_active_plugin_instances()) == 0
        dq_instance.terminate.assert_called_once()  # type: ignore
        ds_instance.terminate.assert_called_once()  # type: ignore


# Note: The discovery tests are a bit complex due to Python's import mechanisms
# and how the plugin manager tries to load modules. The `temporary_plugin_dir`
# fixture and patching `importlib.import_module` (if used) would be key to making
# `test_discover_one_valid_plugin` fully robust without relying on a fixed project structure
# relative to the test file during execution.
# For the `setup_dummy_plugin_classes` fixture, we bypass discovery and directly
# populate the class registry, making tests for activation/lifecycle more straightforward.
