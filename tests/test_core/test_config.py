"""Tests for solver configuration."""

import pytest
import tempfile
import json
from pathlib import Path
from sep_solver.core.config import SolverConfig, load_default_config, load_config_from_env
from sep_solver.core.exceptions import ConfigurationError


class TestSolverConfig:
    """Test cases for SolverConfig class."""
    
    def test_default_config_creation(self):
        """Test creating a default configuration."""
        config = SolverConfig()
        
        assert config.exploration_strategy == "breadth_first"
        assert config.max_iterations == 1000
        assert config.max_solutions == 10
        assert config.enable_logging is True
        assert config.log_level == "INFO"
    
    def test_custom_config_creation(self):
        """Test creating a custom configuration."""
        config = SolverConfig(
            exploration_strategy="depth_first",
            max_iterations=500,
            enable_logging=False
        )
        
        assert config.exploration_strategy == "depth_first"
        assert config.max_iterations == 500
        assert config.enable_logging is False
        # Other values should be defaults
        assert config.max_solutions == 10
        assert config.log_level == "INFO"
    
    def test_config_validation_valid(self):
        """Test validation of valid configuration."""
        config = SolverConfig()
        # Should not raise any exception
        config.validate()
    
    def test_config_validation_invalid_strategy(self):
        """Test validation with invalid exploration strategy."""
        config = SolverConfig(exploration_strategy="invalid_strategy")
        
        with pytest.raises(ConfigurationError, match="Invalid exploration strategy"):
            config.validate()
    
    def test_config_validation_invalid_iterations(self):
        """Test validation with invalid max_iterations."""
        config = SolverConfig(max_iterations=0)
        
        with pytest.raises(ConfigurationError, match="max_iterations must be positive"):
            config.validate()
    
    def test_config_validation_invalid_log_level(self):
        """Test validation with invalid log level."""
        config = SolverConfig(log_level="INVALID")
        
        with pytest.raises(ConfigurationError, match="Invalid log level"):
            config.validate()
    
    def test_config_to_dict(self):
        """Test converting configuration to dictionary."""
        config = SolverConfig(exploration_strategy="depth_first", max_iterations=500)
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["exploration_strategy"] == "depth_first"
        assert config_dict["max_iterations"] == 500
        assert "enable_logging" in config_dict
    
    def test_config_from_dict(self):
        """Test creating configuration from dictionary."""
        config_dict = {
            "exploration_strategy": "depth_first",
            "max_iterations": 500,
            "enable_logging": False
        }
        
        config = SolverConfig.from_dict(config_dict)
        
        assert config.exploration_strategy == "depth_first"
        assert config.max_iterations == 500
        assert config.enable_logging is False
    
    def test_config_from_dict_invalid(self):
        """Test creating configuration from invalid dictionary."""
        config_dict = {
            "exploration_strategy": "invalid_strategy",
            "max_iterations": -1
        }
        
        with pytest.raises(ConfigurationError):
            SolverConfig.from_dict(config_dict)
    
    def test_config_file_save_load(self):
        """Test saving and loading configuration from file."""
        config = SolverConfig(exploration_strategy="depth_first", max_iterations=500)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            # Save configuration
            config.save_to_file(config_path)
            
            # Load configuration
            loaded_config = SolverConfig.from_file(config_path)
            
            assert loaded_config.exploration_strategy == config.exploration_strategy
            assert loaded_config.max_iterations == config.max_iterations
            
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_config_file_load_nonexistent(self):
        """Test loading configuration from non-existent file."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            SolverConfig.from_file("nonexistent_file.json")
    
    def test_config_update(self):
        """Test updating configuration values."""
        config = SolverConfig()
        updated_config = config.update(exploration_strategy="depth_first", max_iterations=500)
        
        # Original config should be unchanged
        assert config.exploration_strategy == "breadth_first"
        assert config.max_iterations == 1000
        
        # Updated config should have new values
        assert updated_config.exploration_strategy == "depth_first"
        assert updated_config.max_iterations == 500
    
    def test_custom_settings(self):
        """Test custom settings functionality."""
        config = SolverConfig()
        
        # Set custom setting
        config.set_custom_setting("my_setting", "my_value")
        assert config.get_custom_setting("my_setting") == "my_value"
        
        # Get non-existent setting with default
        assert config.get_custom_setting("nonexistent", "default") == "default"
        
        # Get non-existent setting without default
        assert config.get_custom_setting("nonexistent") is None


class TestConfigUtilities:
    """Test cases for configuration utility functions."""
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        config = load_default_config()
        
        assert isinstance(config, SolverConfig)
        assert config.exploration_strategy == "breadth_first"
        assert config.max_iterations == 1000
    
    def test_load_config_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        # Set environment variables
        monkeypatch.setenv("SEP_EXPLORATION_STRATEGY", "depth_first")
        monkeypatch.setenv("SEP_MAX_ITERATIONS", "500")
        monkeypatch.setenv("SEP_ENABLE_LOGGING", "false")
        
        config = load_config_from_env()
        
        assert config.exploration_strategy == "depth_first"
        assert config.max_iterations == 500
        assert config.enable_logging is False
    
    def test_load_config_from_env_invalid_values(self, monkeypatch):
        """Test loading configuration from environment with invalid values."""
        # Set invalid environment variables
        monkeypatch.setenv("SEP_MAX_ITERATIONS", "invalid")
        
        config = load_config_from_env()
        
        # Should use default value for invalid environment variable
        assert config.max_iterations == 1000  # Default value