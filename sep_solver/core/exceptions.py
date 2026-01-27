"""Exception classes for the SEP solver."""

from typing import List, Any, Dict


class SEPSolverError(Exception):
    """Base exception for SEP solver errors."""
    pass


class SchemaValidationError(SEPSolverError):
    """Raised when design object fails schema validation."""
    
    def __init__(self, violations: List[str], design_object: Dict[str, Any] = None):
        self.violations = violations
        self.design_object = design_object
        message = f"Schema validation failed with {len(violations)} violations:\n" + "\n".join(f"  - {v}" for v in violations)
        super().__init__(message)


class ConstraintViolationError(SEPSolverError):
    """Raised when constraints are violated."""
    
    def __init__(self, violations: List['ConstraintViolation']):
        self.violations = violations
        message = f"Constraint validation failed with {len(violations)} violations:\n" + "\n".join(f"  - {v}" for v in violations)
        super().__init__(message)


class StructureGenerationError(SEPSolverError):
    """Raised when structure generation fails."""
    
    def __init__(self, message: str, attempted_structure: Any = None):
        self.attempted_structure = attempted_structure
        super().__init__(message)


class VariableAssignmentError(SEPSolverError):
    """Raised when variable assignment fails."""
    
    def __init__(self, message: str, variable_name: str = None, attempted_value: Any = None):
        self.variable_name = variable_name
        self.attempted_value = attempted_value
        super().__init__(message)


class ConfigurationError(SEPSolverError):
    """Raised when configuration is invalid."""
    pass


class ExplorationError(SEPSolverError):
    """Raised when exploration process encounters an error."""
    pass