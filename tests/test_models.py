import pytest
from src.models import (
    AppResearchResult, AuthType, AccessType, APIType, MCPStatus,
    BuildabilityTier, VerificationStatus, SourceEvidence, AuditRecord
)


def test_app_research_result_defaults():
    res = AppResearchResult(
        app="Stripe",
        category="Ecommerce",
        website="https://stripe.com",
        description="Payment infrastructure"
    )
    assert res.app == "Stripe"
    assert res.category == "Ecommerce"
    assert res.auth_type == AuthType.UNKNOWN.value
    assert res.priority_tier == "P3"
    assert res.verification_status == VerificationStatus.RESEARCHED.value


def test_source_evidence_model():
    ev = SourceEvidence(
        url="https://docs.github.com/en/rest",
        title="GitHub REST API documentation",
        is_official_domain=True,
        http_status=200
    )
    assert ev.is_official_domain is True
    assert ev.http_status == 200


def test_audit_record_model():
    rec = AuditRecord(
        app="GitHub",
        category="Developer Platforms",
        field="auth",
        agent_claim="OAuth 2.0",
        evidence_url="https://docs.github.com",
        auditor_result="correct",
        correction="",
        auditor_notes="Verified"
    )
    assert rec.auditor_result == "correct"
    assert rec.field == "auth"
