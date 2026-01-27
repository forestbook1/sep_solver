"""Property-based tests for constraint evaluation accuracy.

**Feature: sep-solver, Property 7: Constraint Evaluation Accuracy**
**Validates: Requirements 5.1, 5.3, 5.4**

For any design object and constraint set, the evaluation should correctly identify 
all constraint violations and provide specific violation information.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import List, Dict, Any

from sep_solver.evaluators.constraint_evaluator import BaseConstraintEvaluator
from sep_solver.models.design_object import DesignObject
from sep_solver.models.structure import Structure, Component, Relationship
from sep_solver.models.variable_assignment import VariableAssignment, Domain
from sep_solver.models.constraint_set import (
    ConstraintSet, ComponentCountConstraint, VariableRangeConstraint,
    StructuralConstraint, VariableConstraint, GlobalConstraint
)


# Test constraint implementations for property testing
class AlwaysSatisfiedConstraint(StructuralConstraint):
    """A constraint that is always satisfied."""
    
    def __init__(self, constraint_id: str):
        super().__init__(constraint_id, "Always satisfied constraint")
    
    def is_satisfied(self, design_object) -> bool:
        return True
    
    def get_violation_message(self, design_object) -> str:
        return "This constraint should never be violated"


class AlwaysViolatedConstraint(StructuralConstraint):
    """A constraint that is always violated."""
    
    def __init__(self, constraint_id: str):
        super().__init__(constraint_id, "Always violated constraint")
    
    def is_satisfied(self, design_object) -> bool:
        return False
    
    def get_violation_message(self, design_object) -> str:
        return f"Constraint {self.constraint_id} is always violated"


class ComponentTypeConstraint(StructuralConstraint):
    """Constraint that requires specific component types."""
    
    def __init__(self, constraint_id: str, required_type: str):
        super().__init__(constraint_id, f"Requires component of type {required_type}")
        self.required_type = required_type
    
    def is_satisfied(self, design_object) -> bool:
        return any(c.type == self.required_type for c in design_object.structure.components)
    
    def get_violation_message(self, design_object) -> str:
        return f"No component of type '{self.required_type}' found"


class RelationshipCountConstraint(StructuralConstraint):
    """Constraint on the number of relationships."""
    
    def __init__(self, constraint_id: str, min_relationships: int = 0, max_relationships: int = None):
        super().__init__(constraint_id, f"Relationship count constraint")
        self.min_relationships = min_relationships
        self.max_relationships = max_relationships
    
    def is_satisfied(self, design_object) -> bool:
        count = len(design_object.structure.relationships)
        if count < self.min_relationships:
            return False
        if self.max_relationships is not None and count > self.max_relationships:
            return False
        return True
    
    def get_violation_message(self, design_object) -> str:
        count = len(design_object.structure.relationships)
        return f"Relationship count {count} violates bounds [{self.min_relationships}, {self.max_relationships}]"


class VariableExistsConstraint(VariableConstraint):
    """Constraint that requires a specific variable to exist."""
    
    def __init__(self, constraint_id: str, variable_name: str):
        super().__init__(constraint_id, f"Variable {variable_name} must exist")
        self.variable_name = variable_name
    
    def is_satisfied(self, design_object) -> bool:
        return design_object.variables.has_variable(self.variable_name)
    
    def get_violation_message(self, design_object) -> str:
        return f"Required variable '{self.variable_name}' is not assigned"


# Hypothesis strategies for generating test data
@st.composite
def component_strategy(draw):
    """Generate a valid Component."""
    component_id = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    component_type = draw(st.sampled_from(['sensor', 'actuator', 'controller', 'processor', 'storage']))
    properties = draw(st.dictionaries(
        st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text(max_size=10)),
        max_size=3
    ))
    return Component(id=component_id, type=component_type, properties=properties)


@st.composite
def relationship_strategy(draw, component_ids):
    """Generate a valid Relationship given component IDs."""
    if len(component_ids) < 2:
        # Need at least 2 components for a relationship
        assume(False)
    
    rel_id = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    source_id = draw(st.sampled_from(component_ids))
    target_id = draw(st.sampled_from([cid for cid in component_ids if cid != source_id]))
    rel_type = draw(st.sampled_from(['connects', 'controls', 'feeds', 'monitors']))
    properties = draw(st.dictionaries(
        st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text(max_size=10)),
        max_size=2
    ))
    return Relationship(id=rel_id, source_id=source_id, target_id=target_id, type=rel_type, properties=properties)


@st.composite
def structure_strategy(draw):
    """Generate a valid Structure."""
    # Generate components
    components = draw(st.lists(component_strategy(), min_size=0, max_size=5, unique_by=lambda c: c.id))
    component_ids = [c.id for c in components]
    
    # Generate relationships (only if we have components)
    relationships = []
    if len(component_ids) >= 2:
        relationships = draw(st.lists(
            relationship_strategy(component_ids), 
            min_size=0, 
            max_size=min(3, len(component_ids)), 
            unique_by=lambda r: r.id
        ))
    
    return Structure(components=components, relationships=relationships)


@st.composite
def domain_strategy(draw):
    """Generate a valid Domain."""
    name = draw(st.text(min_size=1, max_size=8, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    domain_type = draw(st.sampled_from(['int', 'float', 'string', 'bool', 'enum']))
    
    constraints = {}
    if domain_type in ['int', 'float']:
        min_val = draw(st.integers(min_value=0, max_value=50))
        max_val = draw(st.integers(min_value=min_val + 1, max_value=100))
        constraints = {'min': min_val, 'max': max_val}
    elif domain_type == 'enum':
        values = draw(st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=5, unique=True))
        constraints = {'values': values}
    elif domain_type == 'string':
        constraints = {'default': ''}
    
    return Domain(name=name, type=domain_type, constraints=constraints)


@st.composite
def variable_assignment_strategy(draw):
    """Generate a valid VariableAssignment."""
    # Generate domains
    domains_list = draw(st.lists(domain_strategy(), min_size=0, max_size=4, unique_by=lambda d: d.name))
    domains = {d.name: d for d in domains_list}
    
    # Generate assignments for some of the domains
    assignments = {}
    for domain_name, domain in domains.items():
        if draw(st.booleans()):  # Randomly assign some variables
            if domain.type == 'int':
                min_val = domain.constraints.get('min', 0)
                max_val = domain.constraints.get('max', 100)
                value = draw(st.integers(min_value=min_val, max_value=max_val))
            elif domain.type == 'float':
                min_val = domain.constraints.get('min', 0.0)
                max_val = domain.constraints.get('max', 1.0)
                value = draw(st.floats(min_value=min_val, max_value=max_val, allow_nan=False, allow_infinity=False))
            elif domain.type == 'bool':
                value = draw(st.booleans())
            elif domain.type == 'string':
                value = draw(st.text(max_size=10))
            elif domain.type == 'enum':
                values = domain.constraints.get('values', ['default'])
                value = draw(st.sampled_from(values))
            else:
                continue
            
            assignments[domain_name] = value
    
    # Generate simple dependencies
    dependencies = {}
    domain_names = list(domains.keys())
    if len(domain_names) > 1:
        for name in domain_names:
            if draw(st.booleans()) and len(domain_names) > 1:  # Sometimes add dependencies
                other_names = [n for n in domain_names if n != name]
                deps = draw(st.lists(st.sampled_from(other_names), min_size=0, max_size=2, unique=True))
                if deps:
                    dependencies[name] = deps
    
    return VariableAssignment(assignments=assignments, domains=domains, dependencies=dependencies)


@st.composite
def design_object_strategy(draw):
    """Generate a valid DesignObject."""
    obj_id = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    structure = draw(structure_strategy())
    variables = draw(variable_assignment_strategy())
    metadata = draw(st.dictionaries(
        st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        st.one_of(st.integers(), st.text(max_size=10)),
        max_size=2
    ))
    
    return DesignObject(id=obj_id, structure=structure, variables=variables, metadata=metadata)


@st.composite
def constraint_set_strategy(draw):
    """Generate a ConstraintSet with various constraint types."""
    constraint_set = ConstraintSet()
    
    # Add some structural constraints
    num_structural = draw(st.integers(min_value=0, max_value=3))
    for i in range(num_structural):
        constraint_type = draw(st.sampled_from(['component_count', 'component_type', 'relationship_count', 'always_satisfied', 'always_violated']))
        
        if constraint_type == 'component_count':
            min_components = draw(st.integers(min_value=0, max_value=3))
            max_components = draw(st.integers(min_value=min_components, max_value=5))
            constraint = ComponentCountConstraint(f'comp_count_{i}', min_components, max_components)
        elif constraint_type == 'component_type':
            required_type = draw(st.sampled_from(['sensor', 'actuator', 'controller']))
            constraint = ComponentTypeConstraint(f'comp_type_{i}', required_type)
        elif constraint_type == 'relationship_count':
            min_rels = draw(st.integers(min_value=0, max_value=2))
            max_rels = draw(st.integers(min_value=min_rels, max_value=4))
            constraint = RelationshipCountConstraint(f'rel_count_{i}', min_rels, max_rels)
        elif constraint_type == 'always_satisfied':
            constraint = AlwaysSatisfiedConstraint(f'always_sat_{i}')
        else:  # always_violated
            constraint = AlwaysViolatedConstraint(f'always_viol_{i}')
        
        constraint_set.add_constraint(constraint)
    
    # Add some variable constraints
    num_variable = draw(st.integers(min_value=0, max_value=3))
    for i in range(num_variable):
        constraint_type = draw(st.sampled_from(['variable_range', 'variable_exists']))
        
        if constraint_type == 'variable_range':
            var_name = draw(st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
            min_val = draw(st.integers(min_value=0, max_value=50))
            max_val = draw(st.integers(min_value=min_val, max_value=100))
            constraint = VariableRangeConstraint(f'var_range_{i}', var_name, min_val, max_val)
        else:  # variable_exists
            var_name = draw(st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
            constraint = VariableExistsConstraint(f'var_exists_{i}', var_name)
        
        constraint_set.add_constraint(constraint)
    
    return constraint_set


class TestConstraintEvaluationAccuracy:
    """Property tests for constraint evaluation accuracy."""
    
    @given(design_object_strategy(), constraint_set_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_7_constraint_evaluation_accuracy(self, design_object: DesignObject, constraint_set: ConstraintSet):
        """**Property 7: Constraint Evaluation Accuracy**
        **Validates: Requirements 5.1, 5.3, 5.4**
        
        For any design object and constraint set, the evaluation should correctly identify 
        all constraint violations and provide specific violation information.
        """
        evaluator = BaseConstraintEvaluator(constraint_set)
        
        # Evaluate the design object
        result = evaluator.evaluate(design_object)
        violations = evaluator.get_violations(design_object)
        
        # Property 1: Result validity should match absence of violations
        assert result.is_valid == (len(violations) == 0), \
            f"Result validity {result.is_valid} doesn't match violation count {len(violations)}"
        
        # Property 2: All violations should be in the result
        assert result.violations == violations, \
            "Violations from evaluate() and get_violations() should match"
        
        # Property 3: Each violation should correspond to an actual constraint violation
        all_constraints = constraint_set.get_all_constraints()
        for violation in violations:
            # Find the constraint that was violated
            violated_constraint = None
            for constraint in all_constraints:
                if constraint.constraint_id == violation.constraint_id:
                    violated_constraint = constraint
                    break
            
            assert violated_constraint is not None, \
                f"Violation references non-existent constraint {violation.constraint_id}"
            
            # Verify the constraint is actually violated
            is_satisfied = evaluator.evaluate_constraint(violated_constraint, design_object)
            assert not is_satisfied, \
                f"Constraint {violation.constraint_id} reported as violated but actually satisfied"
        
        # Property 4: No satisfied constraints should appear in violations
        satisfied_constraints = []
        for constraint in all_constraints:
            if evaluator.evaluate_constraint(constraint, design_object):
                satisfied_constraints.append(constraint.constraint_id)
        
        violated_constraint_ids = {v.constraint_id for v in violations}
        for satisfied_id in satisfied_constraints:
            assert satisfied_id not in violated_constraint_ids, \
                f"Satisfied constraint {satisfied_id} appears in violations"
        
        # Property 5: Each violation should have meaningful information
        for violation in violations:
            assert violation.constraint_id, "Violation should have constraint ID"
            assert violation.constraint_type, "Violation should have constraint type"
            assert violation.message, "Violation should have message"
            assert violation.severity in ['error', 'warning', 'info'], \
                f"Invalid severity: {violation.severity}"
            assert isinstance(violation.context, dict), "Violation context should be a dict"
    
    @given(design_object_strategy())
    @settings(max_examples=50, deadline=None)
    def test_empty_constraint_set_always_valid(self, design_object: DesignObject):
        """Empty constraint set should always result in valid evaluation."""
        empty_constraint_set = ConstraintSet()
        evaluator = BaseConstraintEvaluator(empty_constraint_set)
        
        result = evaluator.evaluate(design_object)
        violations = evaluator.get_violations(design_object)
        
        assert result.is_valid, "Empty constraint set should always be valid"
        assert len(violations) == 0, "Empty constraint set should have no violations"
        assert len(result.violations) == 0, "Result should have no violations"
    
    @given(design_object_strategy())
    @settings(max_examples=50, deadline=None)
    def test_no_constraint_set_always_valid(self, design_object: DesignObject):
        """No constraint set should always result in valid evaluation."""
        evaluator = BaseConstraintEvaluator()  # No constraint set
        
        result = evaluator.evaluate(design_object)
        violations = evaluator.get_violations(design_object)
        
        assert result.is_valid, "No constraint set should always be valid"
        assert len(violations) == 0, "No constraint set should have no violations"
        assert len(result.violations) == 0, "Result should have no violations"
    
    @given(design_object_strategy())
    @settings(max_examples=50, deadline=None)
    def test_always_satisfied_constraints(self, design_object: DesignObject):
        """Always satisfied constraints should never produce violations."""
        constraint_set = ConstraintSet()
        
        # Add multiple always-satisfied constraints
        for i in range(3):
            constraint_set.add_constraint(AlwaysSatisfiedConstraint(f'always_sat_{i}'))
        
        evaluator = BaseConstraintEvaluator(constraint_set)
        result = evaluator.evaluate(design_object)
        violations = evaluator.get_violations(design_object)
        
        assert result.is_valid, "Always satisfied constraints should result in valid evaluation"
        assert len(violations) == 0, "Always satisfied constraints should have no violations"
    
    @given(design_object_strategy())
    @settings(max_examples=50, deadline=None)
    def test_always_violated_constraints(self, design_object: DesignObject):
        """Always violated constraints should always produce violations."""
        constraint_set = ConstraintSet()
        
        # Add multiple always-violated constraints
        num_constraints = 3
        for i in range(num_constraints):
            constraint_set.add_constraint(AlwaysViolatedConstraint(f'always_viol_{i}'))
        
        evaluator = BaseConstraintEvaluator(constraint_set)
        result = evaluator.evaluate(design_object)
        violations = evaluator.get_violations(design_object)
        
        assert not result.is_valid, "Always violated constraints should result in invalid evaluation"
        assert len(violations) == num_constraints, \
            f"Should have {num_constraints} violations, got {len(violations)}"
        
        # Each violation should correspond to one of our constraints
        violation_ids = {v.constraint_id for v in violations}
        expected_ids = {f'always_viol_{i}' for i in range(num_constraints)}
        assert violation_ids == expected_ids, "Violation IDs should match constraint IDs"
    
    @given(design_object_strategy(), constraint_set_strategy())
    @settings(max_examples=50, deadline=None)
    def test_constraint_type_filtering(self, design_object: DesignObject, constraint_set: ConstraintSet):
        """Constraint evaluation by type should only evaluate constraints of that type."""
        evaluator = BaseConstraintEvaluator(constraint_set)
        
        # Test each constraint type
        for constraint_type in ['structural', 'variable', 'global']:
            result = evaluator.evaluate_constraints_by_type(design_object, constraint_type)
            
            # Get expected constraints of this type
            expected_constraints = constraint_set.get_constraints_by_type(constraint_type)
            
            # Count violations that should occur
            expected_violations = 0
            for constraint in expected_constraints:
                if not evaluator.evaluate_constraint(constraint, design_object):
                    expected_violations += 1
            
            assert len(result.violations) == expected_violations, \
                f"Type {constraint_type}: expected {expected_violations} violations, got {len(result.violations)}"
            
            # All violations should be of the correct type
            for violation in result.violations:
                violated_constraint = constraint_set.get_constraint(violation.constraint_id)
                assert violated_constraint in expected_constraints, \
                    f"Violation {violation.constraint_id} not in expected constraints for type {constraint_type}"
    
    @given(design_object_strategy(), constraint_set_strategy())
    @settings(max_examples=50, deadline=None)
    def test_evaluation_summary_consistency(self, design_object: DesignObject, constraint_set: ConstraintSet):
        """Evaluation summary should be consistent with detailed results."""
        evaluator = BaseConstraintEvaluator(constraint_set)
        
        result = evaluator.evaluate(design_object)
        summary = evaluator.get_evaluation_summary(design_object)
        
        # Summary validity should match result validity
        assert summary['is_valid'] == result.is_valid, \
            "Summary validity should match result validity"
        
        # Total violations should match
        assert summary['total_violations'] == len(result.violations), \
            "Summary total violations should match result violations count"
        
        # Count violations by type and severity
        expected_by_type = {}
        expected_by_severity = {}
        
        for violation in result.violations:
            # By type
            if violation.constraint_type not in expected_by_type:
                expected_by_type[violation.constraint_type] = 0
            expected_by_type[violation.constraint_type] += 1
            
            # By severity
            if violation.severity not in expected_by_severity:
                expected_by_severity[violation.severity] = 0
            expected_by_severity[violation.severity] += 1
        
        assert summary['violations_by_type'] == expected_by_type, \
            "Summary violations by type should match actual counts"
        assert summary['violations_by_severity'] == expected_by_severity, \
            "Summary violations by severity should match actual counts"