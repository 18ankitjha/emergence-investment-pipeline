from pathlib import Path

from investment_pipeline.models import (
    AnalysisResult,
    CandidateStartup,
    CitedClaim,
    EvidenceItem,
    EvidencePacket,
    ScoreBreakdown,
)
from investment_pipeline.recommendation.memo import render_memo


def test_memo_contains_core_sections():
    packet = EvidencePacket(
        candidate=CandidateStartup(id="yc-1", name="Acme", website="https://example.com", one_liner="Automates invoices"),
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
        product_summary="Acme automates invoices.",
        team_assessment="Unknown.",
        market_assessment="SMB finance teams.",
        why_now="AI can handle document workflows.",
        risks=["Thin evidence."],
        open_questions=["Who pays?"],
        score_breakdown=ScoreBreakdown(
            team=10,
            product=12,
            market=8,
            traction_freshness=5,
            why_now=7,
            defensibility=4,
            risk_adjustment=4,
            total=50,
        ),
        recommendation="Pass",
        recommendation_rationale="Below threshold.",
        why_we_care="Relevant workflow.",
        what_would_change_mind=["Customer proof."],
        cited_claims=[CitedClaim(claim="Product claim.", evidence_ids=["YC1"])],
    )

    template_dir = Path("src/investment_pipeline/recommendation/templates")
    memo = render_memo(packet, analysis, template_dir)

    assert "# Acme" in memo
    assert "## Sources" in memo
    assert "**Score:** 50/100" in memo

