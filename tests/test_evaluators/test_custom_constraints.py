"""Unit tests for custom constraint types and evaluator extensibility."""

import pytest
from sep_solver.evaluators.constraint_evaluator import BaseConstraintEvaluator
from sep_solver.evaluators.custom_constraints import (
    ComponentPropertyConstraint, RelationshipPatternConstraint,
    VariableDependencyConstraint, ResourceConstraint, ConnectivityConstraint,
    custom_component_evaluator, custom_resource_evaluator
)
from sep_solver.models.design_object import DesignObject
from sep_solver.models.structure import Structure, Component, Relationship
from sep_solver.models.variable_assignment import VariableAssignment, Domain
from sep_solver.models.constraint_set import ConstraintSet


class TestCustomConstraints:
    """Test custom constraint implementations."""
    
    def test_component_property_constraint(self):
        """Test ComponentPropertyConstraint functionality."""
        # Create a design object with components
        components = [
            Component(id="sensor1", type="sensor", properties={"accuracy": 0.95, "range": 100}),
            Component(id="sensor2", type="sensor", properties={"accuracy": 0.85, "range": 50}),
            Component(id="actuator1", type="actuator", properties={"power": 10})
        ]
        structure = Structure(components=components)
        variables = VariableAssignment()
        design_object = DesignObject(id="test", structure=structure, variables=variables, metadata={})
        
        # Test exact value constraint (satisfied)
        constraint1 = ComponentPropertyConstraint("prop1", "actuator", "power", expected_value=10)
        assert constraint1.is_satisfied(design_object)
        
        # Test exact value constraint (violated)
        constraint2 = ComponentPropertyConstraint("prop2", "actuator", "power", expected_value=20)
        assert not constraint2.is_satisfied(design_object)
        
        # Test range constraint (satisfied)
        constraint3 = ComponentPropertyConstraint("prop3", "sensor", "accuracy", min_value=0.8, max_value=1.0)
        assert constraint3.is_satisfied(design_object)
        
        # Test range constraint (violated)
        constraint4 = ComponentPropertyConstraint("prop4", "sensor", "accuracy", min_value=0.9, max_value=1.0)
        assert not constraint4.is_satisfied(design_object)
        
        # Test missing property
        constraint5 = ComponentPropertyConstraint("prop5", "sensor", "missing_prop", expected_value=1)
        assert not constraint5.is_satisfied(design_object)
        
        # Test non-existent component type
        constraint6 = ComponentPropertyConstraint("prop6", "nonexistent", "prop", expected_value=1)
        assert constraint6.is_satisfied(design_object)  # Vacuously satisfied
    
    def test_relationship_pattern_constraint(self):
        """Test RelationshipPatternConstraint functionality."""
        # Create a design object with relationships
        components = [
            Component(id="sensor1", type="sensor"),
            Component(id="controller1", type="controller"),
            Component(id="actuator1", type="actuator")
        ]
        relationships = [
            Relationship(id="rel1", source_id="sensor1", target_id="controller1", type="feeds"),
            Relationship(id="rel2", source_id="controller1", target_id="actuator1", type="controls")
        ]
        structure = Structure(components=components, relationships=relationships)
        variables = VariableAssignment()
        design_object = DesignObject(id="test", structure=structure, variables=variables, metadata={})
        
        # Test required pattern (satisfied)
        constraint1 = RelationshipPatternConstraint("pat1", "sensor", "controller", "feeds", required=True)
        assert constraint1.is_satisfied(design_object)
        
        # Test required pattern (violated)
        constraint2 = RelationshipPatternConstraint("pat2", "sensor", "actuator", "controls", required=True)
        assert not constraint2.is_satisfied(design_object)
        
        # Test forbidden pattern (satisfied)
        constraint3 = RelationshipPatternConstraint("pat3", "sensor", "actuator", "controls", required=False)
        assert constraint3.is_satisfied(design_object)
        
        # Test forbidden pattern (violated)
        constraint4 = RelationshipPatternConstraint("pat4", "sensor", "controller", "feeds", required=False)
        assert not constraint4.is_satisfied(design_object)
    
    def test_variable_dependency_constraint(self):
        """Test VariableDependencyConstraint functionality."""
        # Create a design object with variables
        variables = VariableAssignment()
        variables.set_variable("temperature", 25)
        variables.set_variable("pressure", 100)
        variables.set_variable("flow_rate", 50)
        
        structure = Structure()
        design_object = DesignObject(id="test", structure=structure, variables=variables, metadata={})
        
        # Test simple dependency (satisfied)
        constraint1 = VariableDependencyConstraint("dep1", "flow_rate", {"temperature": 25})
        assert constraint1.is_satisfied(design_object)
        
        # Test simple dependency (violated)
        constraint2 = VariableDependencyConstraint("dep2", "flow_rate", {"temperature": 30})
        assert not constraint2.is_satisfied(design_object)
        
        # Test range dependency (satisfied)
        constraint3 = VariableDependencyConstraint("dep3", "flow_rate", {
            "temperature": {"min": 20, "max": 30},
            "pressure": {"min": 90, "max": 110}
        })
        assert constraint3.is_satisfied(design_object)
        
        # Test range dependency (violated)
        constraint4 = VariableDependencyConstraint("dep4", "flow_rate", {
            "temperature": {"min": 30, "max": 40}
        })
        assert not constraint4.is_satisfied(design_object)
        
        # Test missing dependency variable
        constraint5 = VariableDependencyConstraint("dep5", "flow_rate", {"missing_var": 10})
        assert not constraint5.is_satisfied(design_object)
        
        # Test non-existent dependent variable
        constraint6 = VariableDependencyConstraint("dep6", "missing_dependent", {"temperature": 25})
        assert constraint6.is_satisfied(design_object)  # Vacuously satisfied
    
    def test_resource_constraint(self):
        """Test ResourceConstraint functionality."""
        # Create a design object with resource usage
        components = [
            Component(id="comp1", type="processor", properties={"power": 10, "memory": 512}),
            Component(id="comp2", type="storage", properties={"power": 5, "memory": 1024})
        ]
        structure = Structure(components=components)
        
        variables = VariableAssignment()
        variables.set_variable("power_overhead", 3)
        variables.set_variable("memory_cache", 256)
        
        design_object = DesignObject(id="test", structure=structure, variables=variables, metadata={})
        
        # Test power constraint (satisfied)
        constraint1 = ResourceConstraint("res1", "power", 20)  # 10 + 5 + 3 = 18 <= 20
        assert constraint1.is_satisfied(design_object)
        
        # Test power constraint (violated)
        constraint2 = ResourceConstraint("res2", "power", 15)  # 18 > 15
        assert not constraint2.is_satisfied(design_object)
        
        # Test memory constraint (satisfied)
        constraint3 = ResourceConstraint("res3", "memory", 2000)  # 512 + 1024 + 256 = 1792 <= 2000
        assert constraint3.is_satisfied(design_object)
        
        # Test memory constraint (violated)
        constraint4 = ResourceConstraint("res4", "memory", 1500)  # 1792 > 1500
        assert not constraint4.is_satisfied(design_object)
    
    def test_connectivity_constraint(self):
        """Test ConnectivityConstraint functionality."""
        # Create connected structure
        components = [
            Component(id="a", type="node"),
            Component(id="b", type="node"),
            Component(id="c", type="node")
        ]
        relationships = [
            Relationship(id="r1", source_id="a", target_id="b", type="connects"),
            Relationship(id="r2", source_id="b", target_id="c", type="connects")
        ]
        connected_structure = Structure(components=components, relationships=relationships)
        
        # Create disconnected structure
        disconnected_relationships = [
            Relationship(id="r1", source_id="a", target_id="b", type="connects")
            # c is isolated
        ]
        disconnected_structure = Structure(components=components, relationships=disconnected_relationships)
        
        # Create fully connected structure
        fully_connected_relationships = [
            Relationship(id="r1", source_id="a", target_id="b", type="connects"),
            Relationship(id="r2", source_id="b", target_id="c", type="connects"),
            Relationship(id="r3", source_id="a", target_id="c", type="connects")
        ]
        fully_connected_structure = Structure(components=components, relationships=fully_connected_relationships)
        
        # Create cyclic structure
        cyclic_relationships = [
            Relationship(id="r1", source_id="a", target_id="b", type="connects"),
            Relationship(id="r2", source_id="b", target_id="c", type="connects"),
            Relationship(id="r3", source_id="c", target_id="a", type="connects")
        ]
        cyclic_structure = Structure(components=components, relationships=cyclic_relationships)
        
        variables = VariableAssignment()
        
        # Test connectivity
        constraint1 = ConnectivityConstraint("conn1", "connected")
        
        connected_obj = DesignObject(id="test1", structure=connected_structure, variables=variables, metadata={})
        assert constraint1.is_satisfied(connected_obj)
        
        disconnected_obj = DesignObject(id="test2", structure=disconnected_structure, variables=variables, metadata={})
        assert not constraint1.is_satisfied(disconnected_obj)
        
        # Test full connectivity
        constraint2 = ConnectivityConstraint("conn2", "fully_connected")
        
        fully_connected_obj = DesignObject(id="test3", structure=fully_connected_structure, variables=variables, metadata={})
        assert constraint2.is_satisfied(fully_connected_obj)
        
        assert not constraint2.is_satisfied(connected_obj)  # Connected but not fully connected
        
        # Test acyclicity
        constraint3 = ConnectivityConstraint("conn3", "acyclic")
        
        assert constraint3.is_satisfied(connected_obj)  # Linear chain is acyclic
        
        cyclic_obj = DesignObject(id="test4", structure=cyclic_structure, variables=variables, metadata={})
        assert not constraint3.is_satisfied(cyclic_obj)  # Contains cycle


class TestConstraintEvaluatorExtensibility:
    """Test the constraint evaluator's extensibility features."""
    
    def test_custom_evaluator_registration(self):
        """Test registering and using custom evaluators."""
        evaluator = BaseConstraintEvaluator()
        
        # Initially no custom evaluators
        assert len(evaluator.get_registered_evaluators()) == 0
        
        # Register a custom evaluator
        evaluator.register_custom_evaluator("ComponentPropertyConstraint", custom_component_evaluator)
        
        # Check registration
        registered = evaluator.get_registered_evaluators()
        assert len(registered) == 1
        assert "ComponentPropertyConstraint" in registered
        
        # Register another evaluator
        evaluator.register_custom_evaluator("ResourceConstraint", custom_resource_evaluator)
        
        registered = evaluator.get_registered_evaluators()
        assert len(registered) == 2
        assert "ResourceConstraint" in registered
        
        # Unregister an evaluator
        success = evaluator.unregister_custom_evaluator("ComponentPropertyConstraint")
        assert success
        
        registered = evaluator.get_registered_evaluators()
        assert len(registered) == 1
        assert "ComponentPropertyConstraint" not in registered
        assert "ResourceConstraint" in registered
        
        # Try to unregister non-existent evaluator
        success = evaluator.unregister_custom_evaluator("NonExistent")
        assert not success
    
    def test_custom_evaluator_usage(self):
        """Test that custom evaluators are actually used during evaluation."""
        # Create a design object that would normally violate a resource constraint
        # Use 95 power with 90 limit: 95 > 90 (violated) but 95 <= 99 (90 * 1.1, satisfied with custom)
        components = [
            Component(id="comp1", type="processor", properties={"power": 95})
        ]
        structure = Structure(components=components)
        variables = VariableAssignment()
        design_object = DesignObject(id="test", structure=structure, variables=variables, metadata={})
        
        # Create a resource constraint that would be violated
        constraint = ResourceConstraint("res1", "power", 90)  # 95 > 90
        constraint_set = ConstraintSet()
        constraint_set.add_constraint(constraint)
        
        # Test with default evaluator (should be violated)
        evaluator1 = BaseConstraintEvaluator(constraint_set)
        result1 = evaluator1.evaluate(design_object)
        assert not result1.is_valid  # Constraint violated
        
        # Test with custom evaluator (should be satisfied due to 10% tolerance: 95 <= 90*1.1=99)
        evaluator2 = BaseConstraintEvaluator(constraint_set)
        evaluator2.register_custom_evaluator("ResourceConstraint", custom_resource_evaluator)
        result2 = evaluator2.evaluate(design_object)
        assert result2.is_valid  # Constraint satisfied with custom evaluator
    
    def test_constraint_set_with_custom_constraints(self):
        """Test using custom constraint types with the constraint evaluator."""
        # Create a design object with fully connected structure
        components = [
            Component(id="sensor1", type="sensor", properties={"accuracy": 0.95}),
            Component(id="controller1", type="controller"),
            Component(id="actuator1", type="actuator")
        ]
        relationships = [
            Relationship(id="rel1", source_id="sensor1", target_id="controller1", type="feeds"),
            Relationship(id="rel2", source_id="controller1", target_id="actuator1", type="controls")
        ]
        structure = Structure(components=components, relationships=relationships)
        
        variables = VariableAssignment()
        variables.set_variable("temperature", 25)
        variables.set_variable("pressure", 100)
        
        design_object = DesignObject(id="test", structure=structure, variables=variables, metadata={})
        
        # Create constraint set with custom constraints
        constraint_set = ConstraintSet()
        
        # Add custom constraints that should all be satisfied
        constraint_set.add_constraint(ComponentPropertyConstraint("prop1", "sensor", "accuracy", min_value=0.9))
        constraint_set.add_constraint(RelationshipPatternConstraint("pat1", "sensor", "controller", "feeds"))
        constraint_set.add_constraint(VariableDependencyConstraint("dep1", "pressure", {"temperature": 25}))
        constraint_set.add_constraint(ConnectivityConstraint("conn1", "connected"))
        
        # Evaluate with constraint evaluator
        evaluator = BaseConstraintEvaluator(constraint_set)
        result = evaluator.evaluate(design_object)
        
        # All constraints should be satisfied
        assert result.is_valid
        assert len(result.violations) == 0
        
        # Test with a violation
        constraint_set.add_constraint(ComponentPropertyConstraint("prop2", "sensor", "accuracy", min_value=0.99))
        
        evaluator2 = BaseConstraintEvaluator(constraint_set)
        result2 = evaluator2.evaluate(design_object)
        
        # Should have one violation
        assert not result2.is_valid
        assert len(result2.violations) == 1
        assert result2.violations[0].constraint_id == "prop2"
    
    def test_constraint_evaluation_by_type_with_custom_constraints(self):
        """Test evaluating custom constraints by type."""
        # Create a design object
        components = [Component(id="comp1", type="processor", properties={"power": 10})]
        structure = Structure(components=components)
        variables = VariableAssignment()
        variables.set_variable("temp", 25)
        design_object = DesignObject(id="test", structure=structure, variables=variables, metadata={})
        
        # Create constraint set with different types of custom constraints
        constraint_set = ConstraintSet()
        constraint_set.add_constraint(ComponentPropertyConstraint("struct1", "processor", "power", max_value=5))  # Violated
        constraint_set.add_constraint(ConnectivityConstraint("struct2", "connected"))  # Satisfied
        constraint_set.add_constraint(VariableDependencyConstraint("var1", "temp", {"nonexistent": 1}))  # Violated
        constraint_set.add_constraint(ResourceConstraint("global1", "power", 5))  # Violated
        
        evaluator = BaseConstraintEvaluator(constraint_set)
        
        # Test structural constraints
        structural_result = evaluator.evaluate_constraints_by_type(design_object, "structural")
        assert not structural_result.is_valid
        assert len(structural_result.violations) == 1  # Only struct1 violated
        
        # Test variable constraints
        variable_result = evaluator.evaluate_constraints_by_type(design_object, "variable")
        assert not variable_result.is_valid
        assert len(variable_result.violations) == 1  # Only var1 violated
        
        # Test global constraints
        global_result = evaluator.evaluate_constraints_by_type(design_object, "global")
        assert not global_result.is_valid
        assert len(global_result.violations) == 1  # Only global1 violated
    
    def test_evaluation_summary_with_custom_constraints(self):
        """Test evaluation summary with custom constraint types."""
        # Create a design object that will violate specific constraints
        components = [Component(id="comp1", type="processor")]  # No properties, isolated
        structure = Structure(components=components)
        variables = VariableAssignment()
        design_object = DesignObject(id="test", structure=structure, variables=variables, metadata={})
        
        # Create constraint set with violations
        constraint_set = ConstraintSet()
        # This will be violated because the component has no "missing" property
        constraint_set.add_constraint(ComponentPropertyConstraint("prop1", "processor", "missing", expected_value=1))
        # This will be satisfied because single component is trivially fully connected
        constraint_set.add_constraint(ConnectivityConstraint("conn1", "fully_connected"))
        # This will be satisfied because no power usage (0) is within limit (10)
        constraint_set.add_constraint(ResourceConstraint("res1", "power", 10))
        
        evaluator = BaseConstraintEvaluator(constraint_set)
        summary = evaluator.get_evaluation_summary(design_object)
        
        # Check summary structure
        assert not summary['is_valid']
        # Only prop1 should be violated
        expected_violations = 1
        assert summary['total_violations'] == expected_violations
        
        # Check violations by type
        expected_types = {
            'ComponentPropertyConstraint': 1
        }
        assert summary['violations_by_type'] == expected_types
        
        # Check violations by severity (all should be errors by default)
        assert summary['violations_by_severity'] == {'error': expected_violations}