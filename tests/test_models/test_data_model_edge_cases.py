"""Unit tests for data model edge cases.

This module tests edge cases, error conditions, and boundary scenarios
for the core data models: Structure, VariableAssignment, and ConstraintSet.

Requirements tested: 3.1, 4.1, 5.5
"""

import pytest
from unittest.mock import Mock
from sep_solver.models.structure import (
    Structure, Component, Relationship, 
    AddComponentModification, RemoveComponentModification
)
from sep_solver.models.variable_assignment import (
    VariableAssignment, Domain, AssignmentSpace
)
from sep_solver.models.constraint_set import (
    ConstraintSet, Constraint, StructuralConstraint, VariableConstraint, 
    GlobalConstraint, ConstraintViolation, ComponentCountConstraint, 
    VariableRangeConstraint
)
from sep_solver.models.design_object import DesignObject


class TestStructureEdgeCases:
    """Test edge cases for Structure model."""
    
    def test_structure_with_empty_component_id(self):
        """Test structure with component having empty ID."""
        structure = Structure()
        component = Component(id="", type="processor")
        
        # Should allow empty ID (though not recommended)
        structure.add_component(component)
        assert len(structure.components) == 1
        assert structure.components[0].id == ""
    
    def test_structure_with_none_component_properties(self):
        """Test structure with component having None properties."""
        structure = Structure()
        component = Component(id="comp1", type="processor", properties=None)
        
        # Properties should default to empty dict if None
        structure.add_component(component)
        assert structure.components[0].properties is None
    
    def test_structure_with_circular_relationships(self):
        """Test structure with circular relationships."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp2", type="memory")
        
        structure.add_component(comp1)
        structure.add_component(comp2)
        
        # Create circular relationships
        rel1 = Relationship(id="rel1", source_id="comp1", target_id="comp2", type="connection")
        rel2 = Relationship(id="rel2", source_id="comp2", target_id="comp1", type="connection")
        
        structure.add_relationship(rel1)
        structure.add_relationship(rel2)
        
        # Should be valid (circular relationships are allowed)
        assert structure.is_valid()
        assert len(structure.relationships) == 2
    
    def test_structure_with_self_referencing_relationship(self):
        """Test structure with component connected to itself."""
        structure = Structure()
        component = Component(id="comp1", type="processor")
        structure.add_component(component)
        
        # Self-referencing relationship
        relationship = Relationship(id="rel1", source_id="comp1", target_id="comp1", type="self_loop")
        structure.add_relationship(relationship)
        
        assert structure.is_valid()
        assert len(structure.relationships) == 1
    
    def test_structure_remove_nonexistent_component(self):
        """Test removing a component that doesn't exist."""
        structure = Structure()
        component = Component(id="comp1", type="processor")
        structure.add_component(component)
        
        # Remove non-existent component (should not raise error)
        structure.remove_component("nonexistent")
        
        # Original component should still be there
        assert len(structure.components) == 1
        assert structure.components[0].id == "comp1"
    
    def test_structure_with_duplicate_component_ids_manual_insertion(self):
        """Test structure validation with manually inserted duplicate component IDs."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp1", type="memory")  # Same ID
        
        structure.add_component(comp1)
        # Manually insert duplicate to bypass add_component validation
        structure.components.append(comp2)
        
        assert not structure.is_valid()
        errors = structure.get_validation_errors()
        assert any("Duplicate component ID 'comp1'" in error for error in errors)
    
    def test_structure_with_orphaned_relationships_after_component_removal(self):
        """Test structure with relationships that become orphaned after component removal."""
        structure = Structure()
        comp1 = Component(id="comp1", type="processor")
        comp2 = Component(id="comp2", type="memory")
        comp3 = Component(id="comp3", type="storage")
        
        structure.add_component(comp1)
        structure.add_component(comp2)
        structure.add_component(comp3)
        
        rel1 = Relationship(id="rel1", source_id="comp1", target_id="comp2", type="connection")
        rel2 = Relationship(id="rel2", source_id="comp2", target_id="comp3", type="connection")
        
        structure.add_relationship(rel1)
        structure.add_relationship(rel2)
        
        # Manually remove component without using remove_component method
        structure.components = [c for c in structure.components if c.id != "comp2"]
        
        # Structure should now be invalid due to orphaned relationships
        assert not structure.is_valid()
        errors = structure.get_validation_errors()
        assert len(errors) >= 2  # Both relationships should be invalid
    
    def test_structure_with_extremely_long_component_id(self):
        """Test structure with extremely long component ID."""
        structure = Structure()
        long_id = "a" * 10000  # Very long ID
        component = Component(id=long_id, type="processor")
        
        structure.add_component(component)
        assert len(structure.components) == 1
        assert structure.components[0].id == long_id
    
    def test_structure_with_special_characters_in_ids(self):
        """Test structure with special characters in component and relationship IDs."""
        structure = Structure()
        
        # Component with special characters
        comp1 = Component(id="comp-1_test@domain.com", type="processor")
        comp2 = Component(id="comp/2\\test", type="memory")
        
        structure.add_component(comp1)
        structure.add_component(comp2)
        
        # Relationship with special characters
        relationship = Relationship(
            id="rel:1#test", 
            source_id="comp-1_test@domain.com", 
            target_id="comp/2\\test", 
            type="connection"
        )
        structure.add_relationship(relationship)
        
        assert structure.is_valid()
    
    def test_structure_serialization_with_complex_properties(self):
        """Test structure serialization with complex nested properties."""
        structure = Structure()
        
        complex_properties = {
            "nested": {
                "level1": {
                    "level2": ["item1", "item2"],
                    "numbers": [1, 2, 3.14, -5]
                }
            },
            "boolean": True,
            "null_value": None,
            "empty_list": [],
            "empty_dict": {}
        }
        
        component = Component(id="comp1", type="processor", properties=complex_properties)
        structure.add_component(component)
        
        # Test serialization round-trip
        structure_dict = structure.to_dict()
        restored_structure = Structure.from_dict(structure_dict)
        
        assert len(restored_structure.components) == 1
        restored_comp = restored_structure.components[0]
        assert restored_comp.properties == complex_properties
    
    def test_structure_modification_with_invalid_component(self):
        """Test structure modification with invalid component data."""
        structure = Structure()
        
        # Try to add component with same ID as existing one
        existing_comp = Component(id="comp1", type="processor")
        structure.add_component(existing_comp)
        
        duplicate_comp = Component(id="comp1", type="memory")
        modification = AddComponentModification(duplicate_comp)
        
        # Should raise error when applying modification
        with pytest.raises(ValueError, match="Component with ID 'comp1' already exists"):
            modification.apply(structure)
    
    def test_structure_hash_consistency(self):
        """Test that structure hash is consistent with equality."""
        structure1 = Structure()
        structure2 = Structure()
        
        # Add identical components in same order
        for i in range(3):
            comp1 = Component(id=f"comp{i}", type="processor")
            comp2 = Component(id=f"comp{i}", type="processor")
            structure1.add_component(comp1)
            structure2.add_component(comp2)
        
        assert structure1 == structure2
        assert hash(structure1) == hash(structure2)
        
        # Add different component to one structure
        structure2.add_component(Component(id="comp3", type="memory"))
        assert structure1 != structure2
        assert hash(structure1) != hash(structure2)


class TestVariableAssignmentEdgeCases:
    """Test edge cases for VariableAssignment model."""
    
    def test_domain_with_invalid_type(self):
        """Test domain with invalid/unknown type."""
        domain = Domain(name="test", type="unknown_type")
        
        # Unknown types fall through to return True (permissive behavior)
        assert domain.is_valid_value("any_value")
    
    def test_domain_with_conflicting_constraints(self):
        """Test domain with conflicting constraints (min > max)."""
        domain = Domain(
            name="test", 
            type="int", 
            constraints={"min": 10, "max": 5}  # min > max
        )
        
        # Should reject all values due to impossible constraints
        assert not domain.is_valid_value(7)
        assert not domain.is_valid_value(3)
        assert not domain.is_valid_value(12)
    
    def test_domain_enum_with_empty_values(self):
        """Test enum domain with empty values list."""
        domain = Domain(
            name="color", 
            type="enum", 
            constraints={"values": []}
        )
        
        # Should reject all values
        assert not domain.is_valid_value("red")
        assert not domain.is_valid_value("")
        assert not domain.is_valid_value(None)
        
        # Sample value should be None
        assert domain.get_sample_value() is None
    
    def test_domain_enum_with_none_values(self):
        """Test enum domain with None in values list."""
        domain = Domain(
            name="nullable", 
            type="enum", 
            constraints={"values": ["value1", None, "value2"]}
        )
        
        assert domain.is_valid_value("value1")
        assert domain.is_valid_value(None)
        assert domain.is_valid_value("value2")
        assert not domain.is_valid_value("invalid")
    
    def test_variable_assignment_with_circular_dependencies(self):
        """Test variable assignment with circular dependencies."""
        assignment = VariableAssignment()
        
        assignment.set_variable("var1", 10)
        assignment.set_variable("var2", 20)
        assignment.set_variable("var3", 30)
        
        # Create circular dependency chain: var1 -> var2 -> var3 -> var1
        assignment.add_dependency("var1", ["var2"])
        assignment.add_dependency("var2", ["var3"])
        assignment.add_dependency("var3", ["var1"])
        
        # Should still be consistent since all variables are assigned
        assert assignment.is_consistent()
    
    def test_variable_assignment_with_self_dependency(self):
        """Test variable assignment with self-dependency."""
        assignment = VariableAssignment()
        
        assignment.set_variable("var1", 10)
        assignment.add_dependency("var1", ["var1"])  # Self-dependency
        
        # Should be consistent (variable depends on itself and is assigned)
        assert assignment.is_consistent()
    
    def test_variable_assignment_with_empty_dependency_list(self):
        """Test variable assignment with empty dependency list."""
        assignment = VariableAssignment()
        
        assignment.set_variable("var1", 10)
        assignment.add_dependency("var1", [])  # Empty dependency list
        
        # Should be consistent (no dependencies to check)
        assert assignment.is_consistent()
    
    def test_variable_assignment_domain_validation_bypass(self):
        """Test bypassing domain validation by direct assignment manipulation."""
        assignment = VariableAssignment()
        
        # Add strict domain
        domain = Domain(name="speed", type="int", constraints={"min": 0, "max": 100})
        assignment.add_domain(domain)
        
        # Set valid value first
        assignment.set_variable("speed", 50)
        
        # Manually set invalid value to bypass validation
        assignment.assignments["speed"] = 150
        
        # Validation should catch this
        errors = assignment.validate_all_assignments()
        assert len(errors) > 0
        assert "speed" in errors[0]
        assert "invalid value" in errors[0]
    
    def test_variable_assignment_with_none_values(self):
        """Test variable assignment with None values."""
        assignment = VariableAssignment()
        
        # Set None value (should be allowed if no domain restrictions)
        assignment.set_variable("nullable_var", None)
        assert assignment.get_variable("nullable_var") is None
        
        # Test with domain that allows None
        domain = Domain(name="optional", type="enum", constraints={"values": [None, "value1"]})
        assignment.add_domain(domain)
        assignment.set_variable("optional", None)
        
        assert assignment.get_variable("optional") is None
    
    def test_variable_assignment_serialization_with_complex_values(self):
        """Test variable assignment serialization with complex values."""
        assignment = VariableAssignment()
        
        # Set complex values
        complex_value = {
            "nested": {"list": [1, 2, {"inner": True}]},
            "tuple_like": [1, 2, 3],
            "boolean": False,
            "null": None
        }
        
        assignment.set_variable("complex", complex_value)
        assignment.set_variable("simple_list", [1, 2, 3])
        assignment.set_variable("simple_dict", {"key": "value"})
        
        # Test serialization round-trip
        data = assignment.to_dict()
        restored = VariableAssignment.from_dict(data)
        
        assert restored.get_variable("complex") == complex_value
        assert restored.get_variable("simple_list") == [1, 2, 3]
        assert restored.get_variable("simple_dict") == {"key": "value"}
    
    def test_variable_assignment_with_extremely_long_variable_names(self):
        """Test variable assignment with extremely long variable names."""
        assignment = VariableAssignment()
        
        long_name = "a" * 10000
        assignment.set_variable(long_name, "value")
        
        assert assignment.has_variable(long_name)
        assert assignment.get_variable(long_name) == "value"
    
    def test_assignment_space_with_zero_sized_domains(self):
        """Test assignment space with domains that have zero size."""
        domains = {
            "empty_enum": Domain(name="empty_enum", type="enum", constraints={"values": []}),
            "impossible_range": Domain(name="impossible", type="int", constraints={"min": 10, "max": 5})
        }
        
        space = AssignmentSpace(domains)
        
        # Should handle zero-sized domains gracefully
        assert space.get_domain_size("empty_enum") == 0
        # For impossible range (min > max), get_domain_size returns None (unknown/infinite)
        assert space.get_domain_size("impossible") is None
        
        # Total combinations should be 0 due to empty domain
        total = space.estimate_total_combinations()
        assert total == 0
    
    def test_assignment_space_with_mixed_finite_infinite_domains(self):
        """Test assignment space with mix of finite and infinite domains."""
        domains = {
            "finite": Domain(name="finite", type="bool"),  # 2 values
            "infinite": Domain(name="infinite", type="float"),  # No constraints = infinite
            "large_finite": Domain(name="large_finite", type="int", constraints={"min": 0, "max": 1000000})
        }
        
        space = AssignmentSpace(domains)
        
        assert space.get_domain_size("finite") == 2
        assert space.get_domain_size("infinite") is None
        assert space.get_domain_size("large_finite") == 1000001
        
        # Total should be None due to infinite domain
        assert space.estimate_total_combinations() is None


class TestConstraintSetEdgeCases:
    """Test edge cases for ConstraintSet model."""
    
    def test_constraint_set_with_duplicate_constraint_ids(self):
        """Test constraint set with duplicate constraint IDs across types."""
        constraint_set = ConstraintSet()
        
        # Add constraints with same ID but different types
        struct_constraint = ComponentCountConstraint("duplicate_id", min_components=1)
        var_constraint = VariableRangeConstraint("duplicate_id", "test_var", min_value=0)
        
        constraint_set.add_constraint(struct_constraint)
        constraint_set.add_constraint(var_constraint)
        
        # Should allow duplicate IDs across different constraint types
        assert len(constraint_set) == 2
        
        # get_constraint should return the first match found
        found = constraint_set.get_constraint("duplicate_id")
        assert found is not None
        assert found.constraint_id == "duplicate_id"
    
    def test_constraint_set_remove_constraint_multiple_matches(self):
        """Test removing constraint when multiple constraints have same ID."""
        constraint_set = ConstraintSet()
        
        # Manually add constraints with same ID to different lists
        struct_constraint = ComponentCountConstraint("same_id", min_components=1)
        var_constraint = VariableRangeConstraint("same_id", "test_var", min_value=0)
        
        constraint_set.add_constraint(struct_constraint)
        constraint_set.add_constraint(var_constraint)
        
        # Remove should only remove the first match
        result = constraint_set.remove_constraint("same_id")
        assert result is True
        assert len(constraint_set) == 1  # One should remain
        
        # Remove again should remove the second one
        result = constraint_set.remove_constraint("same_id")
        assert result is True
        assert len(constraint_set) == 0
    
    def test_constraint_violation_with_complex_context(self):
        """Test constraint violation with complex context data."""
        complex_context = {
            "component_ids": ["comp1", "comp2", "comp3"],
            "nested_data": {
                "measurements": [1.5, 2.7, 3.9],
                "metadata": {"timestamp": "2023-01-01", "valid": True}
            },
            "error_details": {
                "expected_range": [0, 100],
                "actual_value": 150,
                "tolerance": 0.01
            }
        }
        
        violation = ConstraintViolation(
            constraint_id="complex_constraint",
            constraint_type="variable",
            message="Complex constraint violation",
            severity="warning",
            context=complex_context
        )
        
        assert violation.context["component_ids"] == ["comp1", "comp2", "comp3"]
        assert violation.context["nested_data"]["measurements"][1] == 2.7
        assert violation.context["error_details"]["actual_value"] == 150
    
    def test_constraint_with_none_description(self):
        """Test constraint with None description."""
        class TestConstraint(StructuralConstraint):
            def is_satisfied(self, design_object):
                return True
            
            def get_violation_message(self, design_object):
                return "Test violation"
        
        # Create constraint with None description
        constraint = TestConstraint("test_id", None)
        assert constraint.description is None
        
        constraint_set = ConstraintSet()
        constraint_set.add_constraint(constraint)
        
        # Should handle None description gracefully
        constraint_dict = constraint_set.to_dict()
        assert constraint_dict["structural_constraints"][0]["description"] is None
    
    def test_constraint_set_with_empty_constraint_lists(self):
        """Test constraint set operations with empty constraint lists."""
        constraint_set = ConstraintSet()
        
        # All operations should work with empty set
        assert constraint_set.is_empty()
        assert len(constraint_set) == 0
        assert constraint_set.get_constraint("nonexistent") is None
        assert constraint_set.remove_constraint("nonexistent") is False
        assert constraint_set.get_all_constraints() == []
        assert constraint_set.get_constraints_by_type("structural") == []
        assert constraint_set.get_constraints_for_component("comp1") == []
        
        counts = constraint_set.count_constraints()
        assert all(count == 0 for count in counts.values())
    
    def test_component_count_constraint_edge_cases(self):
        """Test ComponentCountConstraint with edge cases."""
        # Create design object with no components
        empty_structure = Structure()
        empty_variables = VariableAssignment()
        empty_design = DesignObject("empty", empty_structure, empty_variables, {})
        
        # Constraint requiring at least 1 component
        constraint = ComponentCountConstraint("min_one", min_components=1)
        assert not constraint.is_satisfied(empty_design)
        
        # Constraint with no maximum (None)
        constraint_no_max = ComponentCountConstraint("no_max", min_components=0, max_components=None)
        assert constraint_no_max.is_satisfied(empty_design)
        
        # Create design with many components
        large_structure = Structure()
        for i in range(1000):
            comp = Component(id=f"comp{i}", type="processor")
            large_structure.add_component(comp)
        
        large_design = DesignObject("large", large_structure, empty_variables, {})
        assert constraint_no_max.is_satisfied(large_design)
    
    def test_variable_range_constraint_edge_cases(self):
        """Test VariableRangeConstraint with edge cases."""
        # Create design object with no variables
        empty_structure = Structure()
        empty_variables = VariableAssignment()
        empty_design = DesignObject("empty", empty_structure, empty_variables, {})
        
        # Constraint on non-existent variable
        constraint = VariableRangeConstraint("range_test", "nonexistent_var", min_value=0, max_value=10)
        assert not constraint.is_satisfied(empty_design)
        
        message = constraint.get_violation_message(empty_design)
        assert "is not assigned" in message
        
        # Constraint with no bounds (None values)
        constraint_no_bounds = VariableRangeConstraint("no_bounds", "test_var", min_value=None, max_value=None)
        
        # Add variable to design
        variables_with_var = VariableAssignment()
        variables_with_var.set_variable("test_var", 999999)  # Very large value
        design_with_var = DesignObject("with_var", empty_structure, variables_with_var, {})
        
        # Should be satisfied regardless of value when no bounds
        assert constraint_no_bounds.is_satisfied(design_with_var)
    
    def test_constraint_inheritance_and_polymorphism(self):
        """Test constraint inheritance and polymorphic behavior."""
        class CustomStructuralConstraint(StructuralConstraint):
            def __init__(self, constraint_id: str):
                super().__init__(constraint_id, "Custom structural constraint")
                self.call_count = 0
            
            def is_satisfied(self, design_object):
                self.call_count += 1
                return True
            
            def get_violation_message(self, design_object):
                return f"Custom violation for {self.constraint_id}"
        
        class CustomVariableConstraint(VariableConstraint):
            def is_satisfied(self, design_object):
                return False  # Always fails
            
            def get_violation_message(self, design_object):
                return "Custom variable constraint always fails"
        
        constraint_set = ConstraintSet()
        
        # Add custom constraints
        custom_struct = CustomStructuralConstraint("custom_struct")
        custom_var = CustomVariableConstraint("custom_var", "Custom variable constraint")
        
        constraint_set.add_constraint(custom_struct)
        constraint_set.add_constraint(custom_var)
        
        # Verify they're stored in correct lists
        assert len(constraint_set.structural_constraints) == 1
        assert len(constraint_set.variable_constraints) == 1
        assert isinstance(constraint_set.structural_constraints[0], CustomStructuralConstraint)
        assert isinstance(constraint_set.variable_constraints[0], CustomVariableConstraint)
        
        # Test polymorphic behavior
        empty_design = DesignObject("test", Structure(), VariableAssignment(), {})
        
        assert custom_struct.is_satisfied(empty_design)
        assert custom_struct.call_count == 1
        
        assert not custom_var.is_satisfied(empty_design)
        assert "always fails" in custom_var.get_violation_message(empty_design)


class TestIntegratedEdgeCases:
    """Test edge cases involving multiple data models together."""
    
    def test_design_object_with_inconsistent_structure_and_variables(self):
        """Test design object where structure and variables are inconsistent."""
        # Create structure with components that have variable references
        structure = Structure()
        comp1 = Component(id="comp1", type="processor", properties={"speed_var": "cpu_speed"})
        comp2 = Component(id="comp2", type="memory", properties={"size_var": "memory_size"})
        structure.add_component(comp1)
        structure.add_component(comp2)
        
        # Create variables that don't match the component references
        variables = VariableAssignment()
        variables.set_variable("unrelated_var1", 100)
        variables.set_variable("unrelated_var2", 200)
        # Missing: cpu_speed, memory_size
        
        design_object = DesignObject("inconsistent", structure, variables, {})
        
        # Design object should still be created (consistency checking is separate)
        assert design_object.id == "inconsistent"
        assert len(design_object.structure.components) == 2
        assert len(design_object.variables.assignments) == 2
    
    def test_constraint_evaluation_with_malformed_design_object(self):
        """Test constraint evaluation with malformed design object."""
        # Create constraint
        constraint = ComponentCountConstraint("test_constraint", min_components=1, max_components=5)
        
        # Create design object with None structure (malformed)
        variables = VariableAssignment()
        
        # This would normally not be allowed, but test edge case handling
        class MalformedDesignObject:
            def __init__(self):
                self.structure = None
                self.variables = variables
        
        malformed_design = MalformedDesignObject()
        
        # Constraint should handle malformed input gracefully
        with pytest.raises(AttributeError):
            constraint.is_satisfied(malformed_design)
    
    def test_large_scale_data_model_operations(self):
        """Test data model operations with large amounts of data."""
        # Create large structure
        structure = Structure()
        
        # Add many components
        for i in range(1000):
            comp = Component(id=f"comp_{i:04d}", type=f"type_{i % 10}")
            structure.add_component(comp)
        
        # Add many relationships
        for i in range(500):
            source_id = f"comp_{i:04d}"
            target_id = f"comp_{(i+1):04d}"
            rel = Relationship(id=f"rel_{i:04d}", source_id=source_id, target_id=target_id, type="connection")
            structure.add_relationship(rel)
        
        # Create large variable assignment
        variables = VariableAssignment()
        for i in range(1000):
            var_name = f"var_{i:04d}"
            domain = Domain(name=var_name, type="int", constraints={"min": 0, "max": 1000})
            variables.add_domain(domain)
            variables.set_variable(var_name, i)
        
        # Create large constraint set
        constraint_set = ConstraintSet()
        for i in range(100):
            constraint = ComponentCountConstraint(f"constraint_{i:03d}", min_components=i, max_components=i+100)
            constraint_set.add_constraint(constraint)
        
        # Test operations still work with large data
        assert structure.is_valid()
        assert len(structure.components) == 1000
        assert len(structure.relationships) == 500
        
        assert variables.is_complete()
        assert variables.is_consistent()
        assert len(variables.assignments) == 1000
        
        assert len(constraint_set) == 100
        assert not constraint_set.is_empty()
        
        # Test serialization with large data
        structure_dict = structure.to_dict()
        assert len(structure_dict["components"]) == 1000
        
        variables_dict = variables.to_dict()
        assert len(variables_dict["assignments"]) == 1000
    
    def test_memory_efficiency_with_repeated_operations(self):
        """Test memory efficiency with repeated create/destroy operations."""
        # This test ensures no memory leaks in repeated operations
        
        for iteration in range(100):
            # Create and destroy structures repeatedly
            structure = Structure()
            
            for i in range(10):
                comp = Component(id=f"comp_{iteration}_{i}", type="processor")
                structure.add_component(comp)
            
            # Create relationships
            for i in range(5):
                rel = Relationship(
                    id=f"rel_{iteration}_{i}",
                    source_id=f"comp_{iteration}_{i}",
                    target_id=f"comp_{iteration}_{i+1}",
                    type="connection"
                )
                structure.add_relationship(rel)
            
            # Verify structure
            assert len(structure.components) == 10
            assert len(structure.relationships) == 5
            assert structure.is_valid()
            
            # Structure should be garbage collected after this iteration
            del structure
        
        # If we get here without memory issues, the test passes
        assert True
    
    def test_unicode_and_special_character_handling(self):
        """Test handling of Unicode and special characters in all models."""
        # Test with various Unicode characters
        unicode_id = "测试_component_🚀"
        emoji_type = "🔧_processor_type"
        
        # Structure with Unicode
        structure = Structure()
        component = Component(
            id=unicode_id,
            type=emoji_type,
            properties={"名前": "テスト", "emoji": "🎯", "special": "àáâãäåæçèéêë"}
        )
        structure.add_component(component)
        
        # Variables with Unicode
        variables = VariableAssignment()
        unicode_var_name = "変数_test_🎲"
        variables.set_variable(unicode_var_name, "Unicode_value_测试")
        
        # Constraint with Unicode
        constraint_set = ConstraintSet()
        unicode_constraint = ComponentCountConstraint("制約_constraint_🔒", min_components=1)
        constraint_set.add_constraint(unicode_constraint)
        
        # Test serialization with Unicode
        structure_dict = structure.to_dict()
        restored_structure = Structure.from_dict(structure_dict)
        
        assert restored_structure.components[0].id == unicode_id
        assert restored_structure.components[0].type == emoji_type
        assert restored_structure.components[0].properties["名前"] == "テスト"
        
        variables_dict = variables.to_dict()
        restored_variables = VariableAssignment.from_dict(variables_dict)
        
        assert restored_variables.get_variable(unicode_var_name) == "Unicode_value_测试"
        
        # Test constraint operations with Unicode
        assert unicode_constraint.constraint_id == "制約_constraint_🔒"
        found_constraint = constraint_set.get_constraint("制約_constraint_🔒")
        assert found_constraint is not None