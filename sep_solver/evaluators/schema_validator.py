"""JSON schema validator implementation."""

from typing import Dict, Any, List
import jsonschema
from jsonschema import Draft7Validator, ValidationError
from ..core.interfaces import SchemaValidator
from ..core.results import ValidationResult, SchemaError
from ..core.exceptions import SchemaValidationError


class JSONSchemaValidator(SchemaValidator):
    """JSON schema validator implementation using jsonschema library.
    
    Provides comprehensive JSON schema validation with detailed error reporting
    for validation failures. Uses Draft 7 JSON Schema specification.
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """Initialize with JSON schema definition.
        
        Args:
            schema: JSON schema dictionary following Draft 7 specification
            
        Raises:
            SchemaValidationError: If the provided schema is invalid
        """
        self.schema = schema
        
        # Validate the schema itself
        try:
            Draft7Validator.check_schema(schema)
            self._validator = Draft7Validator(schema)
        except jsonschema.SchemaError as e:
            raise SchemaValidationError([f"Invalid schema: {e.message}"])
    
    def validate(self, design_object: Dict[str, Any]) -> ValidationResult:
        """Validate design object against schema.
        
        Args:
            design_object: Design object as dictionary
            
        Returns:
            ValidationResult containing validation details
        """
        errors = self.get_schema_errors(design_object)
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def get_schema_errors(self, design_object: Dict[str, Any]) -> List[SchemaError]:
        """Return detailed schema validation errors.
        
        Args:
            design_object: Design object as dictionary
            
        Returns:
            List of SchemaError objects describing validation errors
        """
        errors = []
        
        # Collect all validation errors
        for error in self._validator.iter_errors(design_object):
            path = self._format_error_path(error.absolute_path)
            message = self._format_error_message(error)
            value = self._get_error_value(error, design_object)
            
            errors.append(SchemaError(
                path=path,
                message=message,
                value=value
            ))
        
        return errors
    
    def _format_error_path(self, path_deque) -> str:
        """Format the error path for human readability.
        
        Args:
            path_deque: Deque of path elements from jsonschema
            
        Returns:
            Formatted path string
        """
        if not path_deque:
            return "root"
        
        path_parts = []
        for part in path_deque:
            if isinstance(part, int):
                path_parts.append(f"[{part}]")
            else:
                if path_parts:
                    path_parts.append(f".{part}")
                else:
                    path_parts.append(str(part))
        
        return "".join(path_parts)
    
    def _format_error_message(self, error: ValidationError) -> str:
        """Format the error message for clarity.
        
        Args:
            error: ValidationError from jsonschema
            
        Returns:
            Formatted error message
        """
        # Enhance common error messages for better clarity
        message = error.message
        
        if error.validator == "required":
            missing_props = error.validator_value
            if isinstance(missing_props, list) and len(missing_props) == 1:
                message = f"Missing required property: '{missing_props[0]}'"
            else:
                message = f"Missing required properties: {missing_props}"
        
        elif error.validator == "type":
            expected_type = error.validator_value
            actual_value = error.instance
            actual_type = type(actual_value).__name__
            # Map Python type names to JSON schema type names for consistency
            type_mapping = {
                'str': 'string',
                'int': 'integer', 
                'float': 'number',
                'bool': 'boolean',
                'list': 'array',
                'dict': 'object',
                'NoneType': 'null'
            }
            json_type = type_mapping.get(actual_type, actual_type)
            message = f"Expected type '{expected_type}', got '{json_type}'"
        
        elif error.validator == "enum":
            allowed_values = error.validator_value
            message = f"Value must be one of: {allowed_values}"
        
        elif error.validator == "minLength":
            min_length = error.validator_value
            actual_length = len(error.instance) if error.instance else 0
            message = f"String too short (minimum length: {min_length}, actual: {actual_length})"
        
        elif error.validator == "maxLength":
            max_length = error.validator_value
            actual_length = len(error.instance) if error.instance else 0
            message = f"String too long (maximum length: {max_length}, actual: {actual_length})"
        
        elif error.validator == "minimum":
            min_value = error.validator_value
            message = f"Value must be >= {min_value}"
        
        elif error.validator == "maximum":
            max_value = error.validator_value
            message = f"Value must be <= {max_value}"
        
        elif error.validator == "pattern":
            pattern = error.validator_value
            message = f"String does not match required pattern: {pattern}"
        
        elif error.validator == "additionalProperties":
            if error.validator_value is False:
                # Extract property name from the error message if available
                # Message format: "Additional properties are not allowed ('property_name' was unexpected)"
                import re
                match = re.search(r"\('([^']+)' was unexpected\)", error.message)
                if match:
                    prop_name = match.group(1)
                    message = f"Additional property '{prop_name}' is not allowed"
                else:
                    message = "Additional properties are not allowed"
        
        return message
    
    def _get_error_value(self, error: ValidationError, design_object: Dict[str, Any]) -> Any:
        """Extract the problematic value from the design object.
        
        Args:
            error: ValidationError from jsonschema
            design_object: The original design object
            
        Returns:
            The value that caused the validation error, or None if not accessible
        """
        try:
            # Navigate to the error location in the design object
            current = design_object
            for path_element in error.absolute_path:
                if isinstance(current, dict):
                    current = current.get(path_element)
                elif isinstance(current, list) and isinstance(path_element, int):
                    if 0 <= path_element < len(current):
                        current = current[path_element]
                    else:
                        return None
                else:
                    return None
            return current
        except (KeyError, IndexError, TypeError):
            # If we can't navigate to the value, return the instance from the error
            return getattr(error, 'instance', None)