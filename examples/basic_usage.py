#!/usr/bin/env python3
"""
Basic usage example for the SEP solver.

This example demonstrates the fundamental usage of the SEP solver with
a simple problem setup and exploration.
"""

import json
from sep_solver import SEPEngine
from sep_solver.core.config import SolverConfig
from sep_solver.models.constraint_set import ConstraintSet


def main():
    """Demonstrate basic SEP solver usage."""
    print("SEP Solver - Basic Usage Example")
    print("=" * 40)
    
    # Define a simple JSON schema for design objects
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "structure": {
                "type": "object",
                "properties": {
                    "components": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "properties": {"type": "object"}
                            },
                            "required": ["id", "type"]
                        }
                    },
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "from": {"type": "string"},
                                "to": {"type": "string"},
                                "type": {"type": "string"}
                            },
                            "required": ["id", "from", "to", "type"]
                        }
                    }
                },
                "required": ["components", "relationships"]
            },
            "variables": {
                "type": "object",
                "properties": {
                    "assignments": {"type": "object"}
                },
                "required": ["assignments"]
            }
        },
        "required": ["id", "structure", "variables"]
    }
    
    # Create constraint set (empty for this basic example)
    constraints = ConstraintSet()
    
    # Create solver configuration
    config = SolverConfig(
        exploration_strategy="breadth_first",
        max_iterations=50,
        max_solutions=5,
        enable_logging=True,
        log_level="INFO"
    )
    
    print(f"Configuration:")
    print(f"  Strategy: {config.exploration_strategy}")
    print(f"  Max iterations: {config.max_iterations}")
    print(f"  Max solutions: {config.max_solutions}")
    print()
    
    # Create SEP engine
    engine = SEPEngine(schema, constraints, config)
    
    # Add console progress reporter
    engine.create_console_progress_reporter(update_interval=2.0, show_details=True)
    
    print("Starting exploration...")
    
    try:
        # Run exploration
        solutions = engine.solve()
        
        print(f"\nExploration completed!")
        print(f"Found {len(solutions)} solutions")
        
        # Display solutions
        for i, solution in enumerate(solutions, 1):
            print(f"\nSolution {i}: {solution.id}")
            print(f"  Components: {len(solution.structure.components)}")
            print(f"  Relationships: {len(solution.structure.relationships)}")
            print(f"  Variables: {len(solution.variables.assignments)}")
        
        # Get exploration statistics
        stats = engine.get_solution_statistics()
        print(f"\nExploration Statistics:")
        print(f"  Total solutions: {stats['total_solutions']}")
        if stats['total_solutions'] > 0:
            print(f"  Average components: {stats['average_components']:.1f}")
            print(f"  Average relationships: {stats['average_relationships']:.1f}")
            print(f"  Average variables: {stats['average_variables']:.1f}")
        
        # Export solutions
        if solutions:
            print(f"\nExporting solutions...")
            engine.export_solutions("json", "basic_example_solutions.json")
            engine.generate_solution_report("basic_example_report.txt")
            print(f"Solutions exported to basic_example_solutions.json")
            print(f"Report generated: basic_example_report.txt")
    
    except Exception as e:
        print(f"Error during exploration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())