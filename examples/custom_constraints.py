#!/usr/bin/env python3
"""
Custom constraints example for the SEP solver.

This example demonstrates how to create and use custom constraints
to guide the exploration process toward specific design requirements.
"""

from typing import List, Dict, Any
from sep_solver import SEPEngine
from sep_solver.core.config import SolverConfig
from sep_solver.models.constraint_set import ConstraintSet, StructuralConstraint, VariableConstraint
from sep_solver.models.design_object import DesignObject


class MinimumComponentsConstraint(StructuralConstraint):
    """Constraint requiring a minimum number of components."""
    
    def __init__(self, min_components: int):
        """Initialize constraint.
        
        Args:
            min_components: Minimum number of components required
        """
        super().__init__(
            constraint_id=f"min_components_{min_components}",
            description=f"Requires at least {min_components} components"
        )
        self.min_components = min_components
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        """Check if the constraint is satisfied."""
        actual_components = len(design_object.structure.components)
        return actual_components >= self.min_components
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        """Get violation message."""
        actual_components = len(design_object.structure.components)
        return f"Design has {actual_components} components, but requires at least {self.min_components}"


class MaximumComponentsConstraint(StructuralConstraint):
    """Constraint limiting the maximum number of components."""
    
    def __init__(self, max_components: int):
        """Initialize constraint.
        
        Args:
            max_components: Maximum number of components allowed
        """
        super().__init__(
            constraint_id=f"max_components_{max_components}",
            description=f"Allows at most {max_components} components"
        )
        self.max_components = max_components
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        """Check if the constraint is satisfied."""
        actual_components = len(design_object.structure.components)
        return actual_components <= self.max_components
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        """Get violation message."""
        actual_components = len(design_object.structure.components)
        return f"Design has {actual_components} components, but allows at most {self.max_components}"


class RequiredComponentTypeConstraint(StructuralConstraint):
    """Constraint requiring specific component types."""
    
    def __init__(self, required_types: List[str]):
        """Initialize constraint.
        
        Args:
            required_types: List of component types that must be present
        """
        super().__init__(
            constraint_id=f"required_types_{'_'.join(required_types)}",
            description=f"Requires component types: {', '.join(required_types)}"
        )
        self.required_types = set(required_types)
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        """Check if the constraint is satisfied."""
        # Get all component types in the design
        present_types = set()
        for component in design_object.structure.components:
            present_types.add(component.type)
        
        # Check if all required types are present
        return self.required_types.issubset(present_types)
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        """Get violation message."""
        # Get all component types in the design
        present_types = set()
        for component in design_object.structure.components:
            present_types.add(component.type)
        
        # Check for missing required types
        missing_types = self.required_types - present_types
        return f"Design is missing required component types: {', '.join(missing_types)}"


class VariableRangeConstraint(VariableConstraint):
    """Constraint requiring variables to be within specific ranges."""
    
    def __init__(self, variable_ranges: Dict[str, tuple]):
        """Initialize constraint.
        
        Args:
            variable_ranges: Dictionary mapping variable names to (min, max) tuples
        """
        super().__init__(
            constraint_id=f"variable_ranges_{len(variable_ranges)}",
            description=f"Enforces ranges for {len(variable_ranges)} variables"
        )
        self.variable_ranges = variable_ranges
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        """Check if the constraint is satisfied."""
        for var_name, (min_val, max_val) in self.variable_ranges.items():
            if var_name in design_object.variables.assignments:
                value = design_object.variables.assignments[var_name]
                
                try:
                    # Convert to numeric for comparison
                    numeric_value = float(value)
                    
                    if numeric_value < min_val or numeric_value > max_val:
                        return False
                        
                except (ValueError, TypeError):
                    # Non-numeric value is considered a violation
                    return False
        
        return True
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        """Get violation message."""
        violations = []
        
        for var_name, (min_val, max_val) in self.variable_ranges.items():
            if var_name in design_object.variables.assignments:
                value = design_object.variables.assignments[var_name]
                
                try:
                    # Convert to numeric for comparison
                    numeric_value = float(value)
                    
                    if numeric_value < min_val or numeric_value > max_val:
                        violations.append(f"Variable '{var_name}' value {numeric_value} is outside range [{min_val}, {max_val}]")
                        
                except (ValueError, TypeError):
                    # Non-numeric value
                    violations.append(f"Variable '{var_name}' has non-numeric value: {value}")
        
        return "; ".join(violations) if violations else "Variable range constraint violated"


class ConnectivityConstraint(StructuralConstraint):
    """Constraint requiring all components to be connected."""
    
    def __init__(self):
        """Initialize constraint."""
        super().__init__(
            constraint_id="connectivity_required",
            description="Requires all components to be connected through relationships"
        )
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        """Check if the constraint is satisfied."""
        components = design_object.structure.components
        relationships = design_object.structure.relationships
        
        if len(components) <= 1:
            # Single component or empty structure is trivially connected
            return True
        
        # Build adjacency list
        adjacency = {comp.id: set() for comp in components}
        
        for rel in relationships:
            if rel.source_id in adjacency and rel.target_id in adjacency:
                adjacency[rel.source_id].add(rel.target_id)
                adjacency[rel.target_id].add(rel.source_id)  # Treat as undirected
        
        # Check connectivity using DFS
        if components:
            visited = set()
            start_component = components[0].id
            
            def dfs(component_id):
                if component_id in visited:
                    return
                visited.add(component_id)
                for neighbor in adjacency[component_id]:
                    dfs(neighbor)
            
            dfs(start_component)
            
            # Check if all components were visited
            all_component_ids = {comp.id for comp in components}
            return len(visited) == len(all_component_ids)
        
        return True
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        """Get violation message."""
        components = design_object.structure.components
        relationships = design_object.structure.relationships
        
        if len(components) <= 1:
            return "Connectivity constraint satisfied"
        
        # Build adjacency list
        adjacency = {comp.id: set() for comp in components}
        
        for rel in relationships:
            if rel.source_id in adjacency and rel.target_id in adjacency:
                adjacency[rel.source_id].add(rel.target_id)
                adjacency[rel.target_id].add(rel.source_id)  # Treat as undirected
        
        # Check connectivity using DFS
        if components:
            visited = set()
            start_component = components[0].id
            
            def dfs(component_id):
                if component_id in visited:
                    return
                visited.add(component_id)
                for neighbor in adjacency[component_id]:
                    dfs(neighbor)
            
            dfs(start_component)
            
            # Check if all components were visited
            all_component_ids = {comp.id for comp in components}
            unconnected = all_component_ids - visited
            
            if unconnected:
                return f"Components are not fully connected. Isolated components: {', '.join(unconnected)}"
        
        return "Connectivity constraint satisfied"


def create_example_constraints() -> ConstraintSet:
    """Create a set of example constraints."""
    constraints = ConstraintSet()
    
    # Add structural constraints
    constraints.add_constraint(MinimumComponentsConstraint(2))
    constraints.add_constraint(MaximumComponentsConstraint(6))
    constraints.add_constraint(RequiredComponentTypeConstraint(["processor", "memory"]))
    constraints.add_constraint(ConnectivityConstraint())
    
    # Add variable constraints
    variable_ranges = {
        "cpu_speed": (1.0, 5.0),  # GHz
        "memory_size": (4, 64),   # GB
        "power_consumption": (10, 200)  # Watts
    }
    constraints.add_constraint(VariableRangeConstraint(variable_ranges))
    
    return constraints


def main():
    """Demonstrate custom constraints usage."""
    print("SEP Solver - Custom Constraints Example")
    print("=" * 45)
    
    # Define schema
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
    
    # Create custom constraints
    constraints = create_example_constraints()
    
    print("Custom constraints created:")
    for constraint in constraints.get_all_constraints():
        print(f"  - {constraint.constraint_id}: {constraint.description}")
    
    # Create configuration
    config = SolverConfig(
        exploration_strategy="best_first",
        max_iterations=200,
        max_solutions=5,
        enable_logging=True,
        log_level="INFO",
        log_constraint_violations=True
    )
    
    print(f"\nConfiguration:")
    print(f"  Strategy: {config.exploration_strategy}")
    print(f"  Max iterations: {config.max_iterations}")
    print(f"  Max solutions: {config.max_solutions}")
    
    # Create engine
    engine = SEPEngine(schema, constraints, config)
    
    # Add progress reporting
    engine.create_console_progress_reporter(update_interval=3.0, show_details=True)
    
    # Custom callback to report constraint violations
    def solution_found_callback(solution_count, solution_id):
        print(f"\n🎯 Solution {solution_count} found: {solution_id}")
        
        # Get the solution and show its characteristics
        solutions = engine.get_solutions()
        if solutions:
            solution = solutions[-1]  # Get the latest solution
            print(f"   Components: {len(solution.structure.components)}")
            print(f"   Relationships: {len(solution.structure.relationships)}")
            print(f"   Variables: {len(solution.variables.assignments)}")
            
            # Show component types
            component_types = [comp.type for comp in solution.structure.components]
            print(f"   Component types: {', '.join(set(component_types))}")
    
    engine.create_callback_progress_reporter(solution_callback=solution_found_callback)
    
    print(f"\nStarting exploration with custom constraints...")
    print("=" * 45)
    
    try:
        # Run exploration
        solutions = engine.solve()
        
        print(f"\n" + "=" * 45)
        print(f"Exploration completed!")
        print(f"Found {len(solutions)} solutions that satisfy all constraints")
        
        # Analyze solutions
        if solutions:
            print(f"\nSolution Analysis:")
            print("-" * 20)
            
            for i, solution in enumerate(solutions, 1):
                print(f"\nSolution {i}: {solution.id}")
                print(f"  Components ({len(solution.structure.components)}):")
                
                for comp in solution.structure.components:
                    print(f"    - {comp.id} ({comp.type})")
                
                print(f"  Relationships ({len(solution.structure.relationships)}):")
                for rel in solution.structure.relationships:
                    print(f"    - {rel.source_id} -> {rel.target_id} ({rel.type})")
                
                print(f"  Variables ({len(solution.variables.assignments)}):")
                for var_name, var_value in solution.variables.assignments.items():
                    print(f"    - {var_name} = {var_value}")
        
        # Get constraint violation statistics
        inspection = engine.inspect_constraint_violations()
        print(f"\nConstraint Violation Statistics:")
        print(f"  Total violations encountered: {inspection['total_violations']}")
        print(f"  Unique constraints violated: {inspection['unique_constraints_violated']}")
        print(f"  Violation rate: {inspection['violation_rate']:.1%}")
        
        if inspection['most_violated']:
            print(f"  Most violated constraints:")
            for constraint_id, count in inspection['most_violated'][:3]:
                print(f"    - {constraint_id}: {count} violations")
        
        # Export results
        if solutions:
            engine.export_solutions("json", "custom_constraints_solutions.json")
            engine.generate_solution_report("custom_constraints_report.txt")
            print(f"\nResults exported:")
            print(f"  - custom_constraints_solutions.json")
            print(f"  - custom_constraints_report.txt")
    
    except Exception as e:
        print(f"Error during exploration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())