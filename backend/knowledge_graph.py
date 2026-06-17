"""
Candidate Knowledge Graph Visualization
"""

import logging
from typing import List, Dict, Set, Tuple, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import Candidate

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import plotly.graph_objects as go
    import plotly.express as px
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CandidateKnowledgeGraph:
    """Build and visualize candidate knowledge graphs"""
    
    def __init__(self):
        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX or Plotly not available. Graph visualization disabled.")
        self.graph = nx.DiGraph() if NETWORKX_AVAILABLE else None
    
    def build_candidate_graph(self, candidates: List[Candidate]) -> Optional[nx.DiGraph]:
        """Build a knowledge graph from candidate data"""
        if not NETWORKX_AVAILABLE:
            logger.warning("Cannot build graph - NetworkX not available")
            return None
        
        self.graph = nx.DiGraph()
        
        for candidate in candidates:
            # Add candidate node
            self.graph.add_node(candidate.candidate_id, 
                               name=candidate.profile.anonymized_name,
                               title=candidate.profile.current_title,
                               company=candidate.profile.current_company,
                               type='candidate')
            
            # Add skill nodes and edges
            for skill in candidate.skills:
                skill_id = f"skill_{skill.name.lower().replace(' ', '_')}"
                if not self.graph.has_node(skill_id):
                    self.graph.add_node(skill_id, name=skill.name, type='skill')
                
                # Add edge from candidate to skill with proficiency as weight
                proficiency_weight = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}
                weight = proficiency_weight.get(skill.proficiency, 1)
                self.graph.add_edge(candidate.candidate_id, skill_id, weight=weight)
            
            # Add company nodes and edges
            company_id = f"company_{candidate.profile.current_company.lower().replace(' ', '_')}"
            if not self.graph.has_node(company_id):
                self.graph.add_node(company_id, name=candidate.profile.current_company, type='company')
            
            self.graph.add_edge(candidate.candidate_id, company_id, relationship='works_at')
            
            # Add industry nodes
            industry_id = f"industry_{candidate.profile.current_industry.lower().replace(' ', '_')}"
            if not self.graph.has_node(industry_id):
                self.graph.add_node(industry_id, name=candidate.profile.current_industry, type='industry')
            
            self.graph.add_edge(company_id, industry_id, relationship='belongs_to')
            
            # Add education nodes
            for edu in candidate.education:
                edu_id = f"edu_{edu.institution.lower().replace(' ', '_')}"
                if not self.graph.has_node(edu_id):
                    self.graph.add_node(edu_id, name=edu.institution, type='education')
                
                self.graph.add_edge(candidate.candidate_id, edu_id, relationship='educated_at')
        
        logger.info(f"Built knowledge graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        return self.graph
    
    def get_skill_clusters(self) -> Dict[str, List[str]]:
        """Identify clusters of related skills"""
        if not NETWORKX_AVAILABLE or self.graph is None:
            return {}
        
        skill_nodes = [node for node, data in self.graph.nodes(data=True) if data.get('type') == 'skill']
        clusters = {}
        
        for skill_node in skill_nodes:
            # Find candidates with this skill
            candidates_with_skill = list(self.graph.predecessors(skill_node))
            
            # Find other skills these candidates have
            related_skills = set()
            for candidate in candidates_with_skill:
                for neighbor in self.graph.successors(candidate):
                    if self.graph.nodes[neighbor].get('type') == 'skill' and neighbor != skill_node:
                        related_skills.add(neighbor)
            
            clusters[skill_node] = list(related_skills)
        
        return clusters
    
    def get_top_skills(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Get the most common skills in the dataset"""
        if not NETWORKX_AVAILABLE or self.graph is None:
            return []
        
        skill_nodes = [node for node, data in self.graph.nodes(data=True) if data.get('type') == 'skill']
        skill_counts = []
        
        for skill_node in skill_nodes:
            candidate_count = len(list(self.graph.predecessors(skill_node)))
            skill_counts.append((self.graph.nodes[skill_node]['name'], candidate_count))
        
        # Sort by count and return top N
        skill_counts.sort(key=lambda x: x[1], reverse=True)
        return skill_counts[:top_n]
    
    def get_company_clusters(self) -> Dict[str, List[str]]:
        """Get clusters of companies and their shared skills"""
        if not NETWORKX_AVAILABLE or self.graph is None:
            return {}
        
        company_nodes = [node for node, data in self.graph.nodes(data=True) if data.get('type') == 'company']
        clusters = {}
        
        for company_node in company_nodes:
            company_name = self.graph.nodes[company_node]['name']
            
            # Get candidates at this company
            candidates_at_company = list(self.graph.predecessors(company_node))
            
            # Get all skills from these candidates
            company_skills = set()
            for candidate in candidates_at_company:
                for neighbor in self.graph.successors(candidate):
                    if self.graph.nodes[neighbor].get('type') == 'skill':
                        company_skills.add(self.graph.nodes[neighbor]['name'])
            
            clusters[company_name] = list(company_skills)
        
        return clusters
    
    def visualize_graph_matplotlib(self, output_path: Optional[Path] = None):
        """Visualize the graph using matplotlib (for smaller graphs)"""
        if not NETWORKX_AVAILABLE or self.graph is None:
            logger.warning("Cannot visualize - NetworkX not available")
            return
        
        if self.graph.number_of_nodes() > 100:
            logger.warning("Graph too large for matplotlib visualization. Consider using plotly instead.")
            return
        
        plt.figure(figsize=(15, 10))
        
        # Create color map for node types
        color_map = []
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('type', 'unknown')
            if node_type == 'candidate':
                color_map.append('lightblue')
            elif node_type == 'skill':
                color_map.append('lightgreen')
            elif node_type == 'company':
                color_map.append('lightcoral')
            elif node_type == 'industry':
                color_map.append('lightyellow')
            else:
                color_map.append('lightgray')
        
        # Draw the graph
        pos = nx.spring_layout(self.graph, k=1, iterations=50)
        nx.draw(self.graph, pos, node_color=color_map, with_labels=True, 
                node_size=500, font_size=8, font_weight='bold')
        
        plt.title("Candidate Knowledge Graph")
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Graph visualization saved to {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def visualize_graph_plotly(self, output_path: Optional[Path] = None):
        """Visualize the graph using plotly (for larger graphs)"""
        if not NETWORKX_AVAILABLE or self.graph is None:
            logger.warning("Cannot visualize - NetworkX/Plotly not available")
            return
        
        # Create positions
        pos = nx.spring_layout(self.graph, k=1, iterations=50)
        
        # Extract node and edge data
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(self.graph.nodes[node].get('name', node))
            
            # Color by node type
            node_type = self.graph.nodes[node].get('type', 'unknown')
            if node_type == 'candidate':
                node_colors.append('blue')
                node_sizes.append(10)
            elif node_type == 'skill':
                node_colors.append('green')
                node_sizes.append(5)
            elif node_type == 'company':
                node_colors.append('red')
                node_sizes.append(8)
            else:
                node_colors.append('gray')
                node_sizes.append(6)
        
        # Create edges
        edge_x = []
        edge_y = []
        
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create plotly figure
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=1, color='black')
            )
        ))
        
        fig.update_layout(
            title="Candidate Knowledge Graph",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ dict(
                text="Knowledge graph showing candidates, skills, and companies",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom',
                font=dict(size=12)
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        if output_path:
            fig.write_html(str(output_path))
            logger.info(f"Interactive graph visualization saved to {output_path}")
        else:
            fig.show()
    
    def analyze_graph_properties(self) -> Dict[str, any]:
        """Analyze properties of the knowledge graph"""
        if not NETWORKX_AVAILABLE or self.graph is None:
            return {}
        
        properties = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': self._count_node_types(),
            'average_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0,
            'is_connected': nx.is_connected(self.graph.to_undirected()),
            'density': nx.density(self.graph)
        }
        
        return properties
    
    def _count_node_types(self) -> Dict[str, int]:
        """Count nodes by type"""
        type_counts = {}
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        return type_counts
    
    def find_similar_candidates(self, candidate_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """Find candidates similar to a given candidate based on shared skills"""
        if not NETWORKX_AVAILABLE or self.graph is None:
            return []
        
        if not self.graph.has_node(candidate_id):
            return []
        
        # Get skills of the target candidate
        target_skills = set()
        for neighbor in self.graph.successors(candidate_id):
            if self.graph.nodes[neighbor].get('type') == 'skill':
                target_skills.add(neighbor)
        
        # Find other candidates with similar skills
        candidate_nodes = [node for node, data in self.graph.nodes(data=True) if data.get('type') == 'candidate']
        similarities = []
        
        for candidate in candidate_nodes:
            if candidate == candidate_id:
                continue
            
            # Get skills of this candidate
            candidate_skills = set()
            for neighbor in self.graph.successors(candidate):
                if self.graph.nodes[neighbor].get('type') == 'skill':
                    candidate_skills.add(neighbor)
            
            # Calculate Jaccard similarity
            intersection = len(target_skills & candidate_skills)
            union = len(target_skills | candidate_skills)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0:
                similarities.append((candidate, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]