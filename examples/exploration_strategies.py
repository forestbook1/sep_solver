#!/usr/bin/env python3
"""
Exploration strategies comparison example for the SEP solver.

This example demonstrates different exploration strategies and compares
their performance and behavior on the same problem.
"""

import time
from typing import Dict, Any, List
from sep_solver import SEPEngine
from sep_solver.core.config import SolverConfig
from sep_solver.models.constraint_set import ConstraintSet


class StrategyComparison:
    """Class to compare different exploration strategies."""
    
    def __init__(self, schema: Dict[str, Any], constraints: ConstraintSet):
        """Initialize strategy comparison.
        
        Args:
            schema: JSON schema for design objects
            constraints: Constraint set to use
        """
        self.schema = schema
        self.constraints = constraints
        self.results = {}
    
    def run_strategy(self, strategy: str, max_iterations: int = 100, 
                    max_solutions: int = 10) -> Dict[str, Any]:
        """Run exploration with a specific strategy.
        
        Args:
            strategy: Exploration strategy name
            max_iterations: Maximum iterations
            max_solutions: Maximum solutions
            
        Returns:
            Dictionary with results
        """
        print(f"\n--- Running {strategy.upper()} strategy ---")
        
        # Create configuration for this strategy
        config = SolverConfig(
            exploration_strategy=strategy,
            max_iterations=max_iterations,
            max_solutions=max_solutions,
            enable_logging=False,  # Disable logging for cleaner output
            enable_debug_tracing=False
        )
        
        # Create engine
        engine = SEPEngine(self.schema, self.constraints, config)
        
        # Add progress reporter
        engine.create_console_progress_reporter(update_interval=2.0, show_details=True)
        
        # Track timing
        start_time = time.time()
        
        try:
            # Run exploration
            solutions = engine.solve()
            end_time = time.time()
            
            # Get final metrics
            metrics = engine.get_progress_metrics()
            stats = engine.get_solution_statistics()
            
            # Compile results
            result = {
                "strategy": strategy,
                "solutions_found": len(solutions),
                "iterations_completed": metrics["current_iteration"],
                "total_time": end_time - start_time,
                "success_rate": metrics["success_rate"],
                "iterations_per_second": metrics["iterations_per_second"],
                "solutions_per_second": metrics["solutions_per_second"],
                "average_evaluation_time": metrics["average_evaluation_time"],
                "statistics": stats,
                "solutions": solutions
            }
            
            print(f"✓ Completed: {len(solutions)} solutions in {result['total_time']:.2f}s")
            
            return result
            
        except Exception as e:
            print(f"✗ Failed: {e}")
            return {
                "strategy": strategy,
                "error": str(e),
                "solutions_found": 0,
                "total_time": time.time() - start_time
            }
    
    def compare_strategies(self, strategies: List[str], 
                          max_iterations: int = 100, 
                          max_solutions: int = 10) -> None:
        """Compare multiple exploration strategies.
        
        Args:
            strategies: List of strategy names to compare
            max_iterations: Maximum iterations per strategy
            max_solutions: Maximum solutions per strategy
        """
        self.max_iterations = max_iterations
        self.max_solutions = max_solutions
        
        print("SEP Solver - Exploration Strategies Comparison")
        print("=" * 60)
        print(f"Problem setup:")
        print(f"  Max iterations: {max_iterations}")
        print(f"  Max solutions: {max_solutions}")
        print(f"  Strategies to compare: {', '.join(strategies)}")
        
        # Run each strategy
        for strategy in strategies:
            result = self.run_strategy(strategy, max_iterations, max_solutions)
            self.results[strategy] = result
        
        # Display comparison
        self._display_comparison()
        
        # Export detailed results
        self._export_results()
    
    def _display_comparison(self) -> None:
        """Display comparison results."""
        print("\n" + "=" * 60)
        print("STRATEGY COMPARISON RESULTS")
        print("=" * 60)
        
        # Summary table
        print(f"{'Strategy':<15} {'Solutions':<10} {'Time (s)':<10} {'Success Rate':<12} {'Speed (it/s)':<12}")
        print("-" * 60)
        
        for strategy, result in self.results.items():
            if "error" not in result:
                print(f"{strategy:<15} {result['solutions_found']:<10} "
                      f"{result['total_time']:<10.2f} {result['success_rate']:<12.3f} "
                      f"{result['iterations_per_second']:<12.1f}")
            else:
                print(f"{strategy:<15} {'ERROR':<10} {result['total_time']:<10.2f} {'N/A':<12} {'N/A':<12}")
        
        # Detailed analysis
        print("\nDETAILED ANALYSIS:")
        print("-" * 30)
        
        successful_results = {k: v for k, v in self.results.items() if "error" not in v}
        
        if successful_results:
            # Best performing strategy by different metrics
            best_solutions = max(successful_results.items(), key=lambda x: x[1]['solutions_found'])
            best_time = min(successful_results.items(), key=lambda x: x[1]['total_time'])
            best_success_rate = max(successful_results.items(), key=lambda x: x[1]['success_rate'])
            best_speed = max(successful_results.items(), key=lambda x: x[1]['iterations_per_second'])
            
            print(f"🏆 Most solutions found: {best_solutions[0]} ({best_solutions[1]['solutions_found']} solutions)")
            print(f"⚡ Fastest completion: {best_time[0]} ({best_time[1]['total_time']:.2f}s)")
            print(f"🎯 Highest success rate: {best_success_rate[0]} ({best_success_rate[1]['success_rate']:.1%})")
            print(f"🚀 Highest iteration speed: {best_speed[0]} ({best_speed[1]['iterations_per_second']:.1f} it/s)")
            
            # Strategy characteristics
            print(f"\nSTRATEGY CHARACTERISTICS:")
            print("-" * 25)
            
            for strategy, result in successful_results.items():
                print(f"\n{strategy.upper()}:")
                print(f"  - Solutions: {result['solutions_found']}/{self.max_solutions}")
                print(f"  - Completion: {result['iterations_completed']}/{self.max_iterations} iterations")
                print(f"  - Efficiency: {result['success_rate']:.1%} success rate")
                print(f"  - Performance: {result['iterations_per_second']:.1f} iterations/second")
                
                if result['statistics']['total_solutions'] > 0:
                    stats = result['statistics']
                    print(f"  - Solution complexity: {stats['average_components']:.1f} components, "
                          f"{stats['average_relationships']:.1f} relationships")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        print("-" * 15)
        
        if successful_results:
            if len(successful_results) > 1:
                # Compare strategies and give recommendations
                solution_counts = [r['solutions_found'] for r in successful_results.values()]
                times = [r['total_time'] for r in successful_results.values()]
                
                if max(solution_counts) > min(solution_counts):
                    print("- For maximum solution discovery, use strategies that find more solutions")
                
                if max(times) > min(times) * 2:
                    print("- For time-critical applications, consider faster strategies")
                
                print("- For balanced performance, consider 'best_first' or 'balanced' preset")
                print("- For thorough exploration, use 'breadth_first' strategy")
                print("- For quick prototyping, use 'random' strategy")
            else:
                print("- Only one strategy completed successfully - try different configurations")
        else:
            print("- No strategies completed successfully - check problem setup and constraints")
    
    def _export_results(self) -> None:
        """Export detailed results to files."""
        import json
        
        # Export raw results
        with open("strategy_comparison_results.json", "w") as f:
            # Convert results to JSON-serializable format
            export_data = {}
            for strategy, result in self.results.items():
                export_result = result.copy()
                if "solutions" in export_result:
                    # Convert solutions to dictionaries
                    export_result["solutions"] = [sol.to_dict() for sol in export_result["solutions"]]
                export_data[strategy] = export_result
            
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"\n📁 Detailed results exported to: strategy_comparison_results.json")


def main():
    """Run exploration strategies comparison."""
    
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
                }
            },
            "variables": {
                "type": "object",
                "properties": {
                    "assignments": {"type": "object"}
                }
            }
        },
        "required": ["id", "structure", "variables"]
    }
    
    # Create empty constraint set
    constraints = ConstraintSet()
    
    # Create comparison instance
    comparison = StrategyComparison(schema, constraints)
    
    # Define strategies to compare
    strategies = ["breadth_first", "depth_first", "best_first", "random"]
    
    # Run comparison
    comparison.compare_strategies(
        strategies=strategies,
        max_iterations=80,
        max_solutions=8
    )
    
    return 0


if __name__ == "__main__":
    exit(main())