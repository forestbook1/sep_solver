"""Exploration state model for the SEP solver."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import json
from .design_object import DesignObject


@dataclass
class DecisionTrace:
    """Represents a decision made during exploration."""
    timestamp: datetime
    step: int
    decision_type: str  # "structure_generation", "variable_assignment", "constraint_evaluation"
    decision_data: Dict[str, Any]
    outcome: str  # "success", "failure", "partial"
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "step": self.step,
            "decision_type": self.decision_type,
            "decision_data": self.decision_data,
            "outcome": self.outcome,
            "reasoning": self.reasoning
        }


@dataclass
class CandidateSnapshot:
    """Snapshot of a candidate at a specific point in exploration."""
    candidate_id: str
    step: int
    timestamp: datetime
    structure_info: Dict[str, Any]
    variables_info: Dict[str, Any]
    validation_result: Dict[str, Any]
    score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "candidate_id": self.candidate_id,
            "step": self.step,
            "timestamp": self.timestamp.isoformat(),
            "structure_info": self.structure_info,
            "variables_info": self.variables_info,
            "validation_result": self.validation_result,
            "score": self.score
        }


@dataclass
class ExplorationState:
    """Represents the current state of the exploration process."""
    
    # Exploration progress
    iteration_count: int = 0
    solutions_found: int = 0
    candidates_evaluated: int = 0
    
    # Current exploration data
    current_candidate: Optional[DesignObject] = None
    best_candidates: List[DesignObject] = field(default_factory=list)
    recent_violations: List[str] = field(default_factory=list)
    
    # Exploration strategy state
    strategy: str = "breadth_first"
    exploration_queue: List[Any] = field(default_factory=list)
    visited_states: set = field(default_factory=set)
    
    # Performance metrics
    start_time: Optional[datetime] = None
    last_solution_time: Optional[datetime] = None
    evaluation_times: List[float] = field(default_factory=list)
    
    # Debug information
    debug_log: List[str] = field(default_factory=list)
    constraint_violation_counts: Dict[str, int] = field(default_factory=dict)
    
    # Enhanced inspection data
    decision_trace: List[DecisionTrace] = field(default_factory=list)
    candidate_snapshots: List[CandidateSnapshot] = field(default_factory=list)
    intermediate_states: List[Dict[str, Any]] = field(default_factory=list)
    component_performance: Dict[str, List[float]] = field(default_factory=dict)
    exploration_path: List[str] = field(default_factory=list)
    
    def start_exploration(self, strategy: str = "breadth_first") -> None:
        """Start a new exploration session.
        
        Args:
            strategy: Exploration strategy to use
        """
        self.strategy = strategy
        self.start_time = datetime.now()
        self.iteration_count = 0
        self.solutions_found = 0
        self.candidates_evaluated = 0
        self.best_candidates.clear()
        self.recent_violations.clear()
        self.exploration_queue.clear()
        self.visited_states.clear()
        self.debug_log.clear()
        self.constraint_violation_counts.clear()
        self.evaluation_times.clear()
        self.decision_trace.clear()
        self.candidate_snapshots.clear()
        self.intermediate_states.clear()
        self.component_performance.clear()
        self.exploration_path.clear()
        
        self.add_debug_message(f"Started exploration with strategy: {strategy}")
    
    def record_iteration(self) -> None:
        """Record completion of an exploration iteration."""
        self.iteration_count += 1
        self.exploration_path.append(f"step_{self.iteration_count}")
    
    def record_candidate_evaluation(self, candidate: DesignObject, is_valid: bool, 
                                  evaluation_time: float = 0.0) -> None:
        """Record evaluation of a candidate solution.
        
        Args:
            candidate: The candidate that was evaluated
            is_valid: Whether the candidate is valid
            evaluation_time: Time taken to evaluate (seconds)
        """
        self.candidates_evaluated += 1
        self.current_candidate = candidate
        
        if evaluation_time > 0:
            self.evaluation_times.append(evaluation_time)
        
        # Create candidate snapshot
        snapshot = CandidateSnapshot(
            candidate_id=candidate.id,
            step=self.iteration_count,
            timestamp=datetime.now(),
            structure_info={
                "components_count": len(candidate.structure.components),
                "relationships_count": len(candidate.structure.relationships),
                "component_types": [comp.type for comp in candidate.structure.components]
            },
            variables_info={
                "assignments_count": len(candidate.variables.assignments),
                "domains_count": len(candidate.variables.domains),
                "variable_names": list(candidate.variables.assignments.keys())
            },
            validation_result={
                "is_valid": is_valid,
                "evaluation_time": evaluation_time
            }
        )
        self.candidate_snapshots.append(snapshot)
        
        # Keep only recent snapshots
        max_snapshots = 100
        if len(self.candidate_snapshots) > max_snapshots:
            self.candidate_snapshots = self.candidate_snapshots[-max_snapshots:]
        
        if is_valid:
            self.solutions_found += 1
            self.last_solution_time = datetime.now()
            self.best_candidates.append(candidate)
            
            self.add_debug_message(f"Found valid solution: {candidate.id}")
            
            # Keep only the best N candidates
            max_best = 10
            if len(self.best_candidates) > max_best:
                self.best_candidates = self.best_candidates[-max_best:]
        else:
            self.add_debug_message(f"Invalid candidate: {candidate.id}")
    
    def record_constraint_violation(self, constraint_id: str, message: str) -> None:
        """Record a constraint violation.
        
        Args:
            constraint_id: ID of the violated constraint
            message: Violation message
        """
        self.recent_violations.append(f"{constraint_id}: {message}")
        
        # Keep only recent violations
        max_recent = 50
        if len(self.recent_violations) > max_recent:
            self.recent_violations = self.recent_violations[-max_recent:]
        
        # Count violations by constraint
        if constraint_id in self.constraint_violation_counts:
            self.constraint_violation_counts[constraint_id] += 1
        else:
            self.constraint_violation_counts[constraint_id] = 1
    
    def record_decision(self, decision_type: str, decision_data: Dict[str, Any], 
                       outcome: str, reasoning: str) -> None:
        """Record a decision made during exploration.
        
        Args:
            decision_type: Type of decision made
            decision_data: Data associated with the decision
            outcome: Outcome of the decision
            reasoning: Reasoning behind the decision
        """
        decision = DecisionTrace(
            timestamp=datetime.now(),
            step=self.iteration_count,
            decision_type=decision_type,
            decision_data=decision_data,
            outcome=outcome,
            reasoning=reasoning
        )
        self.decision_trace.append(decision)
        
        # Keep only recent decisions
        max_decisions = 200
        if len(self.decision_trace) > max_decisions:
            self.decision_trace = self.decision_trace[-max_decisions:]
        
        self.add_debug_message(f"Decision: {decision_type} -> {outcome} ({reasoning})")
    
    def record_component_performance(self, component_name: str, execution_time: float) -> None:
        """Record performance metrics for a component.
        
        Args:
            component_name: Name of the component
            execution_time: Time taken to execute
        """
        if component_name not in self.component_performance:
            self.component_performance[component_name] = []
        
        self.component_performance[component_name].append(execution_time)
        
        # Keep only recent performance data
        max_performance = 100
        if len(self.component_performance[component_name]) > max_performance:
            self.component_performance[component_name] = self.component_performance[component_name][-max_performance:]
    
    def capture_intermediate_state(self, state_name: str, state_data: Dict[str, Any]) -> None:
        """Capture an intermediate state during exploration.
        
        Args:
            state_name: Name/description of the state
            state_data: Data representing the state
        """
        state = {
            "name": state_name,
            "step": self.iteration_count,
            "timestamp": datetime.now().isoformat(),
            "data": state_data
        }
        self.intermediate_states.append(state)
        
        # Keep only recent states
        max_states = 50
        if len(self.intermediate_states) > max_states:
            self.intermediate_states = self.intermediate_states[-max_states:]
    
    def add_debug_message(self, message: str) -> None:
        """Add a debug message to the log.
        
        Args:
            message: Debug message
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.debug_log.append(f"[{timestamp}] {message}")
        
        # Keep only recent debug messages
        max_debug = 100
        if len(self.debug_log) > max_debug:
            self.debug_log = self.debug_log[-max_debug:]
    
    def get_exploration_duration(self) -> Optional[float]:
        """Get the duration of exploration in seconds.
        
        Returns:
            Duration in seconds or None if not started
        """
        if self.start_time is None:
            return None
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_average_evaluation_time(self) -> float:
        """Get the average evaluation time per candidate.
        
        Returns:
            Average evaluation time in seconds
        """
        if not self.evaluation_times:
            return 0.0
        return sum(self.evaluation_times) / len(self.evaluation_times)
    
    def get_solutions_per_second(self) -> float:
        """Get the rate of solution discovery.
        
        Returns:
            Solutions found per second
        """
        duration = self.get_exploration_duration()
        if duration is None or duration == 0:
            return 0.0
        return self.solutions_found / duration
    
    def get_most_violated_constraints(self, top_n: int = 5) -> List[tuple]:
        """Get the most frequently violated constraints.
        
        Args:
            top_n: Number of top constraints to return
            
        Returns:
            List of (constraint_id, violation_count) tuples
        """
        sorted_violations = sorted(
            self.constraint_violation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_violations[:top_n]
    
    def get_component_performance_summary(self) -> Dict[str, Dict[str, float]]:
        """Get performance summary for all components.
        
        Returns:
            Dictionary with performance statistics for each component
        """
        summary = {}
        for component, times in self.component_performance.items():
            if times:
                summary[component] = {
                    "count": len(times),
                    "total_time": sum(times),
                    "average_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
            else:
                summary[component] = {
                    "count": 0,
                    "total_time": 0.0,
                    "average_time": 0.0,
                    "min_time": 0.0,
                    "max_time": 0.0
                }
        return summary
    
    def get_decision_summary(self) -> Dict[str, Any]:
        """Get summary of decisions made during exploration.
        
        Returns:
            Dictionary with decision statistics
        """
        if not self.decision_trace:
            return {"total_decisions": 0}
        
        decision_types = {}
        outcomes = {}
        
        for decision in self.decision_trace:
            # Count by decision type
            if decision.decision_type not in decision_types:
                decision_types[decision.decision_type] = 0
            decision_types[decision.decision_type] += 1
            
            # Count by outcome
            if decision.outcome not in outcomes:
                outcomes[decision.outcome] = 0
            outcomes[decision.outcome] += 1
        
        return {
            "total_decisions": len(self.decision_trace),
            "by_type": decision_types,
            "by_outcome": outcomes,
            "recent_decisions": [d.to_dict() for d in self.decision_trace[-5:]]
        }
    
    def get_exploration_path_summary(self) -> Dict[str, Any]:
        """Get summary of the exploration path taken.
        
        Returns:
            Dictionary with path information
        """
        return {
            "total_steps": len(self.exploration_path),
            "current_step": self.exploration_path[-1] if self.exploration_path else None,
            "path": self.exploration_path[-10:] if len(self.exploration_path) > 10 else self.exploration_path
        }
    
    def get_candidate_analysis(self) -> Dict[str, Any]:
        """Get analysis of evaluated candidates.
        
        Returns:
            Dictionary with candidate analysis
        """
        if not self.candidate_snapshots:
            return {"total_candidates": 0}
        
        valid_candidates = [s for s in self.candidate_snapshots if s.validation_result.get("is_valid", False)]
        invalid_candidates = [s for s in self.candidate_snapshots if not s.validation_result.get("is_valid", False)]
        
        # Analyze structure patterns
        component_counts = [s.structure_info["components_count"] for s in self.candidate_snapshots]
        relationship_counts = [s.structure_info["relationships_count"] for s in self.candidate_snapshots]
        
        return {
            "total_candidates": len(self.candidate_snapshots),
            "valid_candidates": len(valid_candidates),
            "invalid_candidates": len(invalid_candidates),
            "success_rate": len(valid_candidates) / len(self.candidate_snapshots) if self.candidate_snapshots else 0,
            "structure_analysis": {
                "avg_components": sum(component_counts) / len(component_counts) if component_counts else 0,
                "avg_relationships": sum(relationship_counts) / len(relationship_counts) if relationship_counts else 0,
                "component_range": (min(component_counts), max(component_counts)) if component_counts else (0, 0),
                "relationship_range": (min(relationship_counts), max(relationship_counts)) if relationship_counts else (0, 0)
            }
        }
    
    def get_recent_activity(self, last_n_steps: int = 10) -> Dict[str, Any]:
        """Get recent exploration activity.
        
        Args:
            last_n_steps: Number of recent steps to analyze
            
        Returns:
            Dictionary with recent activity information
        """
        recent_snapshots = self.candidate_snapshots[-last_n_steps:] if len(self.candidate_snapshots) >= last_n_steps else self.candidate_snapshots
        recent_decisions = self.decision_trace[-last_n_steps:] if len(self.decision_trace) >= last_n_steps else self.decision_trace
        recent_violations = self.recent_violations[-last_n_steps:] if len(self.recent_violations) >= last_n_steps else self.recent_violations
        
        return {
            "steps_analyzed": min(last_n_steps, self.iteration_count),
            "candidates_in_period": len(recent_snapshots),
            "decisions_in_period": len(recent_decisions),
            "violations_in_period": len(recent_violations),
            "recent_candidates": [s.to_dict() for s in recent_snapshots],
            "recent_decisions": [d.to_dict() for d in recent_decisions],
            "recent_violations": recent_violations
        }
    
    def export_debug_trace(self, format: str = "json") -> str:
        """Export complete debug trace.
        
        Args:
            format: Export format ("json" or "summary")
            
        Returns:
            Formatted debug trace
        """
        if format == "json":
            trace_data = {
                "exploration_info": {
                    "strategy": self.strategy,
                    "start_time": self.start_time.isoformat() if self.start_time else None,
                    "duration": self.get_exploration_duration(),
                    "iteration_count": self.iteration_count,
                    "solutions_found": self.solutions_found
                },
                "decision_trace": [d.to_dict() for d in self.decision_trace],
                "candidate_snapshots": [s.to_dict() for s in self.candidate_snapshots],
                "intermediate_states": self.intermediate_states,
                "component_performance": self.get_component_performance_summary(),
                "debug_log": self.debug_log
            }
            return json.dumps(trace_data, indent=2)
        
        elif format == "summary":
            lines = []
            lines.append(f"Exploration Debug Trace Summary")
            lines.append(f"Strategy: {self.strategy}")
            lines.append(f"Duration: {self.get_exploration_duration():.2f}s")
            lines.append(f"Iterations: {self.iteration_count}")
            lines.append(f"Solutions: {self.solutions_found}")
            lines.append("")
            
            lines.append("Recent Decisions:")
            for decision in self.decision_trace[-5:]:
                lines.append(f"  {decision.decision_type}: {decision.outcome} - {decision.reasoning}")
            lines.append("")
            
            lines.append("Component Performance:")
            perf_summary = self.get_component_performance_summary()
            for component, stats in perf_summary.items():
                lines.append(f"  {component}: {stats['average_time']:.4f}s avg ({stats['count']} calls)")
            lines.append("")
            
            lines.append("Recent Debug Messages:")
            for msg in self.debug_log[-10:]:
                lines.append(f"  {msg}")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def is_exploration_active(self) -> bool:
        """Check if exploration is currently active.
        
        Returns:
            True if exploration has been started
        """
        return self.start_time is not None
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of exploration progress.
        
        Returns:
            Dictionary containing progress information
        """
        return {
            "iteration_count": self.iteration_count,
            "solutions_found": self.solutions_found,
            "candidates_evaluated": self.candidates_evaluated,
            "strategy": self.strategy,
            "duration_seconds": self.get_exploration_duration(),
            "average_evaluation_time": self.get_average_evaluation_time(),
            "solutions_per_second": self.get_solutions_per_second(),
            "most_violated_constraints": self.get_most_violated_constraints(3),
            "component_performance": self.get_component_performance_summary(),
            "decision_summary": self.get_decision_summary(),
            "candidate_analysis": self.get_candidate_analysis()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation of exploration state
        """
        return {
            "iteration_count": self.iteration_count,
            "solutions_found": self.solutions_found,
            "candidates_evaluated": self.candidates_evaluated,
            "strategy": self.strategy,
            "current_candidate_id": self.current_candidate.id if self.current_candidate else None,
            "best_candidates_count": len(self.best_candidates),
            "recent_violations_count": len(self.recent_violations),
            "constraint_violation_counts": self.constraint_violation_counts,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "duration_seconds": self.get_exploration_duration(),
            "progress_summary": self.get_progress_summary(),
            "decision_trace_count": len(self.decision_trace),
            "candidate_snapshots_count": len(self.candidate_snapshots),
            "intermediate_states_count": len(self.intermediate_states)
        }
    
    def __str__(self) -> str:
        """String representation."""
        duration = self.get_exploration_duration()
        duration_str = f"{duration:.1f}s" if duration else "not started"
        return f"ExplorationState(iter={self.iteration_count}, solutions={self.solutions_found}, duration={duration_str})"