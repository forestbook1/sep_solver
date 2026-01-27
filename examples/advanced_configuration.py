#!/usr/bin/env python3
"""
Advanced configuration example for the SEP solver.

This example demonstrates advanced configuration features including:
- Runtime configuration modification
- Configuration presets
- Custom callbacks
- Plugin system usage
"""

import json
import time
from sep_solver import SEPEngine
from sep_solver.core.config import SolverConfig, ConfigurationManager
from sep_solver.models.constraint_set import ConstraintSet


def progress_callback(metrics):
    """Custom progress callback."""
    if metrics.current_iteration % 10 == 0:  # Report every 10 iterations
        print(f"Custom Progress: {metrics.current_iteration}/{metrics.total_iterations} "
              f"({metrics.get_progress_percentage():.1f}%) - "
              f"Solutions: {metrics.solutions_found}")


def solution_callback(solution_count, solution_id):
    """Custom solution found callback."""
    print(f"🎉 Custom Alert: Solution #{solution_count} found - {solution_id}")


def completion_callback(metrics, success):
    """Custom completion callback."""
    status = "SUCCESS" if success else "FAILED"
    print(f"🏁 Custom Alert: Exploration {status}")
    print(f"   Final stats: {metrics.solutions_found} solutions in {metrics.current_iteration} iterations")


def config_change_callback(param_name, new_value, old_value):
    """Configuration change callback."""
    print(f"⚙️  Configuration changed: {param_name} = {new_value} (was {old_value})")


def main():
    """Demonstrate advanced configuration features."""
    print("SEP Solver - Advanced Configuration Example")
    print("=" * 50)
    
    # Create configuration manager
    config_manager = ConfigurationManager()
    
    # Load initial configuration
    initial_config = {
        "exploration_strategy": "random",
        "max_iterations": 100,
        "max_solutions": 3,
        "enable_logging": True,
        "log_level": "INFO",
        "enable_debug_tracing": False,
        "allow_runtime_modification": True
    }
    
    config_manager.load_from_dict(initial_config)
    print("Initial configuration loaded")
    
    # Define schema and constraints
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "structure": {"type": "object"},
            "variables": {"type": "object"}
        },
        "required": ["id", "structure", "variables"]
    }
    
    constraints = ConstraintSet()
    
    # Create engine with initial configuration
    engine = SEPEngine(schema, constraints, config_manager.config)
    
    # Add configuration change callback
    engine.add_configuration_callback("exploration_strategy", config_change_callback)
    engine.add_configuration_callback("max_iterations", config_change_callback)
    
    # Add custom progress reporters
    engine.create_callback_progress_reporter(
        progress_callback=progress_callback,
        solution_callback=solution_callback,
        completion_callback=completion_callback
    )
    
    # Also add console reporter for standard output
    engine.create_console_progress_reporter(update_interval=5.0, show_details=False)
    
    # Add file reporter for logging
    engine.create_file_progress_reporter("advanced_example_progress.json", "json")
    
    print("\n1. Running with initial configuration (random strategy)...")
    print(f"   Strategy: {engine.config.exploration_strategy}")
    print(f"   Max iterations: {engine.config.max_iterations}")
    
    # Run first exploration
    solutions_1 = engine.solve()
    print(f"   Results: {len(solutions_1)} solutions found")
    
    # Demonstrate runtime configuration modification
    print("\n2. Modifying configuration at runtime...")
    engine.update_configuration(
        exploration_strategy="breadth_first",
        max_iterations=150,
        enable_debug_tracing=True
    )
    
    # Reset engine state for new exploration
    engine.reset()
    
    print(f"   New strategy: {engine.config.exploration_strategy}")
    print(f"   New max iterations: {engine.config.max_iterations}")
    
    # Run second exploration
    solutions_2 = engine.solve()
    print(f"   Results: {len(solutions_2)} solutions found")
    
    # Demonstrate configuration presets
    print("\n3. Applying configuration presets...")
    
    presets = ["fast", "thorough", "balanced", "debug"]
    
    for preset in presets:
        print(f"\n   Applying '{preset}' preset...")
        engine.apply_configuration_preset(preset)
        
        print(f"     Strategy: {engine.config.exploration_strategy}")
        print(f"     Max iterations: {engine.config.max_iterations}")
        print(f"     Max solutions: {engine.config.max_solutions}")
        print(f"     Debug tracing: {engine.config.enable_debug_tracing}")
        
        # Run quick exploration with preset
        engine.reset()
        preset_solutions = engine.solve()
        print(f"     Results: {len(preset_solutions)} solutions")
    
    # Demonstrate configuration file operations
    print("\n4. Configuration file operations...")
    
    # Save current configuration
    config_filename = "advanced_example_config.json"
    engine.save_configuration(config_filename, "json")
    print(f"   Configuration saved to {config_filename}")
    
    # Load configuration from file
    loaded_config = SolverConfig.from_file(config_filename)
    print(f"   Configuration loaded from file")
    print(f"     Strategy: {loaded_config.exploration_strategy}")
    print(f"     Max iterations: {loaded_config.max_iterations}")
    
    # Demonstrate configuration comparison
    print("\n5. Configuration comparison...")
    
    # Create a different configuration
    different_config = SolverConfig(
        exploration_strategy="depth_first",
        max_iterations=200,
        max_solutions=8
    )
    
    # Compare configurations
    config_manager.config = engine.config
    diff = config_manager.get_config_diff(different_config)
    
    print("   Configuration differences:")
    if diff["changed"]:
        for param, changes in diff["changed"].items():
            print(f"     {param}: {changes['new']} -> {changes['old']}")
    
    # Demonstrate configuration history and rollback
    print("\n6. Configuration history and rollback...")
    
    # Make several configuration changes
    config_manager.modify_config(exploration_strategy="random", max_iterations=75)
    config_manager.modify_config(max_solutions=12)
    config_manager.modify_config(enable_debug_tracing=True)
    
    print(f"   Current config: strategy={config_manager.config.exploration_strategy}, "
          f"iterations={config_manager.config.max_iterations}, "
          f"solutions={config_manager.config.max_solutions}")
    
    # Rollback 2 steps
    success = config_manager.rollback_config(2)
    if success:
        print(f"   After rollback: strategy={config_manager.config.exploration_strategy}, "
              f"iterations={config_manager.config.max_iterations}, "
              f"solutions={config_manager.config.max_solutions}")
    
    # Demonstrate plugin system (basic)
    print("\n7. Plugin system demonstration...")
    
    try:
        # List available plugins
        plugins = engine.list_available_plugins()
        print(f"   Available plugins: {len(plugins)}")
        
        for plugin in plugins[:3]:  # Show first 3 plugins
            print(f"     - {plugin['name']} ({plugin['component_type']}): {plugin['description']}")
        
        # Get plugin info
        if plugins:
            plugin_info = engine.get_plugin_info(plugins[0]['name'])
            if plugin_info:
                print(f"   Plugin details: {plugin_info['name']} v{plugin_info['version']}")
    
    except Exception as e:
        print(f"   Plugin system error: {e}")
    
    # Final summary
    print("\n" + "=" * 50)
    print("Advanced Configuration Example Complete")
    print(f"Total solutions found across all runs: {len(solutions_1) + len(solutions_2)}")
    print("Files created:")
    print(f"  - {config_filename}")
    print(f"  - advanced_example_progress.json")
    
    return 0


if __name__ == "__main__":
    exit(main())