# Building System Design with SEP Solver

## Overview

This guide demonstrates how to use the SEP Solver for architectural and building system design, going beyond traditional BIM (Building Information Modeling) to include both physical and non-physical design elements.

## Why Beyond BIM?

Traditional BIM focuses primarily on physical building components (walls, floors, MEP systems). However, designers work with many non-physical concepts:

- **Functional zones** - Areas with specific purposes
- **Circulation paths** - Movement patterns and flows
- **Design intent** - Conceptual goals and principles
- **Performance requirements** - Criteria that must be met
- **Spatial relationships** - Adjacencies and connections

The SEP Solver allows you to explore designs that satisfy both physical constraints and conceptual requirements.

## Component Types

### Physical Components

#### Spaces
- `room` - Enclosed functional space
- `corridor` - Circulation space
- `lobby` - Entry/gathering space
- `stairwell` - Vertical circulation

#### Structural Elements
- `column` - Vertical support
- `beam` - Horizontal support
- `wall` - Enclosure/partition
- `floor_slab` - Horizontal surface

#### MEP Systems
- `hvac_unit` - Heating/cooling system
- `electrical_panel` - Power distribution
- `plumbing_riser` - Water distribution
- `lighting_system` - Illumination

### Non-Physical Elements

- `functional_zone` - Programmatic area definition
- `circulation_path` - Movement pattern
- `design_intent` - Conceptual goal
- `performance_requirement` - Performance criterion

## Design Constraints

### Spatial Constraints

```python
class MinimumSpacesConstraint(StructuralConstraint):
    """Ensure minimum number of space components."""
    
    def __init__(self, min_spaces: int = 3):
        self.min_spaces = min_spaces
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        space_types = ["room", "corridor", "lobby", "stairwell"]
        space_count = sum(1 for comp in design_object.structure.components 
                         if comp.type in space_types)
        return space_count >= self.min_spaces
```

### Functional Constraints

```python
class RequiredFunctionalZoneConstraint(StructuralConstraint):
    """Ensure functional zones are defined."""
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        return any(comp.type == "functional_zone" 
                  for comp in design_object.structure.components)
```

### System Constraints

```python
class MEPSystemRequirementConstraint(StructuralConstraint):
    """Ensure MEP systems are included."""
    
    def __init__(self, required_systems: List[str]):
        self.required_systems = required_systems
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        present_systems = set(comp.type for comp in design_object.structure.components 
                             if comp.type in ["hvac_unit", "electrical_panel", ...])
        return all(system in present_systems for system in self.required_systems)
```

### Balance Constraints

```python
class PhysicalNonPhysicalBalanceConstraint(StructuralConstraint):
    """Ensure balance between physical and non-physical elements."""
    
    def __init__(self, min_ratio: float = 0.3):
        self.min_ratio = min_ratio
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        physical_count = sum(1 for comp in design_object.structure.components 
                            if comp.type in physical_types)
        non_physical_count = sum(1 for comp in design_object.structure.components 
                                if comp.type in non_physical_types)
        
        total = physical_count + non_physical_count
        return (non_physical_count / total) >= self.min_ratio if total > 0 else False
```

## Example Usage

### Basic Building Design

```python
from sep_solver import SEPEngine, SolverConfig, ConstraintSet

# Create schema
schema = create_building_schema()

# Define constraints
constraints = ConstraintSet()
constraints.add_constraint(MinimumSpacesConstraint(min_spaces=2))
constraints.add_constraint(RequiredFunctionalZoneConstraint())
constraints.add_constraint(CirculationRequirementConstraint())
constraints.add_constraint(MEPSystemRequirementConstraint())
constraints.add_constraint(DesignIntentConstraint())

# Configure solver
config = SolverConfig(
    exploration_strategy="breadth_first",
    max_iterations=150,
    max_solutions=8,
    output_directory="output/building_design"
)

# Run solver
engine = SEPEngine(schema, constraints, config)
solutions = engine.solve()

# Analyze solutions
for solution in solutions:
    analysis = analyze_building_solution(solution)
    print(f"Solution: {analysis['total_components']} components")
    print(f"  Physical: {analysis['physical_components']}")
    print(f"  Non-Physical: {analysis['non_physical_components']}")
```

### Visualizing Building Designs

```python
# Create interactive dashboard
engine.create_interactive_dashboard("building_dashboard.html")

# Visualize specific solution with hierarchical layout
engine.visualize_solution_interactive(
    solution_index=0,
    output_file="building_detail.html",
    layout="hierarchical",  # Good for building hierarchies
    show_variables=False
)

# Generate statistics
engine.visualize_solution_statistics("building_stats.html")
```

## Use Cases

### 1. Early Design Exploration

Explore multiple design alternatives that satisfy:
- Spatial requirements (minimum rooms, circulation)
- Functional requirements (zones, adjacencies)
- System requirements (MEP, structure)
- Design intent (concepts, goals)

### 2. Design Validation

Verify that a design satisfies:
- Building codes and regulations
- Performance criteria
- Client requirements
- Design principles

### 3. Design Optimization

Find designs that:
- Minimize complexity
- Balance physical and conceptual elements
- Satisfy multiple competing requirements
- Optimize for specific criteria

### 4. Conceptual Design

Explore designs at a conceptual level:
- Define functional zones before spaces
- Establish circulation patterns
- Document design intent
- Set performance targets

## Advanced Patterns

### Hierarchical Design

```python
# Define hierarchy: Zone -> Spaces -> Systems
class ZoneSpaceHierarchyConstraint(StructuralConstraint):
    """Ensure zones contain spaces."""
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        # Check that functional zones have "contains" relationships to spaces
        zones = [c for c in design_object.structure.components 
                if c.type == "functional_zone"]
        
        for zone in zones:
            has_spaces = any(
                rel.source_id == zone.id and rel.type == "contains"
                for rel in design_object.structure.relationships
            )
            if not has_spaces:
                return False
        
        return True
```

### Performance-Based Design

```python
class PerformanceRequirementConstraint(StructuralConstraint):
    """Ensure performance requirements are linked to systems."""
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        # Check that performance requirements are addressed by systems
        requirements = [c for c in design_object.structure.components 
                       if c.type == "performance_requirement"]
        
        for req in requirements:
            has_system = any(
                rel.source_id == req.id and rel.type == "addressed_by"
                for rel in design_object.structure.relationships
            )
            if not has_system:
                return False
        
        return True
```

### Multi-Criteria Design

```python
# Combine multiple constraint types
constraints = ConstraintSet()

# Spatial
constraints.add_constraint(MinimumSpacesConstraint(3))
constraints.add_constraint(CirculationRequirementConstraint())

# Functional
constraints.add_constraint(RequiredFunctionalZoneConstraint())
constraints.add_constraint(DesignIntentConstraint())

# Systems
constraints.add_constraint(MEPSystemRequirementConstraint())

# Balance
constraints.add_constraint(PhysicalNonPhysicalBalanceConstraint(0.25))
constraints.add_constraint(MaximumComplexityConstraint(12))
```

## Analysis and Insights

### Component Analysis

```python
def analyze_building_solution(solution: DesignObject) -> Dict[str, Any]:
    """Analyze a building design solution."""
    
    # Count by category
    physical_comps = [c for c in solution.structure.components 
                     if c.type in physical_types]
    non_physical_comps = [c for c in solution.structure.components 
                         if c.type in non_physical_types]
    
    # Analyze relationships
    relationship_types = {}
    for rel in solution.structure.relationships:
        relationship_types[rel.type] = relationship_types.get(rel.type, 0) + 1
    
    return {
        "total_components": len(solution.structure.components),
        "physical_components": len(physical_comps),
        "non_physical_components": len(non_physical_comps),
        "relationships": len(solution.structure.relationships),
        "relationship_types": relationship_types
    }
```

### Comparative Analysis

```python
# Compare multiple solutions
all_analyses = [analyze_building_solution(sol) for sol in solutions]

# Calculate averages
avg_components = sum(a['total_components'] for a in all_analyses) / len(all_analyses)
avg_physical = sum(a['physical_components'] for a in all_analyses) / len(all_analyses)

# Find patterns
from collections import Counter
all_types = []
for sol in solutions:
    all_types.extend([c.type for c in sol.structure.components])

most_common = Counter(all_types).most_common(5)
```

## Best Practices

### 1. Start with Conceptual Elements

Define non-physical elements first:
- Functional zones
- Design intent
- Performance requirements

Then add physical components that satisfy them.

### 2. Use Hierarchical Relationships

Establish clear hierarchies:
- Zones contain spaces
- Spaces contain systems
- Requirements addressed by systems

### 3. Balance Physical and Conceptual

Maintain a good balance:
- 25-40% non-physical elements
- Document design rationale
- Link requirements to solutions

### 4. Iterate and Refine

Use the solver to:
- Explore alternatives
- Test different configurations
- Validate against requirements
- Optimize designs

### 5. Visualize Results

Use interactive visualizations to:
- Understand design structure
- Compare alternatives
- Communicate with stakeholders
- Document decisions

## Example Output

Running the building system design example generates:

```
output/building_design/
├── building_dashboard.html          # Interactive dashboard
├── building_solution_detail.html    # Detailed solution view
├── building_statistics.html         # Statistical analysis
├── building_solutions.json          # JSON export
└── building_solutions.csv           # CSV export
```

## Conclusion

The SEP Solver provides a flexible framework for building system design that:

✅ **Goes beyond BIM** - Includes non-physical design elements  
✅ **Explores alternatives** - Generates multiple valid designs  
✅ **Validates requirements** - Ensures constraints are satisfied  
✅ **Balances concerns** - Physical, functional, and conceptual  
✅ **Supports iteration** - Easy to refine and optimize  
✅ **Visualizes results** - Interactive exploration of designs  

This approach enables designers to work at multiple levels of abstraction, from high-level concepts to detailed physical systems, all within a unified framework.

## Running the Example

```bash
# Run the building system design example
python examples/building_system_design.py

# View the results
open output/building_design/building_dashboard.html
```

The example will:
1. Define building component types and constraints
2. Explore design alternatives
3. Analyze solutions
4. Generate visualizations
5. Export results

Explore the generated visualizations to see how physical and non-physical elements work together in valid building designs!
