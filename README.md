# SEP Solver

SEP (Structural Exploration Problem) Solver is a modular system that explores both structural configurations and variable assignments under constraints. The solver operates on JSON-based design objects with a focus on modularity, extensibility, and debuggability.

## Features

### Core Capabilities
- **Modular Architecture**: Clear separation between structure generation, variable assignment, and constraint evaluation
- **JSON Schema Validation**: Ensures design objects conform to specified schemas with detailed error reporting
- **Multiple Exploration Strategies**: Support for breadth-first, depth-first, best-first, and random exploration
- **Property-Based Testing**: Comprehensive testing using Hypothesis for correctness guarantees

### Advanced Features
- **Plugin System**: Extensible architecture allowing custom components through a plugin framework
  - Component registration and discovery
  - Plugin loading from modules, directories, or configuration files
  - Runtime component substitution
- **Comprehensive Logging**: Detailed exploration process logging with structured logging support
  - Exploration state tracking
  - Constraint violation logging
  - Performance metrics
- **Debugging & Introspection**: Advanced debugging capabilities
  - Decision trace analysis
  - Candidate journey tracking
  - Intermediate state inspection
  - Exploration pattern analysis
- **Visualization & Export**: Multiple output formats for solutions
  - Export: JSON, CSV, YAML, XML
  - Visualization: Text, DOT graphs, Mermaid diagrams, ASCII trees
  - Comprehensive solution reports

## Installation

```bash
# Install from source
pip install -e .

# Install with development dependencies
pip install -e ".[dev,test]"
```

## Quick Start

### Basic Usage

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
    },
    "required": ["id", "structure", "variables"]
}

# Create constraint set
constraints = ConstraintSet()

# Configure solver
config = SolverConfig(
    exploration_strategy="breadth_first",
    max_iterations=1000,
    max_solutions=10,
    enable_logging=True
)

# Initialize and run solver
engine = SEPEngine(schema, constraints, config)
solutions = engine.solve()

# Access solutions
for solution in solutions:
    print(f"Solution {solution.id}:")
    print(f"  Components: {len(solution.structure.components)}")
    print(f"  Variables: {len(solution.variables.assignments)}")
```

### Using the Plugin System

```python
from sep_solver.plugins.example_plugins import CustomStructureGeneratorPlugin

# Register a custom plugin
plugin = CustomStructureGeneratorPlugin()
plugin.initialize()
engine.register_plugin(plugin)

# Substitute a component with the plugin
engine.substitute_component_with_plugin(
    "structure_generator", 
    "custom_structure_generator",
    complexity_bias=0.8
)

# Continue exploration with custom component
solutions = engine.solve()
```

### Exporting and Visualizing Solutions

```python
# Export solutions to different formats
engine.export_solutions(solutions, "solutions", format="json")
engine.export_solutions(solutions, "solutions", format="csv")

# Generate visualizations
text_viz = engine.visualize_solution(solutions[0], format="text")
dot_graph = engine.visualize_solution(solutions[0], format="dot")
mermaid = engine.visualize_solution(solutions[0], format="mermaid")

# Create comprehensive report
report = engine.create_solution_report("solution_report.txt")

# Save all visualizations
engine.save_solution_visualizations("visualizations/", formats=["text", "dot", "mermaid"])
```

### Debugging and Introspection

```python
# Get exploration statistics
stats = engine.get_exploration_statistics()
print(f"Iterations: {stats['iteration_count']}")
print(f"Solutions found: {stats['solutions_found']}")

# Analyze decision-making
decisions = engine.get_decision_trace(decision_type="structure_generation")
for decision in decisions:
    print(f"Decision: {decision['decision_type']}")
    print(f"Reasoning: {decision['reasoning']}")

# Trace a specific candidate
journey = engine.trace_candidate_journey("candidate_0")
print(f"Candidate was valid: {journey['journey_summary']['was_valid']}")

# Analyze exploration patterns
patterns = engine.analyze_exploration_patterns()
print(f"Most common decision: {patterns['decision_patterns']}")
```

## Architecture

The SEP solver follows a layered architecture:

### Core Components
- **SEP Engine**: Orchestrates the exploration process and coordinates all components
- **Plugin Manager**: Manages plugin registration, loading, and component substitution
- **Configuration System**: Flexible configuration with validation and runtime modification

### Generation Layer
- **Structure Generator**: Creates valid structural configurations
  - Random generation with constraint satisfaction
  - Incremental modification and variant generation
  - Pluggable through the plugin system
- **Variable Assigner**: Assigns values to variables within structures
  - Multiple strategies: random, systematic, heuristic
  - Dependency handling and propagation
  - Domain validation

### Evaluation Layer
- **Constraint Evaluator**: Evaluates design candidates against constraints
  - Support for structural, variable, and global constraints
  - Detailed violation reporting
  - Custom constraint type registration
- **Schema Validator**: Validates design objects against JSON schemas
  - Comprehensive error reporting with paths
  - Support for complex nested schemas

### Data Models
- **Design Object**: Complete design with structure and variable assignments
- **Structure**: Component configurations and relationships
- **Variable Assignment**: Variable values with domains and dependencies
- **Constraint Set**: Collection of constraints to be satisfied

### Utilities
- **Logging System**: Structured logging with exploration tracking
- **Visualization**: Multiple export and visualization formats
- **Progress Tracking**: Real-time exploration progress monitoring

## Development

### Running Tests

```bash
# Run all tests (365 tests)
pytest

# Run with coverage
pytest --cov=sep_solver --cov-report=html

# Run specific test categories
pytest tests/test_core/              # Core functionality
pytest tests/test_evaluators/        # Evaluators
pytest tests/test_generators/        # Generators
pytest tests/test_models/            # Data models
pytest tests/test_integration/       # Integration tests

# Run property-based tests
pytest -m hypothesis

# Run with verbose output
pytest -v
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

The SEP solver is feature-complete with comprehensive testing:

### Completed Features ✅
- ✅ **Task 1**: Project structure and core interfaces
- ✅ **Task 2**: JSON schema validation and design object handling
- ✅ **Task 3**: Core data models (Structure, VariableAssignment, ConstraintSet)
- ✅ **Task 4**: Component integration checkpoint
- ✅ **Task 5**: Structure Generator with modification capabilities
- ✅ **Task 6**: Variable Assigner with dependency handling
- ✅ **Task 7**: Constraint Evaluator with custom constraint types
- ✅ **Task 8**: Component integration checkpoint
- ✅ **Task 9**: SEP Engine with exploration strategies
- ✅ **Task 10**: Debugging and introspection capabilities
  - Comprehensive logging system
  - Exploration state inspection
  - Solution visualization and export
- ✅ **Task 11.1-11.2**: Plugin architecture and property testing

### Test Coverage
- **Total Tests**: 365 tests passing
- **Property-Based Tests**: 12 correctness properties validated
- **Test Categories**:
  - Core functionality: 34 tests
  - Plugin system: 34 tests
  - Evaluators: 38 tests
  - Generators: 48 tests
  - Models: 205 tests
  - Integration: 6 tests

### Correctness Properties
The solver validates 12 universal correctness properties:
1. Schema Validation Completeness
2. Serialization Round Trip
3. Structure Generation Validity
4. Structure Modification Preservation
5. Variable Assignment Completeness
6. Dependency Satisfaction
7. Constraint Evaluation Accuracy
8. Exploration Solution Validity
9. Plugin Component Substitution
10. Configuration Application
11. Error Message Descriptiveness
12. Exploration Strategy Differentiation

## Plugin Development

### Creating a Custom Plugin

```python
from sep_solver.core.plugin_system import ComponentPlugin, PluginMetadata
from sep_solver.generators.structure_generator import BaseStructureGenerator

class MyCustomPlugin(ComponentPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_custom_plugin",
            version="1.0.0",
            description="My custom structure generator",
            component_type="structure_generator",
            author="Your Name"
        )
    
    def initialize(self, config=None):
        self.config = config or {}
    
    def validate_dependencies(self):
        return []  # No dependencies
    
    def create_component(self, **kwargs):
        # Return your custom component instance
        return MyCustomStructureGenerator(**kwargs)
```

### Loading Plugins

```python
# Load from module
engine.load_plugins_from_module("my_plugins.custom")

# Load from directory
engine.load_plugins_from_directory("./plugins")

# Load from configuration file
engine.load_plugins_from_config("plugins.json")
```

## Documentation

For detailed documentation, see:
- [Requirements Document](.kiro/specs/sep-solver/requirements.md)
- [Design Document](.kiro/specs/sep-solver/design.md)
- [Implementation Tasks](.kiro/specs/sep-solver/tasks.md)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

For major changes, please open an issue first to discuss the proposed changes.