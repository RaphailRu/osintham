"""OsintHAM — OSINT Scanner API Router v2"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db, InvestigationModel, NodeModel, EdgeModel
from app.osint_engine import (
    validate_email, validate_phone, analyze_domain, analyze_ip,
    search_username, analyze_url, generate_hashes,
)
from app.osint_integrations import (
    run_sherlock, run_maigret, run_holehe, run_theharvester,
    check_hibp, check_shodan, check_censys, check_dnsdumpster,
    check_wayback, check_intelx, run_spiderfoot, run_exiftool,
    run_recon_ng, run_snoop, run_osintgram, run_x_osint,
    check_infoooze, check_leakcheck, run_breachhound,
    get_ghdb_queries, check_pimeyes, check_odnoklassniki, check_vk,
    get_google_earth_link, universal_search, run_full_osint,
)

router = APIRouter(prefix="/api/osint", tags=["osint"])


class ScanRequest(BaseModel):
    target: str
    target_type: str = "auto"
    investigation_id: Optional[str] = None
    auto_add_nodes: bool = False
    enabled_tools: Optional[list] = None


def _get_node_color(node_type: str) -> str:
    colors = {
        "email": "#ef4444", "phone": "#f97316", "person": "#8b5cf6",
        "organization": "#06b6d4", "social_account": "#10b981",
        "domain": "#f59e0b", "ip": "#ec4899", "event": "#6366f1",
        "document": "#64748b",
    }
    return colors.get(node_type, "#6366f1")


# ── Master Scanner ──

@router.post("/scan")
async def scan_full(req: ScanRequest):
    """Run full OSINT scan using all applicable tools."""
    try:
        tools = req.enabled_tools if req.enabled_tools else None
        result = await run_full_osint(req.target, req.target_type, tools)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/bulk-scan")
async def bulk_scan(requests: list[ScanRequest]):
    """Scan multiple targets."""
    results = []
    for req in requests:
        try:
            tools = req.enabled_tools if req.enabled_tools else None
            result = await run_full_osint(req.target, req.target_type, tools)
            results.append(result)
        except Exception as e:
            results.append({"target": req.target, "error": str(e)})
    return {"results": results, "total": len(requests)}


# ── Individual Tool Endpoints ──

@router.get("/sherlock/{username}")
async def scan_sherlock(username: str):
    return await run_sherlock(username)


@router.get("/maigret/{username}")
async def scan_maigret(username: str):
    return await run_maigret(username)


@router.get("/holehe/{email}")
async def scan_holehe(email: str):
    return await run_holehe(email)


@router.get("/theharvester/{domain}")
async def scan_harvester(domain: str):
    return await run_theharvester(domain)


@router.get("/hibp/{email}")
async def scan_hibp(email: str):
    return await check_hibp(email)


@router.get("/shodan")
async def scan_shodan(ip: str = "", domain: str = ""):
    return await check_shodan(ip=ip, domain=domain)


@router.get("/censys")
async def scan_censys(ip: str = "", domain: str = ""):
    return await check_censys(ip=ip, domain=domain)


@router.get("/dnsdumpster/{domain}")
async def scan_dnsdumpster(domain: str):
    return await check_dnsdumpster(domain)


@router.get("/wayback")
async def scan_wayback(url: str = "", domain: str = "", limit: int = 20):
    return await check_wayback(url=url, domain=domain, limit=limit)


@router.get("/intelx/{query}")
async def scan_intelx(query: str):
    return await check_intelx(query)


@router.get("/spiderfoot/{target}")
async def scan_spiderfoot(target: str):
    return await run_spiderfoot(target)


@router.get("/exiftool")
async def scan_exiftool(file_path: str):
    return await run_exiftool(file_path)


@router.get("/recon-ng/{domain}")
async def scan_recon_ng(domain: str):
    return await run_recon_ng(domain)


@router.get("/snoop/{username}")
async def scan_snoop(username: str):
    return await run_snoop(username)


@router.get("/osintgram/{username}")
async def scan_osintgram(username: str):
    return await run_osintgram(username)


@router.get("/x-osint/{target}")
async def scan_x_osint(target: str):
    return await run_x_osint(target)


@router.get("/infoooze")
async def scan_infoooze(query: str, query_type: str = "ip"):
    return await check_infoooze(query, query_type)


@router.get("/leakcheck")
async def scan_leakcheck(query: str, query_type: str = "email"):
    return await check_leakcheck(query, query_type=query_type)


@router.get("/breachhound/{email}")
async def scan_breachhound(email: str):
    return await run_breachhound(email)


@router.get("/ghdb/{domain}")
async def scan_ghdb(domain: str):
    return get_ghdb_queries(domain)


@router.get("/pimeyes")
async def scan_pimeyes(image_url: str = ""):
    return await check_pimeyes(image_url=image_url)


@router.get("/odnoklassniki")
async def scan_ok(user_id: str = "", name: str = ""):
    return await check_odnoklassniki(user_id=user_id, name=name)


@router.get("/vk")
async def scan_vk(user_id: str = "", name: str = ""):
    return await check_vk(user_id=user_id, name=name)


@router.get("/google-earth")
async def google_earth(lat: float = 0, lon: float = 0, zoom: int = 15):
    return get_google_earth_link(lat, lon, zoom)


@router.get("/universal/{query}")
async def scan_universal(query: str):
    return await universal_search(query)


# ── Legacy v1 Endpoints ──

@router.get("/email/{email}")
def scan_email(email: str):
    return validate_email(email)


@router.get("/phone/{phone}")
def scan_phone(phone: str):
    return validate_phone(phone)


@router.get("/domain/{domain}")
def scan_domain(domain: str):
    return analyze_domain(domain)


@router.get("/ip/{ip}")
def scan_ip(ip: str):
    return analyze_ip(ip)


@router.get("/username/{username}")
def scan_username(username: str):
    return search_username(username)


@router.get("/url")
def scan_url(url: str):
    return analyze_url(url)


@router.get("/hash/{text}")
def get_hashes(text: str):
    return generate_hashes(text)


# ── Auto-Enrichment ──

@router.post("/enrich/{inv_id}")
async def enrich_investigation(inv_id: str, req: ScanRequest, db: Session = Depends(get_db)):
    """Scan target and auto-add results to investigation graph."""
    inv = db.query(InvestigationModel).filter(InvestigationModel.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    tools = req.enabled_tools if req.enabled_tools else None
    scan_result = await run_full_osint(req.target, req.target_type, tools)

    added_nodes = []
    node_id_map = {}

    for i, node_data in enumerate(scan_result.get("suggested_nodes", [])):
        node = NodeModel(
            investigation_id=inv_id,
            type=node_data.get("type", "person"),
            label=node_data.get("label", req.target),
            trust_level=node_data.get("trust_level", 3),
            data=json.dumps(node_data.get("data", {})),
            source=node_data.get("source", "OSINT scan"),
            color=_get_node_color(node_data.get("type", "person")),
        )
        db.add(node)
        db.flush()
        node_id_map[i] = node.id
        node_id_map[f"{node.type}_node"] = node.id
        added_nodes.append({"id": node.id, "label": node.label, "type": node.type})

    added_edges = []
    for edge_data in scan_result.get("suggested_edges", []):
        from_id = edge_data.get("from", "")
        to_id = edge_data.get("to", "")
        if from_id in node_id_map:
            from_id = node_id_map[from_id]
        if to_id in node_id_map:
            to_id = node_id_map[to_id]
        if not from_id or not to_id or from_id == to_id:
            continue
        edge = EdgeModel(
            investigation_id=inv_id,
            from_node=str(from_id),
            to_node=str(to_id),
            label=edge_data.get("label", "related to"),
            trust_level=3,
        )
        db.add(edge)
        db.flush()
        added_edges.append({"id": edge.id, "label": edge.label})

    db.commit()

    return {
        "scan_result": scan_result,
        "added_nodes": added_nodes,
        "added_edges": added_edges,
        "investigation_id": inv_id,
    }
