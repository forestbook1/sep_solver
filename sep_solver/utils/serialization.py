"""Serialization utilities for the SEP solver."""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, TypeVar
from pathlib import Path

T = TypeVar('T', bound='JSONSerializable')


class JSONSerializable(ABC):
    """Abstract base class for objects that can be serialized to/from JSON."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary representation.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create object from dictionary representation.
        
        Args:
            data: Dictionary containing object data
            
        Returns:
            Object instance
        """
        pass
    
    def to_json(self, indent: int = None) -> str:
        """Convert object to JSON string.
        
        Args:
            indent: Optional indentation for pretty printing
            
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Create object from JSON string.
        
        Args:
            json_str: JSON string representation
            
        Returns:
            Object instance
            
        Raises:
            ValueError: If JSON is invalid
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    def save_to_file(self, file_path: str, indent: int = 2) -> None:
        """Save object to JSON file.
        
        Args:
            file_path: Path to save file
            indent: Indentation for pretty printing
            
        Raises:
            IOError: If file cannot be written
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=indent, default=str)
    
    @classmethod
    def load_from_file(cls: Type[T], file_path: str) -> T:
        """Load object from JSON file.
        
        Args:
            file_path: Path to load file
            
        Returns:
            Object instance
            
        Raises:
            IOError: If file cannot be read
            ValueError: If file contains invalid JSON
        """
        path = Path(file_path)
        if not path.exists():
            raise IOError(f"File not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)


def serialize_object(obj: Any) -> Dict[str, Any]:
    """Serialize an object to dictionary format.
    
    Args:
        obj: Object to serialize
        
    Returns:
        Dictionary representation
        
    Raises:
        ValueError: If object cannot be serialized
    """
    if isinstance(obj, JSONSerializable):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        # Try to serialize using object attributes
        result = {}
        for key, value in obj.__dict__.items():
            if not key.startswith('_'):  # Skip private attributes
                try:
                    result[key] = serialize_object(value)
                except ValueError:
                    # Skip attributes that can't be serialized
                    pass
        return result
    elif isinstance(obj, (list, tuple)):
        return [serialize_object(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: serialize_object(value) for key, value in obj.items()}
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    else:
        # Try to convert to string as fallback
        return str(obj)


def deserialize_object(data: Dict[str, Any], target_class: Type[T]) -> T:
    """Deserialize dictionary data to an object.
    
    Args:
        data: Dictionary data
        target_class: Target class to deserialize to
        
    Returns:
        Deserialized object
        
    Raises:
        ValueError: If deserialization fails
    """
    if issubclass(target_class, JSONSerializable):
        return target_class.from_dict(data)
    else:
        raise ValueError(f"Class {target_class} does not support deserialization")


def save_json(data: Any, file_path: str, indent: int = 2) -> None:
    """Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save file
        indent: Indentation for pretty printing
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=indent, default=str)


def load_json(file_path: str) -> Any:
    """Load data from JSON file.
    
    Args:
        file_path: Path to load file
        
    Returns:
        Loaded data
        
    Raises:
        IOError: If file cannot be read
        ValueError: If file contains invalid JSON
    """
    path = Path(file_path)
    if not path.exists():
        raise IOError(f"File not found: {file_path}")
    
    with open(path, 'r') as f:
        return json.load(f)