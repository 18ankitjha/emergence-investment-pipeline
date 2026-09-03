from investment_pipeline.analysis.validation import validate_analysis
from investment_pipeline.models import (
    AnalysisResult,
    CandidateStartup,
    CitedClaim,
    EvidenceItem,
    EvidencePacket,
    ScoreBreakdown,
)


def test_validation_rejects_unknown_evidence_id():
    packet = EvidencePacket(
        candidate=CandidateStartup(id="yc-1", name="Acme", one_liner="Automates invoices"),
        evidence=[
            EvidenceItem(
                evidence_id="YC1",
                candidate_id="yc-1",
                source="yc",
                url="https://example.com",
                claim="Acme automates invoices",
                category="product",
            )
        ],
    )
    analysis = AnalysisResult(
        candidate_id="yc-1",
        product_summary="Product",
        team_assessment="Team",
        market_assessment="Market",
        why_now="Why now",
        risks=["Risk"],
        open_questions=["Question"],
        score_breakdown=ScoreBreakdown(
            team=1,
            product=1,
            market=1,
            traction_freshness=1,
            why_now=1,
            defensibility=1,
            risk_adjustment=1,
            total=7,
        ),
        recommendation="Pass",
        recommendation_rationale="Rationale",
        why_we_care="Care",
        what_would_change_mind=["Proof"],
        cited_claims=[CitedClaim(claim="Unsupported", evidence_ids=["WEB9"])],
    )

    issues = validate_analysis(packet, analysis)

    assert any(issue.severity == "error" for issue in issues)

