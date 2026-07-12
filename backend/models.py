from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Verdict(str, Enum):
    recommend = "recommend"
    caution = "caution"
    reject = "reject"


class Workspace(str, Enum):
    general = "general"
    embedded = "embedded"


class Job(BaseModel):
    """Normalized, account-free job record accepted from every connector."""

    id: str
    workspace: Workspace = Workspace.general
    platform: str
    title: str
    category: str = "other"
    budget: str | None = None
    budgetAmount: float | None = Field(default=None, ge=0)
    currency: str | None = None
    client: str | None = None
    clientReputation: int = Field(default=3, ge=1, le=5)
    posted: str | None = None
    url: str | None = None
    description: str
    deliverables: list[str] = Field(default_factory=list)
    deliverableClarity: int = Field(default=3, ge=1, le=5)
    constraints: list[str] = Field(default_factory=list)
    requiredSkills: list[str] = Field(default_factory=list)
    manualWorkLevel: int = Field(default=3, ge=1, le=5)
    riskLevel: int = Field(default=3, ge=1, le=5)
    estimatedMinutes: int = Field(default=120, ge=1)
    aiAutonomy: float = Field(default=0.5, ge=0, le=1)
    embedded: dict[str, Any] = Field(default_factory=dict)
    source: str = "manual"
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("platform", "title", "description")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field must not be empty")
        return value


class ScoreBreakdown(BaseModel):
    aiAutonomy: int
    timeFit: int
    manualEffort: int
    risk: int
    budgetFit: int
    clientReputation: int
    deliverableClarity: int
    embeddedReadiness: int | None = None


class ScoredJob(Job):
    score: int = Field(ge=0, le=100)
    verdict: Verdict
    reason: str
    scoreBreakdown: ScoreBreakdown
    proposalDraft: str
    deliveryPlan: list[str]
    embeddedAssessment: "EmbeddedAssessment | None" = None


class SearchRequest(BaseModel):
    workspace: Workspace = Workspace.general
    platforms: list[str] = Field(default_factory=list)
    query: str = ""
    categories: list[str] = Field(default_factory=list)
    max_results: int = Field(default=50, ge=1, le=200)


class TargetProfile(BaseModel):
    """A transparent filter for work that can be delivered with limited human input."""

    maxMinutes: int = Field(default=120, ge=15, le=480)
    minimumBudgetCny: float = Field(default=50, ge=0)
    minimumAiAutonomy: float = Field(default=0.85, ge=0, le=1)
    maximumManualWorkLevel: int = Field(default=2, ge=1, le=5)
    maximumRiskLevel: int = Field(default=2, ge=1, le=5)


class EmbeddedTargetProfile(TargetProfile):
    """Strict profile for work an AI agent can prepare without touching real hardware."""

    workspace: Workspace = Workspace.embedded
    minimumAgentReadiness: int = Field(default=80, ge=0, le=100)
    allowSimulationOnly: bool = True


class EmbeddedAssessment(BaseModel):
    """Facts that separate desk-only firmware work from real-world hardware work."""

    target: str = "unknown"
    scope: str = "unknown"
    sourceFilesProvided: bool = False
    toolchainKnown: bool = False
    testFixturesProvided: bool = False
    hardwareAccessRequired: bool = False
    physicalDeliveryRequired: bool = False
    onDeviceTestingRequired: bool = False
    productionFlashOrDeploy: bool = False
    safetyCritical: bool = False
    agentReadiness: int = Field(default=0, ge=0, le=100)
    blockers: list[str] = Field(default_factory=list)
    recommendedArtifacts: list[str] = Field(default_factory=list)


class PlatformProfile(BaseModel):
    workspace: Workspace = Workspace.general
    name: str
    region: str
    url: str
    workModel: str
    intakeMode: str
    bestFor: list[str]
    suitability: str
    note: str
    requiresAccount: bool = True
    agentAccess: str = "只读导入；平台操作需人工确认"


class ConnectorHealth(BaseModel):
    platform: str
    mode: str
    ok: bool
    message: str
    workspace: Workspace = Workspace.general


class ConnectorInfo(ConnectorHealth):
    supportsCsv: bool = False
    supportsPaste: bool = True
    supportsDomCapture: bool = False


class ImportResult(BaseModel):
    imported: int
    rejected: int = 0
    errors: list[str] = Field(default_factory=list)


class PasteRequest(BaseModel):
    workspace: Workspace = Workspace.general
    platform: str
    text: str = Field(min_length=10, max_length=50_000)


class DomCaptureRequest(BaseModel):
    workspace: Workspace = Workspace.general
    platform: str
    jobs: list[dict[str, Any]] = Field(min_length=1, max_length=200)


class ProposalRequest(BaseModel):
    language: Literal["auto", "en", "zh"] = "auto"


class HighRiskConfirmation(BaseModel):
    action: Literal["submit_proposal", "send_message", "accept_contract", "make_payment"]
    job_id: str | None = None
    confirmation: str


class AuditEvent(BaseModel):
    id: int
    event: str
    details: dict[str, Any]
    created_at: str
