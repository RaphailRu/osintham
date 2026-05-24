"""OsintHAM — Agent System API Router

REST endpoints for running the agent system:
  POST /api/agents/investigate    — Run full investigation
  GET  /api/agents/status/{id}     — Check investigation status
  GET  /api/agents/result/{id}     — Get investigation result
  DELETE /api/agents/cancel/{id}    — Cancel running investigation
  GET  /api/agents/scanners        — List available scanner agents
  GET  /api/agents/health          — Agent system health check
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger("osintham.api.agents")

router = APIRouter(prefix="/api/agents", tags=["agents"])

# In-memory store for running investigations
# In production, replace with Redis / DB
_investigations: dict[str, dict] = {}


# ═══════════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════════

class InvestigationRequest(BaseModel):
    title: str = ""
    targets: list[dict]  # [{"type": "email", "value": "test@example.com"}, ...]
    priority: str = "standard"  # quick | standard | deep
    auto_validate: bool = True
    auto_correlate: bool = True
    auto_report: bool = True


class InvestigationResponse(BaseModel):
    investigation_id: str
    status: str
    message: str


class InvestigationStatus(BaseModel):
    investigation_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    duration_ms: int = 0
    scan_count: int = 0
    error_count: int = 0


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════

@router.post("/investigate", response_model=InvestigationResponse)
async def start_investigation(
    req: InvestigationRequest,
    background_tasks: BackgroundTasks,
):
    """Start a new OSINT investigation with the agent system."""
    inv_id = f"inv_{uuid.uuid4().hex[:8]}"

    _investigations[inv_id] = {
        "id": inv_id,
        "title": req.title,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "duration_ms": 0,
        "scan_count": 0,
        "error_count": 0,
        "result": None,
    }

    background_tasks.add_task(
        _run_investigation,
        inv_id,
        req,
    )

    logger.info(f"[api] Started investigation {inv_id} with {len(req.targets)} targets")

    return InvestigationResponse(
        investigation_id=inv_id,
        status="processing",
        message=f"Investigation started with {len(req.targets)} targets",
    )


@router.get("/status/{inv_id}", response_model=InvestigationStatus)
async def get_investigation_status(inv_id: str):
    """Get the current status of an investigation."""
    inv = _investigations.get(inv_id)
    if not inv:
        # Check if there's a saved result on disk
        result_path = Path(f"/tmp/osintham/investigations/{inv_id}/investigation_result.json")
        if result_path.exists():
            return InvestigationStatus(
                investigation_id=inv_id,
                status="completed",
                completed_at="unknown",
                scan_count=-1,
            )
        raise HTTPException(status_code=404, detail=f"Investigation {inv_id} not found")

    return InvestigationStatus(
        investigation_id=inv_id,
        status=inv["status"],
        created_at=inv["created_at"],
        completed_at=inv.get("completed_at"),
        duration_ms=inv.get("duration_ms", 0),
        scan_count=inv.get("scan_count", 0),
        error_count=inv.get("error_count", 0),
    )


@router.get("/result/{inv_id}")
async def get_investigation_result(inv_id: str):
    """Get the full investigation result."""
    inv = _investigations.get(inv_id)
    if inv and inv.get("result"):
        return inv["result"]

    # Try loading from disk
    result_path = Path(f"/tmp/osintham/investigations/{inv_id}/investigation_result.json")
    if result_path.exists():
        with open(result_path) as f:
            return json.load(f)

    if inv:
        return {"status": inv["status"], "message": "Investigation still running"}

    raise HTTPException(status_code=404, detail=f"Investigation {inv_id} not found")


@router.delete("/cancel/{inv_id}")
async def cancel_investigation(inv_id: str):
    """Cancel a running investigation."""
    inv = _investigations.get(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {inv_id} not found")
    if inv["status"] in ("completed", "error"):
        return {"message": f"Investigation already {inv['status']}"}

    inv["status"] = "cancelled"
    logger.info(f"[api] Cancelled investigation {inv_id}")
    return {"message": "Investigation cancelled"}


@router.get("/scanners")
async def list_scanners():
    """List available scanner agents."""
    from app.agents.scanner_agent import ScannerAgent
    return {
        "scanners": ScannerAgent.available_scanners(),
        "description": "Available OSINT scanner tools",
    }


@router.get("/health")
async def agent_health():
    """Check agent system health."""
    return {
        "status": "healthy",
        "active_investigations": sum(
            1 for inv in _investigations.values()
            if inv["status"] == "processing"
        ),
        "total_investigations": len(_investigations),
        "available_scanners": ["email", "domain", "ip", "username"],
        "available_correlation": True,
        "available_validation": True,
        "available_report": True,
    }


# ═══════════════════════════════════════════════════════════════
# Background Task
# ═══════════════════════════════════════════════════════════════

async def _run_investigation(inv_id: str, req: InvestigationRequest):
    """Run the full investigation pipeline in background."""
    from app.agents.investigation_agent import InvestigationAgent
    from app.agents.correlation_agent import CorrelationAgent
    from app.agents.validation_agent import ValidationAgent
    from app.agents.report_agent import ReportAgent
    from app.agents import ExecutionContext
    from app.models import Target, TargetType, Priority

    inv_record = _investigations[inv_id]
    inv_record["status"] = "processing"

    try:
        # Parse targets
        targets = []
        for t in req.targets:
            tt = TargetType(t.get("type", "auto"))
            targets.append(Target(type=tt, value=t["value"], label=t.get("label", "")))

        priority = Priority(req.priority)

        # Create work directory
        base_dir = Path.home() / ".osintham" / "investigations"
        work_dir = str(base_dir / inv_id)
        os.makedirs(work_dir, exist_ok=True)

        ctx = ExecutionContext(investigation_id=inv_id, work_dir=work_dir)

        # Phase 1: Investigation (parallel scans)
        agent = InvestigationAgent()
        inv_result = await agent.execute(
            ctx=ctx,
            targets=targets,
            priority=priority,
            title=req.title,
            investigation_id=inv_id,
        )

        inv_record["scan_count"] = len(inv_result.scan_results)
        inv_record["error_count"] = len(inv_result.errors)

        # Phase 2: Validation (optional)
        validation_result = None
        if req.auto_validate and inv_result.scan_results:
            val_agent = ValidationAgent()
            validation_result = await val_agent.execute(
                ctx=ctx,
                scan_results=inv_result.scan_results,
                min_confidence=0.6,
            )
            inv_result.validation_result = validation_result

        # Phase 3: Correlation (optional)
        correlation_result = None
        if req.auto_correlate and inv_result.scan_results:
            corr_agent = CorrelationAgent()
            correlation_result = await corr_agent.execute(
                ctx=ctx,
                scan_results=inv_result.scan_results,
            )
            inv_result.correlation_result = correlation_result

        # Phase 4: Report (optional)
        report = None
        if req.auto_report:
            report_agent = ReportAgent()
            report = await report_agent.execute(
                ctx=ctx,
                investigation=inv_result,
                validation=validation_result,
                correlation=correlation_result,
            )
            inv_result.report = report

        inv_result.status = inv_result.status
        inv_record["status"] = "completed"
        inv_record["completed_at"] = datetime.utcnow().isoformat()
        inv_record["duration_ms"] = inv_result.duration_ms
        inv_record["result"] = inv_result.to_dict()

        logger.info(
            f"[api] Investigation {inv_id} completed: "
            f"{inv_record['scan_count']} scans, "
            f"{inv_record['error_count']} errors"
        )

    except Exception as exc:
        logger.error(f"[api] Investigation {inv_id} failed: {exc}")
        inv_record["status"] = "error"
        inv_record["completed_at"] = datetime.utcnow().isoformat()
        inv_record["result"] = {"error": str(exc)}
