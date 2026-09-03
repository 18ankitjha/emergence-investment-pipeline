from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from investment_pipeline.config import SCORE_WEIGHTS


RecommendationCall = Literal["Pass", "Watch", "Take a meeting"]
EvidenceCategory = Literal[
    "team",
    "product",
    "market",
    "traction",
    "freshness",
    "risk",
    "website",
    "source",
]
EvidenceSource = Literal["yc", "website", "hn", "pipeline"]
Confidence = Literal["high", "medium", "low"]


class SourceRef(BaseModel):
    id: str
    source_type: EvidenceSource
    title: str
    url: str
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_path: str | None = None


class CandidateStartup(BaseModel):
    id: str
    name: str
    website: str | None = None
    one_liner: str
    description: str | None = None
    batch: str | None = None
    industry: str | None = None
    status: str | None = None
    stage: str | None = None
    tags: list[str] = Field(default_factory=list)
    team_size: int | None = None
    source_refs: list[SourceRef] = Field(default_factory=list)
    raw_source_path: str | None = None

    @field_validator("name", "one_liner")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class EvidenceItem(BaseModel):
    evidence_id: str
    candidate_id: str
    source: EvidenceSource
    url: str
    claim: str
    category: EvidenceCategory
    confidence: Confidence = "medium"

    @field_validator("evidence_id")
    @classmethod
    def evidence_id_format(cls, value: str) -> str:
        if not value or not any(value.startswith(prefix) for prefix in ("YC", "WEB", "HN", "PIPE")):
            raise ValueError("evidence_id must start with YC, WEB, HN, or PIPE")
        return value


class EvidencePacket(BaseModel):
    candidate: CandidateStartup
    evidence: list[EvidenceItem]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def evidence_ids(self) -> set[str]:
        return {item.evidence_id for item in self.evidence}


class CitedClaim(BaseModel):
    claim: str
    evidence_ids: list[str]


class ScoreBreakdown(BaseModel):
    team: int = Field(ge=0, le=SCORE_WEIGHTS["team"])
    product: int = Field(ge=0, le=SCORE_WEIGHTS["product"])
    market: int = Field(ge=0, le=SCORE_WEIGHTS["market"])
    traction_freshness: int = Field(ge=0, le=SCORE_WEIGHTS["traction_freshness"])
    why_now: int = Field(ge=0, le=SCORE_WEIGHTS["why_now"])
    defensibility: int = Field(ge=0, le=SCORE_WEIGHTS["defensibility"])
    risk_adjustment: int = Field(ge=0, le=SCORE_WEIGHTS["risk_adjustment"])
    total: int = Field(ge=0, le=100)
    rationale_by_component: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def total_matches_components(self) -> "ScoreBreakdown":
        expected = deterministic_total(self)
        if self.total != expected:
            raise ValueError(f"total must equal component sum {expected}")
        return self


class AnalysisResult(BaseModel):
    candidate_id: str
    product_summary: str
    team_assessment: str
    market_assessment: str
    why_now: str
    risks: list[str]
    open_questions: list[str]
    score_breakdown: ScoreBreakdown
    recommendation: RecommendationCall
    recommendation_rationale: str
    why_we_care: str
    what_would_change_mind: list[str]
    cited_claims: list[CitedClaim]
    analysis_mode: Literal["openai", "gemini", "deterministic_fallback"] = "deterministic_fallback"


class ValidationIssue(BaseModel):
    candidate_id: str
    severity: Literal["error", "warning"]
    message: str


class ValidationReport(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    issues: list[ValidationIssue] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)


class RunManifest(BaseModel):
    run_id: str
    topic: str
    thesis: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    selected_count: int
    analysis_mode: str
    analysis_model: str | None = None
    sources: list[str]
    command: str


def deterministic_total(score: ScoreBreakdown | dict[str, Any]) -> int:
    if isinstance(score, ScoreBreakdown):
        data = score.model_dump()
    else:
        data = score
    return int(
        data["team"]
        + data["product"]
        + data["market"]
        + data["traction_freshness"]
        + data["why_now"]
        + data["defensibility"]
        + data["risk_adjustment"]
    )


def recommendation_for_score(total: int) -> RecommendationCall:
    if total >= 75:
        return "Take a meeting"
    if total >= 55:
        return "Watch"
    return "Pass"
