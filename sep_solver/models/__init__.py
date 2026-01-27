"""Data models for the SEP solver."""

from .design_object import DesignObject
from .structure import (
    Structure, Component, Relationship, Modification,
    AddComponentModification, RemoveComponentModification,
    AddRelationshipModification, RemoveRelationshipModification,
    ModifyComponentPropertiesModification, ModifyRelationshipPropertiesModification,
    ChangeComponentTypeModification
)
from .variable_assignment import VariableAssignment, Domain
from .constraint_set import ConstraintSet, Constraint, ConstraintViolation, StructuralConstraint
from .exploration_state import ExplorationState

__all__ = [
    "DesignObject",
    "Structure",
    "Component", 
    "Relationship",
    "Modification",
    "AddComponentModification",
    "RemoveComponentModification", 
    "AddRelationshipModification",
    "RemoveRelationshipModification",
    "ModifyComponentPropertiesModification",
    "ModifyRelationshipPropertiesModification",
    "ChangeComponentTypeModification",
    "StructuralConstraint",
    "VariableAssignment",
    "Domain",
    "ConstraintSet",
    "Constraint",
    "ConstraintViolation",
    "ExplorationState"
]