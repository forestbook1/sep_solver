"""Property-based tests for DesignObject model."""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
import json

from sep_solver.models.design_object import DesignObject
from sep_solver.models.structure import Structure, Component, Relationship
from sep_solver.models.variable_assignment import VariableAssignment, Domain


# Strategy for generating valid component IDs
component_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'),
    min_size=1,
    max_size=20
).filter(lambda x: x and not x.startswith('-') and not x.endswith('-'))

# Strategy for generating component types
component_type_strategy = st.sampled_from([
    'processor', 'memory', 'storage', 'network', 'sensor', 'actuator', 'controller'
])

# Strategy for generating property values
property_value_strategy = st.one_of(
    st.integers(min_value=-1000, max_value=1000),
    st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    st.text(max_size=50),
    st.booleans()
)

# Strategy for generating component properties
component_properties_strategy = st.dictionaries(
    keys=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=1, max_size=10),
    values=property_value_strategy,
    max_size=5
)

@composite
def component_strategy(draw):
    """Generate a valid Component."""
    return Component(
        id=draw(component_id_strategy),
        type=draw(component_type_strategy),
        properties=draw(component_properties_strategy)
    )

@composite
def relationship_strategy(draw, component_ids):
    """Generate a valid Relationship given available component IDs."""
    assume(len(component_ids) >= 2)
    source_id = draw(st.sampled_from(component_ids))
    target_id = draw(st.sampled_from([cid for cid in component_ids if cid != source_id]))
    
    return Relationship(
        id=draw(component_id_strategy),
        source_id=source_id,
        target_id=target_id,
        type=draw(st.sampled_from(['connection', 'dependency', 'communication', 'control'])),
        properties=draw(component_properties_strategy)
    )

@composite
def structure_strategy(draw):
    """Generate a valid Structure."""
    # Generate components first (smaller max size)
    components = draw(st.lists(component_strategy(), min_size=0, max_size=3, unique_by=lambda c: c.id))
    
    structure = Structure()
    for component in components:
        structure.add_component(component)
    
    # Generate relationships if we have enough components (fewer relationships)
    if len(components) >= 2:
        component_ids = [c.id for c in components]
        relationships = draw(st.lists(
            relationship_strategy(component_ids), 
            min_size=0, 
            max_size=min(2, len(components) - 1),
            unique_by=lambda r: r.id
        ))
        
        for relationship in relationships:
            structure.add_relationship(relationship)
    
    return structure

# Strategy for generating domain types
domain_type_strategy = st.sampled_from(['int', 'float', 'string', 'bool', 'enum'])

@composite
def domain_strategy(draw):
    """Generate a valid Domain."""
    name = draw(component_id_strategy)
    domain_type = draw(domain_type_strategy)
    
    constraints = {}
    if domain_type == 'int':
        min_val = draw(st.integers(min_value=-100, max_value=50))
        max_val = draw(st.integers(min_value=min_val, max_value=100))
        constraints = {'min': min_val, 'max': max_val}
    elif domain_type == 'float':
        min_val = draw(st.floats(min_value=-100.0, max_value=50.0, allow_nan=False, allow_infinity=False))
        max_val = draw(st.floats(min_value=min_val, max_value=100.0, allow_nan=False, allow_infinity=False))
        constraints = {'min': min_val, 'max': max_val}
    elif domain_type == 'enum':
        values = draw(st.lists(st.text(max_size=10), min_size=1, max_size=5, unique=True))
        constraints = {'values': values}
    
    return Domain(name=name, type=domain_type, constraints=constraints)

@composite
def variable_assignment_strategy(draw):
    """Generate a valid VariableAssignment."""
    # Generate domains (smaller max size)
    domains = draw(st.lists(domain_strategy(), min_size=0, max_size=3, unique_by=lambda d: d.name))
    
    variables = VariableAssignment()
    
    # Add domains
    for domain in domains:
        variables.add_domain(domain)
    
    # Assign values to some variables
    for domain in domains:
        if draw(st.booleans()):  # Randomly decide whether to assign
            if domain.type == 'int':
                min_val = domain.constraints.get('min', 0)
                max_val = domain.constraints.get('max', 100)
                value = draw(st.integers(min_value=min_val, max_value=max_val))
            elif domain.type == 'float':
                min_val = domain.constraints.get('min', 0.0)
                max_val = domain.constraints.get('max', 1.0)
                value = draw(st.floats(min_value=min_val, max_value=max_val, allow_nan=False, allow_infinity=False))
            elif domain.type == 'string':
                value = draw(st.text(max_size=20))
            elif domain.type == 'bool':
                value = draw(st.booleans())
            elif domain.type == 'enum':
                values = domain.constraints.get('values', ['default'])
                value = draw(st.sampled_from(values))
            else:
                continue
            
            variables.set_variable(domain.name, value)
    
    return variables

# Strategy for generating metadata
metadata_strategy = st.dictionaries(
    keys=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=1, max_size=10),
    values=st.one_of(
        st.text(max_size=50),
        st.integers(min_value=-1000, max_value=1000),
        st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.lists(st.text(max_size=20), max_size=3)
    ),
    max_size=5
)

@composite
def design_object_strategy(draw):
    """Generate a valid DesignObject."""
    return DesignObject(
        id=draw(component_id_strategy),
        structure=draw(structure_strategy()),
        variables=draw(variable_assignment_strategy()),
        metadata=draw(metadata_strategy)
    )


class TestDesignObjectProperties:
    """Property-based tests for DesignObject."""
    
    @given(design_object_strategy())
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    def test_serialization_round_trip_property(self, design_object):
        """**Property 2: Serialization Round Trip**
        
        For any valid design object, serializing then deserializing should produce an equivalent object.
        **Validates: Requirements 2.3**
        """
        # Serialize to JSON
        json_data = design_object.to_json()
        
        # Verify JSON is serializable (no circular references, etc.)
        json_str = json.dumps(json_data)
        assert isinstance(json_str, str)
        
        # Deserialize back
        reconstructed = DesignObject.from_json(json_data)
        
        # Should be equivalent
        assert reconstructed == design_object
        assert reconstructed.id == design_object.id
        assert reconstructed.structure == design_object.structure
        assert reconstructed.variables == design_object.variables
        assert reconstructed.metadata == design_object.metadata
    
    @given(design_object_strategy())
    def test_json_string_round_trip_property(self, design_object):
        """Property: JSON string serialization round trip preserves equivalence.
        
        For any valid design object, converting to JSON string and back should preserve equivalence.
        """
        # Convert to JSON string
        json_str = design_object.to_json_string()
        
        # Should be valid JSON
        parsed_data = json.loads(json_str)
        assert isinstance(parsed_data, dict)
        
        # Convert back
        reconstructed = DesignObject.from_json_string(json_str)
        
        # Should be equivalent
        assert reconstructed == design_object
    
    @given(design_object_strategy())
    def test_copy_preserves_equivalence_property(self, design_object):
        """Property: Copying a design object preserves equivalence but creates new instances.
        
        For any valid design object, copying should create an equivalent but separate object.
        """
        copied = design_object.copy()
        
        # Should be equivalent
        assert copied == design_object
        
        # But should be different objects
        assert copied is not design_object
        assert copied.structure is not design_object.structure
        assert copied.variables is not design_object.variables
        assert copied.metadata is not design_object.metadata
    
    @given(design_object_strategy())
    def test_hash_consistency_property(self, design_object):
        """Property: Hash consistency for equivalent objects.
        
        For any design object, equivalent objects should have the same hash.
        """
        # Create equivalent object through serialization
        json_data = design_object.to_json()
        equivalent = DesignObject.from_json(json_data)
        
        # Should have same hash
        assert hash(design_object) == hash(equivalent)
        
        # Should be usable in sets
        design_set = {design_object, equivalent}
        assert len(design_set) == 1
    
    @given(design_object_strategy())
    def test_string_representation_contains_key_info_property(self, design_object):
        """Property: String representation contains key identifying information.
        
        For any design object, the string representation should contain the ID and basic counts.
        """
        str_repr = str(design_object)
        
        # Should contain the ID
        assert design_object.id in str_repr
        
        # Should contain "DesignObject"
        assert "DesignObject" in str_repr
        
        # Should contain component and variable counts
        assert f"components={len(design_object.structure.components)}" in str_repr
        assert f"variables={len(design_object.variables.assignments)}" in str_repr
    
    @given(design_object_strategy(), st.integers(min_value=0, max_value=4))
    def test_json_indentation_preserves_data_property(self, design_object, indent):
        """Property: JSON indentation preserves data content.
        
        For any design object and indentation level, the data content should be preserved.
        """
        # Generate JSON with different indentation
        json_str_indented = design_object.to_json_string(indent=indent)
        json_str_compact = design_object.to_json_string(indent=None)
        
        # Parse both
        data_indented = json.loads(json_str_indented)
        data_compact = json.loads(json_str_compact)
        
        # Should have same data
        assert data_indented == data_compact
        
        # Both should reconstruct to equivalent objects
        obj_from_indented = DesignObject.from_json_string(json_str_indented)
        obj_from_compact = DesignObject.from_json_string(json_str_compact)
        
        assert obj_from_indented == design_object
        assert obj_from_compact == design_object
        assert obj_from_indented == obj_from_compact


class TestDesignObjectErrorProperties:
    """Property-based tests for DesignObject error handling."""
    
    @given(st.text().filter(lambda x: x.strip() != '' and not x.startswith('{') and x not in ['0', '1', 'true', 'false', 'null']))
    def test_invalid_json_string_raises_error_property(self, invalid_json):
        """Property: Invalid JSON strings should raise ValueError.
        
        For any string that is not valid JSON, from_json_string should raise ValueError.
        """
        with pytest.raises(ValueError):
            DesignObject.from_json_string(invalid_json)
    
    @given(st.dictionaries(
        keys=st.text(max_size=10), 
        values=st.one_of(st.text(max_size=10), st.integers(), st.booleans()),
        max_size=3
    ).filter(lambda d: 'id' not in d or 'structure' not in d or 'variables' not in d))
    def test_incomplete_json_data_raises_error_property(self, incomplete_data):
        """Property: Incomplete JSON data should raise ValueError.
        
        For any dictionary missing required fields, from_json should raise ValueError.
        """
        with pytest.raises(ValueError, match="Missing required field"):
            DesignObject.from_json(incomplete_data)