# Output Organization Guide

## Overview

The SEP Solver now automatically organizes output files into directories to keep your workspace clean.

## Default Directory Structure

```
your_project/
├── output/                    # All generated files go here (default)
│   ├── *.html                # Visualization files
│   ├── *.json                # Solution exports
│   ├── *.csv                 # CSV exports
│   └── *.txt                 # Reports
├── docs/                      # Documentation
│   ├── VISUALIZATION.md      # User guide
│   ├── VISUALIZATION_QUICK_REFERENCE.md
│   └── implementation/       # Implementation docs
│       ├── IMPLEMENTATION_SUMMARY.md
│       ├── VISUALIZATION_FEATURES.md
│       ├── SUCCESS_SUMMARY.md
│       └── CHECKLIST.md
├── examples/                  # Example scripts
├── tests/                     # Test files
└── sep_solver/               # Source code
```

## Configuration

### Default Output Directory

By default, all output files are saved to the `output/` directory:

```python
from sep_solver import SEPEngine, SolverConfig, ConstraintSet

# Default configuration (uses 'output/' directory)
config = SolverConfig()
engine = SEPEngine(schema, constraints, config)

# Files will be saved to output/
engine.create_interactive_dashboard("dashboard.html")
# Creates: output/dashboard.html
```

### Custom Output Directory

You can change the output directory:

```python
# Use a custom output directory
config = SolverConfig(
    output_directory="my_results",
    create_output_directory=True  # Auto-create if doesn't exist
)
engine = SEPEngine(schema, constraints, config)

# Files will be saved to my_results/
engine.create_interactive_dashboard("dashboard.html")
# Creates: my_results/dashboard.html
```

### Disable Auto-Directory

To save files in the current directory (old behavior):

```python
# Save to current directory
config = SolverConfig(
    output_directory=".",  # Current directory
    create_output_directory=False
)
```

### Absolute Paths

Absolute paths bypass the output directory:

```python
# This will save to the exact path specified
engine.create_interactive_dashboard("/absolute/path/dashboard.html")
# Creates: /absolute/path/dashboard.html (not in output/)
```

## File Organization Best Practices

### 1. Organize by Project

```python
config = SolverConfig(output_directory="results/project_a")
```

### 2. Organize by Date

```python
from datetime import datetime
date_str = datetime.now().strftime("%Y%m%d")
config = SolverConfig(output_directory=f"results/{date_str}")
```

### 3. Organize by Experiment

```python
experiment_name = "experiment_001"
config = SolverConfig(output_directory=f"experiments/{experiment_name}")
```

### 4. Subdirectories

You can use subdirectories in filenames:

```python
# Creates: output/visualizations/dashboard.html
engine.create_interactive_dashboard("visualizations/dashboard.html")

# Creates: output/exports/solutions.json
engine.export_solutions("json", "exports/solutions.json")
```

## Example: Complete Organization

```python
from sep_solver import SEPEngine, SolverConfig, ConstraintSet
from datetime import datetime

# Create organized output structure
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
config = SolverConfig(
    output_directory=f"results/{timestamp}",
    create_output_directory=True
)

engine = SEPEngine(schema, constraints, config)
solutions = engine.solve()

# All files go to results/YYYYMMDD_HHMMSS/
engine.create_interactive_dashboard("dashboard.html")
engine.export_solutions("json", "solutions.json")
engine.export_solutions("csv", "solutions.csv")
engine.visualize_solution_statistics("stats.html")

# With subdirectories
engine.visualize_solution_interactive(0, "visualizations/solution_0.html")
engine.visualize_solution_interactive(1, "visualizations/solution_1.html")
```

This creates:
```
results/
└── 20260207_154500/
    ├── dashboard.html
    ├── solutions.json
    ├── solutions.csv
    ├── stats.html
    └── visualizations/
        ├── solution_0.html
        └── solution_1.html
```

## Configuration Options

### SolverConfig Output Settings

```python
config = SolverConfig(
    # Output directory (default: "output")
    output_directory="output",
    
    # Auto-create directory if it doesn't exist (default: True)
    create_output_directory=True,
    
    # Overwrite existing files (default: True)
    overwrite_existing_files=True
)
```

## Migration from Old Code

If you have existing code that saves to the root directory:

### Before (saves to root)
```python
engine.create_interactive_dashboard("dashboard.html")
# Creates: dashboard.html (in root)
```

### After (saves to output/)
```python
# Option 1: Use default (recommended)
engine.create_interactive_dashboard("dashboard.html")
# Creates: output/dashboard.html

# Option 2: Keep old behavior
config = SolverConfig(output_directory=".")
engine = SEPEngine(schema, constraints, config)
engine.create_interactive_dashboard("dashboard.html")
# Creates: dashboard.html (in root)

# Option 3: Use absolute path
engine.create_interactive_dashboard("./dashboard.html")
# Creates: ./dashboard.html (in root)
```

## Tips

1. **Use relative paths** - Let the output_directory handle organization
2. **Use subdirectories** - Organize within output directory
3. **Use timestamps** - Avoid overwriting previous results
4. **Use descriptive names** - Make files easy to identify
5. **Clean up regularly** - Remove old output directories

## Cleaning Up

### Manual Cleanup
```bash
# Remove all output files
rm -rf output/

# Remove specific experiment
rm -rf results/experiment_001/
```

### Programmatic Cleanup
```python
import shutil
import os

# Remove old output directory
if os.path.exists("output"):
    shutil.rmtree("output")

# Remove outputs older than 7 days
import time
from pathlib import Path

cutoff = time.time() - (7 * 24 * 60 * 60)  # 7 days
for path in Path("results").glob("*"):
    if path.stat().st_mtime < cutoff:
        shutil.rmtree(path)
```

## Summary

- ✅ All output files go to `output/` by default
- ✅ Configurable via `SolverConfig.output_directory`
- ✅ Auto-creates directories as needed
- ✅ Supports subdirectories for organization
- ✅ Absolute paths bypass output directory
- ✅ Backward compatible with old code

This keeps your workspace clean and organized!
