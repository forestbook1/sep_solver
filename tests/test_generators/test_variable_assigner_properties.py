"""Property-based tests for VariableAssigner component."""

import pytest
from hypothesis import given, strategies as st, assume
from hypothesis.strategies import composite

from sep_solver.generators.variable_assigner import BaseVariableAssigner
from sep_solver.models.structure import Structure, Component, Relationship
from sep_solver.models.variable_assignment import Domain, VariableAssignment
from sep_solver.core.exceptions import VariableAssignmentError


# Test data generators

@composite
def domain_strategy(draw):
    """Generate a valid Domain."""
    name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
    domain_type = draw(st.sampled_from(["int", "float", "string", "bool", "enum", "range"]))
    
    constraints = {}
    if domain_type in ["int", "float", "range"]:
        min_val = draw(st.integers(min_value=0, max_value=50))
        max_val = draw(st.integers(min_value=min_val + 1, max_value=100))
        constraints = {"min": min_val, "max": max_val}
    elif domain_type == "enum":
        values = draw(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5, unique=True))
        constraints = {"values": values}
    elif domain_type == "string":
        default = draw(st.text(min_size=0, max_size=10))
        constraints = {"default": default}
    
    return Domain(name=name, type=domain_type, constraints=constraints)


@composite
def component_with_variables_strategy(draw):
    """Generate a Component with variable properties."""
    component_id = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
    component_type = draw(st.text(min_size=1, max_size=10))
    
    # Generate properties with some variables
    properties = {}
    num_vars = draw(st.integers(min_value=0, max_value=3))
    
    for i in range(num_vars):
        prop_name = f"prop_{i}"
        domain = draw(domain_strategy())
        properties[prop_name] = {
            "variable": {
                "type": domain.type,
                "constraints": domain.constraints
            }
        }
    
    # Add some non-variable properties
    num_regular = draw(st.integers(min_value=0, max_value=2))
    for i in range(num_regular):
        prop_name = f"regular_{i}"
        properties[prop_name] = draw(st.text(min_size=1, max_size=10))
    
    return Component(id=component_id, type=component_type, properties=properties)


@composite
def relationship_with_variables_strategy(draw):
    """Generate a Relationship with variable properties."""
    rel_id = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
    source_id = draw(st.text(min_size=1, max_size=10))
    target_id = draw(st.text(min_size=1, max_size=10))
    rel_type = draw(st.text(min_size=1, max_size=10))
    
    # Generate properties with some variables
    properties = {}
    num_vars = draw(st.integers(min_value=0, max_value=2))
    
    for i in range(num_vars):
        prop_name = f"prop_{i}"
        domain = draw(domain_strategy())
        properties[prop_name] = {
            "variable": {
                "type": domain.type,
                "constraints": domain.constraints
            }
        }
    
    return Relationship(id=rel_id, source_id=source_id, target_id=target_id, type=rel_type, properties=properties)


@composite
def structure_with_variables_strategy(draw):
    """Generate a Structure with variables in components and relationships."""
    # Generate components
    components = draw(st.lists(component_with_variables_strategy(), min_size=1, max_size=3, unique_by=lambda c: c.id))
    
    # Generate relationships (ensure they reference existing components)
    relationships = []
    if len(components) >= 2:
        num_rels = draw(st.integers(min_value=0, max_value=2))
        component_ids = [c.id for c in components]
        
        for i in range(num_rels):
            source_id = draw(st.sampled_from(component_ids))
            target_id = draw(st.sampled_from(component_ids))
            rel = draw(relationship_with_variables_strategy())
            rel.source_id = source_id
            rel.target_id = target_id
            rel.id = f"rel_{i}_{source_id}_{target_id}"
            relationships.append(rel)
    
    return Structure(components=components, relationships=relationships)


class TestVariableAssignmentCompleteness:
    """Property tests for variable assignment completeness."""
    
    @given(structure_with_variables_strategy(), st.sampled_from(["random", "systematic", "heuristic"]))
    def test_property_5_variable_assignment_completeness(self, structure, strategy):
        """**Property 5: Variable Assignment Completeness**
        
        For any structure with defined variables, the assignment process should assign 
        values to all variables within their valid domains and types.
        
        **Validates: Requirements 4.1, 4.2**
        """
        assigner = BaseVariableAssigner(seed=42)  # Use seed for reproducibility
        
        # Get the assignment space to understand what variables exist
        assignment_space = assigner.get_assignment_space(structure)
        
        # Perform variable assignment
        assignment = assigner.assign_variables(structure, strategy=strategy)
        
        # Property: All variables with domains should be assigned
        for domain_name in assignment_space.domains:
            assert assignment.has_variable(domain_name), f"Variable '{domain_name}' was not assigned"
        
        # Property: All assigned values should be valid for their domains
        validation_errors = assignment.validate_all_assignments()
        assert len(validation_errors) == 0, f"Assignment validation failed: {validation_errors}"
        
        # Property: Assignment should be complete
        assert assignment.is_complete(), "Assignment is not complete - some variables with domains are unassigned"
        
        # Property: All assigned values should match their domain types
        for var_name, value in assignment.assignments.items():
            if var_name in assignment.domains:
                domain = assignment.domains[var_name]
                assert domain.is_valid_value(value), f"Value {value} is invalid for domain {domain.type} of variable {var_name}"
    
    @given(structure_with_variables_strategy())
    def test_assignment_determinism_with_seed(self, structure):
        """Test that assignment is deterministic when using the same seed."""
        assigner1 = BaseVariableAssigner(seed=123)
        assigner2 = BaseVariableAssigner(seed=123)
        
        assignment1 = assigner1.assign_variables(structure, strategy="random")
        assignment2 = assigner2.assign_variables(structure, strategy="random")
        
        # Should produce identical assignments with same seed
        assert assignment1.assignments == assignment2.assignments
    
    @given(structure_with_variables_strategy())
    def test_assignment_space_consistency(self, structure):
        """Test that assignment space correctly represents the structure's variables."""
        assigner = BaseVariableAssigner()
        
        assignment_space = assigner.get_assignment_space(structure)
        assignment = assigner.assign_variables(structure)
        
        # Assignment space should contain all variables that get assigned
        for var_name in assignment.assignments:
            if var_name in assignment.domains:  # Only check variables with domains
                assert var_name in assignment_space.domains, f"Variable {var_name} missing from assignment space"
        
        # All domains in assignment space should be valid
        for domain_name, domain in assignment_space.domains.items():
            assert isinstance(domain.name, str)
            assert domain.type in ["int", "float", "string", "bool", "enum", "range"]
    
    @given(structure_with_variables_strategy(), st.sampled_from(["random", "systematic", "heuristic"]))
    def test_different_strategies_produce_valid_assignments(self, structure, strategy):
        """Test that all assignment strategies produce valid assignments."""
        assigner = BaseVariableAssigner(seed=42)
        
        assignment = assigner.assign_variables(structure, strategy=strategy)
        
        # All strategies should produce complete, valid assignments
        assert assignment.is_complete()
        assert len(assignment.validate_all_assignments()) == 0
        assert assignment.is_consistent()
    
    def test_empty_structure_assignment(self):
        """Test assignment on structure with no variables."""
        structure = Structure(
            components=[Component(id="comp1", type="simple", properties={"name": "test"})],
            relationships=[]
        )
        
        assigner = BaseVariableAssigner()
        assignment = assigner.assign_variables(structure)
        
        # Should handle empty variable case gracefully
        assert assignment.is_complete()
        assert assignment.is_consistent()
        assert len(assignment.assignments) == 0
    
    def test_invalid_strategy_raises_error(self):
        """Test that invalid strategy raises appropriate error."""
        structure = Structure(components=[], relationships=[])
        assigner = BaseVariableAssigner()
        
        with pytest.raises(VariableAssignmentError, match="Unknown assignment strategy"):
            assigner.assign_variables(structure, strategy="invalid_strategy")


class TestVariableAssignmentModification:
    """Tests for variable assignment modification."""
    
    @given(structure_with_variables_strategy())
    def test_modify_assignment_preserves_validity(self, structure):
        """Test that modifying assignments preserves validity."""
        assigner = BaseVariableAssigner(seed=42)
        
        # Skip if no variables
        assignment_space = assigner.get_assignment_space(structure)
        assume(len(assignment_space.domains) > 0)
        
        original_assignment = assigner.assign_variables(structure)
        
        # Pick a variable to modify
        var_name = list(original_assignment.assignments.keys())[0]
        domain = original_assignment.domains[var_name]
        
        # Generate a new valid value (different from current if possible)
        current_value = original_assignment.get_variable(var_name)
        new_value = None
        
        if domain.type == "int":
            min_val = domain.constraints.get("min", 0)
            max_val = domain.constraints.get("max", 100)
            # Try to find a different value
            if min_val < max_val:
                new_value = min_val if current_value != min_val else max_val
            else:
                new_value = min_val  # Only one possible value
        elif domain.type == "bool":
            new_value = not current_value
        elif domain.type == "enum":
            values = domain.constraints.get("values", [])
            # Try to find a different value
            different_values = [v for v in values if v != current_value]
            new_value = different_values[0] if different_values else values[0]
        elif domain.type == "float":
            min_val = domain.constraints.get("min", 0.0)
            max_val = domain.constraints.get("max", 1.0)
            # Try to find a different value
            if abs(max_val - min_val) > 0.001:  # Ensure there's room for difference
                new_value = min_val if abs(current_value - min_val) > 0.001 else max_val
            else:
                new_value = min_val  # Only one practical value
        else:
            # For other types, use sample value
            new_value = domain.get_sample_value()
        
        # Modify the assignment
        modified_assignment = assigner.modify_assignment(original_assignment, var_name, new_value)
        
        # Modified assignment should still be valid
        assert modified_assignment.is_complete()
        assert len(modified_assignment.validate_all_assignments()) == 0
        assert modified_assignment.is_consistent()
        
        # The specific variable should have the new value
        assert modified_assignment.get_variable(var_name) == new_value
        
        # Original assignment should be unchanged (unless new_value == current_value due to constraints)
        if new_value != current_value:
            assert original_assignment.get_variable(var_name) != new_value
    
    def test_modify_assignment_invalid_value_raises_error(self):
        """Test that modifying with invalid value raises error."""
        from sep_solver.models.variable_assignment import VariableAssignment, Domain
        
        assignment = VariableAssignment()
        domain = Domain(name="test_var", type="int", constraints={"min": 0, "max": 10})
        assignment.add_domain(domain)
        assignment.set_variable("test_var", 5)
        
        assigner = BaseVariableAssigner()
        
        # Try to set invalid value
        with pytest.raises(VariableAssignmentError, match="not valid for variable"):
            assigner.modify_assignment(assignment, "test_var", 15)  # Outside range
    
    def test_modify_nonexistent_variable(self):
        """Test modifying a variable that doesn't exist."""
        from sep_solver.models.variable_assignment import VariableAssignment
        
        assignment = VariableAssignment()
        assigner = BaseVariableAssigner()
        
        # Should work for variables without domains
        modified = assigner.modify_assignment(assignment, "new_var", "value")
        assert modified.get_variable("new_var") == "value"


@composite
def structure_with_dependencies_strategy(draw):
    """Generate a Structure with variables that have dependencies."""
    # Create a simple structure with dependent variables
    component_id = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
    
    # Create component with multiple variables where some depend on others
    properties = {}
    
    # Base variable (no dependencies)
    base_domain = draw(domain_strategy())
    properties["base_var"] = {
        "variable": {
            "type": base_domain.type,
            "constraints": base_domain.constraints
        }
    }
    
    # Dependent variable (depends on base_var)
    dep_domain = draw(domain_strategy())
    properties["dep_var"] = {
        "variable": {
            "type": dep_domain.type,
            "constraints": dep_domain.constraints,
            "depends_on": ["base_var"]
        }
    }
    
    # Optional: Add a variable that depends on the dependent variable (chain)
    if draw(st.booleans()):
        chain_domain = draw(domain_strategy())
        properties["chain_var"] = {
            "variable": {
                "type": chain_domain.type,
                "constraints": chain_domain.constraints,
                "depends_on": ["dep_var"]
            }
        }
    
    component = Component(id=component_id, type="test", properties=properties)
    return Structure(components=[component], relationships=[])


class TestDependencySatisfaction:
    """Property tests for dependency satisfaction."""
    
    @given(structure_with_dependencies_strategy(), st.sampled_from(["random", "systematic", "heuristic"]))
    def test_property_6_dependency_satisfaction(self, structure, strategy):
        """**Property 6: Dependency Satisfaction**
        
        For any structure with variable dependencies, all assigned values should 
        satisfy the dependency relationships.
        
        **Validates: Requirements 4.4**
        """
        assigner = BaseVariableAssigner(seed=42)
        
        # Perform variable assignment
        assignment = assigner.assign_variables(structure, strategy=strategy)
        
        # Property: All dependencies should be satisfied
        dependency_violations = assigner.validate_dependencies(assignment)
        assert len(dependency_violations) == 0, f"Dependency violations found: {dependency_violations}"
        
        # Property: Assignment should be consistent
        assert assignment.is_consistent(), "Assignment is not consistent with dependencies"
        
        # Property: All variables in dependency chains should be assigned
        for var_name, deps in assignment.dependencies.items():
            if var_name in assignment.assignments:
                for dep in deps:
                    assert dep in assignment.assignments, f"Dependency '{dep}' of variable '{var_name}' is not assigned"
    
    @given(structure_with_dependencies_strategy())
    def test_dependency_resolution_after_modification(self, structure):
        """Test that dependency conflicts are resolved after modification."""
        assigner = BaseVariableAssigner(seed=42)
        
        # Get initial assignment
        assignment = assigner.assign_variables(structure, strategy="systematic")
        
        # Find a variable that has dependents
        dependent_vars = []
        for var_name, deps in assignment.dependencies.items():
            for dep in deps:
                if dep in assignment.assignments:
                    dependent_vars.append(dep)
        
        if not dependent_vars:
            # No dependencies to test
            return
        
        # Pick a variable that others depend on
        base_var = dependent_vars[0]
        domain = assignment.domains[base_var]
        
        # Generate a new value
        if domain.type == "int":
            min_val = domain.constraints.get("min", 0)
            max_val = domain.constraints.get("max", 100)
            current_val = assignment.get_variable(base_var)
            new_value = min_val if current_val != min_val else max_val
        elif domain.type == "bool":
            new_value = not assignment.get_variable(base_var)
        else:
            new_value = domain.get_sample_value()
        
        # Modify the assignment
        modified_assignment = assigner.modify_assignment(assignment, base_var, new_value)
        
        # Dependencies should still be satisfied
        dependency_violations = assigner.validate_dependencies(modified_assignment)
        assert len(dependency_violations) == 0, f"Dependencies violated after modification: {dependency_violations}"
        
        # Assignment should still be consistent
        assert modified_assignment.is_consistent(), "Assignment inconsistent after modification"
    
    @given(structure_with_dependencies_strategy())
    def test_batch_modification_preserves_dependencies(self, structure):
        """Test that batch modifications preserve dependency relationships."""
        assigner = BaseVariableAssigner(seed=42)
        
        # Get initial assignment
        assignment = assigner.assign_variables(structure, strategy="systematic")
        
        # Skip if no variables to modify
        if len(assignment.assignments) == 0:
            return
        
        # Create batch modifications (modify up to 2 variables)
        modifications = {}
        var_names = list(assignment.assignments.keys())[:2]
        
        for var_name in var_names:
            domain = assignment.domains[var_name]
            
            if domain.type == "int":
                min_val = domain.constraints.get("min", 0)
                max_val = domain.constraints.get("max", 100)
                current_val = assignment.get_variable(var_name)
                new_value = min_val if current_val != min_val else max_val
            elif domain.type == "bool":
                new_value = not assignment.get_variable(var_name)
            else:
                new_value = domain.get_sample_value()
            
            modifications[var_name] = new_value
        
        # Apply batch modifications
        modified_assignment = assigner.modify_assignment_batch(assignment, modifications)
        
        # Dependencies should still be satisfied
        dependency_violations = assigner.validate_dependencies(modified_assignment)
        assert len(dependency_violations) == 0, f"Dependencies violated after batch modification: {dependency_violations}"
        
        # Assignment should still be consistent
        assert modified_assignment.is_consistent(), "Assignment inconsistent after batch modification"
    
    def test_circular_dependency_handling(self):
        """Test handling of circular dependencies."""
        from sep_solver.models.variable_assignment import VariableAssignment, Domain
        
        # Create assignment with circular dependencies
        assignment = VariableAssignment()
        
        domain1 = Domain(name="var1", type="int", constraints={"min": 0, "max": 10})
        domain2 = Domain(name="var2", type="int", constraints={"min": 0, "max": 10})
        
        assignment.add_domain(domain1)
        assignment.add_domain(domain2)
        
        # Create circular dependency
        assignment.add_dependency("var1", ["var2"])
        assignment.add_dependency("var2", ["var1"])
        
        assigner = BaseVariableAssigner()
        
        # Should handle circular dependencies gracefully
        # (topological sort should fall back to original order)
        sorted_vars = assigner._topological_sort(assignment)
        assert len(sorted_vars) == 2
        assert "var1" in sorted_vars
        assert "var2" in sorted_vars
    
    def test_dependency_validation_with_missing_variables(self):
        """Test dependency validation when some variables are missing."""
        from sep_solver.models.variable_assignment import VariableAssignment, Domain
        
        assignment = VariableAssignment()
        
        domain = Domain(name="var1", type="int")
        assignment.add_domain(domain)
        assignment.add_dependency("var1", ["missing_var"])
        assignment.set_variable("var1", 5)
        
        assigner = BaseVariableAssigner()
        
        # Should detect missing dependency
        violations = assigner.validate_dependencies(assignment)
        assert len(violations) > 0
        assert "missing_var" in violations[0]
    
    def test_dependency_resolution_success(self):
        """Test successful dependency conflict resolution."""
        from sep_solver.models.variable_assignment import VariableAssignment, Domain
        
        assignment = VariableAssignment()
        
        # Create variables with dependencies
        domain1 = Domain(name="base", type="int", constraints={"min": 0, "max": 10})
        domain2 = Domain(name="dependent", type="int", constraints={"min": 0, "max": 10})
        
        assignment.add_domain(domain1)
        assignment.add_domain(domain2)
        assignment.add_dependency("dependent", ["base"])
        
        # Assign only the dependent variable (violates dependency)
        assignment.set_variable("dependent", 5)
        
        assigner = BaseVariableAssigner()
        
        # Should resolve by assigning the base variable
        resolved = assigner.resolve_dependency_conflicts(assignment)
        
        # Both variables should now be assigned
        assert resolved.has_variable("base")
        assert resolved.has_variable("dependent")
        
        # Dependencies should be satisfied
        violations = assigner.validate_dependencies(resolved)
        assert len(violations) == 0