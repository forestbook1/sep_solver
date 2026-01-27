"""Progress reporting utilities for the SEP solver."""

import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


@dataclass
class ProgressMetrics:
    """Metrics for tracking exploration progress."""
    
    # Basic progress
    current_iteration: int = 0
    total_iterations: int = 0
    solutions_found: int = 0
    target_solutions: int = 0
    candidates_evaluated: int = 0
    
    # Timing information
    start_time: Optional[datetime] = None
    current_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    # Performance metrics
    iterations_per_second: float = 0.0
    solutions_per_second: float = 0.0
    average_evaluation_time: float = 0.0
    
    # Quality metrics
    success_rate: float = 0.0
    constraint_violation_rate: float = 0.0
    
    # Resource usage
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "current_iteration": self.current_iteration,
            "total_iterations": self.total_iterations,
            "solutions_found": self.solutions_found,
            "target_solutions": self.target_solutions,
            "candidates_evaluated": self.candidates_evaluated,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "current_time": self.current_time.isoformat() if self.current_time else None,
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "iterations_per_second": self.iterations_per_second,
            "solutions_per_second": self.solutions_per_second,
            "average_evaluation_time": self.average_evaluation_time,
            "success_rate": self.success_rate,
            "constraint_violation_rate": self.constraint_violation_rate,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent
        }
    
    def get_progress_percentage(self) -> float:
        """Get progress as percentage (0-100)."""
        if self.total_iterations <= 0:
            return 0.0
        return min(100.0, (self.current_iteration / self.total_iterations) * 100.0)
    
    def get_elapsed_time(self) -> Optional[timedelta]:
        """Get elapsed time since start."""
        if self.start_time is None or self.current_time is None:
            return None
        return self.current_time - self.start_time
    
    def get_remaining_time(self) -> Optional[timedelta]:
        """Get estimated remaining time."""
        if self.estimated_completion is None or self.current_time is None:
            return None
        return self.estimated_completion - self.current_time


class ProgressReporter(ABC):
    """Abstract base class for progress reporters."""
    
    @abstractmethod
    def report_progress(self, metrics: ProgressMetrics) -> None:
        """Report progress with current metrics.
        
        Args:
            metrics: Current progress metrics
        """
        pass
    
    @abstractmethod
    def report_start(self, total_iterations: int, target_solutions: int) -> None:
        """Report exploration start.
        
        Args:
            total_iterations: Total iterations planned
            target_solutions: Target number of solutions
        """
        pass
    
    @abstractmethod
    def report_completion(self, metrics: ProgressMetrics, success: bool) -> None:
        """Report exploration completion.
        
        Args:
            metrics: Final progress metrics
            success: Whether exploration completed successfully
        """
        pass
    
    @abstractmethod
    def report_solution_found(self, solution_count: int, solution_id: str) -> None:
        """Report that a solution was found.
        
        Args:
            solution_count: Total solutions found so far
            solution_id: ID of the solution that was found
        """
        pass


class ConsoleProgressReporter(ProgressReporter):
    """Progress reporter that outputs to console."""
    
    def __init__(self, update_interval: float = 1.0, show_details: bool = True):
        """Initialize console progress reporter.
        
        Args:
            update_interval: Minimum seconds between progress updates
            show_details: Whether to show detailed metrics
        """
        self.update_interval = update_interval
        self.show_details = show_details
        self.last_update_time = 0.0
    
    def report_progress(self, metrics: ProgressMetrics) -> None:
        """Report progress to console."""
        current_time = time.time()
        
        # Throttle updates based on interval
        if current_time - self.last_update_time < self.update_interval:
            return
        
        self.last_update_time = current_time
        
        # Basic progress line
        progress_pct = metrics.get_progress_percentage()
        bar_length = 40
        filled_length = int(bar_length * progress_pct / 100)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f"\rProgress: |{bar}| {progress_pct:.1f}% "
              f"({metrics.current_iteration}/{metrics.total_iterations}) "
              f"Solutions: {metrics.solutions_found}/{metrics.target_solutions}", end='')
        
        # Detailed metrics on new line
        if self.show_details:
            elapsed = metrics.get_elapsed_time()
            remaining = metrics.get_remaining_time()
            
            details = []
            if elapsed:
                details.append(f"Elapsed: {self._format_duration(elapsed)}")
            if remaining:
                details.append(f"Remaining: {self._format_duration(remaining)}")
            if metrics.iterations_per_second > 0:
                details.append(f"Speed: {metrics.iterations_per_second:.1f} iter/s")
            if metrics.success_rate > 0:
                details.append(f"Success: {metrics.success_rate:.1%}")
            
            if details:
                print(f"\n{' | '.join(details)}", end='')
    
    def report_start(self, total_iterations: int, target_solutions: int) -> None:
        """Report exploration start."""
        print(f"\nStarting exploration: {total_iterations} iterations, target {target_solutions} solutions")
        print("=" * 80)
    
    def report_completion(self, metrics: ProgressMetrics, success: bool) -> None:
        """Report exploration completion."""
        print("\n" + "=" * 80)
        status = "COMPLETED" if success else "TERMINATED"
        print(f"Exploration {status}")
        print(f"Solutions found: {metrics.solutions_found}/{metrics.target_solutions}")
        print(f"Iterations completed: {metrics.current_iteration}/{metrics.total_iterations}")
        
        elapsed = metrics.get_elapsed_time()
        if elapsed:
            print(f"Total time: {self._format_duration(elapsed)}")
        
        if metrics.success_rate > 0:
            print(f"Success rate: {metrics.success_rate:.1%}")
    
    def report_solution_found(self, solution_count: int, solution_id: str) -> None:
        """Report solution found."""
        print(f"\n✓ Solution {solution_count} found: {solution_id}")
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format duration for display."""
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


class CallbackProgressReporter(ProgressReporter):
    """Progress reporter that calls user-provided callbacks."""
    
    def __init__(self):
        """Initialize callback progress reporter."""
        self.progress_callbacks: List[Callable[[ProgressMetrics], None]] = []
        self.start_callbacks: List[Callable[[int, int], None]] = []
        self.completion_callbacks: List[Callable[[ProgressMetrics, bool], None]] = []
        self.solution_callbacks: List[Callable[[int, str], None]] = []
    
    def add_progress_callback(self, callback: Callable[[ProgressMetrics], None]) -> None:
        """Add a progress update callback."""
        self.progress_callbacks.append(callback)
    
    def add_start_callback(self, callback: Callable[[int, int], None]) -> None:
        """Add an exploration start callback."""
        self.start_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable[[ProgressMetrics, bool], None]) -> None:
        """Add an exploration completion callback."""
        self.completion_callbacks.append(callback)
    
    def add_solution_callback(self, callback: Callable[[int, str], None]) -> None:
        """Add a solution found callback."""
        self.solution_callbacks.append(callback)
    
    def report_progress(self, metrics: ProgressMetrics) -> None:
        """Report progress via callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(metrics)
            except Exception:
                # Don't let callback errors break progress reporting
                pass
    
    def report_start(self, total_iterations: int, target_solutions: int) -> None:
        """Report exploration start via callbacks."""
        for callback in self.start_callbacks:
            try:
                callback(total_iterations, target_solutions)
            except Exception:
                pass
    
    def report_completion(self, metrics: ProgressMetrics, success: bool) -> None:
        """Report exploration completion via callbacks."""
        for callback in self.completion_callbacks:
            try:
                callback(metrics, success)
            except Exception:
                pass
    
    def report_solution_found(self, solution_count: int, solution_id: str) -> None:
        """Report solution found via callbacks."""
        for callback in self.solution_callbacks:
            try:
                callback(solution_count, solution_id)
            except Exception:
                pass


class FileProgressReporter(ProgressReporter):
    """Progress reporter that writes to a file."""
    
    def __init__(self, filename: str, format: str = "json"):
        """Initialize file progress reporter.
        
        Args:
            filename: Output filename
            format: Output format ("json" or "csv")
        """
        self.filename = filename
        self.format = format.lower()
        self.entries: List[Dict[str, Any]] = []
    
    def report_progress(self, metrics: ProgressMetrics) -> None:
        """Report progress to file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "progress",
            "metrics": metrics.to_dict()
        }
        self.entries.append(entry)
        self._write_to_file()
    
    def report_start(self, total_iterations: int, target_solutions: int) -> None:
        """Report exploration start to file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "start",
            "total_iterations": total_iterations,
            "target_solutions": target_solutions
        }
        self.entries.append(entry)
        self._write_to_file()
    
    def report_completion(self, metrics: ProgressMetrics, success: bool) -> None:
        """Report exploration completion to file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "completion",
            "success": success,
            "final_metrics": metrics.to_dict()
        }
        self.entries.append(entry)
        self._write_to_file()
    
    def report_solution_found(self, solution_count: int, solution_id: str) -> None:
        """Report solution found to file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "solution_found",
            "solution_count": solution_count,
            "solution_id": solution_id
        }
        self.entries.append(entry)
        self._write_to_file()
    
    def _write_to_file(self) -> None:
        """Write entries to file."""
        try:
            if self.format == "json":
                import json
                with open(self.filename, 'w') as f:
                    json.dump(self.entries, f, indent=2, default=str)
            elif self.format == "csv":
                import csv
                if self.entries:
                    # Flatten the data for CSV
                    flattened_entries = []
                    for entry in self.entries:
                        flat_entry = {
                            "timestamp": entry["timestamp"],
                            "event_type": entry["event_type"]
                        }
                        
                        # Add metrics if present
                        if "metrics" in entry:
                            flat_entry.update(entry["metrics"])
                        
                        # Add other fields
                        for key, value in entry.items():
                            if key not in ["timestamp", "event_type", "metrics"]:
                                flat_entry[key] = value
                        
                        flattened_entries.append(flat_entry)
                    
                    # Write CSV
                    with open(self.filename, 'w', newline='') as f:
                        if flattened_entries:
                            fieldnames = set()
                            for entry in flattened_entries:
                                fieldnames.update(entry.keys())
                            
                            writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                            writer.writeheader()
                            writer.writerows(flattened_entries)
        except Exception:
            # Don't let file writing errors break progress reporting
            pass


class CompositeProgressReporter(ProgressReporter):
    """Progress reporter that combines multiple reporters."""
    
    def __init__(self, reporters: List[ProgressReporter] = None):
        """Initialize composite progress reporter.
        
        Args:
            reporters: List of reporters to combine
        """
        self.reporters = reporters or []
    
    def add_reporter(self, reporter: ProgressReporter) -> None:
        """Add a reporter to the composite."""
        self.reporters.append(reporter)
    
    def remove_reporter(self, reporter: ProgressReporter) -> None:
        """Remove a reporter from the composite."""
        try:
            self.reporters.remove(reporter)
        except ValueError:
            pass
    
    def report_progress(self, metrics: ProgressMetrics) -> None:
        """Report progress to all reporters."""
        for reporter in self.reporters:
            try:
                reporter.report_progress(metrics)
            except Exception:
                pass
    
    def report_start(self, total_iterations: int, target_solutions: int) -> None:
        """Report exploration start to all reporters."""
        for reporter in self.reporters:
            try:
                reporter.report_start(total_iterations, target_solutions)
            except Exception:
                pass
    
    def report_completion(self, metrics: ProgressMetrics, success: bool) -> None:
        """Report exploration completion to all reporters."""
        for reporter in self.reporters:
            try:
                reporter.report_completion(metrics, success)
            except Exception:
                pass
    
    def report_solution_found(self, solution_count: int, solution_id: str) -> None:
        """Report solution found to all reporters."""
        for reporter in self.reporters:
            try:
                reporter.report_solution_found(solution_count, solution_id)
            except Exception:
                pass


class ProgressTracker:
    """Tracks and calculates progress metrics during exploration."""
    
    def __init__(self):
        """Initialize progress tracker."""
        self.metrics = ProgressMetrics()
        self.reporters: List[ProgressReporter] = []
        self.evaluation_times: List[float] = []
        self.violation_count = 0
        self.last_update_time = 0.0
        self.update_interval = 0.5  # Update every 0.5 seconds
    
    def add_reporter(self, reporter: ProgressReporter) -> None:
        """Add a progress reporter."""
        self.reporters.append(reporter)
    
    def start_exploration(self, total_iterations: int, target_solutions: int) -> None:
        """Start tracking exploration progress."""
        self.metrics.start_time = datetime.now()
        self.metrics.current_time = self.metrics.start_time
        self.metrics.total_iterations = total_iterations
        self.metrics.target_solutions = target_solutions
        self.metrics.current_iteration = 0
        self.metrics.solutions_found = 0
        self.metrics.candidates_evaluated = 0
        
        # Notify reporters
        for reporter in self.reporters:
            reporter.report_start(total_iterations, target_solutions)
    
    def update_iteration(self, iteration: int) -> None:
        """Update current iteration."""
        self.metrics.current_iteration = iteration
        self.metrics.current_time = datetime.now()
        self._update_calculated_metrics()
        self._report_progress()
    
    def record_candidate_evaluation(self, evaluation_time: float, is_valid: bool) -> None:
        """Record evaluation of a candidate."""
        self.metrics.candidates_evaluated += 1
        self.evaluation_times.append(evaluation_time)
        
        if not is_valid:
            self.violation_count += 1
        
        self._update_calculated_metrics()
    
    def record_solution_found(self, solution_id: str) -> None:
        """Record that a solution was found."""
        self.metrics.solutions_found += 1
        
        # Notify reporters
        for reporter in self.reporters:
            reporter.report_solution_found(self.metrics.solutions_found, solution_id)
        
        self._update_calculated_metrics()
        self._report_progress()
    
    def complete_exploration(self, success: bool = True) -> None:
        """Complete exploration tracking."""
        self.metrics.current_time = datetime.now()
        self._update_calculated_metrics()
        
        # Notify reporters
        for reporter in self.reporters:
            reporter.report_completion(self.metrics, success)
    
    def _update_calculated_metrics(self) -> None:
        """Update calculated metrics."""
        if self.metrics.start_time and self.metrics.current_time:
            elapsed = (self.metrics.current_time - self.metrics.start_time).total_seconds()
            
            if elapsed > 0:
                self.metrics.iterations_per_second = self.metrics.current_iteration / elapsed
                self.metrics.solutions_per_second = self.metrics.solutions_found / elapsed
        
        # Average evaluation time
        if self.evaluation_times:
            self.metrics.average_evaluation_time = sum(self.evaluation_times) / len(self.evaluation_times)
        
        # Success rate
        if self.metrics.candidates_evaluated > 0:
            self.metrics.success_rate = self.metrics.solutions_found / self.metrics.candidates_evaluated
            self.metrics.constraint_violation_rate = self.violation_count / self.metrics.candidates_evaluated
        
        # Estimate completion time
        if (self.metrics.iterations_per_second > 0 and 
            self.metrics.current_iteration < self.metrics.total_iterations):
            remaining_iterations = self.metrics.total_iterations - self.metrics.current_iteration
            remaining_seconds = remaining_iterations / self.metrics.iterations_per_second
            self.metrics.estimated_completion = self.metrics.current_time + timedelta(seconds=remaining_seconds)
        
        # Resource usage (basic implementation)
        try:
            import psutil
            process = psutil.Process()
            self.metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            self.metrics.cpu_usage_percent = process.cpu_percent()
        except ImportError:
            # psutil not available
            pass
    
    def _report_progress(self) -> None:
        """Report progress if enough time has elapsed."""
        current_time = time.time()
        
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time
            
            for reporter in self.reporters:
                reporter.report_progress(self.metrics)
    
    def get_current_metrics(self) -> ProgressMetrics:
        """Get current progress metrics."""
        self._update_calculated_metrics()
        return self.metrics


# Convenience functions
def create_console_reporter(update_interval: float = 1.0, show_details: bool = True) -> ConsoleProgressReporter:
    """Create a console progress reporter."""
    return ConsoleProgressReporter(update_interval, show_details)


def create_file_reporter(filename: str, format: str = "json") -> FileProgressReporter:
    """Create a file progress reporter."""
    return FileProgressReporter(filename, format)


def create_callback_reporter() -> CallbackProgressReporter:
    """Create a callback progress reporter."""
    return CallbackProgressReporter()