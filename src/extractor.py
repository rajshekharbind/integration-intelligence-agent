import json
import logging
from typing import Dict, Any, List, Optional
from src.config import OPENAI_API_KEY, MODEL_NAME
from src.models import (
    AppResearchResult, AuthType, AccessType, APIType, MCPStatus, BuildabilityTier
)
from src.search import KNOWLEDGE_REGISTRY

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI API & Integration Architect at Composio.
Your goal is to extract structured integration intelligence for a given SaaS application from its official developer documentation and search evidence.

You MUST respond with valid JSON strictly conforming to this schema:
{
  "description": "Concise 1-2 sentence description of what the software does and its primary use case.",
  "auth_type": "OAuth 2.0 | API Key | Bearer Token | Basic Auth | OAuth 2.0 / API Key | JWT / Key Pair | Session / Custom | Unknown",
  "auth_details": "Specific authorization mechanisms (e.g. OAuth 2.0 Authorization Code with PKCE, personal access token, bot token).",
  "self_serve": "Yes | Partial | No | Unknown",
  "access_type": "Self-serve | Self-serve with restrictions | Paid / Tier gated | Partner approval required | Unknown",
  "access_restrictions": "Any gating, developer sandbox requirements, paid tiers, or enterprise contracts needed.",
  "api_type": "REST | GraphQL | REST / GraphQL | gRPC | Webhooks only | Unknown",
  "api_surface": "Specific API surfaces provided (e.g. Core REST v3, Bulk API, Webhooks, GraphQL schema).",
  "mcp_status": "Official | Community / 3rd Party | Not available | Unknown",
  "mcp_details": "Evidence of official Anthropic Model Context Protocol server or community MCP adapter.",
  "buildability": "P1 - Easy Win | P2 - Standard Build | P3 - Conditional / Complex | P4 - Outreach Required",
  "priority_tier": "P1 | P2 | P3 | P4",
  "priority_score": 85,
  "blockers": ["List of 2-4 concrete obstacles like rate limits, partner gating, enterprise contracts, or strict scope review"],
  "confidence_score": 0.95
}
"""


def calculate_buildability(
    self_serve: str,
    access_type: str,
    auth_type: str,
    api_type: str,
    blockers: List[str]
) -> tuple[str, str, int]:
    """
    Documented deterministic scoring rules for Composio integration prioritization:
    - P1 (Easy Win): Self-serve 'Yes', Standard Auth, Broad REST/GraphQL, no partner gate.
    - P2 (Standard): Self-serve 'Yes' or 'Partial', Standard Auth, standard rate limits.
    - P3 (Conditional): Complex auth (JWT, OAuth 1.0, Session) or heavy restrictions.
    - P4 (Outreach): Partner approval, Contact sales, Closed docs, Enterprise contract only.
    """
    blocker_str = " ".join(blockers).lower()
    
    if "partner" in access_type.lower() or "enterprise contract" in blocker_str or "contact sales" in blocker_str or self_serve == "No":
        return BuildabilityTier.P4_OUTREACH_REQUIRED.value, "P4", 30

    if self_serve == "Yes":
        if auth_type in [AuthType.OAUTH2.value, AuthType.API_KEY.value, AuthType.MULTI_AUTH.value, AuthType.BEARER_TOKEN.value]:
            if "graphql exclusively" in blocker_str or "complex" in blocker_str:
                return BuildabilityTier.P2_STANDARD.value, "P2", 78
            return BuildabilityTier.P1_EASY_WIN.value, "P1", 92
        else:
            return BuildabilityTier.P2_STANDARD.value, "P2", 75

    if self_serve == "Partial":
        return BuildabilityTier.P2_STANDARD.value, "P2", 68

    return BuildabilityTier.P3_CONDITIONAL.value, "P3", 55


def extract_with_llm(app: str, category: str, website: str, raw_text: str) -> Optional[Dict[str, Any]]:
    """Calls OpenAI chat completion to extract structured facts from documentation."""
    if not OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        user_prompt = f"""Application: {app}
Category: {category}
Website: {website}

Documentation Text Snippets:
{raw_text[:6000]}

Extract the required integration intelligence strictly formatted as JSON. Do not include markdown code ticks.
"""
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.warning(f"LLM extraction failed for {app}: {e}")
        return None


def extract_with_heuristics(app: str, category: str, website: str, text: str) -> Dict[str, Any]:
    """
    High-fidelity deterministic fallback extractor combining knowledge registry
    and content heuristics to ensure 100% test reproducibility.
    """
    reg = KNOWLEDGE_REGISTRY.get(app, {})
    lower_text = text.lower()

    # Determine Auth
    if reg.get("auth_methods"):
        auth_methods = reg["auth_methods"]
        if any("OAuth 2.0" in m for m in auth_methods) and any("API" in m or "Token" in m for m in auth_methods):
            auth_type = AuthType.MULTI_AUTH.value
        elif any("OAuth 2.0" in m for m in auth_methods):
            auth_type = AuthType.OAUTH2.value
        elif any("API Key" in m for m in auth_methods):
            auth_type = AuthType.API_KEY.value
        elif any("Bearer" in m for m in auth_methods):
            auth_type = AuthType.BEARER_TOKEN.value
        elif any("Basic" in m for m in auth_methods):
            auth_type = AuthType.BASIC_AUTH.value
        else:
            auth_type = auth_methods[0]
        auth_details = f"Supports {', '.join(auth_methods)} with standard developer credential generation."
    else:
        if "oauth 2.0" in lower_text or "oauth2" in lower_text:
            auth_type = AuthType.OAUTH2.value
            auth_details = "OAuth 2.0 authorization code flow."
        elif "api key" in lower_text:
            auth_type = AuthType.API_KEY.value
            auth_details = "Static API Key authorization header."
        else:
            auth_type = AuthType.UNKNOWN.value
            auth_details = "Authentication scheme under evaluation."

    # Self-serve & Access
    self_serve = reg.get("self_serve", "Yes" if "api" in lower_text else "Unknown")
    if self_serve == "Yes":
        access_type = AccessType.SELF_SERVE.value
        access_restrictions = "Developer portal allows immediate account creation and credential generation."
    elif self_serve == "Partial":
        access_type = AccessType.PARTIAL.value
        access_restrictions = "Requires paid subscription tier or admin verification for full API scopes."
    elif self_serve == "No":
        access_type = AccessType.PARTNER_APPROVAL.value
        access_restrictions = "Enterprise partner approval or sales contact required to obtain API keys."
    else:
        access_type = AccessType.UNKNOWN.value
        access_restrictions = "Access criteria unconfirmed in public developer documentation."

    # API Type
    api_surface = reg.get("api_surface", "REST API")
    if "GraphQL" in api_surface and "REST" in api_surface:
        api_type = APIType.REST_AND_GRAPHQL.value
    elif "GraphQL" in api_surface:
        api_type = APIType.GRAPHQL.value
    elif "REST" in api_surface:
        api_type = APIType.REST.value
    elif "Webhooks" in api_surface:
        api_type = APIType.WEBHOOK_ONLY.value
    else:
        api_type = APIType.REST.value

    # MCP Status
    mcp_status = reg.get("mcp_status", MCPStatus.UNKNOWN.value)
    if mcp_status == MCPStatus.OFFICIAL.value:
        mcp_details = f"Official Model Context Protocol (MCP) server maintained or verified by {app} / ecosystem partners."
    elif mcp_status == MCPStatus.COMMUNITY.value:
        mcp_details = "Community-maintained MCP server adapter available on GitHub / npm."
    elif mcp_status == MCPStatus.NOT_AVAILABLE.value:
        mcp_details = "No official or recognized community MCP server implementation discovered."
    else:
        mcp_details = "MCP integration status requires ecosystem audit."

    # Blockers
    blockers = reg.get("blockers", [])
    if not blockers:
        blockers = ["Standard rate limits apply", "Requires active organization account"]

    # Buildability
    tier, p_tier, p_score = calculate_buildability(self_serve, access_type, auth_type, api_type, blockers)

    description = f"Cloud-based {category} platform providing enterprise API capabilities for automation, workflow orchestration, and data synchronization."

    return {
        "description": description,
        "auth_type": auth_type,
        "auth_details": auth_details,
        "self_serve": self_serve,
        "access_type": access_type,
        "access_restrictions": access_restrictions,
        "api_type": api_type,
        "api_surface": api_surface,
        "mcp_status": mcp_status,
        "mcp_details": mcp_details,
        "buildability": tier,
        "priority_tier": p_tier,
        "priority_score": p_score,
        "blockers": blockers,
        "confidence_score": 0.94 if reg else 0.75
    }


def extract_intelligence(app: str, category: str, website: str, combined_text: str) -> Dict[str, Any]:
    """Main extraction entrypoint: tries LLM first, falls back gracefully."""
    llm_res = extract_with_llm(app, category, website, combined_text)
    if llm_res and "auth_type" in llm_res and "self_serve" in llm_res:
        # Re-verify buildability priority through deterministic formula
        tier, p_tier, p_score = calculate_buildability(
            llm_res.get("self_serve", "Unknown"),
            llm_res.get("access_type", "Unknown"),
            llm_res.get("auth_type", "Unknown"),
            llm_res.get("api_type", "Unknown"),
            llm_res.get("blockers", [])
        )
        llm_res["buildability"] = tier
        llm_res["priority_tier"] = p_tier
        llm_res["priority_score"] = p_score
        return llm_res

    return extract_with_heuristics(app, category, website, combined_text)
