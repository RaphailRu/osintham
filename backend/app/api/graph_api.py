"""OsintHAM — Graph API Router"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, InvestigationModel, NodeModel, EdgeModel
from app.graph_engine import GraphEngine
from app.schemas import GraphData

router = APIRouter(prefix="/api", tags=["graph"])


@router.get("/investigations/{inv_id}/graph")
def get_graph(inv_id: str, db: Session = Depends(get_db)):
    """Get full graph data for visualization."""
    inv = db.query(InvestigationModel).filter(InvestigationModel.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    nodes = []
    for node in inv.nodes:
        nodes.append({
            "id": node.id,
            "type": node.type,
            "label": node.label,
            "trust_level": node.trust_level,
            "data": json.loads(node.data) if node.data else {},
            "source": node.source,
            "color": _node_color(node.type, node.trust_level),
            "group": node.type,
        })

    edges = []
    for edge in inv.edges:
        edges.append({
            "id": edge.id,
            "from": edge.from_node,
            "to": edge.to_node,
            "label": edge.label,
            "trust_level": edge.trust_level,
            "bidirectional": edge.bidirectional,
        })

    # Build graph engine for analysis
    engine = GraphEngine()
    for n in nodes:
        engine.add_node(n["id"], **n)
    for e in edges:
        engine.add_edge(e["from"], e["to"], **e)

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": engine.get_stats(),
        "centrality": engine.get_centrality(),
        "communities": engine.get_communities(),
    }


@router.get("/investigations/{inv_id}/paths")
def find_paths(inv_id: str, source: str, target: str, cutoff: int = 10, db: Session = Depends(get_db)):
    """Find all paths between two nodes."""
    inv = db.query(InvestigationModel).filter(InvestigationModel.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    engine = GraphEngine()
    for node in inv.nodes:
        engine.add_node(node.id)
    for edge in inv.edges:
        engine.add_edge(edge.from_node, edge.to_node)

    paths = engine.find_paths(source, target, cutoff)
    return {"paths": paths, "count": len(paths)}


@router.get("/investigations/{inv_id}/connected/{node_id}")
def find_connected(inv_id: str, node_id: str, db: Session = Depends(get_db)):
    """Find all nodes connected to given node."""
    inv = db.query(InvestigationModel).filter(InvestigationModel.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    engine = GraphEngine()
    for node in inv.nodes:
        engine.add_node(node.id)
    for edge in inv.edges:
        engine.add_edge(edge.from_node, edge.to_node)

    connected = engine.find_connected(node_id)
    return {"connected": connected, "count": len(connected)}


def _node_color(node_type: str, trust_level: int) -> str:
    """Return color based on node type and trust level."""
    type_colors = {
        "email": "#ef4444",
        "phone": "#f97316",
        "person": "#8b5cf6",
        "organization": "#06b6d4",
        "social_account": "#10b981",
        "domain": "#f59e0b",
        "ip": "#ec4899",
        "event": "#6366f1",
        "document": "#64748b",
    }
    base = type_colors.get(node_type, "#6366f1")
    return base
