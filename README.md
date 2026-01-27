# SEP Solver

SEP (Structural Exploration Problem) Solver is a modular system that explores both structural configurations and variable assignments under constraints. The solver operates on JSON-based design objects with a focus on modularity, extensibility, and debuggability.

## Features

- **Modular Architecture**: Clear separation between structure generation, variable assignment, and constraint evaluation
- **JSON Schema Validation**: Ensures design objects conform to specified schemas
- **Pluggable Components**: Extensible architecture allowing custom generators, assigners, and evaluators
- **Property-Based Testing**: Comprehensive testing using hypothesis for correctness guarantees
- **Comprehensive Logging**: Detailed exploration process logging and debugging capabilities
- **Multiple Exploration Strategies**: Support for breadth-first, depth-first, and best-first exploration

## Installation

```bash
# Install from source
pip install -e .

# Install with development dependencies
pip install -e ".[dev,test]"
```

## Quick Start

```python
from sep_solver import SEPEngine, ConstraintSet, SolverConfig

# Define your JSON schema
schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "structure": {"type": "object"},
        "variables": {"type": "object"},
        "metadata": {"type": "object"}
    }
}

# Create constraint set
constraints = ConstraintSet()

# Configure solver
config = SolverConfig(
    exploration_strategy="breadth_first",
    max_iterations=1000,
    max_solutions=10
)

# Initialize and run solver
engine = SEPEngine(schema, constraints, config)
solutions = engine.solve()
```

## Architecture

The SEP solver follows a layered architecture:

- **Core Layer**: SEP Engine orchestrates the exploration process
- **Generation Layer**: Structure generators and variable assigners create candidates
- **Evaluation Layer**: Constraint evaluators and schema validators check validity
- **Data Layer**: Design objects, structures, and constraints represent the problem space

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=sep_solver

# Run only unit tests
pytest -m unit

# Run only property-based tests
pytest -m property
```

### Code Quality

```bash
# Format code
black sep_solver tests

# Lint code
flake8 sep_solver tests

# Type checking
mypy sep_solver
```

## Project Status

This project is currently under active development. The implementation follows a task-based approach:

- ✅ Task 1: Project structure and core interfaces
- ⏳ Task 2: JSON schema validation and design object handling
- ⏳ Task 3: Core data models
- ⏳ Task 4-13: Component implementations and integration
- ⏳ Task 14: Final testing and validation

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.