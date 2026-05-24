"""OsintHAM — ScannerAgent

Runs a single OSINT scanner tool against a target.
Wraps the existing scanners/ module and returns structured ScanResult.

Supported scanner tools:
  - email:      Full email analysis (DNS, MX, SPF, DMARC, HIBP, social)
  - domain:     DNS, WHOIS, SSL, web tech, subdomain enumeration
  - ip:         Geo, ASN, reputation, reverse DNS
  - username:   Social platform search, GitHub/GitLab, HIBP
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional, Callable, Awaitable

from app.agents import BaseAgent, ExecutionContext
from app.models import (
    AgentConfig,
    AgentConstraints,
    AgentRole,
    ScanResult,
    ScanStatus,
    TargetType,
)
from app.osint_registry import ToolsRegistry

logger = logging.getLogger("osintham.agents.scanner")

# Type alias for scanner functions
ScannerFunc = Callable[..., Awaitable[dict[str, Any]]]


class ScannerAgent(BaseAgent):
    """Runs a single OSINT scanner and returns a ScanResult."""

    role = AgentRole.SCANNER

    # Map of tool names to the scanner coroutines in scanners/
    _SCANNER_MAP: dict[str, str] = {
        "email":      "app.scanners:scan_email",
        "domain":     "app.scanners:scan_domain",
        "ip":         "app.scanners.ip_username:scan_ip",
        "username":   "app.scanners.ip_username:scan_username",
    }

    # Tools that can be invoked (slug -> scanner tool name)
    _TOOL_TO_SCANNER: dict[str, str] = {}

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        constraints: Optional[AgentConstraints] = None,
        tools_registry: Optional[ToolsRegistry] = None,
    ):
        super().__init__(config=config, constraints=constraints)
        self.registry = tools_registry or ToolsRegistry()
        self._lazy_load_scanners()

    def _lazy_load_scanners(self):
        """Import scanner functions lazily to avoid circular imports."""
        if ScannerAgent._TOOL_TO_SCANNER:
            return  # already loaded

        try:
            from app.scanners import scan_email
            from app.scanners.domain import scan_domain
            from app.scanners.ip_username import scan_ip, scan_username

            ScannerAgent._TOOL_TO_SCANNER = {
                "email":    "email",
                "domain":   "domain",
                "ip":       "ip",
                "username": "username",
            }
            ScannerAgent._SCANNER_FUNCS = {
                "email":    scan_email,
                "domain":   scan_domain,
                "ip":       scan_ip,
                "username": scan_username,
            }
        except ImportError as e:
            logger.warning(f"Could not import scanners: {e}")
            ScannerAgent._SCANNER_FUNCS = {}

    async def run(
        self,
        ctx: ExecutionContext,
        *,
        target: str,
        scanner_tool: str,
        target_type: TargetType = TargetType.AUTO,
        options: Optional[dict[str, Any]] = None,
    ) -> ScanResult:
        """Execute a single scan.

        Args:
            target:       The value to scan (email, domain, IP, username)
            scanner_tool: Which scanner to use ("email", "domain", "ip", "username")
            target_type:  Explicit target type (auto-detected if AUTO)
            options:      Extra options passed to the scanner
        """
        self._lazy_load_scanners()
        options = options or {}

        # Auto-detect target type
        if target_type == TargetType.AUTO:
            target_type = self._detect_target_type(target)

        # Resolve scanner function
        func_name = self._TOOL_TO_SCANNER.get(scanner_tool)
        scanner_func = getattr(self, "_SCANNER_FUNCS", {}).get(func_name or scanner_tool)

        if scanner_func is None:
            return ScanResult(
                tool=scanner_tool,
                target=target,
                target_type=target_type,
                status=ScanStatus.ERROR,
                error=f"Unknown scanner tool: {scanner_tool!r}. "
                      f"Available: {list(self._TOOL_TO_SCANNER.keys())}",
            )

        # Verify target type matches scanner
        expected = self._scanner_expected_type(scanner_tool)
        if expected and target_type != expected and target_type != TargetType.AUTO:
            logger.warning(
                f"Target type {target_type.value} may not match scanner "
                f"{scanner_tool} (expects {expected.value})"
            )

        # Check tool availability
        if not self.registry.check_tool_installed(scanner_tool):
            logger.info(
                f"Tool {scanner_tool} not installed as CLI — "
                f"using built-in Python scanner"
            )

        # Run scanner
        start = time.monotonic()
        try:
            raw = await scanner_func(target)
            duration_ms = int((time.monotonic() - start) * 1000)

            # Parse result into ScanResult
            success = raw.get("success", True)
            errors = raw.get("errors", [])
            data = raw.get("data", raw)  # normalize

            # Wrap scalar data into list
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                data = [{"value": data}] if data else []

            status = ScanStatus.DONE if success and not errors else (
                ScanStatus.PARTIAL if success else ScanStatus.ERROR
            )

            result = ScanResult(
                tool=scanner_tool,
                target=target,
                target_type=target_type,
                status=status,
                data=data,
                metadata={
                    "duration_ms": duration_ms,
                    "records_found": len(data),
                    "agent_id": ctx.agent_id,
                    "tools_used": raw.get("metadata", {}).get("tools_used", []),
                },
                error="; ".join(errors) if errors else None,
                duration_ms=duration_ms,
            )

            self._save_json(ctx, "scan_result.json", result.to_dict())
            return result

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error(f"Scanner {scanner_tool} failed: {exc}")
            return ScanResult(
                tool=scanner_tool,
                target=target,
                target_type=target_type,
                status=ScanStatus.ERROR,
                error=str(exc),
                duration_ms=duration_ms,
            )

    def _error_result(self, error: Optional[Exception], duration_ms: int) -> ScanResult:
        return ScanResult(
            tool="unknown",
            target="unknown",
            target_type=TargetType.AUTO,
            status=ScanStatus.ERROR,
            error=str(error) if error else "Unknown error",
            duration_ms=duration_ms,
        )

    # ── Helpers ────────────────────────────────────────────

    @staticmethod
    def _detect_target_type(target: str) -> TargetType:
        if "@" in target:
            return TargetType.EMAIL
        import re
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", target):
            return TargetType.IP
        if re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", target):
            return TargetType.DOMAIN
        if re.match(r"^[a-zA-Z0-9_.-]{3,30}$", target):
            return TargetType.USERNAME
        return TargetType.URL

    @staticmethod
    def _scanner_expected_type(scanner_tool: str) -> Optional[TargetType]:
        return {
            "email":    TargetType.EMAIL,
            "domain":   TargetType.DOMAIN,
            "ip":       TargetType.IP,
            "username": TargetType.USERNAME,
        }.get(scanner_tool)

    @classmethod
    def available_scanners(cls) -> list[str]:
        cls._lazy_load_scanners = cls._lazy_load_scanners  # ensure exists
        return list(cls._TOOL_TO_SCANNER.keys())
