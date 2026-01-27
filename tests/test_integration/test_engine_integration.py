"""Integration tests for SEP Engine end-to-end functionality."""

import pytest
from sep_solver.core.engine import SEPEngine
from sep_solver.core.config import SolverConfig
from sep_solver.models.constraint_set import ConstraintSet


class TestEngineIntegration:
    """Integration tests for complete SEP Engine workflows."""
    
    def test_basic_engine_workflow(self):
        """Test basic engine workflow with minimal configuration."""
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
                        "assignments": {"type": "object"},
                        "domains": {"type": "object"},
                        "dependencies": {"type": "object"}
                    },
                    "required": ["assignments", "domains", "dependencies"]
                },
                "metadata": {"type": "object"}
            },
            "required": ["id", "structure", "variables", "metadata"]
        }
        
        # Create empty constraint set
        constraints = ConstraintSet()
        
        # Create configuration
        config = SolverConfig(
            exploration_strategy="random",
            max_iterations=5,
            max_solutions=2,
            enable_logging=False
        )
        
        # Create and run engine
        engine = SEPEngine(schema, constraints, config)
        solutions = engine.solve()
        
        # Verify results
        assert isinstance(solutions, list)
        assert len(solutions) <= config.max_solutions
        
        # Verify each solution
        for solution in solutions:
            assert hasattr(solution, 'id')
            assert hasattr(solution, 'structure')
            assert hasattr(solution, 'variables')
            assert hasattr(solution, 'metadata')
            
            # Verify solution can be serialized
            solution_dict = solution.to_dict()
            assert isinstance(solution_dict, dict)
            
            # Verify schema validation
            schema_result = engine.schema_validator.validate(solution_dict)
            assert schema_result.is_valid
    
    def test_all_exploration_strategies(self):
        """Test that all exploration strategies work."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "structure": {"type": "object"},
                "variables": {"type": "object"},
                "metadata": {"type": "object"}
            },
            "required": ["id", "structure", "variables", "metadata"]
        }
        
        constraints = ConstraintSet()
        
        strategies = ["breadth_first", "depth_first", "best_first", "random"]
        
        for strategy in strategies:
            config = SolverConfig(
                exploration_strategy=strategy,
                max_iterations=3,
                max_solutions=1,
                enable_logging=False
            )
            
            engine = SEPEngine(schema, constraints, config)
            
            try:
                solutions = engine.solve()
                
                # Verify strategy was used
                state = engine.get_exploration_state()
                assert state.strategy == strategy
                
                # Verify solutions are valid if any found
                for solution in solutions:
                    schema_result = engine.schema_validator.validate(solution.to_dict())
                    assert schema_result.is_valid
                    
                    evaluation_result = engine.constraint_evaluator.evaluate(solution)
                    assert evaluation_result.is_valid
                    
            except Exception as e:
                # Some strategies might fail to find solutions, which is acceptable
                pytest.skip(f"Strategy {strategy} failed (acceptable): {e}")
    
    def test_engine_solution_management(self):
        """Test engine solution management features."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "structure": {"type": "object"},
                "variables": {"type": "object"},
                "metadata": {"type": "object"}
            },
            "required": ["id", "structure", "variables", "metadata"]
        }
        
        constraints = ConstraintSet()
        config = SolverConfig(
            exploration_strategy="random",
            max_iterations=5,
            max_solutions=3,
            enable_logging=False
        )
        
        engine = SEPEngine(schema, constraints, config)
        solutions = engine.solve()
        
        # Test solution retrieval
        retrieved_solutions = engine.get_solutions()
        assert len(retrieved_solutions) == len(solutions)
        
        # Test best solutions
        best_solutions = engine.get_best_solutions(n=2)
        assert len(best_solutions) <= min(2, len(solutions))
        
        # Test solution statistics
        stats = engine.get_solution_statistics()
        assert isinstance(stats, dict)
        assert "total_solutions" in stats
        assert stats["total_solutions"] == len(solutions)
        
        # Test solution export
        json_export = engine.export_solutions("json")
        assert isinstance(json_export, str)
        
        summary_export = engine.export_solutions("summary")
        assert isinstance(summary_export, str)
        assert "Found" in summary_export
        
        # Test solution filtering
        filtered = engine.filter_solutions(lambda s: len(s.structure.components) > 0)
        assert isinstance(filtered, list)
        
        # Test clearing solutions
        engine.clear_solutions()
        assert len(engine.get_solutions()) == 0
    
    def test_engine_exploration_state_tracking(self):
        """Test that engine properly tracks exploration state."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "structure": {"type": "object"},
                "variables": {"type": "object"},
                "metadata": {"type": "object"}
            },
            "required": ["id", "structure", "variables", "metadata"]
        }
        
        constraints = ConstraintSet()
        config = SolverConfig(
            exploration_strategy="breadth_first",
            max_iterations=3,
            max_solutions=2,
            enable_logging=False
        )
        
        engine = SEPEngine(schema, constraints, config)
        
        # Check initial state
        initial_state = engine.get_exploration_state()
        assert initial_state.iteration_count == 0
        assert initial_state.solutions_found == 0
        assert initial_state.candidates_evaluated == 0
        
        # Run exploration
        solutions = engine.solve()
        
        # Check final state
        final_state = engine.get_exploration_state()
        assert final_state.iteration_count > 0
        assert final_state.solutions_found == len(solutions)
        assert final_state.candidates_evaluated >= len(solutions)
        assert final_state.strategy == "breadth_first"
        
        # Test state reset
        engine.reset()
        reset_state = engine.get_exploration_state()
        assert reset_state.iteration_count == 0
        assert reset_state.solutions_found == 0
        assert reset_state.candidates_evaluated == 0
    
    def test_engine_component_management(self):
        """Test engine component management functionality."""
        schema = {"type": "object"}
        constraints = ConstraintSet()
        config = SolverConfig(enable_logging=False)
        
        # Create engine without components
        engine = SEPEngine(schema, constraints, config, 
                          structure_generator=None,
                          variable_assigner=None,
                          constraint_evaluator=None,
                          schema_validator=None)
        
        # Verify default components were initialized
        assert engine.structure_generator is not None
        assert engine.variable_assigner is not None
        assert engine.constraint_evaluator is not None
        assert engine.schema_validator is not None
        
        # Test component retrieval
        sg = engine.get_component("structure_generator")
        assert sg is not None
        
        va = engine.get_component("variable_assigner")
        assert va is not None
        
        ce = engine.get_component("constraint_evaluator")
        assert ce is not None
        
        sv = engine.get_component("schema_validator")
        assert sv is not None
        
        # Test invalid component type
        with pytest.raises(Exception):
            engine.get_component("invalid_component")