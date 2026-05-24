"""OsintHAM — InvestigationAgent

Orchestrates a full OSINT investigation by:
  1. Analyzing targets and scope
  2. Selecting appropriate scanners based on priority
  3. Running scanners in parallel (up to max_concurrent_scans)
  4. Collecting and aggregating results
  5. Delegating to ValidationAgent, CorrelationAgent, ReportAgent

Priority levels:
  QUICK    — Only fast scanners (< 15s each)
  STANDARD — + social search, DNS/WHOIS
  DEEP     — All available scanners, subdomain enum, etc.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from app.agents import BaseAgent, ExecutionContext
from app.agents.scanner_agent import ScannerAgent
from app.models import (
    AgentConfig,
    AgentConstraints,
    AgentRole,
    InvestigationResult,
    Priority,
    ScanResult,
    ScanStatus,
    Target,
    TargetType,
)

logger = logging.getLogger("osintham.agents.investigation")


# ═══════════════════════════════════════════════════════════════
# Scanner Selection Matrix
# ═══════════════════════════════════════════════════════════════

# Maps (priority, target_type) -> list of scanner tool names
SCANNER_MATRIX: dict[tuple[Priority, TargetType], list[str]] = {
    # QUICK
    (Priority.QUICK, TargetType.EMAIL):    ["email"],
    (Priority.QUICK, TargetType.USERNAME): ["username"],
    (Priority.QUICK, TargetType.DOMAIN):   ["domain"],
    (Priority.QUICK, TargetType.IP):       ["ip"],
    (Priority.QUICK, TargetType.PHONE):    [],
    (Priority.QUICK, TargetType.URL):      [],
    # STANDARD
    (Priority.STANDARD, TargetType.EMAIL):    ["email"],
    (Priority.STANDARD, TargetType.USERNAME): ["username"],
    (Priority.STANDARD, TargetType.DOMAIN):   ["domain"],
    (Priority.STANDARD, TargetType.IP):       ["ip"],
    (Priority.STANDARD, TargetType.PHONE):    [],
    (Priority.STANDARD, TargetType.URL):      [],
    # DEEP
    (Priority.DEEP, TargetType.EMAIL):    ["email"],
    (Priority.DEEP, TargetType.USERNAME): ["username"],
    (Priority.DEEP, TargetType.DOMAIN):   ["domain"],
    (Priority.DEEP, TargetType.IP):       ["ip"],
    (Priority.DEEP, TargetType.PHONE):    [],
    (Priority.DEEP, TargetType.URL):      [],
}


def _select_scanners(target_type: TargetType, priority: Priority) -> list[str]:
    """Return list of scanner tool names for given target type + priority."""
    key = (priority, target_type)
    if key in SCANNER_MATRIX:
        return SCANNER_MATRIX[key]
    # Fallback: try STANDARD, then QUICK
    for fallback in [Priority.STANDARD, Priority.QUICK]:
        key2 = (fallback, target_type)
        if key2 in SCANNER_MATRIX:
            return SCANNER_MATRIX[key2]
    return []


class InvestigationAgent(BaseAgent):
    """Orchestrates a full OSINT investigation with parallel scanning."""

    role = AgentRole.INVESTIGATION

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        constraints: Optional[AgentConstraints] = None,
    ):
        super().__init__(
            config=config or AgentConfig(
                role=self.role,
                name="InvestigationAgent",
                timeout_sec=600,
            ),
            constraints=constraints or AgentConstraints(),
        )
        self._scanner = ScannerAgent(constraints=self.constraints)
        self._children: list[BaseAgent] = []

    async def run(
        self,
        ctx: ExecutionContext,
        *,
        targets: list[Target],
        priority: Priority = Priority.STANDARD,
        title: str = "",
        investigation_id: Optional[str] = None,
    ) -> InvestigationResult:
        """Run a full investigation.

        Args:
            targets:          List of targets to investigate
            priority:         Investigation depth (quick / standard / deep)
            title:            Human-readable title
            investigation_id: Optional investigation ID (generated if not provided)
        """
        inv_id = investigation_id or f"inv_{int(time.time())}"
        start = time.monotonic()

        logger.info(
            f"[investigation] Starting '{title}' id={inv_id} "
            f"targets={len(targets)} priority={priority.value}"
        )

        result = InvestigationResult(
            id=inv_id,
            title=title or f"Investigation {inv_id}",
            targets=targets,
            status=ScanStatus.PENDING,
        )

        # Phase 1: Plan — determine which scanners to run for each target
        scan_plan: list[dict[str, Any]] = []
        for target in targets:
            scanners = _select_scanners(target.type, priority)
            for scanner_tool in scanners:
                scan_plan.append({
                    "target": target,
                    "scanner_tool": scanner_tool,
                })

        logger.info(
            f"[investigation] Plan: {len(scan_plan)} scans across "
            f"{len(targets)} targets"
        )

        # Phase 2: Execute scans in parallel (with concurrency limit)
        result.status = ScanStatus.PENDING
        semaphore = asyncio.Semaphore(self.constraints.max_concurrent_scans)

        async def _run_single_scan(plan_item: dict) -> ScanResult:
            async with semaphore:
                target: Target = plan_item["target"]
                scanner_tool: str = plan_item["scanner_tool"]

                logger.info(
                    f"[investigation] Running {scanner_tool} on "
                    f"{target.type.value}:{target.value}"
                )

                child_ctx = ExecutionContext(
                    investigation_id=inv_id,
                    work_dir=ctx.work_dir,
                )

                scan_result = await self._scanner.execute(
                    ctx=child_ctx,
                    target=target.value,
                    scanner_tool=scanner_tool,
                    target_type=target.type,
                )

                status_icon = "✓" if scan_result.status == ScanStatus.DONE else "✗"
                logger.info(
                    f"[investigation] {status_icon} {scanner_tool} → "
                    f"{scan_result.status.value} "
                    f"({scan_result.duration_ms}ms, "
                    f"{len(scan_result.data)} records)"
                )

                return scan_result

        # Run all scans concurrently (bounded by semaphore)
        scan_tasks = [_run_single_scan(item) for item in scan_plan]
        scan_results = await asyncio.gather(*scan_tasks, return_exceptions=True)

        # Collect results, converting exceptions to error results
        for i, sr in enumerate(scan_results):
            if isinstance(sr, BaseException):
                logger.error(f"[investigation] Scan task {i} raised: {sr}")
                target = scan_plan[i]["target"]
                error_result = ScanResult(
                    tool=scan_plan[i]["scanner_tool"],
                    target=target.value,
                    target_type=target.type,
                    status=ScanStatus.ERROR,
                    error=str(sr),
                )
                result.scan_results.append(error_result)
                result.errors.append(f"Scan {i}: {sr}")
            else:
                result.scan_results.append(sr)

        # Determine overall status
        statuses = {sr.status for sr in result.scan_results}
        if all(s == ScanStatus.DONE for s in statuses):
            result.status = ScanStatus.DONE
        elif ScanStatus.ERROR in statuses and len(statuses) == 1:
            result.status = ScanStatus.ERROR
        elif ScanStatus.PARTIAL in statuses or ScanStatus.ERROR in statuses:
            result.status = ScanStatus.PARTIAL
        else:
            result.status = ScanStatus.DONE

        result.duration_ms = int((time.monotonic() - start) * 1000)
        result.completed_at = time.strftime("%Y-%m-%dT%H:%M:%S")

        logger.info(
            f"[investigation] Completed {inv_id}: status={result.status.value} "
            f"scans={len(result.scan_results)} "
            f"duration={result.duration_ms}ms"
        )

        # Save full result
        self._save_json(ctx, "investigation_result.json", result.to_dict())

        return result

    def cancel(self):
        """Cancel this investigation and all child agents."""
        super().cancel()
        for child in self._children:
            child.cancel()
        self._scanner.cancel()
        logger.info("[investigation] Cancelled all child agents")

    def _error_result(
        self, error: Optional[Exception], duration_ms: int
    ) -> InvestigationResult:
        return InvestigationResult(
            status=ScanStatus.ERROR,
            errors=[str(error) if error else "Investigation failed"],
            duration_ms=duration_ms,
        )
