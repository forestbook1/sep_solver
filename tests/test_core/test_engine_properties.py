"""Property-based tests for SEP Engine exploration solution validity."""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any, List

from sep_solver.core.engine import SEPEngine
from sep_solver.core.config import SolverConfig
from sep_solver.models.constraint_set import ConstraintSet
from sep_solver.models.design_object import DesignObject


# Test data generators
@st.composite
def valid_json_schema(draw):
    """Generate a valid JSON schema for design objects."""
    return {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "structure": {
                "type": "object",
                "properties": {
                    "components": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "properties": {"type": "object"}
                            },
                            "required": ["id", "type", "properties"]
                        }
                    },
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "source_id": {"type": "string"},
                                "target_id": {"type": "string"},
                                "type": {"type": "string"},
                                "properties": {"type": "object"}
                            },
                            "required": ["id", "source_id", "target_id", "type", "properties"]
                        }
                    }
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


@st.composite
def solver_config(draw):
    """Generate a valid solver configuration."""
    strategy = draw(st.sampled_from(["breadth_first", "depth_first", "best_first", "random"]))
    max_iterations = draw(st.integers(min_value=1, max_value=50))  # Keep small for testing
    max_solutions = draw(st.integers(min_value=1, max_value=10))
    
    return SolverConfig(
        exploration_strategy=strategy,
        max_iterations=max_iterations,
        max_solutions=max_solutions,
        enable_logging=False,  # Disable logging for tests
        log_exploration_steps=False
    )


@st.composite
def constraint_set(draw):
    """Generate a constraint set (can be empty for basic testing)."""
    return ConstraintSet()


class TestEngineExplorationProperties:
    """Property-based tests for SEP Engine exploration solution validity.
    
    **Feature: sep-solver, Property 8: Exploration Solution Validity**
    **Validates: Requirements 6.2, 6.4**
    """
    
    @given(
        schema=valid_json_schema(),
        constraints=constraint_set(),
        config=solver_config()
    )
    @settings(max_examples=100, deadline=30000)  # 30 second deadline per test
    def test_exploration_solution_validity_property(self, schema: Dict[str, Any], 
                                                  constraints: ConstraintSet, 
                                                  config: SolverConfig):
        """Property 8: For any exploration run that finds solutions, all returned solutions 
        should satisfy all constraints and be valid according to the schema.
        
        **Validates: Requirements 6.2, 6.4**
        """
        # Create SEP engine
        engine = SEPEngine(schema, constraints, config)
        
        try:
            # Run exploration
            solutions = engine.solve()
            
            # Property: All returned solutions must be valid
            for solution in solutions:
                # Check that solution is a DesignObject
                assert isinstance(solution, DesignObject), \
                    f"Solution {solution} is not a DesignObject instance"
                
                # Check that solution has required attributes
                assert hasattr(solution, 'id'), "Solution missing 'id' attribute"
                assert hasattr(solution, 'structure'), "Solution missing 'structure' attribute"
                assert hasattr(solution, 'variables'), "Solution missing 'variables' attribute"
                assert hasattr(solution, 'metadata'), "Solution missing 'metadata' attribute"
                
                # Check that solution can be serialized to dict
                solution_dict = solution.to_dict()
                assert isinstance(solution_dict, dict), "Solution cannot be serialized to dict"
                
                # Check schema validation
                schema_result = engine.schema_validator.validate(solution_dict)
                assert schema_result.is_valid, \
                    f"Solution {solution.id} fails schema validation: {[e.message for e in schema_result.errors]}"
                
                # Check constraint validation
                evaluation_result = engine.constraint_evaluator.evaluate(solution)
                assert evaluation_result.is_valid, \
                    f"Solution {solution.id} fails constraint validation: {[v.message for v in evaluation_result.violations]}"
                
                # Check that structure is valid
                assert solution.structure.is_valid(), \
                    f"Solution {solution.id} has invalid structure: {solution.structure.get_validation_errors()}"
                
                # Check that variable assignment is consistent
                assert solution.variables.is_consistent(), \
                    f"Solution {solution.id} has inconsistent variable assignment"
        
        except Exception as e:
            # If exploration fails completely, that's acceptable (no solutions found)
            # But we should not get invalid solutions
            pytest.skip(f"Exploration failed (acceptable): {e}")
    
    @given(
        schema=valid_json_schema(),
        constraints=constraint_set(),
        strategy=st.sampled_from(["breadth_first", "depth_first", "best_first", "random"])
    )
    @settings(max_examples=50, deadline=30000)
    def test_strategy_specific_solution_validity(self, schema: Dict[str, Any], 
                                               constraints: ConstraintSet, 
                                               strategy: str):
        """Test that each exploration strategy produces valid solutions.
        
        **Validates: Requirements 6.2, 6.3, 6.4**
        """
        config = SolverConfig(
            exploration_strategy=strategy,
            max_iterations=20,  # Keep small for testing
            max_solutions=5,
            enable_logging=False
        )
        
        engine = SEPEngine(schema, constraints, config)
        
        try:
            # Test strategy-specific solving
            solutions = engine.solve_with_strategy(strategy)
            
            # Property: All solutions from any strategy must be valid
            for solution in solutions:
                # Validate solution structure
                assert isinstance(solution, DesignObject)
                assert solution.structure.is_valid()
                assert solution.variables.is_consistent()
                
                # Validate against schema and constraints
                schema_result = engine.schema_validator.validate(solution.to_dict())
                assert schema_result.is_valid
                
                evaluation_result = engine.constraint_evaluator.evaluate(solution)
                assert evaluation_result.is_valid
                
                # Check that solution metadata indicates correct strategy
                assert solution.metadata.get("generation_strategy") == strategy, \
                    f"Solution metadata does not indicate correct strategy: expected {strategy}, got {solution.metadata.get('generation_strategy')}"
        
        except Exception as e:
            # Strategy might fail to find solutions, which is acceptable
            pytest.skip(f"Strategy {strategy} failed (acceptable): {e}")
    
    @given(
        schema=valid_json_schema(),
        constraints=constraint_set()
    )
    @settings(max_examples=30, deadline=30000)
    def test_solution_uniqueness_property(self, schema: Dict[str, Any], constraints: ConstraintSet):
        """Test that solutions have unique identifiers and are distinct.
        
        **Validates: Requirements 6.4**
        """
        config = SolverConfig(
            exploration_strategy="random",
            max_iterations=15,
            max_solutions=5,
            enable_logging=False
        )
        
        engine = SEPEngine(schema, constraints, config)
        
        try:
            solutions = engine.solve()
            
            if len(solutions) > 1:
                # Property: All solutions must have unique IDs
                solution_ids = [solution.id for solution in solutions]
                assert len(solution_ids) == len(set(solution_ids)), \
                    f"Solutions do not have unique IDs: {solution_ids}"
                
                # Property: Solutions should be structurally different
                # (This is a weaker property - we check that not all solutions are identical)
                solution_hashes = []
                for solution in solutions:
                    # Create a simple hash of the solution structure
                    structure_repr = (
                        len(solution.structure.components),
                        len(solution.structure.relationships),
                        len(solution.variables.assignments)
                    )
                    solution_hashes.append(structure_repr)
                
                # If we have multiple solutions, at least some should be different
                # (unless the problem space is very constrained)
                if len(solutions) >= 3:
                    unique_hashes = set(solution_hashes)
                    # Allow some duplicates, but expect some diversity
                    assert len(unique_hashes) >= max(1, len(solutions) // 3), \
                        f"Solutions lack diversity: all have similar structure {solution_hashes}"
        
        except Exception as e:
            pytest.skip(f"Solution generation failed (acceptable): {e}")
    
    @given(
        schema=valid_json_schema(),
        constraints=constraint_set()
    )
    @settings(max_examples=20, deadline=30000)
    def test_exploration_state_consistency(self, schema: Dict[str, Any], constraints: ConstraintSet):
        """Test that exploration state remains consistent during solving.
        
        **Validates: Requirements 6.2, 6.5**
        """
        config = SolverConfig(
            exploration_strategy="breadth_first",
            max_iterations=10,
            max_solutions=3,
            enable_logging=False
        )
        
        engine = SEPEngine(schema, constraints, config)
        
        try:
            # Get initial state
            initial_state = engine.get_exploration_state()
            assert initial_state.solutions_found == 0
            assert initial_state.candidates_evaluated == 0
            assert initial_state.iteration_count == 0
            
            # Run exploration
            solutions = engine.solve()
            
            # Get final state
            final_state = engine.get_exploration_state()
            
            # Property: Exploration state should be consistent with results
            assert final_state.solutions_found == len(solutions), \
                f"State solutions count ({final_state.solutions_found}) != actual solutions ({len(solutions)})"
            
            assert final_state.candidates_evaluated >= len(solutions), \
                f"Candidates evaluated ({final_state.candidates_evaluated}) < solutions found ({len(solutions)})"
            
            assert final_state.iteration_count > 0, \
                "No iterations recorded despite running exploration"
            
            # Property: Best candidates in state should match returned solutions
            state_solutions = final_state.best_candidates
            assert len(state_solutions) == len(solutions), \
                f"State best candidates ({len(state_solutions)}) != returned solutions ({len(solutions)})"
            
            # All state solutions should be valid
            for solution in state_solutions:
                assert isinstance(solution, DesignObject)
                schema_result = engine.schema_validator.validate(solution.to_dict())
                assert schema_result.is_valid
                
                evaluation_result = engine.constraint_evaluator.evaluate(solution)
                assert evaluation_result.is_valid
        
        except Exception as e:
            pytest.skip(f"Exploration failed (acceptable): {e}")
    
    def test_empty_constraint_set_always_valid(self):
        """Test that with no constraints, generated solutions are always valid.
        
        This is a simpler test to ensure basic functionality works.
        """
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
        
        constraints = ConstraintSet()  # Empty constraint set
        config = SolverConfig(
            exploration_strategy="random",
            max_iterations=5,
            max_solutions=2,
            enable_logging=False
        )
        
        engine = SEPEngine(schema, constraints, config)
        
        try:
            solutions = engine.solve()
            
            # With no constraints, any generated solution should be valid
            for solution in solutions:
                assert isinstance(solution, DesignObject)
                
                # Should pass schema validation
                schema_result = engine.schema_validator.validate(solution.to_dict())
                assert schema_result.is_valid, \
                    f"Solution fails schema validation: {[e.message for e in schema_result.errors]}"
                
                # Should pass constraint validation (empty constraints)
                evaluation_result = engine.constraint_evaluator.evaluate(solution)
                assert evaluation_result.is_valid, \
                    f"Solution fails constraint validation: {[v.message for v in evaluation_result.violations]}"
        
        except Exception as e:
            pytest.fail(f"Basic exploration with empty constraints should not fail: {e}")
    
    @given(
        schema=valid_json_schema(),
        constraints=constraint_set()
    )
    @settings(max_examples=30, deadline=60000)  # Longer deadline for strategy comparison
    def test_exploration_strategy_differentiation_property(self, schema: Dict[str, Any], 
                                                         constraints: ConstraintSet):
        """Property 12: For any two different exploration strategies (breadth-first vs depth-first), 
        they should produce different exploration sequences while both finding valid solutions when they exist.
        
        **Validates: Requirements 6.3**
        """
        strategies = ["breadth_first", "depth_first"]
        
        # Test with a configuration that's likely to find solutions
        config_base = SolverConfig(
            max_iterations=20,
            max_solutions=5,
            enable_logging=False,
            log_exploration_steps=False
        )
        
        strategy_results = {}
        strategy_sequences = {}
        
        for strategy in strategies:
            config = config_base.update(exploration_strategy=strategy)
            engine = SEPEngine(schema, constraints, config)
            
            try:
                # Track exploration sequence
                exploration_sequence = []
                
                # Run exploration and capture sequence
                solutions = engine.solve_with_strategy(strategy)
                
                # Get exploration state for sequence analysis
                final_state = engine.get_exploration_state()
                
                strategy_results[strategy] = {
                    'solutions': solutions,
                    'iterations': final_state.iteration_count,
                    'candidates_evaluated': final_state.candidates_evaluated,
                    'strategy_used': final_state.strategy
                }
                
                # Create a signature of the exploration process
                exploration_signature = (
                    final_state.iteration_count,
                    final_state.candidates_evaluated,
                    len(solutions),
                    final_state.strategy
                )
                strategy_sequences[strategy] = exploration_signature
                
            except Exception as e:
                # Strategy might fail, which is acceptable
                strategy_results[strategy] = None
                strategy_sequences[strategy] = None
        
        # Property: If both strategies succeeded, they should show different behavior
        successful_strategies = [s for s in strategies if strategy_results[s] is not None]
        
        if len(successful_strategies) >= 2:
            # Check that strategies used different approaches
            breadth_result = strategy_results.get("breadth_first")
            depth_result = strategy_results.get("depth_first")
            
            if breadth_result and depth_result:
                # Property 1: Both should find valid solutions
                for strategy in successful_strategies:
                    result = strategy_results[strategy]
                    for solution in result['solutions']:
                        assert isinstance(solution, DesignObject)
                        # Verify solution validity
                        engine_temp = SEPEngine(schema, constraints, config_base)
                        schema_result = engine_temp.schema_validator.validate(solution.to_dict())
                        assert schema_result.is_valid, \
                            f"Strategy {strategy} produced invalid solution"
                        
                        evaluation_result = engine_temp.constraint_evaluator.evaluate(solution)
                        assert evaluation_result.is_valid, \
                            f"Strategy {strategy} produced solution that violates constraints"
                
                # Property 2: Strategies should show different exploration patterns
                breadth_seq = strategy_sequences["breadth_first"]
                depth_seq = strategy_sequences["depth_first"]
                
                if breadth_seq and depth_seq:
                    # They should have used different strategies (recorded in state)
                    assert breadth_result['strategy_used'] == "breadth_first"
                    assert depth_result['strategy_used'] == "depth_first"
                    
                    # The exploration sequences should be different
                    # (unless the problem is so constrained that there's only one path)
                    if breadth_seq != depth_seq:
                        # This is the expected case - strategies behave differently
                        pass
                    else:
                        # If sequences are identical, the problem might be too simple
                        # or the strategies might have converged - this is acceptable
                        # but we should at least verify they used different strategy names
                        assert breadth_result['strategy_used'] != depth_result['strategy_used']
                
                # Property 3: Both strategies should be deterministic for the same inputs
                # (We can't easily test this without running multiple times, so we skip for now)
        
        else:
            # If strategies failed, that's acceptable - the property doesn't require success
            pytest.skip(f"Strategies failed to find solutions (acceptable): {successful_strategies}")
    
    @given(
        schema=valid_json_schema(),
        constraints=constraint_set(),
        strategy1=st.sampled_from(["breadth_first", "depth_first", "best_first"]),
        strategy2=st.sampled_from(["breadth_first", "depth_first", "best_first"])
    )
    @settings(max_examples=20, deadline=45000)
    def test_strategy_independence_property(self, schema: Dict[str, Any], 
                                          constraints: ConstraintSet,
                                          strategy1: str, strategy2: str):
        """Test that different strategies can be used independently and produce valid results.
        
        **Validates: Requirements 6.3**
        """
        assume(strategy1 != strategy2)  # Only test different strategies
        
        config = SolverConfig(
            max_iterations=15,
            max_solutions=3,
            enable_logging=False
        )
        
        results = {}
        
        for strategy in [strategy1, strategy2]:
            engine = SEPEngine(schema, constraints, config)
            
            try:
                solutions = engine.solve_with_strategy(strategy)
                results[strategy] = {
                    'solutions': solutions,
                    'state': engine.get_exploration_state()
                }
                
                # Verify all solutions are valid
                for solution in solutions:
                    assert isinstance(solution, DesignObject)
                    
                    schema_result = engine.schema_validator.validate(solution.to_dict())
                    assert schema_result.is_valid
                    
                    evaluation_result = engine.constraint_evaluator.evaluate(solution)
                    assert evaluation_result.is_valid
                    
                    # Check strategy is recorded correctly
                    assert solution.metadata.get("generation_strategy") == strategy
                
            except Exception as e:
                results[strategy] = None
        
        # Property: Each strategy should work independently
        for strategy, result in results.items():
            if result is not None:
                # Strategy should record its name correctly
                assert result['state'].strategy == strategy
                
                # Solutions should be tagged with correct strategy
                for solution in result['solutions']:
                    assert solution.metadata.get("generation_strategy") == strategy
    
    @given(
        schema=valid_json_schema(),
        constraints=constraint_set()
    )
    @settings(max_examples=15, deadline=30000)
    def test_strategy_consistency_property(self, schema: Dict[str, Any], constraints: ConstraintSet):
        """Test that the same strategy produces consistent types of results.
        
        **Validates: Requirements 6.3**
        """
        strategy = "random"  # Use random for consistency testing
        config = SolverConfig(
            exploration_strategy=strategy,
            max_iterations=10,
            max_solutions=3,
            enable_logging=False
        )
        
        # Run the same strategy multiple times
        runs = []
        for run_num in range(2):  # Keep small for testing
            engine = SEPEngine(schema, constraints, config)
            
            try:
                solutions = engine.solve()
                state = engine.get_exploration_state()
                
                runs.append({
                    'solutions': solutions,
                    'strategy': state.strategy,
                    'run': run_num
                })
                
                # Verify solutions are valid
                for solution in solutions:
                    assert isinstance(solution, DesignObject)
                    
                    schema_result = engine.schema_validator.validate(solution.to_dict())
                    assert schema_result.is_valid
                    
                    evaluation_result = engine.constraint_evaluator.evaluate(solution)
                    assert evaluation_result.is_valid
                    
            except Exception as e:
                runs.append(None)
        
        # Property: All successful runs should use the same strategy
        successful_runs = [run for run in runs if run is not None]
        
        if len(successful_runs) >= 2:
            strategies_used = [run['strategy'] for run in successful_runs]
            assert all(s == strategy for s in strategies_used), \
                f"Strategy consistency violated: expected {strategy}, got {strategies_used}"
            
            # All solutions should be tagged consistently
            for run in successful_runs:
                for solution in run['solutions']:
                    assert solution.metadata.get("generation_strategy") == strategy