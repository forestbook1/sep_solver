"""Main SEP Engine that orchestrates the solving process."""

from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING, Callable
import logging
import time
from .config import SolverConfig
from .exceptions import SEPSolverError, ConfigurationError
from ..utils.logging import setup_logger

if TYPE_CHECKING:
    from .interfaces import StructureGenerator, VariableAssigner, ConstraintEvaluator, SchemaValidator
    from ..models.design_object import DesignObject
    from ..models.constraint_set import ConstraintSet
    from ..models.exploration_state import ExplorationState


class SEPEngine:
    """Central orchestrator that coordinates all solver components.
    
    The SEP Engine manages the exploration process by coordinating between
    structure generation, variable assignment, and constraint evaluation components.
    """
    
    def __init__(self, 
                 schema: Dict[str, Any], 
                 constraints: 'ConstraintSet', 
                 config: SolverConfig,
                 structure_generator: Optional['StructureGenerator'] = None,
                 variable_assigner: Optional['VariableAssigner'] = None,
                 constraint_evaluator: Optional['ConstraintEvaluator'] = None,
                 schema_validator: Optional['SchemaValidator'] = None):
        """Initialize the SEP engine with schema, constraints, and configuration.
        
        Args:
            schema: JSON schema for design objects
            constraints: Set of constraints that must be satisfied
            config: Solver configuration
            structure_generator: Optional custom structure generator
            variable_assigner: Optional custom variable assigner
            constraint_evaluator: Optional custom constraint evaluator
            schema_validator: Optional custom schema validator
            
        Raises:
            ConfigurationError: If configuration is invalid
            SEPSolverError: If initialization fails
        """
        from ..models.exploration_state import ExplorationState
        
        self.schema = schema
        self.constraints = constraints
        self.config = config
        
        # Validate configuration
        self.config.validate()
        
        # Set up logging
        self.logger = setup_logger("SEPEngine", config.log_level) if config.enable_logging else None
        
        # Set up debug logging (temporarily disabled to avoid import issues)
        self.debug_logger = None
        
        # Initialize components (will be implemented in later tasks)
        self.structure_generator = structure_generator
        self.variable_assigner = variable_assigner
        self.constraint_evaluator = constraint_evaluator
        self.schema_validator = schema_validator
        
        # Initialize default components if not provided
        self._initialize_default_components()
        
        # Initialize exploration state
        self.exploration_state = ExplorationState()
        
        # Initialize progress tracking
        from ..utils.progress import ProgressTracker
        self.progress_tracker = ProgressTracker()
        
        if self.logger:
            self.logger.info(f"SEP Engine initialized with strategy: {config.exploration_strategy}")
        
        # Log initialization
        self._log_debug("log_exploration_start",
            strategy=config.exploration_strategy,
            config={
                "max_iterations": config.max_iterations,
                "max_solutions": config.max_solutions,
                "enable_schema_validation": config.enable_schema_validation,
                "enable_constraint_validation": config.enable_constraint_validation,
                "variable_assignment_strategy": config.variable_assignment_strategy
            }
        )
    
    def _log_debug(self, method_name: str, *args, **kwargs):
        """Helper method to safely call debug logger methods."""
        if self.debug_logger and hasattr(self.debug_logger, method_name):
            method = getattr(self.debug_logger, method_name)
            method(*args, **kwargs)
    
    def solve(self, exploration_strategy: Optional[str] = None) -> List['DesignObject']:
        """Main solving method that returns valid solutions.
        
        Args:
            exploration_strategy: Optional override for exploration strategy
            
        Returns:
            List of valid DesignObject solutions
            
        Raises:
            SEPSolverError: If solving fails
        """
        strategy = exploration_strategy or self.config.exploration_strategy
        start_time = time.time()
        
        if self.logger:
            self.logger.info(f"Starting exploration with strategy: {strategy}")
        
        # Log exploration start
        if self.debug_logger:
            self._log_debug("log_exploration_start",
                strategy=strategy,
                config={
                    "max_iterations": self.config.max_iterations,
                    "max_solutions": self.config.max_solutions,
                    "enable_schema_validation": self.config.enable_schema_validation,
                    "enable_constraint_validation": self.config.enable_constraint_validation
                }
            )
        
        # Validate that all required components are available
        self._validate_components()
        
        # Initialize exploration state
        self.exploration_state.start_exploration(strategy)
        
        # Start progress tracking
        self.progress_tracker.start_exploration(
            total_iterations=self.config.max_iterations,
            target_solutions=self.config.max_solutions
        )
        
        solutions = []
        max_iterations = self.config.max_iterations
        max_solutions = self.config.max_solutions
        
        try:
            # Use strategy-specific solving method
            solutions = self.solve_with_strategy(strategy)
            
            total_time = time.time() - start_time
            
            if self.logger:
                self.logger.info(f"Exploration completed. Found {len(solutions)} solutions in {self.exploration_state.iteration_count} iterations.")
            
            # Log exploration completion
            self._log_debug("log_exploration_complete",
                total_steps=self.exploration_state.iteration_count,
                solutions_found=len(solutions),
                total_time=total_time
            )
            
            # Log performance metrics
            self._log_debug("log_performance_metric",
                component="SEPEngine",
                metric_name="total_exploration_time",
                value=total_time,
                unit="seconds"
            )
            
            self._log_debug("log_performance_metric",
                component="SEPEngine", 
                metric_name="solutions_per_second",
                value=len(solutions) / max(total_time, 0.001),
                unit="solutions/sec"
            )
            
            # Complete progress tracking
            self.progress_tracker.complete_exploration(success=True)
            
            return solutions
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Exploration failed: {str(e)}")
            
            # Log error
            self._log_debug("log_error",
                component="SEPEngine",
                error=e,
                context={
                    "strategy": strategy,
                    "iteration_count": self.exploration_state.iteration_count,
                    "solutions_found": len(solutions)
                }
            )
            
            # Complete progress tracking with failure
            self.progress_tracker.complete_exploration(success=False)
            
            raise SEPSolverError(f"Solving failed: {str(e)}")
    
    def _validate_components(self) -> None:
        """Validate that all required components are available.
        
        Raises:
            ConfigurationError: If required components are missing
        """
        from .exceptions import ConfigurationError
        
        required_components = [
            ("structure_generator", self.structure_generator),
            ("variable_assigner", self.variable_assigner),
            ("constraint_evaluator", self.constraint_evaluator),
            ("schema_validator", self.schema_validator)
        ]
        
        missing_components = []
        for name, component in required_components:
            if component is None:
                missing_components.append(name)
        
        if missing_components:
            raise ConfigurationError(f"Missing required components: {', '.join(missing_components)}")
    
    def _should_continue_exploration(self, solutions: List['DesignObject'], iteration: int) -> bool:
        """Determine if exploration should continue.
        
        Args:
            solutions: Current solutions found
            iteration: Current iteration number
            
        Returns:
            True if exploration should continue
        """
        # Stop if we've reached the maximum number of solutions
        if len(solutions) >= self.config.max_solutions:
            return False
        
        # Stop if we've reached the maximum number of iterations
        if iteration >= self.config.max_iterations - 1:
            return False
        
        # Strategy-specific stopping conditions could be added here
        return True
    
    def solve_with_strategy(self, strategy: str, **strategy_params) -> List['DesignObject']:
        """Solve using a specific exploration strategy with parameters.
        
        Args:
            strategy: Exploration strategy ("breadth_first", "depth_first", "best_first", "random")
            **strategy_params: Strategy-specific parameters
            
        Returns:
            List of valid DesignObject solutions
            
        Raises:
            SEPSolverError: If solving fails
        """
        if strategy == "breadth_first":
            return self._solve_breadth_first(**strategy_params)
        elif strategy == "depth_first":
            return self._solve_depth_first(**strategy_params)
        elif strategy == "best_first":
            return self._solve_best_first(**strategy_params)
        elif strategy == "random":
            return self._solve_random(**strategy_params)
        else:
            raise SEPSolverError(f"Unknown exploration strategy: {strategy}")
    
    def _solve_breadth_first(self, **params) -> List['DesignObject']:
        """Solve using breadth-first exploration strategy.
        
        Explores all candidates at the current level before moving to the next level.
        Maintains a queue of candidates to explore systematically.
        
        Returns:
            List of valid solutions found
        """
        from collections import deque
        
        if self.logger:
            self.logger.info("Starting breadth-first exploration")
        
        self._validate_components()
        self.exploration_state.start_exploration("breadth_first")
        
        solutions = []
        candidate_queue = deque()
        
        # Initialize with a base structure
        try:
            initial_candidate, is_valid = self.explore_step()
            if is_valid:
                solutions.append(initial_candidate)
            else:
                # Generate variants of the initial candidate for the queue
                variants = self.structure_generator.get_structure_variants(initial_candidate.structure)
                for variant in variants[:5]:  # Limit initial variants
                    candidate_queue.append(variant)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to generate initial candidate: {e}")
        
        max_iterations = self.config.max_iterations
        max_solutions = self.config.max_solutions
        
        for iteration in range(max_iterations):
            if len(solutions) >= max_solutions:
                break
            
            if not candidate_queue:
                # Generate new candidates if queue is empty
                try:
                    candidate, is_valid = self.explore_step()
                    if is_valid:
                        solutions.append(candidate)
                    else:
                        # Add variants to queue for further exploration
                        variants = self.structure_generator.get_structure_variants(candidate.structure)
                        candidate_queue.extend(variants[:3])  # Limit variants per candidate
                except Exception as e:
                    if self.logger:
                        self.logger.debug(f"Failed to generate candidate in iteration {iteration}: {e}")
                    
                    # Extract and record constraint violations from exception messages
                    error_msg = str(e)
                    if "Constraint violation:" in error_msg:
                        # Extract the violation message
                        violation_msg = error_msg.split("Constraint violation: ", 1)[1]
                        
                        # Try to determine constraint ID from the message
                        constraint_id = "unknown_constraint"
                        if "components, requires at least" in violation_msg:
                            constraint_id = "min_components_constraint"
                        elif "components, allows at most" in violation_msg:
                            constraint_id = "max_components_constraint"
                        
                        # Record the violation
                        self.exploration_state.record_constraint_violation(constraint_id, violation_msg)
                    
                    continue
            else:
                # Process next candidate from queue
                structure = candidate_queue.popleft()
                try:
                    # Create design object from structure
                    variable_assignment = self.variable_assigner.assign_variables(structure)
                    candidate = self._create_design_object(structure, variable_assignment, iteration)
                    
                    # Validate candidate
                    is_valid = self._validate_candidate(candidate)
                    
                    if is_valid:
                        solutions.append(candidate)
                        if self.logger:
                            self.logger.info(f"Found valid solution {len(solutions)}: {candidate.id}")
                    else:
                        # Add more variants to queue if this one failed
                        variants = self.structure_generator.get_structure_variants(structure)
                        candidate_queue.extend(variants[:2])
                        
                except Exception as e:
                    if self.logger:
                        self.logger.debug(f"Failed to process queued candidate: {e}")
                    
                    # Extract and record constraint violations from exception messages
                    error_msg = str(e)
                    if "Constraint violation:" in error_msg:
                        # Extract the violation message
                        violation_msg = error_msg.split("Constraint violation: ", 1)[1]
                        
                        # Try to determine constraint ID from the message
                        constraint_id = "unknown_constraint"
                        if "components, requires at least" in violation_msg:
                            constraint_id = "min_components_constraint"
                        elif "components, allows at most" in violation_msg:
                            constraint_id = "max_components_constraint"
                        
                        # Record the violation
                        self.exploration_state.record_constraint_violation(constraint_id, violation_msg)
        
        if self.logger:
            self.logger.info(f"Breadth-first exploration completed. Found {len(solutions)} solutions.")
        
        return solutions
    
    def _solve_depth_first(self, **params) -> List['DesignObject']:
        """Solve using depth-first exploration strategy.
        
        Explores each candidate deeply by generating and exploring its variants
        before moving to the next candidate.
        
        Returns:
            List of valid solutions found
        """
        if self.logger:
            self.logger.info("Starting depth-first exploration")
        
        self._validate_components()
        self.exploration_state.start_exploration("depth_first")
        
        solutions = []
        max_iterations = self.config.max_iterations
        max_solutions = self.config.max_solutions
        max_depth = params.get('max_depth', 5)
        
        def explore_recursive(structure, depth=0):
            """Recursively explore a structure and its variants."""
            if depth >= max_depth or len(solutions) >= max_solutions:
                return
            
            try:
                # Create candidate from structure
                variable_assignment = self.variable_assigner.assign_variables(structure)
                candidate = self._create_design_object(structure, variable_assignment, 
                                                    self.exploration_state.iteration_count)
                
                # Validate candidate
                is_valid = self._validate_candidate(candidate)
                
                if is_valid:
                    solutions.append(candidate)
                    if self.logger:
                        self.logger.info(f"Found valid solution {len(solutions)}: {candidate.id}")
                
                # Explore variants recursively
                if len(solutions) < max_solutions:
                    variants = self.structure_generator.get_structure_variants(structure)
                    for variant in variants[:2]:  # Limit variants per level
                        if len(solutions) >= max_solutions:
                            break
                        explore_recursive(variant, depth + 1)
                        
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Failed to explore structure at depth {depth}: {e}")
        
        # Start with initial candidates
        for iteration in range(min(max_iterations // max_depth, 10)):  # Limit initial candidates
            if len(solutions) >= max_solutions:
                break
            
            try:
                initial_candidate, is_valid = self.explore_step()
                if is_valid:
                    solutions.append(initial_candidate)
                
                # Explore this candidate's variants deeply
                explore_recursive(initial_candidate.structure)
                
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Failed to generate initial candidate {iteration}: {e}")
                
                # Extract and record constraint violations from exception messages
                error_msg = str(e)
                if "Constraint violation:" in error_msg:
                    # Extract the violation message
                    violation_msg = error_msg.split("Constraint violation: ", 1)[1]
                    
                    # Try to determine constraint ID from the message
                    constraint_id = "unknown_constraint"
                    if "components, requires at least" in violation_msg:
                        constraint_id = "min_components_constraint"
                    elif "components, allows at most" in violation_msg:
                        constraint_id = "max_components_constraint"
                    
                    # Record the violation
                    self.exploration_state.record_constraint_violation(constraint_id, violation_msg)
        
        if self.logger:
            self.logger.info(f"Depth-first exploration completed. Found {len(solutions)} solutions.")
        
        return solutions
    
    def _solve_best_first(self, **params) -> List['DesignObject']:
        """Solve using best-first exploration strategy.
        
        Prioritizes candidates based on a scoring function and explores
        the most promising candidates first.
        
        Returns:
            List of valid solutions found
        """
        import heapq
        
        if self.logger:
            self.logger.info("Starting best-first exploration")
        
        self._validate_components()
        self.exploration_state.start_exploration("best_first")
        
        solutions = []
        # Priority queue: (negative_score, iteration, structure)
        candidate_heap = []
        max_iterations = self.config.max_iterations
        max_solutions = self.config.max_solutions
        
        # Generate initial candidates
        for i in range(min(5, max_iterations // 10)):  # Initial candidate pool
            try:
                candidate, is_valid = self.explore_step()
                if is_valid:
                    solutions.append(candidate)
                
                # Score the candidate and add to heap
                score = self._score_candidate(candidate)
                heapq.heappush(candidate_heap, (-score, i, candidate.structure))
                
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Failed to generate initial candidate {i}: {e}")
                
                # Extract and record constraint violations from exception messages
                error_msg = str(e)
                if "Constraint violation:" in error_msg:
                    # Extract the violation message
                    violation_msg = error_msg.split("Constraint violation: ", 1)[1]
                    
                    # Try to determine constraint ID from the message
                    constraint_id = "unknown_constraint"
                    if "components, requires at least" in violation_msg:
                        constraint_id = "min_components_constraint"
                    elif "components, allows at most" in violation_msg:
                        constraint_id = "max_components_constraint"
                    
                    # Record the violation
                    self.exploration_state.record_constraint_violation(constraint_id, violation_msg)
        
        # Explore candidates in order of score
        iteration = len(candidate_heap)
        while candidate_heap and len(solutions) < max_solutions and iteration < max_iterations:
            try:
                neg_score, _, structure = heapq.heappop(candidate_heap)
                
                # Generate variants of the best candidate
                variants = self.structure_generator.get_structure_variants(structure)
                
                for variant in variants:
                    if len(solutions) >= max_solutions:
                        break
                    
                    # Create and validate variant
                    variable_assignment = self.variable_assigner.assign_variables(variant)
                    candidate = self._create_design_object(variant, variable_assignment, iteration)
                    
                    is_valid = self._validate_candidate(candidate)
                    
                    if is_valid:
                        solutions.append(candidate)
                        if self.logger:
                            self.logger.info(f"Found valid solution {len(solutions)}: {candidate.id}")
                    
                    # Add variant back to heap with its score
                    score = self._score_candidate(candidate)
                    heapq.heappush(candidate_heap, (-score, iteration, variant))
                    iteration += 1
                    
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Failed to process best candidate: {e}")
                
                # Extract and record constraint violations from exception messages
                error_msg = str(e)
                if "Constraint violation:" in error_msg:
                    # Extract the violation message
                    violation_msg = error_msg.split("Constraint violation: ", 1)[1]
                    
                    # Try to determine constraint ID from the message
                    constraint_id = "unknown_constraint"
                    if "components, requires at least" in violation_msg:
                        constraint_id = "min_components_constraint"
                    elif "components, allows at most" in violation_msg:
                        constraint_id = "max_components_constraint"
                    
                    # Record the violation
                    self.exploration_state.record_constraint_violation(constraint_id, violation_msg)
                
                iteration += 1
        
        if self.logger:
            self.logger.info(f"Best-first exploration completed. Found {len(solutions)} solutions.")
        
        return solutions
    
    def _solve_random(self, **params) -> List['DesignObject']:
        """Solve using random exploration strategy.
        
        Generates completely random candidates without any systematic exploration.
        This is the simplest strategy and serves as a baseline.
        
        Returns:
            List of valid solutions found
        """
        if self.logger:
            self.logger.info("Starting random exploration")
        
        self._validate_components()
        self.exploration_state.start_exploration("random")
        
        solutions = []
        max_iterations = self.config.max_iterations
        max_solutions = self.config.max_solutions
        
        for iteration in range(max_iterations):
            if len(solutions) >= max_solutions:
                break
            
            try:
                candidate, is_valid = self.explore_step()
                
                if is_valid:
                    solutions.append(candidate)
                    if self.logger:
                        self.logger.info(f"Found valid solution {len(solutions)}: {candidate.id}")
                        
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Failed to generate random candidate {iteration}: {e}")
                
                # Extract and record constraint violations from exception messages
                error_msg = str(e)
                if "Constraint violation:" in error_msg:
                    # Extract the violation message
                    violation_msg = error_msg.split("Constraint violation: ", 1)[1]
                    
                    # Try to determine constraint ID from the message
                    constraint_id = "unknown_constraint"
                    if "components, requires at least" in violation_msg:
                        constraint_id = "min_components_constraint"
                    elif "components, allows at most" in violation_msg:
                        constraint_id = "max_components_constraint"
                    
                    # Record the violation
                    self.exploration_state.record_constraint_violation(constraint_id, violation_msg)
        
        if self.logger:
            self.logger.info(f"Random exploration completed. Found {len(solutions)} solutions.")
        
        return solutions
    
    def _create_design_object(self, structure, variable_assignment, iteration: int) -> 'DesignObject':
        """Create a design object from structure and variable assignment.
        
        Args:
            structure: The structure
            variable_assignment: The variable assignment
            iteration: Current iteration number
            
        Returns:
            DesignObject instance
        """
        import time
        from ..models.design_object import DesignObject
        
        return DesignObject(
            id=f"candidate_{iteration}_{int(time.time() * 1000) % 10000}",
            structure=structure,
            variables=variable_assignment,
            metadata={
                "generation_strategy": self.exploration_state.strategy,
                "iteration": iteration,
                "timestamp": time.time()
            }
        )
    
    def _validate_candidate(self, candidate: 'DesignObject') -> bool:
        """Validate a candidate design object.
        
        Args:
            candidate: The candidate to validate
            
        Returns:
            True if candidate is valid
        """
        import time
        
        start_time = time.time()
        
        try:
            # Schema validation
            if self.config.enable_schema_validation:
                schema_result = self.schema_validator.validate(candidate.to_dict())
                if not schema_result.is_valid:
                    for error in schema_result.errors:
                        self.exploration_state.record_constraint_violation(
                            "schema_validation", 
                            f"Schema error at {error.path}: {error.message}"
                        )
                    
                    evaluation_time = time.time() - start_time
                    self.exploration_state.record_candidate_evaluation(candidate, False, evaluation_time)
                    return False
            
            # Constraint validation
            if self.config.enable_constraint_validation:
                evaluation_result = self.constraint_evaluator.evaluate(candidate)
                is_valid = evaluation_result.is_valid
                
                if not is_valid:
                    for violation in evaluation_result.violations:
                        self.exploration_state.record_constraint_violation(
                            violation.constraint_id,
                            violation.message
                        )
                
                evaluation_time = time.time() - start_time
                self.exploration_state.record_candidate_evaluation(candidate, is_valid, evaluation_time)
                return is_valid
            
            # If no validation enabled, consider valid
            evaluation_time = time.time() - start_time
            self.exploration_state.record_candidate_evaluation(candidate, True, evaluation_time)
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Validation failed for candidate {candidate.id}: {e}")
            
            evaluation_time = time.time() - start_time
            self.exploration_state.record_candidate_evaluation(candidate, False, evaluation_time)
            return False
    
    def _score_candidate(self, candidate: 'DesignObject') -> float:
        """Score a candidate for best-first exploration.
        
        Args:
            candidate: The candidate to score
            
        Returns:
            Score (higher is better)
        """
        score = 0.0
        
        try:
            # Score based on structure complexity (moderate complexity preferred)
            num_components = len(candidate.structure.components)
            num_relationships = len(candidate.structure.relationships)
            
            # Prefer moderate complexity (not too simple, not too complex)
            optimal_components = 3
            optimal_relationships = 2
            
            component_score = 1.0 - abs(num_components - optimal_components) / 10.0
            relationship_score = 1.0 - abs(num_relationships - optimal_relationships) / 10.0
            
            score += component_score + relationship_score
            
            # Score based on variable assignment completeness
            num_variables = len(candidate.variables.assignments)
            if num_variables > 0:
                score += min(num_variables / 10.0, 1.0)  # Bonus for having variables
            
            # Score based on constraint satisfaction (if we can evaluate without errors)
            try:
                evaluation_result = self.constraint_evaluator.evaluate(candidate)
                if evaluation_result.is_valid:
                    score += 5.0  # Big bonus for valid candidates
                else:
                    # Partial score based on how many constraints are satisfied
                    total_constraints = len(self.constraints.get_all_constraints())
                    violations = len(evaluation_result.violations)
                    if total_constraints > 0:
                        satisfaction_ratio = 1.0 - (violations / total_constraints)
                        score += satisfaction_ratio * 2.0
            except Exception:
                # If evaluation fails, don't penalize too much
                pass
            
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Failed to score candidate {candidate.id}: {e}")
            score = 0.0
        
        return max(score, 0.0)  # Ensure non-negative score
    
    def get_solutions(self) -> List['DesignObject']:
        """Get all solutions found during exploration.
        
        Returns:
            List of valid solutions from exploration state
        """
        return self.exploration_state.best_candidates.copy()
    
    def get_best_solutions(self, n: int = 5) -> List['DesignObject']:
        """Get the n best solutions found during exploration.
        
        Args:
            n: Number of best solutions to return
            
        Returns:
            List of best solutions, sorted by score
        """
        solutions = self.get_solutions()
        
        # Score and sort solutions
        scored_solutions = []
        for solution in solutions:
            score = self._score_candidate(solution)
            scored_solutions.append((score, solution))
        
        # Sort by score (descending) and return top n
        scored_solutions.sort(key=lambda x: x[0], reverse=True)
        return [solution for _, solution in scored_solutions[:n]]
    
    def filter_solutions(self, filter_func: callable) -> List['DesignObject']:
        """Filter solutions using a custom function.
        
        Args:
            filter_func: Function that takes a DesignObject and returns bool
            
        Returns:
            List of solutions that pass the filter
        """
        solutions = self.get_solutions()
        return [solution for solution in solutions if filter_func(solution)]
    
    def get_solution_statistics(self) -> Dict[str, Any]:
        """Get statistics about found solutions.
        
        Returns:
            Dictionary with solution statistics
        """
        solutions = self.get_solutions()
        
        if not solutions:
            return {
                "total_solutions": 0,
                "average_components": 0,
                "average_relationships": 0,
                "average_variables": 0,
                "component_range": (0, 0),
                "relationship_range": (0, 0),
                "variable_range": (0, 0)
            }
        
        # Calculate statistics
        component_counts = [len(s.structure.components) for s in solutions]
        relationship_counts = [len(s.structure.relationships) for s in solutions]
        variable_counts = [len(s.variables.assignments) for s in solutions]
        
        return {
            "total_solutions": len(solutions),
            "average_components": sum(component_counts) / len(component_counts),
            "average_relationships": sum(relationship_counts) / len(relationship_counts),
            "average_variables": sum(variable_counts) / len(variable_counts),
            "component_range": (min(component_counts), max(component_counts)),
            "relationship_range": (min(relationship_counts), max(relationship_counts)),
            "variable_range": (min(variable_counts), max(variable_counts))
        }
    
    def export_solutions(self, format: str = "json", filename: Optional[str] = None,
                        include_metadata: bool = True) -> str:
        """Export solutions in the specified format.
        
        Args:
            format: Export format ("json", "xml", "csv", "yaml", "dot", "summary")
            filename: Optional filename to write to
            include_metadata: Whether to include metadata in export
            
        Returns:
            Exported solutions as string (if no filename provided)
            
        Raises:
            SEPSolverError: If export format is unsupported
        """
        from ..utils.visualization import SolutionVisualizer
        
        solutions = self.get_solutions()
        visualizer = SolutionVisualizer()
        
        if filename:
            visualizer.export_solutions(solutions, filename, format, include_metadata)
            if self.logger:
                self.logger.info(f"Exported {len(solutions)} solutions to {filename} in {format} format")
            return f"Exported {len(solutions)} solutions to {filename}"
        else:
            # Return as string for supported formats
            if format == "json":
                import json
                export_data = {
                    "export_info": {
                        "timestamp": time.time(),
                        "solution_count": len(solutions),
                        "format": format
                    },
                    "solutions": [sol.to_dict() for sol in solutions]
                }
                return json.dumps(export_data, indent=2, default=str)
            
            elif format == "summary":
                lines = [f"Found {len(solutions)} solutions:\n"]
                
                for i, solution in enumerate(solutions, 1):
                    lines.append(f"Solution {i}: {solution.id}")
                    lines.append(f"  Components: {len(solution.structure.components)}")
                    lines.append(f"  Relationships: {len(solution.structure.relationships)}")
                    lines.append(f"  Variables: {len(solution.variables.assignments)}")
                    lines.append("")
                
                return "\n".join(lines)
            
            else:
                raise SEPSolverError(f"String export not supported for format: {format}. Use filename parameter.")
    
    def visualize_solutions(self, filename: str, format: str = "dot") -> None:
        """Create visualization of solutions.
        
        Args:
            filename: Output filename
            format: Visualization format ("dot" for Graphviz)
        """
        from ..utils.visualization import SolutionVisualizer
        
        solutions = self.get_solutions()
        visualizer = SolutionVisualizer()
        
        if format == "dot":
            visualizer.export_solutions(solutions, filename, "dot", include_metadata=False)
            if self.logger:
                self.logger.info(f"Created DOT visualization of {len(solutions)} solutions: {filename}")
        else:
            raise SEPSolverError(f"Unsupported visualization format: {format}")
    
    def generate_solution_report(self, filename: str, include_comparison: bool = True) -> None:
        """Generate comprehensive solution report.
        
        Args:
            filename: Output filename
            include_comparison: Whether to include comparison analysis
        """
        from ..utils.visualization import SolutionVisualizer
        
        solutions = self.get_solutions()
        visualizer = SolutionVisualizer()
        visualizer.generate_solution_report(solutions, filename, include_comparison)
        
        if self.logger:
            self.logger.info(f"Generated solution report for {len(solutions)} solutions: {filename}")
    
    def compare_solutions(self) -> Dict[str, Any]:
        """Compare all found solutions.
        
        Returns:
            Dictionary with comparison analysis
        """
        from ..utils.visualization import SolutionVisualizer
        
        solutions = self.get_solutions()
        visualizer = SolutionVisualizer()
        return visualizer.create_solution_comparison(solutions)
    
    def get_solution_summary(self) -> Dict[str, Any]:
        """Get summary of all solutions with basic visualization data.
        
        Returns:
            Dictionary with solution summary and visualization data
        """
        solutions = self.get_solutions()
        
        if not solutions:
            return {
                "total_solutions": 0,
                "message": "No solutions found"
            }
        
        # Basic statistics
        component_counts = [len(s.structure.components) for s in solutions]
        relationship_counts = [len(s.structure.relationships) for s in solutions]
        variable_counts = [len(s.variables.assignments) for s in solutions]
        
        # Component and relationship type analysis
        all_component_types = set()
        all_relationship_types = set()
        component_type_freq = {}
        relationship_type_freq = {}
        
        for solution in solutions:
            for comp in solution.structure.components:
                all_component_types.add(comp.type)
                component_type_freq[comp.type] = component_type_freq.get(comp.type, 0) + 1
            
            for rel in solution.structure.relationships:
                all_relationship_types.add(rel.type)
                relationship_type_freq[rel.type] = relationship_type_freq.get(rel.type, 0) + 1
        
        return {
            "total_solutions": len(solutions),
            "structure_statistics": {
                "components": {
                    "min": min(component_counts),
                    "max": max(component_counts),
                    "average": sum(component_counts) / len(component_counts),
                    "total": sum(component_counts)
                },
                "relationships": {
                    "min": min(relationship_counts),
                    "max": max(relationship_counts),
                    "average": sum(relationship_counts) / len(relationship_counts),
                    "total": sum(relationship_counts)
                },
                "variables": {
                    "min": min(variable_counts),
                    "max": max(variable_counts),
                    "average": sum(variable_counts) / len(variable_counts),
                    "total": sum(variable_counts)
                }
            },
            "type_analysis": {
                "component_types": {
                    "unique_types": len(all_component_types),
                    "types": sorted(list(all_component_types)),
                    "frequency": component_type_freq
                },
                "relationship_types": {
                    "unique_types": len(all_relationship_types),
                    "types": sorted(list(all_relationship_types)),
                    "frequency": relationship_type_freq
                }
            },
            "solution_ids": [s.id for s in solutions],
            "visualization_ready": True
        }
    
    def clear_solutions(self) -> None:
        """Clear all found solutions and reset exploration state."""
        self.exploration_state.best_candidates.clear()
        self.exploration_state.solutions_found = 0
        if self.logger:
            self.logger.info("Cleared all solutions and reset exploration state")
    
    def explore_step(self) -> Tuple['DesignObject', bool]:
        """Execute one exploration step, return candidate and validity.
        
        Returns:
            Tuple of (design_object, is_valid)
            
        Raises:
            SEPSolverError: If exploration step fails
        """
        import time
        from ..models.design_object import DesignObject
        
        start_time = time.time()
        
        try:
            # Record iteration
            self.exploration_state.record_iteration()
            
            # Update progress tracking
            self.progress_tracker.update_iteration(self.exploration_state.iteration_count)
            
            if self.logger:
                self.logger.debug(f"Starting exploration step {self.exploration_state.iteration_count}")
            
            # Step 1: Generate structure
            structure_start_time = time.time()
            structural_constraints = self.constraints.get_constraints_by_type("structural")
            
            # Record decision about structure generation
            self.exploration_state.record_decision(
                decision_type="structure_generation",
                decision_data={
                    "constraints_count": len(structural_constraints),
                    "strategy": self.config.exploration_strategy
                },
                outcome="attempting",
                reasoning=f"Generating structure with {len(structural_constraints)} structural constraints"
            )
            
            structure = self.structure_generator.generate_structure(structural_constraints)
            structure_time = time.time() - structure_start_time
            
            # Record structure generation outcome
            self.exploration_state.record_decision(
                decision_type="structure_generation",
                decision_data={
                    "components_generated": len(structure.components),
                    "relationships_generated": len(structure.relationships),
                    "generation_time": structure_time
                },
                outcome="success",
                reasoning=f"Successfully generated structure with {len(structure.components)} components"
            )
            
            # Record component performance
            self.exploration_state.record_component_performance("StructureGenerator", structure_time)
            
            if self.logger:
                self.logger.debug(f"Generated structure with {len(structure.components)} components")
            
            # Log structure generation
            self._log_debug("log_structure_generation",
                generator_type=self.structure_generator.__class__.__name__,
                structure_id=f"struct_{self.exploration_state.iteration_count}",
                components_count=len(structure.components),
                relationships_count=len(structure.relationships),
                generation_time=structure_time
            )
            
            # Capture intermediate state after structure generation
            self.exploration_state.capture_intermediate_state(
                state_name="post_structure_generation",
                state_data={
                    "structure_id": f"struct_{self.exploration_state.iteration_count}",
                    "components": [{"id": comp.id, "type": comp.type} for comp in structure.components],
                    "relationships": [{"id": rel.id, "type": rel.type} for rel in structure.relationships]
                }
            )
            
            # Step 2: Assign variables
            assignment_start_time = time.time()
            
            # Record decision about variable assignment
            self.exploration_state.record_decision(
                decision_type="variable_assignment",
                decision_data={
                    "structure_id": f"struct_{self.exploration_state.iteration_count}",
                    "strategy": self.config.variable_assignment_strategy,
                    "variables_to_assign": len([comp for comp in structure.components if hasattr(comp, 'variables')])
                },
                outcome="attempting",
                reasoning=f"Assigning variables using {self.config.variable_assignment_strategy} strategy"
            )
            
            variable_assignment = self.variable_assigner.assign_variables(
                structure, 
                strategy=self.config.variable_assignment_strategy
            )
            assignment_time = time.time() - assignment_start_time
            
            # Record variable assignment outcome
            self.exploration_state.record_decision(
                decision_type="variable_assignment",
                decision_data={
                    "variables_assigned": len(variable_assignment.assignments),
                    "domains_defined": len(variable_assignment.domains),
                    "assignment_time": assignment_time
                },
                outcome="success",
                reasoning=f"Successfully assigned {len(variable_assignment.assignments)} variables"
            )
            
            # Record component performance
            self.exploration_state.record_component_performance("VariableAssigner", assignment_time)
            
            if self.logger:
                self.logger.debug(f"Assigned {len(variable_assignment.assignments)} variables")
            
            # Log variable assignment
            self._log_debug("log_variable_assignment",
                assigner_type=self.variable_assigner.__class__.__name__,
                structure_id=f"struct_{self.exploration_state.iteration_count}",
                variables_assigned=len(variable_assignment.assignments),
                assignment_time=assignment_time,
                strategy=self.config.variable_assignment_strategy
            )
            
            # Capture intermediate state after variable assignment
            self.exploration_state.capture_intermediate_state(
                state_name="post_variable_assignment",
                state_data={
                    "assignments": dict(list(variable_assignment.assignments.items())[:5]),  # Sample of assignments
                    "domains": {k: str(v) for k, v in list(variable_assignment.domains.items())[:5]},  # Sample of domains
                    "total_assignments": len(variable_assignment.assignments)
                }
            )
            
            # Step 3: Create design object
            design_object = DesignObject(
                id=f"candidate_{self.exploration_state.iteration_count}",
                structure=structure,
                variables=variable_assignment,
                metadata={
                    "generation_strategy": self.config.exploration_strategy,
                    "iteration": self.exploration_state.iteration_count,
                    "timestamp": time.time()
                }
            )
            
            # Log exploration step
            self._log_debug("log_exploration_step",
                step=self.exploration_state.iteration_count,
                candidate_id=design_object.id,
                structure_info={
                    "components": len(structure.components),
                    "relationships": len(structure.relationships)
                },
                variables_info={
                    "assignments": len(variable_assignment.assignments),
                    "domains": len(variable_assignment.domains)
                }
            )
            
            # Step 4: Validate against schema
            schema_start_time = time.time()
            schema_result = self.schema_validator.validate(design_object.to_dict())
            schema_time = time.time() - schema_start_time
            
            if not schema_result.is_valid:
                if self.logger:
                    self.logger.debug(f"Schema validation failed: {[e.message for e in schema_result.errors]}")
                
                evaluation_time = time.time() - start_time
                self.exploration_state.record_candidate_evaluation(design_object, False, evaluation_time)
                
                # Record schema violations
                for error in schema_result.errors:
                    self.exploration_state.record_constraint_violation(
                        "schema_validation", 
                        f"Schema error at {error.path}: {error.message}"
                    )
                
                return design_object, False
            
            # Step 5: Evaluate constraints
            constraint_start_time = time.time()
            
            # Record decision about constraint evaluation
            self.exploration_state.record_decision(
                decision_type="constraint_evaluation",
                decision_data={
                    "candidate_id": design_object.id,
                    "constraints_to_check": len(self.constraints.get_all_constraints()),
                    "schema_valid": schema_result.is_valid
                },
                outcome="attempting",
                reasoning=f"Evaluating {len(self.constraints.get_all_constraints())} constraints for candidate"
            )
            
            evaluation_result = self.constraint_evaluator.evaluate(design_object)
            constraint_time = time.time() - constraint_start_time
            is_valid = evaluation_result.is_valid
            
            # Record constraint evaluation outcome
            self.exploration_state.record_decision(
                decision_type="constraint_evaluation",
                decision_data={
                    "is_valid": is_valid,
                    "violations_count": len(evaluation_result.violations),
                    "evaluation_time": constraint_time
                },
                outcome="success" if is_valid else "failure",
                reasoning=f"Constraint evaluation completed: {'valid' if is_valid else f'{len(evaluation_result.violations)} violations'}"
            )
            
            # Record component performance
            self.exploration_state.record_component_performance("ConstraintEvaluator", constraint_time)
            
            evaluation_time = time.time() - start_time
            self.exploration_state.record_candidate_evaluation(design_object, is_valid, evaluation_time)
            
            # Record progress
            self.progress_tracker.record_candidate_evaluation(evaluation_time, is_valid)
            
            # Log constraint evaluation with detailed violation information
            self._log_debug("log_constraint_evaluation",
                candidate_id=design_object.id,
                constraints_checked=len(self.constraints.get_all_constraints()),
                violations=evaluation_result.violations,
                evaluation_time=constraint_time
            )
            
            # Record constraint violations if any
            if not is_valid:
                for violation in evaluation_result.violations:
                    self.exploration_state.record_constraint_violation(
                        violation.constraint_id,
                        violation.message
                    )
                    
                    # Log detailed violation information
                    self._log_debug("log_constraint_violation_details", violation)
                
                if self.logger:
                    self.logger.debug(f"Constraint evaluation failed: {len(evaluation_result.violations)} violations")
                
                # Capture intermediate state for failed candidate
                self.exploration_state.capture_intermediate_state(
                    state_name="constraint_evaluation_failed",
                    state_data={
                        "candidate_id": design_object.id,
                        "violations": [{"id": v.constraint_id, "message": v.message} for v in evaluation_result.violations[:3]],
                        "total_violations": len(evaluation_result.violations)
                    }
                )
            else:
                if self.logger:
                    self.logger.debug("Candidate is valid!")
                
                # Log solution found
                self._log_debug("log_solution_found",
                    solution=design_object,
                    step=self.exploration_state.iteration_count
                )
                
                # Record solution found in progress tracker
                self.progress_tracker.record_solution_found(design_object.id)
                
                # Capture intermediate state for valid candidate
                self.exploration_state.capture_intermediate_state(
                    state_name="valid_solution_found",
                    state_data={
                        "candidate_id": design_object.id,
                        "solution_number": self.exploration_state.solutions_found + 1,
                        "structure_summary": {
                            "components": len(design_object.structure.components),
                            "relationships": len(design_object.structure.relationships)
                        },
                        "variables_summary": {
                            "assignments": len(design_object.variables.assignments)
                        }
                    }
                )
            
            # Log performance metrics
            self._log_debug("log_performance_metric",
                component="StructureGenerator",
                metric_name="generation_time",
                value=structure_time,
                unit="seconds"
            )
            
            self._log_debug("log_performance_metric",
                component="VariableAssigner", 
                metric_name="assignment_time",
                value=assignment_time,
                unit="seconds"
            )
            
            self._log_debug("log_performance_metric",
                component="ConstraintEvaluator",
                metric_name="evaluation_time", 
                value=constraint_time,
                unit="seconds"
            )
            
            return design_object, is_valid
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Exploration step failed: {str(e)}")
            
            # Log error
            self._log_debug("log_error",
                component="SEPEngine",
                error=e,
                context={
                    "step": self.exploration_state.iteration_count,
                    "exploration_strategy": self.config.exploration_strategy
                }
            )
            
            raise SEPSolverError(f"Exploration step failed: {str(e)}")
    
    def get_exploration_state(self) -> 'ExplorationState':
        """Return current exploration state for debugging.
        
        Returns:
            Current ExplorationState object
        """
        return self.exploration_state
    
    def inspect_current_state(self) -> Dict[str, Any]:
        """Get detailed inspection of current exploration state.
        
        Returns:
            Dictionary with comprehensive state information
        """
        return {
            "basic_info": {
                "strategy": self.exploration_state.strategy,
                "iteration_count": self.exploration_state.iteration_count,
                "solutions_found": self.exploration_state.solutions_found,
                "candidates_evaluated": self.exploration_state.candidates_evaluated,
                "is_active": self.exploration_state.is_exploration_active()
            },
            "progress_summary": self.exploration_state.get_progress_summary(),
            "component_performance": self.exploration_state.get_component_performance_summary(),
            "decision_summary": self.exploration_state.get_decision_summary(),
            "candidate_analysis": self.exploration_state.get_candidate_analysis(),
            "recent_activity": self.exploration_state.get_recent_activity(),
            "exploration_path": self.exploration_state.get_exploration_path_summary()
        }
    
    def inspect_decision_trace(self, last_n_decisions: int = 20) -> List[Dict[str, Any]]:
        """Get detailed trace of recent decisions.
        
        Args:
            last_n_decisions: Number of recent decisions to return
            
        Returns:
            List of decision trace entries
        """
        recent_decisions = self.exploration_state.decision_trace[-last_n_decisions:] if len(self.exploration_state.decision_trace) >= last_n_decisions else self.exploration_state.decision_trace
        return [decision.to_dict() for decision in recent_decisions]
    
    def inspect_candidate_history(self, last_n_candidates: int = 10) -> List[Dict[str, Any]]:
        """Get detailed history of recent candidates.
        
        Args:
            last_n_candidates: Number of recent candidates to return
            
        Returns:
            List of candidate snapshot entries
        """
        recent_candidates = self.exploration_state.candidate_snapshots[-last_n_candidates:] if len(self.exploration_state.candidate_snapshots) >= last_n_candidates else self.exploration_state.candidate_snapshots
        return [candidate.to_dict() for candidate in recent_candidates]
    
    def inspect_constraint_violations(self) -> Dict[str, Any]:
        """Get detailed analysis of constraint violations.
        
        Returns:
            Dictionary with violation analysis
        """
        return {
            "total_violations": sum(self.exploration_state.constraint_violation_counts.values()),
            "unique_constraints_violated": len(self.exploration_state.constraint_violation_counts),
            "most_violated": self.exploration_state.get_most_violated_constraints(10),
            "recent_violations": self.exploration_state.recent_violations[-20:],
            "violation_rate": sum(self.exploration_state.constraint_violation_counts.values()) / max(self.exploration_state.candidates_evaluated, 1)
        }
    
    def inspect_component_performance(self) -> Dict[str, Any]:
        """Get detailed component performance analysis.
        
        Returns:
            Dictionary with performance analysis
        """
        performance_summary = self.exploration_state.get_component_performance_summary()
        
        # Add additional analysis
        total_time = sum(stats["total_time"] for stats in performance_summary.values())
        
        analysis = {
            "summary": performance_summary,
            "total_time": total_time,
            "time_distribution": {}
        }
        
        # Calculate time distribution percentages
        if total_time > 0:
            for component, stats in performance_summary.items():
                analysis["time_distribution"][component] = {
                    "percentage": (stats["total_time"] / total_time) * 100,
                    "calls_per_second": stats["count"] / max(total_time, 0.001)
                }
        
        return analysis
    
    def inspect_exploration_efficiency(self) -> Dict[str, Any]:
        """Analyze exploration efficiency metrics.
        
        Returns:
            Dictionary with efficiency analysis
        """
        duration = self.exploration_state.get_exploration_duration()
        if duration is None or duration == 0:
            return {"error": "Exploration not started or no time elapsed"}
        
        return {
            "time_efficiency": {
                "total_duration": duration,
                "time_per_iteration": duration / max(self.exploration_state.iteration_count, 1),
                "time_per_candidate": duration / max(self.exploration_state.candidates_evaluated, 1),
                "time_per_solution": duration / max(self.exploration_state.solutions_found, 1) if self.exploration_state.solutions_found > 0 else None
            },
            "success_rates": {
                "solution_rate": self.exploration_state.solutions_found / max(self.exploration_state.candidates_evaluated, 1),
                "solutions_per_second": self.exploration_state.get_solutions_per_second(),
                "candidates_per_second": self.exploration_state.candidates_evaluated / duration
            },
            "resource_utilization": {
                "average_evaluation_time": self.exploration_state.get_average_evaluation_time(),
                "component_performance": self.exploration_state.get_component_performance_summary()
            }
        }
    
    def export_exploration_trace(self, filename: str, format: str = "json") -> None:
        """Export complete exploration trace to file.
        
        Args:
            filename: Output filename
            format: Export format ("json" or "summary")
        """
        trace_content = self.exploration_state.export_debug_trace(format)
        
        with open(filename, 'w') as f:
            f.write(trace_content)
        
        if self.logger:
            self.logger.info(f"Exported exploration trace to {filename} in {format} format")
    
    def get_debug_recommendations(self) -> List[str]:
        """Get recommendations for debugging based on current state.
        
        Returns:
            List of debugging recommendations
        """
        recommendations = []
        
        # Check solution rate
        if self.exploration_state.candidates_evaluated > 10:
            solution_rate = self.exploration_state.solutions_found / self.exploration_state.candidates_evaluated
            if solution_rate < 0.01:  # Less than 1% success rate
                recommendations.append("Very low solution rate - consider relaxing constraints or adjusting generation strategy")
        
        # Check most violated constraints
        most_violated = self.exploration_state.get_most_violated_constraints(3)
        if most_violated:
            top_constraint, violation_count = most_violated[0]
            if violation_count > self.exploration_state.candidates_evaluated * 0.8:
                recommendations.append(f"Constraint '{top_constraint}' is violated in >80% of candidates - review constraint definition")
        
        # Check component performance
        perf_summary = self.exploration_state.get_component_performance_summary()
        if perf_summary:
            slowest_component = max(perf_summary.items(), key=lambda x: x[1]["average_time"])
            component_name, stats = slowest_component
            if stats["average_time"] > 1.0:  # More than 1 second average
                recommendations.append(f"Component '{component_name}' is slow (avg: {stats['average_time']:.2f}s) - consider optimization")
        
        # Check exploration strategy effectiveness
        if self.exploration_state.iteration_count > 50 and self.exploration_state.solutions_found == 0:
            recommendations.append("No solutions found after many iterations - consider changing exploration strategy")
        
        # Check for repeated failures
        recent_decisions = self.exploration_state.decision_trace[-20:] if len(self.exploration_state.decision_trace) >= 20 else self.exploration_state.decision_trace
        failure_count = sum(1 for d in recent_decisions if d.outcome == "failure")
        if len(recent_decisions) > 10 and failure_count / len(recent_decisions) > 0.9:
            recommendations.append("High failure rate in recent decisions - investigate constraint or generation issues")
        
        if not recommendations:
            recommendations.append("Exploration appears to be running normally")
        
        return recommendations
    
    def reset(self) -> None:
        """Reset the exploration state."""
        from ..models.exploration_state import ExplorationState
        self.exploration_state = ExplorationState()
        if self.logger:
            self.logger.info("Exploration state reset")
    
    def set_component(self, component_type: str, component: Any) -> None:
        """Set a solver component.
        
        Args:
            component_type: Type of component ("structure_generator", "variable_assigner", etc.)
            component: The component instance
            
        Raises:
            ConfigurationError: If component type is invalid
        """
        from .interfaces import StructureGenerator, VariableAssigner, ConstraintEvaluator, SchemaValidator
        
        valid_types = {
            "structure_generator": StructureGenerator,
            "variable_assigner": VariableAssigner, 
            "constraint_evaluator": ConstraintEvaluator,
            "schema_validator": SchemaValidator
        }
        
        if component_type not in valid_types:
            raise ConfigurationError(f"Invalid component type: {component_type}")
        
        expected_interface = valid_types[component_type]
        if not isinstance(component, expected_interface):
            raise ConfigurationError(f"Component must implement {expected_interface.__name__}")
        
        setattr(self, component_type, component)
        
        if self.logger:
            self.logger.info(f"Set {component_type}: {component.__class__.__name__}")
    
    def get_component(self, component_type: str) -> Any:
        """Get a solver component.
        
        Args:
            component_type: Type of component to get
            
        Returns:
            The component instance
            
        Raises:
            ConfigurationError: If component type is invalid or not set
        """
        valid_types = ["structure_generator", "variable_assigner", "constraint_evaluator", "schema_validator"]
        
        if component_type not in valid_types:
            raise ConfigurationError(f"Invalid component type: {component_type}")
        
        component = getattr(self, component_type, None)
        if component is None:
            raise ConfigurationError(f"Component {component_type} not set")
        
        return component
    
    def _initialize_default_components(self) -> None:
        """Initialize default components if not provided."""
        from .plugin_system import get_plugin_manager
        
        plugin_manager = get_plugin_manager()
        plugin_manager.register_default_plugins()
        
        # Initialize default structure generator if not provided
        if self.structure_generator is None:
            self.structure_generator = plugin_manager.create_component("structure_generator")
            if self.logger:
                self.logger.debug("Initialized structure generator via plugin system")
        
        # Initialize default variable assigner if not provided
        if self.variable_assigner is None:
            self.variable_assigner = plugin_manager.create_component("variable_assigner")
            if self.logger:
                self.logger.debug("Initialized variable assigner via plugin system")
        
        # Initialize default constraint evaluator if not provided
        if self.constraint_evaluator is None:
            # Create with constraints
            from ..evaluators.constraint_evaluator import BaseConstraintEvaluator
            self.constraint_evaluator = BaseConstraintEvaluator(self.constraints)
            if self.logger:
                self.logger.debug("Initialized constraint evaluator via plugin system")
        
        # Initialize default schema validator if not provided
        if self.schema_validator is None:
            # Create with schema
            from ..evaluators.schema_validator import JSONSchemaValidator
            self.schema_validator = JSONSchemaValidator(self.schema)
            if self.logger:
                self.logger.debug("Initialized schema validator via plugin system")
    
    def set_component_via_plugin(self, component_type: str, plugin_name: str, 
                                config: Dict[str, Any] = None) -> None:
        """Set a component using a plugin.
        
        Args:
            component_type: Type of component to set
            plugin_name: Name of plugin to use
            config: Optional configuration for the component
            
        Raises:
            ConfigurationError: If plugin not found or component creation fails
        """
        from .plugin_system import get_plugin_manager
        
        plugin_manager = get_plugin_manager()
        
        # Special handling for components that need additional parameters
        if component_type == "constraint_evaluator":
            # Create the component and pass constraints
            plugin = plugin_manager.registry.get_plugin(plugin_name)
            if plugin is None:
                raise ConfigurationError(f"Plugin not found: {plugin_name}")
            
            if config:
                plugin.config.update(config)
                plugin.validate_config(plugin.config)
            
            component = plugin.create_component()
            # If it's a BaseConstraintEvaluator, set constraints
            if hasattr(component, 'constraints'):
                component.constraints = self.constraints
            
            self.constraint_evaluator = component
            
        elif component_type == "schema_validator":
            # Create the component and pass schema
            plugin = plugin_manager.registry.get_plugin(plugin_name)
            if plugin is None:
                raise ConfigurationError(f"Plugin not found: {plugin_name}")
            
            if config:
                plugin.config.update(config)
                plugin.validate_config(plugin.config)
            
            component = plugin.create_component()
            # If it's a JSONSchemaValidator, set schema
            if hasattr(component, 'schema'):
                component.schema = self.schema
            
            self.schema_validator = component
            
        else:
            # Standard component creation
            component = plugin_manager.create_component(component_type, plugin_name, config)
            setattr(self, component_type, component)
        
        if self.logger:
            self.logger.info(f"Set {component_type} using plugin: {plugin_name}")
    
    def list_available_plugins(self, component_type: str = None) -> List[Dict[str, Any]]:
        """List available plugins for components.
        
        Args:
            component_type: Optional filter by component type
            
        Returns:
            List of plugin information dictionaries
        """
        from .plugin_system import get_plugin_manager
        
        plugin_manager = get_plugin_manager()
        plugin_manager.register_default_plugins()
        
        plugins = plugin_manager.list_available_plugins(component_type)
        return [plugin.to_dict() for plugin in plugins]
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Plugin information dictionary or None if not found
        """
        from .plugin_system import get_plugin_manager
        
        plugin_manager = get_plugin_manager()
        plugin_info = plugin_manager.get_plugin_info(plugin_name)
        return plugin_info.to_dict() if plugin_info else None
    
    def update_configuration(self, **kwargs) -> None:
        """Update configuration at runtime.
        
        Args:
            **kwargs: Configuration parameters to update
            
        Raises:
            ConfigurationError: If runtime modification fails
        """
        self.config.modify_runtime(**kwargs)
        
        if self.logger:
            self.logger.info(f"Configuration updated: {list(kwargs.keys())}")
    
    def apply_configuration_preset(self, preset: str) -> None:
        """Apply a configuration preset.
        
        Args:
            preset: Preset name ("fast", "thorough", "balanced", "debug")
        """
        self.config.apply_exploration_preset(preset)
        
        if self.logger:
            self.logger.info(f"Applied configuration preset: {preset}")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration.
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            "exploration_parameters": self.config.get_exploration_parameters(),
            "validation_settings": {
                "enable_schema_validation": self.config.enable_schema_validation,
                "enable_constraint_validation": self.config.enable_constraint_validation,
                "strict_validation": self.config.strict_validation
            },
            "logging_settings": {
                "enable_logging": self.config.enable_logging,
                "log_level": self.config.log_level,
                "enable_debug_tracing": self.config.enable_debug_tracing
            },
            "performance_settings": {
                "parallel_evaluation": self.config.parallel_evaluation,
                "cache_evaluations": self.config.cache_evaluations,
                "cache_size": self.config.cache_size
            },
            "plugin_settings": {
                "plugin_directories": self.config.plugin_directories,
                "enabled_plugins": self.config.enabled_plugins
            }
        }
    
    def save_configuration(self, filename: str, format: str = "json") -> None:
        """Save current configuration to file.
        
        Args:
            filename: Output filename
            format: File format ("json" or "yaml")
        """
        self.config.save_to_file(filename, format)
        
        if self.logger:
            self.logger.info(f"Configuration saved to {filename} in {format} format")
    
    def add_configuration_callback(self, parameter: str, callback: Callable[[str, Any, Any], None]) -> None:
        """Add a callback for configuration changes.
        
        Args:
            parameter: Parameter name to watch
            callback: Callback function (parameter_name, new_value, old_value) -> None
        """
        self.config.add_modification_callback(parameter, callback)
    
    def add_progress_reporter(self, reporter) -> None:
        """Add a progress reporter.
        
        Args:
            reporter: Progress reporter instance
        """
        from ..utils.progress import ProgressReporter
        if isinstance(reporter, ProgressReporter):
            self.progress_tracker.add_reporter(reporter)
        else:
            raise ConfigurationError("Reporter must be an instance of ProgressReporter")
    
    def get_progress_metrics(self) -> Dict[str, Any]:
        """Get current progress metrics.
        
        Returns:
            Dictionary with current progress metrics
        """
        metrics = self.progress_tracker.get_current_metrics()
        return metrics.to_dict()
    
    def create_console_progress_reporter(self, update_interval: float = 1.0, 
                                       show_details: bool = True) -> None:
        """Create and add a console progress reporter.
        
        Args:
            update_interval: Minimum seconds between updates
            show_details: Whether to show detailed metrics
        """
        from ..utils.progress import create_console_reporter
        reporter = create_console_reporter(update_interval, show_details)
        self.add_progress_reporter(reporter)
    
    def create_file_progress_reporter(self, filename: str, format: str = "json") -> None:
        """Create and add a file progress reporter.
        
        Args:
            filename: Output filename
            format: File format ("json" or "csv")
        """
        from ..utils.progress import create_file_reporter
        reporter = create_file_reporter(filename, format)
        self.add_progress_reporter(reporter)
    
    def create_callback_progress_reporter(self, 
                                        progress_callback: Optional[Callable] = None,
                                        solution_callback: Optional[Callable] = None,
                                        completion_callback: Optional[Callable] = None) -> None:
        """Create and add a callback progress reporter.
        
        Args:
            progress_callback: Called with progress metrics
            solution_callback: Called when solution is found
            completion_callback: Called when exploration completes
        """
        from ..utils.progress import create_callback_reporter
        reporter = create_callback_reporter()
        
        if progress_callback:
            reporter.add_progress_callback(progress_callback)
        if solution_callback:
            reporter.add_solution_callback(solution_callback)
        if completion_callback:
            reporter.add_completion_callback(completion_callback)
        
        self.add_progress_reporter(reporter)
    
    def discover_plugins(self, plugin_dirs: List[str] = None) -> List[str]:
        """Discover and load plugins from directories.
        
        Args:
            plugin_dirs: List of directory paths to search for plugins
            
        Returns:
            List of discovered plugin names
        """
        from .plugin_system import get_plugin_manager
        from pathlib import Path
        
        plugin_manager = get_plugin_manager()
        
        paths = []
        if plugin_dirs:
            paths = [Path(dir_path) for dir_path in plugin_dirs]
        
        discovered = plugin_manager.discover_and_load_plugins(paths)
        
        if self.logger:
            self.logger.info(f"Discovered {len(discovered)} plugins: {discovered}")
        
        return discovered