"""Structure model for the SEP solver."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .constraint_set import StructuralConstraint


@dataclass
class Component:
    """Represents a component in the design structure."""
    
    id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type,
            "properties": self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        """Create from dictionary representation."""
        return cls(
            id=data["id"],
            type=data["type"],
            properties=data.get("properties", {})
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((self.id, self.type))


@dataclass
class Relationship:
    """Represents a relationship between components."""
    
    id: str
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "properties": self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Relationship':
        """Create from dictionary representation."""
        return cls(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            type=data["type"],
            properties=data.get("properties", {})
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((self.id, self.source_id, self.target_id, self.type))



@dataclass
class Structure:
    """Represents the structural configuration of components and relationships."""
    
    components: List[Component] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    structural_constraints: List['StructuralConstraint'] = field(default_factory=list)
    
    def add_component(self, component: Component) -> None:
        """Add a component to the structure.
        
        Args:
            component: Component to add
            
        Raises:
            ValueError: If component with same ID already exists
        """
        if any(c.id == component.id for c in self.components):
            raise ValueError(f"Component with ID '{component.id}' already exists")
        self.components.append(component)
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship between components.
        
        Args:
            relationship: Relationship to add
            
        Raises:
            ValueError: If relationship references non-existent components
        """
        component_ids = {c.id for c in self.components}
        if relationship.source_id not in component_ids:
            raise ValueError(f"Source component '{relationship.source_id}' not found")
        if relationship.target_id not in component_ids:
            raise ValueError(f"Target component '{relationship.target_id}' not found")
        
        self.relationships.append(relationship)
    
    def remove_component(self, component_id: str) -> None:
        """Remove a component and all its relationships.
        
        Args:
            component_id: ID of component to remove
        """
        # Remove the component
        self.components = [c for c in self.components if c.id != component_id]
        
        # Remove relationships involving this component
        self.relationships = [r for r in self.relationships 
                            if r.source_id != component_id and r.target_id != component_id]
    
    def get_component(self, component_id: str) -> Optional[Component]:
        """Get a component by ID.
        
        Args:
            component_id: ID of component to find
            
        Returns:
            Component if found, None otherwise
        """
        for component in self.components:
            if component.id == component_id:
                return component
        return None
    
    def get_relationships_for_component(self, component_id: str) -> List[Relationship]:
        """Get all relationships involving a component.
        
        Args:
            component_id: ID of component
            
        Returns:
            List of relationships involving the component
        """
        return [r for r in self.relationships 
                if r.source_id == component_id or r.target_id == component_id]
    
    def is_valid(self) -> bool:
        """Check if structure satisfies structural constraints.
        
        Returns:
            True if all structural constraints are satisfied
        """
        return len(self.get_validation_errors()) == 0
    
    def get_validation_errors(self) -> List[str]:
        """Get detailed validation errors for the structure.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check that all relationships reference existing components
        component_ids = {c.id for c in self.components}
        for relationship in self.relationships:
            if relationship.source_id not in component_ids:
                errors.append(f"Relationship '{relationship.id}' references non-existent source component '{relationship.source_id}'")
            if relationship.target_id not in component_ids:
                errors.append(f"Relationship '{relationship.id}' references non-existent target component '{relationship.target_id}'")
        
        # Check for duplicate component IDs
        seen_ids = set()
        for component in self.components:
            if component.id in seen_ids:
                errors.append(f"Duplicate component ID '{component.id}' found")
            seen_ids.add(component.id)
        
        # Check for duplicate relationship IDs
        seen_rel_ids = set()
        for relationship in self.relationships:
            if relationship.id in seen_rel_ids:
                errors.append(f"Duplicate relationship ID '{relationship.id}' found")
            seen_rel_ids.add(relationship.id)
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "components": [c.to_dict() for c in self.components],
            "relationships": [r.to_dict() for r in self.relationships],
            "structural_constraints": len(self.structural_constraints)  # Simplified for now
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Structure':
        """Create from dictionary representation."""
        components = [Component.from_dict(c) for c in data.get("components", [])]
        relationships = [Relationship.from_dict(r) for r in data.get("relationships", [])]
        
        return cls(
            components=components,
            relationships=relationships,
            structural_constraints=[]  # Will be populated later
        )
    
    def __eq__(self, other) -> bool:
        """Check equality with another structure."""
        if not isinstance(other, Structure):
            return False
        return (set(self.components) == set(other.components) and
                set(self.relationships) == set(other.relationships))
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((tuple(sorted(self.components, key=lambda c: c.id)),
                    tuple(sorted(self.relationships, key=lambda r: r.id))))
    
    def __str__(self) -> str:
        """String representation."""
        return f"Structure(components={len(self.components)}, relationships={len(self.relationships)})"


class Modification(ABC):
    """Abstract base class for structure modifications."""
    
    @abstractmethod
    def apply(self, structure: Structure) -> Structure:
        """Apply the modification to a structure.
        
        Args:
            structure: Structure to modify
            
        Returns:
            New Structure with modification applied
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get a description of the modification."""
        pass


class AddComponentModification(Modification):
    """Modification that adds a component to the structure."""
    
    def __init__(self, component: Component):
        self.component = component
    
    def apply(self, structure: Structure) -> Structure:
        """Apply the modification."""
        new_structure = Structure(
            components=structure.components.copy(),
            relationships=structure.relationships.copy(),
            structural_constraints=structure.structural_constraints.copy()
        )
        new_structure.add_component(self.component)
        return new_structure
    
    def get_description(self) -> str:
        """Get description."""
        return f"Add component {self.component.id} of type {self.component.type}"


class RemoveComponentModification(Modification):
    """Modification that removes a component from the structure."""
    
    def __init__(self, component_id: str):
        self.component_id = component_id
    
    def apply(self, structure: Structure) -> Structure:
        """Apply the modification."""
        new_structure = Structure(
            components=structure.components.copy(),
            relationships=structure.relationships.copy(),
            structural_constraints=structure.structural_constraints.copy()
        )
        new_structure.remove_component(self.component_id)
        return new_structure
    
    def get_description(self) -> str:
        """Get description."""
        return f"Remove component {self.component_id}"


class AddRelationshipModification(Modification):
    """Modification that adds a relationship to the structure."""
    
    def __init__(self, relationship: Relationship):
        self.relationship = relationship
    
    def apply(self, structure: Structure) -> Structure:
        """Apply the modification."""
        new_structure = Structure(
            components=structure.components.copy(),
            relationships=structure.relationships.copy(),
            structural_constraints=structure.structural_constraints.copy()
        )
        new_structure.add_relationship(self.relationship)
        return new_structure
    
    def get_description(self) -> str:
        """Get description."""
        return f"Add relationship {self.relationship.id} from {self.relationship.source_id} to {self.relationship.target_id}"


class RemoveRelationshipModification(Modification):
    """Modification that removes a relationship from the structure."""
    
    def __init__(self, relationship_id: str):
        self.relationship_id = relationship_id
    
    def apply(self, structure: Structure) -> Structure:
        """Apply the modification."""
        new_structure = Structure(
            components=structure.components.copy(),
            relationships=[r for r in structure.relationships if r.id != self.relationship_id],
            structural_constraints=structure.structural_constraints.copy()
        )
        return new_structure
    
    def get_description(self) -> str:
        """Get description."""
        return f"Remove relationship {self.relationship_id}"


class ModifyComponentPropertiesModification(Modification):
    """Modification that changes properties of an existing component."""
    
    def __init__(self, component_id: str, new_properties: Dict[str, Any]):
        self.component_id = component_id
        self.new_properties = new_properties
    
    def apply(self, structure: Structure) -> Structure:
        """Apply the modification."""
        new_structure = Structure(
            components=[],
            relationships=structure.relationships.copy(),
            structural_constraints=structure.structural_constraints.copy()
        )
        
        # Copy components, modifying the target component
        for component in structure.components:
            if component.id == self.component_id:
                modified_component = Component(
                    id=component.id,
                    type=component.type,
                    properties=self.new_properties.copy()
                )
                new_structure.components.append(modified_component)
            else:
                new_structure.components.append(Component(
                    id=component.id,
                    type=component.type,
                    properties=component.properties.copy()
                ))
        
        return new_structure
    
    def get_description(self) -> str:
        """Get description."""
        return f"Modify properties of component {self.component_id}"


class ModifyRelationshipPropertiesModification(Modification):
    """Modification that changes properties of an existing relationship."""
    
    def __init__(self, relationship_id: str, new_properties: Dict[str, Any]):
        self.relationship_id = relationship_id
        self.new_properties = new_properties
    
    def apply(self, structure: Structure) -> Structure:
        """Apply the modification."""
        new_structure = Structure(
            components=structure.components.copy(),
            relationships=[],
            structural_constraints=structure.structural_constraints.copy()
        )
        
        # Copy relationships, modifying the target relationship
        for relationship in structure.relationships:
            if relationship.id == self.relationship_id:
                modified_relationship = Relationship(
                    id=relationship.id,
                    source_id=relationship.source_id,
                    target_id=relationship.target_id,
                    type=relationship.type,
                    properties=self.new_properties.copy()
                )
                new_structure.relationships.append(modified_relationship)
            else:
                new_structure.relationships.append(Relationship(
                    id=relationship.id,
                    source_id=relationship.source_id,
                    target_id=relationship.target_id,
                    type=relationship.type,
                    properties=relationship.properties.copy()
                ))
        
        return new_structure
    
    def get_description(self) -> str:
        """Get description."""
        return f"Modify properties of relationship {self.relationship_id}"


class ChangeComponentTypeModification(Modification):
    """Modification that changes the type of an existing component."""
    
    def __init__(self, component_id: str, new_type: str):
        self.component_id = component_id
        self.new_type = new_type
    
    def apply(self, structure: Structure) -> Structure:
        """Apply the modification."""
        new_structure = Structure(
            components=[],
            relationships=structure.relationships.copy(),
            structural_constraints=structure.structural_constraints.copy()
        )
        
        # Copy components, changing the type of the target component
        for component in structure.components:
            if component.id == self.component_id:
                modified_component = Component(
                    id=component.id,
                    type=self.new_type,
                    properties=component.properties.copy()
                )
                new_structure.components.append(modified_component)
            else:
                new_structure.components.append(Component(
                    id=component.id,
                    type=component.type,
                    properties=component.properties.copy()
                ))
        
        return new_structure
    
    def get_description(self) -> str:
        """Get description."""
        return f"Change component {self.component_id} type to {self.new_type}"