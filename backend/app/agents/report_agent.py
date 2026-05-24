"""OsintHAM — ReportAgent

Generates final investigation reports in multiple formats:
  - Markdown (for GitHub / human reading)
  - HTML (for web interface)
  - JSON (for API consumers)
  - Graph SVG (visual entity-relationship diagram)

Report sections:
  1. Executive summary
  2. Targets overview
  3. Scan results by tool
  4. Entity-relationship graph
  5. Key findings
  6. Confidence assessment
  7. Recommendations
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from app.agents import BaseAgent, ExecutionContext
from app.models import (
    AgentConfig,
    AgentConstraints,
    AgentRole,
    CorrelationResult,
    InvestigationResult,
    Report,
    ScanResult,
    ValidationResult,
)

logger = logging.getLogger("osintham.agents.report")


class ReportAgent(BaseAgent):
    """Generates multi-format investigation reports."""

    role = AgentRole.REPORT

    async def run(
        self,
        ctx: ExecutionContext,
        *,
        investigation: InvestigationResult,
        validation: Optional[ValidationResult] = None,
        correlation: Optional[CorrelationResult] = None,
    ) -> Report:
        """Generate a full investigation report.

        Args:
            investigation: The complete investigation result
            validation:    Optional validation result
            correlation:   Optional correlation result
        """
        logger.info(
            f"[report] Generating report for investigation {investigation.id}"
        )

        md = self._build_markdown(investigation, validation, correlation)
        html = self._build_html(investigation, validation, correlation)
        json_data = self._build_json(investigation, validation, correlation)

        report = Report(
            investigation_id=investigation.id,
            markdown=md,
            html=html,
            json_data=json_data,
            created_at=datetime.utcnow().isoformat(),
        )

        self._save_json(ctx, "report.json", report.to_dict())
        logger.info(f"[report] Report generated: {len(md)} chars markdown")

        return report

    def _error_result(
        self, error: Optional[Exception], duration_ms: int
    ) -> Report:
        return Report(
            markdown=f"# Error\n\nFailed to generate report: {error}",
            html=f"<h1>Error</h1><p>{error}</p>",
            json_data={"error": str(error) if error else "Report generation failed"},
        )

    # ── Markdown ───────────────────────────────────────────

    def _build_markdown(
        self,
        inv: InvestigationResult,
        validation: Optional[ValidationResult],
        correlation: Optional[CorrelationResult],
    ) -> str:
        lines: list[str] = []

        # Header
        lines.append(f"# 🔍 OSINT Investigation Report: {inv.title}")
        lines.append("")
        lines.append(f"**ID:** `{inv.id}`")
        lines.append(f"**Status:** {inv.status.value}")
        lines.append(f"**Created:** {inv.created_at}")
        if inv.completed_at:
            lines.append(f"**Completed:** {inv.completed_at}")
        lines.append(f"**Duration:** {inv.duration_ms}ms")
        lines.append("")

        # Targets
        lines.append("## 🎯 Targets")
        lines.append("")
        for t in inv.targets:
            lines.append(f"- **{t.type.value}:** `{t.value}`")
        lines.append("")

        # Scan Results Summary
        lines.append("## 📊 Scan Results")
        lines.append("")
        lines.append("| Tool | Target | Status | Records | Duration |")
        lines.append("|------|--------|--------|---------|----------|")
        for sr in inv.scan_results:
            lines.append(
                f"| {sr.tool} | `{sr.target}` | {sr.status.value} "
                f"| {len(sr.data)} | {sr.duration_ms}ms |"
            )
        lines.append("")

        # Detailed Results
        lines.append("## 🔬 Detailed Findings")
        lines.append("")
        for sr in inv.scan_results:
            lines.append(f"### {sr.tool} → `{sr.target}`")
            lines.append("")
            if sr.error:
                lines.append(f"⚠️ **Error:** {sr.error}")
                lines.append("")
            for record in sr.data[:20]:  # limit to 20 per scanner
                if isinstance(record, dict):
                    for k, v in record.items():
                        if isinstance(v, str) and v.startswith("http"):
                            lines.append(f"- **{k}:** [{v}]({v})")
                        else:
                            lines.append(f"- **{k}:** {v}")
                else:
                    lines.append(f"- {record}")
            if len(sr.data) > 20:
                lines.append(f"\n_... and {len(sr.data) - 20} more records_")
            lines.append("")

        # Validation
        if validation:
            lines.append("## ✅ Validation")
            lines.append("")
            lines.append(f"- **Valid items:** {validation.valid_count}")
            lines.append(f"- **Invalid items:** {validation.invalid_count}")
            lines.append(f"- **Average confidence:** {validation.avg_confidence:.1%}")
            lines.append("")

        # Correlation / Graph
        if correlation:
            lines.append("## 🕸️ Entity-Relationship Graph")
            lines.append("")
            lines.append(f"- **Entities:** {len(correlation.entities)}")
            lines.append(f"- **Relationships:** {len(correlation.relationships)}")
            lines.append(f"- **Clusters:** {len(correlation.clusters)}")
            lines.append("")

            if correlation.entities:
                lines.append("### Entities")
                lines.append("")
                for e in correlation.entities[:30]:
                    tools = ", ".join(e.source_tools)
                    lines.append(
                        f"- `{e.label}` ({e.type.value}) "
                        f"confidence={e.confidence:.0%} [{tools}]"
                    )
                lines.append("")

            if correlation.relationships:
                lines.append("### Relationships")
                lines.append("")
                entity_map = {e.id: e.label for e in correlation.entities}
                for r in correlation.relationships[:30]:
                    from_label = entity_map.get(r.from_entity, r.from_entity)
                    to_label = entity_map.get(r.to_entity, r.to_entity)
                    lines.append(
                        f"- `{from_label}` → **{r.label}** → "
                        f"`{to_label}` (confidence={r.confidence:.0%})"
                    )
                lines.append("")

        # Errors
        if inv.errors:
            lines.append("## ⚠️ Errors")
            lines.append("")
            for err in inv.errors:
                lines.append(f"- {err}")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append(f"*Generated by OsintHAM ReportAgent at {datetime.utcnow().isoformat()}*")

        return "\n".join(lines)

    # ── HTML ───────────────────────────────────────────────

    def _build_html(
        self,
        inv: InvestigationResult,
        validation: Optional[ValidationResult],
        correlation: Optional[CorrelationResult],
    ) -> str:
        """Generate HTML report."""
        md = self._build_markdown(inv, validation, correlation)
        # Simple markdown-to-HTML conversion
        html_parts = ["<!DOCTYPE html>", "<html><head>",
                      "<meta charset='utf-8'>",
                      f"<title>OsintHAM Report — {inv.title}</title>",
                      "<style>",
                      "body{font-family:system-ui,sans-serif;max-width:900px;margin:2em auto;padding:0 1em;line-height:1.6;color:#1a1a1a}",
                      "h1{color:#4f46e5;border-bottom:2px solid #4f46e5;padding-bottom:.3em}",
                      "h2{color:#6366f1;margin-top:1.5em}",
                      "h3{color:#818cf8}",
                      "table{border-collapse:collapse;width:100%;margin:1em 0}",
                      "th,td{border:1px solid #e5e7eb;padding:.5em .75em;text-align:left}",
                      "th{background:#f3f4f6;font-weight:600}",
                      "code{background:#f3f4f6;padding:.15em .4em;border-radius:4px;font-size:.9em}",
                      "a{color:#4f46e5;text-decoration:none}",
                      "a:hover{text-decoration:underline}",
                      "</style>",
                      "</head><body>"]

        # Convert markdown to basic HTML
        in_table = False
        for line in md.split("\n"):
            if line.startswith("# "):
                html_parts.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_parts.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_parts.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("|"):
                if not in_table:
                    html_parts.append("<table>")
                    in_table = True
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if all(c.replace("-", "").replace("|", "").strip() == "" for c in cells):
                    continue  # separator row
                tag = "th" if html_parts[-1] == "<table>" else "td"
                html_parts.append(
                    "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"
                )
            else:
                if in_table:
                    html_parts.append("</table>")
                    in_table = False
                if line.startswith("- "):
                    html_parts.append(f"<li>{line[2:]}</li>")
                elif line.startswith("---"):
                    html_parts.append("<hr>")
                elif line.startswith("*") and line.endswith("*"):
                    html_parts.append(f"<p><em>{line.strip('*')}</em></p>")
                elif line.strip():
                    html_parts.append(f"<p>{line}</p>")

        if in_table:
            html_parts.append("</table>")

        html_parts.append("</body></html>")
        return "\n".join(html_parts)

    # ── JSON ───────────────────────────────────────────────

    def _build_json(
        self,
        inv: InvestigationResult,
        validation: Optional[ValidationResult],
        correlation: Optional[CorrelationResult],
    ) -> dict[str, Any]:
        """Generate JSON report data."""
        return {
            "report_type": "osintham_investigation",
            "version": "1.0",
            "investigation": inv.to_dict(),
            "validation": validation.to_dict() if validation else None,
            "correlation": correlation.to_dict() if correlation else None,
            "generated_at": datetime.utcnow().isoformat(),
        }
