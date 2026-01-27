"""Variable assignment model for the SEP solver."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, Set
from abc import ABC, abstractmethod


@dataclass
class Domain:
    """Represents the domain of possible values for a variable."""
    
    name: str
    type: str  # "int", "float", "string", "bool", "enum", "range"
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid_value(self, value: Any) -> bool:
        """Check if a value is valid for this domain.
        
        Args:
            value: Value to check
            
        Returns:
            True if value is valid for this domain
        """
        # Basic type checking
        if self.type == "int" and not isinstance(value, int):
            return False
        elif self.type == "float" and not isinstance(value, (int, float)):
            return False
        elif self.type == "string" and not isinstance(value, str):
            return False
        elif self.type == "bool" and not isinstance(value, bool):
            return False
        
        # Check constraints
        if self.type == "enum":
            allowed_values = self.constraints.get("values", [])
            return value in allowed_values
        elif self.type in ["int", "float", "range"]:
            min_val = self.constraints.get("min")
            max_val = self.constraints.get("max")
            if min_val is not None and value < min_val:
                return False
            if max_val is not None and value > max_val:
                return False
        
        return True
    
    def get_sample_value(self) -> Any:
        """Get a sample valid value from this domain.
        
        Returns:
            A valid value from this domain
        """
        if self.type == "int":
            min_val = self.constraints.get("min", 0)
            max_val = self.constraints.get("max", 100)
            return min_val
        elif self.type == "float":
            min_val = self.constraints.get("min", 0.0)
            max_val = self.constraints.get("max", 1.0)
            return min_val
        elif self.type == "string":
            return self.constraints.get("default", "")
        elif self.type == "bool":
            return False
        elif self.type == "enum":
            values = self.constraints.get("values", [])
            return values[0] if values else None
        elif self.type == "range":
            min_val = self.constraints.get("min", 0)
            return min_val
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.type,
            "constraints": self.constraints
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Domain':
        """Create from dictionary representation."""
        return cls(
            name=data["name"],
            type=data["type"],
            constraints=data.get("constraints", {})
        )


@dataclass
class VariableAssignment:
    """Represents variable assignments within a structure."""
    
    assignments: Dict[str, Any] = field(default_factory=dict)
    domains: Dict[str, Domain] = field(default_factory=dict)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable value.
        
        Args:
            name: Variable name
            value: Variable value
            
        Raises:
            ValueError: If value is invalid for the variable's domain
        """
        if name in self.domains:
            domain = self.domains[name]
            if not domain.is_valid_value(value):
                raise ValueError(f"Value {value} is not valid for domain {domain.name}")
        
        self.assignments[name] = value
    
    def get_variable(self, name: str) -> Any:
        """Get a variable value.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value
            
        Raises:
            KeyError: If variable is not assigned
        """
        return self.assignments[name]
    
    def has_variable(self, name: str) -> bool:
        """Check if a variable is assigned.
        
        Args:
            name: Variable name
            
        Returns:
            True if variable is assigned
        """
        return name in self.assignments
    
    def add_domain(self, domain: Domain) -> None:
        """Add a domain for a variable.
        
        Args:
            domain: Domain to add
        """
        self.domains[domain.name] = domain
    
    def add_dependency(self, variable: str, depends_on: List[str]) -> None:
        """Add dependency relationships for a variable.
        
        Args:
            variable: Variable that has dependencies
            depends_on: List of variables this variable depends on
        """
        self.dependencies[variable] = depends_on
    
    def get_unassigned_variables(self) -> Set[str]:
        """Get variables that have domains but are not assigned.
        
        Returns:
            Set of unassigned variable names
        """
        return set(self.domains.keys()) - set(self.assignments.keys())
    
    def is_consistent(self) -> bool:
        """Check if assignments satisfy dependencies.
        
        Returns:
            True if all dependencies are satisfied
        """
        for variable, deps in self.dependencies.items():
            if variable in self.assignments:
                # Check that all dependencies are satisfied
                for dep in deps:
                    if dep not in self.assignments:
                        return False
                    # Additional dependency logic would go here
        return True
    
    def is_complete(self) -> bool:
        """Check if all variables with domains are assigned.
        
        Returns:
            True if all variables are assigned
        """
        return len(self.get_unassigned_variables()) == 0
    
    def validate_all_assignments(self) -> List[str]:
        """Validate all assignments against their domains.
        
        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []
        for name, value in self.assignments.items():
            if name in self.domains:
                domain = self.domains[name]
                if not domain.is_valid_value(value):
                    errors.append(f"Variable '{name}' has invalid value {value} for domain {domain.type}")
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "assignments": self.assignments,
            "domains": {name: domain.to_dict() for name, domain in self.domains.items()},
            "dependencies": self.dependencies
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VariableAssignment':
        """Create from dictionary representation."""
        domains = {name: Domain.from_dict(domain_data) 
                  for name, domain_data in data.get("domains", {}).items()}
        
        return cls(
            assignments=dict(data.get("assignments", {})),  # Create new dict
            domains=domains,
            dependencies={k: list(v) for k, v in data.get("dependencies", {}).items()}  # Create new dict with new lists
        )
    
    def copy(self) -> 'VariableAssignment':
        """Create a copy of the variable assignment.
        
        Returns:
            New VariableAssignment with copied data
        """
        return self.from_dict(self.to_dict())
    
    def __eq__(self, other) -> bool:
        """Check equality with another variable assignment."""
        if not isinstance(other, VariableAssignment):
            return False
        return (self.assignments == other.assignments and
                self.domains == other.domains and
                self.dependencies == other.dependencies)
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((tuple(sorted(self.assignments.items())),
                    tuple(sorted(self.domains.keys()))))
    
    def __str__(self) -> str:
        """String representation."""
        return f"VariableAssignment(assigned={len(self.assignments)}, domains={len(self.domains)})"


class AssignmentSpace:
    """Represents the space of possible assignments for a structure."""
    
    def __init__(self, domains: Dict[str, Domain], dependencies: Dict[str, List[str]] = None):
        self.domains = domains
        self.dependencies = dependencies or {}
    
    def get_variable_count(self) -> int:
        """Get the number of variables in the assignment space."""
        return len(self.domains)
    
    def get_domain_size(self, variable: str) -> Optional[int]:
        """Get the size of a variable's domain (if finite).
        
        Args:
            variable: Variable name
            
        Returns:
            Domain size or None if infinite/unknown
        """
        if variable not in self.domains:
            return None
        
        domain = self.domains[variable]
        if domain.type == "enum":
            values = domain.constraints.get("values", [])
            return len(values)
        elif domain.type == "bool":
            return 2
        elif domain.type in ["int", "range"]:
            min_val = domain.constraints.get("min")
            max_val = domain.constraints.get("max")
            if min_val is not None and max_val is not None:
                return max_val - min_val + 1
        
        return None  # Infinite or unknown size
    
    def estimate_total_combinations(self) -> Optional[int]:
        """Estimate total number of possible assignments.
        
        Returns:
            Estimated number of combinations or None if infinite
        """
        total = 1
        for variable in self.domains:
            size = self.get_domain_size(variable)
            if size is None:
                return None  # At least one infinite domain
            total *= size
        return total