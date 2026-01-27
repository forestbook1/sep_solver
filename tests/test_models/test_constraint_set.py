"""Tests for constraint set model."""

import pytest
from sep_solver.models.constraint_set import (
    Constraint, StructuralConstraint, VariableConstraint, GlobalConstraint,
    ConstraintSet, ConstraintViolation, ComponentCountConstraint, VariableRangeConstraint
)
from sep_solver.models.design_object import DesignObject
from sep_solver.models.structure import Structure, Component
from sep_solver.models.variable_assignment import VariableAssignment, Domain


class MockConstraint(Constraint):
    """Mock constraint for testing."""
    
    def __init__(self, constraint_id: str, description: str = "", should_pass: bool = True):
        super().__init__(constraint_id, description)
        self.should_pass = should_pass
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return self.should_pass
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        return f"Mock constraint {self.constraint_id} violated"


class MockStructuralConstraint(StructuralConstraint):
    """Mock structural constraint for testing."""
    
    def __init__(self, constraint_id: str, description: str = "", should_pass: bool = True):
        super().__init__(constraint_id, description)
        self.should_pass = should_pass
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return self.should_pass
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        return f"Mock structural constraint {self.constraint_id} violated"


class MockVariableConstraint(VariableConstraint):
    """Mock variable constraint for testing."""
    
    def __init__(self, constraint_id: str, description: str = "", should_pass: bool = True):
        super().__init__(constraint_id, description)
        self.should_pass = should_pass
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return self.should_pass
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        return f"Mock variable constraint {self.constraint_id} violated"


class MockGlobalConstraint(GlobalConstraint):
    """Mock global constraint for testing."""
    
    def __init__(self, constraint_id: str, description: str = "", should_pass: bool = True):
        super().__init__(constraint_id, description)
        self.should_pass = should_pass
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return self.should_pass
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        return f"Mock global constraint {self.constraint_id} violated"


class TestConstraintViolation:
    """Test cases for ConstraintViolation class."""
    
    def test_constraint_violation_creation(self):
        """Test creating a constraint violation."""
        violation = ConstraintViolation(
            constraint_id="test_constraint",
            constraint_type="structural",
            message="Test violation message",
            severity="error",
            context={"component": "comp1"}
        )
        
        assert violation.constraint_id == "test_constraint"
        assert violation.constraint_type == "structural"
        assert violation.message == "Test violation message"
        assert violation.severity == "error"
        assert violation.context["component"] == "comp1"
    
    def test_constraint_violation_default_severity(self):
        """Test constraint violation with default severity."""
        violation = ConstraintViolation(
            constraint_id="test_constraint",
            constraint_type="structural",
            message="Test violation message"
        )
        
        assert violation.severity == "error"
        assert violation.context == {}
    
    def test_constraint_violation_string_representation(self):
        """Test string representation of constraint violation."""
        violation = ConstraintViolation(
            constraint_id="test_constraint",
            constraint_type="structural",
            message="Test violation message",
            severity="warning"
        )
        
        str_repr = str(violation)
        assert "[WARNING]" in str_repr
        assert "structural" in str_repr
        assert "test_constraint" in str_repr
        assert "Test violation message" in str_repr


class TestConstraintSet:
    """Test cases for ConstraintSet class."""
    
    def test_empty_constraint_set_creation(self):
        """Test creating an empty constraint set."""
        constraint_set = ConstraintSet()
        
        assert len(constraint_set.structural_constraints) == 0
        assert len(constraint_set.variable_constraints) == 0
        assert len(constraint_set.global_constraints) == 0
        assert constraint_set.is_empty() is True
    
    def test_add_structural_constraint(self):
        """Test adding a structural constraint."""
        constraint_set = ConstraintSet()
        constraint = MockStructuralConstraint("struct1", "Test structural constraint")
        
        constraint_set.add_constraint(constraint)
        
        assert len(constraint_set.structural_constraints) == 1
        assert constraint_set.structural_constraints[0] == constraint
        assert constraint_set.is_empty() is False
    
    def test_add_variable_constraint(self):
        """Test adding a variable constraint."""
        constraint_set = ConstraintSet()
        constraint = MockVariableConstraint("var1", "Test variable constraint")
        
        constraint_set.add_constraint(constraint)
        
        assert len(constraint_set.variable_constraints) == 1
        assert constraint_set.variable_constraints[0] == constraint
    
    def test_add_global_constraint(self):
        """Test adding a global constraint."""
        constraint_set = ConstraintSet()
        constraint = MockGlobalConstraint("global1", "Test global constraint")
        
        constraint_set.add_constraint(constraint)
        
        assert len(constraint_set.global_constraints) == 1
        assert constraint_set.global_constraints[0] == constraint
    
    def test_add_unknown_constraint_type(self):
        """Test adding an unknown constraint type raises error."""
        constraint_set = ConstraintSet()
        constraint = MockConstraint("unknown1", "Unknown constraint type")
        
        with pytest.raises(ValueError, match="Unknown constraint type"):
            constraint_set.add_constraint(constraint)
    
    def test_remove_constraint_by_id(self):
        """Test removing a constraint by ID."""
        constraint_set = ConstraintSet()
        constraint1 = MockStructuralConstraint("struct1", "Test constraint 1")
        constraint2 = MockVariableConstraint("var1", "Test constraint 2")
        
        constraint_set.add_constraint(constraint1)
        constraint_set.add_constraint(constraint2)
        
        # Remove structural constraint
        result = constraint_set.remove_constraint("struct1")
        assert result is True
        assert len(constraint_set.structural_constraints) == 0
        assert len(constraint_set.variable_constraints) == 1
        
        # Remove variable constraint
        result = constraint_set.remove_constraint("var1")
        assert result is True
        assert len(constraint_set.variable_constraints) == 0
    
    def test_remove_nonexistent_constraint(self):
        """Test removing a non-existent constraint returns False."""
        constraint_set = ConstraintSet()
        
        result = constraint_set.remove_constraint("nonexistent")
        assert result is False
    
    def test_get_constraint_by_id(self):
        """Test getting a constraint by ID."""
        constraint_set = ConstraintSet()
        constraint = MockStructuralConstraint("struct1", "Test constraint")
        
        constraint_set.add_constraint(constraint)
        
        found_constraint = constraint_set.get_constraint("struct1")
        assert found_constraint == constraint
        
        not_found = constraint_set.get_constraint("nonexistent")
        assert not_found is None
    
    def test_get_all_constraints(self):
        """Test getting all constraints."""
        constraint_set = ConstraintSet()
        struct_constraint = MockStructuralConstraint("struct1")
        var_constraint = MockVariableConstraint("var1")
        global_constraint = MockGlobalConstraint("global1")
        
        constraint_set.add_constraint(struct_constraint)
        constraint_set.add_constraint(var_constraint)
        constraint_set.add_constraint(global_constraint)
        
        all_constraints = constraint_set.get_all_constraints()
        assert len(all_constraints) == 3
        assert struct_constraint in all_constraints
        assert var_constraint in all_constraints
        assert global_constraint in all_constraints
    
    def test_get_constraints_by_type(self):
        """Test getting constraints by type."""
        constraint_set = ConstraintSet()
        struct_constraint = MockStructuralConstraint("struct1")
        var_constraint = MockVariableConstraint("var1")
        global_constraint = MockGlobalConstraint("global1")
        
        constraint_set.add_constraint(struct_constraint)
        constraint_set.add_constraint(var_constraint)
        constraint_set.add_constraint(global_constraint)
        
        # Test getting structural constraints
        structural = constraint_set.get_constraints_by_type("structural")
        assert len(structural) == 1
        assert structural[0] == struct_constraint
        
        # Test getting variable constraints
        variable = constraint_set.get_constraints_by_type("variable")
        assert len(variable) == 1
        assert variable[0] == var_constraint
        
        # Test getting global constraints
        global_constraints = constraint_set.get_constraints_by_type("global")
        assert len(global_constraints) == 1
        assert global_constraints[0] == global_constraint
        
        # Test getting unknown type
        unknown = constraint_set.get_constraints_by_type("unknown")
        assert len(unknown) == 0
    
    def test_count_constraints(self):
        """Test counting constraints by type."""
        constraint_set = ConstraintSet()
        
        # Initially empty
        counts = constraint_set.count_constraints()
        assert counts["structural"] == 0
        assert counts["variable"] == 0
        assert counts["global"] == 0
        assert counts["total"] == 0
        
        # Add constraints
        constraint_set.add_constraint(MockStructuralConstraint("struct1"))
        constraint_set.add_constraint(MockStructuralConstraint("struct2"))
        constraint_set.add_constraint(MockVariableConstraint("var1"))
        constraint_set.add_constraint(MockGlobalConstraint("global1"))
        
        counts = constraint_set.count_constraints()
        assert counts["structural"] == 2
        assert counts["variable"] == 1
        assert counts["global"] == 1
        assert counts["total"] == 4
    
    def test_to_dict(self):
        """Test converting constraint set to dictionary."""
        constraint_set = ConstraintSet()
        struct_constraint = MockStructuralConstraint("struct1", "Structural constraint")
        var_constraint = MockVariableConstraint("var1", "Variable constraint")
        
        constraint_set.add_constraint(struct_constraint)
        constraint_set.add_constraint(var_constraint)
        
        constraint_dict = constraint_set.to_dict()
        
        assert "structural_constraints" in constraint_dict
        assert "variable_constraints" in constraint_dict
        assert "global_constraints" in constraint_dict
        
        assert len(constraint_dict["structural_constraints"]) == 1
        assert constraint_dict["structural_constraints"][0]["id"] == "struct1"
        assert constraint_dict["structural_constraints"][0]["description"] == "Structural constraint"
        
        assert len(constraint_dict["variable_constraints"]) == 1
        assert constraint_dict["variable_constraints"][0]["id"] == "var1"
        
        assert len(constraint_dict["global_constraints"]) == 0
    
    def test_len_operator(self):
        """Test len() operator on constraint set."""
        constraint_set = ConstraintSet()
        
        assert len(constraint_set) == 0
        
        constraint_set.add_constraint(MockStructuralConstraint("struct1"))
        constraint_set.add_constraint(MockVariableConstraint("var1"))
        
        assert len(constraint_set) == 2
    
    def test_string_representation(self):
        """Test string representation of constraint set."""
        constraint_set = ConstraintSet()
        constraint_set.add_constraint(MockStructuralConstraint("struct1"))
        constraint_set.add_constraint(MockVariableConstraint("var1"))
        constraint_set.add_constraint(MockGlobalConstraint("global1"))
        
        str_repr = str(constraint_set)
        assert "ConstraintSet" in str_repr
        assert "structural=1" in str_repr
        assert "variable=1" in str_repr
        assert "global=1" in str_repr
    
    def test_get_constraints_for_component_empty(self):
        """Test getting constraints for component when none have affected_components."""
        constraint_set = ConstraintSet()
        constraint_set.add_constraint(MockStructuralConstraint("struct1"))
        
        # Should return empty list since mock constraints don't have affected_components
        constraints = constraint_set.get_constraints_for_component("comp1")
        assert len(constraints) == 0


class TestComponentCountConstraint:
    """Test cases for ComponentCountConstraint example implementation."""
    
    def create_test_design_object(self, component_count: int) -> DesignObject:
        """Create a test design object with specified number of components."""
        structure = Structure()
        for i in range(component_count):
            component = Component(id=f"comp{i}", type="test")
            structure.add_component(component)
        
        variables = VariableAssignment()
        
        return DesignObject(
            id="test_design",
            structure=structure,
            variables=variables,
            metadata={}
        )
    
    def test_component_count_constraint_satisfied(self):
        """Test component count constraint when satisfied."""
        constraint = ComponentCountConstraint("count1", min_components=1, max_components=5)
        design_object = self.create_test_design_object(3)
        
        assert constraint.is_satisfied(design_object) is True
    
    def test_component_count_constraint_too_few(self):
        """Test component count constraint when too few components."""
        constraint = ComponentCountConstraint("count1", min_components=3, max_components=5)
        design_object = self.create_test_design_object(1)
        
        assert constraint.is_satisfied(design_object) is False
        
        message = constraint.get_violation_message(design_object)
        assert "Component count 1 violates bounds [3, 5]" in message
    
    def test_component_count_constraint_too_many(self):
        """Test component count constraint when too many components."""
        constraint = ComponentCountConstraint("count1", min_components=1, max_components=3)
        design_object = self.create_test_design_object(5)
        
        assert constraint.is_satisfied(design_object) is False
        
        message = constraint.get_violation_message(design_object)
        assert "Component count 5 violates bounds [1, 3]" in message
    
    def test_component_count_constraint_no_max(self):
        """Test component count constraint with no maximum."""
        constraint = ComponentCountConstraint("count1", min_components=2, max_components=None)
        
        # Should pass with many components
        design_object = self.create_test_design_object(100)
        assert constraint.is_satisfied(design_object) is True
        
        # Should fail with too few
        design_object = self.create_test_design_object(1)
        assert constraint.is_satisfied(design_object) is False


class TestVariableRangeConstraint:
    """Test cases for VariableRangeConstraint example implementation."""
    
    def create_test_design_object_with_variable(self, variable_name: str, value: any) -> DesignObject:
        """Create a test design object with a specific variable."""
        structure = Structure()
        variables = VariableAssignment()
        variables.set_variable(variable_name, value)
        
        return DesignObject(
            id="test_design",
            structure=structure,
            variables=variables,
            metadata={}
        )
    
    def test_variable_range_constraint_satisfied(self):
        """Test variable range constraint when satisfied."""
        constraint = VariableRangeConstraint("range1", "test_var", min_value=0, max_value=10)
        design_object = self.create_test_design_object_with_variable("test_var", 5)
        
        assert constraint.is_satisfied(design_object) is True
    
    def test_variable_range_constraint_too_low(self):
        """Test variable range constraint when value too low."""
        constraint = VariableRangeConstraint("range1", "test_var", min_value=5, max_value=10)
        design_object = self.create_test_design_object_with_variable("test_var", 3)
        
        assert constraint.is_satisfied(design_object) is False
        
        message = constraint.get_violation_message(design_object)
        assert "test_var" in message
        assert "value 3 violates range [5, 10]" in message
    
    def test_variable_range_constraint_too_high(self):
        """Test variable range constraint when value too high."""
        constraint = VariableRangeConstraint("range1", "test_var", min_value=0, max_value=5)
        design_object = self.create_test_design_object_with_variable("test_var", 8)
        
        assert constraint.is_satisfied(design_object) is False
        
        message = constraint.get_violation_message(design_object)
        assert "test_var" in message
        assert "value 8 violates range [0, 5]" in message
    
    def test_variable_range_constraint_missing_variable(self):
        """Test variable range constraint when variable is missing."""
        constraint = VariableRangeConstraint("range1", "missing_var", min_value=0, max_value=10)
        design_object = self.create_test_design_object_with_variable("other_var", 5)
        
        assert constraint.is_satisfied(design_object) is False
        
        message = constraint.get_violation_message(design_object)
        assert "missing_var" in message
        assert "is not assigned" in message
    
    def test_variable_range_constraint_no_bounds(self):
        """Test variable range constraint with no bounds."""
        constraint = VariableRangeConstraint("range1", "test_var", min_value=None, max_value=None)
        design_object = self.create_test_design_object_with_variable("test_var", 999999)
        
        # Should always pass when no bounds are set
        assert constraint.is_satisfied(design_object) is True


class TestConstraintEdgeCases:
    """Test edge cases and error conditions for constraints."""
    
    def test_constraint_set_with_mixed_constraints(self):
        """Test constraint set with multiple types of constraints."""
        constraint_set = ConstraintSet()
        
        # Add multiple constraints of different types
        for i in range(3):
            constraint_set.add_constraint(MockStructuralConstraint(f"struct{i}"))
            constraint_set.add_constraint(MockVariableConstraint(f"var{i}"))
            constraint_set.add_constraint(MockGlobalConstraint(f"global{i}"))
        
        assert len(constraint_set) == 9
        assert len(constraint_set.structural_constraints) == 3
        assert len(constraint_set.variable_constraints) == 3
        assert len(constraint_set.global_constraints) == 3
        
        # Test that we can find constraints by ID across all types
        assert constraint_set.get_constraint("struct1") is not None
        assert constraint_set.get_constraint("var2") is not None
        assert constraint_set.get_constraint("global0") is not None
    
    def test_constraint_set_remove_all_constraints(self):
        """Test removing all constraints from a set."""
        constraint_set = ConstraintSet()
        
        # Add constraints
        constraint_set.add_constraint(MockStructuralConstraint("struct1"))
        constraint_set.add_constraint(MockVariableConstraint("var1"))
        constraint_set.add_constraint(MockGlobalConstraint("global1"))
        
        assert len(constraint_set) == 3
        
        # Remove all constraints
        constraint_set.remove_constraint("struct1")
        constraint_set.remove_constraint("var1")
        constraint_set.remove_constraint("global1")
        
        assert len(constraint_set) == 0
        assert constraint_set.is_empty() is True
    
    def test_constraint_abstract_methods(self):
        """Test that abstract constraint methods must be implemented."""
        # This test ensures that the abstract base class works correctly
        
        class IncompleteConstraint(Constraint):
            pass
        
        # Should not be able to instantiate incomplete constraint
        with pytest.raises(TypeError):
            IncompleteConstraint("test")
    
    def test_constraint_string_representations(self):
        """Test string representations of constraints."""
        constraint = MockStructuralConstraint("test_id", "Test description")
        
        str_repr = str(constraint)
        assert "MockStructuralConstraint" in str_repr
        assert "test_id" in str_repr
        
        repr_str = repr(constraint)
        assert "MockStructuralConstraint" in repr_str
        assert "test_id" in repr_str
        assert "Test description" in repr_str