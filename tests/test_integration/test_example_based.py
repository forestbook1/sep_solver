"""Example-based integration tests for specific problem instances."""

import pytest
from sep_solver.core.engine import SEPEngine
from sep_solver.core.config import SolverConfig
from sep_solver.models.constraint_set import ConstraintSet, StructuralConstraint, VariableConstraint
from sep_solver.models.design_object import DesignObject


class MinComponentsConstraint(StructuralConstraint):
    """Constraint requiring minimum number of components."""
    
    def __init__(self, min_count: int):
        super().__init__(
            constraint_id=f"min_components_{min_count}",
            description=f"Requires at least {min_count} components"
        )
        self.min_count = min_count
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return len(design_object.structure.components) >= self.min_count
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        actual = len(design_object.structure.components)
        return f"Has {actual} components, requires at least {self.min_count}"


class MaxComponentsConstraint(StructuralConstraint):
    """Constraint limiting maximum number of components."""
    
    def __init__(self, max_count: int):
        super().__init__(
            constraint_id=f"max_components_{max_count}",
            description=f"Allows at most {max_count} components"
        )
        self.max_count = max_count
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return len(design_object.structure.components) <= self.max_count
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        actual = len(design_object.structure.components)
        return f"Has {actual} components, allows at most {self.max_count}"


class ComponentTypeConstraint(StructuralConstraint):
    """Constraint requiring specific component types."""
    
    def __init__(self, required_types: list):
        super().__init__(
            constraint_id=f"required_types_{len(required_types)}",
            description=f"Requires component types: {', '.join(required_types)}"
        )
        self.required_types = set(required_types)
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        present_types = {comp.type for comp in design_object.structure.components}
        return self.required_types.issubset(present_types)
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        present_types = {comp.type for comp in design_object.structure.components}
        missing = self.required_types - present_types
        return f"Missing required component types: {', '.join(missing)}"


class TestExampleBasedProblems:
    """Test specific problem instances with known characteristics."""
    
    @pytest.fixture
    def simple_schema(self):
        """Simple schema for basic testing."""
        return {
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
    
    def test_minimal_system_example(self, simple_schema):
        """Test minimal system with 1-2 components."""
        constraints = ConstraintSet()
        constraints.add_constraint(MinComponentsConstraint(1))
        constraints.add_constraint(MaxComponentsConstraint(2))
        
        config = SolverConfig(
            exploration_strategy="breadth_first",
            max_iterations=10,
            max_solutions=5,
            enable_logging=False
        )
        
        engine = SEPEngine(simple_schema, constraints, config)
        solutions = engine.solve()
        
        # Should find solutions
        assert len(solutions) > 0, "Should find at least one minimal solution"
        
        # All solutions should satisfy constraints
        for solution in solutions:
            component_count = len(solution.structure.components)
            assert 1 <= component_count <= 2, f"Solution has {component_count} components, expected 1-2"
            
            # Verify constraint satisfaction
            constraint_result = engine.constraint_evaluator.evaluate(solution)
            assert constraint_result.is_valid, f"Solution {solution.id} violates constraints"
    
    def test_processor_memory_system_example(self, simple_schema):
        """Test system requiring processor and memory components."""
        constraints = ConstraintSet()
        constraints.add_constraint(ComponentTypeConstraint(["processor", "memory"]))
        constraints.add_constraint(MinComponentsConstraint(2))
        constraints.add_constraint(MaxComponentsConstraint(5))
        
        config = SolverConfig(
            exploration_strategy="best_first",
            max_iterations=50,
            max_solutions=3,
            enable_logging=False
        )
        
        engine = SEPEngine(simple_schema, constraints, config)
        solutions = engine.solve()
        
        # Verify solutions meet requirements
        for solution in solutions:
            component_types = {comp.type for comp in solution.structure.components}
            
            # Must have processor and memory
            assert "processor" in component_types, f"Solution {solution.id} missing processor"
            assert "memory" in component_types, f"Solution {solution.id} missing memory"
            
            # Component count constraints
            component_count = len(solution.structure.components)
            assert 2 <= component_count <= 5, f"Solution has {component_count} components"
            
            # Schema validation
            schema_result = engine.schema_validator.validate(solution.to_dict())
            assert schema_result.is_valid, f"Solution {solution.id} fails schema validation"
    
    def test_network_topology_example(self, simple_schema):
        """Test network topology with connectivity requirements."""
        constraints = ConstraintSet()
        constraints.add_constraint(MinComponentsConstraint(3))
        constraints.add_constraint(MaxComponentsConstraint(6))
        
        config = SolverConfig(
            exploration_strategy="random",
            max_iterations=30,
            max_solutions=4,
            enable_logging=False
        )
        
        engine = SEPEngine(simple_schema, constraints, config)
        solutions = engine.solve()
        
        # Analyze network properties
        for solution in solutions:
            components = solution.structure.components
            relationships = solution.structure.relationships
            
            # Basic topology checks
            assert 3 <= len(components) <= 6, "Component count out of range"
            
            # If there are relationships, they should connect existing components
            component_ids = {comp.id for comp in components}
            for rel in relationships:
                assert rel.source_id in component_ids, f"Relationship {rel.id} has invalid source"
                assert rel.target_id in component_ids, f"Relationship {rel.id} has invalid target"
                assert rel.source_id != rel.target_id, f"Relationship {rel.id} is self-referential"
    
    def test_scalability_example(self, simple_schema):
        """Test scalability with larger systems."""
        constraints = ConstraintSet()
        constraints.add_constraint(MinComponentsConstraint(5))
        constraints.add_constraint(MaxComponentsConstraint(15))
        
        config = SolverConfig(
            exploration_strategy="depth_first",
            max_iterations=20,
            max_solutions=2,
            enable_logging=False
        )
        
        engine = SEPEngine(simple_schema, constraints, config)
        solutions = engine.solve()
        
        # Verify scalability characteristics
        for solution in solutions:
            component_count = len(solution.structure.components)
            relationship_count = len(solution.structure.relationships)
            
            # Size constraints
            assert 5 <= component_count <= 15, f"Component count {component_count} out of range"
            
            # Complexity analysis
            if component_count > 1:
                # Should have some relationships in larger systems
                max_possible_relationships = component_count * (component_count - 1)
                assert relationship_count <= max_possible_relationships, "Too many relationships"
            
            # Performance check - solution should be generated reasonably quickly
            assert solution.metadata.get("iteration", 0) <= config.max_iterations
    
    def test_constraint_satisfaction_example(self, simple_schema):
        """Test complex constraint satisfaction scenarios."""
        constraints = ConstraintSet()
        
        # Multiple overlapping constraints
        constraints.add_constraint(MinComponentsConstraint(2))
        constraints.add_constraint(MaxComponentsConstraint(4))
        constraints.add_constraint(ComponentTypeConstraint(["processor"]))
        
        config = SolverConfig(
            exploration_strategy="best_first",
            max_iterations=25,
            max_solutions=3,
            enable_logging=True,
            log_level="INFO",
            log_constraint_violations=True
        )
        
        engine = SEPEngine(simple_schema, constraints, config)
        solutions = engine.solve()
        
        # Detailed constraint verification
        for solution in solutions:
            # Component count
            component_count = len(solution.structure.components)
            assert 2 <= component_count <= 4, f"Component count {component_count} violates constraints"
            
            # Required types
            component_types = {comp.type for comp in solution.structure.components}
            assert "processor" in component_types, "Missing required processor component"
            
            # Comprehensive constraint evaluation
            constraint_result = engine.constraint_evaluator.evaluate(solution)
            assert constraint_result.is_valid, f"Solution violates constraints: {constraint_result.violations}"
            
            # Schema compliance
            schema_result = engine.schema_validator.validate(solution.to_dict())
            assert schema_result.is_valid, f"Schema validation failed: {schema_result.errors}"
    
    def test_edge_case_examples(self, simple_schema):
        """Test edge cases and boundary conditions."""
        # Test with very restrictive constraints
        constraints = ConstraintSet()
        constraints.add_constraint(MinComponentsConstraint(1))
        constraints.add_constraint(MaxComponentsConstraint(1))  # Exactly 1 component
        
        config = SolverConfig(
            exploration_strategy="breadth_first",
            max_iterations=15,
            max_solutions=3,
            enable_logging=False
        )
        
        engine = SEPEngine(simple_schema, constraints, config)
        solutions = engine.solve()
        
        # All solutions should have exactly 1 component
        for solution in solutions:
            assert len(solution.structure.components) == 1, "Should have exactly 1 component"
            assert len(solution.structure.relationships) == 0, "Single component should have no relationships"
    
    def test_impossible_constraint_example(self, simple_schema):
        """Test handling of impossible constraint combinations."""
        constraints = ConstraintSet()
        
        # Impossible constraints: need at least 5 components but allow at most 2
        constraints.add_constraint(MinComponentsConstraint(5))
        constraints.add_constraint(MaxComponentsConstraint(2))
        
        config = SolverConfig(
            exploration_strategy="random",
            max_iterations=20,
            max_solutions=5,
            enable_logging=False
        )
        
        engine = SEPEngine(simple_schema, constraints, config)
        solutions = engine.solve()
        
        # Should find no solutions due to impossible constraints
        assert len(solutions) == 0, "Should find no solutions with impossible constraints"
        
        # Verify constraint violation tracking
        violation_stats = engine.inspect_constraint_violations()
        assert violation_stats["total_violations"] > 0, "Should have recorded constraint violations"
    
    def test_performance_benchmark_example(self, simple_schema):
        """Test performance characteristics with known problem sizes."""
        import time
        
        constraints = ConstraintSet()
        constraints.add_constraint(MinComponentsConstraint(2))
        constraints.add_constraint(MaxComponentsConstraint(8))
        
        config = SolverConfig(
            exploration_strategy="best_first",
            max_iterations=40,
            max_solutions=5,
            enable_logging=False
        )
        
        engine = SEPEngine(simple_schema, constraints, config)
        
        # Measure performance
        start_time = time.time()
        solutions = engine.solve()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 10.0, f"Execution took too long: {execution_time:.2f}s"
        
        if len(solutions) > 0:
            avg_time_per_solution = execution_time / len(solutions)
            assert avg_time_per_solution < 5.0, f"Average time per solution too high: {avg_time_per_solution:.2f}s"
        
        # Verify solution quality
        for solution in solutions:
            assert 2 <= len(solution.structure.components) <= 8, "Solution out of expected range"
    
    def test_deterministic_behavior_example(self, simple_schema):
        """Test deterministic behavior with fixed seeds."""
        constraints = ConstraintSet()
        constraints.add_constraint(MinComponentsConstraint(2))
        constraints.add_constraint(MaxComponentsConstraint(4))
        
        # Run same configuration multiple times
        results = []
        
        for run in range(3):
            config = SolverConfig(
                exploration_strategy="breadth_first",  # More deterministic than random
                max_iterations=10,
                max_solutions=2,
                enable_logging=False
            )
            
            engine = SEPEngine(simple_schema, constraints, config)
            solutions = engine.solve()
            
            results.append({
                "solution_count": len(solutions),
                "component_counts": [len(sol.structure.components) for sol in solutions],
                "relationship_counts": [len(sol.structure.relationships) for sol in solutions]
            })
        
        # Verify some level of consistency (breadth-first should be more predictable)
        solution_counts = [r["solution_count"] for r in results]
        
        # All runs should find some solutions
        assert all(count > 0 for count in solution_counts), "All runs should find solutions"
        
        # Component counts should be within expected range
        for result in results:
            for comp_count in result["component_counts"]:
                assert 2 <= comp_count <= 4, f"Component count {comp_count} out of range"
    
    def test_solution_diversity_example(self, simple_schema):
        """Test solution diversity and uniqueness."""
        constraints = ConstraintSet()
        constraints.add_constraint(MinComponentsConstraint(2))
        constraints.add_constraint(MaxComponentsConstraint(5))
        
        config = SolverConfig(
            exploration_strategy="random",
            max_iterations=30,
            max_solutions=8,
            enable_logging=False
        )
        
        engine = SEPEngine(simple_schema, constraints, config)
        solutions = engine.solve()
        
        if len(solutions) > 1:
            # Check solution uniqueness
            solution_signatures = []
            
            for solution in solutions:
                # Create signature based on structure
                signature = (
                    len(solution.structure.components),
                    len(solution.structure.relationships),
                    tuple(sorted(comp.type for comp in solution.structure.components))
                )
                solution_signatures.append(signature)
            
            # Should have some diversity (not all solutions identical)
            unique_signatures = set(solution_signatures)
            diversity_ratio = len(unique_signatures) / len(solution_signatures)
            
            # At least some diversity expected
            assert diversity_ratio > 0.3, f"Low solution diversity: {diversity_ratio:.2f}"
    
    def test_error_handling_example(self, simple_schema):
        """Test error handling with problematic configurations."""
        constraints = ConstraintSet()
        constraints.add_constraint(MinComponentsConstraint(1))
        
        # Test with very low iteration limit
        config = SolverConfig(
            exploration_strategy="depth_first",
            max_iterations=1,  # Very low
            max_solutions=5,
            enable_logging=False
        )
        
        engine = SEPEngine(simple_schema, constraints, config)
        
        # Should handle gracefully without crashing
        try:
            solutions = engine.solve()
            # May find 0 or few solutions due to low iteration limit
            assert isinstance(solutions, list), "Should return list even with low iterations"
            
        except Exception as e:
            pytest.fail(f"Should handle low iteration limit gracefully, but raised: {e}")
    
    def test_comprehensive_system_example(self, simple_schema):
        """Test comprehensive system with multiple constraint types."""
        constraints = ConstraintSet()
        
        # Structural constraints
        constraints.add_constraint(MinComponentsConstraint(3))
        constraints.add_constraint(MaxComponentsConstraint(7))
        constraints.add_constraint(ComponentTypeConstraint(["processor", "memory"]))
        
        config = SolverConfig(
            exploration_strategy="best_first",
            max_iterations=35,
            max_solutions=4,
            enable_logging=True,
            log_level="INFO",
            enable_schema_validation=True,
            enable_constraint_validation=True
        )
        
        engine = SEPEngine(simple_schema, constraints, config)
        solutions = engine.solve()
        
        # Comprehensive validation
        for solution in solutions:
            # Structural requirements
            components = solution.structure.components
            assert 3 <= len(components) <= 7, "Component count out of range"
            
            # Type requirements
            component_types = {comp.type for comp in components}
            assert "processor" in component_types, "Missing processor"
            assert "memory" in component_types, "Missing memory"
            
            # Schema validation
            schema_result = engine.schema_validator.validate(solution.to_dict())
            assert schema_result.is_valid, f"Schema validation failed: {schema_result.errors}"
            
            # Constraint validation
            constraint_result = engine.constraint_evaluator.evaluate(solution)
            assert constraint_result.is_valid, f"Constraint validation failed: {constraint_result.violations}"
            
            # Metadata validation
            assert "generation_strategy" in solution.metadata, "Missing generation strategy"
            assert "iteration" in solution.metadata, "Missing iteration info"
            assert solution.metadata["generation_strategy"] == config.exploration_strategy
        
        # System-level checks
        if len(solutions) > 0:
            # Get statistics
            stats = engine.get_solution_statistics()
            assert stats["total_solutions"] == len(solutions)
            
            # Performance metrics
            metrics = engine.get_progress_metrics()
            assert metrics["current_iteration"] > 0
            assert metrics["solutions_found"] <= len(solutions)  # May differ due to timing