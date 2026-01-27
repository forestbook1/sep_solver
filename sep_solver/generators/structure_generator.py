"""Base structure generator implementation."""

import random
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from ..core.interfaces import StructureGenerator
from ..core.exceptions import StructureGenerationError

if TYPE_CHECKING:
    from ..models.structure import Structure, Modification, Component, Relationship
    from ..models.constraint_set import Constraint, StructuralConstraint


class BaseStructureGenerator(StructureGenerator):
    """Base implementation of structure generator with random generation capabilities.
    
    This implementation provides basic random structure generation that creates
    valid structural configurations with components and relationships while
    respecting structural constraints.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the base structure generator.
        
        Args:
            seed: Optional random seed for reproducible generation
        """
        self.random = random.Random(seed)
        self.component_types = ["processor", "memory", "storage", "network", "sensor", "actuator"]
        self.relationship_types = ["connects_to", "depends_on", "controls", "monitors"]
    
    def generate_structure(self, constraints: List['Constraint']) -> 'Structure':
        """Generate a valid structure satisfying structural constraints.
        
        Args:
            constraints: List of structural constraints to satisfy
            
        Returns:
            A valid Structure object
            
        Raises:
            StructureGenerationError: If structure generation fails
        """
        from ..models.structure import Structure, Component, Relationship
        from ..models.constraint_set import StructuralConstraint
        
        try:
            # Filter structural constraints
            structural_constraints = [c for c in constraints if isinstance(c, StructuralConstraint)]
            
            # Determine component count based on constraints
            min_components, max_components = self._get_component_bounds(structural_constraints)
            
            # Generate random number of components within bounds
            num_components = self.random.randint(min_components, max_components)
            
            # Create structure
            structure = Structure()
            
            # Generate components
            for i in range(num_components):
                component = self._generate_random_component(f"comp_{i}")
                structure.add_component(component)
            
            # Generate relationships between components
            if len(structure.components) > 1:
                num_relationships = self.random.randint(1, min(len(structure.components) * 2, 10))
                for i in range(num_relationships):
                    relationship = self._generate_random_relationship(f"rel_{i}", structure.components)
                    if relationship:
                        structure.add_relationship(relationship)
            
            # Add structural constraints to the structure
            structure.structural_constraints = structural_constraints
            
            # Validate the generated structure
            if not structure.is_valid():
                errors = structure.get_validation_errors()
                raise StructureGenerationError(f"Generated invalid structure: {'; '.join(errors)}")
            
            # Check if structure satisfies all structural constraints
            self._validate_against_constraints(structure, structural_constraints)
            
            return structure
            
        except Exception as e:
            if isinstance(e, StructureGenerationError):
                raise
            raise StructureGenerationError(f"Failed to generate structure: {str(e)}")
    
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
        try:
            # Apply the modification
            modified_structure = modification.apply(structure)
            
            # Validate the modified structure
            if not modified_structure.is_valid():
                errors = modified_structure.get_validation_errors()
                raise StructureGenerationError(f"Modification resulted in invalid structure: {'; '.join(errors)}")
            
            return modified_structure
            
        except Exception as e:
            if isinstance(e, StructureGenerationError):
                raise
            raise StructureGenerationError(f"Failed to modify structure: {str(e)}")
    
    def get_structure_variants(self, base_structure: 'Structure') -> List['Structure']:
        """Generate alternative structural configurations.
        
        Args:
            base_structure: The base structure to generate variants from
            
        Returns:
            List of alternative Structure objects
        """
        from ..models.structure import (
            AddComponentModification, RemoveComponentModification, 
            AddRelationshipModification, RemoveRelationshipModification,
            ModifyComponentPropertiesModification, ChangeComponentTypeModification,
            Component, Relationship
        )
        
        variants = []
        
        try:
            # Variant 1: Add a random component
            if len(base_structure.components) < 10:  # Reasonable upper limit
                new_component = self._generate_random_component(f"variant_comp_{len(base_structure.components)}")
                add_mod = AddComponentModification(new_component)
                try:
                    variant = self.modify_structure(base_structure, add_mod)
                    variants.append(variant)
                except StructureGenerationError:
                    pass  # Skip this variant if it fails
            
            # Variant 2: Remove a component (if we have more than 1)
            if len(base_structure.components) > 1:
                component_to_remove = self.random.choice(base_structure.components)
                remove_mod = RemoveComponentModification(component_to_remove.id)
                try:
                    variant = self.modify_structure(base_structure, remove_mod)
                    variants.append(variant)
                except StructureGenerationError:
                    pass  # Skip this variant if it fails
            
            # Variant 3: Add a new relationship (if we have at least 2 components)
            if len(base_structure.components) >= 2:
                # Find two components that aren't already connected
                available_pairs = []
                for source in base_structure.components:
                    for target in base_structure.components:
                        if source.id != target.id:
                            # Check if relationship already exists
                            existing = any(r.source_id == source.id and r.target_id == target.id 
                                         for r in base_structure.relationships)
                            if not existing:
                                available_pairs.append((source, target))
                
                if available_pairs:
                    source, target = self.random.choice(available_pairs)
                    new_relationship = self._generate_random_relationship(
                        f"variant_rel_{len(base_structure.relationships)}", 
                        [source, target]
                    )
                    if new_relationship:
                        add_rel_mod = AddRelationshipModification(new_relationship)
                        try:
                            variant = self.modify_structure(base_structure, add_rel_mod)
                            variants.append(variant)
                        except StructureGenerationError:
                            pass
            
            # Variant 4: Remove a relationship (if we have any)
            if base_structure.relationships:
                relationship_to_remove = self.random.choice(base_structure.relationships)
                remove_rel_mod = RemoveRelationshipModification(relationship_to_remove.id)
                try:
                    variant = self.modify_structure(base_structure, remove_rel_mod)
                    variants.append(variant)
                except StructureGenerationError:
                    pass
            
            # Variant 5: Modify component properties
            if base_structure.components:
                component_to_modify = self.random.choice(base_structure.components)
                new_properties = component_to_modify.properties.copy()
                new_properties["variant_property"] = self.random.randint(1, 100)
                new_properties["modified_at"] = "variant_generation"
                
                modify_props_mod = ModifyComponentPropertiesModification(
                    component_to_modify.id, new_properties
                )
                try:
                    variant = self.modify_structure(base_structure, modify_props_mod)
                    variants.append(variant)
                except StructureGenerationError:
                    pass
            
            # Variant 6: Change component type
            if base_structure.components:
                component_to_change = self.random.choice(base_structure.components)
                # Choose a different type
                available_types = [t for t in self.component_types if t != component_to_change.type]
                if available_types:
                    new_type = self.random.choice(available_types)
                    change_type_mod = ChangeComponentTypeModification(component_to_change.id, new_type)
                    try:
                        variant = self.modify_structure(base_structure, change_type_mod)
                        variants.append(variant)
                    except StructureGenerationError:
                        pass
            
        except Exception as e:
            # If variant generation fails, return what we have so far
            pass
        
        return variants
    
    def _get_component_bounds(self, constraints: List['StructuralConstraint']) -> tuple[int, int]:
        """Extract component count bounds from constraints.
        
        Args:
            constraints: List of structural constraints
            
        Returns:
            Tuple of (min_components, max_components)
        """
        min_components = 1  # Default minimum
        max_components = 5  # Default maximum
        
        # Track if we found any explicit constraints
        found_min_constraint = False
        found_max_constraint = False
        
        for constraint in constraints:
            # Check for component count constraints
            if hasattr(constraint, 'min_components'):
                min_components = max(min_components, constraint.min_components)
                found_min_constraint = True
            if hasattr(constraint, 'max_components') and constraint.max_components is not None:
                if found_max_constraint:
                    max_components = min(max_components, constraint.max_components)
                else:
                    max_components = constraint.max_components
                    found_max_constraint = True
        
        # Ensure min <= max
        if min_components > max_components:
            max_components = min_components
        
        return min_components, max_components
    
    def _generate_random_component(self, component_id: str) -> 'Component':
        """Generate a random component.
        
        Args:
            component_id: ID for the component
            
        Returns:
            A randomly generated Component
        """
        from ..models.structure import Component
        
        component_type = self.random.choice(self.component_types)
        properties = {
            "capacity": self.random.randint(1, 100),
            "priority": self.random.choice(["low", "medium", "high"]),
            "active": self.random.choice([True, False])
        }
        
        return Component(
            id=component_id,
            type=component_type,
            properties=properties
        )
    
    def _generate_random_relationship(self, relationship_id: str, components: List['Component']) -> Optional['Relationship']:
        """Generate a random relationship between components.
        
        Args:
            relationship_id: ID for the relationship
            components: List of available components
            
        Returns:
            A randomly generated Relationship, or None if generation fails
        """
        from ..models.structure import Relationship
        
        if len(components) < 2:
            return None
        
        # Select two different components
        source = self.random.choice(components)
        target = self.random.choice([c for c in components if c.id != source.id])
        
        relationship_type = self.random.choice(self.relationship_types)
        properties = {
            "strength": self.random.uniform(0.1, 1.0),
            "bidirectional": self.random.choice([True, False])
        }
        
        return Relationship(
            id=relationship_id,
            source_id=source.id,
            target_id=target.id,
            type=relationship_type,
            properties=properties
        )
    
    def _validate_against_constraints(self, structure: 'Structure', constraints: List['StructuralConstraint']) -> None:
        """Validate structure against structural constraints.
        
        Args:
            structure: Structure to validate
            constraints: List of structural constraints
            
        Raises:
            StructureGenerationError: If any constraint is violated
        """
        # Create a dummy design object for constraint checking
        # This is a simplified approach - in practice we'd need a proper design object
        from ..models.design_object import DesignObject
        from ..models.variable_assignment import VariableAssignment
        
        try:
            # Create minimal design object for constraint validation
            design_object = DesignObject(
                id="temp_validation",
                structure=structure,
                variables=VariableAssignment(),
                metadata={}
            )
            
            for constraint in constraints:
                if not constraint.is_satisfied(design_object):
                    violation_msg = constraint.get_violation_message(design_object)
                    raise StructureGenerationError(f"Constraint violation: {violation_msg}")
                    
        except ImportError:
            # If design object classes aren't available yet, skip constraint validation
            # This allows the structure generator to work independently
            pass
    
    def _create_structure_copy(self, structure: 'Structure') -> 'Structure':
        """Create a deep copy of a structure.
        
        Args:
            structure: Structure to copy
            
        Returns:
            A copy of the structure
        """
        from ..models.structure import Structure, Component, Relationship
        
        # Copy components
        new_components = []
        for comp in structure.components:
            new_comp = Component(
                id=comp.id,
                type=comp.type,
                properties=comp.properties.copy()
            )
            new_components.append(new_comp)
        
        # Copy relationships
        new_relationships = []
        for rel in structure.relationships:
            new_rel = Relationship(
                id=rel.id,
                source_id=rel.source_id,
                target_id=rel.target_id,
                type=rel.type,
                properties=rel.properties.copy()
            )
            new_relationships.append(new_rel)
        
        # Create new structure
        new_structure = Structure(
            components=new_components,
            relationships=new_relationships,
            structural_constraints=structure.structural_constraints.copy()
        )
        
        return new_structure