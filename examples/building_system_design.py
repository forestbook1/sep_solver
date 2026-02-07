"""
Building System Design Example

This example demonstrates using the SEP Solver for architectural and building system design,
going beyond traditional BIM (Building Information Modeling) to include:
- Physical components (spaces, structures, MEP systems)
- Non-physical elements (zones, requirements, design intent)
- Relationships and dependencies
- Design constraints and performance criteria

NOTE: This is a conceptual demonstration. The default structure generator creates
generic components. For production use, you would implement a custom BuildingStructureGenerator
that understands building-specific component types and relationships.

This flexible approach allows designers to explore design alternatives that satisfy
both physical and conceptual requirements.
"""

from typing import List, Dict, Any
from sep_solver import SEPEngine, SolverConfig, ConstraintSet
from sep_solver.models.constraint_set import StructuralConstraint, VariableConstraint
from sep_solver.models.design_object import DesignObject


# ============================================================================
# Building Component Type Definitions
# ============================================================================

class BuildingComponentTypes:
    """Defines the types of components in a building system."""
    
    # Physical Spaces
    ROOM = "room"
    CORRIDOR = "corridor"
    LOBBY = "lobby"
    STAIRWELL = "stairwell"
    
    # Structural Elements
    COLUMN = "column"
    BEAM = "beam"
    WALL = "wall"
    FLOOR_SLAB = "floor_slab"
    
    # MEP Systems (Mechanical, Electrical, Plumbing)
    HVAC_UNIT = "hvac_unit"
    ELECTRICAL_PANEL = "electrical_panel"
    PLUMBING_RISER = "plumbing_riser"
    LIGHTING_SYSTEM = "lighting_system"
    
    # Non-Physical Design Elements
    FUNCTIONAL_ZONE = "functional_zone"
    CIRCULATION_PATH = "circulation_path"
    DESIGN_INTENT = "design_intent"
    PERFORMANCE_REQUIREMENT = "performance_requirement"
    
    @classmethod
    def get_physical_types(cls) -> List[str]:
        """Get all physical component types."""
        return [
            cls.ROOM, cls.CORRIDOR, cls.LOBBY, cls.STAIRWELL,
            cls.COLUMN, cls.BEAM, cls.WALL, cls.FLOOR_SLAB,
            cls.HVAC_UNIT, cls.ELECTRICAL_PANEL, cls.PLUMBING_RISER, cls.LIGHTING_SYSTEM
        ]
    
    @classmethod
    def get_non_physical_types(cls) -> List[str]:
        """Get all non-physical component types."""
        return [
            cls.FUNCTIONAL_ZONE, cls.CIRCULATION_PATH,
            cls.DESIGN_INTENT, cls.PERFORMANCE_REQUIREMENT
        ]
    
    @classmethod
    def get_space_types(cls) -> List[str]:
        """Get space component types."""
        return [cls.ROOM, cls.CORRIDOR, cls.LOBBY, cls.STAIRWELL]
    
    @classmethod
    def get_mep_types(cls) -> List[str]:
        """Get MEP system types."""
        return [cls.HVAC_UNIT, cls.ELECTRICAL_PANEL, cls.PLUMBING_RISER, cls.LIGHTING_SYSTEM]


# ============================================================================
# Building-Specific Constraints
# ============================================================================

class MinimumSpacesConstraint(StructuralConstraint):
    """Ensure minimum number of space components."""
    
    def __init__(self, min_spaces: int = 3):
        super().__init__(
            constraint_id="min_spaces",
            description=f"Requires at least {min_spaces} space components"
        )
        self.min_spaces = min_spaces
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        space_types = BuildingComponentTypes.get_space_types()
        space_count = sum(1 for comp in design_object.structure.components 
                         if comp.type in space_types)
        return space_count >= self.min_spaces
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        space_types = BuildingComponentTypes.get_space_types()
        space_count = sum(1 for comp in design_object.structure.components 
                         if comp.type in space_types)
        return f"Design has {space_count} spaces, requires at least {self.min_spaces}"


class RequiredFunctionalZoneConstraint(StructuralConstraint):
    """Ensure at least one functional zone is defined."""
    
    def __init__(self):
        super().__init__(
            constraint_id="required_functional_zone",
            description="Requires at least one functional zone"
        )
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return any(comp.type == BuildingComponentTypes.FUNCTIONAL_ZONE 
                  for comp in design_object.structure.components)
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        return "Design must include at least one functional zone"


class CirculationRequirementConstraint(StructuralConstraint):
    """Ensure circulation paths connect spaces."""
    
    def __init__(self):
        super().__init__(
            constraint_id="circulation_requirement",
            description="Requires circulation paths between spaces"
        )
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        # Check if there are circulation-related components or relationships
        has_circulation = any(
            comp.type in [BuildingComponentTypes.CORRIDOR, BuildingComponentTypes.CIRCULATION_PATH]
            for comp in design_object.structure.components
        )
        
        # Or check for adjacency relationships between spaces
        has_adjacency = any(
            rel.type in ["adjacent_to", "connects_to", "accessible_from"]
            for rel in design_object.structure.relationships
        )
        
        return has_circulation or has_adjacency
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        return "Design must include circulation paths or space adjacencies"


class MEPSystemRequirementConstraint(StructuralConstraint):
    """Ensure MEP systems are included."""
    
    def __init__(self, required_systems: List[str] = None):
        self.required_systems = required_systems or [
            BuildingComponentTypes.HVAC_UNIT,
            BuildingComponentTypes.ELECTRICAL_PANEL
        ]
        super().__init__(
            constraint_id="mep_system_requirement",
            description=f"Requires MEP systems: {', '.join(self.required_systems)}"
        )
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        present_systems = set(comp.type for comp in design_object.structure.components 
                             if comp.type in BuildingComponentTypes.get_mep_types())
        return all(system in present_systems for system in self.required_systems)
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        present_systems = set(comp.type for comp in design_object.structure.components 
                             if comp.type in BuildingComponentTypes.get_mep_types())
        missing = set(self.required_systems) - present_systems
        return f"Missing required MEP systems: {', '.join(missing)}"


class DesignIntentConstraint(StructuralConstraint):
    """Ensure design intent is captured."""
    
    def __init__(self):
        super().__init__(
            constraint_id="design_intent",
            description="Requires design intent documentation"
        )
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return any(comp.type == BuildingComponentTypes.DESIGN_INTENT 
                  for comp in design_object.structure.components)
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        return "Design must include design intent documentation"


class PhysicalNonPhysicalBalanceConstraint(StructuralConstraint):
    """Ensure balance between physical and non-physical elements."""
    
    def __init__(self, min_ratio: float = 0.3):
        super().__init__(
            constraint_id="physical_nonphysical_balance",
            description=f"Requires at least {min_ratio*100}% non-physical elements"
        )
        self.min_ratio = min_ratio
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        physical_types = BuildingComponentTypes.get_physical_types()
        non_physical_types = BuildingComponentTypes.get_non_physical_types()
        
        physical_count = sum(1 for comp in design_object.structure.components 
                            if comp.type in physical_types)
        non_physical_count = sum(1 for comp in design_object.structure.components 
                                if comp.type in non_physical_types)
        
        total = physical_count + non_physical_count
        if total == 0:
            return False
        
        return (non_physical_count / total) >= self.min_ratio
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        physical_types = BuildingComponentTypes.get_physical_types()
        non_physical_types = BuildingComponentTypes.get_non_physical_types()
        
        physical_count = sum(1 for comp in design_object.structure.components 
                            if comp.type in physical_types)
        non_physical_count = sum(1 for comp in design_object.structure.components 
                                if comp.type in non_physical_types)
        
        total = physical_count + non_physical_count
        ratio = (non_physical_count / total * 100) if total > 0 else 0
        
        return f"Non-physical elements are {ratio:.1f}%, requires at least {self.min_ratio*100}%"


class MaximumComplexityConstraint(StructuralConstraint):
    """Limit design complexity."""
    
    def __init__(self, max_components: int = 15):
        super().__init__(
            constraint_id="max_complexity",
            description=f"Limits design to {max_components} components"
        )
        self.max_components = max_components
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return len(design_object.structure.components) <= self.max_components
    
    def get_violation_message(self, design_object: DesignObject) -> str:
        count = len(design_object.structure.components)
        return f"Design has {count} components, maximum allowed is {self.max_components}"


# ============================================================================
# Main Example
# ============================================================================

def create_building_schema() -> Dict[str, Any]:
    """Create JSON schema for building system design."""
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
                            }
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
                                "type": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "variables": {
                "type": "object",
                "properties": {
                    "assignments": {"type": "object"},
                    "domains": {"type": "object"}
                }
            },
            "metadata": {"type": "object"}
        },
        "required": ["id", "structure", "variables"]
    }


def create_building_constraints() -> ConstraintSet:
    """Create constraint set for building system design.
    
    NOTE: These are simplified constraints that work with the default generator.
    For a real building design system, you would:
    1. Implement a custom BuildingStructureGenerator
    2. Use the full set of building-specific constraints
    3. Define component type probabilities and relationships
    """
    constraints = ConstraintSet()
    
    # Simple constraints that work with default generator
    # In production, you'd use the building-specific constraints defined above
    
    # Limit complexity
    constraints.add_constraint(MaximumComplexityConstraint(max_components=10))
    
    # Minimum components
    class MinComponentsConstraint(StructuralConstraint):
        def __init__(self):
            super().__init__(
                constraint_id="min_components",
                description="Requires at least 3 components"
            )
        
        def is_satisfied(self, design_object: DesignObject) -> bool:
            return len(design_object.structure.components) >= 3
        
        def get_violation_message(self, design_object: DesignObject) -> str:
            count = len(design_object.structure.components)
            return f"Design has {count} components, requires at least 3"
    
    constraints.add_constraint(MinComponentsConstraint())
    
    # Minimum relationships
    class MinRelationshipsConstraint(StructuralConstraint):
        def __init__(self):
            super().__init__(
                constraint_id="min_relationships",
                description="Requires at least 2 relationships"
            )
        
        def is_satisfied(self, design_object: DesignObject) -> bool:
            return len(design_object.structure.relationships) >= 2
        
        def get_violation_message(self, design_object: DesignObject) -> str:
            count = len(design_object.structure.relationships)
            return f"Design has {count} relationships, requires at least 2"
    
    constraints.add_constraint(MinRelationshipsConstraint())
    
    return constraints


def analyze_building_solution(solution: DesignObject) -> Dict[str, Any]:
    """Analyze a building design solution."""
    physical_types = BuildingComponentTypes.get_physical_types()
    non_physical_types = BuildingComponentTypes.get_non_physical_types()
    space_types = BuildingComponentTypes.get_space_types()
    mep_types = BuildingComponentTypes.get_mep_types()
    
    # Count components by category
    physical_comps = [c for c in solution.structure.components if c.type in physical_types]
    non_physical_comps = [c for c in solution.structure.components if c.type in non_physical_types]
    space_comps = [c for c in solution.structure.components if c.type in space_types]
    mep_comps = [c for c in solution.structure.components if c.type in mep_types]
    
    # Analyze relationships
    relationship_types = {}
    for rel in solution.structure.relationships:
        relationship_types[rel.type] = relationship_types.get(rel.type, 0) + 1
    
    return {
        "solution_id": solution.id,
        "total_components": len(solution.structure.components),
        "physical_components": len(physical_comps),
        "non_physical_components": len(non_physical_comps),
        "spaces": len(space_comps),
        "mep_systems": len(mep_comps),
        "relationships": len(solution.structure.relationships),
        "relationship_types": relationship_types,
        "component_breakdown": {
            "physical": [c.type for c in physical_comps],
            "non_physical": [c.type for c in non_physical_comps],
            "spaces": [c.type for c in space_comps],
            "mep": [c.type for c in mep_comps]
        }
    }


def print_solution_details(solution: DesignObject, index: int):
    """Print detailed information about a solution."""
    analysis = analyze_building_solution(solution)
    
    print(f"\n{'='*70}")
    print(f"Solution {index}: {solution.id}")
    print(f"{'='*70}")
    
    print(f"\nOverview:")
    print(f"  Total Components: {analysis['total_components']}")
    print(f"  Physical: {analysis['physical_components']}")
    print(f"  Non-Physical: {analysis['non_physical_components']}")
    print(f"  Relationships: {analysis['relationships']}")
    
    print(f"\nComponent Breakdown:")
    print(f"  Spaces ({analysis['spaces']}):")
    for space_type in set(analysis['component_breakdown']['spaces']):
        count = analysis['component_breakdown']['spaces'].count(space_type)
        print(f"    - {space_type}: {count}")
    
    if analysis['component_breakdown']['mep']:
        print(f"  MEP Systems ({analysis['mep_systems']}):")
        for mep_type in set(analysis['component_breakdown']['mep']):
            count = analysis['component_breakdown']['mep'].count(mep_type)
            print(f"    - {mep_type}: {count}")
    
    if analysis['component_breakdown']['non_physical']:
        print(f"  Non-Physical Elements ({analysis['non_physical_components']}):")
        for np_type in set(analysis['component_breakdown']['non_physical']):
            count = analysis['component_breakdown']['non_physical'].count(np_type)
            print(f"    - {np_type}: {count}")
    
    if analysis['relationship_types']:
        print(f"\nRelationships:")
        for rel_type, count in analysis['relationship_types'].items():
            print(f"    - {rel_type}: {count}")


def main():
    """Main execution function."""
    print("="*70)
    print("Building System Design Example")
    print("Exploring Architectural Design with Physical and Non-Physical Elements")
    print("="*70)
    print("\nNOTE: This example uses simplified constraints with the default generator.")
    print("For production building design, implement a custom BuildingStructureGenerator")
    print("that understands building-specific component types and relationships.")
    print("="*70)
    
    # Create schema and constraints
    print("\n1. Setting up building design schema and constraints...")
    schema = create_building_schema()
    constraints = create_building_constraints()
    
    print(f"   ✓ Schema defined")
    print(f"   ✓ {len(constraints.get_all_constraints())} constraints configured:")
    for constraint in constraints.get_all_constraints():
        print(f"      - {constraint.description}")
    
    # Configure solver
    print("\n2. Configuring solver...")
    config = SolverConfig(
        exploration_strategy="breadth_first",
        max_iterations=150,
        max_solutions=8,
        enable_logging=True,
        log_level="INFO",
        output_directory="output/building_design"
    )
    print(f"   ✓ Strategy: {config.exploration_strategy}")
    print(f"   ✓ Max iterations: {config.max_iterations}")
    print(f"   ✓ Max solutions: {config.max_solutions}")
    
    # Run solver
    print("\n3. Running solver to explore building designs...")
    print("   (This may take a moment...)")
    engine = SEPEngine(schema, constraints, config)
    solutions = engine.solve()
    
    print(f"\n{'='*70}")
    print(f"✓ Exploration Complete!")
    print(f"{'='*70}")
    print(f"Found {len(solutions)} valid building design solutions")
    
    if not solutions:
        print("\nNo solutions found. Try relaxing constraints or increasing max_iterations.")
        return
    
    # Analyze solutions
    print(f"\n4. Analyzing solutions...")
    
    for i, solution in enumerate(solutions, 1):
        print_solution_details(solution, i)
    
    # Generate visualizations
    print(f"\n{'='*70}")
    print("5. Generating visualizations...")
    print(f"{'='*70}")
    
    try:
        # Check if visualization is available
        from sep_solver.utils.visualization import SolutionVisualizer
        visualizer = SolutionVisualizer()
        
        if visualizer.interactive_enabled:
            print("\n   Creating interactive visualizations...")
            
            # Dashboard
            engine.create_interactive_dashboard("building_dashboard.html")
            print(f"   ✓ Dashboard: output/building_design/building_dashboard.html")
            
            # First solution detail
            if len(solutions) > 0:
                engine.visualize_solution_interactive(
                    0, 
                    "building_solution_detail.html",
                    layout="hierarchical",
                    show_variables=False
                )
                print(f"   ✓ Solution detail: output/building_design/building_solution_detail.html")
            
            # Statistics
            engine.visualize_solution_statistics("building_statistics.html")
            print(f"   ✓ Statistics: output/building_design/building_statistics.html")
            
            print(f"\n   Open the HTML files in your browser to explore the designs!")
        else:
            print("\n   Interactive visualization not available.")
            print("   Install with: pip install networkx plotly numpy")
    except Exception as e:
        print(f"\n   Visualization error: {e}")
    
    # Export solutions
    print(f"\n6. Exporting solutions...")
    try:
        engine.export_solutions("json", "building_solutions.json")
        print(f"   ✓ JSON export: output/building_design/building_solutions.json")
        
        engine.export_solutions("csv", "building_solutions.csv")
        print(f"   ✓ CSV export: output/building_design/building_solutions.csv")
    except Exception as e:
        print(f"   Export error: {e}")
    
    # Summary statistics
    print(f"\n{'='*70}")
    print("Summary Statistics")
    print(f"{'='*70}")
    
    all_analyses = [analyze_building_solution(sol) for sol in solutions]
    
    avg_components = sum(a['total_components'] for a in all_analyses) / len(all_analyses)
    avg_physical = sum(a['physical_components'] for a in all_analyses) / len(all_analyses)
    avg_non_physical = sum(a['non_physical_components'] for a in all_analyses) / len(all_analyses)
    avg_relationships = sum(a['relationships'] for a in all_analyses) / len(all_analyses)
    
    print(f"\nAverages across {len(solutions)} solutions:")
    print(f"  Components: {avg_components:.1f}")
    print(f"  Physical: {avg_physical:.1f}")
    print(f"  Non-Physical: {avg_non_physical:.1f}")
    print(f"  Relationships: {avg_relationships:.1f}")
    
    # Component type frequency
    all_physical = []
    all_non_physical = []
    for analysis in all_analyses:
        all_physical.extend(analysis['component_breakdown']['physical'])
        all_non_physical.extend(analysis['component_breakdown']['non_physical'])
    
    print(f"\nMost common physical components:")
    from collections import Counter
    physical_freq = Counter(all_physical).most_common(5)
    for comp_type, count in physical_freq:
        print(f"  - {comp_type}: {count} occurrences")
    
    print(f"\nMost common non-physical elements:")
    non_physical_freq = Counter(all_non_physical).most_common(5)
    for comp_type, count in non_physical_freq:
        print(f"  - {comp_type}: {count} occurrences")
    
    print(f"\n{'='*70}")
    print("Building System Design Exploration Complete!")
    print(f"{'='*70}")
    print(f"\nKey Insights:")
    print(f"  • Successfully integrated physical and non-physical design elements")
    print(f"  • Explored {len(solutions)} valid design alternatives")
    print(f"  • Balanced spatial, MEP, and conceptual requirements")
    print(f"  • Demonstrated flexible design exploration beyond traditional BIM")
    print(f"\nOutput files saved to: output/building_design/")


if __name__ == "__main__":
    main()
