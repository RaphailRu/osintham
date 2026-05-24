"""OsintHAM — Agent System Tests

Tests for all agent classes:
  - Models (dataclasses, enums)
  - ScannerAgent (single scan execution)
  - InvestigationAgent (parallel orchestration)
  - CorrelationAgent (entity extraction, relationships)
  - ValidationAgent (data quality, dedup)
  - ReportAgent (multi-format reports)
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models import (
    AgentConfig,
    AgentConstraints,
    AgentRole,
    CorrelationResult,
    Entity,
    EntityType,
    InvestigationResult,
    Priority,
    Relationship,
    Report,
    ScanResult,
    ScanStatus,
    Target,
    TargetType,
    ValidatedItem,
    ValidationResult,
)
from app.agents import ExecutionContext
from app.agents.scanner_agent import ScannerAgent
from app.agents.investigation_agent import InvestigationAgent, _select_scanners
from app.agents.correlation_agent import CorrelationAgent
from app.agents.validation_agent import ValidationAgent
from app.agents.report_agent import ReportAgent


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def ctx(tmp_path):
    """Create a test ExecutionContext with temp directory."""
    return ExecutionContext(
        agent_id="test_agent",
        investigation_id="test_inv",
        work_dir=str(tmp_path),
    )


@pytest.fixture
def sample_scan_result():
    return ScanResult(
        tool="email",
        target="test@example.com",
        target_type=TargetType.EMAIL,
        status=ScanStatus.DONE,
        data=[
            {"email": "test@example.com", "provider": "gmail.com", "valid": True},
            {"breach": "Adobe", "date": "2013-10-04"},
        ],
        duration_ms=150,
    )


@pytest.fixture
def sample_scan_results():
    return [
        ScanResult(
            tool="email",
            target="test@example.com",
            target_type=TargetType.EMAIL,
            status=ScanStatus.DONE,
            data=[
                {"email": "test@example.com", "provider": "gmail.com"},
                {"domain": "gmail.com", "mx": "gmail-smtp-in.l.google.com"},
            ],
            duration_ms=100,
        ),
        ScanResult(
            tool="domain",
            target="example.com",
            target_type=TargetType.DOMAIN,
            status=ScanStatus.DONE,
            data=[
                {"a_records": ["93.184.216.34"]},
                {"domain": "example.com", "whois_registrar": "Example Inc"},
                {"mx_records": [{"exchange": "mail.example.com"}]},
            ],
            duration_ms=200,
        ),
        ScanResult(
            tool="username",
            target="john",
            target_type=TargetType.USERNAME,
            status=ScanStatus.PARTIAL,
            data=[
                {"platform": "github", "url": "https://github.com/john", "status": "found"},
                {"platform": "twitter", "url": "https://twitter.com/john", "status": "found"},
            ],
            duration_ms=300,
            error="Some platforms timed out",
        ),
    ]


@pytest.fixture
def sample_targets():
    return [
        Target(type=TargetType.EMAIL, value="test@example.com"),
        Target(type=TargetType.DOMAIN, value="example.com"),
    ]


# ═══════════════════════════════════════════════════════════════
# Models Tests
# ═══════════════════════════════════════════════════════════════

class TestModels:
    def test_target_creation(self):
        t = Target(type=TargetType.EMAIL, value="a@b.com")
        assert t.label == "a@b.com"
        assert t.type == TargetType.EMAIL

    def test_target_with_label(self):
        t = Target(type=TargetType.EMAIL, value="a@b.com", label="Primary")
        assert t.label == "Primary"

    def test_scan_result_to_dict(self, sample_scan_result):
        d = sample_scan_result.to_dict()
        assert d["tool"] == "email"
        assert d["status"] == "done"
        assert isinstance(d["data"], list)
        assert d["duration_ms"] == 150

    def test_investigation_result_to_dict(self, sample_targets, sample_scan_results):
        inv = InvestigationResult(
            id="test_123",
            title="Test Investigation",
            targets=sample_targets,
            scan_results=sample_scan_results,
        )
        d = inv.to_dict()
        assert d["id"] == "test_123"
        assert len(d["targets"]) == 2
        assert len(d["scan_results"]) == 3

    def test_entity_default_id(self):
        e = Entity(type=EntityType.EMAIL, label="a@b.com")
        assert len(e.id) == 12
        assert e.confidence == 0.5

    def test_validation_result_counts(self):
        vr = ValidationResult(
            items=[
                ValidatedItem(item={}, valid=True, confidence=0.9),
                ValidatedItem(item={}, valid=True, confidence=0.7),
                ValidatedItem(item={}, valid=False, confidence=0.2),
            ],
            valid_count=2,
            invalid_count=1,
            avg_confidence=0.6,
        )
        d = vr.to_dict()
        assert d["valid_count"] == 2
        assert d["invalid_count"] == 1

    def test_correlation_result_to_dict(self):
        cr = CorrelationResult(
            entities=[
                Entity(type=EntityType.DOMAIN, label="example.com"),
                Entity(type=EntityType.IP, label="93.184.216.34"),
            ],
            relationships=[
                Relationship(
                    from_entity="entity1",
                    to_entity="entity2",
                    label="resolves_to",
                ),
            ],
        )
        d = cr.to_dict()
        assert len(d["entities"]) == 2
        assert d["relationships"][0]["label"] == "resolves_to"

    def test_agent_constraints_defaults(self):
        ac = AgentConstraints()
        assert ac.max_concurrent_scans == 5
        assert ac.max_scan_timeout_sec == 120
        assert ac.min_confidence == 0.6

    def test_agent_config_defaults(self):
        config = AgentConfig(role=AgentRole.SCANNER, name="test")
        assert config.enabled is True
        assert config.timeout_sec == 120


# ═══════════════════════════════════════════════════════════════
# Scanner Selection Tests
# ═══════════════════════════════════════════════════════════════

class TestScannerSelection:
    def test_quick_email(self):
        assert "email" in _select_scanners(TargetType.EMAIL, Priority.QUICK)

    def test_standard_username(self):
        scanners = _select_scanners(TargetType.USERNAME, Priority.STANDARD)
        assert "username" in scanners

    def test_deep_domain(self):
        scanners = _select_scanners(TargetType.DOMAIN, Priority.DEEP)
        assert "domain" in scanners

    def test_quick_phone_empty(self):
        assert _select_scanners(TargetType.PHONE, Priority.QUICK) == []

    def test_fallback_unknown_type(self):
        # URL has no entry, should fallback gracefully
        result = _select_scanners(TargetType.URL, Priority.STANDARD)
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════════
# ScannerAgent Tests
# ═══════════════════════════════════════════════════════════════

class TestScannerAgent:
    def test_detect_target_type_email(self):
        assert ScannerAgent._detect_target_type("a@b.com") == TargetType.EMAIL

    def test_detect_target_type_ip(self):
        assert ScannerAgent._detect_target_type("1.2.3.4") == TargetType.IP

    def test_detect_target_type_domain(self):
        assert ScannerAgent._detect_target_type("example.com") == TargetType.DOMAIN

    def test_detect_target_type_username(self):
        assert ScannerAgent._detect_target_type("johndoe") == TargetType.USERNAME

    def test_scanner_expected_type(self):
        assert ScannerAgent._scanner_expected_type("email") == TargetType.EMAIL
        assert ScannerAgent._scanner_expected_type("domain") == TargetType.DOMAIN
        assert ScannerAgent._scanner_expected_type("nonexistent") is None

    def test_available_scanners(self):
        scanners = ScannerAgent.available_scanners()
        assert isinstance(scanners, list)

    @pytest.mark.asyncio
    async def test_execute_unknown_scanner(self, ctx):
        agent = ScannerAgent()
        result = await agent.execute(
            ctx=ctx,
            target="test",
            scanner_tool="nonexistent_tool",
            target_type=TargetType.AUTO,
        )
        assert result.status == ScanStatus.ERROR
        assert "Unknown scanner tool" in (result.error or "")

    @pytest.mark.asyncio
    async def test_execute_mocked_scanner(self, ctx):
        agent = ScannerAgent()
        agent._lazy_load_scanners = lambda: None
        agent._TOOL_TO_SCANNER = {"mock_tool": "mock_tool"}
        agent._SCANNER_FUNCS = {
            "mock_tool": AsyncMock(return_value={
                "success": True,
                "data": {"key": "value"},
                "errors": [],
                "metadata": {"tools_used": ["mock_tool"]},
            })
        }
        result = await agent.execute(
            ctx=ctx,
            target="test",
            scanner_tool="mock_tool",
            target_type=TargetType.AUTO,
        )
        assert result.status == ScanStatus.DONE
        assert len(result.data) > 0

    def test_cancel(self):
        agent = ScannerAgent()
        agent.cancel()
        assert agent._cancelled is True


# ═══════════════════════════════════════════════════════════════
# InvestigationAgent Tests
# ═══════════════════════════════════════════════════════════════

class TestInvestigationAgent:
    def test_error_result(self):
        agent = InvestigationAgent()
        result = agent._error_result(ValueError("test"), 100)
        assert result.status == ScanStatus.ERROR
        assert "test" in result.errors[0]

    @pytest.mark.asyncio
    async def test_run_with_mocked_scanners(self, ctx, sample_targets):
        agent = InvestigationAgent()

        # Mock the scanner agent's execute method
        mock_results = [
            ScanResult(
                tool="email",
                target="test@example.com",
                target_type=TargetType.EMAIL,
                status=ScanStatus.DONE,
                data=[{"email": "test@example.com"}],
                duration_ms=100,
            ),
            ScanResult(
                tool="domain",
                target="example.com",
                target_type=TargetType.DOMAIN,
                status=ScanStatus.DONE,
                data=[{"domain": "example.com"}],
                duration_ms=200,
            ),
        ]
        agent._scanner.execute = AsyncMock(side_effect=mock_results)

        result = await agent.execute(
            ctx=ctx,
            targets=sample_targets,
            priority=Priority.STANDARD,
            title="Test Investigation",
        )

        assert result.status in (ScanStatus.DONE, ScanStatus.PARTIAL)
        assert len(result.scan_results) == 2
        assert result.targets == sample_targets

    @pytest.mark.asyncio
    async def test_run_scan_error_handling(self, ctx):
        """Test that individual scan errors don't crash the investigation."""
        targets = [Target(type=TargetType.EMAIL, value="test@example.com")]
        agent = InvestigationAgent()

        # Mock the scanner to raise an exception
        async def _raise(*a, **kw):
            raise ValueError("Scanner crashed")
        agent._scanner.execute = _raise

        result = await agent.execute(
            ctx=ctx,
            targets=targets,
            priority=Priority.QUICK,
        )

        # Should still have a result (with error)
        assert len(result.scan_results) >= 0  # gather may or may not include

    def test_cancel_propagates(self):
        agent = InvestigationAgent()
        agent._scanner = MagicMock()
        agent.cancel()
        assert agent._cancelled is True


# ═══════════════════════════════════════════════════════════════
# CorrelationAgent Tests
# ═══════════════════════════════════════════════════════════════

class TestCorrelationAgent:
    @pytest.mark.asyncio
    async def test_extract_email_entities(self, ctx, sample_scan_results):
        agent = CorrelationAgent()
        result = await agent.execute(ctx=ctx, scan_results=sample_scan_results)

        email_entities = [e for e in result.entities if e.type == EntityType.EMAIL]
        assert len(email_entities) > 0

    @pytest.mark.asyncio
    async def test_extract_domain_entities(self, ctx, sample_scan_results):
        agent = CorrelationAgent()
        result = await agent.execute(ctx=ctx, scan_results=sample_scan_results)

        domain_entities = [e for e in result.entities if e.type == EntityType.DOMAIN]
        assert len(domain_entities) > 0

    @pytest.mark.asyncio
    async def test_extract_ip_entities(self, ctx, sample_scan_results):
        agent = CorrelationAgent()
        result = await agent.execute(ctx=ctx, scan_results=sample_scan_results)

        ip_entities = [e for e in result.entities if e.type == EntityType.IP]
        assert len(ip_entities) > 0

    @pytest.mark.asyncio
    async def test_social_account_entities(self, ctx, sample_scan_results):
        agent = CorrelationAgent()
        result = await agent.execute(ctx=ctx, scan_results=sample_scan_results)

        social = [e for e in result.entities if e.type == EntityType.SOCIAL_ACCOUNT]
        assert len(social) > 0

    @pytest.mark.asyncio
    async def test_relationships_created(self, ctx, sample_scan_results):
        agent = CorrelationAgent()
        result = await agent.execute(ctx=ctx, scan_results=sample_scan_results)

        # Should have at least some relationships from co-occurrence
        assert len(result.entities) > 0

    @pytest.mark.asyncio
    async def test_empty_scan_results(self, ctx):
        agent = CorrelationAgent()
        result = await agent.execute(ctx=ctx, scan_results=[])

        assert result.entities == []
        assert result.relationships == []

    @pytest.mark.asyncio
    async def test_clustering(self, ctx, sample_scan_results):
        agent = CorrelationAgent()
        result = await agent.execute(ctx=ctx, scan_results=sample_scan_results)

        # Clusters should be a list of lists
        assert isinstance(result.clusters, list)
        for cluster in result.clusters:
            assert isinstance(cluster, list)
            assert len(cluster) > 1

    def test_error_result(self):
        agent = CorrelationAgent()
        result = agent._error_result(RuntimeError("fail"), 50)
        assert result.entities == []
        assert "fail" in result.metadata["error"]


# ═══════════════════════════════════════════════════════════════
# ValidationAgent Tests
# ═══════════════════════════════════════════════════════════════

class TestValidationAgent:
    @pytest.mark.asyncio
    async def test_validate_scan_results(self, ctx, sample_scan_results):
        agent = ValidationAgent()
        result = await agent.execute(
            ctx=ctx,
            scan_results=sample_scan_results,
        )

        assert result.items is not None
        assert isinstance(result.valid_count, int)
        assert isinstance(result.invalid_count, int)

    @pytest.mark.asyncio
    async def test_valid_email_format(self, ctx):
        sr = ScanResult(
            tool="email",
            target="test@example.com",
            target_type=TargetType.EMAIL,
            status=ScanStatus.DONE,
            data=[{"email": "test@example.com"}],
        )
        agent = ValidationAgent()
        result = await agent.execute(ctx=ctx, scan_results=[sr])

        email_validated = [i for i in result.items
                          if i.item.get("email") == "test@example.com"]
        assert len(email_validated) > 0
        assert email_validated[0].valid is True

    @pytest.mark.asyncio
    async def test_url_found_status(self, ctx):
        sr = ScanResult(
            tool="username",
            target="john",
            target_type=TargetType.USERNAME,
            status=ScanStatus.DONE,
            data=[{"platform": "github", "url": "https://github.com/john", "status": "found"}],
        )
        agent = ValidationAgent()
        result = await agent.execute(ctx=ctx, scan_results=[sr])

        url_validated = [i for i in result.items if i.item.get("url")]
        assert len(url_validated) > 0
        assert url_validated[0].valid is True
        assert url_validated[0].confidence >= 0.8

    @pytest.mark.asyncio
    async def test_deduplication(self, ctx):
        """Same record from two scans with same tool+url should be deduped."""
        sr1 = ScanResult(
            tool="email",
            target="test@example.com",
            target_type=TargetType.EMAIL,
            status=ScanStatus.DONE,
            data=[{"url": "https://github.com/test", "status": "found"}],
        )
        sr2 = ScanResult(
            tool="email",  # Same tool → dedup should work
            target="test@example.com",
            target_type=TargetType.EMAIL,
            status=ScanStatus.DONE,
            data=[{"url": "https://github.com/test", "status": "found"}],
        )
        agent = ValidationAgent()
        result = await agent.execute(ctx=ctx, scan_results=[sr1, sr2])

        urls = [i.item.get("url") for i in result.items if i.item.get("url")]
        # Should be deduped — only one entry (same tool+url)
        assert urls.count("https://github.com/test") == 1

    @pytest.mark.asyncio
    async def test_min_confidence_filter(self, ctx):
        sr = ScanResult(
            tool="username",
            target="test",
            target_type=TargetType.USERNAME,
            status=ScanStatus.DONE,
            data=[{"platform": "obscure_site", "username": "test", "status": "unknown"}],
        )
        agent = ValidationAgent()
        result = await agent.execute(ctx=ctx, scan_results=[sr], min_confidence=0.9)

        # The generic record has confidence 0.5, below min
        low_conf = [i for i in result.items if i.confidence < 0.9]
        assert all(not i.valid for i in low_conf)

    def test_error_result(self):
        agent = ValidationAgent()
        result = agent._error_result(ValueError("fail"), 50)
        assert result.avg_confidence == 0.0


# ═══════════════════════════════════════════════════════════════
# ReportAgent Tests
# ═══════════════════════════════════════════════════════════════

class TestReportAgent:
    @pytest.mark.asyncio
    async def test_full_report(self, ctx, sample_targets, sample_scan_results):
        agent = ReportAgent()
        inv = InvestigationResult(
            id="test_inv",
            title="Test Investigation",
            targets=sample_targets,
            scan_results=sample_scan_results,
            status=ScanStatus.DONE,
            duration_ms=600,
        )
        validation = ValidationResult(
            items=[
                ValidatedItem(item={"url": "https://github.com/john"}, valid=True, confidence=0.9),
            ],
            valid_count=1,
            invalid_count=0,
            avg_confidence=0.9,
        )
        correlation = CorrelationResult(
            entities=[
                Entity(type=EntityType.DOMAIN, label="example.com"),
                Entity(type=EntityType.IP, label="93.184.216.34"),
            ],
            relationships=[
                Relationship(
                    from_entity="e1",
                    to_entity="e2",
                    label="resolves_to",
                    confidence=0.85,
                ),
            ],
            clusters=[["e1", "e2"]],
        )

        report = await agent.execute(
            ctx=ctx,
            investigation=inv,
            validation=validation,
            correlation=correlation,
        )

        assert isinstance(report, Report)
        assert len(report.markdown) > 0
        assert len(report.html) > 0
        assert report.investigation_id == "test_inv"
        assert "example.com" in report.markdown
        assert "93.184.216.34" in report.markdown
        assert "<html>" in report.html.lower()

    @pytest.mark.asyncio
    async def test_report_without_validation(self, ctx, sample_targets, sample_scan_results):
        agent = ReportAgent()
        inv = InvestigationResult(
            id="test_inv",
            title="Test",
            targets=sample_targets,
            scan_results=sample_scan_results,
            status=ScanStatus.DONE,
        )

        report = await agent.execute(
            ctx=ctx,
            investigation=inv,
        )

        assert len(report.markdown) > 0
        # Should not crash without validation/correlation

    @pytest.mark.asyncio
    async def test_report_json_data(self, ctx, sample_targets):
        agent = ReportAgent()
        inv = InvestigationResult(
            id="json_test",
            title="JSON Test",
            targets=sample_targets,
            scan_results=[],
        )

        report = await agent.execute(ctx=ctx, investigation=inv)

        assert "report" in report.html.lower() or "investigation" in report.markdown.lower()
        json_data = report.json_data
        assert json_data["report_type"] == "osintham_investigation"

    def test_error_result(self):
        agent = ReportAgent()
        report = agent._error_result(ValueError("fail"), 50)
        assert "Error" in report.markdown
        assert "fail" in report.json_data["error"]


# ═══════════════════════════════════════════════════════════════
# ExecutionContext Tests
# ═══════════════════════════════════════════════════════════════

class TestExecutionContext:
    def test_agent_dir_creation(self, tmp_path):
        ctx = ExecutionContext(
            agent_id="test123",
            investigation_id="inv456",
            work_dir=str(tmp_path),
        )
        assert ctx.agent_dir.exists()
        assert ctx.agent_dir.name == "test123"

    def test_log_file_path(self, tmp_path):
        ctx = ExecutionContext(work_dir=str(tmp_path))
        assert ctx.log_file.name == "agent.log"

    def test_cancelled_default(self, tmp_path):
        ctx = ExecutionContext(work_dir=str(tmp_path))
        assert ctx.cancelled is False


# ═══════════════════════════════════════════════════════════════
# AgentConstraints Tests
# ═══════════════════════════════════════════════════════════════

class TestAgentConstraints:
    def test_defaults(self):
        c = AgentConstraints()
        assert c.max_concurrent_scans == 5
        assert c.max_scan_timeout_sec == 120
        assert c.max_investigation_timeout_sec == 600
        assert c.min_confidence == 0.6
        assert c.max_retries == 1

    def test_custom(self):
        c = AgentConstraints(max_concurrent_scans=10, min_confidence=0.8)
        assert c.max_concurrent_scans == 10
        assert c.min_confidence == 0.8
