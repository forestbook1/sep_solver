"""Design object model for the SEP solver."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, TYPE_CHECKING
import json

if TYPE_CHECKING:
    from .structure import Structure
    from .variable_assignment import VariableAssignment
    from ..core.interfaces import SchemaValidator
    from ..core.results import ValidationResult


@dataclass
class DesignObject:
    """Represents a complete design with structure and variable assignments.
    
    A DesignObject is the core data structure that represents a complete design
    configuration including both structural elements and variable assignments.
    """
    
    id: str
    structure: 'Structure'
    variables: 'VariableAssignment'
    metadata: Dict[str, Any]
    
    def to_json(self) -> Dict[str, Any]:
        """Serialize to JSON format.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "id": self.id,
            "structure": self.structure.to_dict(),
            "variables": self.variables.to_dict(),
            "metadata": self.metadata
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary format (alias for to_json).
        
        Returns:
            Dictionary representation
        """
        return self.to_json()
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'DesignObject':
        """Deserialize from JSON format.
        
        Args:
            data: Dictionary containing design object data
            
        Returns:
            DesignObject instance
            
        Raises:
            ValueError: If data is invalid
        """
        from .structure import Structure
        from .variable_assignment import VariableAssignment
        
        try:
            return cls(
                id=data["id"],
                structure=Structure.from_dict(data["structure"]),
                variables=VariableAssignment.from_dict(data["variables"]),
                metadata=data.get("metadata", {})
            )
        except KeyError as e:
            raise ValueError(f"Missing required field in design object: {e}")
        except Exception as e:
            raise ValueError(f"Invalid design object data: {e}")
    
    def validate_schema(self, validator: 'SchemaValidator') -> 'ValidationResult':
        """Validate against JSON schema.
        
        Args:
            validator: Schema validator instance
            
        Returns:
            ValidationResult indicating success or failure
        """
        return validator.validate(self.to_json())
    
    def to_json_string(self, indent: Optional[int] = None) -> str:
        """Convert to JSON string.
        
        Args:
            indent: Optional indentation for pretty printing
            
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_json(), indent=indent)
    
    @classmethod
    def from_json_string(cls, json_str: str) -> 'DesignObject':
        """Create from JSON string.
        
        Args:
            json_str: JSON string representation
            
        Returns:
            DesignObject instance
            
        Raises:
            ValueError: If JSON is invalid
        """
        try:
            data = json.loads(json_str)
            return cls.from_json(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    def copy(self) -> 'DesignObject':
        """Create a deep copy of the design object.
        
        Returns:
            New DesignObject instance with copied data
        """
        import copy
        return DesignObject(
            id=self.id,
            structure=self.structure.from_dict(self.structure.to_dict()),
            variables=self.variables.copy(),
            metadata=copy.deepcopy(self.metadata)
        )
    
    def __eq__(self, other) -> bool:
        """Check equality with another design object."""
        if not isinstance(other, DesignObject):
            return False
        return (self.id == other.id and 
                self.structure == other.structure and
                self.variables == other.variables and
                self.metadata == other.metadata)
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((self.id, hash(self.structure), hash(self.variables)))
    
    def __str__(self) -> str:
        """String representation."""
        return f"DesignObject(id='{self.id}', components={len(self.structure.components)}, variables={len(self.variables.assignments)})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"DesignObject(id='{self.id}', structure={self.structure}, variables={self.variables}, metadata={self.metadata})"