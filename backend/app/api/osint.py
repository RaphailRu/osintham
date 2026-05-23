"""OsintHAM — OSINT Scanner API Router v4 (Modular)"""
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db, InvestigationModel, NodeModel, EdgeModel
from app.scanners import (
    scan_email, scan_domain, scan_ip, scan_username,
    ScanResult
)

router = APIRouter(prefix="/api/osint", tags=["osint"])


class ScanRequest(BaseModel):
    target: str
    target_type: str = "auto"
    investigation_id: Optional[str] = None
    auto_add_nodes: bool = False
    enabled_tools: Optional[List[str]] = None


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    message: str
    result: Optional[dict] = None
    errors: List[str] = []


def _node_color(node_type: str) -> str:
    colors = {
        "email": "#ef4444", "phone": "#f97316", "person": "#8b5cf6",
        "organization": "#06b6d4", "social_account": "#10b981",
        "domain": "#f59e0b", "ip": "#ec4899", "event": "#6366f1",
        "document": "#64748b",
    }
    return colors.get(node_type, "#6366f1")


@router.post("/scan")
async def start_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    """Run OSINT scan on target."""
    try:
        # Determine scan type
        target_type = req.target_type
        if target_type == "auto":
            if "@" in req.target:
                target_type = "email"
            elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', req.target):
                target_type = "ip"
            elif re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', req.target):
                target_type = "domain"
            elif re.match(r'^[a-zA-Z0-9_.-]{3,30}$', req.target):
                target_type = "username"
            else:
                target_type = "unknown"
        
        # Choose scanner
        scanner_map = {
            "email": scan_email,
            "domain": scan_domain,
            "ip": scan_ip,
            "username": scan_username,
        }
        
        if target_type not in scanner_map:
            return ScanResponse(
                scan_id=f"error_{datetime.now().timestamp()}",
                status="error",
                message=f"Unsupported target type: {target_type}",
                errors=[f"Cannot scan: {req.target}"]
            )
        
        scanner = scanner_map[target_type]
        
        # Start scan in background
        scan_id = f"scan_{datetime.now().timestamp()}"
        background_tasks.add_task(
            run_scan_background,
            scan_id,
            req.target,
            target_type,
            scanner,
            req.investigation_id,
            req.auto_add_nodes,
            req.enabled_tools
        )
        
        return ScanResponse(
            scan_id=scan_id,
            status="processing",
            message=f"Starting {target_type} scan for: {req.target}"
        )
        
    except Exception as e:
        return ScanResponse(
            scan_id=f"error_{datetime.now().timestamp()}",
            status="error",
            message=f"Scan request failed: {str(e)}",
            errors=[str(e)]
        )


async def run_scan_background(
    scan_id: str,
    target: str,
    target_type: str,
    scanner_func,
    investigation_id: Optional[str],
    auto_add_nodes: bool,
    enabled_tools: Optional[List[str]]
):
    """Run scan in background and optionally add to graph."""
    try:
        result = await scanner_func(target)
        
        # Optionally add to graph
        if auto_add_nodes and investigation_id:
            await add_scan_to_graph(investigation_id, result)
        
        # Save to database (in production: use proper DB)
        # For now: log to file
        with open(f"/tmp/osint_scans_{scan_id}.json", "w") as f:
            json.dump(result, f, indent=2)
            
    except Exception as e:
        # Log error
        with open(f"/tmp/osint_scans_{scan_id}_error.json", "w") as f:
            json.dump({"error": str(e)}, f)


@router.get("/results/{scan_id}")
async def get_scan_results(scan_id: str):
    """Get scan results by ID."""
    try:
        # Check if results file exists
        import os
        results_file = f"/tmp/osint_scans_{scan_id}.json"
        if os.path.exists(results_file):
            with open(results_file) as f:
                return json.load(f)
        
        error_file = f"/tmp/osint_scans_{scan_id}_error.json"
        if os.path.exists(error_file):
            with open(error_file) as f:
                return {"status": "error", "error": json.load(f)["error"]}
        
        return {"status": "pending", "message": "Scan is still running"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.get("/email/{email}")
async def scan_email_endpoint(email: str):
    """Scan specific email address."""
    try:
        result = await scan_email(email)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email scan failed: {str(e)}")


@router.get("/domain/{domain}")
async def scan_domain_endpoint(domain: str):
    """Scan specific domain."""
    try:
        result = await scan_domain(domain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Domain scan failed: {str(e)}")


@router.get("/ip/{ip}")
async def scan_ip_endpoint(ip: str):
    """Scan specific IP address."""
    try:
        result = await scan_ip(ip)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IP scan failed: {str(e)}")


@router.get("/username/{username}")
async def scan_username_endpoint(username: str):
    """Scan specific username."""
    try:
        result = await scan_username(username)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Username scan failed: {str(e)}")


@router.get("/health")
async def check_health():
    """Check OSINT scanner health."""
    return {
        "status": "healthy",
        "scanners": ["email", "domain", "ip", "username"],
        "features": [
            "DNS analysis",
            "WHOIS lookup",
            "SSL certificate analysis",
            "Social media search",
            "Geolocation",
            "ASN lookup",
            "Reputation checking",
            "Subdomain enumeration"
        ]
    }


async def add_scan_to_graph(investigation_id: str, scan_result: dict):
    """Add scan results to investigation graph."""
    try:
        db = next(get_db())
        
        # Add main node
        main_node = NodeModel(
            investigation_id=investigation_id,
            label=scan_result.get("target", ""),
            type=scan_result.get("scan_type", "unknown"),
            data=scan_result,
            trust_level=3  # Medium trust for automated scans
        )
        db.add(main_node)
        db.commit()
        
        # Add related nodes (social accounts, domains, etc.)
        if scan_result.get("social_accounts"):
            for account in scan_result["social_accounts"]:
                node = NodeModel(
                    investigation_id=investigation_id,
                    label=f"{account.get('platform', '')}: {account.get('username', '')}",
                    type="social_account",
                    data=account,
                    trust_level=2
                )
                db.add(node)
                db.commit()
                
                # Add edge
                edge = EdgeModel(
                    investigation_id=investigation_id,
                    source_id=main_node.id,
                    target_id=node.id,
                    label="found_on"
                )
                db.add(edge)
                db.commit()
        
        db.close()
        
    except Exception as e:
        print(f"Failed to add scan to graph: {str(e)}")


# Import re at the top
import re