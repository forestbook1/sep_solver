"""Custom constraint types for the SEP solver.

This module provides examples of custom constraint implementations
that can be used with the constraint evaluator's extensible system.
"""

from typing import Any, Dict, List, Set, TYPE_CHECKING
from ..models.constraint_set import Constraint, StructuralConstraint, VariableConstraint, GlobalConstraint

if TYPE_CHECKING:
    from ..models.design_object import DesignObject


class ComponentPropertyConstraint(StructuralConstraint):
    """Constraint that checks component properties."""
    
    def __init__(self, constraint_id: str, component_type: str, property_name: str, 
                 expected_value: Any = None, min_value: Any = None, max_value: Any = None):
        super().__init__(constraint_id, f"Component {component_type} property {property_name} constraint")
        self.component_type = component_type
        self.property_name = property_name
        self.expected_value = expected_value
        self.min_value = min_value
        self.max_value = max_value
    
    def is_satisfied(self, design_object: 'DesignObject') -> bool:
        """Check if components of the specified type have the required property values."""
        matching_components = [c for c in design_object.structure.components if c.type == self.component_type]
        
        if not matching_components:
            return True  # No components of this type, constraint is vacuously satisfied
        
        for component in matching_components:
            if self.property_name not in component.properties:
                return False
            
            value = component.properties[self.property_name]
            
            if self.expected_value is not None and value != self.expected_value:
                return False
            
            if self.min_value is not None and value < self.min_value:
                return False
            
            if self.max_value is not None and value > self.max_value:
                return False
        
        return True
    
    def get_violation_message(self, design_object: 'DesignObject') -> str:
        """Get violation message."""
        matching_components = [c for c in design_object.structure.components if c.type == self.component_type]
        
        for component in matching_components:
            if self.property_name not in component.properties:
                return f"Component {component.id} of type {self.component_type} missing property {self.property_name}"
            
            value = component.properties[self.property_name]
            
            if self.expected_value is not None and value != self.expected_value:
                return f"Component {component.id} property {self.property_name} is {value}, expected {self.expected_value}"
            
            if self.min_value is not None and value < self.min_value:
                return f"Component {component.id} property {self.property_name} is {value}, minimum {self.min_value}"
            
            if self.max_value is not None and value > self.max_value:
                return f"Component {component.id} property {self.property_name} is {value}, maximum {self.max_value}"
        
        return f"Component property constraint violated"


class RelationshipPatternConstraint(StructuralConstraint):
    """Constraint that checks for specific relationship patterns."""
    
    def __init__(self, constraint_id: str, source_type: str, target_type: str, 
                 relationship_type: str, required: bool = True):
        super().__init__(constraint_id, f"Relationship pattern {source_type} -> {target_type} via {relationship_type}")
        self.source_type = source_type
        self.target_type = target_type
        self.relationship_type = relationship_type
        self.required = required
    
    def is_satisfied(self, design_object: 'DesignObject') -> bool:
        """Check if the required relationship pattern exists."""
        # Find components of the required types
        source_components = [c for c in design_object.structure.components if c.type == self.source_type]
        target_components = [c for c in design_object.structure.components if c.type == self.target_type]
        
        if not source_components or not target_components:
            return not self.required  # If components don't exist, pattern can't exist
        
        # Check if the relationship pattern exists
        pattern_exists = False
        for relationship in design_object.structure.relationships:
            if relationship.type == self.relationship_type:
                source_component = next((c for c in source_components if c.id == relationship.source_id), None)
                target_component = next((c for c in target_components if c.id == relationship.target_id), None)
                
                if source_component and target_component:
                    pattern_exists = True
                    break
        
        return pattern_exists if self.required else not pattern_exists
    
    def get_violation_message(self, design_object: 'DesignObject') -> str:
        """Get violation message."""
        if self.required:
            return f"Required relationship pattern not found: {self.source_type} -> {self.target_type} via {self.relationship_type}"
        else:
            return f"Forbidden relationship pattern found: {self.source_type} -> {self.target_type} via {self.relationship_type}"


class VariableDependencyConstraint(VariableConstraint):
    """Constraint that enforces complex variable dependencies."""
    
    def __init__(self, constraint_id: str, dependent_var: str, dependency_rules: Dict[str, Any]):
        super().__init__(constraint_id, f"Variable dependency constraint for {dependent_var}")
        self.dependent_var = dependent_var
        self.dependency_rules = dependency_rules
    
    def is_satisfied(self, design_object: 'DesignObject') -> bool:
        """Check if variable dependencies are satisfied."""
        if not design_object.variables.has_variable(self.dependent_var):
            return True  # Variable not assigned, constraint is vacuously satisfied
        
        dependent_value = design_object.variables.get_variable(self.dependent_var)
        
        for rule_var, rule_condition in self.dependency_rules.items():
            if not design_object.variables.has_variable(rule_var):
                return False  # Dependency variable not assigned
            
            rule_value = design_object.variables.get_variable(rule_var)
            
            # Check different types of rules
            if isinstance(rule_condition, dict):
                if 'equals' in rule_condition and rule_value != rule_condition['equals']:
                    return False
                if 'min' in rule_condition and rule_value < rule_condition['min']:
                    return False
                if 'max' in rule_condition and rule_value > rule_condition['max']:
                    return False
                if 'not_equals' in rule_condition and rule_value == rule_condition['not_equals']:
                    return False
            else:
                # Simple equality check
                if rule_value != rule_condition:
                    return False
        
        return True
    
    def get_violation_message(self, design_object: 'DesignObject') -> str:
        """Get violation message."""
        if not design_object.variables.has_variable(self.dependent_var):
            return f"Dependent variable {self.dependent_var} is not assigned"
        
        for rule_var, rule_condition in self.dependency_rules.items():
            if not design_object.variables.has_variable(rule_var):
                return f"Dependency variable {rule_var} is not assigned"
            
            rule_value = design_object.variables.get_variable(rule_var)
            
            if isinstance(rule_condition, dict):
                if 'equals' in rule_condition and rule_value != rule_condition['equals']:
                    return f"Variable {rule_var} is {rule_value}, expected {rule_condition['equals']}"
                if 'min' in rule_condition and rule_value < rule_condition['min']:
                    return f"Variable {rule_var} is {rule_value}, minimum {rule_condition['min']}"
                if 'max' in rule_condition and rule_value > rule_condition['max']:
                    return f"Variable {rule_var} is {rule_value}, maximum {rule_condition['max']}"
                if 'not_equals' in rule_condition and rule_value == rule_condition['not_equals']:
                    return f"Variable {rule_var} is {rule_value}, must not equal {rule_condition['not_equals']}"
            else:
                if rule_value != rule_condition:
                    return f"Variable {rule_var} is {rule_value}, expected {rule_condition}"
        
        return f"Variable dependency constraint violated for {self.dependent_var}"


class ResourceConstraint(GlobalConstraint):
    """Constraint that checks global resource usage across structure and variables."""
    
    def __init__(self, constraint_id: str, resource_name: str, max_usage: float):
        super().__init__(constraint_id, f"Resource constraint for {resource_name}")
        self.resource_name = resource_name
        self.max_usage = max_usage
    
    def is_satisfied(self, design_object: 'DesignObject') -> bool:
        """Check if total resource usage is within limits."""
        total_usage = 0.0
        
        # Calculate resource usage from components
        for component in design_object.structure.components:
            if self.resource_name in component.properties:
                usage = component.properties[self.resource_name]
                if isinstance(usage, (int, float)):
                    total_usage += usage
        
        # Calculate resource usage from variables
        for var_name, var_value in design_object.variables.assignments.items():
            if var_name.startswith(f"{self.resource_name}_") and isinstance(var_value, (int, float)):
                total_usage += var_value
        
        return total_usage <= self.max_usage
    
    def get_violation_message(self, design_object: 'DesignObject') -> str:
        """Get violation message."""
        total_usage = 0.0
        
        # Calculate total usage
        for component in design_object.structure.components:
            if self.resource_name in component.properties:
                usage = component.properties[self.resource_name]
                if isinstance(usage, (int, float)):
                    total_usage += usage
        
        for var_name, var_value in design_object.variables.assignments.items():
            if var_name.startswith(f"{self.resource_name}_") and isinstance(var_value, (int, float)):
                total_usage += var_value
        
        return f"Resource {self.resource_name} usage {total_usage} exceeds limit {self.max_usage}"


class ConnectivityConstraint(StructuralConstraint):
    """Constraint that checks structural connectivity properties."""
    
    def __init__(self, constraint_id: str, connectivity_type: str = "connected"):
        super().__init__(constraint_id, f"Connectivity constraint: {connectivity_type}")
        self.connectivity_type = connectivity_type
    
    def is_satisfied(self, design_object: 'DesignObject') -> bool:
        """Check connectivity properties."""
        components = design_object.structure.components
        relationships = design_object.structure.relationships
        
        if len(components) <= 1:
            return True  # Single component or empty structure is trivially connected
        
        if self.connectivity_type == "connected":
            return self._is_connected(components, relationships)
        elif self.connectivity_type == "fully_connected":
            return self._is_fully_connected(components, relationships)
        elif self.connectivity_type == "acyclic":
            return self._is_acyclic(components, relationships)
        else:
            return True
    
    def _is_connected(self, components, relationships) -> bool:
        """Check if the structure is connected (all components reachable)."""
        if not components:
            return True
        
        # Build adjacency list
        adjacency = {c.id: set() for c in components}
        for rel in relationships:
            if rel.source_id in adjacency and rel.target_id in adjacency:
                adjacency[rel.source_id].add(rel.target_id)
                adjacency[rel.target_id].add(rel.source_id)  # Treat as undirected
        
        # DFS from first component
        visited = set()
        stack = [components[0].id]
        
        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                stack.extend(adjacency[current] - visited)
        
        return len(visited) == len(components)
    
    def _is_fully_connected(self, components, relationships) -> bool:
        """Check if every component is connected to every other component."""
        n = len(components)
        if n <= 1:
            return True
        
        # Count unique connections
        connections = set()
        for rel in relationships:
            if rel.source_id != rel.target_id:  # No self-loops
                connections.add((min(rel.source_id, rel.target_id), max(rel.source_id, rel.target_id)))
        
        # Full connectivity requires n*(n-1)/2 unique connections
        required_connections = n * (n - 1) // 2
        return len(connections) >= required_connections
    
    def _is_acyclic(self, components, relationships) -> bool:
        """Check if the structure has no cycles (is a DAG)."""
        # Build directed adjacency list
        adjacency = {c.id: [] for c in components}
        for rel in relationships:
            if rel.source_id in adjacency and rel.target_id in adjacency:
                adjacency[rel.source_id].append(rel.target_id)
        
        # DFS cycle detection
        white = set(c.id for c in components)  # Unvisited
        gray = set()   # Currently being processed
        black = set()  # Completely processed
        
        def has_cycle(node):
            if node in gray:
                return True  # Back edge found
            if node in black:
                return False  # Already processed
            
            gray.add(node)
            white.discard(node)
            
            for neighbor in adjacency[node]:
                if has_cycle(neighbor):
                    return True
            
            gray.discard(node)
            black.add(node)
            return False
        
        while white:
            if has_cycle(white.pop()):
                return False
        
        return True
    
    def get_violation_message(self, design_object: 'DesignObject') -> str:
        """Get violation message."""
        if self.connectivity_type == "connected":
            return "Structure is not connected - some components are isolated"
        elif self.connectivity_type == "fully_connected":
            return "Structure is not fully connected - missing required connections"
        elif self.connectivity_type == "acyclic":
            return "Structure contains cycles - must be acyclic"
        else:
            return f"Connectivity constraint {self.connectivity_type} violated"


# Custom evaluator functions for demonstration
def custom_component_evaluator(constraint: Constraint, design_object: 'DesignObject') -> bool:
    """Custom evaluator for component-related constraints."""
    if isinstance(constraint, ComponentPropertyConstraint):
        # Custom logic that might be different from the constraint's built-in method
        return constraint.is_satisfied(design_object)
    return True


def custom_resource_evaluator(constraint: Constraint, design_object: 'DesignObject') -> bool:
    """Custom evaluator for resource constraints with different logic."""
    if isinstance(constraint, ResourceConstraint):
        # Example: More lenient evaluation that allows 10% over the limit
        total_usage = 0.0
        
        for component in design_object.structure.components:
            if constraint.resource_name in component.properties:
                usage = component.properties[constraint.resource_name]
                if isinstance(usage, (int, float)):
                    total_usage += usage
        
        for var_name, var_value in design_object.variables.assignments.items():
            if var_name.startswith(f"{constraint.resource_name}_") and isinstance(var_value, (int, float)):
                total_usage += var_value
        
        # Allow 10% over the limit
        return total_usage <= constraint.max_usage * 1.1
    
    return True