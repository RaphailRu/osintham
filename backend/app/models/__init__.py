"""OsintHAM — Models Package
Re-exports all models from the agents subsystem.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════

class TargetType(str, Enum):
    EMAIL = "email"
    USERNAME = "username"
    DOMAIN = "domain"
    IP = "ip"
    PHONE = "phone"
    URL = "url"
    AUTO = "auto"


class ScanStatus(str, Enum):
    DONE = "done"
    PARTIAL = "partial"
    ERROR = "error"
    TIMEOUT = "timeout"
    PENDING = "pending"


class Priority(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class AgentRole(str, Enum):
    SCANNER = "scanner"
    INVESTIGATION = "investigation"
    CORRELATION = "correlation"
    VALIDATION = "validation"
    REPORT = "report"
    MONITOR = "monitor"


class EntityType(str, Enum):
    EMAIL = "email"
    USERNAME = "username"
    DOMAIN = "domain"
    IP = "ip"
    PHONE = "phone"
    PERSON = "person"
    ORGANIZATION = "organization"
    SOCIAL_ACCOUNT = "social_account"
    URL = "url"
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════
# Core Data Structures
# ═══════════════════════════════════════════════════════════════

@dataclass
class Target:
    type: TargetType
    value: str
    label: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.label:
            self.label = self.value


@dataclass
class ScanResult:
    tool: str
    target: str
    target_type: TargetType
    status: ScanStatus
    data: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    scan_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "tool": self.tool,
            "target": self.target,
            "target_type": self.target_type.value,
            "status": self.status.value,
            "data": self.data,
            "metadata": self.metadata,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


@dataclass
class ValidatedItem:
    item: dict[str, Any]
    valid: bool
    confidence: float
    notes: str = ""


@dataclass
class ValidationResult:
    items: list[ValidatedItem] = field(default_factory=list)
    valid_count: int = 0
    invalid_count: int = 0
    avg_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [
                {"item": i.item, "valid": i.valid, "confidence": i.confidence, "notes": i.notes}
                for i in self.items
            ],
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "avg_confidence": self.avg_confidence,
        }


@dataclass
class Entity:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    type: EntityType = EntityType.UNKNOWN
    label: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    source_tools: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    from_entity: str = ""
    to_entity: str = ""
    label: str = ""
    confidence: float = 0.5
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class CorrelationResult:
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    clusters: list[list[str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities": [
                {
                    "id": e.id, "type": e.type.value, "label": e.label,
                    "properties": e.properties, "confidence": e.confidence,
                    "source_tools": e.source_tools,
                }
                for e in self.entities
            ],
            "relationships": [
                {
                    "id": r.id, "from": r.from_entity, "to": r.to_entity,
                    "label": r.label, "confidence": r.confidence,
                }
                for r in self.relationships
            ],
            "clusters": self.clusters,
            "metadata": self.metadata,
        }


@dataclass
class Report:
    investigation_id: str = ""
    markdown: str = ""
    html: str = ""
    json_data: dict[str, Any] = field(default_factory=dict)
    graph_svg: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "markdown": self.markdown,
            "html": self.html,
            "json": self.json_data,
            "graph_svg": self.graph_svg,
            "created_at": self.created_at,
        }


@dataclass
class InvestigationResult:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    title: str = ""
    targets: list[Target] = field(default_factory=list)
    scan_results: list[ScanResult] = field(default_factory=list)
    validation_result: Optional[ValidationResult] = None
    correlation_result: Optional[CorrelationResult] = None
    report: Optional[Report] = None
    status: ScanStatus = ScanStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    duration_ms: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "targets": [{"type": t.type.value, "value": t.value, "label": t.label} for t in self.targets],
            "scan_results": [sr.to_dict() for sr in self.scan_results],
            "validation": self.validation_result.to_dict() if self.validation_result else None,
            "correlation": self.correlation_result.to_dict() if self.correlation_result else None,
            "report": self.report.to_dict() if self.report else None,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "errors": self.errors,
        }


# ═══════════════════════════════════════════════════════════════
# Agent Configuration
# ═══════════════════════════════════════════════════════════════

@dataclass
class AgentConstraints:
    max_concurrent_scans: int = 5
    max_scan_timeout_sec: int = 120
    max_investigation_timeout_sec: int = 600
    rate_limit_per_domain: int = 10
    min_confidence: float = 0.6
    max_retries: int = 1
    retry_delay_sec: float = 2.0


@dataclass
class AgentConfig:
    role: AgentRole
    name: str
    enabled: bool = True
    timeout_sec: int = 120
    max_retries: int = 1
    tools: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
