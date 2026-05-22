"""OsintHAM — Graph Engine (NetworkX)"""
import networkx as nx
from typing import Optional


class GraphEngine:
    """Graph analysis engine for investigations."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node_id: str, **attrs):
        self.graph.add_node(node_id, **attrs)

    def add_edge(self, from_id: str, to_id: str, **attrs):
        self.graph.add_edge(from_id, to_id, **attrs)

    def remove_node(self, node_id: str):
        if node_id in self.graph:
            self.graph.remove_node(node_id)

    def remove_edge(self, from_id: str, to_id: str):
        if self.graph.has_edge(from_id, to_id):
            self.graph.remove_edge(from_id, to_id)

    def get_centrality(self) -> dict:
        """Degree centrality — most connected nodes."""
        if not self.graph.nodes:
            return {}
        centrality = nx.degree_centrality(self.graph)
        return {nid: round(score, 4) for nid, score in centrality.items()}

    def get_betweenness(self) -> dict:
        """Betweenness centrality — bridge nodes."""
        if not self.graph.nodes:
            return {}
        try:
            betweenness = nx.betweenness_centrality(self.graph)
            return {nid: round(score, 4) for nid, score in betweenness.items()}
        except Exception:
            return {}

    def find_paths(self, source: str, target: str, cutoff: int = 10) -> list:
        """Find all simple paths between two nodes."""
        try:
            paths = list(nx.all_simple_paths(self.graph, source, target, cutoff=cutoff))
            return [list(p) for p in paths]
        except (nx.NetworkXError, nx.NodeNotFound):
            return []

    def find_connected(self, node_id: str) -> list:
        """Find all nodes connected to given node."""
        if node_id not in self.graph:
            return []
        undirected = self.graph.to_undirected()
        connected = nx.node_connected_component(undirected, node_id)
        return list(connected)

    def get_communities(self) -> list:
        """Detect communities using greedy modularity."""
        if not self.graph.nodes:
            return []
        try:
            undirected = self.graph.to_undirected()
            from networkx.algorithms.community import greedy_modularity_communities
            communities = greedy_modularity_communities(undirected)
            return [list(c) for c in communities]
        except Exception:
            return []

    def get_stats(self) -> dict:
        """Graph statistics."""
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "density": round(nx.density(self.graph), 4),
            "is_connected": nx.is_weakly_connected(self.graph) if self.graph.nodes else False,
            "components": nx.number_weakly_connected_components(self.graph) if self.graph.nodes else 0,
        }

    def to_cytoscape(self) -> list:
        """Convert to Cytoscape.js format."""
        elements = []
        for nid, attrs in self.graph.nodes(data=True):
            elements.append({
                "data": {"id": nid, **attrs}
            })
        for src, tgt, attrs in self.graph.edges(data=True):
            elements.append({
                "data": {"id": f"{src}_{tgt}", "source": src, "target": tgt, **attrs}
            })
        return elements

    def to_d3(self) -> dict:
        """Convert to D3.js / react-force-graph format."""
        nodes = []
        for nid, attrs in self.graph.nodes(data=True):
            nodes.append({"id": nid, **attrs})
        links = []
        for src, tgt, attrs in self.graph.edges(data=True):
            links.append({"source": src, "target": tgt, **attrs})
        return {"nodes": nodes, "links": links}

    def clear(self):
        self.graph.clear()
