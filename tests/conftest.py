"""Pytest configuration and fixtures for SEP solver tests."""

import pytest
from typing import Dict, Any
from sep_solver.core.config import SolverConfig
from sep_solver.models.constraint_set import ConstraintSet
from sep_solver.models.structure import Structure, Component, Relationship
from sep_solver.models.variable_assignment import VariableAssignment, Domain
from sep_solver.models.design_object import DesignObject


@pytest.fixture
def sample_schema() -> Dict[str, Any]:
    """Sample JSON schema for testing."""
    return {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "structure": {
                "type": "object",
                "properties": {
                    "components": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "properties": {"type": "object"}
                            },
                            "required": ["id", "type"]
                        }
                    },
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "source_id": {"type": "string"},
                                "target_id": {"type": "string"},
                                "type": {"type": "string"},
                                "properties": {"type": "object"}
                            },
                            "required": ["id", "source_id", "target_id", "type"]
                        }
                    }
                },
                "required": ["components", "relationships"]
            },
            "variables": {
                "type": "object",
                "properties": {
                    "assignments": {"type": "object"},
                    "domains": {"type": "object"},
                    "dependencies": {"type": "object"}
                },
                "required": ["assignments", "domains", "dependencies"]
            },
            "metadata": {"type": "object"}
        },
        "required": ["id", "structure", "variables", "metadata"]
    }


@pytest.fixture
def default_config() -> SolverConfig:
    """Default solver configuration for testing."""
    return SolverConfig(
        exploration_strategy="breadth_first",
        max_iterations=100,
        max_solutions=5,
        enable_logging=False,  # Disable logging in tests
        log_level="ERROR"
    )


@pytest.fixture
def empty_constraint_set() -> ConstraintSet:
    """Empty constraint set for testing."""
    return ConstraintSet()


@pytest.fixture
def sample_component() -> Component:
    """Sample component for testing."""
    return Component(
        id="comp1",
        type="processor",
        properties={"speed": 100, "cores": 4}
    )


@pytest.fixture
def sample_relationship(sample_component) -> Relationship:
    """Sample relationship for testing."""
    return Relationship(
        id="rel1",
        source_id="comp1",
        target_id="comp2",
        type="connection",
        properties={"bandwidth": 1000}
    )


@pytest.fixture
def sample_structure(sample_component) -> Structure:
    """Sample structure for testing."""
    comp2 = Component(id="comp2", type="memory", properties={"size": 8192})
    rel = Relationship(
        id="rel1",
        source_id="comp1",
        target_id="comp2",
        type="connection"
    )
    
    structure = Structure()
    structure.add_component(sample_component)
    structure.add_component(comp2)
    structure.add_relationship(rel)
    
    return structure


@pytest.fixture
def sample_domain() -> Domain:
    """Sample domain for testing."""
    return Domain(
        name="speed",
        type="int",
        constraints={"min": 1, "max": 1000}
    )


@pytest.fixture
def sample_variable_assignment(sample_domain) -> VariableAssignment:
    """Sample variable assignment for testing."""
    assignment = VariableAssignment()
    assignment.add_domain(sample_domain)
    assignment.set_variable("speed", 100)
    return assignment


@pytest.fixture
def sample_design_object(sample_structure, sample_variable_assignment) -> DesignObject:
    """Sample design object for testing."""
    return DesignObject(
        id="design1",
        structure=sample_structure,
        variables=sample_variable_assignment,
        metadata={"created_by": "test", "version": "1.0"}
    )


# Hypothesis strategies for property-based testing
from hypothesis import strategies as st

@pytest.fixture
def component_strategy():
    """Hypothesis strategy for generating components."""
    return st.builds(
        Component,
        id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        type=st.sampled_from(["processor", "memory", "storage", "network", "sensor"]),
        properties=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.one_of(st.integers(), st.floats(), st.text(), st.booleans())
        )
    )


@pytest.fixture
def domain_strategy():
    """Hypothesis strategy for generating domains."""
    return st.builds(
        Domain,
        name=st.text(min_size=1, max_size=20),
        type=st.sampled_from(["int", "float", "string", "bool", "enum"]),
        constraints=st.dictionaries(
            keys=st.sampled_from(["min", "max", "values", "default"]),
            values=st.one_of(st.integers(), st.floats(), st.text(), st.lists(st.text()))
        )
    )


# Test utilities
def assert_valid_json_serialization(obj):
    """Assert that an object can be serialized to JSON and back."""
    if hasattr(obj, 'to_json') and hasattr(obj, 'from_json'):
        json_str = obj.to_json()
        assert isinstance(json_str, str)
        
        # Should be able to deserialize back
        restored = obj.__class__.from_json(json_str)
        assert restored == obj
    elif hasattr(obj, 'to_dict') and hasattr(obj, 'from_dict'):
        dict_repr = obj.to_dict()
        assert isinstance(dict_repr, dict)
        
        # Should be able to deserialize back
        restored = obj.__class__.from_dict(dict_repr)
        assert restored == obj