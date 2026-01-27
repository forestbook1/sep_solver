"""Constraint evaluator implementation for the SEP solver."""

from typing import List, Dict, Any, TYPE_CHECKING
from ..core.interfaces import ConstraintEvaluator
from ..core.results import EvaluationResult

if TYPE_CHECKING:
    from ..models.design_object import DesignObject
    from ..models.constraint_set import Constraint, ConstraintViolation, ConstraintSet


class BaseConstraintEvaluator(ConstraintEvaluator):
    """Base implementation of constraint evaluator.
    
    Evaluates constraints against design objects and provides detailed
    violation information for debugging and validation purposes.
    """
    
    def __init__(self, constraint_set: 'ConstraintSet' = None):
        """Initialize the constraint evaluator.
        
        Args:
            constraint_set: Optional constraint set to use for evaluation
        """
        self.constraint_set = constraint_set
        self._custom_evaluators: Dict[str, callable] = {}
    
    def set_constraint_set(self, constraint_set: 'ConstraintSet') -> None:
        """Set the constraint set for evaluation.
        
        Args:
            constraint_set: Constraint set to use
        """
        self.constraint_set = constraint_set
    
    def evaluate(self, design_object: 'DesignObject') -> EvaluationResult:
        """Evaluate all constraints against a design object.
        
        Args:
            design_object: The design object to evaluate
            
        Returns:
            An EvaluationResult containing evaluation details
        """
        if self.constraint_set is None:
            # No constraints to evaluate - consider valid
            return EvaluationResult(is_valid=True, violations=[])
        
        violations = self.get_violations(design_object)
        is_valid = len(violations) == 0
        
        return EvaluationResult(is_valid=is_valid, violations=violations)
    
    def evaluate_constraint(self, constraint: 'Constraint', design_object: 'DesignObject') -> bool:
        """Evaluate a single constraint.
        
        Args:
            constraint: The constraint to evaluate
            design_object: The design object to evaluate against
            
        Returns:
            True if constraint is satisfied, False otherwise
        """
        try:
            # Check if we have a custom evaluator for this constraint type
            constraint_type = constraint.__class__.__name__
            if constraint_type in self._custom_evaluators:
                return self._custom_evaluators[constraint_type](constraint, design_object)
            
            # Use the constraint's built-in evaluation method
            return constraint.is_satisfied(design_object)
        
        except Exception as e:
            # If evaluation fails, consider constraint violated
            # This provides robustness against malformed constraints
            return False
    
    def get_violations(self, design_object: 'DesignObject') -> List['ConstraintViolation']:
        """Return detailed information about constraint violations.
        
        Args:
            design_object: The design object to check
            
        Returns:
            List of ConstraintViolation objects describing violations
        """
        from ..models.constraint_set import ConstraintViolation
        
        violations = []
        
        if self.constraint_set is None:
            return violations
        
        # Evaluate all constraints in the constraint set
        all_constraints = self.constraint_set.get_all_constraints()
        
        for constraint in all_constraints:
            if not self.evaluate_constraint(constraint, design_object):
                # Constraint is violated - create violation record
                try:
                    message = constraint.get_violation_message(design_object)
                except Exception:
                    # Fallback message if constraint can't provide details
                    message = f"Constraint {constraint.constraint_id} is violated"
                
                violation = ConstraintViolation(
                    constraint_id=constraint.constraint_id,
                    constraint_type=constraint.__class__.__name__,
                    message=message,
                    severity="error",
                    context=self._get_violation_context(constraint, design_object)
                )
                violations.append(violation)
        
        return violations
    
    def register_custom_evaluator(self, constraint_type: str, evaluator: callable) -> None:
        """Register a custom evaluator for a specific constraint type.
        
        Args:
            constraint_type: Name of the constraint class
            evaluator: Function that takes (constraint, design_object) and returns bool
        """
        self._custom_evaluators[constraint_type] = evaluator
    
    def unregister_custom_evaluator(self, constraint_type: str) -> bool:
        """Unregister a custom evaluator.
        
        Args:
            constraint_type: Name of the constraint class
            
        Returns:
            True if evaluator was found and removed
        """
        if constraint_type in self._custom_evaluators:
            del self._custom_evaluators[constraint_type]
            return True
        return False
    
    def get_registered_evaluators(self) -> List[str]:
        """Get list of registered custom evaluator types.
        
        Returns:
            List of constraint type names with custom evaluators
        """
        return list(self._custom_evaluators.keys())
    
    def evaluate_constraints_by_type(self, design_object: 'DesignObject', constraint_type: str) -> EvaluationResult:
        """Evaluate only constraints of a specific type.
        
        Args:
            design_object: The design object to evaluate
            constraint_type: Type of constraints to evaluate ("structural", "variable", "global")
            
        Returns:
            EvaluationResult for constraints of the specified type
        """
        if self.constraint_set is None:
            return EvaluationResult(is_valid=True, violations=[])
        
        constraints = self.constraint_set.get_constraints_by_type(constraint_type)
        violations = []
        
        for constraint in constraints:
            if not self.evaluate_constraint(constraint, design_object):
                from ..models.constraint_set import ConstraintViolation
                
                try:
                    message = constraint.get_violation_message(design_object)
                except Exception:
                    message = f"Constraint {constraint.constraint_id} is violated"
                
                violation = ConstraintViolation(
                    constraint_id=constraint.constraint_id,
                    constraint_type=constraint.__class__.__name__,
                    message=message,
                    severity="error",
                    context=self._get_violation_context(constraint, design_object)
                )
                violations.append(violation)
        
        is_valid = len(violations) == 0
        return EvaluationResult(is_valid=is_valid, violations=violations)
    
    def _get_violation_context(self, constraint: 'Constraint', design_object: 'DesignObject') -> Dict[str, Any]:
        """Get context information for a constraint violation.
        
        Args:
            constraint: The violated constraint
            design_object: The design object being evaluated
            
        Returns:
            Dictionary with context information
        """
        context = {
            "constraint_id": constraint.constraint_id,
            "constraint_description": constraint.description,
            "design_object_id": design_object.id,
            "component_count": len(design_object.structure.components),
            "relationship_count": len(design_object.structure.relationships),
            "variable_count": len(design_object.variables.assignments)
        }
        
        # Add constraint-specific context if available
        if hasattr(constraint, 'get_context'):
            try:
                constraint_context = constraint.get_context(design_object)
                context.update(constraint_context)
            except Exception:
                # Ignore errors in context generation
                pass
        
        return context
    
    def get_evaluation_summary(self, design_object: 'DesignObject') -> Dict[str, Any]:
        """Get a summary of constraint evaluation results.
        
        Args:
            design_object: The design object to evaluate
            
        Returns:
            Dictionary with evaluation summary
        """
        result = self.evaluate(design_object)
        
        summary = {
            "is_valid": result.is_valid,
            "total_violations": len(result.violations),
            "violations_by_type": {},
            "violations_by_severity": {}
        }
        
        # Count violations by type and severity
        for violation in result.violations:
            # By type
            if violation.constraint_type not in summary["violations_by_type"]:
                summary["violations_by_type"][violation.constraint_type] = 0
            summary["violations_by_type"][violation.constraint_type] += 1
            
            # By severity
            if violation.severity not in summary["violations_by_severity"]:
                summary["violations_by_severity"][violation.severity] = 0
            summary["violations_by_severity"][violation.severity] += 1
        
        return summary