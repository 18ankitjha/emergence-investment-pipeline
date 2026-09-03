from __future__ import annotations

import re

from investment_pipeline.models import (
    AnalysisResult,
    EvidencePacket,
    ScoreBreakdown,
    deterministic_total,
    recommendation_for_score,
)

BUYER_TERMS = (
    "smb",
    "mid-market",
    "business",
    "businesses",
    "companies",
    "teams",
    "fintech",
    "fintechs",
    "banks",
    "universities",
    "enterprise",
    "manufacturers",
    "brands",
    "lenders",
    "security teams",
)
QUANTIFIED_TRACTION = re.compile(
    r"\$\s?\d[\d.,]*\s?[kmb]?\s*(?:mrr|arr|revenue|/mo)"
    r"|\b(?:mrr|arr)\b"
    r"|\bfrom\s+\$?\d[\d.,]*\s+to\s+\$?\d"
    r"|\d[\d,.]*\s*(?:paying customers|paying users|customers|clients|brands|banks|lenders|design partners|enterprises|deployments)"
    r"|\d+\s*%\s*(?:wow|mom|week[- ]on[- ]week|month[- ]on[- ]month|growth|retention)",
    re.IGNORECASE,
)


def normalize_score_and_recommendation(analysis: AnalysisResult, packet: EvidencePacket | None = None) -> AnalysisResult:
    score = analysis.score_breakdown
    normalized_score = ScoreBreakdown(
        team=score.team,
        product=score.product,
        market=score.market,
        traction_freshness=score.traction_freshness,
        why_now=score.why_now,
        defensibility=score.defensibility,
        risk_adjustment=score.risk_adjustment,
        total=deterministic_total(score),
        rationale_by_component=score.rationale_by_component,
    )
    recommendation = recommendation_for_score(normalized_score.total)
    if packet and recommendation == "Take a meeting" and not has_take_meeting_evidence(packet):
        recommendation = "Watch"
    return analysis.model_copy(
        update={
            "score_breakdown": normalized_score,
            "recommendation": recommendation,
        }
    )


def has_take_meeting_evidence(packet: EvidencePacket) -> bool:
    text = " ".join(item.claim.lower() for item in packet.evidence)
    has_product = "YC1" in packet.evidence_ids and (
        "YC2" in packet.evidence_ids or any(item.source == "website" for item in packet.evidence)
    )
    has_buyer = any(term in text for term in BUYER_TERMS)
    return has_product and has_buyer and has_hard_traction(packet, text)


def has_hard_traction(packet: EvidencePacket, text: str) -> bool:
    strong_hn = any(
        item.source == "hn"
        and "No HN story traction" not in item.claim
        and _story_points(item.claim) >= 20
        for item in packet.evidence
    )
    return strong_hn or bool(QUANTIFIED_TRACTION.search(text))


def _story_points(claim: str) -> int:
    match = re.search(r"had\s+(\d+)\s+points", claim)
    return int(match.group(1)) if match else 0
