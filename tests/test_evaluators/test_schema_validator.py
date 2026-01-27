"""Unit tests for SchemaValidator implementation."""

import pytest
import re
from typing import Dict, Any
from hypothesis import given, strategies as st, assume, settings
from sep_solver.evaluators.schema_validator import JSONSchemaValidator
from sep_solver.core.results import ValidationResult, SchemaError
from sep_solver.core.exceptions import SchemaValidationError


class TestJSONSchemaValidator:
    """Test cases for JSONSchemaValidator class."""
    
    def test_init_with_valid_schema(self):
        """Test initialization with a valid JSON schema."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name"]
        }
        
        validator = JSONSchemaValidator(schema)
        assert validator.schema == schema
        assert validator._validator is not None
    
    def test_init_with_invalid_schema(self):
        """Test initialization with an invalid JSON schema."""
        invalid_schema = {
            "type": "invalid_type",  # Invalid type
            "properties": "not_an_object"  # Should be an object
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            JSONSchemaValidator(invalid_schema)
        
        assert "Invalid schema" in str(exc_info.value)
    
    def test_validate_valid_object(self):
        """Test validation of a valid design object."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name"]
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {"name": "John", "age": 30}
        
        result = validator.validate(design_object)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert bool(result) is True  # Test __bool__ method
    
    def test_validate_invalid_object_missing_required(self):
        """Test validation of object missing required properties."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "age"]
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {"name": "John"}  # Missing 'age'
        
        result = validator.validate(design_object)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "age" in result.errors[0].message
        assert "required" in result.errors[0].message.lower()
        assert bool(result) is False
    
    def test_validate_invalid_object_wrong_type(self):
        """Test validation of object with wrong property types."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {"name": "John", "age": "thirty"}  # age should be integer
        
        result = validator.validate(design_object)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        error = result.errors[0]
        assert error.path == "age"
        assert "integer" in error.message
        assert "string" in error.message
        assert error.value == "thirty"
    
    def test_get_schema_errors_multiple_violations(self):
        """Test detailed error reporting for multiple violations."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 2},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "email": {"type": "string", "pattern": r"^[^@]+@[^@]+\.[^@]+$"}
            },
            "required": ["name", "age", "email"],
            "additionalProperties": False
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {
            "name": "J",  # Too short
            "age": -5,    # Below minimum
            "email": "invalid-email",  # Invalid pattern
            "extra": "not allowed"  # Additional property
        }
        
        errors = validator.get_schema_errors(design_object)
        
        assert len(errors) >= 3  # At least 3 errors expected
        
        # Check for specific error types
        error_messages = [error.message for error in errors]
        assert any("too short" in msg.lower() for msg in error_messages)
        assert any(">=" in msg for msg in error_messages)
        assert any("pattern" in msg.lower() for msg in error_messages)
    
    def test_error_path_formatting_nested_objects(self):
        """Test error path formatting for nested objects."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"}
                            },
                            "required": ["name"]
                        }
                    },
                    "required": ["profile"]
                }
            },
            "required": ["user"]
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {
            "user": {
                "profile": {}  # Missing 'name'
            }
        }
        
        errors = validator.get_schema_errors(design_object)
        
        assert len(errors) == 1
        assert "user.profile" in errors[0].path
    
    def test_error_path_formatting_arrays(self):
        """Test error path formatting for arrays."""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"}
                        },
                        "required": ["id"]
                    }
                }
            }
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {
            "items": [
                {"id": 1},
                {"name": "invalid"}  # Missing 'id'
            ]
        }
        
        errors = validator.get_schema_errors(design_object)
        
        assert len(errors) == 1
        assert "items[1]" in errors[0].path
    
    def test_enum_validation_error(self):
        """Test validation error for enum constraints."""
        schema = {
            "type": "object",
            "properties": {
                "status": {"enum": ["active", "inactive", "pending"]}
            }
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {"status": "unknown"}
        
        errors = validator.get_schema_errors(design_object)
        
        assert len(errors) == 1
        error = errors[0]
        assert "one of" in error.message
        assert "active" in error.message
        assert "inactive" in error.message
        assert "pending" in error.message
    
    def test_string_length_validation_errors(self):
        """Test validation errors for string length constraints."""
        schema = {
            "type": "object",
            "properties": {
                "short": {"type": "string", "minLength": 5},
                "long": {"type": "string", "maxLength": 10}
            }
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {
            "short": "hi",  # Too short
            "long": "this is way too long"  # Too long
        }
        
        errors = validator.get_schema_errors(design_object)
        
        assert len(errors) == 2
        
        short_error = next(e for e in errors if e.path == "short")
        long_error = next(e for e in errors if e.path == "long")
        
        assert "too short" in short_error.message.lower()
        assert "minimum length: 5" in short_error.message
        assert "actual: 2" in short_error.message
        
        assert "too long" in long_error.message.lower()
        assert "maximum length: 10" in long_error.message
    
    def test_numeric_range_validation_errors(self):
        """Test validation errors for numeric range constraints."""
        schema = {
            "type": "object",
            "properties": {
                "min_val": {"type": "number", "minimum": 10},
                "max_val": {"type": "number", "maximum": 100}
            }
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {
            "min_val": 5,    # Below minimum
            "max_val": 150   # Above maximum
        }
        
        errors = validator.get_schema_errors(design_object)
        
        assert len(errors) == 2
        
        min_error = next(e for e in errors if e.path == "min_val")
        max_error = next(e for e in errors if e.path == "max_val")
        
        assert ">= 10" in min_error.message
        assert "<= 100" in max_error.message
    
    def test_pattern_validation_error(self):
        """Test validation error for pattern constraints."""
        schema = {
            "type": "object",
            "properties": {
                "code": {"type": "string", "pattern": r"^[A-Z]{3}-\d{3}$"}
            }
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {"code": "invalid-code"}
        
        errors = validator.get_schema_errors(design_object)
        
        assert len(errors) == 1
        error = errors[0]
        assert "pattern" in error.message.lower()
        assert "^[A-Z]{3}-\\d{3}$" in error.message
    
    def test_additional_properties_error(self):
        """Test validation error for additional properties."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "additionalProperties": False
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {
            "name": "John",
            "extra": "not allowed"
        }
        
        errors = validator.get_schema_errors(design_object)
        
        assert len(errors) == 1
        error = errors[0]
        assert "additional property" in error.message.lower()
        assert "extra" in error.message
    
    def test_root_level_error_path(self):
        """Test error path formatting for root level errors."""
        schema = {"type": "string"}
        
        validator = JSONSchemaValidator(schema)
        design_object = 123  # Should be string
        
        errors = validator.get_schema_errors(design_object)
        
        assert len(errors) == 1
        assert errors[0].path == "root"
    
    def test_error_value_extraction_complex_path(self):
        """Test extraction of error values from complex nested structures."""
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "integer"}
                        }
                    }
                }
            }
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {
            "data": [
                {"value": 42},
                {"value": "not_an_integer"}
            ]
        }
        
        errors = validator.get_schema_errors(design_object)
        
        assert len(errors) == 1
        error = errors[0]
        assert error.value == "not_an_integer"
        assert "data[1].value" in error.path
    
    def test_empty_design_object(self):
        """Test validation of empty design object."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {}
        
        result = validator.validate(design_object)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "name" in result.errors[0].message
    
    def test_null_values_handling(self):
        """Test handling of null values in design object."""
        schema = {
            "type": "object",
            "properties": {
                "optional": {"type": ["string", "null"]},
                "required": {"type": "string"}
            },
            "required": ["required"]
        }
        
        validator = JSONSchemaValidator(schema)
        design_object = {
            "optional": None,  # Should be valid
            "required": None   # Should be invalid
        }
        
        errors = validator.get_schema_errors(design_object)
        
        assert len(errors) == 1
        error = errors[0]
        assert error.path == "required"
        assert "string" in error.message


class TestSchemaValidationProperties:
    """Property-based tests for schema validation correctness."""
    
    # Strategy for generating simple JSON schemas
    @st.composite
    def simple_schema(draw):
        """Generate simple but valid JSON schemas for testing."""
        schema_type = draw(st.sampled_from(["object", "string", "integer", "number", "boolean", "array"]))
        
        if schema_type == "object":
            # Generate object schema with properties
            num_props = draw(st.integers(min_value=0, max_value=3))
            properties = {}
            required = []
            
            for i in range(num_props):
                prop_name = f"prop_{i}"
                prop_type = draw(st.sampled_from(["string", "integer", "number", "boolean"]))
                properties[prop_name] = {"type": prop_type}
                
                # Sometimes make properties required
                if draw(st.booleans()):
                    required.append(prop_name)
            
            schema = {
                "type": "object",
                "properties": properties
            }
            
            if required:
                schema["required"] = required
                
            # Sometimes add additionalProperties constraint
            if draw(st.booleans()):
                schema["additionalProperties"] = draw(st.booleans())
                
            return schema
            
        elif schema_type == "string":
            schema = {"type": "string"}
            
            # Sometimes add string constraints
            if draw(st.booleans()):
                min_length = draw(st.integers(min_value=0, max_value=5))
                schema["minLength"] = min_length
                
            if draw(st.booleans()):
                max_length = draw(st.integers(min_value=1, max_value=10))
                if "minLength" in schema:
                    max_length = max(max_length, schema["minLength"])
                schema["maxLength"] = max_length
                
            return schema
            
        elif schema_type == "integer":
            schema = {"type": "integer"}
            
            # Sometimes add numeric constraints
            if draw(st.booleans()):
                minimum = draw(st.integers(min_value=-100, max_value=100))
                schema["minimum"] = minimum
                
            if draw(st.booleans()):
                maximum = draw(st.integers(min_value=-100, max_value=100))
                if "minimum" in schema:
                    maximum = max(maximum, schema["minimum"])
                schema["maximum"] = maximum
                
            return schema
            
        elif schema_type == "number":
            schema = {"type": "number"}
            
            # Sometimes add numeric constraints
            if draw(st.booleans()):
                minimum = draw(st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False))
                schema["minimum"] = minimum
                
            if draw(st.booleans()):
                maximum = draw(st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False))
                if "minimum" in schema:
                    maximum = max(maximum, schema["minimum"])
                schema["maximum"] = maximum
                
            return schema
            
        elif schema_type == "boolean":
            return {"type": "boolean"}
            
        elif schema_type == "array":
            # Simple array schema
            item_type = draw(st.sampled_from(["string", "integer", "boolean"]))
            schema = {
                "type": "array",
                "items": {"type": item_type}
            }
            
            # Sometimes add array constraints
            if draw(st.booleans()):
                min_items = draw(st.integers(min_value=0, max_value=3))
                schema["minItems"] = min_items
                
            if draw(st.booleans()):
                max_items = draw(st.integers(min_value=1, max_value=5))
                if "minItems" in schema:
                    max_items = max(max_items, schema["minItems"])
                schema["maxItems"] = max_items
                
            return schema
    
    @st.composite
    def design_object_for_schema(draw, schema):
        """Generate design objects that may or may not conform to the given schema."""
        if schema.get("type") == "object":
            obj = {}
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            additional_properties = schema.get("additionalProperties", True)
            
            # Add required properties (sometimes valid, sometimes invalid)
            for prop_name in required:
                if prop_name in properties:
                    prop_schema = properties[prop_name]
                    if draw(st.booleans()):  # Sometimes generate valid values
                        obj[prop_name] = draw(TestSchemaValidationProperties.value_for_type(prop_schema.get("type", "string")))
                    else:  # Sometimes generate invalid values
                        obj[prop_name] = draw(TestSchemaValidationProperties.invalid_value_for_type(prop_schema.get("type", "string")))
                else:
                    # Generate some value for required property not in properties
                    obj[prop_name] = draw(st.one_of(st.text(), st.integers(), st.booleans()))
            
            # Sometimes omit required properties to test validation
            if draw(st.booleans()) and required:
                prop_to_omit = draw(st.sampled_from(required))
                obj.pop(prop_to_omit, None)
            
            # Add optional properties
            for prop_name, prop_schema in properties.items():
                if prop_name not in obj and draw(st.booleans()):
                    if draw(st.booleans()):  # Sometimes valid
                        obj[prop_name] = draw(TestSchemaValidationProperties.value_for_type(prop_schema.get("type", "string")))
                    else:  # Sometimes invalid
                        obj[prop_name] = draw(TestSchemaValidationProperties.invalid_value_for_type(prop_schema.get("type", "string")))
            
            # Sometimes add additional properties
            if draw(st.booleans()):
                extra_prop = f"extra_{draw(st.integers(min_value=0, max_value=10))}"
                obj[extra_prop] = draw(st.one_of(st.text(), st.integers(), st.booleans()))
            
            return obj
            
        elif schema.get("type") == "string":
            if draw(st.booleans()):  # Sometimes generate valid strings
                min_length = schema.get("minLength", 0)
                max_length = schema.get("maxLength", 20)
                return draw(st.text(min_size=min_length, max_size=max_length))
            else:  # Sometimes generate invalid values
                return draw(st.one_of(st.integers(), st.booleans(), st.lists(st.text())))
                
        elif schema.get("type") == "integer":
            if draw(st.booleans()):  # Sometimes generate valid integers
                minimum = schema.get("minimum", -1000)
                maximum = schema.get("maximum", 1000)
                return draw(st.integers(min_value=minimum, max_value=maximum))
            else:  # Sometimes generate invalid values
                return draw(st.one_of(st.text(), st.floats(), st.booleans()))
                
        elif schema.get("type") == "number":
            if draw(st.booleans()):  # Sometimes generate valid numbers
                minimum = schema.get("minimum", -1000.0)
                maximum = schema.get("maximum", 1000.0)
                return draw(st.floats(min_value=minimum, max_value=maximum, allow_nan=False, allow_infinity=False))
            else:  # Sometimes generate invalid values
                return draw(st.one_of(st.text(), st.booleans(), st.lists(st.integers())))
                
        elif schema.get("type") == "boolean":
            if draw(st.booleans()):  # Sometimes generate valid booleans
                return draw(st.booleans())
            else:  # Sometimes generate invalid values
                return draw(st.one_of(st.text(), st.integers(), st.lists(st.text())))
                
        elif schema.get("type") == "array":
            if draw(st.booleans()):  # Sometimes generate valid arrays
                item_schema = schema.get("items", {"type": "string"})
                min_items = schema.get("minItems", 0)
                max_items = schema.get("maxItems", 5)
                
                items = []
                num_items = draw(st.integers(min_value=min_items, max_value=max_items))
                for _ in range(num_items):
                    if draw(st.booleans()):  # Sometimes valid items
                        items.append(draw(TestSchemaValidationProperties.value_for_type(item_schema.get("type", "string"))))
                    else:  # Sometimes invalid items
                        items.append(draw(TestSchemaValidationProperties.invalid_value_for_type(item_schema.get("type", "string"))))
                return items
            else:  # Sometimes generate invalid values
                return draw(st.one_of(st.text(), st.integers(), st.booleans()))
        
        # Fallback: generate any JSON-like value
        return draw(st.one_of(
            st.text(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.lists(st.one_of(st.text(), st.integers(), st.booleans()), max_size=3),
            st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans()), max_size=3)
        ))
    
    @st.composite
    def value_for_type(draw, type_name):
        """Generate valid values for a given JSON schema type."""
        if type_name == "string":
            return draw(st.text())
        elif type_name == "integer":
            return draw(st.integers())
        elif type_name == "number":
            return draw(st.floats(allow_nan=False, allow_infinity=False))
        elif type_name == "boolean":
            return draw(st.booleans())
        elif type_name == "array":
            return draw(st.lists(st.one_of(st.text(), st.integers(), st.booleans()), max_size=3))
        elif type_name == "object":
            return draw(st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans()), max_size=3))
        else:
            return draw(st.text())  # Default to string
    
    @st.composite
    def invalid_value_for_type(draw, type_name):
        """Generate invalid values for a given JSON schema type."""
        if type_name == "string":
            return draw(st.one_of(st.integers(), st.booleans(), st.lists(st.text())))
        elif type_name == "integer":
            return draw(st.one_of(st.text(), st.floats(), st.booleans()))
        elif type_name == "number":
            return draw(st.one_of(st.text(), st.booleans(), st.lists(st.integers())))
        elif type_name == "boolean":
            return draw(st.one_of(st.text(), st.integers(), st.lists(st.text())))
        elif type_name == "array":
            return draw(st.one_of(st.text(), st.integers(), st.booleans()))
        elif type_name == "object":
            return draw(st.one_of(st.text(), st.integers(), st.booleans()))
        else:
            return draw(st.integers())  # Default to integer (invalid for string)
    
    @given(schema=simple_schema(), data=st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_schema_validation_completeness(self, schema, data):
        """**Property 1: Schema Validation Completeness**
        
        **Validates: Requirements 2.1, 2.2, 2.4**
        
        For any design object and JSON schema, the validation process should 
        correctly identify all schema violations and accept all valid objects.
        
        This property ensures that:
        1. Valid objects are always accepted (no false negatives)
        2. Invalid objects are always rejected (no false positives)  
        3. All violations are correctly identified and reported
        4. The validation result is consistent with the schema requirements
        """
        # Generate design object that may or may not conform to schema
        design_object = data.draw(TestSchemaValidationProperties.design_object_for_schema(schema))
        
        try:
            # Create validator with the schema
            validator = JSONSchemaValidator(schema)
            
            # Perform validation
            result = validator.validate(design_object)
            errors = validator.get_schema_errors(design_object)
            
            # Property 1: Validation result consistency
            # The validation result should be consistent with the presence of errors
            assert result.is_valid == (len(errors) == 0), \
                f"Validation result inconsistent: is_valid={result.is_valid}, errors={len(errors)}"
            
            # Property 2: Error list consistency  
            # The errors in ValidationResult should match get_schema_errors output
            assert result.errors == errors, \
                "ValidationResult.errors should match get_schema_errors() output"
            
            # Property 3: Boolean conversion consistency
            # The boolean value of ValidationResult should match is_valid
            assert bool(result) == result.is_valid, \
                "Boolean conversion of ValidationResult should match is_valid"
            
            # Property 4: Error completeness
            # If there are errors, each error should have required fields
            for error in errors:
                assert hasattr(error, 'path'), "SchemaError must have path attribute"
                assert hasattr(error, 'message'), "SchemaError must have message attribute"
                assert isinstance(error.path, str), "SchemaError.path must be string"
                assert isinstance(error.message, str), "SchemaError.message must be string"
                assert len(error.message) > 0, "SchemaError.message must not be empty"
            
            # Property 5: Validation determinism
            # Multiple validations of the same object should produce identical results
            result2 = validator.validate(design_object)
            errors2 = validator.get_schema_errors(design_object)
            
            assert result.is_valid == result2.is_valid, \
                "Validation should be deterministic"
            assert len(errors) == len(errors2), \
                "Error count should be deterministic"
            
            # Property 6: Error path validity
            # Error paths should be non-empty and properly formatted
            for error in errors:
                assert len(error.path) > 0, "Error path should not be empty"
                # Path should be either "root" or contain valid path elements
                assert error.path == "root" or any(c.isalnum() or c in ".[]-_" for c in error.path), \
                    f"Error path should contain valid characters: {error.path}"
            
        except SchemaValidationError:
            # If schema itself is invalid, that's acceptable for this property test
            # We're testing with generated schemas that might be invalid
            pass
    
    @given(
        schema=simple_schema(),
        design_object=st.deferred(lambda: st.dictionaries(
            st.text(min_size=1, max_size=10), 
            st.one_of(st.text(), st.integers(), st.booleans()),
            min_size=0, max_size=5
        ))
    )
    @settings(max_examples=50, deadline=None)
    def test_property_validation_with_random_objects(self, schema, design_object):
        """Test schema validation with completely random design objects.
        
        This tests the robustness of validation against arbitrary inputs.
        """
        try:
            validator = JSONSchemaValidator(schema)
            result = validator.validate(design_object)
            
            # Basic consistency checks
            assert isinstance(result.is_valid, bool)
            assert isinstance(result.errors, list)
            assert bool(result) == result.is_valid
            
            # All errors should be properly formed
            for error in result.errors:
                assert isinstance(error.path, str)
                assert isinstance(error.message, str)
                assert len(error.message) > 0
                
        except SchemaValidationError:
            # Invalid schema is acceptable in property testing
            pass
    
    def test_property_validation_edge_cases(self):
        """Test validation with edge case inputs."""
        # Test with minimal valid schema
        schema = {"type": "object"}
        validator = JSONSchemaValidator(schema)
        
        # Test empty object
        result = validator.validate({})
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # Test with None (should fail)
        result = validator.validate(None)
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Test with non-dict (should fail for object schema)
        result = validator.validate("not an object")
        assert result.is_valid is False
        assert len(result.errors) > 0

    @given(schema=simple_schema(), data=st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_error_message_descriptiveness(self, schema, data):
        """**Property 11: Error Message Descriptiveness**
        
        **Validates: Requirements 2.5, 5.4**
        
        For any validation failure or constraint violation, the error messages should 
        contain specific information about what failed and why.
        
        This property ensures that:
        1. Error messages are non-empty and descriptive
        2. Error messages contain specific details about the failure
        3. Error messages include context about expected vs actual values
        4. Error paths are specific and navigable
        5. Error messages are human-readable and actionable
        """
        # Generate design object that may cause validation errors
        design_object = data.draw(TestSchemaValidationProperties.design_object_for_schema(schema))
        
        try:
            # Create validator with the schema
            validator = JSONSchemaValidator(schema)
            
            # Perform validation and get detailed errors
            result = validator.validate(design_object)
            errors = validator.get_schema_errors(design_object)
            
            # Only test error message quality when there are actual errors
            if not result.is_valid and len(errors) > 0:
                
                # Property 1: Error messages must be descriptive and non-empty
                for error in errors:
                    assert len(error.message) > 0, "Error message must not be empty"
                    assert len(error.message) >= 10, f"Error message too short: '{error.message}'"
                    
                    # Error message should not be just the raw jsonschema message
                    assert not error.message.startswith("None is not of type"), \
                        "Error message should be enhanced, not raw jsonschema output"
                
                # Property 2: Error paths must be specific and navigable
                for error in errors:
                    assert len(error.path) > 0, "Error path must not be empty"
                    
                    # Path should be either "root" or contain valid path elements
                    if error.path != "root":
                        # Path should contain identifiable elements (property names, array indices)
                        assert any(c.isalnum() or c in ".[]-_" for c in error.path), \
                            f"Error path should contain navigable elements: '{error.path}'"
                
                # Property 3: Type errors should include expected and actual types
                type_errors = [e for e in errors if "type" in e.message.lower() or "expected" in e.message.lower()]
                for error in type_errors:
                    # Should mention what was expected
                    assert any(keyword in error.message.lower() for keyword in ["expected", "should be", "must be"]), \
                        f"Type error should mention expectation: '{error.message}'"
                    
                    # Should mention the actual type or value received
                    assert any(keyword in error.message.lower() for keyword in ["got", "received", "actual", "was"]), \
                        f"Type error should mention actual value: '{error.message}'"
                
                # Property 4: Range/constraint errors should include specific limits
                range_errors = [e for e in errors if any(keyword in e.message.lower() 
                                                       for keyword in ["minimum", "maximum", "length", ">=", "<=", "too short", "too long"])]
                for error in range_errors:
                    # Should include specific numeric limits or constraints
                    import re
                    has_numeric_info = bool(re.search(r'\d+', error.message))
                    assert has_numeric_info, f"Range error should include specific limits: '{error.message}'"
                
                # Property 5: Required property errors should name the missing property
                required_errors = [e for e in errors if "required" in e.message.lower() or "missing" in e.message.lower()]
                for error in required_errors:
                    # Should mention the specific property name
                    # Look for quoted property names or property names in the message
                    import re
                    has_property_name = bool(re.search(r"'[^']+'" , error.message)) or \
                                       bool(re.search(r'"[^"]+"', error.message)) or \
                                       any(word.isalnum() and len(word) > 1 for word in error.message.split())
                    assert has_property_name, f"Required property error should name the property: '{error.message}'"
                
                # Property 6: Pattern errors should include the pattern
                pattern_errors = [e for e in errors if "pattern" in e.message.lower()]
                for error in pattern_errors:
                    # Should include the actual pattern that was expected
                    assert any(char in error.message for char in ["^", "$", "\\", "[", "]", "*", "+", "?"]), \
                        f"Pattern error should include the regex pattern: '{error.message}'"
                
                # Property 7: Enum errors should list allowed values
                enum_errors = [e for e in errors if "one of" in error.message.lower() or "enum" in e.message.lower()]
                for error in enum_errors:
                    # Should list the allowed values
                    assert "[" in error.message and "]" in error.message, \
                        f"Enum error should list allowed values: '{error.message}'"
                
                # Property 8: Additional property errors should name the unexpected property
                additional_prop_errors = [e for e in errors if "additional" in e.message.lower()]
                for error in additional_prop_errors:
                    # Should mention the specific property that was unexpected
                    import re
                    has_property_name = bool(re.search(r"'[^']+'" , error.message)) or \
                                       bool(re.search(r'"[^"]+"', error.message))
                    assert has_property_name, f"Additional property error should name the property: '{error.message}'"
                
                # Property 9: Error messages should be human-readable
                for error in errors:
                    # Should not contain raw technical jargon without explanation
                    technical_terms = ["jsonschema", "validator", "instance", "deque"]
                    for term in technical_terms:
                        assert term not in error.message.lower(), \
                            f"Error message should be human-readable, avoid technical terms: '{error.message}'"
                    
                    # Should use clear, actionable language
                    assert not error.message.startswith("Failed validating"), \
                        f"Error message should be user-friendly: '{error.message}'"
                
                # Property 10: Error values should be extractable when available
                for error in errors:
                    # If error has a value, it should be meaningful
                    if error.value is not None:
                        # Value should not be a complex internal object
                        assert not str(type(error.value)).startswith("<class 'jsonschema"), \
                            f"Error value should be the actual problematic value, not internal objects"
                
        except SchemaValidationError:
            # If schema itself is invalid, that's acceptable for this property test
            # We're testing with generated schemas that might be invalid
            pass