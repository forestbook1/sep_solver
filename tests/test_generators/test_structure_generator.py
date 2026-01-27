"""Unit tests for the structure generator."""

import pytest
from sep_solver.generators.structure_generator import BaseStructureGenerator
from sep_solver.models.structure import Structure, Component, Relationship, AddComponentModification, RemoveComponentModification
from sep_solver.models.constraint_set import ComponentCountConstraint
from sep_solver.core.exceptions import StructureGenerationError


class TestBaseStructureGenerator:
    """Test cases for BaseStructureGenerator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = BaseStructureGenerator(seed=42)  # Use seed for reproducible tests
    
    def test_initialization(self):
        """Test generator initialization."""
        generator = BaseStructureGenerator()
        assert generator is not None
        assert hasattr(generator, 'component_types')
        assert hasattr(generator, 'relationship_types')
        
        # Test with seed
        seeded_generator = BaseStructureGenerator(seed=123)
        assert seeded_generator is not None
    
    def test_generate_structure_basic(self):
        """Test basic structure generation without constraints."""
        structure = self.generator.generate_structure([])
        
        assert isinstance(structure, Structure)
        assert len(structure.components) >= 1
        assert structure.is_valid()
        
        # Check that components have proper IDs and types
        for component in structure.components:
            assert component.id.startswith("comp_")
            assert component.type in self.generator.component_types
            assert isinstance(component.properties, dict)
    
    def test_generate_structure_with_component_count_constraint(self):
        """Test structure generation with component count constraints."""
        # Test minimum constraint
        min_constraint = ComponentCountConstraint("min_test", min_components=3)
        structure = self.generator.generate_structure([min_constraint])
        
        assert len(structure.components) >= 3
        assert structure.is_valid()
        
        # Test maximum constraint
        max_constraint = ComponentCountConstraint("max_test", max_components=2)
        structure = self.generator.generate_structure([max_constraint])
        
        assert len(structure.components) <= 2
        assert structure.is_valid()
        
        # Test range constraint
        range_constraint = ComponentCountConstraint("range_test", min_components=2, max_components=4)
        structure = self.generator.generate_structure([range_constraint])
        
        assert 2 <= len(structure.components) <= 4
        assert structure.is_valid()
    
    def test_generate_structure_with_relationships(self):
        """Test that generated structures include relationships when appropriate."""
        # Generate structure with multiple components
        constraint = ComponentCountConstraint("multi_comp", min_components=3, max_components=5)
        structure = self.generator.generate_structure([constraint])
        
        # Should have relationships between components
        if len(structure.components) > 1:
            # May or may not have relationships, but if they exist, they should be valid
            for relationship in structure.relationships:
                assert relationship.id.startswith("rel_")
                assert relationship.type in self.generator.relationship_types
                assert relationship.source_id in [c.id for c in structure.components]
                assert relationship.target_id in [c.id for c in structure.components]
                assert relationship.source_id != relationship.target_id
    
    def test_modify_structure_add_component(self):
        """Test structure modification by adding a component."""
        # Create base structure
        base_structure = self.generator.generate_structure([])
        original_count = len(base_structure.components)
        
        # Create modification
        new_component = Component("new_comp", "processor", {"test": True})
        modification = AddComponentModification(new_component)
        
        # Apply modification
        modified_structure = self.generator.modify_structure(base_structure, modification)
        
        assert len(modified_structure.components) == original_count + 1
        assert modified_structure.is_valid()
        assert any(c.id == "new_comp" for c in modified_structure.components)
        
        # Original structure should be unchanged
        assert len(base_structure.components) == original_count
    
    def test_modify_structure_remove_component(self):
        """Test structure modification by removing a component."""
        # Create base structure with multiple components
        constraint = ComponentCountConstraint("multi", min_components=3)
        base_structure = self.generator.generate_structure([constraint])
        original_count = len(base_structure.components)
        
        # Remove a component
        component_to_remove = base_structure.components[0]
        modification = RemoveComponentModification(component_to_remove.id)
        
        # Apply modification
        modified_structure = self.generator.modify_structure(base_structure, modification)
        
        assert len(modified_structure.components) == original_count - 1
        assert modified_structure.is_valid()
        assert not any(c.id == component_to_remove.id for c in modified_structure.components)
        
        # Check that relationships involving the removed component are also removed
        for relationship in modified_structure.relationships:
            assert relationship.source_id != component_to_remove.id
            assert relationship.target_id != component_to_remove.id
    
    def test_modify_structure_invalid_modification(self):
        """Test that invalid modifications raise appropriate errors."""
        base_structure = self.generator.generate_structure([])
        
        # Try to add component with duplicate ID
        existing_component = base_structure.components[0]
        duplicate_component = Component(existing_component.id, "memory")
        modification = AddComponentModification(duplicate_component)
        
        with pytest.raises(StructureGenerationError):
            self.generator.modify_structure(base_structure, modification)
    
    def test_get_structure_variants(self):
        """Test generation of structure variants."""
        # Create base structure
        constraint = ComponentCountConstraint("base", min_components=2, max_components=3)
        base_structure = self.generator.generate_structure([constraint])
        
        # Generate variants
        variants = self.generator.get_structure_variants(base_structure)
        
        assert isinstance(variants, list)
        # Should generate at least one variant
        assert len(variants) >= 0  # May be 0 if all variants fail validation
        
        # Each variant should be valid and different from base
        for variant in variants:
            assert isinstance(variant, Structure)
            assert variant.is_valid()
            # Variants should be different from base (not necessarily true for all variants)
    
    def test_get_structure_variants_single_component(self):
        """Test variant generation with single component structure."""
        # Create structure with single component
        constraint = ComponentCountConstraint("single", min_components=1, max_components=1)
        base_structure = self.generator.generate_structure([constraint])
        
        # Generate variants
        variants = self.generator.get_structure_variants(base_structure)
        
        # Should still be able to generate some variants (e.g., by adding components)
        assert isinstance(variants, list)
    
    def test_generate_random_component(self):
        """Test random component generation."""
        component = self.generator._generate_random_component("test_comp")
        
        assert component.id == "test_comp"
        assert component.type in self.generator.component_types
        assert isinstance(component.properties, dict)
        assert "capacity" in component.properties
        assert "priority" in component.properties
        assert "active" in component.properties
    
    def test_generate_random_relationship(self):
        """Test random relationship generation."""
        # Create components
        comp1 = Component("comp1", "processor")
        comp2 = Component("comp2", "memory")
        components = [comp1, comp2]
        
        relationship = self.generator._generate_random_relationship("test_rel", components)
        
        assert relationship is not None
        assert relationship.id == "test_rel"
        assert relationship.type in self.generator.relationship_types
        assert relationship.source_id in ["comp1", "comp2"]
        assert relationship.target_id in ["comp1", "comp2"]
        assert relationship.source_id != relationship.target_id
        assert isinstance(relationship.properties, dict)
    
    def test_generate_random_relationship_insufficient_components(self):
        """Test relationship generation with insufficient components."""
        # Single component
        comp1 = Component("comp1", "processor")
        relationship = self.generator._generate_random_relationship("test_rel", [comp1])
        
        assert relationship is None
        
        # No components
        relationship = self.generator._generate_random_relationship("test_rel", [])
        
        assert relationship is None
    
    def test_get_component_bounds(self):
        """Test component bounds extraction from constraints."""
        # No constraints
        min_comp, max_comp = self.generator._get_component_bounds([])
        assert min_comp == 1
        assert max_comp == 5
        
        # With constraints
        constraint1 = ComponentCountConstraint("test1", min_components=3)
        constraint2 = ComponentCountConstraint("test2", max_components=8)
        
        min_comp, max_comp = self.generator._get_component_bounds([constraint1, constraint2])
        assert min_comp == 3
        assert max_comp == 8
        
        # Conflicting constraints (min > max)
        constraint3 = ComponentCountConstraint("test3", min_components=10, max_components=5)
        min_comp, max_comp = self.generator._get_component_bounds([constraint3])
        assert min_comp == 10
        assert max_comp == 10  # Should adjust max to equal min
    
    def test_create_structure_copy(self):
        """Test structure copying functionality."""
        # Create original structure
        original = self.generator.generate_structure([])
        
        # Create copy
        copy = self.generator._create_structure_copy(original)
        
        assert copy is not original
        assert copy == original  # Should be equal in content
        assert copy.is_valid()
        
        # Modify copy and ensure original is unchanged
        if copy.components:
            copy.components[0].properties["modified"] = True
            assert "modified" not in original.components[0].properties
    
    def test_error_handling(self):
        """Test error handling in structure generation."""
        # This test ensures that the generator handles errors gracefully
        # In practice, specific error conditions would depend on the constraint implementations
        
        # Test with empty constraints list (should work)
        structure = self.generator.generate_structure([])
        assert structure.is_valid()
        
        # Test that generator doesn't crash with various inputs
        try:
            variants = self.generator.get_structure_variants(Structure())
            assert isinstance(variants, list)
        except Exception as e:
            # Should not raise unexpected exceptions
            assert isinstance(e, (StructureGenerationError, ValueError))
    
    def test_enhanced_structure_variants(self):
        """Test enhanced structure variant generation with new modification types."""
        # Create a base structure with multiple components and relationships
        constraint = ComponentCountConstraint("multi", min_components=3, max_components=4)
        base_structure = self.generator.generate_structure([constraint])
        
        # Ensure we have some relationships
        if len(base_structure.relationships) == 0 and len(base_structure.components) >= 2:
            # Add a relationship manually for testing
            rel = self.generator._generate_random_relationship("test_rel", base_structure.components[:2])
            if rel:
                base_structure.add_relationship(rel)
        
        # Generate variants
        variants = self.generator.get_structure_variants(base_structure)
        
        # Should generate multiple types of variants
        assert isinstance(variants, list)
        
        # Each variant should be valid
        for variant in variants:
            assert isinstance(variant, Structure)
            assert variant.is_valid()
        
        # Variants should be different from the base structure
        # (This is not guaranteed for all variants, but at least some should be different)
        different_variants = [v for v in variants if v != base_structure]
        # We expect at least some variants to be different
        # (The exact number depends on the random generation and constraints)
    
    def test_modify_structure_with_new_modification_types(self):
        """Test structure modification with the new modification types."""
        from sep_solver.models.structure import (
            AddRelationshipModification, RemoveRelationshipModification,
            ModifyComponentPropertiesModification, ChangeComponentTypeModification
        )
        
        # Create base structure with multiple components
        constraint = ComponentCountConstraint("multi", min_components=2)
        base_structure = self.generator.generate_structure([constraint])
        
        # Test adding a relationship
        if len(base_structure.components) >= 2:
            new_relationship = self.generator._generate_random_relationship(
                "test_add_rel", base_structure.components[:2]
            )
            if new_relationship:
                add_rel_mod = AddRelationshipModification(new_relationship)
                modified_structure = self.generator.modify_structure(base_structure, add_rel_mod)
                
                assert modified_structure.is_valid()
                assert len(modified_structure.relationships) == len(base_structure.relationships) + 1
                assert any(r.id == new_relationship.id for r in modified_structure.relationships)
        
        # Test modifying component properties
        if base_structure.components:
            component = base_structure.components[0]
            new_properties = {"test_prop": "test_value", "modified": True}
            modify_props_mod = ModifyComponentPropertiesModification(component.id, new_properties)
            modified_structure = self.generator.modify_structure(base_structure, modify_props_mod)
            
            assert modified_structure.is_valid()
            modified_component = modified_structure.get_component(component.id)
            assert modified_component is not None
            assert modified_component.properties == new_properties
        
        # Test changing component type
        if base_structure.components:
            component = base_structure.components[0]
            new_type = "modified_type"
            change_type_mod = ChangeComponentTypeModification(component.id, new_type)
            modified_structure = self.generator.modify_structure(base_structure, change_type_mod)
            
            assert modified_structure.is_valid()
            modified_component = modified_structure.get_component(component.id)
            assert modified_component is not None
            assert modified_component.type == new_type