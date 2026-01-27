"""Property-based tests for the plugin system."""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, Any, List
import tempfile
import json
from pathlib import Path

from sep_solver.core.plugin_system import (
    Plugin, PluginMetadata, PluginRegistry, PluginManager,
    get_plugin_manager, register_plugin
)
from sep_solver.core.interfaces import StructureGenerator, VariableAssigner, ConstraintEvaluator, SchemaValidator
from sep_solver.core.exceptions import ConfigurationError
from sep_solver.models.constraint_set import ConstraintSet
from sep_solver.models.structure import Structure, Component, Relationship
from sep_solver.models.variable_assignment import VariableAssignment, Domain


# Test plugin implementations
class TestStructureGeneratorPlugin(Plugin):
    """Test plugin for structure generator."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._metadata = PluginMetadata(
            name=f"test_structure_generator_{id(self)}",
            version="1.0.0",
            description="Test structure generator plugin",
            component_type="structure_generator"
        )
    
    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata
    
    def create_component(self) -> StructureGenerator:
        from sep_solver.generators.structure_generator import BaseStructureGenerator
        return BaseStructureGenerator()


class TestVariableAssignerPlugin(Plugin):
    """Test plugin for variable assigner."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._metadata = PluginMetadata(
            name=f"test_variable_assigner_{id(self)}",
            version="1.0.0",
            description="Test variable assigner plugin",
            component_type="variable_assigner"
        )
    
    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata
    
    def create_component(self) -> VariableAssigner:
        from sep_solver.generators.variable_assigner import BaseVariableAssigner
        return BaseVariableAssigner()


class TestConstraintEvaluatorPlugin(Plugin):
    """Test plugin for constraint evaluator."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._metadata = PluginMetadata(
            name=f"test_constraint_evaluator_{id(self)}",
            version="1.0.0",
            description="Test constraint evaluator plugin",
            component_type="constraint_evaluator"
        )
    
    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata
    
    def create_component(self) -> ConstraintEvaluator:
        from sep_solver.evaluators.constraint_evaluator import BaseConstraintEvaluator
        return BaseConstraintEvaluator(ConstraintSet())


class TestSchemaValidatorPlugin(Plugin):
    """Test plugin for schema validator."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._metadata = PluginMetadata(
            name=f"test_schema_validator_{id(self)}",
            version="1.0.0",
            description="Test schema validator plugin",
            component_type="schema_validator"
        )
    
    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata
    
    def create_component(self) -> SchemaValidator:
        from sep_solver.evaluators.schema_validator import JSONSchemaValidator
        return JSONSchemaValidator({})


# Strategies for generating test data
@st.composite
def plugin_metadata_strategy(draw):
    """Generate plugin metadata."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    version = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Nd', 'Po'))))
    description = draw(st.text(min_size=1, max_size=200))
    component_type = draw(st.sampled_from(["structure_generator", "variable_assigner", "constraint_evaluator", "schema_validator"]))
    
    return PluginMetadata(
        name=name,
        version=version,
        description=description,
        component_type=component_type
    )


@st.composite
def plugin_config_strategy(draw):
    """Generate plugin configuration."""
    config = {}
    num_keys = draw(st.integers(min_value=0, max_value=5))
    
    for _ in range(num_keys):
        key = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
        value = draw(st.one_of(
            st.text(max_size=50),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans()
        ))
        config[key] = value
    
    return config


class TestPluginSystemProperties:
    """Property-based tests for plugin system functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create fresh plugin manager for each test
        global _plugin_manager
        import sep_solver.core.plugin_system as plugin_module
        plugin_module._plugin_manager = None
    
    @given(plugin_config_strategy())
    @settings(max_examples=50)
    def test_plugin_registration_and_retrieval(self, config):
        """
        **Property 9: Plugin Component Substitution**
        **Validates: Requirements 8.1**
        
        For any plugin with valid metadata and configuration, registering it should
        allow retrieval and component creation, and the created component should
        implement the expected interface.
        """
        registry = PluginRegistry()
        
        # Test with each component type
        component_types = ["structure_generator", "variable_assigner", "constraint_evaluator", "schema_validator"]
        
        for component_type in component_types:
            # Create appropriate test plugin
            if component_type == "structure_generator":
                plugin = TestStructureGeneratorPlugin(config)
            elif component_type == "variable_assigner":
                plugin = TestVariableAssignerPlugin(config)
            elif component_type == "constraint_evaluator":
                plugin = TestConstraintEvaluatorPlugin(config)
            else:  # schema_validator
                plugin = TestSchemaValidatorPlugin(config)
            
            # Register plugin
            registry.register_plugin(plugin)
            
            # Verify plugin is registered
            retrieved_plugin = registry.get_plugin(plugin.metadata.name)
            assert retrieved_plugin is not None
            assert retrieved_plugin.metadata.name == plugin.metadata.name
            assert retrieved_plugin.metadata.component_type == component_type
            
            # Verify plugin appears in component type listing
            plugins_by_type = registry.get_plugins_by_type(component_type)
            assert any(p.metadata.name == plugin.metadata.name for p in plugins_by_type)
            
            # Create component and verify interface
            component = registry.create_component(plugin.metadata.name)
            
            if component_type == "structure_generator":
                assert isinstance(component, StructureGenerator)
            elif component_type == "variable_assigner":
                assert isinstance(component, VariableAssigner)
            elif component_type == "constraint_evaluator":
                assert isinstance(component, ConstraintEvaluator)
            else:  # schema_validator
                assert isinstance(component, SchemaValidator)
    
    @given(st.lists(plugin_config_strategy(), min_size=1, max_size=5))
    @settings(max_examples=30)
    def test_multiple_plugin_registration(self, configs):
        """
        Test that multiple plugins can be registered and managed correctly.
        """
        registry = PluginRegistry()
        registered_plugins = []
        
        for i, config in enumerate(configs):
            # Create plugin with unique name
            plugin = TestStructureGeneratorPlugin(config)
            plugin._metadata.name = f"test_plugin_{i}"
            
            registry.register_plugin(plugin)
            registered_plugins.append(plugin)
        
        # Verify all plugins are registered
        all_plugins = registry.list_plugins()
        assert len(all_plugins) == len(registered_plugins)
        
        # Verify each plugin can be retrieved and used
        for plugin in registered_plugins:
            retrieved = registry.get_plugin(plugin.metadata.name)
            assert retrieved is not None
            
            component = registry.create_component(plugin.metadata.name)
            assert isinstance(component, StructureGenerator)
    
    @given(plugin_config_strategy())
    @settings(max_examples=5, deadline=None)  # Disable deadline for this test
    def test_plugin_substitution_maintains_functionality(self, config):
        """
        Test that substituting plugins maintains core functionality.
        """
        from sep_solver.core.engine import SEPEngine
        from sep_solver.core.config import SolverConfig
        from sep_solver.models.constraint_set import ConstraintSet
        
        # Create basic test setup
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        constraints = ConstraintSet()
        solver_config = SolverConfig()
        
        # Create engine with default components
        engine1 = SEPEngine(schema, constraints, solver_config)
        
        # Verify engine1 has components
        assert hasattr(engine1, 'structure_generator')
        assert hasattr(engine1, 'variable_assigner')
        assert hasattr(engine1, 'constraint_evaluator')
        assert hasattr(engine1, 'schema_validator')
        
        # Create engine with plugin-based components
        engine2 = SEPEngine(schema, constraints, solver_config)
        
        # Replace components with plugin-created ones
        plugin_manager = get_plugin_manager()
        plugin_manager.register_default_plugins()
        
        # Register test plugins
        test_sg_plugin = TestStructureGeneratorPlugin(config)
        test_va_plugin = TestVariableAssignerPlugin(config)
        
        plugin_manager.registry.register_plugin(test_sg_plugin)
        plugin_manager.registry.register_plugin(test_va_plugin)
        
        # Set components via plugins
        engine2.set_component_via_plugin("structure_generator", test_sg_plugin.metadata.name)
        engine2.set_component_via_plugin("variable_assigner", test_va_plugin.metadata.name)
        
        # Both engines should have the same interface
        assert hasattr(engine1, 'solve')
        assert hasattr(engine2, 'solve')
        assert hasattr(engine1, 'explore_step')
        assert hasattr(engine2, 'explore_step')
        
        # Both engines should have components of the correct type
        assert isinstance(engine1.structure_generator, StructureGenerator)
        assert isinstance(engine2.structure_generator, StructureGenerator)
        assert isinstance(engine1.variable_assigner, VariableAssigner)
        assert isinstance(engine2.variable_assigner, VariableAssigner)
    
    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=30)
    def test_plugin_unregistration(self, plugin_name_suffix):
        """
        Test that plugins can be unregistered correctly.
        """
        registry = PluginRegistry()
        
        # Register a plugin
        plugin = TestStructureGeneratorPlugin()
        plugin._metadata.name = f"test_plugin_{plugin_name_suffix}"
        registry.register_plugin(plugin)
        
        # Verify plugin is registered
        assert registry.get_plugin(plugin.metadata.name) is not None
        assert len(registry.get_plugins_by_type("structure_generator")) >= 1
        
        # Unregister plugin
        registry.unregister_plugin(plugin.metadata.name)
        
        # Verify plugin is unregistered
        assert registry.get_plugin(plugin.metadata.name) is None
        
        # Verify plugin is removed from component type listing
        remaining_plugins = registry.get_plugins_by_type("structure_generator")
        assert not any(p.metadata.name == plugin.metadata.name for p in remaining_plugins)
    
    @given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=3, unique=True))
    @settings(max_examples=20)
    def test_plugin_discovery_simulation(self, plugin_names):
        """
        Test plugin discovery and loading simulation.
        """
        registry = PluginRegistry()
        
        # Simulate discovered plugins
        discovered_plugins = []
        for name in plugin_names:
            plugin = TestStructureGeneratorPlugin()
            plugin._metadata.name = name
            discovered_plugins.append(plugin)
        
        # Register discovered plugins
        for plugin in discovered_plugins:
            registry.register_plugin(plugin)
        
        # Verify all plugins are available
        all_plugins = registry.list_plugins()
        assert len(all_plugins) == len(plugin_names)
        
        # Verify each plugin can create components
        for plugin_name in plugin_names:
            component = registry.create_component(plugin_name)
            assert isinstance(component, StructureGenerator)
    
    def test_plugin_configuration_validation(self):
        """
        Test that plugin configuration validation works correctly.
        """
        # Create plugin with configuration schema
        plugin = TestStructureGeneratorPlugin()
        plugin._metadata.config_schema = {
            "type": "object",
            "properties": {
                "max_components": {"type": "integer", "minimum": 1},
                "strategy": {"type": "string", "enum": ["random", "systematic"]}
            },
            "required": ["max_components"]
        }
        
        # Valid configuration should work
        valid_config = {"max_components": 5, "strategy": "random"}
        plugin.config = valid_config
        assert plugin.validate_config(valid_config) == True
        
        # Invalid configuration should raise error (if jsonschema available)
        try:
            import jsonschema
            invalid_config = {"max_components": -1, "strategy": "invalid"}
            plugin.config = invalid_config
            with pytest.raises(ConfigurationError):
                plugin.validate_config(invalid_config)
        except ImportError:
            # Skip validation test if jsonschema not available
            pass
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=20)
    def test_plugin_manager_component_creation(self, num_plugins):
        """
        Test that plugin manager can create components correctly.
        """
        manager = PluginManager()
        
        # Register multiple plugins for the same component type
        for i in range(num_plugins):
            plugin = TestStructureGeneratorPlugin()
            plugin._metadata.name = f"test_plugin_{i}"
            manager.registry.register_plugin(plugin)
        
        # Create component using first available plugin
        component = manager.create_component("structure_generator")
        assert isinstance(component, StructureGenerator)
        
        # Create component using specific plugin
        specific_component = manager.create_component("structure_generator", "test_plugin_0")
        assert isinstance(specific_component, StructureGenerator)
    
    def test_plugin_metadata_serialization(self):
        """
        Test that plugin metadata can be serialized and deserialized correctly.
        """
        original_metadata = PluginMetadata(
            name="test_plugin",
            version="1.2.3",
            description="Test plugin for serialization",
            author="Test Author",
            component_type="structure_generator",
            dependencies=["dep1", "dep2"],
            config_schema={"type": "object", "properties": {"test": {"type": "string"}}}
        )
        
        # Serialize to dict
        metadata_dict = original_metadata.to_dict()
        
        # Deserialize from dict
        restored_metadata = PluginMetadata.from_dict(metadata_dict)
        
        # Verify all fields are preserved
        assert restored_metadata.name == original_metadata.name
        assert restored_metadata.version == original_metadata.version
        assert restored_metadata.description == original_metadata.description
        assert restored_metadata.author == original_metadata.author
        assert restored_metadata.component_type == original_metadata.component_type
        assert restored_metadata.dependencies == original_metadata.dependencies
        assert restored_metadata.config_schema == original_metadata.config_schema
    
    @given(st.lists(st.sampled_from(["structure_generator", "variable_assigner", "constraint_evaluator", "schema_validator"]), min_size=1, max_size=4, unique=True))
    @settings(max_examples=20)
    def test_component_type_filtering(self, component_types):
        """
        Test that plugins can be filtered by component type correctly.
        """
        registry = PluginRegistry()
        
        # Register plugins for each component type
        registered_by_type = {}
        for i, component_type in enumerate(component_types):
            if component_type == "structure_generator":
                plugin = TestStructureGeneratorPlugin()
            elif component_type == "variable_assigner":
                plugin = TestVariableAssignerPlugin()
            elif component_type == "constraint_evaluator":
                plugin = TestConstraintEvaluatorPlugin()
            else:  # schema_validator
                plugin = TestSchemaValidatorPlugin()
            
            plugin._metadata.name = f"test_{component_type}_{i}"
            registry.register_plugin(plugin)
            
            if component_type not in registered_by_type:
                registered_by_type[component_type] = []
            registered_by_type[component_type].append(plugin.metadata.name)
        
        # Verify filtering works for each component type
        for component_type in component_types:
            plugins = registry.get_plugins_by_type(component_type)
            plugin_names = [p.metadata.name for p in plugins]
            
            # Should contain all plugins of this type
            for expected_name in registered_by_type[component_type]:
                assert expected_name in plugin_names
            
            # Should not contain plugins of other types
            for other_type, other_names in registered_by_type.items():
                if other_type != component_type:
                    for other_name in other_names:
                        assert other_name not in plugin_names