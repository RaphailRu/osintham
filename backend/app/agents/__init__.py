"""OsintHAM — Base Agent

All agents inherit from BaseAgent which provides:
  - Lifecycle management (start / stop / cancel)
  - Structured logging
  - Error handling with retry
  - Result persistence
  - Execution context (investigation_id, agent_id, timestamps)
"""
from __future__ import annotations

import asyncio
import logging
import time
import traceback
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.models import (
    AgentConfig,
    AgentConstraints,
    AgentRole,
    ScanStatus,
)

logger = logging.getLogger("osintham.agents")


# ═══════════════════════════════════════════════════════════════
# Execution Context
# ═══════════════════════════════════════════════════════════════

@dataclass
class ExecutionContext:
    """Runtime context passed to every agent run."""
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    investigation_id: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    work_dir: str = ""
    cancelled: bool = False

    @property
    def agent_dir(self) -> Path:
        base = Path(self.work_dir) if self.work_dir else Path.home() / ".osintham" / "agents"
        p = base / self.agent_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def log_file(self) -> Path:
        return self.agent_dir / "agent.log"


# ═══════════════════════════════════════════════════════════════
# Base Agent
# ═══════════════════════════════════════════════════════════════

class BaseAgent(ABC):
    """Abstract base class for all OsintHAM agents.

    Subclasses must implement:
      - role: AgentRole  (class attribute)
      - async run(**kwargs) -> Any  (the actual work)

    Usage:
        agent = SomeAgent(config, constraints)
        result = await agent.execute(ctx, **kwargs)
    """

    role: AgentRole = AgentRole.SCANNER  # override in subclass

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        constraints: Optional[AgentConstraints] = None,
    ):
        self.config = config or AgentConfig(role=self.role, name=self.__class__.__name__)
        self.constraints = constraints or AgentConstraints()
        self._cancelled = False
        self._retries = 0

    # ── Lifecycle ──────────────────────────────────────────

    async def execute(
        self,
        ctx: ExecutionContext,
        **kwargs: Any,
    ) -> Any:
        """Run the agent with logging, retry, and error handling."""
        log_path = ctx.log_file
        file_handler = logging.FileHandler(str(log_path))
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        ))
        logger.addHandler(file_handler)

        logger.info(f"[{self.role.value}] Agent {ctx.agent_id} started")
        logger.info(f"[{self.role.value}] Config: {self.config}")

        start = time.monotonic()
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            if ctx.cancelled or self._cancelled:
                logger.warning(f"[{self.role.value}] Cancelled before attempt {attempt}")
                break

            if attempt > 0:
                logger.info(f"[{self.role.value}] Retry {attempt}/{self.config.max_retries}")
                await asyncio.sleep(self.constraints.retry_delay_sec * attempt)

            try:
                result = await asyncio.wait_for(
                    self.run(ctx, **kwargs),
                    timeout=self.config.timeout_sec,
                )
                elapsed = int((time.monotonic() - start) * 1000)
                logger.info(f"[{self.role.value}] Completed in {elapsed}ms")
                return result

            except asyncio.TimeoutError:
                elapsed = int((time.monotonic() - start) * 1000)
                logger.error(
                    f"[{self.role.value}] Timeout after {elapsed}ms "
                    f"(limit: {self.config.timeout_sec}s)"
                )
                last_error = TimeoutError(
                    f"Agent {self.role.value} timed out after {self.config.timeout_sec}s"
                )

            except Exception as exc:
                elapsed = int((time.monotonic() - start) * 1000)
                logger.error(
                    f"[{self.role.value}] Error on attempt {attempt}: {exc}"
                )
                logger.debug(traceback.format_exc())
                last_error = exc

        # All retries exhausted
        elapsed = int((time.monotonic() - start) * 1000)
        logger.error(
            f"[{self.role.value}] All attempts failed after {elapsed}ms"
        )
        file_handler.close()
        logger.removeHandler(file_handler)
        return self._error_result(last_error, elapsed)

    def cancel(self):
        """Request cancellation of a running agent."""
        self._cancelled = True
        logger.info(f"[{self.role.value}] Cancellation requested")

    # ── Abstract Interface ─────────────────────────────────

    @abstractmethod
    async def run(self, ctx: ExecutionContext, **kwargs: Any) -> Any:
        """Override this with the agent's actual logic."""
        ...

    @abstractmethod
    def _error_result(self, error: Optional[Exception], duration_ms: int) -> Any:
        """Return a standardized error result when all retries fail."""
        ...

    # ── Helpers ────────────────────────────────────────────

    def _save_json(self, ctx: ExecutionContext, filename: str, data: Any):
        """Save JSON data to the agent's work directory."""
        import json
        path = ctx.agent_dir / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        logger.debug(f"[{self.role.value}] Saved {path}")

    def _load_json(self, ctx: ExecutionContext, filename: str) -> Any:
        """Load JSON data from the agent's work directory."""
        import json
        path = ctx.agent_dir / filename
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None
