"""
SEP (Structural Exploration Problem) Solver

A modular system that explores both structural configurations and variable assignments under constraints.
The solver operates on JSON-based design objects with a focus on modularity, extensibility, and debuggability.
"""

__version__ = "0.1.0"
__author__ = "SEP Solver Team"

from .core.engine import SEPEngine
from .core.config import SolverConfig
from .core.interfaces import (
    StructureGenerator,
    VariableAssigner,
    ConstraintEvaluator,
    SchemaValidator
)
from .models.design_object import DesignObject
from .models.structure import Structure
from .models.variable_assignment import VariableAssignment
from .models.constraint_set import ConstraintSet

__all__ = [
    "SEPEngine",
    "SolverConfig",
    "StructureGenerator", 
    "VariableAssigner",
    "ConstraintEvaluator",
    "SchemaValidator",
    "DesignObject",
    "Structure",
    "VariableAssignment", 
    "ConstraintSet"
]