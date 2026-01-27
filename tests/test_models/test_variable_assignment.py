"""Unit tests for VariableAssignment and Domain classes."""

import pytest
from sep_solver.models.variable_assignment import VariableAssignment, Domain, AssignmentSpace


class TestDomain:
    """Test cases for the Domain class."""
    
    def test_domain_creation(self):
        """Test basic domain creation."""
        domain = Domain(name="speed", type="int", constraints={"min": 0, "max": 100})
        assert domain.name == "speed"
        assert domain.type == "int"
        assert domain.constraints == {"min": 0, "max": 100}
    
    def test_domain_creation_with_defaults(self):
        """Test domain creation with default constraints."""
        domain = Domain(name="enabled", type="bool")
        assert domain.name == "enabled"
        assert domain.type == "bool"
        assert domain.constraints == {}
    
    def test_int_domain_validation(self):
        """Test integer domain validation."""
        domain = Domain(name="count", type="int", constraints={"min": 0, "max": 10})
        
        assert domain.is_valid_value(5)
        assert domain.is_valid_value(0)
        assert domain.is_valid_value(10)
        assert not domain.is_valid_value(-1)
        assert not domain.is_valid_value(11)
        assert not domain.is_valid_value("5")
        assert not domain.is_valid_value(5.5)
    
    def test_float_domain_validation(self):
        """Test float domain validation."""
        domain = Domain(name="ratio", type="float", constraints={"min": 0.0, "max": 1.0})
        
        assert domain.is_valid_value(0.5)
        assert domain.is_valid_value(0.0)
        assert domain.is_valid_value(1.0)
        assert domain.is_valid_value(1)  # int should be valid for float (within range)
        assert not domain.is_valid_value(-0.1)
        assert not domain.is_valid_value(1.1)
        assert not domain.is_valid_value(5)  # int outside range should be invalid
        assert not domain.is_valid_value("0.5")
    
    def test_string_domain_validation(self):
        """Test string domain validation."""
        domain = Domain(name="name", type="string")
        
        assert domain.is_valid_value("test")
        assert domain.is_valid_value("")
        assert not domain.is_valid_value(123)
        assert not domain.is_valid_value(None)
    
    def test_bool_domain_validation(self):
        """Test boolean domain validation."""
        domain = Domain(name="enabled", type="bool")
        
        assert domain.is_valid_value(True)
        assert domain.is_valid_value(False)
        assert not domain.is_valid_value(1)
        assert not domain.is_valid_value(0)
        assert not domain.is_valid_value("true")
    
    def test_enum_domain_validation(self):
        """Test enum domain validation."""
        domain = Domain(name="color", type="enum", constraints={"values": ["red", "green", "blue"]})
        
        assert domain.is_valid_value("red")
        assert domain.is_valid_value("green")
        assert domain.is_valid_value("blue")
        assert not domain.is_valid_value("yellow")
        assert not domain.is_valid_value("")
    
    def test_range_domain_validation(self):
        """Test range domain validation."""
        domain = Domain(name="level", type="range", constraints={"min": 1, "max": 5})
        
        assert domain.is_valid_value(3)
        assert domain.is_valid_value(1)
        assert domain.is_valid_value(5)
        assert not domain.is_valid_value(0)
        assert not domain.is_valid_value(6)
    
    def test_get_sample_value_int(self):
        """Test getting sample values for int domain."""
        domain = Domain(name="count", type="int", constraints={"min": 5, "max": 10})
        sample = domain.get_sample_value()
        assert sample == 5
        assert domain.is_valid_value(sample)
    
    def test_get_sample_value_float(self):
        """Test getting sample values for float domain."""
        domain = Domain(name="ratio", type="float", constraints={"min": 0.5, "max": 1.0})
        sample = domain.get_sample_value()
        assert sample == 0.5
        assert domain.is_valid_value(sample)
    
    def test_get_sample_value_string(self):
        """Test getting sample values for string domain."""
        domain = Domain(name="name", type="string", constraints={"default": "test"})
        sample = domain.get_sample_value()
        assert sample == "test"
        assert domain.is_valid_value(sample)
    
    def test_get_sample_value_bool(self):
        """Test getting sample values for bool domain."""
        domain = Domain(name="enabled", type="bool")
        sample = domain.get_sample_value()
        assert sample is False
        assert domain.is_valid_value(sample)
    
    def test_get_sample_value_enum(self):
        """Test getting sample values for enum domain."""
        domain = Domain(name="color", type="enum", constraints={"values": ["red", "green", "blue"]})
        sample = domain.get_sample_value()
        assert sample == "red"
        assert domain.is_valid_value(sample)
    
    def test_domain_serialization(self):
        """Test domain to_dict and from_dict."""
        original = Domain(name="speed", type="int", constraints={"min": 0, "max": 100})
        data = original.to_dict()
        
        expected = {
            "name": "speed",
            "type": "int",
            "constraints": {"min": 0, "max": 100}
        }
        assert data == expected
        
        restored = Domain.from_dict(data)
        assert restored.name == original.name
        assert restored.type == original.type
        assert restored.constraints == original.constraints


class TestVariableAssignment:
    """Test cases for the VariableAssignment class."""
    
    def test_empty_assignment_creation(self):
        """Test creating an empty variable assignment."""
        assignment = VariableAssignment()
        assert len(assignment.assignments) == 0
        assert len(assignment.domains) == 0
        assert len(assignment.dependencies) == 0
    
    def test_add_domain(self):
        """Test adding domains to assignment."""
        assignment = VariableAssignment()
        domain = Domain(name="speed", type="int", constraints={"min": 0, "max": 100})
        
        assignment.add_domain(domain)
        assert "speed" in assignment.domains
        assert assignment.domains["speed"] == domain
    
    def test_set_variable_valid(self):
        """Test setting valid variable values."""
        assignment = VariableAssignment()
        domain = Domain(name="speed", type="int", constraints={"min": 0, "max": 100})
        assignment.add_domain(domain)
        
        assignment.set_variable("speed", 50)
        assert assignment.get_variable("speed") == 50
    
    def test_set_variable_invalid_domain(self):
        """Test setting invalid variable values."""
        assignment = VariableAssignment()
        domain = Domain(name="speed", type="int", constraints={"min": 0, "max": 100})
        assignment.add_domain(domain)
        
        with pytest.raises(ValueError, match="Value 150 is not valid for domain speed"):
            assignment.set_variable("speed", 150)
    
    def test_set_variable_no_domain(self):
        """Test setting variable without domain (should work)."""
        assignment = VariableAssignment()
        assignment.set_variable("unknown", "value")
        assert assignment.get_variable("unknown") == "value"
    
    def test_get_variable_missing(self):
        """Test getting missing variable."""
        assignment = VariableAssignment()
        
        with pytest.raises(KeyError):
            assignment.get_variable("missing")
    
    def test_has_variable(self):
        """Test checking if variable exists."""
        assignment = VariableAssignment()
        assignment.set_variable("test", "value")
        
        assert assignment.has_variable("test")
        assert not assignment.has_variable("missing")
    
    def test_add_dependency(self):
        """Test adding variable dependencies."""
        assignment = VariableAssignment()
        assignment.add_dependency("var1", ["var2", "var3"])
        
        assert "var1" in assignment.dependencies
        assert assignment.dependencies["var1"] == ["var2", "var3"]
    
    def test_get_unassigned_variables(self):
        """Test getting unassigned variables."""
        assignment = VariableAssignment()
        
        # Add domains
        domain1 = Domain(name="var1", type="int")
        domain2 = Domain(name="var2", type="int")
        domain3 = Domain(name="var3", type="int")
        assignment.add_domain(domain1)
        assignment.add_domain(domain2)
        assignment.add_domain(domain3)
        
        # Assign only some variables
        assignment.set_variable("var1", 10)
        assignment.set_variable("var2", 20)
        
        unassigned = assignment.get_unassigned_variables()
        assert unassigned == {"var3"}
    
    def test_is_consistent_no_dependencies(self):
        """Test consistency check with no dependencies."""
        assignment = VariableAssignment()
        assignment.set_variable("var1", 10)
        
        assert assignment.is_consistent()
    
    def test_is_consistent_satisfied_dependencies(self):
        """Test consistency check with satisfied dependencies."""
        assignment = VariableAssignment()
        assignment.set_variable("var1", 10)
        assignment.set_variable("var2", 20)
        assignment.add_dependency("var1", ["var2"])
        
        assert assignment.is_consistent()
    
    def test_is_consistent_unsatisfied_dependencies(self):
        """Test consistency check with unsatisfied dependencies."""
        assignment = VariableAssignment()
        assignment.set_variable("var1", 10)
        assignment.add_dependency("var1", ["var2"])  # var2 not assigned
        
        assert not assignment.is_consistent()
    
    def test_is_complete_empty(self):
        """Test completeness check with no domains."""
        assignment = VariableAssignment()
        assert assignment.is_complete()
    
    def test_is_complete_all_assigned(self):
        """Test completeness check with all variables assigned."""
        assignment = VariableAssignment()
        
        domain1 = Domain(name="var1", type="int")
        domain2 = Domain(name="var2", type="int")
        assignment.add_domain(domain1)
        assignment.add_domain(domain2)
        
        assignment.set_variable("var1", 10)
        assignment.set_variable("var2", 20)
        
        assert assignment.is_complete()
    
    def test_is_complete_partial_assignment(self):
        """Test completeness check with partial assignment."""
        assignment = VariableAssignment()
        
        domain1 = Domain(name="var1", type="int")
        domain2 = Domain(name="var2", type="int")
        assignment.add_domain(domain1)
        assignment.add_domain(domain2)
        
        assignment.set_variable("var1", 10)
        # var2 not assigned
        
        assert not assignment.is_complete()
    
    def test_validate_all_assignments_valid(self):
        """Test validation with all valid assignments."""
        assignment = VariableAssignment()
        
        domain = Domain(name="speed", type="int", constraints={"min": 0, "max": 100})
        assignment.add_domain(domain)
        assignment.set_variable("speed", 50)
        
        errors = assignment.validate_all_assignments()
        assert len(errors) == 0
    
    def test_validate_all_assignments_invalid(self):
        """Test validation with invalid assignments."""
        assignment = VariableAssignment()
        
        domain = Domain(name="speed", type="int", constraints={"min": 0, "max": 100})
        assignment.add_domain(domain)
        
        # Bypass domain validation by setting directly
        assignment.assignments["speed"] = 150
        
        errors = assignment.validate_all_assignments()
        assert len(errors) == 1
        assert "speed" in errors[0]
        assert "invalid value" in errors[0]
    
    def test_serialization_round_trip(self):
        """Test serialization and deserialization."""
        assignment = VariableAssignment()
        
        # Add domain and assignment
        domain = Domain(name="speed", type="int", constraints={"min": 0, "max": 100})
        assignment.add_domain(domain)
        assignment.set_variable("speed", 50)
        assignment.add_dependency("speed", ["power"])
        
        # Serialize
        data = assignment.to_dict()
        
        # Deserialize
        restored = VariableAssignment.from_dict(data)
        
        assert restored.assignments == assignment.assignments
        assert restored.dependencies == assignment.dependencies
        assert len(restored.domains) == len(assignment.domains)
        assert restored.domains["speed"].name == assignment.domains["speed"].name
    
    def test_copy(self):
        """Test copying variable assignment."""
        assignment = VariableAssignment()
        
        domain = Domain(name="speed", type="int")
        assignment.add_domain(domain)
        assignment.set_variable("speed", 50)
        assignment.add_dependency("speed", ["power"])
        
        copy = assignment.copy()
        
        assert copy == assignment
        assert copy is not assignment
        assert copy.assignments is not assignment.assignments
        assert copy.domains is not assignment.domains
        assert copy.dependencies is not assignment.dependencies
    
    def test_equality(self):
        """Test equality comparison."""
        assignment1 = VariableAssignment()
        assignment2 = VariableAssignment()
        
        # Empty assignments should be equal
        assert assignment1 == assignment2
        
        # Add same data to both
        domain = Domain(name="speed", type="int")
        assignment1.add_domain(domain)
        assignment2.add_domain(domain)
        assignment1.set_variable("speed", 50)
        assignment2.set_variable("speed", 50)
        
        assert assignment1 == assignment2
        
        # Different assignments should not be equal
        assignment2.set_variable("speed", 60)
        assert assignment1 != assignment2
    
    def test_equality_different_types(self):
        """Test equality with different types."""
        assignment = VariableAssignment()
        assert assignment != "not an assignment"
        assert assignment != 42
        assert assignment != None
    
    def test_hash(self):
        """Test hashing for use in sets and dictionaries."""
        assignment1 = VariableAssignment()
        assignment2 = VariableAssignment()
        
        assignment1.set_variable("speed", 50)
        assignment2.set_variable("speed", 50)
        
        # Equal assignments should have same hash
        assert hash(assignment1) == hash(assignment2)
        
        # Can be used in sets
        assignment_set = {assignment1, assignment2}
        assert len(assignment_set) == 1
    
    def test_string_representation(self):
        """Test string representation."""
        assignment = VariableAssignment()
        
        domain = Domain(name="speed", type="int")
        assignment.add_domain(domain)
        assignment.set_variable("speed", 50)
        
        str_repr = str(assignment)
        assert "VariableAssignment" in str_repr
        assert "assigned=1" in str_repr
        assert "domains=1" in str_repr


class TestAssignmentSpace:
    """Test cases for the AssignmentSpace class."""
    
    def test_assignment_space_creation(self):
        """Test creating assignment space."""
        domains = {
            "var1": Domain(name="var1", type="int", constraints={"min": 0, "max": 10}),
            "var2": Domain(name="var2", type="bool")
        }
        dependencies = {"var1": ["var2"]}
        
        space = AssignmentSpace(domains, dependencies)
        assert space.domains == domains
        assert space.dependencies == dependencies
    
    def test_assignment_space_no_dependencies(self):
        """Test creating assignment space without dependencies."""
        domains = {
            "var1": Domain(name="var1", type="int")
        }
        
        space = AssignmentSpace(domains)
        assert space.domains == domains
        assert space.dependencies == {}
    
    def test_get_variable_count(self):
        """Test getting variable count."""
        domains = {
            "var1": Domain(name="var1", type="int"),
            "var2": Domain(name="var2", type="bool"),
            "var3": Domain(name="var3", type="string")
        }
        
        space = AssignmentSpace(domains)
        assert space.get_variable_count() == 3
    
    def test_get_domain_size_enum(self):
        """Test getting domain size for enum."""
        domain = Domain(name="color", type="enum", constraints={"values": ["red", "green", "blue"]})
        domains = {"color": domain}
        
        space = AssignmentSpace(domains)
        assert space.get_domain_size("color") == 3
    
    def test_get_domain_size_bool(self):
        """Test getting domain size for boolean."""
        domain = Domain(name="enabled", type="bool")
        domains = {"enabled": domain}
        
        space = AssignmentSpace(domains)
        assert space.get_domain_size("enabled") == 2
    
    def test_get_domain_size_int_range(self):
        """Test getting domain size for integer range."""
        domain = Domain(name="count", type="int", constraints={"min": 1, "max": 5})
        domains = {"count": domain}
        
        space = AssignmentSpace(domains)
        assert space.get_domain_size("count") == 5  # 1, 2, 3, 4, 5
    
    def test_get_domain_size_range_type(self):
        """Test getting domain size for range type."""
        domain = Domain(name="level", type="range", constraints={"min": 0, "max": 2})
        domains = {"level": domain}
        
        space = AssignmentSpace(domains)
        assert space.get_domain_size("level") == 3  # 0, 1, 2
    
    def test_get_domain_size_infinite(self):
        """Test getting domain size for infinite domains."""
        domain = Domain(name="value", type="float")  # No constraints = infinite
        domains = {"value": domain}
        
        space = AssignmentSpace(domains)
        assert space.get_domain_size("value") is None
    
    def test_get_domain_size_missing_variable(self):
        """Test getting domain size for missing variable."""
        space = AssignmentSpace({})
        assert space.get_domain_size("missing") is None
    
    def test_estimate_total_combinations_finite(self):
        """Test estimating total combinations for finite domains."""
        domains = {
            "bool_var": Domain(name="bool_var", type="bool"),  # 2 values
            "enum_var": Domain(name="enum_var", type="enum", constraints={"values": ["a", "b", "c"]}),  # 3 values
            "int_var": Domain(name="int_var", type="int", constraints={"min": 1, "max": 2})  # 2 values
        }
        
        space = AssignmentSpace(domains)
        assert space.estimate_total_combinations() == 12  # 2 * 3 * 2
    
    def test_estimate_total_combinations_infinite(self):
        """Test estimating total combinations with infinite domain."""
        domains = {
            "bool_var": Domain(name="bool_var", type="bool"),  # 2 values
            "float_var": Domain(name="float_var", type="float")  # infinite
        }
        
        space = AssignmentSpace(domains)
        assert space.estimate_total_combinations() is None
    
    def test_estimate_total_combinations_empty(self):
        """Test estimating total combinations for empty space."""
        space = AssignmentSpace({})
        assert space.estimate_total_combinations() == 1  # Empty product = 1


class TestVariableAssignmentEdgeCases:
    """Test edge cases and error conditions for VariableAssignment."""
    
    def test_domain_validation_edge_cases(self):
        """Test domain validation with edge cases."""
        # Test with None constraints
        domain = Domain(name="test", type="int")
        assert domain.is_valid_value(42)
        
        # Test enum with empty values
        domain = Domain(name="empty_enum", type="enum", constraints={"values": []})
        assert not domain.is_valid_value("anything")
        
        # Test range with only min constraint
        domain = Domain(name="min_only", type="range", constraints={"min": 5})
        assert domain.is_valid_value(10)
        assert not domain.is_valid_value(3)
        
        # Test range with only max constraint
        domain = Domain(name="max_only", type="range", constraints={"max": 10})
        assert domain.is_valid_value(5)
        assert not domain.is_valid_value(15)
    
    def test_assignment_with_circular_dependencies(self):
        """Test assignment with circular dependencies."""
        assignment = VariableAssignment()
        assignment.set_variable("var1", 10)
        assignment.set_variable("var2", 20)
        
        # Create circular dependency
        assignment.add_dependency("var1", ["var2"])
        assignment.add_dependency("var2", ["var1"])
        
        # Should still be consistent since both variables are assigned
        assert assignment.is_consistent()
    
    def test_assignment_serialization_empty_constraints(self):
        """Test serialization with empty constraints."""
        assignment = VariableAssignment()
        domain = Domain(name="simple", type="string")  # No constraints
        assignment.add_domain(domain)
        
        data = assignment.to_dict()
        restored = VariableAssignment.from_dict(data)
        
        assert restored.domains["simple"].constraints == {}
    
    def test_multiple_dependencies_per_variable(self):
        """Test variable with multiple dependencies."""
        assignment = VariableAssignment()
        assignment.set_variable("var1", 10)
        assignment.set_variable("var2", 20)
        assignment.set_variable("var3", 30)
        assignment.add_dependency("var1", ["var2", "var3"])
        
        assert assignment.is_consistent()
        
        # Remove one dependency
        assignment.assignments.pop("var2")
        assert not assignment.is_consistent()