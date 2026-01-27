"""Result classes for SEP solver operations."""

from typing import List, Any
from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """Result of constraint evaluation."""
    
    is_valid: bool
    violations: List['ConstraintViolation'] = None
    
    def __post_init__(self):
        if self.violations is None:
            self.violations = []
        
    def __bool__(self) -> bool:
        return self.is_valid


@dataclass
class ValidationResult:
    """Result of schema validation."""
    
    is_valid: bool
    errors: List['SchemaError'] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        
    def __bool__(self) -> bool:
        return self.is_valid


@dataclass
class SchemaError:
    """Represents a schema validation error."""
    
    path: str
    message: str
    value: Any = None
        
    def __str__(self) -> str:
        return f"Schema error at '{self.path}': {self.message}"