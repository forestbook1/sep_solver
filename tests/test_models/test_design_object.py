"""Tests for DesignObject model."""

import pytest
import json
from unittest.mock import Mock, MagicMock

from sep_solver.models.design_object import DesignObject
from sep_solver.models.structure import Structure, Component, Relationship
from sep_solver.models.variable_assignment import VariableAssignment, Domain
from sep_solver.core.results import ValidationResult, SchemaError


class TestDesignObject:
    """Test cases for DesignObject class."""
    
    def test_design_object_creation(self):
        """Test creating a design object."""
        # Create test structure
        structure = Structure()
        component = Component(id="comp1", type="processor", properties={"speed": 100})
        structure.add_component(component)
        
        # Create test variable assignment
        variables = VariableAssignment()
        domain = Domain(name="speed", type="int", constraints={"min": 50, "max": 200})
        variables.add_domain(domain)
        variables.set_variable("speed", 100)
        
        # Create design object
        design_object = DesignObject(
            id="design1",
            structure=structure,
            variables=variables,
            metadata={"version": "1.0", "author": "test"}
        )
        
        assert design_object.id == "design1"
        assert design_object.structure == structure
        assert design_object.variables == variables
        assert design_object.metadata["version"] == "1.0"
        assert design_object.metadata["author"] == "test"
    
    def test_to_json(self):
        """Test serializing design object to JSON."""
        # Create minimal test objects
        structure = Structure()
        component = Component(id="comp1", type="processor")
        structure.add_component(component)
        
        variables = VariableAssignment()
        variables.set_variable("param1", "value1")
        
        design_object = DesignObject(
            id="design1",
            structure=structure,
            variables=variables,
            metadata={"test": True}
        )
        
        json_data = design_object.to_json()
        
        assert json_data["id"] == "design1"
        assert "structure" in json_data
        assert "variables" in json_data
        assert "metadata" in json_data
        assert json_data["metadata"]["test"] is True
        
        # Verify structure serialization
        assert "components" in json_data["structure"]
        assert len(json_data["structure"]["components"]) == 1
        assert json_data["structure"]["components"][0]["id"] == "comp1"
        
        # Verify variables serialization
        assert "assignments" in json_data["variables"]
        assert json_data["variables"]["assignments"]["param1"] == "value1"
    
    def test_from_json(self):
        """Test deserializing design object from JSON."""
        json_data = {
            "id": "design1",
            "structure": {
                "components": [
                    {"id": "comp1", "type": "processor", "properties": {"speed": 100}}
                ],
                "relationships": [],
                "structural_constraints": 0
            },
            "variables": {
                "assignments": {"param1": "value1"},
                "domains": {
                    "param1": {
                        "name": "param1",
                        "type": "string",
                        "constraints": {}
                    }
                },
                "dependencies": {}
            },
            "metadata": {"version": "1.0"}
        }
        
        design_object = DesignObject.from_json(json_data)
        
        assert design_object.id == "design1"
        assert len(design_object.structure.components) == 1
        assert design_object.structure.components[0].id == "comp1"
        assert design_object.structure.components[0].properties["speed"] == 100
        assert design_object.variables.get_variable("param1") == "value1"
        assert design_object.metadata["version"] == "1.0"
    
    def test_from_json_missing_required_field(self):
        """Test deserializing with missing required field."""
        json_data = {
            "id": "design1",
            "structure": {"components": [], "relationships": []},
            # Missing "variables" field
            "metadata": {}
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            DesignObject.from_json(json_data)
    
    def test_from_json_invalid_data(self):
        """Test deserializing with invalid data."""
        json_data = {
            "id": "design1",
            "structure": "invalid_structure",  # Should be dict
            "variables": {"assignments": {}},
            "metadata": {}
        }
        
        with pytest.raises(ValueError, match="Invalid design object data"):
            DesignObject.from_json(json_data)
    
    def test_validate_schema(self):
        """Test schema validation."""
        # Create test design object
        structure = Structure()
        variables = VariableAssignment()
        design_object = DesignObject(
            id="design1",
            structure=structure,
            variables=variables,
            metadata={}
        )
        
        # Mock schema validator
        mock_validator = Mock()
        mock_result = ValidationResult(is_valid=True, errors=[])
        mock_validator.validate.return_value = mock_result
        
        result = design_object.validate_schema(mock_validator)
        
        assert result.is_valid is True
        mock_validator.validate.assert_called_once()
        
        # Verify the validator was called with the JSON representation
        call_args = mock_validator.validate.call_args[0][0]
        assert call_args["id"] == "design1"
    
    def test_validate_schema_with_errors(self):
        """Test schema validation with errors."""
        structure = Structure()
        variables = VariableAssignment()
        design_object = DesignObject(
            id="design1",
            structure=structure,
            variables=variables,
            metadata={}
        )
        
        # Mock schema validator with errors
        mock_validator = Mock()
        schema_error = SchemaError(path="id", message="Invalid ID format", value="design1")
        mock_result = ValidationResult(is_valid=False, errors=[schema_error])
        mock_validator.validate.return_value = mock_result
        
        result = design_object.validate_schema(mock_validator)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].path == "id"
        assert result.errors[0].message == "Invalid ID format"
    
    def test_to_json_string(self):
        """Test converting to JSON string."""
        structure = Structure()
        variables = VariableAssignment()
        design_object = DesignObject(
            id="design1",
            structure=structure,
            variables=variables,
            metadata={"test": True}
        )
        
        json_str = design_object.to_json_string()
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["id"] == "design1"
        assert parsed["metadata"]["test"] is True
    
    def test_to_json_string_with_indent(self):
        """Test converting to JSON string with indentation."""
        structure = Structure()
        variables = VariableAssignment()
        design_object = DesignObject(
            id="design1",
            structure=structure,
            variables=variables,
            metadata={}
        )
        
        json_str = design_object.to_json_string(indent=2)
        
        # Should contain newlines and spaces for indentation
        assert "\n" in json_str
        assert "  " in json_str
        
        # Should still be valid JSON
        parsed = json.loads(json_str)
        assert parsed["id"] == "design1"
    
    def test_from_json_string(self):
        """Test creating from JSON string."""
        json_str = '''
        {
            "id": "design1",
            "structure": {
                "components": [],
                "relationships": [],
                "structural_constraints": 0
            },
            "variables": {
                "assignments": {},
                "domains": {},
                "dependencies": {}
            },
            "metadata": {"version": "1.0"}
        }
        '''
        
        design_object = DesignObject.from_json_string(json_str)
        
        assert design_object.id == "design1"
        assert design_object.metadata["version"] == "1.0"
    
    def test_from_json_string_invalid_json(self):
        """Test creating from invalid JSON string."""
        invalid_json = '{"id": "design1", "invalid": }'
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            DesignObject.from_json_string(invalid_json)
    
    def test_copy(self):
        """Test creating a copy of design object."""
        # Create original with some data
        structure = Structure()
        component = Component(id="comp1", type="processor")
        structure.add_component(component)
        
        variables = VariableAssignment()
        variables.set_variable("param1", "value1")
        
        original = DesignObject(
            id="design1",
            structure=structure,
            variables=variables,
            metadata={"version": "1.0"}
        )
        
        # Create copy
        copy_obj = original.copy()
        
        # Should be equal but not the same object
        assert copy_obj == original
        assert copy_obj is not original
        assert copy_obj.structure is not original.structure
        assert copy_obj.variables is not original.variables
        assert copy_obj.metadata is not original.metadata
        
        # Modifying copy should not affect original
        copy_obj.metadata["version"] = "2.0"
        assert original.metadata["version"] == "1.0"
    
    def test_equality(self):
        """Test design object equality."""
        structure1 = Structure()
        component1 = Component(id="comp1", type="processor")
        structure1.add_component(component1)
        
        structure2 = Structure()
        component2 = Component(id="comp1", type="processor")
        structure2.add_component(component2)
        
        variables1 = VariableAssignment()
        variables1.set_variable("param1", "value1")
        
        variables2 = VariableAssignment()
        variables2.set_variable("param1", "value1")
        
        design1 = DesignObject(
            id="design1",
            structure=structure1,
            variables=variables1,
            metadata={"version": "1.0"}
        )
        
        design2 = DesignObject(
            id="design1",
            structure=structure2,
            variables=variables2,
            metadata={"version": "1.0"}
        )
        
        design3 = DesignObject(
            id="design2",  # Different ID
            structure=structure2,
            variables=variables2,
            metadata={"version": "1.0"}
        )
        
        assert design1 == design2
        assert design1 != design3
        assert design1 != "not_a_design_object"
    
    def test_hash(self):
        """Test design object hashing."""
        structure = Structure()
        variables = VariableAssignment()
        
        design1 = DesignObject(
            id="design1",
            structure=structure,
            variables=variables,
            metadata={}
        )
        
        design2 = DesignObject(
            id="design1",
            structure=structure,
            variables=variables,
            metadata={}
        )
        
        # Equal objects should have same hash
        assert hash(design1) == hash(design2)
        
        # Should be usable in sets
        design_set = {design1, design2}
        assert len(design_set) == 1
    
    def test_str_representation(self):
        """Test string representation."""
        structure = Structure()
        component1 = Component(id="comp1", type="processor")
        component2 = Component(id="comp2", type="memory")
        structure.add_component(component1)
        structure.add_component(component2)
        
        variables = VariableAssignment()
        variables.set_variable("param1", "value1")
        variables.set_variable("param2", "value2")
        
        design_object = DesignObject(
            id="design1",
            structure=structure,
            variables=variables,
            metadata={}
        )
        
        str_repr = str(design_object)
        
        assert "DesignObject" in str_repr
        assert "design1" in str_repr
        assert "components=2" in str_repr
        assert "variables=2" in str_repr
    
    def test_repr_representation(self):
        """Test detailed string representation."""
        structure = Structure()
        variables = VariableAssignment()
        
        design_object = DesignObject(
            id="design1",
            structure=structure,
            variables=variables,
            metadata={"test": True}
        )
        
        repr_str = repr(design_object)
        
        assert "DesignObject" in repr_str
        assert "id='design1'" in repr_str
        assert "structure=" in repr_str
        assert "variables=" in repr_str
        assert "metadata=" in repr_str


class TestDesignObjectIntegration:
    """Integration tests for DesignObject with real components."""
    
    def test_round_trip_serialization(self):
        """Test complete round-trip serialization."""
        # Create a complex design object
        structure = Structure()
        
        # Add components
        comp1 = Component(id="processor1", type="cpu", properties={"cores": 4, "speed": 3.2})
        comp2 = Component(id="memory1", type="ram", properties={"size": 16, "type": "DDR4"})
        structure.add_component(comp1)
        structure.add_component(comp2)
        
        # Add relationship
        relationship = Relationship(
            id="conn1",
            source_id="processor1",
            target_id="memory1",
            type="memory_bus",
            properties={"bandwidth": 25600}
        )
        structure.add_relationship(relationship)
        
        # Create variable assignment with domains
        variables = VariableAssignment()
        
        # Add domains
        cpu_freq_domain = Domain(name="cpu_frequency", type="float", constraints={"min": 2.0, "max": 4.0})
        ram_size_domain = Domain(name="ram_size", type="int", constraints={"min": 8, "max": 64})
        variables.add_domain(cpu_freq_domain)
        variables.add_domain(ram_size_domain)
        
        # Set variables
        variables.set_variable("cpu_frequency", 3.2)
        variables.set_variable("ram_size", 16)
        
        # Add dependencies
        variables.add_dependency("ram_size", ["cpu_frequency"])
        
        # Create design object
        original = DesignObject(
            id="complex_design",
            structure=structure,
            variables=variables,
            metadata={
                "version": "2.1",
                "created_by": "test_suite",
                "tags": ["performance", "gaming"],
                "config": {"optimization": True, "debug": False}
            }
        )
        
        # Serialize to JSON and back
        json_data = original.to_json()
        reconstructed = DesignObject.from_json(json_data)
        
        # Verify everything is preserved
        assert reconstructed == original
        assert reconstructed.id == "complex_design"
        
        # Verify structure details
        assert len(reconstructed.structure.components) == 2
        assert len(reconstructed.structure.relationships) == 1
        
        proc_comp = reconstructed.structure.get_component("processor1")
        assert proc_comp is not None
        assert proc_comp.properties["cores"] == 4
        assert proc_comp.properties["speed"] == 3.2
        
        mem_comp = reconstructed.structure.get_component("memory1")
        assert mem_comp is not None
        assert mem_comp.properties["size"] == 16
        
        # Verify variables
        assert reconstructed.variables.get_variable("cpu_frequency") == 3.2
        assert reconstructed.variables.get_variable("ram_size") == 16
        assert "cpu_frequency" in reconstructed.variables.domains
        assert "ram_size" in reconstructed.variables.domains
        assert reconstructed.variables.dependencies["ram_size"] == ["cpu_frequency"]
        
        # Verify metadata
        assert reconstructed.metadata["version"] == "2.1"
        assert reconstructed.metadata["created_by"] == "test_suite"
        assert reconstructed.metadata["tags"] == ["performance", "gaming"]
        assert reconstructed.metadata["config"]["optimization"] is True
    
    def test_json_string_round_trip(self):
        """Test round-trip through JSON string."""
        # Create simple design object
        structure = Structure()
        component = Component(id="test_comp", type="test_type")
        structure.add_component(component)
        
        variables = VariableAssignment()
        variables.set_variable("test_var", 42)
        
        original = DesignObject(
            id="test_design",
            structure=structure,
            variables=variables,
            metadata={"test": True}
        )
        
        # Convert to JSON string and back
        json_str = original.to_json_string(indent=2)
        reconstructed = DesignObject.from_json_string(json_str)
        
        assert reconstructed == original
        assert reconstructed.variables.get_variable("test_var") == 42
        assert reconstructed.metadata["test"] is True
    
    def test_schema_validation_integration(self):
        """Test integration with actual schema validator."""
        from sep_solver.evaluators.schema_validator import JSONSchemaValidator
        
        # Define a simple schema
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "structure": {
                    "type": "object",
                    "properties": {
                        "components": {"type": "array"},
                        "relationships": {"type": "array"}
                    },
                    "required": ["components", "relationships"]
                },
                "variables": {
                    "type": "object",
                    "properties": {
                        "assignments": {"type": "object"}
                    },
                    "required": ["assignments"]
                },
                "metadata": {"type": "object"}
            },
            "required": ["id", "structure", "variables", "metadata"]
        }
        
        validator = JSONSchemaValidator(schema)
        
        # Create valid design object
        structure = Structure()
        variables = VariableAssignment()
        design_object = DesignObject(
            id="valid_design",
            structure=structure,
            variables=variables,
            metadata={}
        )
        
        # Should validate successfully
        result = design_object.validate_schema(validator)
        assert result.is_valid is True
        assert len(result.errors) == 0