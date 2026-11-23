from src.research_agent import research_single_app
from src.extractor import calculate_buildability, BuildabilityTier
from src.verifier import verify_app_research


def test_calculate_buildability_scoring():
    # P1 Easy Win
    tier, p_tier, score = calculate_buildability(
        self_serve="Yes",
        access_type="Self-serve",
        auth_type="OAuth 2.0",
        api_type="REST",
        blockers=["Standard rate limit"]
    )
    assert p_tier == "P1"
    assert score >= 90

    # P4 Outreach Required
    tier_p4, p_tier_p4, score_p4 = calculate_buildability(
        self_serve="No",
        access_type="Partner approval required",
        auth_type="OAuth 2.0",
        api_type="REST",
        blockers=["Enterprise partner approval required", "Contact sales gate"]
    )
    assert p_tier_p4 == "P4"
    assert score_p4 <= 40


def test_research_single_app():
    app_info = {
        "app": "GitHub",
        "category": "Developer Platforms",
        "website": "https://github.com"
    }
    result = research_single_app(app_info)
    assert result.app == "GitHub"
    assert "OAuth" in result.auth_type or "Token" in result.auth_type
    assert result.self_serve == "Yes"
    assert result.priority_tier == "P1"
    assert len(result.evidence_urls) > 0
    assert result.verification_status in ["evidence_checked", "researched"]
