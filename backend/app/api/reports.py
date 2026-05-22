"""OsintHAM — Report Generation API"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db, InvestigationModel

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/investigations/{inv_id}/report")
def get_report_json(inv_id: str, db: Session = Depends(get_db)):
    """Generate JSON report."""
    inv = db.query(InvestigationModel).filter(InvestigationModel.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    nodes = []
    for n in inv.nodes:
        nodes.append({
            "id": n.id,
            "type": n.type,
            "label": n.label,
            "trust_level": n.trust_level,
            "data": json.loads(n.data) if n.data else {},
            "source": n.source,
        })

    edges = []
    for e in inv.edges:
        edges.append({
            "from": e.from_node,
            "to": e.to_node,
            "label": e.label,
            "trust_level": e.trust_level,
        })

    return {
        "report_type": "osintham_investigation",
        "generated_at": datetime.utcnow().isoformat(),
        "investigation": {
            "id": inv.id,
            "title": inv.title,
            "description": inv.description,
            "status": inv.status,
            "created_at": inv.created_at.isoformat(),
        },
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": _count_types(nodes),
            "avg_trust": _avg_trust(nodes),
        },
        "nodes": nodes,
        "edges": edges,
    }


@router.get("/investigations/{inv_id}/report/html", response_class=HTMLResponse)
def get_report_html(inv_id: str, db: Session = Depends(get_db)):
    """Generate HTML report."""
    inv = db.query(InvestigationModel).filter(InvestigationModel.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    nodes_html = ""
    for n in inv.nodes:
        data = json.loads(n.data) if n.data else {}
        data_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in data.items())
        trust_badge = _trust_badge(n.trust_level)
        nodes_html += f"""
        <div class="node-card">
            <h3>{n.label} <span class="badge">{n.type}</span> {trust_badge}</h3>
            <p><strong>ID:</strong> {n.id}</p>
            <p><strong>Source:</strong> {n.source or 'N/A'}</p>
            {f'<table>{data_rows}</table>' if data_rows else ''}
        </div>"""

    edges_html = ""
    for e in inv.edges:
        edges_html += f"""
        <div class="edge-card">
            <p><strong>{e.from_node}</strong> → <strong>{e.to_node}</strong></p>
            <p>Label: {e.label or 'N/A'} | Trust: {e.trust_level}/5</p>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>OsintHAM Report — {inv.title}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; background: #f8f9fa; }}
        h1 {{ color: #1e293b; border-bottom: 3px solid #6366f1; padding-bottom: 0.5rem; }}
        h2 {{ color: #334155; margin-top: 2rem; }}
        .meta {{ color: #64748b; font-size: 0.9rem; }}
        .node-card, .edge-card {{ background: white; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .badge {{ background: #6366f1; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }}
        .trust-5 {{ background: #10b981; }} .trust-4 {{ background: #34d399; }}
        .trust-3 {{ background: #fbbf24; }} .trust-2 {{ background: #f97316; }} .trust-1 {{ background: #ef4444; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; }}
        td {{ padding: 4px 8px; border-bottom: 1px solid #e2e8f0; }}
        td:first-child {{ font-weight: bold; color: #475569; width: 30%; }}
    </style>
</head>
<body>
    <h1>🕷️ OsintHAM Investigation Report</h1>
    <p class="meta">Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>

    <h2>📋 Investigation: {inv.title}</h2>
    <p>{inv.description or 'No description'}</p>
    <p class="meta">Status: {inv.status} | Created: {inv.created_at.strftime('%Y-%m-%d')}</p>

    <h2>🔵 Nodes ({len(inv.nodes)})</h2>
    {nodes_html or '<p>No nodes yet.</p>'}

    <h2>🔗 Edges ({len(inv.edges)})</h2>
    {edges_html or '<p>No edges yet.</p>'}
</body>
</html>"""


@router.get("/investigations/{inv_id}/report/markdown", response_class=PlainTextResponse)
def get_report_markdown(inv_id: str, db: Session = Depends(get_db)):
    """Generate Markdown report."""
    inv = db.query(InvestigationModel).filter(InvestigationModel.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    md = f"# 🕷️ OsintHAM Report: {inv.title}\n\n"
    md += f"> Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
    md += f"> Status: {inv.status}\n\n"
    md += f"## Description\n{inv.description or 'N/A'}\n\n"
    md += f"## Nodes ({len(inv.nodes)})\n\n"
    md += "| Type | Label | Trust | Source |\n"
    md += "|------|-------|-------|--------|\n"
    for n in inv.nodes:
        md += f"| {n.type} | {n.label} | {'⭐' * n.trust_level} | {n.source or '-'} |\n"
    md += f"\n## Edges ({len(inv.edges)})\n\n"
    md += "| From | To | Label | Trust |\n"
    md += "|------|----|-------|-------|\n"
    for e in inv.edges:
        md += f"| {e.from_node[:12]}... | {e.to_node[:12]}... | {e.label or '-'} | {'⭐' * e.trust_level} |\n"
    return md


def _count_types(nodes: list) -> dict:
    counts = {}
    for n in nodes:
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    return counts


def _avg_trust(nodes: list) -> float:
    if not nodes:
        return 0
    return round(sum(n["trust_level"] for n in nodes) / len(nodes), 1)


def _trust_badge(level: int) -> str:
    labels = {5: "Verified", 4: "Reliable", 3: "Uncertain", 2: "Dubious", 1: "Rumor"}
    return f'<span class="badge trust-{level}">{labels.get(level, "?")}</span>'
