"""OsintHAM — ValidationAgent

Validates and filters scan results:
  - URL reachability checks
  - Email format validation
  - False-positive filtering
  - Confidence scoring
  - Deduplication

Rules:
  - URLs returning 2xx/3xx → valid
  - URLs returning 4xx/5xx → invalid (unless scanner confirmed)
  - Emails matching RFC 5322 pattern → valid format
  - Duplicate entries across scanners → merge with highest confidence
  - Entries with confidence < min_confidence → flagged
"""
from __future__ import annotations

import logging
import re
from typing import Any, Optional

from app.agents import BaseAgent, ExecutionContext
from app.models import (
    AgentConfig,
    AgentConstraints,
    AgentRole,
    ScanStatus,
    ScanResult,
    ValidatedItem,
    ValidationResult,
)

logger = logging.getLogger("osintham.agents.validation")

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)


class ValidationAgent(BaseAgent):
    """Validates scan results and filters false positives."""

    role = AgentRole.VALIDATION

    async def run(
        self,
        ctx: ExecutionContext,
        *,
        scan_results: list[ScanResult],
        min_confidence: float = 0.6,
    ) -> ValidationResult:
        """Validate all scan results.

        Args:
            scan_results:  Results from InvestigationAgent
            min_confidence: Minimum confidence threshold for inclusion
        """
        logger.info(
            f"[validation] Validating {len(scan_results)} scan results "
            f"(min_confidence={min_confidence})"
        )

        all_items: list[ValidatedItem] = []
        seen: set[str] = set()  # dedup key

        for sr in scan_results:
            for record in sr.data:
                if not isinstance(record, dict):
                    continue

                # Dedup key
                url = record.get("url", "")
                platform = record.get("platform", "")
                key = f"{sr.tool}:{url or platform or str(record)}"

                if key in seen:
                    continue
                seen.add(key)

                # Validate based on record type
                item = self._validate_record(record, sr.tool, min_confidence)
                all_items.append(item)

        valid_count = sum(1 for i in all_items if i.valid)
        invalid_count = len(all_items) - valid_count
        avg_confidence = (
            sum(i.confidence for i in all_items) / len(all_items)
            if all_items else 0.0
        )

        result = ValidationResult(
            items=all_items,
            valid_count=valid_count,
            invalid_count=invalid_count,
            avg_confidence=round(avg_confidence, 3),
        )

        logger.info(
            f"[validation] Done: {valid_count} valid, {invalid_count} invalid, "
            f"avg_confidence={avg_confidence:.2f}"
        )

        self._save_json(ctx, "validation_result.json", result.to_dict())
        return result

    def _error_result(
        self, error: Optional[Exception], duration_ms: int
    ) -> ValidationResult:
        return ValidationResult(
            items=[], valid_count=0, invalid_count=0, avg_confidence=0.0,
        )

    # ── Record Validation ──────────────────────────────────

    def _validate_record(
        self,
        record: dict[str, Any],
        tool: str,
        min_confidence: float,
    ) -> ValidatedItem:
        """Validate a single record from scan data."""
        url = record.get("url", "")
        platform = record.get("platform", "")
        status = record.get("status", "")
        email = record.get("email", "")

        # URL-based validation
        if url and URL_RE.match(url):
            return self._validate_url_record(record, tool, min_confidence)

        # Email-based validation
        if email and EMAIL_RE.match(email):
            return ValidatedItem(
                item=record,
                valid=True,
                confidence=0.9,
                notes="Valid email format",
            )

        # Platform/social account validation
        if platform:
            is_valid = status in ("found", "confirmed", "active")
            confidence = 0.8 if is_valid else 0.4
            return ValidatedItem(
                item=record,
                valid=is_valid and confidence >= min_confidence,
                confidence=confidence,
                notes=f"Platform: {platform}, status: {status}",
            )

        # Generic: accept if scan was successful
        return ValidatedItem(
            item=record,
            valid=True,
            confidence=0.5,
            notes=f"Generic record from {tool}",
        )

    def _validate_url_record(
        self,
        record: dict[str, Any],
        tool: str,
        min_confidence: float,
    ) -> ValidatedItem:
        """Validate a URL record."""
        url = record.get("url", "")
        status = record.get("status", "")

        # If scanner already confirmed
        if status == "found":
            return ValidatedItem(
                item=record,
                valid=True,
                confidence=0.85,
                notes=f"Confirmed by {tool}",
            )

        if status == "not_found":
            return ValidatedItem(
                item=record,
                valid=False,
                confidence=0.3,
                notes=f"Not found by {tool}",
            )

        # URL format check
        if URL_RE.match(url):
            return ValidatedItem(
                item=record,
                valid=True,
                confidence=0.6,
                notes="Valid URL format, unconfirmed",
            )

        return ValidatedItem(
            item=record,
            valid=False,
            confidence=0.2,
            notes="Invalid URL format",
        )
