"""OsintHAM — CorrelationAgent

Analyzes results from multiple scanners to find connections:
  - Entity extraction from scan data
  - Relationship detection (shared domains, emails, IPs, etc.)
  - Graph clustering
  - Confidence scoring for discovered links

Algorithm:
  1. Extract all entities (emails, domains, IPs, usernames, URLs) from scan data
  2. Match entities across scanners (e.g., same domain found by DNS + WHOIS)
  3. Build relationships based on co-occurrence and shared attributes
  4. Cluster related entities
  5. Score confidence for each relationship
"""
from __future__ import annotations

import logging
import re
from typing import Any, Optional
from urllib.parse import urlparse

from app.agents import BaseAgent, ExecutionContext
from app.models import (
    AgentConfig,
    AgentConstraints,
    AgentRole,
    CorrelationResult,
    Entity,
    EntityType,
    Relationship,
    ScanResult,
)

logger = logging.getLogger("osintham.agents.correlation")


class CorrelationAgent(BaseAgent):
    """Finds connections between scan results and builds entity-relationship graph."""

    role = AgentRole.CORRELATION

    EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    DOMAIN_RE = re.compile(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?(?:\.[a-zA-Z]{2,})+")
    IP_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

    async def run(
        self,
        ctx: ExecutionContext,
        *,
        scan_results: list[ScanResult],
    ) -> CorrelationResult:
        """Build entity-relationship graph from scan results.

        Args:
            scan_results: List of ScanResult objects from InvestigationAgent
        """
        logger.info(
            f"[correlation] Analyzing {len(scan_results)} scan results"
        )

        # Phase 1: Extract & deduplicate entities
        all_entities: list[Entity] = []
        entity_index: dict[str, Entity] = {}  # key -> entity (dedup)

        for sr in scan_results:
            entities = self._extract_entities(sr)
            for entity in entities:
                key = f"{entity.type.value}:{entity.label}"
                if key in entity_index:
                    # Merge: increase confidence, add source tools
                    existing = entity_index[key]
                    existing.confidence = min(1.0, existing.confidence + 0.1)
                    for tool in entity.source_tools:
                        if tool not in existing.source_tools:
                            existing.source_tools.append(tool)
                else:
                    entity_index[key] = entity
                    all_entities.append(entity)

        logger.info(f"[correlation] Extracted {len(all_entities)} unique entities")

        # Phase 2: Build relationships on deduplicated entities
        relationships = self._build_relationships(all_entities, entity_index, scan_results)

        logger.info(f"[correlation] Found {len(relationships)} relationships")

        # Phase 3: Cluster
        clusters = self._cluster_entities(all_entities, relationships)

        result = CorrelationResult(
            entities=all_entities,
            relationships=relationships,
            clusters=clusters,
            metadata={
                "scan_results_analyzed": len(scan_results),
                "tools_used": list({sr.tool for sr in scan_results}),
            },
        )

        self._save_json(ctx, "correlation_result.json", result.to_dict())
        return result

    def _error_result(
        self, error: Optional[Exception], duration_ms: int
    ) -> CorrelationResult:
        return CorrelationResult(
            entities=[], relationships=[], clusters=[],
            metadata={"error": str(error) if error else "Correlation failed"},
        )

    # ── Entity Extraction ──────────────────────────────────

    def _extract_entities(self, sr: ScanResult) -> list[Entity]:
        """Extract entities from a single scan result."""
        entities: list[Entity] = []
        text = str(sr.data)

        # Extract emails
        for match in self.EMAIL_RE.finditer(text):
            email = match.group()
            entities.append(Entity(
                type=EntityType.EMAIL,
                label=email,
                properties={"email": email},
                confidence=0.9,
                source_tools=[sr.tool],
            ))

        # Extract domains (but not emails)
        for match in self.DOMAIN_RE.finditer(text):
            domain = match.group()
            if "@" not in domain and not self.EMAIL_RE.match(domain):
                entities.append(Entity(
                    type=EntityType.DOMAIN,
                    label=domain,
                    properties={"domain": domain},
                    confidence=0.8,
                    source_tools=[sr.tool],
                ))

        # Extract IPs
        for match in self.IP_RE.finditer(text):
            ip = match.group()
            entities.append(Entity(
                type=EntityType.IP,
                label=ip,
                properties={"ip": ip},
                confidence=0.9,
                source_tools=[sr.tool],
            ))

        # Extract usernames from social accounts
        for item in sr.data:
            if isinstance(item, dict):
                platform = item.get("platform", "")
                username = item.get("username", "")
                # Try to extract username from URL if not provided
                if not username:
                    url = item.get("url", "")
                    if url and "http" in url:
                        from urllib.parse import urlparse
                        path = urlparse(url).path.strip("/")
                        if path:
                            username = path.split("/")[0]
                if platform and username:
                    entities.append(Entity(
                        type=EntityType.SOCIAL_ACCOUNT,
                        label=f"{platform}:{username}",
                        properties={"platform": platform, "username": username},
                        confidence=item.get("confidence", 0.7),
                        source_tools=[sr.tool],
                    ))

        # Extract main target entity
        target_entity_type = {
            "email": EntityType.EMAIL,
            "domain": EntityType.DOMAIN,
            "ip": EntityType.IP,
            "username": EntityType.USERNAME,
        }.get(sr.tool)

        if target_entity_type:
            entities.insert(0, Entity(
                type=target_entity_type,
                label=sr.target,
                properties={"target": sr.target, "scan_tool": sr.tool},
                confidence=1.0,
                source_tools=[sr.tool],
            ))

        return entities

    # ── Relationship Building ──────────────────────────────

    def _build_relationships(
        self,
        entities: list[Entity],
        entity_index: dict[str, Entity],
        scan_results: list[ScanResult],
    ) -> list[Relationship]:
        """Build relationships between deduplicated entities."""
        relationships: list[Relationship] = []
        entities_by_type: dict[EntityType, list[Entity]] = {}
        for e in entities:
            entities_by_type.setdefault(e.type, []).append(e)

        # Helper: get dedup entity ID for a (type, label) key
        def _dedup_id(entity_type: EntityType, label: str) -> str | None:
            key = f"{entity_type.value}:{label}"
            ent = entity_index.get(key)
            return ent.id if ent else None

        # Relationship: same scan result = "found_with"
        for sr in scan_results:
            sr_entities = self._extract_entities(sr)
            deduped = []
            for se in sr_entities:
                key = f"{se.type.value}:{se.label}"
                if key in entity_index:
                    deduped.append(entity_index[key])
            for i, e1 in enumerate(deduped):
                for e2 in deduped[i + 1:]:
                    if e1.id != e2.id:
                        relationships.append(Relationship(
                            from_entity=e1.id,
                            to_entity=e2.id,
                            label="found_with",
                            confidence=0.7,
                        ))

        # Relationship: domain → IP (from A records)
        domains = entities_by_type.get(EntityType.DOMAIN, [])
        ips = entities_by_type.get(EntityType.IP, [])
        for d in domains:
            for ip in ips:
                common_tools = set(d.source_tools) & set(ip.source_tools)
                if common_tools:
                    relationships.append(Relationship(
                        from_entity=d.id,
                        to_entity=ip.id,
                        label="resolves_to",
                        confidence=0.85,
                    ))

        # Relationship: email → domain (extracted from email)
        emails = entities_by_type.get(EntityType.EMAIL, [])
        for email_entity in emails:
            email = email_entity.label
            if "@" in email:
                _, domain_str = email.split("@", 1)
                for d in domains:
                    if d.label == domain_str:
                        relationships.append(Relationship(
                            from_entity=email_entity.id,
                            to_entity=d.id,
                            label="has_domain",
                            confidence=0.95,
                        ))

        # Deduplicate relationships
        seen: set[str] = set()
        deduped_rel: list[Relationship] = []
        for r in relationships:
            key = f"{r.from_entity}:{r.to_entity}:{r.label}"
            if key not in seen:
                seen.add(key)
                deduped_rel.append(r)

        return deduped_rel

    # ── Clustering ─────────────────────────────────────────

    def _cluster_entities(
        self,
        entities: list[Entity],
        relationships: list[Relationship],
    ) -> list[list[str]]:
        """Simple union-find clustering of connected entities."""
        entity_ids = {e.id for e in entities}
        parent: dict[str, str] = {e.id: e.id for e in entities}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: str, b: str):
            if a not in parent or b not in parent:
                return  # skip dangling references
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for r in relationships:
            union(r.from_entity, r.to_entity)

        clusters: dict[str, list[str]] = {}
        for e in entities:
            root = find(e.id)
            clusters.setdefault(root, []).append(e.id)

        return [members for members in clusters.values() if len(members) > 1]
