"""Enhanced debugging logger for the SEP solver."""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from ..models.design_object import DesignObject
from ..models.constraint_set import ConstraintViolation


@dataclass
class LogEntry:
    """Represents a single log entry with structured data."""
    timestamp: float
    level: str
    component: str
    event_type: str
    message: str
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert log entry to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)


class DebugLogger:
    """Enhanced debug logger for SEP solver with structured logging."""
    
    def __init__(self, name: str = "SEPSolver", log_file: Optional[str] = None):
        """Initialize debug logger.
        
        Args:
            name: Logger name
            log_file: Optional file to write structured logs
        """
        self.name = name
        self.log_file = log_file
        self.entries: List[LogEntry] = []
        self.start_time = time.time()
        
        # Set up standard logger
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
    
    def log_exploration_start(self, strategy: str, config: Dict[str, Any]) -> None:
        """Log the start of exploration process."""
        self._log_event(
            level="INFO",
            component="SEPEngine",
            event_type="exploration_start",
            message=f"Starting exploration with strategy: {strategy}",
            data={
                "strategy": strategy,
                "config": config,
                "start_time": time.time()
            }
        )
    
    def log_exploration_step(self, step: int, candidate_id: str, 
                           structure_info: Dict[str, Any], 
                           variables_info: Dict[str, Any]) -> None:
        """Log a single exploration step."""
        self._log_event(
            level="DEBUG",
            component="SEPEngine",
            event_type="exploration_step",
            message=f"Exploration step {step}: evaluating candidate {candidate_id}",
            data={
                "step": step,
                "candidate_id": candidate_id,
                "structure": structure_info,
                "variables": variables_info,
                "timestamp": time.time()
            }
        )
    
    def log_structure_generation(self, generator_type: str, structure_id: str,
                               components_count: int, relationships_count: int,
                               generation_time: float) -> None:
        """Log structure generation details."""
        self._log_event(
            level="DEBUG",
            component="StructureGenerator",
            event_type="structure_generated",
            message=f"Generated structure {structure_id} with {components_count} components",
            data={
                "generator_type": generator_type,
                "structure_id": structure_id,
                "components_count": components_count,
                "relationships_count": relationships_count,
                "generation_time": generation_time
            }
        )
    
    def log_variable_assignment(self, assigner_type: str, structure_id: str,
                              variables_assigned: int, assignment_time: float,
                              strategy: str) -> None:
        """Log variable assignment details."""
        self._log_event(
            level="DEBUG",
            component="VariableAssigner",
            event_type="variables_assigned",
            message=f"Assigned {variables_assigned} variables for structure {structure_id}",
            data={
                "assigner_type": assigner_type,
                "structure_id": structure_id,
                "variables_assigned": variables_assigned,
                "assignment_time": assignment_time,
                "strategy": strategy
            }
        )
    
    def log_constraint_evaluation(self, candidate_id: str, 
                                constraints_checked: int,
                                violations: List[ConstraintViolation],
                                evaluation_time: float) -> None:
        """Log constraint evaluation with detailed violation information."""
        violation_details = []
        for violation in violations:
            violation_details.append({
                "constraint_id": violation.constraint_id,
                "constraint_type": violation.constraint_type,
                "message": violation.message,
                "component_id": getattr(violation, 'component_id', None),
                "variable_name": getattr(violation, 'variable_name', None),
                "expected_value": getattr(violation, 'expected_value', None),
                "actual_value": getattr(violation, 'actual_value', None)
            })
        
        self._log_event(
            level="INFO" if not violations else "WARNING",
            component="ConstraintEvaluator",
            event_type="constraint_evaluation",
            message=f"Evaluated {constraints_checked} constraints for {candidate_id}: {len(violations)} violations",
            data={
                "candidate_id": candidate_id,
                "constraints_checked": constraints_checked,
                "violations_count": len(violations),
                "violations": violation_details,
                "evaluation_time": evaluation_time,
                "is_valid": len(violations) == 0
            }
        )
    
    def log_constraint_violation_details(self, violation: ConstraintViolation) -> None:
        """Log detailed information about a specific constraint violation."""
        self._log_event(
            level="WARNING",
            component="ConstraintEvaluator",
            event_type="constraint_violation",
            message=f"Constraint violation: {violation.message}",
            data={
                "constraint_id": violation.constraint_id,
                "constraint_type": violation.constraint_type,
                "message": violation.message,
                "component_id": getattr(violation, 'component_id', None),
                "variable_name": getattr(violation, 'variable_name', None),
                "expected_value": getattr(violation, 'expected_value', None),
                "actual_value": getattr(violation, 'actual_value', None),
                "severity": getattr(violation, 'severity', 'error')
            }
        )
    
    def log_solution_found(self, solution: DesignObject, step: int) -> None:
        """Log when a valid solution is found."""
        self._log_event(
            level="INFO",
            component="SEPEngine",
            event_type="solution_found",
            message=f"Valid solution found at step {step}: {solution.id}",
            data={
                "solution_id": solution.id,
                "step": step,
                "components_count": len(solution.structure.components),
                "relationships_count": len(solution.structure.relationships),
                "variables_count": len(solution.variables.assignments),
                "metadata": solution.metadata
            }
        )
    
    def log_exploration_complete(self, total_steps: int, solutions_found: int,
                               total_time: float) -> None:
        """Log exploration completion summary."""
        self._log_event(
            level="INFO",
            component="SEPEngine",
            event_type="exploration_complete",
            message=f"Exploration complete: {solutions_found} solutions found in {total_steps} steps",
            data={
                "total_steps": total_steps,
                "solutions_found": solutions_found,
                "total_time": total_time,
                "average_time_per_step": total_time / max(total_steps, 1),
                "success_rate": solutions_found / max(total_steps, 1)
            }
        )
    
    def log_error(self, component: str, error: Exception, context: Dict[str, Any] = None) -> None:
        """Log error with context information."""
        self._log_event(
            level="ERROR",
            component=component,
            event_type="error",
            message=f"Error in {component}: {str(error)}",
            data={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
                "traceback": str(error.__traceback__) if error.__traceback__ else None
            }
        )
    
    def log_performance_metric(self, component: str, metric_name: str, 
                             value: Union[int, float], unit: str = "") -> None:
        """Log performance metrics."""
        self._log_event(
            level="DEBUG",
            component=component,
            event_type="performance_metric",
            message=f"{component} {metric_name}: {value} {unit}",
            data={
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "timestamp": time.time()
            }
        )
    
    def _log_event(self, level: str, component: str, event_type: str,
                   message: str, data: Dict[str, Any]) -> None:
        """Internal method to log an event."""
        entry = LogEntry(
            timestamp=time.time(),
            level=level,
            component=component,
            event_type=event_type,
            message=message,
            data=data
        )
        
        self.entries.append(entry)
        
        # Log to standard logger
        log_method = getattr(self.logger, level.lower())
        log_method(message)
        
        # Write to file if specified
        if self.log_file:
            self._write_to_file(entry)
    
    def _write_to_file(self, entry: LogEntry) -> None:
        """Write log entry to file."""
        try:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_path, 'a') as f:
                f.write(entry.to_json() + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write to log file: {e}")
    
    def get_entries_by_component(self, component: str) -> List[LogEntry]:
        """Get all log entries for a specific component."""
        return [entry for entry in self.entries if entry.component == component]
    
    def get_entries_by_event_type(self, event_type: str) -> List[LogEntry]:
        """Get all log entries for a specific event type."""
        return [entry for entry in self.entries if entry.event_type == event_type]
    
    def get_constraint_violations(self) -> List[LogEntry]:
        """Get all constraint violation log entries."""
        return self.get_entries_by_event_type("constraint_violation")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from logged metrics."""
        performance_entries = self.get_entries_by_event_type("performance_metric")
        
        summary = {}
        for entry in performance_entries:
            component = entry.component
            metric = entry.data["metric_name"]
            value = entry.data["value"]
            
            if component not in summary:
                summary[component] = {}
            
            if metric not in summary[component]:
                summary[component][metric] = []
            
            summary[component][metric].append(value)
        
        # Calculate statistics
        for component in summary:
            for metric in summary[component]:
                values = summary[component][metric]
                summary[component][metric] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "total": sum(values)
                }
        
        return summary
    
    def export_logs(self, filename: str, format: str = "json") -> None:
        """Export all logs to a file.
        
        Args:
            filename: Output filename
            format: Export format ("json" or "csv")
        """
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "json":
            with open(output_path, 'w') as f:
                json.dump([entry.to_dict() for entry in self.entries], f, 
                         indent=2, default=str)
        elif format.lower() == "csv":
            import csv
            with open(output_path, 'w', newline='') as f:
                if self.entries:
                    fieldnames = ['timestamp', 'level', 'component', 'event_type', 'message']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for entry in self.entries:
                        row = {
                            'timestamp': datetime.fromtimestamp(entry.timestamp).isoformat(),
                            'level': entry.level,
                            'component': entry.component,
                            'event_type': entry.event_type,
                            'message': entry.message
                        }
                        writer.writerow(row)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def clear_logs(self) -> None:
        """Clear all logged entries."""
        self.entries.clear()
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Get a summary of all logged events."""
        if not self.entries:
            return {"total_entries": 0}
        
        summary = {
            "total_entries": len(self.entries),
            "time_range": {
                "start": min(entry.timestamp for entry in self.entries),
                "end": max(entry.timestamp for entry in self.entries),
                "duration": max(entry.timestamp for entry in self.entries) - 
                           min(entry.timestamp for entry in self.entries)
            },
            "by_level": {},
            "by_component": {},
            "by_event_type": {}
        }
        
        for entry in self.entries:
            # Count by level
            summary["by_level"][entry.level] = summary["by_level"].get(entry.level, 0) + 1
            
            # Count by component
            summary["by_component"][entry.component] = summary["by_component"].get(entry.component, 0) + 1
            
            # Count by event type
            summary["by_event_type"][entry.event_type] = summary["by_event_type"].get(entry.event_type, 0) + 1
        
        return summary


# Global debug logger instance
_debug_logger: Optional[DebugLogger] = None


def get_debug_logger(name: str = "SEPSolver", log_file: Optional[str] = None) -> DebugLogger:
    """Get or create the global debug logger instance."""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = DebugLogger(name, log_file)
    return _debug_logger


def setup_debug_logging(name: str = "SEPSolver", log_file: Optional[str] = None) -> DebugLogger:
    """Set up debug logging for the SEP solver."""
    global _debug_logger
    _debug_logger = DebugLogger(name, log_file)
    return _debug_logger