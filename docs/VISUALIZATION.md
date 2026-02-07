# Interactive Visualization Guide

The SEP Solver includes powerful interactive visualization capabilities using NetworkX and Plotly. This guide shows you how to use them.

## Installation

Interactive visualization requires two additional libraries:

```bash
# Option 1: Install directly
pip install networkx plotly

# Option 2: Use requirements file
pip install -r requirements-viz.txt

# Option 3: Install with scipy for better layouts (optional)
pip install networkx plotly scipy
```

## Quick Start

```python
from sep_solver import SEPEngine, SolverConfig, ConstraintSet

# ... configure and run your solver ...
solutions = engine.solve()

# Create interactive visualization
engine.visualize_solution_interactive(
    solution_index=0,
    output_file="solution.html"
)

# Open solution.html in your browser!
```

## Visualization Types

### 1. Single Solution Interactive Graph

Visualize a single solution as an interactive network graph.

```python
engine.visualize_solution_interactive(
    solution_index=0,              # Which solution to visualize
    output_file="solution.html",   # Output file
    layout="spring",               # Layout algorithm
    show_variables=True,           # Show variable assignments
    show_metadata=False            # Show metadata
)
```

**Layout Options:**
- `"spring"` - Force-directed layout (default, good for most graphs)
- `"circular"` - Nodes arranged in a circle
- `"hierarchical"` - Tree-like hierarchical layout
- `"kamada_kawai"` - Energy-minimization layout

**Features:**
- Interactive pan and zoom
- Hover over nodes to see details
- Color-coded by component type
- Edge labels show relationship types
- Variable assignments displayed in corner

### 2. Solution Comparison

Compare multiple solutions side-by-side.

```python
engine.visualize_solutions_comparison(
    output_file="comparison.html",
    max_solutions=6  # Show up to 6 solutions
)
```

**Features:**
- Grid layout showing multiple solutions
- Easy visual comparison of structures
- Hover for details on each solution
- Automatically scales to fit solutions

### 3. Statistical Visualization

Generate interactive charts showing solution statistics.

```python
engine.visualize_solution_statistics(
    output_file="statistics.html"
)
```

**Charts Included:**
- Components per solution (bar chart)
- Relationships per solution (bar chart)
- Variables per solution (bar chart)
- Structure complexity scatter plot

**Features:**
- Interactive charts with zoom and pan
- Hover for exact values
- Color-coded by variable count
- Identifies outliers visually

### 4. Exploration Metrics

Visualize the exploration process metrics.

```python
engine.visualize_exploration_metrics(
    output_file="metrics.html"
)
```

**Metrics Shown:**
- Constraint violations by type
- Component performance (execution time)
- Candidate evaluation timeline
- Success rate over time

**Features:**
- Track exploration efficiency
- Identify bottlenecks
- See which constraints fail most
- Monitor success rate trends

### 5. Comprehensive Dashboard

Create an all-in-one dashboard with all visualizations.

```python
engine.create_interactive_dashboard(
    output_file="dashboard.html"
)
```

**Includes:**
- Summary statistics
- Solution statistics charts
- Solution comparison grid
- Individual solution details
- Exploration metrics

**Perfect for:**
- Presentations
- Reports
- Comprehensive analysis
- Sharing results with stakeholders

## Advanced Usage

### Programmatic Access

Get HTML strings instead of writing to files:

```python
# Get HTML as string
html = engine.visualize_solution_interactive(solution_index=0)

# Use in web applications, notebooks, etc.
from IPython.display import HTML
display(HTML(html))
```

### Custom Styling

The generated HTML includes embedded CSS. You can modify the dashboard styling:

```python
from sep_solver.utils.visualization import SolutionVisualizer

visualizer = SolutionVisualizer()
html = visualizer.create_interactive_dashboard(solutions, exploration_state)

# Modify HTML/CSS as needed
custom_html = html.replace("background-color: #f5f5f5", "background-color: #ffffff")

with open("custom_dashboard.html", "w") as f:
    f.write(custom_html)
```

### Jupyter Notebook Integration

Use visualizations directly in Jupyter notebooks:

```python
from IPython.display import HTML

# Display interactive visualization inline
html = engine.visualize_solution_interactive(solution_index=0)
HTML(html)
```

## Examples

### Example 1: Basic Workflow

```python
from sep_solver import SEPEngine, SolverConfig, ConstraintSet

# Configure and run solver
config = SolverConfig(max_solutions=10)
engine = SEPEngine(schema, constraints, config)
solutions = engine.solve()

# Create visualizations
engine.visualize_solution_interactive(0, "solution_0.html")
engine.visualize_solutions_comparison("comparison.html")
engine.create_interactive_dashboard("dashboard.html")

print("Open dashboard.html in your browser!")
```

### Example 2: Comparing Layouts

```python
# Try different layouts for the same solution
layouts = ["spring", "circular", "hierarchical", "kamada_kawai"]

for layout in layouts:
    engine.visualize_solution_interactive(
        solution_index=0,
        output_file=f"solution_{layout}.html",
        layout=layout
    )
```

### Example 3: Batch Processing

```python
# Create individual visualizations for all solutions
for i in range(len(engine.get_solutions())):
    engine.visualize_solution_interactive(
        solution_index=i,
        output_file=f"solutions/solution_{i}.html"
    )
```

## Troubleshooting

### Libraries Not Installed

**Error:** `ImportError: Interactive visualization requires 'networkx' and 'plotly'`

**Solution:**
```bash
pip install networkx plotly
```

### Large Graphs Performance

For solutions with many components (>50), consider:

1. Use simpler layouts: `layout="circular"` is faster than `layout="spring"`
2. Disable variable display: `show_variables=False`
3. Limit comparison: `max_solutions=3` instead of 6

### Browser Compatibility

The visualizations work best in modern browsers:
- Chrome/Edge (recommended)
- Firefox
- Safari

## API Reference

### SEPEngine Methods

```python
# Single solution
visualize_solution_interactive(
    solution_index: int = 0,
    output_file: Optional[str] = None,
    layout: str = "spring",
    show_variables: bool = True
) -> str

# Comparison
visualize_solutions_comparison(
    output_file: Optional[str] = None,
    max_solutions: int = 6
) -> str

# Statistics
visualize_solution_statistics(
    output_file: Optional[str] = None
) -> str

# Metrics
visualize_exploration_metrics(
    output_file: Optional[str] = None
) -> str

# Dashboard
create_interactive_dashboard(
    output_file: str
) -> None
```

### SolutionVisualizer Methods

For direct access to the visualizer:

```python
from sep_solver.utils.visualization import SolutionVisualizer

visualizer = SolutionVisualizer()

# Check capabilities
visualizer.interactive_enabled  # bool
visualizer.has_networkx        # bool
visualizer.has_plotly          # bool

# Create visualizations
html = visualizer.visualize_solution_interactive(solution, layout="spring")
html = visualizer.visualize_solutions_comparison(solutions)
html = visualizer.visualize_solution_statistics(solutions)
html = visualizer.visualize_exploration_metrics(exploration_state)
html = visualizer.create_interactive_dashboard(solutions, exploration_state)
```

## Tips and Best Practices

1. **Start with the dashboard** - It gives you everything in one place
2. **Use spring layout** - Best for most graph structures
3. **Limit comparisons** - 3-6 solutions is optimal for comparison view
4. **Check metrics** - Exploration metrics help optimize your solver configuration
5. **Share HTML files** - They're self-contained and work offline

## Next Steps

- See `examples/interactive_visualization.py` for a complete example
- Check `examples/custom_constraints.py` for advanced constraint usage
- Read the main README for general solver documentation
