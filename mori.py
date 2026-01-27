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