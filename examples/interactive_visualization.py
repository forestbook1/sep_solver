"""
Example demonstrating interactive visualization capabilities of the SEP solver.

This example shows how to:
1. Run the solver to find solutions
2. Create interactive HTML visualizations
3. Generate comparison charts
4. Create a comprehensive dashboard
"""

from sep_solver import SEPEngine, SolverConfig, ConstraintSet
from sep_solver.models.constraint_set import StructuralConstraint
from sep_solver.models.design_object import DesignObject


class MinComponentsConstraint(StructuralConstraint):
    """Constraint requiring minimum components."""
    
    def __init__(self, min_count: int):
        super().__init__(
            constraint_id="min_components",
            description=f"Requires at least {min_count} components"
        )
        self.min_count = min_count
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return len(design_object.structure.components) >= self.min_count
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        actual = len(design_object.structure.components)
        return f"Has {actual} components, requires at least {self.min_count}"


class MaxComponentsConstraint(StructuralConstraint):
    """Constraint limiting maximum components."""
    
    def __init__(self, max_count: int):
        super().__init__(
            constraint_id="max_components",
            description=f"Allows at most {max_count} components"
        )
        self.max_count = max_count
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return len(design_object.structure.components) <= self.max_count
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        actual = len(design_object.structure.components)
        return f"Has {actual} components, allows at most {self.max_count}"


class MinRelationshipsConstraint(StructuralConstraint):
    """Constraint requiring minimum relationships."""
    
    def __init__(self, min_count: int):
        super().__init__(
            constraint_id="min_relationships",
            description=f"Requires at least {min_count} relationship"
        )
        self.min_count = min_count
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return len(design_object.structure.relationships) >= self.min_count
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        actual = len(design_object.structure.relationships)
        return f"Has {actual} relationships, requires at least {self.min_count}"


def main():
    print("=" * 60)
    print("SEP Solver - Interactive Visualization Example")
    print("=" * 60)
    
    # Define schema
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "structure": {
                "type": "object",
                "properties": {
                    "components": {"type": "array"},
                    "relationships": {"type": "array"}
                }
            },
            "variables": {
                "type": "object",
                "properties": {
                    "assignments": {"type": "object"},
                    "domains": {"type": "object"}
                }
            },
            "metadata": {"type": "object"}
        },
        "required": ["id", "structure", "variables"]
    }
    
    # Create constraints
    constraints = ConstraintSet()
    
    # Add structural constraints
    constraints.add_constraint(MinComponentsConstraint(2))
    constraints.add_constraint(MaxComponentsConstraint(5))
    constraints.add_constraint(MinRelationshipsConstraint(1))
    
    # Configure solver
    config = SolverConfig(
        exploration_strategy="breadth_first",
        max_iterations=100,
        max_solutions=10,
        enable_logging=True,
        log_level="INFO"
    )
    
    # Create and run solver
    print("\n1. Running solver to find solutions...")
    engine = SEPEngine(schema, constraints, config)
    solutions = engine.solve()
    
    print(f"\nFound {len(solutions)} solutions!")
    
    if not solutions:
        print("No solutions found. Cannot create visualizations.")
        return
    
    # Check if interactive visualization is available
    from sep_solver.utils.visualization import SolutionVisualizer
    visualizer = SolutionVisualizer()
    
    if not visualizer.interactive_enabled:
        print("\n" + "=" * 60)
        print("Interactive visualization requires additional libraries!")
        print("Install with: pip install networkx plotly")
        print("=" * 60)
        return
    
    print("\n" + "=" * 60)
    print("Creating Interactive Visualizations")
    print("=" * 60)
    
    # Create output directory
    import os
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Single solution interactive visualization
    print("\n2. Creating interactive visualization of first solution...")
    try:
        engine.visualize_solution_interactive(
            solution_index=0,
            output_file=f"{output_dir}/interactive_solution.html",
            layout="spring",
            show_variables=True
        )
        print(f"   ✓ Saved to: {output_dir}/interactive_solution.html")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 2. Solution comparison
    if len(solutions) > 1:
        print("\n3. Creating solution comparison visualization...")
        try:
            engine.visualize_solutions_comparison(
                output_file=f"{output_dir}/solution_comparison.html",
                max_solutions=6
            )
            print(f"   ✓ Saved to: {output_dir}/solution_comparison.html")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    # 3. Statistical visualization
    print("\n4. Creating statistical visualization...")
    try:
        engine.visualize_solution_statistics(
            output_file=f"{output_dir}/solution_statistics.html"
        )
        print(f"   ✓ Saved to: {output_dir}/solution_statistics.html")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 4. Exploration metrics
    print("\n5. Creating exploration metrics visualization...")
    try:
        engine.visualize_exploration_metrics(
            output_file=f"{output_dir}/exploration_metrics.html"
        )
        print(f"   ✓ Saved to: {output_dir}/exploration_metrics.html")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 5. Comprehensive dashboard
    print("\n6. Creating comprehensive interactive dashboard...")
    try:
        engine.create_interactive_dashboard(
            output_file=f"{output_dir}/dashboard.html"
        )
        print(f"   ✓ Saved to: {output_dir}/dashboard.html")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Visualization Complete!")
    print("=" * 60)
    print(f"\nGenerated files in '{output_dir}/' directory:")
    print(f"  • interactive_solution.html    - Interactive graph of first solution")
    if len(solutions) > 1:
        print(f"  • solution_comparison.html     - Side-by-side solution comparison")
    print(f"  • solution_statistics.html     - Statistical charts and analysis")
    print(f"  • exploration_metrics.html     - Exploration process metrics")
    print(f"  • dashboard.html               - Comprehensive dashboard")
    print(f"\nOpen any HTML file in your web browser to explore interactively!")
    print("=" * 60)
    
    # Print solution summary
    print("\nSolution Summary:")
    for i, solution in enumerate(solutions, 1):
        print(f"\n  Solution {i}: {solution.id}")
        print(f"    Components: {len(solution.structure.components)}")
        print(f"    Relationships: {len(solution.structure.relationships)}")
        print(f"    Variables: {len(solution.variables.assignments)}")


if __name__ == "__main__":
    main()
