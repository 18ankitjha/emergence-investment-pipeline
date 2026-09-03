from __future__ import annotations

from investment_pipeline.models import AnalysisResult, EvidencePacket, ScoreBreakdown, deterministic_total, recommendation_for_score


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
    has_product = "YC1" in packet.evidence_ids and ("YC2" in packet.evidence_ids or any(item.source == "website" for item in packet.evidence))
    has_buyer = any(
        term in text
        for term in (
            "smb",
            "mid-market",
            "business",
            "businesses",
            "companies",
            "teams",
            "fintech",
            "banks",
            "universities",
            "enterprise",
            "manufacturers",
            "security teams",
        )
    )
    has_traction = any(
        item.source == "hn" and "No HN story traction" not in item.claim and (" points " in item.claim or " comments " in item.claim)
        for item in packet.evidence
    ) or any(
        term in text
        for term in (
            "customer",
            "customers",
            "users",
            "mrr",
            "revenue",
            "live across",
            "early users",
            "users have",
            "companies like",
            "trusted by",
            "saved",
            "processed",
            "cut time",
            "growth",
        )
    )
    return has_product and has_buyer and has_traction
