"""Tests for structure model."""

import pytest
from sep_solver.models.structure import (
    Component, Relationship, Structure, 
    AddComponentModification, RemoveComponentModification
)


class TestComponent:
    """Test cases for Component class."""
    
    def test_component_creation(self):
        """Test creating a component."""
        component = Component(
            id="comp1",
            type="processor",
            properties={"speed": 100, "cores": 4}
        )
        
        assert component.id == "comp1"
        assert component.type == "processor"
        assert component.properties["speed"] == 100
        assert component.properties["cores"] == 4
    
    def test_component_to_dict(self):
        """Test converting component to dictionary."""
        component = Component(id="comp1", type="processor", properties={"speed": 100})
        component_dict = component.to_dict()
        
        expected = {
            "id": "comp1",
            "type": "processor",
            "properties": {"speed": 100}
        }
        assert component_dict == expected
    
    def test_component_from_dict(self):
        """Test creating component from dictionary."""
        data = {
            "id": "comp1",
            "type": "processor",
            "properties": {"speed": 100}
        }
        
        component = Component.from_dict(data)
        
        assert component.id == "comp1"
        assert component.type == "processor"
        assert component.properties["speed"] == 100
    
    def test_component_equality(self):
        """Test component equality."""
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp1", type="processor")
        comp3 = Component(id="comp2", type="processor")
        
        assert comp1 == comp2
        assert comp1 != comp3
    
    def test_component_hash(self):
        """Test component hashing."""
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp1", type="processor")
        
        # Should be hashable and equal components should have same hash
        assert hash(comp1) == hash(comp2)
        
        # Should be usable in sets
        component_set = {comp1, comp2}
        assert len(component_set) == 1


class TestRelationship:
    """Test cases for Relationship class."""
    
    def test_relationship_creation(self):
        """Test creating a relationship."""
        relationship = Relationship(
            id="rel1",
            source_id="comp1",
            target_id="comp2",
            type="connection",
            properties={"bandwidth": 1000}
        )
        
        assert relationship.id == "rel1"
        assert relationship.source_id == "comp1"
        assert relationship.target_id == "comp2"
        assert relationship.type == "connection"
        assert relationship.properties["bandwidth"] == 1000
    
    def test_relationship_to_dict(self):
        """Test converting relationship to dictionary."""
        relationship = Relationship(
            id="rel1",
            source_id="comp1", 
            target_id="comp2",
            type="connection"
        )
        relationship_dict = relationship.to_dict()
        
        expected = {
            "id": "rel1",
            "source_id": "comp1",
            "target_id": "comp2",
            "type": "connection",
            "properties": {}
        }
        assert relationship_dict == expected
    
    def test_relationship_from_dict(self):
        """Test creating relationship from dictionary."""
        data = {
            "id": "rel1",
            "source_id": "comp1",
            "target_id": "comp2",
            "type": "connection",
            "properties": {"bandwidth": 1000}
        }
        
        relationship = Relationship.from_dict(data)
        
        assert relationship.id == "rel1"
        assert relationship.source_id == "comp1"
        assert relationship.target_id == "comp2"
        assert relationship.type == "connection"
        assert relationship.properties["bandwidth"] == 1000


class TestStructure:
    """Test cases for Structure class."""
    
    def test_empty_structure_creation(self):
        """Test creating an empty structure."""
        structure = Structure()
        
        assert len(structure.components) == 0
        assert len(structure.relationships) == 0
        assert len(structure.structural_constraints) == 0
    
    def test_add_component(self):
        """Test adding a component to structure."""
        structure = Structure()
        component = Component(id="comp1", type="processor")
        
        structure.add_component(component)
        
        assert len(structure.components) == 1
        assert structure.components[0] == component
    
    def test_add_duplicate_component(self):
        """Test adding a component with duplicate ID."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp1", type="memory")  # Same ID
        
        structure.add_component(comp1)
        
        with pytest.raises(ValueError, match="Component with ID 'comp1' already exists"):
            structure.add_component(comp2)
    
    def test_add_relationship(self):
        """Test adding a relationship to structure."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp2", type="memory")
        relationship = Relationship(id="rel1", source_id="comp1", target_id="comp2", type="connection")
        
        structure.add_component(comp1)
        structure.add_component(comp2)
        structure.add_relationship(relationship)
        
        assert len(structure.relationships) == 1
        assert structure.relationships[0] == relationship
    
    def test_add_relationship_invalid_source(self):
        """Test adding relationship with invalid source component."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        relationship = Relationship(id="rel1", source_id="nonexistent", target_id="comp1", type="connection")
        
        structure.add_component(comp1)
        
        with pytest.raises(ValueError, match="Source component 'nonexistent' not found"):
            structure.add_relationship(relationship)
    
    def test_add_relationship_invalid_target(self):
        """Test adding relationship with invalid target component."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        relationship = Relationship(id="rel1", source_id="comp1", target_id="nonexistent", type="connection")
        
        structure.add_component(comp1)
        
        with pytest.raises(ValueError, match="Target component 'nonexistent' not found"):
            structure.add_relationship(relationship)
    
    def test_remove_component(self):
        """Test removing a component from structure."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp2", type="memory")
        relationship = Relationship(id="rel1", source_id="comp1", target_id="comp2", type="connection")
        
        structure.add_component(comp1)
        structure.add_component(comp2)
        structure.add_relationship(relationship)
        
        # Remove component should also remove related relationships
        structure.remove_component("comp1")
        
        assert len(structure.components) == 1
        assert structure.components[0].id == "comp2"
        assert len(structure.relationships) == 0  # Relationship should be removed
    
    def test_get_component(self):
        """Test getting a component by ID."""
        structure = Structure()
        component = Component(id="comp1", type="processor")
        
        structure.add_component(component)
        
        found_component = structure.get_component("comp1")
        assert found_component == component
        
        not_found = structure.get_component("nonexistent")
        assert not_found is None
    
    def test_get_relationships_for_component(self):
        """Test getting relationships for a component."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp2", type="memory")
        comp3 = Component(id="comp3", type="storage")
        
        rel1 = Relationship(id="rel1", source_id="comp1", target_id="comp2", type="connection")
        rel2 = Relationship(id="rel2", source_id="comp2", target_id="comp3", type="connection")
        rel3 = Relationship(id="rel3", source_id="comp3", target_id="comp1", type="connection")
        
        structure.add_component(comp1)
        structure.add_component(comp2)
        structure.add_component(comp3)
        structure.add_relationship(rel1)
        structure.add_relationship(rel2)
        structure.add_relationship(rel3)
        
        # comp1 should be involved in rel1 (as source) and rel3 (as target)
        comp1_relationships = structure.get_relationships_for_component("comp1")
        assert len(comp1_relationships) == 2
        assert rel1 in comp1_relationships
        assert rel3 in comp1_relationships
    
    def test_structure_to_dict(self):
        """Test converting structure to dictionary."""
        structure = Structure()
        component = Component(id="comp1", type="processor")
        structure.add_component(component)
        
        structure_dict = structure.to_dict()
        
        assert "components" in structure_dict
        assert "relationships" in structure_dict
        assert "structural_constraints" in structure_dict
        assert len(structure_dict["components"]) == 1
        assert structure_dict["components"][0]["id"] == "comp1"
    
    def test_structure_from_dict(self):
        """Test creating structure from dictionary."""
        data = {
            "components": [
                {"id": "comp1", "type": "processor", "properties": {}}
            ],
            "relationships": [
                {"id": "rel1", "source_id": "comp1", "target_id": "comp2", "type": "connection", "properties": {}}
            ]
        }
        
        structure = Structure.from_dict(data)
        
        assert len(structure.components) == 1
        assert structure.components[0].id == "comp1"
        assert len(structure.relationships) == 1
        assert structure.relationships[0].id == "rel1"
    
    def test_structure_equality(self):
        """Test structure equality."""
        # Create two identical structures
        structure1 = Structure()
        structure2 = Structure()
        
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp1", type="processor")  # Same as comp1
        
        structure1.add_component(comp1)
        structure2.add_component(comp2)
        
        assert structure1 == structure2
    
    def test_structure_is_valid_empty(self):
        """Test that empty structure is valid (no constraints to violate)."""
        structure = Structure()
        assert structure.is_valid() is True
    
    def test_structure_is_valid_with_components_and_relationships(self):
        """Test that structure with valid relationships is valid."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp2", type="memory")
        relationship = Relationship(id="rel1", source_id="comp1", target_id="comp2", type="connection")
        
        structure.add_component(comp1)
        structure.add_component(comp2)
        structure.add_relationship(relationship)
        
        assert structure.is_valid() is True
    
    def test_structure_is_invalid_with_orphaned_relationships(self):
        """Test that structure with relationships to non-existent components is invalid."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        # Create relationship to non-existent component
        relationship = Relationship(id="rel1", source_id="comp1", target_id="nonexistent", type="connection")
        
        structure.add_component(comp1)
        # Manually add relationship to bypass validation in add_relationship
        structure.relationships.append(relationship)
        
        assert structure.is_valid() is False
    
    def test_structure_is_invalid_with_duplicate_relationship_ids(self):
        """Test that structure with duplicate relationship IDs is invalid."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp2", type="memory")
        rel1 = Relationship(id="rel1", source_id="comp1", target_id="comp2", type="connection")
        rel2 = Relationship(id="rel1", source_id="comp2", target_id="comp1", type="connection")  # Same ID
        
        structure.add_component(comp1)
        structure.add_component(comp2)
        structure.add_relationship(rel1)
        # Manually add second relationship to bypass any ID checking
        structure.relationships.append(rel2)
        
        assert structure.is_valid() is False
    
    def test_get_validation_errors(self):
        """Test getting detailed validation errors."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        # Create relationship to non-existent component
        relationship = Relationship(id="rel1", source_id="comp1", target_id="nonexistent", type="connection")
        
        structure.add_component(comp1)
        # Manually add relationship to bypass validation in add_relationship
        structure.relationships.append(relationship)
        
        errors = structure.get_validation_errors()
        assert len(errors) == 1
        assert "nonexistent" in errors[0]
        assert "target component" in errors[0]


class TestModifications:
    """Test cases for structure modifications."""
    
    def test_add_component_modification(self):
        """Test adding component modification."""
        structure = Structure()
        component = Component(id="comp1", type="processor")
        modification = AddComponentModification(component)
        
        new_structure = modification.apply(structure)
        
        # Original structure should be unchanged
        assert len(structure.components) == 0
        
        # New structure should have the component
        assert len(new_structure.components) == 1
        assert new_structure.components[0] == component
    
    def test_remove_component_modification(self):
        """Test removing component modification."""
        structure = Structure()
        component = Component(id="comp1", type="processor")
        structure.add_component(component)
        
        modification = RemoveComponentModification("comp1")
        new_structure = modification.apply(structure)
        
        # Original structure should be unchanged
        assert len(structure.components) == 1
        
        # New structure should not have the component
        assert len(new_structure.components) == 0
    
    def test_modification_descriptions(self):
        """Test modification descriptions."""
        component = Component(id="comp1", type="processor")
        
        add_mod = AddComponentModification(component)
        assert "Add component comp1 of type processor" in add_mod.get_description()
        
        remove_mod = RemoveComponentModification("comp1")
        assert "Remove component comp1" in remove_mod.get_description()
    
    def test_add_relationship_modification(self):
        """Test adding relationship modification."""
        from sep_solver.models.structure import AddRelationshipModification
        
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp2", type="memory")
        structure.add_component(comp1)
        structure.add_component(comp2)
        
        relationship = Relationship(id="rel1", source_id="comp1", target_id="comp2", type="connects_to")
        modification = AddRelationshipModification(relationship)
        new_structure = modification.apply(structure)
        
        # Original structure should be unchanged
        assert len(structure.relationships) == 0
        
        # New structure should have the relationship
        assert len(new_structure.relationships) == 1
        assert new_structure.relationships[0] == relationship
    
    def test_remove_relationship_modification(self):
        """Test removing relationship modification."""
        from sep_solver.models.structure import RemoveRelationshipModification
        
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp2", type="memory")
        structure.add_component(comp1)
        structure.add_component(comp2)
        
        relationship = Relationship(id="rel1", source_id="comp1", target_id="comp2", type="connects_to")
        structure.add_relationship(relationship)
        
        modification = RemoveRelationshipModification("rel1")
        new_structure = modification.apply(structure)
        
        # Original structure should be unchanged
        assert len(structure.relationships) == 1
        
        # New structure should not have the relationship
        assert len(new_structure.relationships) == 0
    
    def test_modify_component_properties_modification(self):
        """Test modifying component properties."""
        from sep_solver.models.structure import ModifyComponentPropertiesModification
        
        structure = Structure()
        component = Component(id="comp1", type="processor", properties={"old_prop": "old_value"})
        structure.add_component(component)
        
        new_properties = {"new_prop": "new_value", "another_prop": 42}
        modification = ModifyComponentPropertiesModification("comp1", new_properties)
        new_structure = modification.apply(structure)
        
        # Original structure should be unchanged
        assert structure.components[0].properties == {"old_prop": "old_value"}
        
        # New structure should have modified properties
        modified_component = new_structure.get_component("comp1")
        assert modified_component is not None
        assert modified_component.properties == new_properties
    
    def test_modify_relationship_properties_modification(self):
        """Test modifying relationship properties."""
        from sep_solver.models.structure import ModifyRelationshipPropertiesModification
        
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp2", type="memory")
        structure.add_component(comp1)
        structure.add_component(comp2)
        
        relationship = Relationship(
            id="rel1", source_id="comp1", target_id="comp2", 
            type="connects_to", properties={"old_prop": "old_value"}
        )
        structure.add_relationship(relationship)
        
        new_properties = {"new_prop": "new_value", "strength": 0.8}
        modification = ModifyRelationshipPropertiesModification("rel1", new_properties)
        new_structure = modification.apply(structure)
        
        # Original structure should be unchanged
        assert structure.relationships[0].properties == {"old_prop": "old_value"}
        
        # New structure should have modified properties
        modified_relationship = next((r for r in new_structure.relationships if r.id == "rel1"), None)
        assert modified_relationship is not None
        assert modified_relationship.properties == new_properties
    
    def test_change_component_type_modification(self):
        """Test changing component type."""
        from sep_solver.models.structure import ChangeComponentTypeModification
        
        structure = Structure()
        component = Component(id="comp1", type="processor", properties={"capacity": 100})
        structure.add_component(component)
        
        modification = ChangeComponentTypeModification("comp1", "memory")
        new_structure = modification.apply(structure)
        
        # Original structure should be unchanged
        assert structure.components[0].type == "processor"
        
        # New structure should have modified type
        modified_component = new_structure.get_component("comp1")
        assert modified_component is not None
        assert modified_component.type == "memory"
        assert modified_component.properties == {"capacity": 100}  # Properties should be preserved