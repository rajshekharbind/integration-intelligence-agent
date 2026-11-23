from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AuthType(str, Enum):
    OAUTH2 = "OAuth 2.0"
    API_KEY = "API Key"
    BEARER_TOKEN = "Bearer Token"
    BASIC_AUTH = "Basic Auth"
    MULTI_AUTH = "OAuth 2.0 / API Key"
    JWT = "JWT / Key Pair"
    CUSTOM_SESSION = "Session / Custom"
    UNKNOWN = "Unknown"


class AccessType(str, Enum):
    SELF_SERVE = "Self-serve"
    PARTIAL = "Self-serve with restrictions"
    PAID_GATED = "Paid / Tier gated"
    PARTNER_APPROVAL = "Partner approval required"
    UNKNOWN = "Unknown"


class APIType(str, Enum):
    REST = "REST"
    GRAPHQL = "GraphQL"
    REST_AND_GRAPHQL = "REST / GraphQL"
    GRPC = "gRPC"
    WEBHOOK_ONLY = "Webhooks only"
    SOAP = "SOAP / XML"
    UNKNOWN = "Unknown"


class MCPStatus(str, Enum):
    OFFICIAL = "Official"
    COMMUNITY = "Community / 3rd Party"
    NOT_AVAILABLE = "Not available"
    UNKNOWN = "Unknown"


class BuildabilityTier(str, Enum):
    P1_EASY_WIN = "P1 - Easy Win"
    P2_STANDARD = "P2 - Standard Build"
    P3_CONDITIONAL = "P3 - Conditional / Complex"
    P4_OUTREACH_REQUIRED = "P4 - Outreach Required"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    RESEARCHED = "researched"
    EVIDENCE_CHECKED = "evidence_checked"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    HUMAN_VERIFIED = "human_verified"
    FAILED = "failed"


class SourceEvidence(BaseModel):
    url: str
    title: str = ""
    snippet: str = ""
    is_official_domain: bool = False
    http_status: int = 200
    supports_field: Optional[str] = None  # e.g. "auth", "api", "access", "mcp"


class AppResearchResult(BaseModel):
    app: str
    category: str
    website: str
    description: str
    auth_type: str = AuthType.UNKNOWN.value
    auth_details: str = ""
    self_serve: str = "Unknown"  # Yes / Partial / No / Unknown
    access_type: str = AccessType.UNKNOWN.value
    access_restrictions: str = ""
    api_type: str = APIType.UNKNOWN.value
    api_surface: str = ""
    mcp_status: str = MCPStatus.UNKNOWN.value
    mcp_details: str = ""
    buildability: str = BuildabilityTier.P3_CONDITIONAL.value
    priority_tier: str = "P3"
    priority_score: int = 50
    blockers: List[str] = Field(default_factory=list)
    evidence_urls: List[str] = Field(default_factory=list)
    sources: List[SourceEvidence] = Field(default_factory=list)
    verification_status: str = VerificationStatus.RESEARCHED.value
    confidence_score: float = 0.8
    notes: str = ""
    retry_count: int = 0
    research_timestamp: str = ""


class ClaimVerification(BaseModel):
    app: str
    field: str
    claimed_value: str
    evidence_url: str
    url_accessible: bool
    is_official_domain: bool
    source_keyword_match: bool
    status: str  # verified, needs_review, failed
    notes: str = ""


class AuditRecord(BaseModel):
    app: str
    category: str
    field: str
    agent_claim: str
    evidence_url: str
    auditor_result: str  # correct, incorrect, unclear
    correction: str = ""
    auditor_notes: str = ""
