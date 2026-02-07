"""Quick test to verify the visualization module structure."""

from sep_solver.utils.visualization import SolutionVisualizer

# Test basic initialization
visualizer = SolutionVisualizer()

print("Visualization Module Test")
print("=" * 50)
print(f"NetworkX available: {visualizer.has_networkx}")
print(f"Plotly available: {visualizer.has_plotly}")
print(f"Interactive enabled: {visualizer.interactive_enabled}")
print()
print(f"Supported export formats: {visualizer.export_formats}")
if visualizer.interactive_enabled:
    print(f"Interactive formats: {visualizer.interactive_formats}")
print()

if not visualizer.interactive_enabled:
    print("To enable interactive visualization, install:")
    print("  pip install networkx plotly")
    print()
    print("Or use the requirements file:")
    print("  pip install -r requirements-viz.txt")
else:
    print("✓ Interactive visualization is ready!")
    print()
    print("Available methods:")
    print("  - visualize_solution_interactive()")
    print("  - visualize_solutions_comparison()")
    print("  - visualize_solution_statistics()")
    print("  - visualize_exploration_metrics()")
    print("  - create_interactive_dashboard()")

print("=" * 50)
