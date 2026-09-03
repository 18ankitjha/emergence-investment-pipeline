from __future__ import annotations

from investment_pipeline.models import (
    AnalysisResult,
    EvidencePacket,
    ValidationIssue,
    deterministic_total,
    recommendation_for_score,
)


def validate_analysis(packet: EvidencePacket, analysis: AnalysisResult) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    evidence_ids = packet.evidence_ids
    score = analysis.score_breakdown

    if score.total != deterministic_total(score):
        issues.append(
            ValidationIssue(
                candidate_id=packet.candidate.id,
                severity="error",
                message=f"score total {score.total} does not equal component sum {deterministic_total(score)}",
            )
        )
    ladder = ["Pass", "Watch", "Take a meeting"]
    if ladder.index(analysis.recommendation) > ladder.index(recommendation_for_score(score.total)):
        issues.append(
            ValidationIssue(
                candidate_id=packet.candidate.id,
                severity="error",
                message=(
                    f"recommendation {analysis.recommendation!r} is more bullish than score {score.total} allows"
                ),
            )
        )

    if not analysis.cited_claims:
        issues.append(
            ValidationIssue(
                candidate_id=packet.candidate.id,
                severity="error",
                message="analysis has no cited claims",
            )
        )

    for cited_claim in analysis.cited_claims:
        if not cited_claim.evidence_ids:
            issues.append(
                ValidationIssue(
                    candidate_id=packet.candidate.id,
                    severity="error",
                    message=f"claim has no citations: {cited_claim.claim}",
                )
            )
        for evidence_id in cited_claim.evidence_ids:
            if evidence_id not in evidence_ids:
                issues.append(
                    ValidationIssue(
                        candidate_id=packet.candidate.id,
                        severity="error",
                        message=f"claim cites unknown evidence id {evidence_id}: {cited_claim.claim}",
                    )
                )

    if analysis.recommendation == "Take a meeting":
        weak_evidence = [item for item in packet.evidence if item.confidence == "low"]
        if len(packet.evidence) <= 4 or len(weak_evidence) >= 3:
            issues.append(
                ValidationIssue(
                    candidate_id=packet.candidate.id,
                    severity="warning",
                    message="Take a meeting recommendation has limited supporting evidence",
                )
            )
    return issues

