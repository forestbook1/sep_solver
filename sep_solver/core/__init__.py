"""Core components of the SEP solver."""

from .engine import SEPEngine
from .interfaces import (
    StructureGenerator,
    VariableAssigner, 
    ConstraintEvaluator,
    SchemaValidator
)
from .results import EvaluationResult, ValidationResult, SchemaError
from .config import SolverConfig
from .exceptions import (
    SEPSolverError,
    SchemaValidationError,
    ConstraintViolationError,
    StructureGenerationError,
    VariableAssignmentError
)

__all__ = [
    "SEPEngine",
    "StructureGenerator",
    "VariableAssigner",
    "ConstraintEvaluator", 
    "SchemaValidator",
    "EvaluationResult",
    "ValidationResult", 
    "SchemaError",
    "SolverConfig",
    "SEPSolverError",
    "SchemaValidationError",
    "ConstraintViolationError",
    "StructureGenerationError",
    "VariableAssignmentError"
]