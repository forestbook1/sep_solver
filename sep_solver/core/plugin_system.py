"""Plugin system for the SEP solver."""

import importlib
import inspect
from typing import Dict, Any, List, Type, Optional, Callable
from pathlib import Path
import json
from abc import ABC, abstractmethod
from .interfaces import StructureGenerator, VariableAssigner, ConstraintEvaluator, SchemaValidator
from .exceptions import SEPSolverError, ConfigurationError


class PluginMetadata:
    """Metadata for a plugin."""
    
    def __init__(self, name: str, version: str, description: str, 
                 author: str = "", component_type: str = "", 
                 dependencies: List[str] = None, config_schema: Dict[str, Any] = None):
        """Initialize plugin metadata.
        
        Args:
            name: Plugin name
            version: Plugin version
            description: Plugin description
            author: Plugin author
            component_type: Type of component this plugin provides
            dependencies: List of required dependencies
            config_schema: JSON schema for plugin configuration
        """
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.component_type = component_type
        self.dependencies = dependencies or []
        self.config_schema = config_schema or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "component_type": self.component_type,
            "dependencies": self.dependencies,
            "config_schema": self.config_schema
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create from dictionary."""
        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data.get("author", ""),
            component_type=data.get("component_type", ""),
            dependencies=data.get("dependencies", []),
            config_schema=data.get("config_schema", {})
        )


class Plugin(ABC):
    """Base class for all SEP solver plugins."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        self.config = config or {}
        self._metadata = None
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        pass
    
    @abstractmethod
    def create_component(self) -> Any:
        """Create the component instance provided by this plugin.
        
        Returns:
            Component instance
        """
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Basic validation - can be overridden by plugins
        if self.metadata.config_schema:
            try:
                import jsonschema
                jsonschema.validate(config, self.metadata.config_schema)
            except ImportError:
                # If jsonschema not available, skip validation
                pass
            except Exception as e:
                raise ConfigurationError(f"Plugin configuration validation failed: {e}")
        
        return True
    
    def initialize(self) -> None:
        """Initialize the plugin. Called after configuration validation."""
        pass
    
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass


class PluginRegistry:
    """Registry for managing SEP solver plugins."""
    
    def __init__(self):
        """Initialize plugin registry."""
        self.plugins: Dict[str, Plugin] = {}
        self.component_plugins: Dict[str, List[str]] = {
            "structure_generator": [],
            "variable_assigner": [],
            "constraint_evaluator": [],
            "schema_validator": []
        }
        self.plugin_paths: List[Path] = []
    
    def add_plugin_path(self, path: Path) -> None:
        """Add a path to search for plugins.
        
        Args:
            path: Path to plugin directory
        """
        if path not in self.plugin_paths:
            self.plugin_paths.append(path)
    
    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin.
        
        Args:
            plugin: Plugin instance to register
            
        Raises:
            ConfigurationError: If plugin registration fails
        """
        metadata = plugin.metadata
        
        # Validate plugin
        if not metadata.name:
            raise ConfigurationError("Plugin must have a name")
        
        if not metadata.component_type:
            raise ConfigurationError("Plugin must specify component_type")
        
        if metadata.component_type not in self.component_plugins:
            raise ConfigurationError(f"Unknown component type: {metadata.component_type}")
        
        # Check for name conflicts
        if metadata.name in self.plugins:
            existing_version = self.plugins[metadata.name].metadata.version
            if existing_version != metadata.version:
                raise ConfigurationError(f"Plugin {metadata.name} already registered with different version ({existing_version} vs {metadata.version})")
        
        # Validate configuration
        plugin.validate_config(plugin.config)
        
        # Initialize plugin
        plugin.initialize()
        
        # Register plugin
        self.plugins[metadata.name] = plugin
        self.component_plugins[metadata.component_type].append(metadata.name)
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """Unregister a plugin.
        
        Args:
            plugin_name: Name of plugin to unregister
        """
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            
            # Cleanup plugin
            plugin.cleanup()
            
            # Remove from registry
            component_type = plugin.metadata.component_type
            if plugin_name in self.component_plugins[component_type]:
                self.component_plugins[component_type].remove(plugin_name)
            
            del self.plugins[plugin_name]
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a plugin by name.
        
        Args:
            plugin_name: Name of plugin to get
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, component_type: str) -> List[Plugin]:
        """Get all plugins for a component type.
        
        Args:
            component_type: Component type to search for
            
        Returns:
            List of plugins for the component type
        """
        if component_type not in self.component_plugins:
            return []
        
        return [self.plugins[name] for name in self.component_plugins[component_type]]
    
    def list_plugins(self) -> List[PluginMetadata]:
        """List all registered plugins.
        
        Returns:
            List of plugin metadata
        """
        return [plugin.metadata for plugin in self.plugins.values()]
    
    def create_component(self, plugin_name: str, config: Dict[str, Any] = None) -> Any:
        """Create a component using a plugin.
        
        Args:
            plugin_name: Name of plugin to use
            config: Optional configuration for the component
            
        Returns:
            Component instance
            
        Raises:
            ConfigurationError: If plugin not found or creation fails
        """
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            raise ConfigurationError(f"Plugin not found: {plugin_name}")
        
        # Update plugin config if provided
        if config:
            plugin.config.update(config)
            plugin.validate_config(plugin.config)
        
        try:
            return plugin.create_component()
        except Exception as e:
            raise ConfigurationError(f"Failed to create component from plugin {plugin_name}: {e}")
    
    def discover_plugins(self, plugin_dir: Path = None) -> List[str]:
        """Discover and load plugins from directories.
        
        Args:
            plugin_dir: Optional specific directory to search
            
        Returns:
            List of discovered plugin names
        """
        discovered = []
        search_paths = [plugin_dir] if plugin_dir else self.plugin_paths
        
        for path in search_paths:
            if not path.exists():
                continue
            
            # Look for Python files
            for py_file in path.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                
                try:
                    plugin_names = self._load_plugin_file(py_file)
                    discovered.extend(plugin_names)
                except Exception as e:
                    # Log error but continue discovery
                    print(f"Warning: Failed to load plugin from {py_file}: {e}")
            
            # Look for plugin packages
            for pkg_dir in path.iterdir():
                if pkg_dir.is_dir() and (pkg_dir / "__init__.py").exists():
                    try:
                        plugin_names = self._load_plugin_package(pkg_dir)
                        discovered.extend(plugin_names)
                    except Exception as e:
                        print(f"Warning: Failed to load plugin package from {pkg_dir}: {e}")
        
        return discovered
    
    def _load_plugin_file(self, plugin_file: Path) -> List[str]:
        """Load plugins from a Python file.
        
        Args:
            plugin_file: Path to plugin file
            
        Returns:
            List of loaded plugin names
        """
        # Import the module
        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin classes
        plugin_names = []
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, Plugin) and 
                obj != Plugin):
                
                # Create plugin instance
                plugin = obj()
                self.register_plugin(plugin)
                plugin_names.append(plugin.metadata.name)
        
        return plugin_names
    
    def _load_plugin_package(self, plugin_dir: Path) -> List[str]:
        """Load plugins from a package directory.
        
        Args:
            plugin_dir: Path to plugin package directory
            
        Returns:
            List of loaded plugin names
        """
        # Import the package
        spec = importlib.util.spec_from_file_location(plugin_dir.name, plugin_dir / "__init__.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for plugin registration function
        plugin_names = []
        if hasattr(module, 'register_plugins'):
            plugins = module.register_plugins()
            for plugin in plugins:
                self.register_plugin(plugin)
                plugin_names.append(plugin.metadata.name)
        
        return plugin_names
    
    def export_plugin_info(self, filename: str) -> None:
        """Export plugin information to file.
        
        Args:
            filename: Output filename
        """
        plugin_info = {
            "plugins": [plugin.metadata.to_dict() for plugin in self.plugins.values()],
            "component_types": {
                comp_type: plugin_names 
                for comp_type, plugin_names in self.component_plugins.items()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(plugin_info, f, indent=2)


class PluginManager:
    """High-level plugin manager for the SEP solver."""
    
    def __init__(self):
        """Initialize plugin manager."""
        self.registry = PluginRegistry()
        self._default_plugins_registered = False
    
    def register_default_plugins(self) -> None:
        """Register default built-in plugins."""
        if self._default_plugins_registered:
            return
        
        # Register built-in structure generator plugin
        self.registry.register_plugin(BuiltinStructureGeneratorPlugin())
        
        # Register built-in variable assigner plugin
        self.registry.register_plugin(BuiltinVariableAssignerPlugin())
        
        # Register built-in constraint evaluator plugin
        self.registry.register_plugin(BuiltinConstraintEvaluatorPlugin())
        
        # Register built-in schema validator plugin
        self.registry.register_plugin(BuiltinSchemaValidatorPlugin())
        
        self._default_plugins_registered = True
    
    def discover_and_load_plugins(self, plugin_dirs: List[Path] = None) -> List[str]:
        """Discover and load plugins from directories.
        
        Args:
            plugin_dirs: List of directories to search for plugins
            
        Returns:
            List of discovered plugin names
        """
        if plugin_dirs:
            for plugin_dir in plugin_dirs:
                self.registry.add_plugin_path(plugin_dir)
        
        return self.registry.discover_plugins()
    
    def create_component(self, component_type: str, plugin_name: str = None, 
                        config: Dict[str, Any] = None) -> Any:
        """Create a component using plugins.
        
        Args:
            component_type: Type of component to create
            plugin_name: Optional specific plugin to use
            config: Optional configuration
            
        Returns:
            Component instance
            
        Raises:
            ConfigurationError: If component creation fails
        """
        # Ensure default plugins are registered
        self.register_default_plugins()
        
        if plugin_name:
            # Use specific plugin
            return self.registry.create_component(plugin_name, config)
        else:
            # Use first available plugin for the component type
            plugins = self.registry.get_plugins_by_type(component_type)
            if not plugins:
                raise ConfigurationError(f"No plugins available for component type: {component_type}")
            
            # Use the first plugin
            return self.registry.create_component(plugins[0].metadata.name, config)
    
    def list_available_plugins(self, component_type: str = None) -> List[PluginMetadata]:
        """List available plugins.
        
        Args:
            component_type: Optional filter by component type
            
        Returns:
            List of plugin metadata
        """
        self.register_default_plugins()
        
        if component_type:
            plugins = self.registry.get_plugins_by_type(component_type)
            return [plugin.metadata for plugin in plugins]
        else:
            return self.registry.list_plugins()
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginMetadata]:
        """Get information about a specific plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Plugin metadata or None if not found
        """
        plugin = self.registry.get_plugin(plugin_name)
        return plugin.metadata if plugin else None


# Built-in plugins for default components
class BuiltinStructureGeneratorPlugin(Plugin):
    """Built-in plugin for structure generator."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="builtin_structure_generator",
            version="1.0.0",
            description="Built-in structure generator",
            author="SEP Solver",
            component_type="structure_generator"
        )
    
    def create_component(self) -> StructureGenerator:
        from ..generators.structure_generator import BaseStructureGenerator
        return BaseStructureGenerator()


class BuiltinVariableAssignerPlugin(Plugin):
    """Built-in plugin for variable assigner."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="builtin_variable_assigner",
            version="1.0.0",
            description="Built-in variable assigner",
            author="SEP Solver",
            component_type="variable_assigner"
        )
    
    def create_component(self) -> VariableAssigner:
        from ..generators.variable_assigner import BaseVariableAssigner
        return BaseVariableAssigner()


class BuiltinConstraintEvaluatorPlugin(Plugin):
    """Built-in plugin for constraint evaluator."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="builtin_constraint_evaluator",
            version="1.0.0",
            description="Built-in constraint evaluator",
            author="SEP Solver",
            component_type="constraint_evaluator"
        )
    
    def create_component(self) -> ConstraintEvaluator:
        from ..evaluators.constraint_evaluator import BaseConstraintEvaluator
        # Note: This would need constraints passed in real usage
        return BaseConstraintEvaluator(None)


class BuiltinSchemaValidatorPlugin(Plugin):
    """Built-in plugin for schema validator."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="builtin_schema_validator",
            version="1.0.0",
            description="Built-in JSON schema validator",
            author="SEP Solver",
            component_type="schema_validator"
        )
    
    def create_component(self) -> SchemaValidator:
        from ..evaluators.schema_validator import JSONSchemaValidator
        # Note: This would need schema passed in real usage
        return JSONSchemaValidator({})


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def register_plugin(plugin: Plugin) -> None:
    """Register a plugin with the global plugin manager."""
    manager = get_plugin_manager()
    manager.registry.register_plugin(plugin)


def create_component(component_type: str, plugin_name: str = None, 
                    config: Dict[str, Any] = None) -> Any:
    """Create a component using the global plugin manager."""
    manager = get_plugin_manager()
    return manager.create_component(component_type, plugin_name, config)


def list_plugins(component_type: str = None) -> List[PluginMetadata]:
    """List available plugins using the global plugin manager."""
    manager = get_plugin_manager()
    return manager.list_available_plugins(component_type)