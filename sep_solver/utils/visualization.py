"""Solution visualization and export utilities for the SEP solver."""

import json
import csv
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from ..models.design_object import DesignObject
from ..models.structure import Structure, Component, Relationship
from ..models.variable_assignment import VariableAssignment


class SolutionVisualizer:
    """Provides visualization and export capabilities for SEP solver solutions."""
    
    def __init__(self):
        """Initialize the solution visualizer."""
        self.export_formats = ["json", "xml", "csv", "yaml", "dot", "summary"]
    
    def export_solutions(self, solutions: List[DesignObject], 
                        filename: str, format: str = "json",
                        include_metadata: bool = True) -> None:
        """Export solutions to file in specified format.
        
        Args:
            solutions: List of solutions to export
            filename: Output filename
            format: Export format
            include_metadata: Whether to include metadata in export
            
        Raises:
            ValueError: If format is not supported
        """
        if format not in self.export_formats:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.export_formats}")
        
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            self._export_json(solutions, output_path, include_metadata)
        elif format == "xml":
            self._export_xml(solutions, output_path, include_metadata)
        elif format == "csv":
            self._export_csv(solutions, output_path, include_metadata)
        elif format == "yaml":
            self._export_yaml(solutions, output_path, include_metadata)
        elif format == "dot":
            self._export_dot(solutions, output_path, include_metadata)
        elif format == "summary":
            self._export_summary(solutions, output_path, include_metadata)
    
    def _export_json(self, solutions: List[DesignObject], 
                    output_path: Path, include_metadata: bool) -> None:
        """Export solutions to JSON format."""
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "solution_count": len(solutions),
                "format": "json",
                "include_metadata": include_metadata
            },
            "solutions": []
        }
        
        for solution in solutions:
            solution_data = solution.to_dict()
            if not include_metadata:
                solution_data.pop("metadata", None)
            export_data["solutions"].append(solution_data)
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def _export_xml(self, solutions: List[DesignObject], 
                   output_path: Path, include_metadata: bool) -> None:
        """Export solutions to XML format."""
        root = ET.Element("sep_solutions")
        
        # Add export info
        export_info = ET.SubElement(root, "export_info")
        ET.SubElement(export_info, "timestamp").text = datetime.now().isoformat()
        ET.SubElement(export_info, "solution_count").text = str(len(solutions))
        ET.SubElement(export_info, "format").text = "xml"
        ET.SubElement(export_info, "include_metadata").text = str(include_metadata)
        
        # Add solutions
        solutions_elem = ET.SubElement(root, "solutions")
        
        for solution in solutions:
            solution_elem = ET.SubElement(solutions_elem, "solution")
            solution_elem.set("id", solution.id)
            
            # Structure
            structure_elem = ET.SubElement(solution_elem, "structure")
            
            # Components
            components_elem = ET.SubElement(structure_elem, "components")
            for component in solution.structure.components:
                comp_elem = ET.SubElement(components_elem, "component")
                comp_elem.set("id", component.id)
                comp_elem.set("type", component.type)
                if hasattr(component, 'name') and component.name:
                    comp_elem.set("name", component.name)
            
            # Relationships
            relationships_elem = ET.SubElement(structure_elem, "relationships")
            for relationship in solution.structure.relationships:
                rel_elem = ET.SubElement(relationships_elem, "relationship")
                rel_elem.set("id", relationship.id)
                rel_elem.set("type", relationship.type)
                rel_elem.set("from", relationship.from_component)
                rel_elem.set("to", relationship.to_component)
            
            # Variables
            variables_elem = ET.SubElement(solution_elem, "variables")
            for var_name, var_value in solution.variables.assignments.items():
                var_elem = ET.SubElement(variables_elem, "variable")
                var_elem.set("name", var_name)
                var_elem.set("value", str(var_value))
                
                # Add domain info if available
                if var_name in solution.variables.domains:
                    domain = solution.variables.domains[var_name]
                    var_elem.set("domain", str(domain))
            
            # Metadata (if requested)
            if include_metadata and solution.metadata:
                metadata_elem = ET.SubElement(solution_elem, "metadata")
                for key, value in solution.metadata.items():
                    meta_elem = ET.SubElement(metadata_elem, "meta")
                    meta_elem.set("key", key)
                    meta_elem.text = str(value)
        
        # Write to file
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    def _export_csv(self, solutions: List[DesignObject], 
                   output_path: Path, include_metadata: bool) -> None:
        """Export solutions to CSV format."""
        if not solutions:
            return
        
        # Prepare CSV data
        fieldnames = [
            "solution_id", "components_count", "relationships_count", 
            "variables_count", "component_types", "relationship_types",
            "variable_names", "variable_values"
        ]
        
        if include_metadata:
            # Find all metadata keys
            metadata_keys = set()
            for solution in solutions:
                if solution.metadata:
                    metadata_keys.update(solution.metadata.keys())
            fieldnames.extend(sorted(metadata_keys))
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for solution in solutions:
                row = {
                    "solution_id": solution.id,
                    "components_count": len(solution.structure.components),
                    "relationships_count": len(solution.structure.relationships),
                    "variables_count": len(solution.variables.assignments),
                    "component_types": "|".join([comp.type for comp in solution.structure.components]),
                    "relationship_types": "|".join([rel.type for rel in solution.structure.relationships]),
                    "variable_names": "|".join(solution.variables.assignments.keys()),
                    "variable_values": "|".join([str(v) for v in solution.variables.assignments.values()])
                }
                
                if include_metadata and solution.metadata:
                    for key, value in solution.metadata.items():
                        row[key] = str(value)
                
                writer.writerow(row)
    
    def _export_yaml(self, solutions: List[DesignObject], 
                    output_path: Path, include_metadata: bool) -> None:
        """Export solutions to YAML format."""
        try:
            import yaml
        except ImportError:
            # Fallback to simple YAML-like format
            self._export_simple_yaml(solutions, output_path, include_metadata)
            return
        
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "solution_count": len(solutions),
                "format": "yaml",
                "include_metadata": include_metadata
            },
            "solutions": []
        }
        
        for solution in solutions:
            solution_data = solution.to_dict()
            if not include_metadata:
                solution_data.pop("metadata", None)
            export_data["solutions"].append(solution_data)
        
        with open(output_path, 'w') as f:
            yaml.dump(export_data, f, default_flow_style=False, indent=2)
    
    def _export_simple_yaml(self, solutions: List[DesignObject], 
                           output_path: Path, include_metadata: bool) -> None:
        """Export solutions to simple YAML-like format without yaml library."""
        with open(output_path, 'w') as f:
            f.write("export_info:\n")
            f.write(f"  timestamp: {datetime.now().isoformat()}\n")
            f.write(f"  solution_count: {len(solutions)}\n")
            f.write(f"  format: yaml\n")
            f.write(f"  include_metadata: {include_metadata}\n\n")
            
            f.write("solutions:\n")
            for i, solution in enumerate(solutions):
                f.write(f"  - id: {solution.id}\n")
                f.write(f"    structure:\n")
                f.write(f"      components:\n")
                for comp in solution.structure.components:
                    f.write(f"        - id: {comp.id}\n")
                    f.write(f"          type: {comp.type}\n")
                
                f.write(f"      relationships:\n")
                for rel in solution.structure.relationships:
                    f.write(f"        - id: {rel.id}\n")
                    f.write(f"          type: {rel.type}\n")
                    f.write(f"          from: {rel.from_component}\n")
                    f.write(f"          to: {rel.to_component}\n")
                
                f.write(f"    variables:\n")
                for var_name, var_value in solution.variables.assignments.items():
                    f.write(f"      {var_name}: {var_value}\n")
                
                if include_metadata and solution.metadata:
                    f.write(f"    metadata:\n")
                    for key, value in solution.metadata.items():
                        f.write(f"      {key}: {value}\n")
                
                if i < len(solutions) - 1:
                    f.write("\n")
    
    def _export_dot(self, solutions: List[DesignObject], 
                   output_path: Path, include_metadata: bool) -> None:
        """Export solutions to DOT format for graph visualization."""
        with open(output_path, 'w') as f:
            f.write("digraph SEP_Solutions {\n")
            f.write("  rankdir=TB;\n")
            f.write("  node [shape=box, style=rounded];\n")
            f.write("  edge [arrowhead=open];\n\n")
            
            for sol_idx, solution in enumerate(solutions):
                f.write(f"  subgraph cluster_{sol_idx} {{\n")
                f.write(f"    label=\"Solution {solution.id}\";\n")
                f.write(f"    style=dashed;\n")
                f.write(f"    color=blue;\n\n")
                
                # Add components as nodes
                for comp in solution.structure.components:
                    node_id = f"s{sol_idx}_{comp.id}"
                    label = f"{comp.id}\\n({comp.type})"
                    f.write(f"    {node_id} [label=\"{label}\", shape=ellipse];\n")
                
                # Add relationships as edges
                for rel in solution.structure.relationships:
                    from_node = f"s{sol_idx}_{rel.from_component}"
                    to_node = f"s{sol_idx}_{rel.to_component}"
                    f.write(f"    {from_node} -> {to_node} [label=\"{rel.type}\"];\n")
                
                # Add variable assignments as annotations
                if solution.variables.assignments:
                    f.write(f"    variables_{sol_idx} [label=\"Variables:\\n")
                    for var_name, var_value in list(solution.variables.assignments.items())[:5]:  # Limit to first 5
                        f.write(f"{var_name}={var_value}\\n")
                    if len(solution.variables.assignments) > 5:
                        f.write(f"...({len(solution.variables.assignments)-5} more)")
                    f.write(f"\", shape=note, style=filled, fillcolor=lightyellow];\n")
                
                f.write("  }\n\n")
            
            f.write("}\n")
    
    def _export_summary(self, solutions: List[DesignObject], 
                       output_path: Path, include_metadata: bool) -> None:
        """Export solutions to human-readable summary format."""
        with open(output_path, 'w') as f:
            f.write("SEP Solver Solutions Summary\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Solutions: {len(solutions)}\n")
            f.write(f"Include Metadata: {include_metadata}\n\n")
            
            if not solutions:
                f.write("No solutions found.\n")
                return
            
            # Overall statistics
            f.write("Overall Statistics:\n")
            f.write("-" * 20 + "\n")
            
            component_counts = [len(sol.structure.components) for sol in solutions]
            relationship_counts = [len(sol.structure.relationships) for sol in solutions]
            variable_counts = [len(sol.variables.assignments) for sol in solutions]
            
            f.write(f"Components per solution: {min(component_counts)}-{max(component_counts)} (avg: {sum(component_counts)/len(component_counts):.1f})\n")
            f.write(f"Relationships per solution: {min(relationship_counts)}-{max(relationship_counts)} (avg: {sum(relationship_counts)/len(relationship_counts):.1f})\n")
            f.write(f"Variables per solution: {min(variable_counts)}-{max(variable_counts)} (avg: {sum(variable_counts)/len(variable_counts):.1f})\n\n")
            
            # Component type analysis
            all_component_types = set()
            all_relationship_types = set()
            for solution in solutions:
                all_component_types.update([comp.type for comp in solution.structure.components])
                all_relationship_types.update([rel.type for rel in solution.structure.relationships])
            
            f.write(f"Component Types Found: {', '.join(sorted(all_component_types))}\n")
            f.write(f"Relationship Types Found: {', '.join(sorted(all_relationship_types))}\n\n")
            
            # Individual solutions
            f.write("Individual Solutions:\n")
            f.write("-" * 20 + "\n\n")
            
            for i, solution in enumerate(solutions, 1):
                f.write(f"Solution {i}: {solution.id}\n")
                f.write(f"  Components ({len(solution.structure.components)}):\n")
                for comp in solution.structure.components:
                    f.write(f"    - {comp.id} ({comp.type})\n")
                
                f.write(f"  Relationships ({len(solution.structure.relationships)}):\n")
                for rel in solution.structure.relationships:
                    f.write(f"    - {rel.id}: {rel.source_id} -> {rel.target_id} ({rel.type})\n")
                
                f.write(f"  Variables ({len(solution.variables.assignments)}):\n")
                for var_name, var_value in solution.variables.assignments.items():
                    domain_info = ""
                    if var_name in solution.variables.domains:
                        domain_info = f" (domain: {solution.variables.domains[var_name]})"
                    f.write(f"    - {var_name} = {var_value}{domain_info}\n")
                
                if include_metadata and solution.metadata:
                    f.write(f"  Metadata:\n")
                    for key, value in solution.metadata.items():
                        f.write(f"    - {key}: {value}\n")
                
                f.write("\n")
    
    def create_solution_comparison(self, solutions: List[DesignObject]) -> Dict[str, Any]:
        """Create a comparison analysis of multiple solutions.
        
        Args:
            solutions: List of solutions to compare
            
        Returns:
            Dictionary with comparison analysis
        """
        if not solutions:
            return {"error": "No solutions provided"}
        
        comparison = {
            "solution_count": len(solutions),
            "structure_comparison": {},
            "variable_comparison": {},
            "similarity_analysis": {}
        }
        
        # Structure comparison
        component_counts = [len(sol.structure.components) for sol in solutions]
        relationship_counts = [len(sol.structure.relationships) for sol in solutions]
        
        comparison["structure_comparison"] = {
            "components": {
                "min": min(component_counts),
                "max": max(component_counts),
                "avg": sum(component_counts) / len(component_counts),
                "distribution": component_counts
            },
            "relationships": {
                "min": min(relationship_counts),
                "max": max(relationship_counts),
                "avg": sum(relationship_counts) / len(relationship_counts),
                "distribution": relationship_counts
            }
        }
        
        # Variable comparison
        variable_counts = [len(sol.variables.assignments) for sol in solutions]
        all_variable_names = set()
        for solution in solutions:
            all_variable_names.update(solution.variables.assignments.keys())
        
        comparison["variable_comparison"] = {
            "counts": {
                "min": min(variable_counts),
                "max": max(variable_counts),
                "avg": sum(variable_counts) / len(variable_counts),
                "distribution": variable_counts
            },
            "unique_variables": len(all_variable_names),
            "common_variables": self._find_common_variables(solutions)
        }
        
        # Similarity analysis
        comparison["similarity_analysis"] = self._analyze_solution_similarity(solutions)
        
        return comparison
    
    def _find_common_variables(self, solutions: List[DesignObject]) -> List[str]:
        """Find variables that appear in all solutions."""
        if not solutions:
            return []
        
        common_vars = set(solutions[0].variables.assignments.keys())
        for solution in solutions[1:]:
            common_vars &= set(solution.variables.assignments.keys())
        
        return sorted(list(common_vars))
    
    def _analyze_solution_similarity(self, solutions: List[DesignObject]) -> Dict[str, Any]:
        """Analyze similarity between solutions."""
        if len(solutions) < 2:
            return {"note": "Need at least 2 solutions for similarity analysis"}
        
        # Component type similarity
        component_type_sets = []
        for solution in solutions:
            component_types = set([comp.type for comp in solution.structure.components])
            component_type_sets.append(component_types)
        
        # Calculate Jaccard similarity for component types
        similarities = []
        for i in range(len(solutions)):
            for j in range(i + 1, len(solutions)):
                set1, set2 = component_type_sets[i], component_type_sets[j]
                intersection = len(set1 & set2)
                union = len(set1 | set2)
                similarity = intersection / union if union > 0 else 0
                similarities.append({
                    "solution_pair": (solutions[i].id, solutions[j].id),
                    "component_type_similarity": similarity
                })
        
        return {
            "pairwise_similarities": similarities,
            "average_similarity": sum([s["component_type_similarity"] for s in similarities]) / len(similarities) if similarities else 0
        }
    
    def generate_solution_report(self, solutions: List[DesignObject], 
                               filename: str, include_comparison: bool = True) -> None:
        """Generate a comprehensive solution report.
        
        Args:
            solutions: List of solutions to report on
            filename: Output filename
            include_comparison: Whether to include comparison analysis
        """
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write("SEP Solver Solution Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Solutions: {len(solutions)}\n\n")
            
            if not solutions:
                f.write("No solutions found.\n")
                return
            
            # Executive summary
            f.write("Executive Summary\n")
            f.write("-" * 20 + "\n")
            
            component_counts = [len(sol.structure.components) for sol in solutions]
            relationship_counts = [len(sol.structure.relationships) for sol in solutions]
            variable_counts = [len(sol.variables.assignments) for sol in solutions]
            
            f.write(f"- Solutions found: {len(solutions)}\n")
            f.write(f"- Component range: {min(component_counts)}-{max(component_counts)} per solution\n")
            f.write(f"- Relationship range: {min(relationship_counts)}-{max(relationship_counts)} per solution\n")
            f.write(f"- Variable range: {min(variable_counts)}-{max(variable_counts)} per solution\n\n")
            
            # Detailed analysis
            if include_comparison and len(solutions) > 1:
                f.write("Comparative Analysis\n")
                f.write("-" * 20 + "\n")
                
                comparison = self.create_solution_comparison(solutions)
                
                f.write("Structure Comparison:\n")
                struct_comp = comparison["structure_comparison"]
                f.write(f"  Components: avg={struct_comp['components']['avg']:.1f}, range={struct_comp['components']['min']}-{struct_comp['components']['max']}\n")
                f.write(f"  Relationships: avg={struct_comp['relationships']['avg']:.1f}, range={struct_comp['relationships']['min']}-{struct_comp['relationships']['max']}\n")
                
                f.write("\nVariable Analysis:\n")
                var_comp = comparison["variable_comparison"]
                f.write(f"  Total unique variables: {var_comp['unique_variables']}\n")
                f.write(f"  Common variables: {len(var_comp['common_variables'])}\n")
                if var_comp['common_variables']:
                    f.write(f"  Common variable names: {', '.join(var_comp['common_variables'][:5])}\n")
                
                if "pairwise_similarities" in comparison["similarity_analysis"]:
                    avg_sim = comparison["similarity_analysis"]["average_similarity"]
                    f.write(f"\nAverage solution similarity: {avg_sim:.2f}\n")
                
                f.write("\n")
            
            # Individual solution details
            f.write("Solution Details\n")
            f.write("-" * 20 + "\n\n")
            
            for i, solution in enumerate(solutions, 1):
                f.write(f"Solution {i}: {solution.id}\n")
                f.write(f"{'=' * (len(solution.id) + 12)}\n")
                
                f.write(f"Structure Overview:\n")
                f.write(f"  - {len(solution.structure.components)} components\n")
                f.write(f"  - {len(solution.structure.relationships)} relationships\n")
                f.write(f"  - {len(solution.variables.assignments)} variables\n\n")
                
                # Component details
                if solution.structure.components:
                    f.write("Components:\n")
                    for comp in solution.structure.components:
                        f.write(f"  - {comp.id} ({comp.type})\n")
                    f.write("\n")
                
                # Relationship details
                if solution.structure.relationships:
                    f.write("Relationships:\n")
                    for rel in solution.structure.relationships:
                        f.write(f"  - {rel.source_id} -> {rel.target_id} ({rel.type})\n")
                    f.write("\n")
                
                # Variable details
                if solution.variables.assignments:
                    f.write("Variables:\n")
                    for var_name, var_value in solution.variables.assignments.items():
                        f.write(f"  - {var_name} = {var_value}\n")
                    f.write("\n")
                
                if i < len(solutions):
                    f.write("\n" + "-" * 40 + "\n\n")
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats.
        
        Returns:
            List of supported format names
        """
        return self.export_formats.copy()


# Convenience functions
def export_solutions(solutions: List[DesignObject], filename: str, 
                    format: str = "json", include_metadata: bool = True) -> None:
    """Convenience function to export solutions.
    
    Args:
        solutions: List of solutions to export
        filename: Output filename
        format: Export format
        include_metadata: Whether to include metadata
    """
    visualizer = SolutionVisualizer()
    visualizer.export_solutions(solutions, filename, format, include_metadata)


def generate_solution_report(solutions: List[DesignObject], filename: str,
                           include_comparison: bool = True) -> None:
    """Convenience function to generate solution report.
    
    Args:
        solutions: List of solutions to report on
        filename: Output filename
        include_comparison: Whether to include comparison analysis
    """
    visualizer = SolutionVisualizer()
    visualizer.generate_solution_report(solutions, filename, include_comparison)


def compare_solutions(solutions: List[DesignObject]) -> Dict[str, Any]:
    """Convenience function to compare solutions.
    
    Args:
        solutions: List of solutions to compare
        
    Returns:
        Dictionary with comparison analysis
    """
    visualizer = SolutionVisualizer()
    return visualizer.create_solution_comparison(solutions)