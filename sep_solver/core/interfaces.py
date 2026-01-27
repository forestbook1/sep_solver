"""Core interfaces and abstract base classes for the SEP solver."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING
from .results import EvaluationResult, ValidationResult, SchemaError

if TYPE_CHECKING:
    from ..models.design_object import DesignObject
    from ..models.structure import Structure, Modification
    from ..models.variable_assignment import VariableAssignment, AssignmentSpace
    from ..models.constraint_set import ConstraintSet, Constraint, ConstraintViolation
    from ..models.exploration_state import ExplorationState


class StructureGenerator(ABC):
    """Abstract base class for structure generation components."""
    
    @abstractmethod
    def generate_structure(self, constraints: List['Constraint']) -> 'Structure':
        """Generate a valid structure satisfying structural constraints.
        
        Args:
            constraints: List of structural constraints to satisfy
            
        Returns:
            A valid Structure object
            
        Raises:
            StructureGenerationError: If structure generation fails
        """
        pass
    
    @abstractmethod
    def modify_structure(self, structure: 'Structure', modification: 'Modification') -> 'Structure':
        """Apply a modification to an existing structure.
        
        Args:
            structure: The base structure to modify
            modification: The modification to apply
            
        Returns:
            A new Structure object with the modification applied
            
        Raises:
            StructureGenerationError: If modification fails
        """
        pass
    
    @abstractmethod
    def get_structure_variants(self, base_structure: 'Structure') -> List['Structure']:
        """Generate alternative structural configurations.
        
        Args:
            base_structure: The base structure to generate variants from
            
        Returns:
            List of alternative Structure objects
        """
        pass


class VariableAssigner(ABC):
    """Abstract base class for variable assignment components."""
    
    @abstractmethod
    def assign_variables(self, structure: 'Structure', strategy: str = "random") -> 'VariableAssignment':
        """Assign values to all variables in the structure.
        
        Args:
            structure: The structure containing variables to assign
            strategy: Assignment strategy ("random", "systematic", "heuristic")
            
        Returns:
            A VariableAssignment object with all variables assigned
            
        Raises:
            VariableAssignmentError: If assignment fails
        """
        pass
    
    @abstractmethod
    def modify_assignment(self, assignment: 'VariableAssignment', variable: str, value: Any) -> 'VariableAssignment':
        """Modify a specific variable assignment.
        
        Args:
            assignment: The current variable assignment
            variable: Name of the variable to modify
            value: New value for the variable
            
        Returns:
            A new VariableAssignment with the modified value
            
        Raises:
            VariableAssignmentError: If modification fails
        """
        pass
    
    @abstractmethod
    def get_assignment_space(self, structure: 'Structure') -> 'AssignmentSpace':
        """Return the space of possible assignments for a structure.
        
        Args:
            structure: The structure to analyze
            
        Returns:
            An AssignmentSpace describing possible assignments
        """
        pass


class ConstraintEvaluator(ABC):
    """Abstract base class for constraint evaluation components."""
    
    @abstractmethod
    def evaluate(self, design_object: 'DesignObject') -> EvaluationResult:
        """Evaluate all constraints against a design object.
        
        Args:
            design_object: The design object to evaluate
            
        Returns:
            An EvaluationResult containing evaluation details
        """
        pass
    
    @abstractmethod
    def evaluate_constraint(self, constraint: 'Constraint', design_object: 'DesignObject') -> bool:
        """Evaluate a single constraint.
        
        Args:
            constraint: The constraint to evaluate
            design_object: The design object to evaluate against
            
        Returns:
            True if constraint is satisfied, False otherwise
        """
        pass
    
    @abstractmethod
    def get_violations(self, design_object: 'DesignObject') -> List['ConstraintViolation']:
        """Return detailed information about constraint violations.
        
        Args:
            design_object: The design object to check
            
        Returns:
            List of ConstraintViolation objects describing violations
        """
        pass


class SchemaValidator(ABC):
    """Abstract base class for schema validation components."""
    
    @abstractmethod
    def __init__(self, schema: Dict[str, Any]):
        """Initialize with JSON schema definition.
        
        Args:
            schema: JSON schema dictionary
        """
        pass
    
    @abstractmethod
    def validate(self, design_object: Dict[str, Any]) -> ValidationResult:
        """Validate design object against schema.
        
        Args:
            design_object: Design object as dictionary
            
        Returns:
            ValidationResult containing validation details
        """
        pass
    
    @abstractmethod
    def get_schema_errors(self, design_object: Dict[str, Any]) -> List[SchemaError]:
        """Return detailed schema validation errors.
        
        Args:
            design_object: Design object as dictionary
            
        Returns:
            List of SchemaError objects describing validation errors
        """
        pass