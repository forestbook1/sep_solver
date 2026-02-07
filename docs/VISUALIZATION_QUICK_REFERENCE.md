# Interactive Visualization - Quick Reference

## Installation
```bash
pip install networkx plotly
```

## Basic Usage
```python
from sep_solver import SEPEngine, SolverConfig, ConstraintSet

# Run solver
engine = SEPEngine(schema, constraints, config)
solutions = engine.solve()

# Create dashboard (easiest!)
engine.create_interactive_dashboard("dashboard.html")
```

## All Visualization Methods

### 1. Single Solution Graph
```python
engine.visualize_solution_interactive(
    solution_index=0,           # Which solution (0-based)
    output_file="solution.html", # Output file
    layout="spring",            # spring|circular|hierarchical|kamada_kawai
    show_variables=True         # Show variable assignments
)
```

### 2. Solution Comparison
```python
engine.visualize_solutions_comparison(
    output_file="comparison.html",
    max_solutions=6  # Show up to 6 solutions
)
```

### 3. Statistical Charts
```python
engine.visualize_solution_statistics(
    output_file="statistics.html"
)
```

### 4. Exploration Metrics
```python
engine.visualize_exploration_metrics(
    output_file="metrics.html"
)
```

### 5. Complete Dashboard
```python
engine.create_interactive_dashboard(
    output_file="dashboard.html"
)
```

## Layout Options

| Layout | Best For | Speed |
|--------|----------|-------|
| `spring` | General graphs | Medium |
| `circular` | Small graphs | Fast |
| `hierarchical` | Tree-like structures | Medium |
| `kamada_kawai` | Complex graphs | Slow |

## Common Patterns

### Pattern 1: Quick Dashboard
```python
engine.solve()
engine.create_interactive_dashboard("dashboard.html")
```

### Pattern 2: Individual Files
```python
engine.visualize_solution_interactive(0, "solution.html")
engine.visualize_solution_statistics("stats.html")
```

### Pattern 3: Programmatic (No File)
```python
html = engine.visualize_solution_interactive(0)
# Use html string in web app, notebook, etc.
```

### Pattern 4: Batch Processing
```python
for i in range(len(engine.get_solutions())):
    engine.visualize_solution_interactive(i, f"solution_{i}.html")
```

## Jupyter Notebook
```python
from IPython.display import HTML

html = engine.visualize_solution_interactive(0)
HTML(html)
```

## Troubleshooting

### Libraries Not Installed
```bash
pip install networkx plotly
```

### Check Installation
```bash
python test_visualization_basic.py
```

### Run Example
```bash
python examples/interactive_visualization.py
```

## File Outputs

All methods create self-contained HTML files that:
- Work in any modern browser
- Include all necessary JavaScript
- Support pan, zoom, hover
- Work offline (after first load)

## Features

✅ Interactive pan and zoom  
✅ Hover for details  
✅ Color-coded components  
✅ Edge labels  
✅ Variable display  
✅ Multiple layouts  
✅ Statistical charts  
✅ Exploration metrics  
✅ Comprehensive dashboard  

## Documentation

- Full Guide: `docs/VISUALIZATION.md`
- Examples: `examples/interactive_visualization.py`
- Features: `VISUALIZATION_FEATURES.md`
- Implementation: `IMPLEMENTATION_SUMMARY.md`

## Support

1. Check `docs/VISUALIZATION.md` for detailed guide
2. Run `test_visualization_basic.py` to verify setup
3. See `examples/interactive_visualization.py` for working code

---

**Quick Start:** `pip install networkx plotly` → Run solver → `engine.create_interactive_dashboard("dashboard.html")` → Open in browser!
