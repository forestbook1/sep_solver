"""Base variable assigner implementation."""

import random
from typing import Any, Dict, List, Set, TYPE_CHECKING
from ..core.interfaces import VariableAssigner
from ..core.exceptions import VariableAssignmentError

if TYPE_CHECKING:
    from ..models.structure import Structure
    from ..models.variable_assignment import VariableAssignment, AssignmentSpace, Domain


class BaseVariableAssigner(VariableAssigner):
    """Base implementation of variable assigner with multiple assignment strategies."""
    
    def __init__(self, seed: int = None):
        """Initialize the base variable assigner.
        
        Args:
            seed: Random seed for reproducible assignments
        """
        self.random = random.Random(seed)
    
    def assign_variables(self, structure: 'Structure', strategy: str = "random") -> 'VariableAssignment':
        """Assign values to all variables in the structure.
        
        Args:
            structure: The structure containing variables to assign
            strategy: Assignment strategy ("random", "systematic", "heuristic")
            
        Returns:
            A VariableAssignment object with all variables assigned
            
        Raises:
            VariableAssignmentError: If assignment fails
        """
        from ..models.variable_assignment import VariableAssignment
        
        # Extract variables from structure
        assignment = self._extract_variables_from_structure(structure)
        
        # Apply assignment strategy
        if strategy == "random":
            return self._assign_random(assignment)
        elif strategy == "systematic":
            return self._assign_systematic(assignment)
        elif strategy == "heuristic":
            return self._assign_heuristic(assignment)
        else:
            raise VariableAssignmentError(f"Unknown assignment strategy: {strategy}")
    
    def modify_assignment(self, assignment: 'VariableAssignment', variable: str, value: Any) -> 'VariableAssignment':
        """Modify a specific variable assignment.
        
        Args:
            assignment: The current variable assignment
            variable: Name of the variable to modify
            value: New value for the variable
            
        Returns:
            A new VariableAssignment with the modified value
            
        Raises:
            VariableAssignmentError: If modification fails
        """
        # Create a copy of the assignment
        new_assignment = assignment.copy()
        
        # Validate the new value if domain exists
        if variable in new_assignment.domains:
            domain = new_assignment.domains[variable]
            if not domain.is_valid_value(value):
                raise VariableAssignmentError(
                    f"Value {value} is not valid for variable '{variable}' with domain {domain.type}",
                    variable_name=variable,
                    attempted_value=value
                )
        
        # Set the new value
        try:
            new_assignment.set_variable(variable, value)
        except ValueError as e:
            raise VariableAssignmentError(
                f"Failed to set variable '{variable}' to {value}: {str(e)}",
                variable_name=variable,
                attempted_value=value
            )
        
        # Check if dependencies are still satisfied
        dependency_violations = self.validate_dependencies(new_assignment)
        if dependency_violations:
            # Try to resolve dependency conflicts
            resolved_assignment = self.resolve_dependency_conflicts(new_assignment)
            
            # Check if resolution worked
            if self.validate_dependencies(resolved_assignment):
                raise VariableAssignmentError(
                    f"Modifying variable '{variable}' to {value} creates unresolvable dependency violations: {dependency_violations}",
                    variable_name=variable,
                    attempted_value=value
                )
            
            return resolved_assignment
        
        # Check basic consistency
        if not new_assignment.is_consistent():
            raise VariableAssignmentError(
                f"Modifying variable '{variable}' to {value} violates consistency constraints",
                variable_name=variable,
                attempted_value=value
            )
        
        return new_assignment
    
    def modify_assignment_batch(self, assignment: 'VariableAssignment', modifications: Dict[str, Any]) -> 'VariableAssignment':
        """Modify multiple variable assignments in a batch.
        
        Args:
            assignment: The current variable assignment
            modifications: Dictionary of variable names to new values
            
        Returns:
            A new VariableAssignment with all modifications applied
            
        Raises:
            VariableAssignmentError: If any modification fails
        """
        # Create a copy of the assignment
        new_assignment = assignment.copy()
        
        # Apply all modifications
        for variable, value in modifications.items():
            # Validate the new value if domain exists
            if variable in new_assignment.domains:
                domain = new_assignment.domains[variable]
                if not domain.is_valid_value(value):
                    raise VariableAssignmentError(
                        f"Value {value} is not valid for variable '{variable}' with domain {domain.type}",
                        variable_name=variable,
                        attempted_value=value
                    )
            
            # Set the new value
            try:
                new_assignment.set_variable(variable, value)
            except ValueError as e:
                raise VariableAssignmentError(
                    f"Failed to set variable '{variable}' to {value}: {str(e)}",
                    variable_name=variable,
                    attempted_value=value
                )
        
        # Check if dependencies are still satisfied after all modifications
        dependency_violations = self.validate_dependencies(new_assignment)
        if dependency_violations:
            # Try to resolve dependency conflicts
            resolved_assignment = self.resolve_dependency_conflicts(new_assignment)
            
            # Check if resolution worked
            if self.validate_dependencies(resolved_assignment):
                raise VariableAssignmentError(
                    f"Batch modifications create unresolvable dependency violations: {dependency_violations}"
                )
            
            return resolved_assignment
        
        # Check basic consistency
        if not new_assignment.is_consistent():
            raise VariableAssignmentError(
                "Batch modifications violate consistency constraints"
            )
        
        return new_assignment
    
    def get_assignment_space(self, structure: 'Structure') -> 'AssignmentSpace':
        """Return the space of possible assignments for a structure.
        
        Args:
            structure: The structure to analyze
            
        Returns:
            An AssignmentSpace describing possible assignments
        """
        from ..models.variable_assignment import AssignmentSpace
        
        # Extract variables and their domains from structure
        assignment = self._extract_variables_from_structure(structure)
        
        return AssignmentSpace(
            domains=assignment.domains,
            dependencies=assignment.dependencies
        )
    
    def _extract_variables_from_structure(self, structure: 'Structure') -> 'VariableAssignment':
        """Extract variables and their domains from a structure.
        
        Args:
            structure: The structure to extract variables from
            
        Returns:
            A VariableAssignment with domains but no assignments
        """
        from ..models.variable_assignment import VariableAssignment, Domain
        
        assignment = VariableAssignment()
        
        # Extract variables from component properties
        for component in structure.components:
            for prop_name, prop_value in component.properties.items():
                if isinstance(prop_value, dict) and "variable" in prop_value:
                    var_info = prop_value["variable"]
                    var_name = f"{component.id}.{prop_name}"
                    
                    # Create domain from variable info
                    domain = Domain(
                        name=var_name,
                        type=var_info.get("type", "string"),
                        constraints=var_info.get("constraints", {})
                    )
                    assignment.add_domain(domain)
                    
                    # Add dependencies if specified
                    if "depends_on" in var_info:
                        deps = var_info["depends_on"]
                        if isinstance(deps, str):
                            deps = [deps]
                        # Resolve dependency names to full variable names
                        resolved_deps = []
                        for dep in deps:
                            if "." not in dep:
                                # Assume it's a property of the same component
                                resolved_deps.append(f"{component.id}.{dep}")
                            else:
                                resolved_deps.append(dep)
                        assignment.add_dependency(var_name, resolved_deps)
        
        # Extract variables from relationship properties
        for relationship in structure.relationships:
            for prop_name, prop_value in relationship.properties.items():
                if isinstance(prop_value, dict) and "variable" in prop_value:
                    var_info = prop_value["variable"]
                    var_name = f"{relationship.id}.{prop_name}"
                    
                    # Create domain from variable info
                    domain = Domain(
                        name=var_name,
                        type=var_info.get("type", "string"),
                        constraints=var_info.get("constraints", {})
                    )
                    assignment.add_domain(domain)
                    
                    # Add dependencies if specified
                    if "depends_on" in var_info:
                        deps = var_info["depends_on"]
                        if isinstance(deps, str):
                            deps = [deps]
                        # Resolve dependency names to full variable names
                        resolved_deps = []
                        for dep in deps:
                            if "." not in dep:
                                # For relationships, dependencies might reference components
                                # Try both source and target components
                                resolved_deps.extend([
                                    f"{relationship.source_id}.{dep}",
                                    f"{relationship.target_id}.{dep}"
                                ])
                            else:
                                resolved_deps.append(dep)
                        assignment.add_dependency(var_name, resolved_deps)
        
        return assignment
    
    def _assign_random(self, assignment: 'VariableAssignment') -> 'VariableAssignment':
        """Assign variables using random strategy.
        
        Args:
            assignment: Assignment with domains to fill
            
        Returns:
            Assignment with all variables assigned randomly
        """
        # Get variables in random order
        variables = list(assignment.domains.keys())
        self.random.shuffle(variables)
        
        # Assign each variable
        for var_name in variables:
            domain = assignment.domains[var_name]
            value = self._generate_random_value(domain)
            assignment.set_variable(var_name, value)
        
        return assignment
    
    def _assign_systematic(self, assignment: 'VariableAssignment') -> 'VariableAssignment':
        """Assign variables using systematic strategy (dependency-aware).
        
        Args:
            assignment: Assignment with domains to fill
            
        Returns:
            Assignment with all variables assigned systematically
        """
        # Topologically sort variables by dependencies
        sorted_vars = self._topological_sort(assignment)
        
        # Assign variables in dependency order
        for var_name in sorted_vars:
            domain = assignment.domains[var_name]
            
            # For systematic assignment, consider dependencies when choosing value
            value = self._choose_value_considering_dependencies(var_name, domain, assignment)
            assignment.set_variable(var_name, value)
        
        return assignment
    
    def _choose_value_considering_dependencies(self, var_name: str, domain: 'Domain', assignment: 'VariableAssignment') -> Any:
        """Choose a value for a variable considering its dependencies.
        
        Args:
            var_name: Name of the variable
            domain: Domain of the variable
            assignment: Current assignment state
            
        Returns:
            A value that considers dependency constraints
        """
        # Check if this variable has dependencies
        if var_name in assignment.dependencies:
            deps = assignment.dependencies[var_name]
            
            # Check if all dependencies are satisfied
            for dep in deps:
                if dep not in assignment.assignments:
                    # Dependency not yet assigned, use default value
                    return domain.get_sample_value()
            
            # All dependencies are assigned, we can use dependency-aware logic
            # For now, just use sample value, but this could be enhanced
            # with actual dependency constraint evaluation
            return domain.get_sample_value()
        else:
            # No dependencies, use sample value
            return domain.get_sample_value()
    
    def validate_dependencies(self, assignment: 'VariableAssignment') -> List[str]:
        """Validate that all dependencies are satisfied in an assignment.
        
        Args:
            assignment: Assignment to validate
            
        Returns:
            List of dependency violation messages (empty if all satisfied)
        """
        violations = []
        
        for var_name, deps in assignment.dependencies.items():
            if var_name in assignment.assignments:
                for dep in deps:
                    if dep not in assignment.assignments:
                        violations.append(f"Variable '{var_name}' depends on '{dep}' which is not assigned")
                    else:
                        # Could add more sophisticated dependency validation here
                        # For now, just check that the dependency exists
                        pass
        
        return violations
    
    def resolve_dependency_conflicts(self, assignment: 'VariableAssignment') -> 'VariableAssignment':
        """Attempt to resolve dependency conflicts in an assignment.
        
        Args:
            assignment: Assignment with potential conflicts
            
        Returns:
            Assignment with conflicts resolved (or original if unresolvable)
        """
        # Create a copy to work with
        resolved_assignment = assignment.copy()
        
        # Check for dependency violations
        violations = self.validate_dependencies(resolved_assignment)
        
        if not violations:
            return resolved_assignment
        
        # Try to resolve by reassigning variables in dependency order
        try:
            sorted_vars = self._topological_sort(resolved_assignment)
            
            # Clear assignments and reassign in proper order
            resolved_assignment.assignments.clear()
            
            for var_name in sorted_vars:
                if var_name in resolved_assignment.domains:
                    domain = resolved_assignment.domains[var_name]
                    value = self._choose_value_considering_dependencies(var_name, domain, resolved_assignment)
                    resolved_assignment.set_variable(var_name, value)
            
            return resolved_assignment
            
        except Exception:
            # If resolution fails, return original assignment
            return assignment
    
    def _assign_heuristic(self, assignment: 'VariableAssignment') -> 'VariableAssignment':
        """Assign variables using heuristic strategy (most constrained first).
        
        Args:
            assignment: Assignment with domains to fill
            
        Returns:
            Assignment with all variables assigned using heuristics
        """
        # Sort variables by constraint level (most constrained first)
        variables = list(assignment.domains.keys())
        variables.sort(key=lambda v: self._get_constraint_score(assignment.domains[v]), reverse=True)
        
        # Assign variables in constraint order
        for var_name in variables:
            domain = assignment.domains[var_name]
            
            # Use heuristic to pick good value
            value = self._generate_heuristic_value(domain, assignment)
            assignment.set_variable(var_name, value)
        
        return assignment
    
    def _topological_sort(self, assignment: 'VariableAssignment') -> List[str]:
        """Topologically sort variables by their dependencies.
        
        Args:
            assignment: Assignment with dependency information
            
        Returns:
            List of variable names in dependency order
        """
        # Build dependency graph
        in_degree = {var: 0 for var in assignment.domains.keys()}
        graph = {var: [] for var in assignment.domains.keys()}
        
        for var, deps in assignment.dependencies.items():
            if var in in_degree:
                for dep in deps:
                    if dep in graph:
                        graph[dep].append(var)
                        in_degree[var] += 1
        
        # Kahn's algorithm
        queue = [var for var, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            var = queue.pop(0)
            result.append(var)
            
            for neighbor in graph[var]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(assignment.domains):
            # If there's a cycle, just return variables in original order
            return list(assignment.domains.keys())
        
        return result
    
    def _get_constraint_score(self, domain: 'Domain') -> int:
        """Calculate constraint score for a domain (higher = more constrained).
        
        Args:
            domain: Domain to score
            
        Returns:
            Constraint score
        """
        score = 0
        
        # Type constraints
        if domain.type in ["enum", "bool"]:
            score += 10  # Very constrained
        elif domain.type in ["int", "range"]:
            score += 5   # Moderately constrained
        else:
            score += 1   # Minimally constrained
        
        # Range constraints
        if "min" in domain.constraints or "max" in domain.constraints:
            score += 3
        
        # Enum size
        if domain.type == "enum":
            values = domain.constraints.get("values", [])
            score += max(0, 10 - len(values))  # Fewer options = more constrained
        
        return score
    
    def _generate_random_value(self, domain: 'Domain') -> Any:
        """Generate a random value for a domain.
        
        Args:
            domain: Domain to generate value for
            
        Returns:
            Random valid value for the domain
        """
        if domain.type == "int":
            min_val = domain.constraints.get("min", 0)
            max_val = domain.constraints.get("max", 100)
            return self.random.randint(min_val, max_val)
        elif domain.type == "float":
            min_val = domain.constraints.get("min", 0.0)
            max_val = domain.constraints.get("max", 1.0)
            return self.random.uniform(min_val, max_val)
        elif domain.type == "bool":
            return self.random.choice([True, False])
        elif domain.type == "enum":
            values = domain.constraints.get("values", ["default"])
            return self.random.choice(values)
        elif domain.type == "string":
            # Generate random string
            length = self.random.randint(1, 10)
            chars = "abcdefghijklmnopqrstuvwxyz"
            return ''.join(self.random.choice(chars) for _ in range(length))
        elif domain.type == "range":
            min_val = domain.constraints.get("min", 0)
            max_val = domain.constraints.get("max", 100)
            return self.random.randint(min_val, max_val)
        else:
            # Fallback
            return domain.get_sample_value()
    
    def _generate_heuristic_value(self, domain: 'Domain', assignment: 'VariableAssignment') -> Any:
        """Generate a heuristic value for a domain.
        
        Args:
            domain: Domain to generate value for
            assignment: Current assignment state
            
        Returns:
            Heuristically chosen value for the domain
        """
        # For heuristic assignment, prefer middle values for ranges
        if domain.type == "int":
            min_val = domain.constraints.get("min", 0)
            max_val = domain.constraints.get("max", 100)
            return (min_val + max_val) // 2
        elif domain.type == "float":
            min_val = domain.constraints.get("min", 0.0)
            max_val = domain.constraints.get("max", 1.0)
            return (min_val + max_val) / 2.0
        elif domain.type == "bool":
            # Prefer False for heuristic (arbitrary choice)
            return False
        elif domain.type == "enum":
            values = domain.constraints.get("values", ["default"])
            # Prefer first value for heuristic
            return values[0]
        elif domain.type == "range":
            min_val = domain.constraints.get("min", 0)
            max_val = domain.constraints.get("max", 100)
            return (min_val + max_val) // 2
        else:
            # Fallback to sample value
            return domain.get_sample_value()