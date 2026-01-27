"""Configuration management for the SEP solver."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, Callable
import json
import os
import yaml
from pathlib import Path
from .exceptions import ConfigurationError


@dataclass
class SolverConfig:
    """Configuration settings for the SEP solver."""
    
    # Exploration settings
    exploration_strategy: str = "breadth_first"
    max_iterations: int = 1000
    max_solutions: int = 10
    timeout_seconds: Optional[float] = None
    
    # Generation settings
    structure_generation_strategy: str = "random"
    variable_assignment_strategy: str = "random"
    max_structure_size: int = 100
    max_variables_per_structure: int = 50
    
    # Validation settings
    enable_schema_validation: bool = True
    enable_constraint_validation: bool = True
    strict_validation: bool = True
    
    # Debugging and logging
    enable_logging: bool = True
    log_level: str = "INFO"
    log_exploration_steps: bool = False
    log_constraint_violations: bool = True
    enable_debug_tracing: bool = False
    
    # Plugin settings
    plugin_directories: List[str] = field(default_factory=list)
    enabled_plugins: List[str] = field(default_factory=list)
    
    # Performance settings
    parallel_evaluation: bool = False
    cache_evaluations: bool = True
    cache_size: int = 1000
    
    # Runtime modification settings
    allow_runtime_modification: bool = True
    modification_callbacks: Dict[str, List[Callable]] = field(default_factory=dict)
    
    # Custom settings (for extensions)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_file(cls, config_path: str) -> 'SolverConfig':
        """Load configuration from a file (JSON or YAML).
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            SolverConfig instance loaded from file
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        try:
            path = Path(config_path)
            if not path.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")
            
            with open(path, 'r') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    try:
                        config_data = yaml.safe_load(f)
                    except ImportError:
                        raise ConfigurationError("PyYAML is required for YAML configuration files")
                else:
                    config_data = json.load(f)
                
            return cls.from_dict(config_data)
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ConfigurationError(f"Invalid format in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration file: {e}")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SolverConfig':
        """Create configuration from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values
            
        Returns:
            SolverConfig instance
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Filter out unknown keys to avoid TypeError
            valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
            filtered_dict = {k: v for k, v in config_dict.items() if k in valid_keys}
            
            config = cls(**filtered_dict)
            config.validate()
            return config
            
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration parameters: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            "exploration_strategy": self.exploration_strategy,
            "max_iterations": self.max_iterations,
            "max_solutions": self.max_solutions,
            "timeout_seconds": self.timeout_seconds,
            "structure_generation_strategy": self.structure_generation_strategy,
            "variable_assignment_strategy": self.variable_assignment_strategy,
            "max_structure_size": self.max_structure_size,
            "max_variables_per_structure": self.max_variables_per_structure,
            "enable_schema_validation": self.enable_schema_validation,
            "enable_constraint_validation": self.enable_constraint_validation,
            "strict_validation": self.strict_validation,
            "enable_logging": self.enable_logging,
            "log_level": self.log_level,
            "log_exploration_steps": self.log_exploration_steps,
            "log_constraint_violations": self.log_constraint_violations,
            "enable_debug_tracing": self.enable_debug_tracing,
            "plugin_directories": self.plugin_directories,
            "enabled_plugins": self.enabled_plugins,
            "parallel_evaluation": self.parallel_evaluation,
            "cache_evaluations": self.cache_evaluations,
            "cache_size": self.cache_size,
            "allow_runtime_modification": self.allow_runtime_modification,
            "custom_settings": self.custom_settings
        }
    
    def save_to_file(self, config_path: str, format: str = "json") -> None:
        """Save configuration to a file.
        
        Args:
            config_path: Path where to save the configuration
            format: File format ("json" or "yaml")
            
        Raises:
            ConfigurationError: If file cannot be saved
        """
        try:
            path = Path(config_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = self.to_dict()
            
            with open(path, 'w') as f:
                if format.lower() == "yaml":
                    try:
                        yaml.dump(config_data, f, default_flow_style=False, indent=2)
                    except ImportError:
                        raise ConfigurationError("PyYAML is required for YAML format")
                else:
                    json.dump(config_data, f, indent=2)
                
        except Exception as e:
            raise ConfigurationError(f"Error saving configuration file: {e}")
    
    def validate(self) -> None:
        """Validate configuration settings.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Validate exploration strategy
        valid_strategies = ["breadth_first", "depth_first", "best_first", "random"]
        if self.exploration_strategy not in valid_strategies:
            raise ConfigurationError(f"Invalid exploration strategy: {self.exploration_strategy}. Must be one of {valid_strategies}")
        
        # Validate numeric limits
        if self.max_iterations <= 0:
            raise ConfigurationError("max_iterations must be positive")
        if self.max_solutions <= 0:
            raise ConfigurationError("max_solutions must be positive")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ConfigurationError("timeout_seconds must be positive")
        if self.max_structure_size <= 0:
            raise ConfigurationError("max_structure_size must be positive")
        if self.max_variables_per_structure <= 0:
            raise ConfigurationError("max_variables_per_structure must be positive")
        if self.cache_size <= 0:
            raise ConfigurationError("cache_size must be positive")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ConfigurationError(f"Invalid log level: {self.log_level}. Must be one of {valid_log_levels}")
        
        # Validate generation strategies
        valid_gen_strategies = ["random", "systematic", "heuristic"]
        if self.structure_generation_strategy not in valid_gen_strategies:
            raise ConfigurationError(f"Invalid structure generation strategy: {self.structure_generation_strategy}")
        if self.variable_assignment_strategy not in valid_gen_strategies:
            raise ConfigurationError(f"Invalid variable assignment strategy: {self.variable_assignment_strategy}")
    
    def update(self, **kwargs) -> 'SolverConfig':
        """Create a new configuration with updated values.
        
        Args:
            **kwargs: Configuration values to update
            
        Returns:
            New SolverConfig instance with updated values
        """
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return self.from_dict(current_dict)
    
    def modify_runtime(self, **kwargs) -> None:
        """Modify configuration at runtime.
        
        Args:
            **kwargs: Configuration values to modify
            
        Raises:
            ConfigurationError: If runtime modification is not allowed or values are invalid
        """
        if not self.allow_runtime_modification:
            raise ConfigurationError("Runtime configuration modification is disabled")
        
        # Store original values for rollback if validation fails
        original_values = {}
        
        try:
            # Apply changes and validate
            for key, value in kwargs.items():
                if hasattr(self, key):
                    original_values[key] = getattr(self, key)
                    setattr(self, key, value)
                else:
                    raise ConfigurationError(f"Unknown configuration parameter: {key}")
            
            # Validate the modified configuration
            self.validate()
            
            # Trigger callbacks for modified parameters
            for key, value in kwargs.items():
                self._trigger_modification_callbacks(key, value, original_values.get(key))
                
        except Exception as e:
            # Rollback changes on validation failure
            for key, original_value in original_values.items():
                setattr(self, key, original_value)
            raise ConfigurationError(f"Runtime modification failed: {e}")
    
    def add_modification_callback(self, parameter: str, callback: Callable[[str, Any, Any], None]) -> None:
        """Add a callback to be triggered when a parameter is modified.
        
        Args:
            parameter: Parameter name to watch
            callback: Callback function (parameter_name, new_value, old_value) -> None
        """
        if parameter not in self.modification_callbacks:
            self.modification_callbacks[parameter] = []
        self.modification_callbacks[parameter].append(callback)
    
    def remove_modification_callback(self, parameter: str, callback: Callable) -> None:
        """Remove a modification callback.
        
        Args:
            parameter: Parameter name
            callback: Callback function to remove
        """
        if parameter in self.modification_callbacks:
            try:
                self.modification_callbacks[parameter].remove(callback)
            except ValueError:
                pass  # Callback not found
    
    def _trigger_modification_callbacks(self, parameter: str, new_value: Any, old_value: Any) -> None:
        """Trigger callbacks for a modified parameter.
        
        Args:
            parameter: Parameter name
            new_value: New parameter value
            old_value: Previous parameter value
        """
        if parameter in self.modification_callbacks:
            for callback in self.modification_callbacks[parameter]:
                try:
                    callback(parameter, new_value, old_value)
                except Exception:
                    # Don't let callback errors break the modification
                    pass
    
    def get_custom_setting(self, key: str, default: Any = None) -> Any:
        """Get a custom setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        return self.custom_settings.get(key, default)
    
    def set_custom_setting(self, key: str, value: Any) -> None:
        """Set a custom setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.custom_settings[key] = value
    
    def get_exploration_parameters(self) -> Dict[str, Any]:
        """Get parameters specific to exploration behavior.
        
        Returns:
            Dictionary of exploration-related parameters
        """
        return {
            "exploration_strategy": self.exploration_strategy,
            "max_iterations": self.max_iterations,
            "max_solutions": self.max_solutions,
            "timeout_seconds": self.timeout_seconds,
            "structure_generation_strategy": self.structure_generation_strategy,
            "variable_assignment_strategy": self.variable_assignment_strategy,
            "max_structure_size": self.max_structure_size,
            "max_variables_per_structure": self.max_variables_per_structure
        }
    
    def apply_exploration_preset(self, preset: str) -> None:
        """Apply a predefined exploration preset.
        
        Args:
            preset: Preset name ("fast", "thorough", "balanced", "debug")
            
        Raises:
            ConfigurationError: If preset is unknown
        """
        presets = {
            "fast": {
                "exploration_strategy": "random",
                "max_iterations": 100,
                "max_solutions": 5,
                "enable_debug_tracing": False,
                "log_exploration_steps": False
            },
            "thorough": {
                "exploration_strategy": "breadth_first",
                "max_iterations": 5000,
                "max_solutions": 50,
                "enable_debug_tracing": True,
                "log_exploration_steps": True
            },
            "balanced": {
                "exploration_strategy": "best_first",
                "max_iterations": 1000,
                "max_solutions": 10,
                "enable_debug_tracing": False,
                "log_exploration_steps": False
            },
            "debug": {
                "exploration_strategy": "depth_first",
                "max_iterations": 50,
                "max_solutions": 3,
                "enable_debug_tracing": True,
                "log_exploration_steps": True,
                "log_constraint_violations": True,
                "log_level": "DEBUG"
            }
        }
        
        if preset not in presets:
            raise ConfigurationError(f"Unknown preset: {preset}. Available: {list(presets.keys())}")
        
        if self.allow_runtime_modification:
            self.modify_runtime(**presets[preset])
        else:
            # Apply directly if runtime modification is disabled
            for key, value in presets[preset].items():
                setattr(self, key, value)
            self.validate()


class ConfigurationManager:
    """Manages configuration loading, saving, and runtime modification."""
    
    def __init__(self, config: Optional[SolverConfig] = None):
        """Initialize configuration manager.
        
        Args:
            config: Initial configuration (defaults to default config)
        """
        self.config = config or SolverConfig()
        self.config_history: List[Dict[str, Any]] = []
        self.max_history_size = 10
    
    def load_from_file(self, config_path: str) -> None:
        """Load configuration from file.
        
        Args:
            config_path: Path to configuration file
        """
        self._save_to_history()
        self.config = SolverConfig.from_file(config_path)
    
    def load_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Load configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
        """
        self._save_to_history()
        self.config = SolverConfig.from_dict(config_dict)
    
    def save_to_file(self, config_path: str, format: str = "json") -> None:
        """Save current configuration to file.
        
        Args:
            config_path: Path to save configuration
            format: File format ("json" or "yaml")
        """
        self.config.save_to_file(config_path, format)
    
    def modify_config(self, **kwargs) -> None:
        """Modify configuration at runtime.
        
        Args:
            **kwargs: Configuration parameters to modify
        """
        self._save_to_history()
        self.config.modify_runtime(**kwargs)
    
    def apply_preset(self, preset: str) -> None:
        """Apply a configuration preset.
        
        Args:
            preset: Preset name
        """
        self._save_to_history()
        self.config.apply_exploration_preset(preset)
    
    def rollback_config(self, steps: int = 1) -> bool:
        """Rollback configuration to a previous state.
        
        Args:
            steps: Number of steps to rollback
            
        Returns:
            True if rollback was successful
        """
        if len(self.config_history) < steps:
            return False
        
        # Get the configuration from history
        target_config = self.config_history[-(steps)]
        
        # Remove the rolled-back configurations from history
        self.config_history = self.config_history[:-(steps)]
        
        # Apply the target configuration
        self.config = SolverConfig.from_dict(target_config)
        
        return True
    
    def get_config_diff(self, other_config: Union[SolverConfig, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Get differences between current config and another config.
        
        Args:
            other_config: Configuration to compare against
            
        Returns:
            Dictionary showing differences
        """
        if isinstance(other_config, SolverConfig):
            other_dict = other_config.to_dict()
        else:
            other_dict = other_config
        
        current_dict = self.config.to_dict()
        
        diff = {
            "added": {},
            "removed": {},
            "changed": {}
        }
        
        # Find added and changed keys
        for key, value in current_dict.items():
            if key not in other_dict:
                diff["added"][key] = value
            elif other_dict[key] != value:
                diff["changed"][key] = {
                    "old": other_dict[key],
                    "new": value
                }
        
        # Find removed keys
        for key, value in other_dict.items():
            if key not in current_dict:
                diff["removed"][key] = value
        
        return diff
    
    def _save_to_history(self) -> None:
        """Save current configuration to history."""
        self.config_history.append(self.config.to_dict())
        
        # Limit history size
        if len(self.config_history) > self.max_history_size:
            self.config_history = self.config_history[-self.max_history_size:]


def load_default_config() -> SolverConfig:
    """Load default configuration.
    
    Returns:
        Default SolverConfig instance
    """
    return SolverConfig()


def load_config_from_env() -> SolverConfig:
    """Load configuration from environment variables.
    
    Returns:
        SolverConfig instance with values from environment
    """
    config = SolverConfig()
    
    # Map environment variables to config attributes
    env_mappings = {
        "SEP_EXPLORATION_STRATEGY": "exploration_strategy",
        "SEP_MAX_ITERATIONS": ("max_iterations", int),
        "SEP_MAX_SOLUTIONS": ("max_solutions", int),
        "SEP_TIMEOUT_SECONDS": ("timeout_seconds", float),
        "SEP_LOG_LEVEL": "log_level",
        "SEP_ENABLE_LOGGING": ("enable_logging", lambda x: x.lower() == "true"),
        "SEP_ENABLE_DEBUG": ("enable_debug_tracing", lambda x: x.lower() == "true"),
    }
    
    for env_var, mapping in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            if isinstance(mapping, tuple):
                attr_name, converter = mapping
                try:
                    setattr(config, attr_name, converter(value))
                except (ValueError, TypeError):
                    # Skip invalid environment values
                    pass
            else:
                setattr(config, mapping, value)
    
    return config


def create_config_template(filename: str, format: str = "json") -> None:
    """Create a configuration template file.
    
    Args:
        filename: Template filename
        format: File format ("json" or "yaml")
    """
    template_config = SolverConfig()
    template_config.save_to_file(filename, format)