"""Constraint set model for the SEP solver."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .design_object import DesignObject


class Constraint(ABC):
    """Abstract base class for all constraints."""
    
    def __init__(self, constraint_id: str, description: str = ""):
        self.constraint_id = constraint_id
        self.description = description
    
    @abstractmethod
    def is_satisfied(self, design_object: 'DesignObject') -> bool:
        """Check if the constraint is satisfied by a design object.
        
        Args:
            design_object: Design object to check
            
        Returns:
            True if constraint is satisfied
        """
        pass
    
    @abstractmethod
    def get_violation_message(self, design_object: 'DesignObject') -> str:
        """Get a message describing why the constraint is violated.
        
        Args:
            design_object: Design object that violates the constraint
            
        Returns:
            Human-readable violation message
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.constraint_id}')"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.constraint_id}', description='{self.description}')"


class StructuralConstraint(Constraint):
    """Base class for constraints on structure."""
    pass


class VariableConstraint(Constraint):
    """Base class for constraints on variables."""
    pass


class GlobalConstraint(Constraint):
    """Base class for constraints that span structure and variables."""
    pass


@dataclass
class ConstraintViolation:
    """Represents a constraint violation with detailed information."""
    
    constraint_id: str
    constraint_type: str
    message: str
    severity: str = "error"  # "error", "warning", "info"
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.constraint_type} '{self.constraint_id}': {self.message}"


@dataclass
class ConstraintSet:
    """Collection of constraints that must be satisfied."""
    
    structural_constraints: List[StructuralConstraint] = field(default_factory=list)
    variable_constraints: List[VariableConstraint] = field(default_factory=list)
    global_constraints: List[GlobalConstraint] = field(default_factory=list)
    
    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the set.
        
        Args:
            constraint: Constraint to add
            
        Raises:
            ValueError: If constraint type is not recognized
        """
        if isinstance(constraint, StructuralConstraint):
            self.structural_constraints.append(constraint)
        elif isinstance(constraint, VariableConstraint):
            self.variable_constraints.append(constraint)
        elif isinstance(constraint, GlobalConstraint):
            self.global_constraints.append(constraint)
        else:
            raise ValueError(f"Unknown constraint type: {type(constraint)}")
    
    def remove_constraint(self, constraint_id: str) -> bool:
        """Remove a constraint by ID.
        
        Args:
            constraint_id: ID of constraint to remove
            
        Returns:
            True if constraint was found and removed
        """
        for constraint_list in [self.structural_constraints, self.variable_constraints, self.global_constraints]:
            for i, constraint in enumerate(constraint_list):
                if constraint.constraint_id == constraint_id:
                    constraint_list.pop(i)
                    return True
        return False
    
    def get_constraint(self, constraint_id: str) -> Optional[Constraint]:
        """Get a constraint by ID.
        
        Args:
            constraint_id: ID of constraint to find
            
        Returns:
            Constraint if found, None otherwise
        """
        for constraint_list in [self.structural_constraints, self.variable_constraints, self.global_constraints]:
            for constraint in constraint_list:
                if constraint.constraint_id == constraint_id:
                    return constraint
        return None
    
    def get_all_constraints(self) -> List[Constraint]:
        """Get all constraints in the set.
        
        Returns:
            List of all constraints
        """
        return (self.structural_constraints + 
                self.variable_constraints + 
                self.global_constraints)
    
    def get_constraints_for_component(self, component_id: str) -> List[Constraint]:
        """Get constraints affecting a specific component.
        
        Args:
            component_id: ID of component
            
        Returns:
            List of constraints affecting the component
        """
        # This is a simplified implementation
        # In practice, constraints would need to specify which components they affect
        relevant_constraints = []
        
        for constraint in self.get_all_constraints():
            # Check if constraint mentions the component in its context
            if hasattr(constraint, 'affected_components'):
                if component_id in constraint.affected_components:
                    relevant_constraints.append(constraint)
        
        return relevant_constraints
    
    def get_constraints_by_type(self, constraint_type: str) -> List[Constraint]:
        """Get constraints of a specific type.
        
        Args:
            constraint_type: Type of constraints to get
            
        Returns:
            List of constraints of the specified type
        """
        if constraint_type == "structural":
            return self.structural_constraints
        elif constraint_type == "variable":
            return self.variable_constraints
        elif constraint_type == "global":
            return self.global_constraints
        else:
            return []
    
    def count_constraints(self) -> Dict[str, int]:
        """Count constraints by type.
        
        Returns:
            Dictionary with constraint counts by type
        """
        return {
            "structural": len(self.structural_constraints),
            "variable": len(self.variable_constraints),
            "global": len(self.global_constraints),
            "total": len(self.get_all_constraints())
        }
    
    def is_empty(self) -> bool:
        """Check if the constraint set is empty.
        
        Returns:
            True if no constraints are defined
        """
        return len(self.get_all_constraints()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the constraint set
        """
        return {
            "structural_constraints": [
                {"id": c.constraint_id, "type": c.__class__.__name__, "description": c.description}
                for c in self.structural_constraints
            ],
            "variable_constraints": [
                {"id": c.constraint_id, "type": c.__class__.__name__, "description": c.description}
                for c in self.variable_constraints
            ],
            "global_constraints": [
                {"id": c.constraint_id, "type": c.__class__.__name__, "description": c.description}
                for c in self.global_constraints
            ]
        }
    
    def __len__(self) -> int:
        """Get total number of constraints."""
        return len(self.get_all_constraints())
    
    def __str__(self) -> str:
        """String representation."""
        counts = self.count_constraints()
        return f"ConstraintSet(structural={counts['structural']}, variable={counts['variable']}, global={counts['global']})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"ConstraintSet(structural_constraints={self.structural_constraints}, variable_constraints={self.variable_constraints}, global_constraints={self.global_constraints})"


# Example constraint implementations for testing

class ComponentCountConstraint(StructuralConstraint):
    """Constraint on the number of components in a structure."""
    
    def __init__(self, constraint_id: str, min_components: int = 0, max_components: int = None):
        super().__init__(constraint_id, f"Component count between {min_components} and {max_components}")
        self.min_components = min_components
        self.max_components = max_components
    
    def is_satisfied(self, design_object) -> bool:
        """Check if component count is within bounds."""
        count = len(design_object.structure.components)
        if count < self.min_components:
            return False
        if self.max_components is not None and count > self.max_components:
            return False
        return True
    
    def get_violation_message(self, design_object) -> str:
        """Get violation message."""
        count = len(design_object.structure.components)
        return f"Component count {count} violates bounds [{self.min_components}, {self.max_components}]"


class VariableRangeConstraint(VariableConstraint):
    """Constraint on variable value ranges."""
    
    def __init__(self, constraint_id: str, variable_name: str, min_value: Any = None, max_value: Any = None):
        super().__init__(constraint_id, f"Variable {variable_name} range constraint")
        self.variable_name = variable_name
        self.min_value = min_value
        self.max_value = max_value
    
    def is_satisfied(self, design_object) -> bool:
        """Check if variable value is within range."""
        if not design_object.variables.has_variable(self.variable_name):
            return False
        
        value = design_object.variables.get_variable(self.variable_name)
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True
    
    def get_violation_message(self, design_object) -> str:
        """Get violation message."""
        if not design_object.variables.has_variable(self.variable_name):
            return f"Variable '{self.variable_name}' is not assigned"
        
        value = design_object.variables.get_variable(self.variable_name)
        return f"Variable '{self.variable_name}' value {value} violates range [{self.min_value}, {self.max_value}]"