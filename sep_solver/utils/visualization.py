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

# Optional interactive visualization dependencies
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class SolutionVisualizer:
    """Provides visualization and export capabilities for SEP solver solutions."""
    
    def __init__(self):
        """Initialize the solution visualizer."""
        self.export_formats = ["json", "xml", "csv", "yaml", "dot", "summary"]
        self.interactive_formats = ["html", "interactive"]
        
        # Check for interactive visualization capabilities
        self.has_networkx = NETWORKX_AVAILABLE
        self.has_plotly = PLOTLY_AVAILABLE
        self.interactive_enabled = NETWORKX_AVAILABLE and PLOTLY_AVAILABLE
    
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
                rel_elem.set("from", relationship.source_id)
                rel_elem.set("to", relationship.target_id)
            
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
                    f.write(f"          from: {rel.source_id}\n")
                    f.write(f"          to: {rel.target_id}\n")
                
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
                    from_node = f"s{sol_idx}_{rel.source_id}"
                    to_node = f"s{sol_idx}_{rel.target_id}"
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
        formats = self.export_formats.copy()
        if self.interactive_enabled:
            formats.extend(self.interactive_formats)
        return formats
    
    # ========== Interactive Visualization Methods ==========
    
    def visualize_solution_interactive(self, solution: DesignObject, 
                                      layout: str = "spring",
                                      show_variables: bool = True,
                                      show_metadata: bool = False) -> str:
        """Create interactive HTML visualization of a single solution.
        
        Args:
            solution: Solution to visualize
            layout: Graph layout algorithm ("spring", "circular", "hierarchical", "kamada_kawai")
            show_variables: Whether to show variable assignments
            show_metadata: Whether to show metadata
            
        Returns:
            HTML string with interactive visualization
            
        Raises:
            ImportError: If required libraries are not available
        """
        if not self.interactive_enabled:
            raise ImportError(
                "Interactive visualization requires 'networkx' and 'plotly'. "
                "Install with: pip install networkx plotly"
            )
        
        # Build graph with NetworkX
        G = nx.DiGraph()
        
        # Add components as nodes with attributes
        for comp in solution.structure.components:
            G.add_node(
                comp.id,
                type=comp.type,
                label=f"{comp.id}",
                node_type="component"
            )
        
        # Add relationships as edges
        for rel in solution.structure.relationships:
            G.add_edge(
                rel.source_id,
                rel.target_id,
                type=rel.type,
                label=rel.type,
                relationship_id=rel.id
            )
        
        # Choose layout algorithm
        if layout == "spring":
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        elif layout == "circular":
            pos = nx.circular_layout(G)
        elif layout == "hierarchical":
            pos = nx.kamada_kawai_layout(G)
        elif layout == "kamada_kawai":
            pos = nx.kamada_kawai_layout(G)
        else:
            pos = nx.spring_layout(G, seed=42)
        
        # Create edge traces
        edge_traces = []
        edge_annotations = []
        
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            # Edge line
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=2, color='#888'),
                hoverinfo='text',
                hovertext=f"{edge[0]} → {edge[1]}<br>Type: {edge[2].get('type', 'N/A')}",
                showlegend=False
            )
            edge_traces.append(edge_trace)
            
            # Edge label annotation
            edge_annotations.append(
                dict(
                    x=(x0 + x1) / 2,
                    y=(y0 + y1) / 2,
                    text=edge[2].get('type', ''),
                    showarrow=False,
                    font=dict(size=10, color='#666'),
                    bgcolor='rgba(255, 255, 255, 0.8)',
                    borderpad=2
                )
            )
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_hover = []
        node_colors = []
        
        # Color map for component types
        component_types = list(set(G.nodes[node]['type'] for node in G.nodes()))
        color_map = {comp_type: px.colors.qualitative.Set3[i % len(px.colors.qualitative.Set3)] 
                    for i, comp_type in enumerate(component_types)}
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = G.nodes[node]
            node_text.append(node_data['label'])
            
            # Build hover text
            hover_parts = [
                f"<b>{node}</b>",
                f"Type: {node_data['type']}",
                f"Connections: {G.degree(node)}"
            ]
            node_hover.append("<br>".join(hover_parts))
            
            # Color by component type
            node_colors.append(color_map[node_data['type']])
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="top center",
            textfont=dict(size=12, color='#000'),
            marker=dict(
                size=30,
                color=node_colors,
                line=dict(width=2, color='#000')
            ),
            hoverinfo='text',
            hovertext=node_hover,
            showlegend=False
        )
        
        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace])
        
        # Update layout
        title_text = f'Solution: {solution.id}'
        if show_metadata and solution.metadata:
            title_text += f" | Strategy: {solution.metadata.get('generation_strategy', 'N/A')}"
        
        fig.update_layout(
            title=dict(text=title_text, x=0.5, xanchor='center'),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(250, 250, 250, 1)',
            annotations=edge_annotations,
            height=600
        )
        
        # Add variable information as annotation if requested
        if show_variables and solution.variables.assignments:
            var_text = "<b>Variables:</b><br>"
            var_items = list(solution.variables.assignments.items())[:10]  # Limit to 10
            for var_name, var_value in var_items:
                var_text += f"{var_name} = {var_value}<br>"
            if len(solution.variables.assignments) > 10:
                var_text += f"... and {len(solution.variables.assignments) - 10} more"
            
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.02, y=0.98,
                text=var_text,
                showarrow=False,
                font=dict(size=10),
                align="left",
                bgcolor="rgba(255, 255, 200, 0.9)",
                bordercolor="black",
                borderwidth=1,
                xanchor="left",
                yanchor="top"
            )
        
        return fig.to_html(include_plotlyjs='cdn', full_html=True)
    
    def visualize_solutions_comparison(self, solutions: List[DesignObject],
                                      max_solutions: int = 6) -> str:
        """Create interactive comparison visualization of multiple solutions.
        
        Args:
            solutions: List of solutions to compare
            max_solutions: Maximum number of solutions to display
            
        Returns:
            HTML string with interactive comparison visualization
            
        Raises:
            ImportError: If required libraries are not available
        """
        if not self.interactive_enabled:
            raise ImportError(
                "Interactive visualization requires 'networkx' and 'plotly'. "
                "Install with: pip install networkx plotly"
            )
        
        solutions = solutions[:max_solutions]
        
        # Create subplots
        rows = (len(solutions) + 2) // 3  # 3 columns
        cols = min(3, len(solutions))
        
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[f"{sol.id}" for sol in solutions],
            specs=[[{"type": "scatter"}] * cols for _ in range(rows)],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        for idx, solution in enumerate(solutions):
            row = idx // 3 + 1
            col = idx % 3 + 1
            
            # Build graph
            G = nx.DiGraph()
            for comp in solution.structure.components:
                G.add_node(comp.id, type=comp.type)
            for rel in solution.structure.relationships:
                G.add_edge(rel.source_id, rel.target_id)
            
            # Layout
            pos = nx.spring_layout(G, k=1.5, iterations=30, seed=42)
            
            # Add edges
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                fig.add_trace(
                    go.Scatter(
                        x=[x0, x1, None],
                        y=[y0, y1, None],
                        mode='lines',
                        line=dict(width=1, color='#888'),
                        hoverinfo='skip',
                        showlegend=False
                    ),
                    row=row, col=col
                )
            
            # Add nodes
            node_x = [pos[node][0] for node in G.nodes()]
            node_y = [pos[node][1] for node in G.nodes()]
            
            fig.add_trace(
                go.Scatter(
                    x=node_x,
                    y=node_y,
                    mode='markers',
                    marker=dict(size=15, color='lightblue', line=dict(width=1)),
                    hovertext=[f"{node}<br>{G.nodes[node]['type']}" for node in G.nodes()],
                    hoverinfo='text',
                    showlegend=False
                ),
                row=row, col=col
            )
        
        # Update layout
        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
        fig.update_layout(
            title_text="Solution Comparison",
            height=300 * rows,
            showlegend=False,
            hovermode='closest'
        )
        
        return fig.to_html(include_plotlyjs='cdn', full_html=True)
    
    def visualize_solution_statistics(self, solutions: List[DesignObject]) -> str:
        """Create interactive statistical visualization of solutions.
        
        Args:
            solutions: List of solutions to analyze
            
        Returns:
            HTML string with interactive statistical charts
            
        Raises:
            ImportError: If required libraries are not available
        """
        if not self.interactive_enabled:
            raise ImportError(
                "Interactive visualization requires 'networkx' and 'plotly'. "
                "Install with: pip install networkx plotly"
            )
        
        if not solutions:
            return "<html><body><h3>No solutions to visualize</h3></body></html>"
        
        # Collect statistics
        stats_data = {
            'solution_id': [],
            'components': [],
            'relationships': [],
            'variables': [],
            'component_types': [],
            'relationship_types': []
        }
        
        for solution in solutions:
            stats_data['solution_id'].append(solution.id)
            stats_data['components'].append(len(solution.structure.components))
            stats_data['relationships'].append(len(solution.structure.relationships))
            stats_data['variables'].append(len(solution.variables.assignments))
            
            comp_types = [comp.type for comp in solution.structure.components]
            rel_types = [rel.type for rel in solution.structure.relationships]
            stats_data['component_types'].append(', '.join(set(comp_types)))
            stats_data['relationship_types'].append(', '.join(set(rel_types)))
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Components per Solution',
                'Relationships per Solution',
                'Variables per Solution',
                'Structure Complexity'
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "scatter"}]
            ]
        )
        
        # Components bar chart
        fig.add_trace(
            go.Bar(
                x=stats_data['solution_id'],
                y=stats_data['components'],
                name='Components',
                marker_color='lightblue'
            ),
            row=1, col=1
        )
        
        # Relationships bar chart
        fig.add_trace(
            go.Bar(
                x=stats_data['solution_id'],
                y=stats_data['relationships'],
                name='Relationships',
                marker_color='lightcoral'
            ),
            row=1, col=2
        )
        
        # Variables bar chart
        fig.add_trace(
            go.Bar(
                x=stats_data['solution_id'],
                y=stats_data['variables'],
                name='Variables',
                marker_color='lightgreen'
            ),
            row=2, col=1
        )
        
        # Complexity scatter plot
        fig.add_trace(
            go.Scatter(
                x=stats_data['components'],
                y=stats_data['relationships'],
                mode='markers+text',
                text=stats_data['solution_id'],
                textposition="top center",
                marker=dict(
                    size=15,
                    color=stats_data['variables'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Variables")
                ),
                name='Complexity'
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_xaxes(title_text="Solution ID", row=1, col=1)
        fig.update_xaxes(title_text="Solution ID", row=1, col=2)
        fig.update_xaxes(title_text="Solution ID", row=2, col=1)
        fig.update_xaxes(title_text="Components", row=2, col=2)
        
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=2)
        fig.update_yaxes(title_text="Count", row=2, col=1)
        fig.update_yaxes(title_text="Relationships", row=2, col=2)
        
        fig.update_layout(
            title_text="Solution Statistics Dashboard",
            height=800,
            showlegend=False,
            hovermode='closest'
        )
        
        return fig.to_html(include_plotlyjs='cdn', full_html=True)
    
    def visualize_exploration_metrics(self, exploration_state) -> str:
        """Create interactive visualization of exploration metrics.
        
        Args:
            exploration_state: ExplorationState object with metrics
            
        Returns:
            HTML string with interactive metrics visualization
            
        Raises:
            ImportError: If required libraries are not available
        """
        if not self.interactive_enabled:
            raise ImportError(
                "Interactive visualization requires 'networkx' and 'plotly'. "
                "Install with: pip install networkx plotly"
            )
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Constraint Violations',
                'Component Performance',
                'Candidate Evaluation Timeline',
                'Success Rate Over Time'
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "scatter"}, {"type": "scatter"}]
            ]
        )
        
        # Constraint violations
        violations = exploration_state.get_most_violated_constraints(10)
        if violations:
            constraint_ids = [v[0] for v in violations]
            violation_counts = [v[1] for v in violations]
            
            fig.add_trace(
                go.Bar(
                    x=constraint_ids,
                    y=violation_counts,
                    name='Violations',
                    marker_color='salmon'
                ),
                row=1, col=1
            )
        
        # Component performance
        perf_summary = exploration_state.get_component_performance_summary()
        if perf_summary:
            components = list(perf_summary.keys())
            avg_times = [perf_summary[comp]['average_time'] for comp in components]
            
            fig.add_trace(
                go.Bar(
                    x=components,
                    y=avg_times,
                    name='Avg Time',
                    marker_color='lightblue'
                ),
                row=1, col=2
            )
        
        # Candidate evaluation timeline
        snapshots = exploration_state.candidate_snapshots[-50:]  # Last 50
        if snapshots:
            iterations = [s.step for s in snapshots]
            eval_times = [s.validation_result.get('evaluation_time', 0) for s in snapshots]
            is_valid = [s.validation_result.get('is_valid', False) for s in snapshots]
            
            colors = ['green' if valid else 'red' for valid in is_valid]
            
            fig.add_trace(
                go.Scatter(
                    x=iterations,
                    y=eval_times,
                    mode='markers',
                    marker=dict(size=8, color=colors),
                    name='Evaluation Time',
                    hovertext=[f"Valid: {v}" for v in is_valid]
                ),
                row=2, col=1
            )
        
        # Success rate over time
        if snapshots:
            window_size = 10
            success_rates = []
            windows = []
            
            for i in range(len(snapshots) - window_size + 1):
                window = snapshots[i:i+window_size]
                success_rate = sum(1 for s in window if s.validation_result.get('is_valid', False)) / window_size
                success_rates.append(success_rate * 100)
                windows.append(window[-1].step)
            
            fig.add_trace(
                go.Scatter(
                    x=windows,
                    y=success_rates,
                    mode='lines+markers',
                    name='Success Rate',
                    line=dict(color='green', width=2)
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_xaxes(title_text="Constraint", row=1, col=1)
        fig.update_xaxes(title_text="Component", row=1, col=2)
        fig.update_xaxes(title_text="Iteration", row=2, col=1)
        fig.update_xaxes(title_text="Iteration", row=2, col=2)
        
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_yaxes(title_text="Time (s)", row=1, col=2)
        fig.update_yaxes(title_text="Time (s)", row=2, col=1)
        fig.update_yaxes(title_text="Success Rate (%)", row=2, col=2)
        
        fig.update_layout(
            title_text="Exploration Metrics Dashboard",
            height=800,
            showlegend=False,
            hovermode='closest'
        )
        
        return fig.to_html(include_plotlyjs='cdn', full_html=True)
    
    def export_interactive_visualization(self, solutions: List[DesignObject],
                                        filename: str,
                                        viz_type: str = "single",
                                        **kwargs) -> None:
        """Export interactive visualization to HTML file.
        
        Args:
            solutions: List of solutions to visualize
            filename: Output HTML filename
            viz_type: Type of visualization ("single", "comparison", "statistics")
            **kwargs: Additional arguments for specific visualization types
            
        Raises:
            ImportError: If required libraries are not available
            ValueError: If viz_type is not supported
        """
        if not self.interactive_enabled:
            raise ImportError(
                "Interactive visualization requires 'networkx' and 'plotly'. "
                "Install with: pip install networkx plotly"
            )
        
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if viz_type == "single":
            if not solutions:
                raise ValueError("No solutions provided")
            html_content = self.visualize_solution_interactive(solutions[0], **kwargs)
        elif viz_type == "comparison":
            html_content = self.visualize_solutions_comparison(solutions, **kwargs)
        elif viz_type == "statistics":
            html_content = self.visualize_solution_statistics(solutions)
        else:
            raise ValueError(f"Unsupported visualization type: {viz_type}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def create_interactive_dashboard(self, solutions: List[DesignObject],
                                    exploration_state=None) -> str:
        """Create comprehensive interactive dashboard with all visualizations.
        
        Args:
            solutions: List of solutions to visualize
            exploration_state: Optional exploration state for metrics
            
        Returns:
            HTML string with complete dashboard
            
        Raises:
            ImportError: If required libraries are not available
        """
        if not self.interactive_enabled:
            raise ImportError(
                "Interactive visualization requires 'networkx' and 'plotly'. "
                "Install with: pip install networkx plotly"
            )
        
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>SEP Solver Dashboard</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }",
            "h1 { color: #333; text-align: center; }",
            "h2 { color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }",
            ".section { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            ".stats { display: flex; justify-content: space-around; margin: 20px 0; }",
            ".stat-box { text-align: center; padding: 15px; background: #e3f2fd; border-radius: 5px; }",
            ".stat-value { font-size: 2em; font-weight: bold; color: #1976d2; }",
            ".stat-label { color: #666; margin-top: 5px; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>SEP Solver Interactive Dashboard</h1>",
        ]
        
        # Summary statistics
        html_parts.append("<div class='section'>")
        html_parts.append("<h2>Summary</h2>")
        html_parts.append("<div class='stats'>")
        
        html_parts.append("<div class='stat-box'>")
        html_parts.append(f"<div class='stat-value'>{len(solutions)}</div>")
        html_parts.append("<div class='stat-label'>Solutions Found</div>")
        html_parts.append("</div>")
        
        if solutions:
            avg_components = sum(len(s.structure.components) for s in solutions) / len(solutions)
            html_parts.append("<div class='stat-box'>")
            html_parts.append(f"<div class='stat-value'>{avg_components:.1f}</div>")
            html_parts.append("<div class='stat-label'>Avg Components</div>")
            html_parts.append("</div>")
            
            avg_relationships = sum(len(s.structure.relationships) for s in solutions) / len(solutions)
            html_parts.append("<div class='stat-box'>")
            html_parts.append(f"<div class='stat-value'>{avg_relationships:.1f}</div>")
            html_parts.append("<div class='stat-label'>Avg Relationships</div>")
            html_parts.append("</div>")
        
        html_parts.append("</div>")
        html_parts.append("</div>")
        
        # Statistics visualization
        if solutions:
            html_parts.append("<div class='section'>")
            html_parts.append("<h2>Solution Statistics</h2>")
            stats_html = self.visualize_solution_statistics(solutions)
            # Extract just the plotly div
            stats_html = stats_html.split('<body>')[1].split('</body>')[0] if '<body>' in stats_html else stats_html
            html_parts.append(stats_html)
            html_parts.append("</div>")
        
        # Comparison visualization
        if len(solutions) > 1:
            html_parts.append("<div class='section'>")
            html_parts.append("<h2>Solution Comparison</h2>")
            comparison_html = self.visualize_solutions_comparison(solutions)
            comparison_html = comparison_html.split('<body>')[1].split('</body>')[0] if '<body>' in comparison_html else comparison_html
            html_parts.append(comparison_html)
            html_parts.append("</div>")
        
        # Individual solution details
        if solutions:
            html_parts.append("<div class='section'>")
            html_parts.append("<h2>Individual Solutions</h2>")
            for i, solution in enumerate(solutions[:3], 1):  # Show first 3
                html_parts.append(f"<h3>Solution {i}: {solution.id}</h3>")
                solution_html = self.visualize_solution_interactive(solution)
                solution_html = solution_html.split('<body>')[1].split('</body>')[0] if '<body>' in solution_html else solution_html
                html_parts.append(solution_html)
            html_parts.append("</div>")
        
        # Exploration metrics
        if exploration_state:
            html_parts.append("<div class='section'>")
            html_parts.append("<h2>Exploration Metrics</h2>")
            metrics_html = self.visualize_exploration_metrics(exploration_state)
            metrics_html = metrics_html.split('<body>')[1].split('</body>')[0] if '<body>' in metrics_html else metrics_html
            html_parts.append(metrics_html)
            html_parts.append("</div>")
        
        html_parts.extend([
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_parts)


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


# Interactive visualization convenience functions
def visualize_solution_interactive(solution: DesignObject, 
                                   output_file: Optional[str] = None,
                                   **kwargs) -> str:
    """Convenience function for interactive solution visualization.
    
    Args:
        solution: Solution to visualize
        output_file: Optional output HTML file path
        **kwargs: Additional visualization options
        
    Returns:
        HTML string (or writes to file if output_file provided)
    """
    visualizer = SolutionVisualizer()
    html = visualizer.visualize_solution_interactive(solution, **kwargs)
    
    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        return f"Visualization saved to {output_file}"
    
    return html


def create_interactive_dashboard(solutions: List[DesignObject],
                                exploration_state=None,
                                output_file: Optional[str] = None) -> str:
    """Convenience function to create interactive dashboard.
    
    Args:
        solutions: List of solutions to visualize
        exploration_state: Optional exploration state for metrics
        output_file: Optional output HTML file path
        
    Returns:
        HTML string (or writes to file if output_file provided)
    """
    visualizer = SolutionVisualizer()
    html = visualizer.create_interactive_dashboard(solutions, exploration_state)
    
    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        return f"Dashboard saved to {output_file}"
    
    return html


def visualize_solution_statistics(solutions: List[DesignObject],
                                  output_file: Optional[str] = None) -> str:
    """Convenience function for solution statistics visualization.
    
    Args:
        solutions: List of solutions to analyze
        output_file: Optional output HTML file path
        
    Returns:
        HTML string (or writes to file if output_file provided)
    """
    visualizer = SolutionVisualizer()
    html = visualizer.visualize_solution_statistics(solutions)
    
    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        return f"Statistics visualization saved to {output_file}"
    
    return html