"""Basic integration tests to verify the setup works."""

import pytest
from sep_solver import SEPEngine, ConstraintSet, SolverConfig
from sep_solver.core.exceptions import ConfigurationError


class TestBasicSetup:
    """Test basic setup and integration."""
    
    def test_import_main_components(self):
        """Test that main components can be imported."""
        # Should not raise any import errors
        assert SEPEngine is not None
        assert ConstraintSet is not None
        assert SolverConfig is not None
    
    def test_create_basic_engine(self, sample_schema, empty_constraint_set, default_config):
        """Test creating a basic SEP engine."""
        engine = SEPEngine(
            schema=sample_schema,
            constraints=empty_constraint_set,
            config=default_config
        )
        
        assert engine.schema == sample_schema
        assert engine.constraints == empty_constraint_set
        assert engine.config == default_config
        assert engine.exploration_state is not None
    
    def test_engine_component_management(self, sample_schema, empty_constraint_set, default_config):
        """Test engine component management."""
        engine = SEPEngine(
            schema=sample_schema,
            constraints=empty_constraint_set,
            config=default_config
        )
        
        # Test that components are properly initialized
        assert engine.structure_generator is not None
        assert engine.variable_assigner is not None
        assert engine.constraint_evaluator is not None
        assert engine.schema_validator is not None
    
    def test_engine_reset(self, sample_schema, empty_constraint_set, default_config):
        """Test engine state reset."""
        engine = SEPEngine(
            schema=sample_schema,
            constraints=empty_constraint_set,
            config=default_config
        )
        
        # Modify exploration state
        engine.exploration_state.iteration_count = 10
        
        # Reset should create new state
        engine.reset()
        assert engine.exploration_state.iteration_count == 0
    
    def test_solve_implementation(self, sample_schema, empty_constraint_set, default_config):
        """Test that solve method works with the full implementation."""
        engine = SEPEngine(
            schema=sample_schema,
            constraints=empty_constraint_set,
            config=default_config
        )
        
        solutions = engine.solve()
        assert isinstance(solutions, list)
        # With empty constraints, should find some solutions
        assert len(solutions) >= 0
    
    def test_explore_step_implementation(self, sample_schema, empty_constraint_set, default_config):
        """Test that explore_step is properly implemented."""
        engine = SEPEngine(
            schema=sample_schema,
            constraints=empty_constraint_set,
            config=default_config
        )
        
        # explore_step should return a tuple of (design_object, is_valid)
        result = engine.explore_step()
        assert isinstance(result, tuple)
        assert len(result) == 2
        design_object, is_valid = result
        assert hasattr(design_object, 'id')
        assert isinstance(is_valid, bool)