"""Property-based tests for configuration system."""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, Any
import tempfile
import json
from pathlib import Path

from sep_solver.core.config import SolverConfig, ConfigurationManager, load_default_config
from sep_solver.core.exceptions import ConfigurationError
from sep_solver.core.engine import SEPEngine
from sep_solver.models.constraint_set import ConstraintSet


# Strategies for generating test data
@st.composite
def valid_exploration_strategy(draw):
    """Generate valid exploration strategies."""
    return draw(st.sampled_from(["breadth_first", "depth_first", "best_first", "random"]))


@st.composite
def valid_generation_strategy(draw):
    """Generate valid generation strategies."""
    return draw(st.sampled_from(["random", "systematic", "heuristic"]))


@st.composite
def valid_log_level(draw):
    """Generate valid log levels."""
    return draw(st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]))


@st.composite
def valid_config_values(draw):
    """Generate valid configuration values."""
    return {
        "exploration_strategy": draw(valid_exploration_strategy()),
        "max_iterations": draw(st.integers(min_value=1, max_value=10000)),
        "max_solutions": draw(st.integers(min_value=1, max_value=100)),
        "timeout_seconds": draw(st.one_of(st.none(), st.floats(min_value=0.1, max_value=3600.0))),
        "structure_generation_strategy": draw(valid_generation_strategy()),
        "variable_assignment_strategy": draw(valid_generation_strategy()),
        "max_structure_size": draw(st.integers(min_value=1, max_value=1000)),
        "max_variables_per_structure": draw(st.integers(min_value=1, max_value=100)),
        "enable_schema_validation": draw(st.booleans()),
        "enable_constraint_validation": draw(st.booleans()),
        "strict_validation": draw(st.booleans()),
        "enable_logging": draw(st.booleans()),
        "log_level": draw(valid_log_level()),
        "log_exploration_steps": draw(st.booleans()),
        "log_constraint_violations": draw(st.booleans()),
        "enable_debug_tracing": draw(st.booleans()),
        "parallel_evaluation": draw(st.booleans()),
        "cache_evaluations": draw(st.booleans()),
        "cache_size": draw(st.integers(min_value=1, max_value=10000)),
        "allow_runtime_modification": draw(st.booleans())
    }


@st.composite
def partial_config_values(draw):
    """Generate partial configuration values for runtime modification."""
    all_values = draw(valid_config_values())
    # Select a random subset of configuration values
    num_keys = draw(st.integers(min_value=1, max_value=min(5, len(all_values))))
    selected_keys = draw(st.lists(st.sampled_from(list(all_values.keys())), 
                                 min_size=num_keys, max_size=num_keys, unique=True))
    
    return {key: all_values[key] for key in selected_keys}


class TestConfigurationProperties:
    """Property-based tests for configuration functionality."""
    
    @given(valid_config_values())
    @settings(max_examples=50)
    def test_config_creation_and_validation(self, config_values):
        """
        **Property 10: Configuration Application**
        **Validates: Requirements 8.3**
        
        For any valid configuration parameters, creating a SolverConfig should
        succeed and the configuration should pass validation.
        """
        # Create configuration from values
        config = SolverConfig.from_dict(config_values)
        
        # Configuration should be valid
        config.validate()  # Should not raise exception
        
        # All specified values should be applied
        for key, expected_value in config_values.items():
            actual_value = getattr(config, key)
            assert actual_value == expected_value, f"Config value {key}: expected {expected_value}, got {actual_value}"
    
    @given(valid_config_values())
    @settings(max_examples=30)
    def test_config_serialization_roundtrip(self, config_values):
        """
        Test that configuration can be serialized and deserialized without loss.
        """
        # Create original configuration
        original_config = SolverConfig.from_dict(config_values)
        
        # Convert to dict and back
        config_dict = original_config.to_dict()
        restored_config = SolverConfig.from_dict(config_dict)
        
        # All values should be preserved
        for key, expected_value in config_values.items():
            original_value = getattr(original_config, key)
            restored_value = getattr(restored_config, key)
            assert original_value == restored_value, f"Serialization lost value for {key}"
    
    @given(valid_config_values())
    @settings(max_examples=20)
    def test_config_file_operations(self, config_values):
        """
        Test that configuration can be saved to and loaded from files.
        """
        original_config = SolverConfig.from_dict(config_values)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save to file
            original_config.save_to_file(temp_path, "json")
            
            # Load from file
            loaded_config = SolverConfig.from_file(temp_path)
            
            # Verify all values are preserved
            for key, expected_value in config_values.items():
                original_value = getattr(original_config, key)
                loaded_value = getattr(loaded_config, key)
                assert original_value == loaded_value, f"File operation lost value for {key}"
                
        finally:
            # Clean up
            Path(temp_path).unlink(missing_ok=True)
    
    @given(valid_config_values(), partial_config_values())
    @settings(max_examples=30)
    def test_runtime_configuration_modification(self, initial_values, modification_values):
        """
        Test that configuration can be modified at runtime when allowed.
        """
        # Ensure runtime modification is enabled
        initial_values["allow_runtime_modification"] = True
        
        # Create initial configuration
        config = SolverConfig.from_dict(initial_values)
        
        # Store original values for comparison
        original_values = {key: getattr(config, key) for key in modification_values.keys()}
        
        # Apply runtime modifications
        config.modify_runtime(**modification_values)
        
        # Verify modifications were applied
        for key, expected_value in modification_values.items():
            actual_value = getattr(config, key)
            assert actual_value == expected_value, f"Runtime modification failed for {key}"
        
        # Verify unmodified values remain unchanged
        for key, original_value in original_values.items():
            if key not in modification_values:
                current_value = getattr(config, key)
                assert current_value == original_value, f"Unmodified value changed for {key}"
    
    @given(valid_config_values())
    @settings(max_examples=20)
    def test_configuration_presets(self, base_values):
        """
        Test that configuration presets can be applied correctly.
        """
        config = SolverConfig.from_dict(base_values)
        
        presets = ["fast", "thorough", "balanced", "debug"]
        
        for preset in presets:
            # Apply preset
            config.apply_exploration_preset(preset)
            
            # Configuration should still be valid
            config.validate()
            
            # Preset-specific validations
            if preset == "fast":
                assert config.exploration_strategy == "random"
                assert config.max_iterations == 100
                assert config.max_solutions == 5
            elif preset == "thorough":
                assert config.exploration_strategy == "breadth_first"
                assert config.max_iterations == 5000
                assert config.max_solutions == 50
            elif preset == "balanced":
                assert config.exploration_strategy == "best_first"
                assert config.max_iterations == 1000
                assert config.max_solutions == 10
            elif preset == "debug":
                assert config.exploration_strategy == "depth_first"
                assert config.max_iterations == 50
                assert config.max_solutions == 3
                assert config.enable_debug_tracing == True
                assert config.log_level == "DEBUG"
    
    @given(valid_config_values())
    @settings(max_examples=20)
    def test_configuration_manager_functionality(self, config_values):
        """
        Test that ConfigurationManager correctly manages configuration changes.
        """
        manager = ConfigurationManager()
        
        # Load configuration
        manager.load_from_dict(config_values)
        
        # Verify configuration was loaded
        for key, expected_value in config_values.items():
            actual_value = getattr(manager.config, key)
            assert actual_value == expected_value
        
        # Test history functionality
        assert len(manager.config_history) == 1  # Initial config saved to history
        
        # Modify configuration
        if config_values.get("allow_runtime_modification", True):
            modification = {"max_iterations": 500, "max_solutions": 15}
            manager.modify_config(**modification)
            
            # Verify modification
            assert manager.config.max_iterations == 500
            assert manager.config.max_solutions == 15
            
            # History should have grown
            assert len(manager.config_history) == 2
            
            # Test rollback
            success = manager.rollback_config(1)
            assert success == True
            
            # Configuration should be restored
            assert manager.config.max_iterations == config_values["max_iterations"]
            assert manager.config.max_solutions == config_values["max_solutions"]
    
    @given(valid_config_values())
    @settings(max_examples=15, deadline=None)
    def test_engine_configuration_integration(self, config_values):
        """
        Test that SEP Engine correctly applies configuration changes.
        """
        # Create basic test setup
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        constraints = ConstraintSet()
        config = SolverConfig.from_dict(config_values)
        
        # Create engine with configuration
        engine = SEPEngine(schema, constraints, config)
        
        # Verify configuration was applied
        assert engine.config.exploration_strategy == config_values["exploration_strategy"]
        assert engine.config.max_iterations == config_values["max_iterations"]
        assert engine.config.max_solutions == config_values["max_solutions"]
        
        # Test runtime configuration update (if allowed)
        if config_values.get("allow_runtime_modification", True):
            new_strategy = "depth_first" if config_values["exploration_strategy"] != "depth_first" else "breadth_first"
            new_iterations = config_values["max_iterations"] + 100
            
            engine.update_configuration(
                exploration_strategy=new_strategy,
                max_iterations=new_iterations
            )
            
            # Verify updates were applied
            assert engine.config.exploration_strategy == new_strategy
            assert engine.config.max_iterations == new_iterations
    
    def test_invalid_configuration_values(self):
        """
        Test that invalid configuration values are properly rejected.
        """
        invalid_configs = [
            {"exploration_strategy": "invalid_strategy"},
            {"max_iterations": 0},
            {"max_iterations": -1},
            {"max_solutions": 0},
            {"timeout_seconds": -1.0},
            {"log_level": "INVALID_LEVEL"},
            {"structure_generation_strategy": "invalid"},
            {"cache_size": 0}
        ]
        
        for invalid_config in invalid_configs:
            with pytest.raises(ConfigurationError):
                config = SolverConfig.from_dict(invalid_config)
                config.validate()
    
    def test_runtime_modification_disabled(self):
        """
        Test that runtime modification can be disabled.
        """
        config = SolverConfig(allow_runtime_modification=False)
        
        with pytest.raises(ConfigurationError, match="Runtime configuration modification is disabled"):
            config.modify_runtime(max_iterations=500)
    
    @given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5))
    @settings(max_examples=20)
    def test_custom_settings(self, custom_keys):
        """
        Test that custom settings can be stored and retrieved.
        """
        config = SolverConfig()
        
        # Set custom settings
        custom_values = {}
        for i, key in enumerate(custom_keys):
            value = f"value_{i}"
            config.set_custom_setting(key, value)
            custom_values[key] = value
        
        # Verify custom settings
        for key, expected_value in custom_values.items():
            actual_value = config.get_custom_setting(key)
            assert actual_value == expected_value
        
        # Test default values
        assert config.get_custom_setting("nonexistent_key", "default") == "default"
    
    def test_configuration_callbacks(self):
        """
        Test that configuration modification callbacks work correctly.
        """
        config = SolverConfig()
        
        # Track callback invocations
        callback_calls = []
        
        def test_callback(param_name, new_value, old_value):
            callback_calls.append((param_name, new_value, old_value))
        
        # Add callback
        config.add_modification_callback("max_iterations", test_callback)
        
        # Modify configuration
        old_value = config.max_iterations
        new_value = 2000
        config.modify_runtime(max_iterations=new_value)
        
        # Verify callback was called
        assert len(callback_calls) == 1
        assert callback_calls[0] == ("max_iterations", new_value, old_value)
    
    @given(valid_config_values(), valid_config_values())
    @settings(max_examples=20)
    def test_configuration_diff(self, config1_values, config2_values):
        """
        Test that configuration differences can be computed correctly.
        """
        manager = ConfigurationManager()
        config1 = SolverConfig.from_dict(config1_values)
        config2 = SolverConfig.from_dict(config2_values)
        
        manager.config = config1
        diff = manager.get_config_diff(config2)
        
        # Verify diff structure
        assert "added" in diff
        assert "removed" in diff
        assert "changed" in diff
        
        # Check changed values
        for key in config1_values.keys():
            if key in config2_values:
                if config1_values[key] != config2_values[key]:
                    assert key in diff["changed"]
                    assert diff["changed"][key]["old"] == config2_values[key]
                    assert diff["changed"][key]["new"] == config1_values[key]