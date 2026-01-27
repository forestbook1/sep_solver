# SEP Solver Examples

This directory contains example scripts demonstrating various features and usage patterns of the SEP (Structural Exploration Problem) solver.

## Examples Overview

### 1. Basic Usage (`basic_usage.py`)

**Purpose**: Demonstrates fundamental SEP solver usage with minimal setup.

**Features shown**:
- Basic schema definition
- Simple configuration
- Console progress reporting
- Solution export and reporting

**Run with**:
```bash
python examples/basic_usage.py
```

**Expected output**:
- Console progress updates during exploration
- Summary of solutions found
- Exported files: `basic_example_solutions.json`, `basic_example_report.txt`

---

### 2. Advanced Configuration (`advanced_configuration.py`)

**Purpose**: Showcases advanced configuration features and runtime modification capabilities.

**Features shown**:
- Configuration management and history
- Runtime configuration modification
- Configuration presets (fast, thorough, balanced, debug)
- Custom progress callbacks
- Configuration file operations
- Plugin system basics

**Run with**:
```bash
python examples/advanced_configuration.py
```

**Expected output**:
- Multiple exploration runs with different configurations
- Configuration change notifications
- Custom progress alerts
- Exported files: `advanced_example_config.json`, `advanced_example_progress.json`

---

### 3. Exploration Strategies (`exploration_strategies.py`)

**Purpose**: Compares different exploration strategies and their performance characteristics.

**Features shown**:
- Strategy comparison framework
- Performance metrics analysis
- Strategy-specific behavior analysis
- Detailed comparison reporting

**Strategies compared**:
- `breadth_first`: Systematic level-by-level exploration
- `depth_first`: Deep exploration of solution branches
- `best_first`: Heuristic-guided exploration
- `random`: Random candidate generation

**Run with**:
```bash
python examples/exploration_strategies.py
```

**Expected output**:
- Side-by-side strategy comparison
- Performance analysis and recommendations
- Exported file: `strategy_comparison_results.json`

---

### 4. Custom Constraints (`custom_constraints.py`)

**Purpose**: Demonstrates how to create and use custom constraints to guide exploration.

**Features shown**:
- Custom constraint implementation
- Constraint violation handling
- Structural and variable constraints
- Constraint violation statistics

**Custom constraints included**:
- `MinimumComponentsConstraint`: Requires minimum number of components
- `MaximumComponentsConstraint`: Limits maximum number of components
- `RequiredComponentTypeConstraint`: Requires specific component types
- `VariableRangeConstraint`: Enforces variable value ranges
- `ConnectivityConstraint`: Ensures all components are connected

**Run with**:
```bash
python examples/custom_constraints.py
```

**Expected output**:
- Constraint-guided exploration
- Solution analysis showing constraint satisfaction
- Constraint violation statistics
- Exported files: `custom_constraints_solutions.json`, `custom_constraints_report.txt`

---

## Running the Examples

### Prerequisites

1. **Install the SEP solver package**:
   ```bash
   pip install -e .
   ```

2. **Install optional dependencies** (for enhanced features):
   ```bash
   pip install psutil  # For resource usage monitoring
   pip install pyyaml  # For YAML configuration support
   ```

### Running Individual Examples

Each example can be run independently:

```bash
# Basic usage
python examples/basic_usage.py

# Advanced configuration
python examples/advanced_configuration.py

# Strategy comparison
python examples/exploration_strategies.py

# Custom constraints
python examples/custom_constraints.py
```

### Running All Examples

To run all examples in sequence:

```bash
# On Unix/Linux/macOS
for example in examples/*.py; do
    if [[ "$example" != *"README"* ]]; then
        echo "Running $example..."
        python "$example"
        echo "---"
    fi
done

# On Windows (PowerShell)
Get-ChildItem examples\*.py | Where-Object { $_.Name -notlike "*README*" } | ForEach-Object {
    Write-Host "Running $($_.Name)..."
    python $_.FullName
    Write-Host "---"
}
```

## Understanding the Output

### Progress Reporting

Most examples include progress reporting that shows:
- **Progress bar**: Visual indication of completion
- **Iteration count**: Current/total iterations
- **Solutions found**: Number of valid solutions discovered
- **Performance metrics**: Speed, success rate, timing information

### Solution Analysis

Examples typically provide:
- **Solution count**: Total number of solutions found
- **Solution details**: Components, relationships, variables for each solution
- **Statistics**: Average complexity, ranges, patterns
- **Performance data**: Timing, efficiency metrics

### File Outputs

Examples generate various output files:
- **`.json` files**: Detailed solution data and results
- **`.txt` files**: Human-readable reports and summaries
- **Progress logs**: Detailed exploration progress data

## Customizing the Examples

### Modifying Problem Parameters

You can easily modify the examples to explore different problem characteristics:

```python
# Change exploration parameters
config = SolverConfig(
    exploration_strategy="breadth_first",  # Try different strategies
    max_iterations=500,                    # Increase for more thorough search
    max_solutions=20,                      # Find more solutions
    timeout_seconds=60.0                   # Add time limit
)

# Modify schema complexity
schema = {
    # Add more complex structure requirements
    # Include additional validation rules
    # Define custom property constraints
}
```

### Adding Custom Constraints

Follow the pattern in `custom_constraints.py`:

```python
class MyCustomConstraint(Constraint):
    def __init__(self, my_parameter):
        super().__init__(
            constraint_id="my_constraint",
            constraint_type="structural",  # or "variable" or "global"
            description="My custom constraint description"
        )
        self.my_parameter = my_parameter
    
    def evaluate(self, design_object: DesignObject) -> List[ConstraintViolation]:
        violations = []
        # Add your constraint logic here
        return violations
```

### Custom Progress Reporting

Create custom progress callbacks:

```python
def my_progress_callback(metrics):
    # Custom progress handling
    print(f"Custom update: {metrics.current_iteration} iterations")

def my_solution_callback(solution_count, solution_id):
    # Custom solution found handling
    print(f"Found solution: {solution_id}")

engine.create_callback_progress_reporter(
    progress_callback=my_progress_callback,
    solution_callback=my_solution_callback
)
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure the SEP solver package is installed (`pip install -e .`)
2. **Missing dependencies**: Install optional dependencies as needed
3. **Permission errors**: Ensure write permissions for output files
4. **Memory issues**: Reduce `max_iterations` or `max_solutions` for large problems

### Performance Tips

1. **Start small**: Begin with low iteration counts to test your setup
2. **Use appropriate strategies**: Choose strategies based on your problem characteristics
3. **Monitor progress**: Use progress reporting to understand exploration behavior
4. **Tune constraints**: Well-designed constraints can significantly improve efficiency

### Getting Help

- Check the main documentation for detailed API reference
- Review the source code for implementation details
- Examine the test files for additional usage patterns
- Create issues on the project repository for bugs or questions

## Next Steps

After running these examples, consider:

1. **Implementing your own problem domain**: Define custom schemas and constraints
2. **Creating custom exploration strategies**: Extend the solver with domain-specific logic
3. **Building integration tools**: Connect the solver to your existing workflows
4. **Contributing improvements**: Share your enhancements with the community

Happy exploring! 🚀