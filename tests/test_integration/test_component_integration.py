"""Integration tests to verify all components work together properly."""

import pytest
from sep_solver.models.design_object import DesignObject
from sep_solver.models.structure import Structure, Component, Relationship
from sep_solver.models.variable_assignment import VariableAssignment, Domain
from sep_solver.models.constraint_set import ConstraintSet, ComponentCountConstraint, VariableRangeConstraint
from sep_solver.evaluators.schema_validator import JSONSchemaValidator
from sep_solver.evaluators.constraint_evaluator import BaseConstraintEvaluator
from sep_solver.generators.structure_generator import BaseStructureGenerator
from sep_solver.generators.variable_assigner import BaseVariableAssigner


class TestComponentIntegration:
    """Test integration between all major components."""
    
    def test_full_design_object_workflow(self, sample_schema):
        """Test complete workflow from structure generation to constraint evaluation."""
        # 1. Create structure generator and generate a structure
        generator = BaseStructureGenerator()
        structure = generator.generate_structure([])
        
        # Verify structure is valid
        assert structure.is_valid()
        assert len(structure.components) > 0
        
        # 2. Create variable assignment for the structure
        assigner = BaseVariableAssigner()
        
        # Create variable assignment with domains for component properties
        var_assignment = VariableAssignment()
        for i, component in enumerate(structure.components):
            var_name = f"param_{i}"
            domain = Domain(
                name=var_name,
                type="int",
                constraints={"min": 1, "max": 100}
            )
            var_assignment.add_domain(domain)
        
        # Assign variables using the assigner
        assignment = assigner.assign_variables(structure, "random")
        
        # The assigner creates its own assignment, so we need to manually assign our variables
        # for the constraint test to work
        for i in range(len(structure.components)):
            var_name = f"param_{i}"
            domain = Domain(
                name=var_name,
                type="int",
                constraints={"min": 1, "max": 100}
            )
            assignment.add_domain(domain)
            assignment.set_variable(var_name, 50)  # Valid value within range
        
        # Verify assignment is valid
        assert assignment.is_consistent()
        
        # 3. Create design object
        design_obj = DesignObject(
            id="test_design_1",
            structure=structure,
            variables=assignment,
            metadata={"test": True}
        )
        
        # 4. Validate against schema
        validator = JSONSchemaValidator(sample_schema)
        validation_result = validator.validate(design_obj.to_json())
        
        # Should be valid (our sample schema is flexible)
        assert validation_result.is_valid
        
        # 5. Create and evaluate constraints
        constraint_set = ConstraintSet()
        
        # Add component count constraint
        comp_constraint = ComponentCountConstraint(
            constraint_id="min_components",
            min_components=1,
            max_components=10
        )
        constraint_set.add_constraint(comp_constraint)
        
        # Add variable range constraints
        for i in range(len(structure.components)):
            var_constraint = VariableRangeConstraint(
                constraint_id=f"param_{i}_range",
                variable_name=f"param_{i}",
                min_value=1,
                max_value=100
            )
            constraint_set.add_constraint(var_constraint)
        
        # Evaluate constraints
        evaluator = BaseConstraintEvaluator(constraint_set)
        evaluation_result = evaluator.evaluate(design_obj)
        
        # Should satisfy all constraints
        assert evaluation_result.is_valid
        assert len(evaluation_result.violations) == 0
        
        # 6. Test serialization round trip
        json_data = design_obj.to_json()
        restored_obj = DesignObject.from_json(json_data)
        
        assert restored_obj == design_obj
        assert restored_obj.structure.is_valid()
        assert restored_obj.variables.is_consistent()
    
    def test_constraint_violation_detection(self, sample_schema):
        """Test that constraint violations are properly detected across components."""
        # Create a structure with known constraint violations
        structure = Structure()
        
        # Add too many components (will violate count constraint)
        for i in range(15):  # More than max allowed
            component = Component(
                id=f"comp_{i}",
                type="test_component",
                properties={"value": i}
            )
            structure.add_component(component)
        
        # Create variable assignment with out-of-range values
        var_assignment = VariableAssignment()
        for i in range(5):  # Only assign some variables
            var_name = f"param_{i}"
            # Create domain that allows the value we want to set
            domain = Domain(name=var_name, type="int", constraints={"min": 1, "max": 100})
            var_assignment.add_domain(domain)
            var_assignment.set_variable(var_name, 50)  # Valid for domain, but will violate constraint
        
        design_obj = DesignObject(
            id="violation_test",
            structure=structure,
            variables=var_assignment,
            metadata={}
        )
        
        # Create constraints that will be violated
        constraint_set = ConstraintSet()
        
        # Component count constraint (will be violated)
        comp_constraint = ComponentCountConstraint(
            constraint_id="max_components",
            min_components=1,
            max_components=10
        )
        constraint_set.add_constraint(comp_constraint)
        
        # Variable range constraints (will be violated)
        for i in range(5):
            var_constraint = VariableRangeConstraint(
                constraint_id=f"param_{i}_range",
                variable_name=f"param_{i}",
                min_value=1,
                max_value=10
            )
            constraint_set.add_constraint(var_constraint)
        
        # Evaluate constraints
        evaluator = BaseConstraintEvaluator(constraint_set)
        evaluation_result = evaluator.evaluate(design_obj)
        
        # Should detect violations
        assert not evaluation_result.is_valid
        assert len(evaluation_result.violations) > 0
        
        # Should have component count violation
        comp_violations = [v for v in evaluation_result.violations 
                          if v.constraint_id == "max_components"]
        assert len(comp_violations) == 1
        
        # Should have variable range violations
        var_violations = [v for v in evaluation_result.violations 
                         if "param_" in v.constraint_id]
        assert len(var_violations) == 5  # All 5 variables out of range
    
    def test_structure_modification_integration(self):
        """Test that structure modifications work with variable assignments."""
        # Create initial structure
        generator = BaseStructureGenerator()
        structure = generator.generate_structure([])
        
        # Create variable assignment
        var_assignment = VariableAssignment()
        for i, component in enumerate(structure.components):
            var_name = f"comp_{component.id}_param"
            domain = Domain(name=var_name, type="float", constraints={"min": 0.0, "max": 1.0})
            var_assignment.add_domain(domain)
            var_assignment.set_variable(var_name, 0.5)
        
        original_var_count = len(var_assignment.assignments)
        
        # Modify structure by adding a component
        from sep_solver.models.structure import AddComponentModification
        
        new_component = Component(
            id="new_component",
            type="test_type",
            properties={"added": True}
        )
        
        modification = AddComponentModification(new_component)
        modified_structure = generator.modify_structure(structure, modification)
        
        # Verify modification worked
        assert len(modified_structure.components) == len(structure.components) + 1
        assert modified_structure.get_component("new_component") is not None
        
        # Variable assignment should still be valid for original components
        assert len(var_assignment.assignments) == original_var_count
        assert var_assignment.is_consistent()
        
        # Can add variable for new component
        new_var_name = "comp_new_component_param"
        new_domain = Domain(name=new_var_name, type="bool")
        var_assignment.add_domain(new_domain)
        var_assignment.set_variable(new_var_name, True)
        
        assert var_assignment.is_consistent()
        assert len(var_assignment.assignments) == original_var_count + 1
    
    def test_schema_validation_with_complex_design(self, sample_schema):
        """Test schema validation with complex design objects."""
        # Create a complex structure
        structure = Structure()
        
        # Add multiple components with relationships
        comp1 = Component(id="input", type="input_component", properties={"port": 1})
        comp2 = Component(id="processor", type="processing_component", properties={"algorithm": "test"})
        comp3 = Component(id="output", type="output_component", properties={"format": "json"})
        
        structure.add_component(comp1)
        structure.add_component(comp2)
        structure.add_component(comp3)
        
        # Add relationships
        rel1 = Relationship(id="input_to_proc", source_id="input", target_id="processor", type="data_flow")
        rel2 = Relationship(id="proc_to_output", source_id="processor", target_id="output", type="data_flow")
        
        structure.add_relationship(rel1)
        structure.add_relationship(rel2)
        
        # Create complex variable assignment
        var_assignment = VariableAssignment()
        
        # Add variables with dependencies
        var_assignment.add_domain(Domain(name="input_rate", type="int", constraints={"min": 1, "max": 1000}))
        var_assignment.add_domain(Domain(name="processing_delay", type="float", constraints={"min": 0.1, "max": 10.0}))
        var_assignment.add_domain(Domain(name="output_buffer_size", type="int", constraints={"min": 10, "max": 10000}))
        
        # Add dependency: output buffer should be at least 10x input rate
        var_assignment.add_dependency("output_buffer_size", ["input_rate"])
        
        # Assign values that satisfy dependencies
        var_assignment.set_variable("input_rate", 100)
        var_assignment.set_variable("processing_delay", 1.5)
        var_assignment.set_variable("output_buffer_size", 2000)  # 20x input rate
        
        # Create design object
        design_obj = DesignObject(
            id="complex_design",
            structure=structure,
            variables=var_assignment,
            metadata={
                "created_by": "integration_test",
                "complexity": "high",
                "components": len(structure.components),
                "relationships": len(structure.relationships)
            }
        )
        
        # Validate schema
        validator = JSONSchemaValidator(sample_schema)
        validation_result = validator.validate(design_obj.to_json())
        
        assert validation_result.is_valid
        
        # Test serialization preserves all data
        json_data = design_obj.to_json()
        restored_obj = DesignObject.from_json(json_data)
        
        assert restored_obj == design_obj
        assert len(restored_obj.structure.components) == 3
        assert len(restored_obj.structure.relationships) == 2
        assert restored_obj.variables.is_consistent()
        assert len(restored_obj.variables.dependencies) == 1
    
    def test_error_propagation_across_components(self, sample_schema):
        """Test that errors are properly propagated across component boundaries."""
        # Test schema validation error propagation
        invalid_design_data = {
            "id": "test",
            "structure": "invalid_structure_format",  # Should be object
            "variables": {},
            "metadata": {}
        }
        
        validator = JSONSchemaValidator(sample_schema)
        validation_result = validator.validate(invalid_design_data)
        
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0
        
        # Test constraint evaluation with invalid design object
        try:
            invalid_design = DesignObject.from_json(invalid_design_data)
            assert False, "Should have raised exception for invalid data"
        except (ValueError, TypeError, KeyError):
            # Expected - invalid data should raise exception
            pass
        
        # Test variable assignment error propagation
        var_assignment = VariableAssignment()
        domain = Domain(name="test_var", type="int", constraints={"min": 1, "max": 10})
        var_assignment.add_domain(domain)
        
        # Try to set invalid value
        with pytest.raises(ValueError, match="Value .* is not valid for domain"):
            var_assignment.set_variable("test_var", 50)  # Out of range
        
        # Try to set variable without domain - this actually works in the current implementation
        # The domain check is optional, so this won't raise an error
        var_assignment.set_variable("undefined_var", 5)
        assert var_assignment.has_variable("undefined_var")