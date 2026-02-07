# Building System Design Example

## Overview

This example demonstrates how to use the SEP Solver for architectural and building system design that goes beyond traditional BIM (Building Information Modeling).

## What's Included

### Component Types Defined

**Physical Components:**
- Spaces: room, corridor, lobby, stairwell
- Structure: column, beam, wall, floor_slab
- MEP Systems: hvac_unit, electrical_panel, plumbing_riser, lighting_system

**Non-Physical Elements:**
- functional_zone - Programmatic area definitions
- circulation_path - Movement patterns
- design_intent - Conceptual goals
- performance_requirement - Performance criteria

### Constraints Demonstrated

- `MinimumSpacesConstraint` - Ensure adequate spaces
- `RequiredFunctionalZoneConstraint` - Require functional zones
- `CirculationRequirementConstraint` - Ensure circulation paths
- `MEPSystemRequirementConstraint` - Require MEP systems
- `DesignIntentConstraint` - Capture design intent
- `PhysicalNonPhysicalBalanceConstraint` - Balance physical/conceptual
- `MaximumComplexityConstraint` - Limit design complexity

## Running the Example

```bash
python examples/building_system_design.py
```

This will:
1. Define building component types and constraints
2. Explore design alternatives
3. Analyze solutions
4. Generate interactive visualizations
5. Export results to JSON and CSV

## Output

Files are saved to `output/building_design/`:
- `building_dashboard.html` - Interactive dashboard
- `building_solution_detail.html` - Detailed solution view
- `building_statistics.html` - Statistical analysis
- `building_solutions.json` - JSON export
- `building_solutions.csv` - CSV export

## Important Note

This example uses **simplified constraints** with the default structure generator for demonstration purposes. The default generator creates generic components without understanding building-specific types.

### For Production Use

To use this for real building design, you should:

#### 1. Implement a Custom Building Structure Generator

```python
from sep_solver.core.interfaces import StructureGenerator
from sep_solver.models.structure import Structure, Component, Relationship

class BuildingStructureGenerator(StructureGenerator):
    """Custom generator that understands building components."""
    
    def __init__(self):
        self.component_types = BuildingComponentTypes()
        self.relationship_types = [
            "adjacent_to", "contains", "serves", "connects_to",
            "supports", "addressed_by", "requires"
        ]
    
    def generate_structure(self, constraints):
        """Generate a building structure."""
        structure = Structure(components=[], relationships=[])
        
        # Generate spaces
        num_spaces = random.randint(2, 5)
        for i in range(num_spaces):
            space_type = random.choice(self.component_types.get_space_types())
            component = Component(
                id=f"space_{i}",
                type=space_type,
                properties={"area": random.randint(100, 500)}
            )
            structure.components.append(component)
        
        # Generate MEP systems
        for system_type in ["hvac_unit", "electrical_panel"]:
            component = Component(
                id=f"{system_type}_1",
                type=system_type,
                properties={}
            )
            structure.components.append(component)
        
        # Generate non-physical elements
        zone = Component(
            id="zone_1",
            type="functional_zone",
            properties={"purpose": "office"}
        )
        structure.components.append(zone)
        
        intent = Component(
            id="intent_1",
            type="design_intent",
            properties={"goal": "maximize natural light"}
        )
        structure.components.append(intent)
        
        # Generate relationships
        # Spaces adjacent to each other
        for i in range(len(structure.components) - 1):
            rel = Relationship(
                id=f"rel_{i}",
                source_id=structure.components[i].id,
                target_id=structure.components[i+1].id,
                type="adjacent_to"
            )
            structure.relationships.append(rel)
        
        return structure
```

#### 2. Use the Custom Generator

```python
# Create custom generator
building_generator = BuildingStructureGenerator()

# Use with engine
engine = SEPEngine(
    schema,
    constraints,
    config,
    structure_generator=building_generator
)

# Now use full building-specific constraints
constraints = ConstraintSet()
constraints.add_constraint(MinimumSpacesConstraint(min_spaces=2))
constraints.add_constraint(RequiredFunctionalZoneConstraint())
constraints.add_constraint(CirculationRequirementConstraint())
constraints.add_constraint(MEPSystemRequirementConstraint())
constraints.add_constraint(DesignIntentConstraint())
constraints.add_constraint(PhysicalNonPhysicalBalanceConstraint(0.25))
```

#### 3. Add Domain-Specific Logic

```python
class BuildingStructureGenerator(StructureGenerator):
    def generate_structure(self, constraints):
        # Analyze constraints
        min_spaces = self._get_min_spaces_from_constraints(constraints)
        required_systems = self._get_required_systems(constraints)
        
        # Generate structure that satisfies constraints
        structure = Structure(components=[], relationships=[])
        
        # Add required spaces
        for i in range(min_spaces):
            # ... generate spaces
        
        # Add required systems
        for system in required_systems:
            # ... generate systems
        
        # Ensure circulation
        self._add_circulation_paths(structure)
        
        # Add functional zones
        self._add_functional_zones(structure)
        
        return structure
```

## Extending the Example

### Add New Component Types

```python
class BuildingComponentTypes:
    # Add new types
    ELEVATOR = "elevator"
    PARKING = "parking"
    ROOF_GARDEN = "roof_garden"
    
    # Add to categories
    @classmethod
    def get_circulation_types(cls):
        return [cls.CORRIDOR, cls.STAIRWELL, cls.ELEVATOR]
```

### Add New Constraints

```python
class AccessibilityConstraint(StructuralConstraint):
    """Ensure accessible circulation."""
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        # Check for elevator or ramp
        has_accessible_circulation = any(
            comp.type in ["elevator", "ramp"]
            for comp in design_object.structure.components
        )
        return has_accessible_circulation
```

### Add Performance Criteria

```python
class EnergyPerformanceConstraint(VariableConstraint):
    """Ensure energy performance targets."""
    
    def is_satisfied(self, design_object: DesignObject) -> bool:
        # Check energy-related variables
        if "energy_consumption" in design_object.variables.assignments:
            consumption = design_object.variables.assignments["energy_consumption"]
            return consumption <= self.max_consumption
        return True
```

## Use Cases

### 1. Early Design Exploration
Explore multiple design alternatives at the conceptual stage.

### 2. Design Validation
Verify designs against requirements and constraints.

### 3. Compliance Checking
Ensure designs meet building codes and standards.

### 4. Performance Optimization
Find designs that optimize for specific criteria.

### 5. Design Documentation
Capture design intent and rationale alongside physical design.

## Benefits Over Traditional BIM

✅ **Conceptual Elements** - Include non-physical design concepts  
✅ **Exploration** - Generate and evaluate multiple alternatives  
✅ **Validation** - Automatically check constraints  
✅ **Flexibility** - Work at multiple levels of abstraction  
✅ **Documentation** - Capture design intent and requirements  
✅ **Integration** - Link physical and conceptual elements  

## Next Steps

1. **Implement custom generator** - Create BuildingStructureGenerator
2. **Define your constraints** - Add domain-specific requirements
3. **Add variables** - Include performance metrics
4. **Customize analysis** - Add building-specific analysis functions
5. **Integrate with BIM** - Export to IFC or other BIM formats

## Documentation

See `docs/BUILDING_SYSTEM_DESIGN.md` for detailed documentation on:
- Component types and hierarchies
- Constraint patterns
- Advanced use cases
- Best practices
- Integration strategies

## Questions?

This example demonstrates the **concept** of using SEP Solver for building design. For production use, you'll need to implement domain-specific generators and constraints that understand your building design requirements.

The framework is flexible enough to handle:
- Any building type (residential, commercial, industrial)
- Any scale (room, building, campus)
- Any phase (conceptual, schematic, detailed)
- Any domain (architecture, MEP, structure, landscape)

Start with simple constraints and gradually add complexity as needed!
