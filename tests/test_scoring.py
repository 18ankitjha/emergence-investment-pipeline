from investment_pipeline.analysis.scoring import normalize_score_and_recommendation
from investment_pipeline.models import AnalysisResult, CandidateStartup, CitedClaim, EvidenceItem, EvidencePacket, ScoreBreakdown


def make_analysis(total: int = 55) -> AnalysisResult:
    score = ScoreBreakdown(
        team=10,
        product=10,
        market=10,
        traction_freshness=10,
        why_now=5,
        defensibility=5,
        risk_adjustment=5,
        total=55,
    )
    return AnalysisResult(
        candidate_id="yc-1",
        product_summary="Product",
        team_assessment="Team",
        market_assessment="Market",
        why_now="Why now",
        risks=["Risk"],
        open_questions=["Question"],
        score_breakdown=score,
        recommendation="Pass",
        recommendation_rationale="Rationale",
        why_we_care="Care",
        what_would_change_mind=["Proof"],
        cited_claims=[CitedClaim(claim="Claim", evidence_ids=["YC1"])],
    )


def test_recommendation_is_thresholded_from_total():
    analysis = normalize_score_and_recommendation(make_analysis())
    assert analysis.score_breakdown.total == 55
    assert analysis.recommendation == "Watch"


def test_take_meeting_requires_supported_evidence_packet():
    analysis = make_analysis()
    analysis = analysis.model_copy(
        update={
            "score_breakdown": ScoreBreakdown(
                team=20,
                product=20,
                market=15,
                traction_freshness=15,
                why_now=10,
                defensibility=10,
                risk_adjustment=10,
                total=100,
            )
        }
    )
    packet = EvidencePacket(
        candidate=CandidateStartup(id="yc-1", name="Acme", one_liner="AI workflow tool"),
        evidence=[
            EvidenceItem(
                evidence_id="YC1",
                candidate_id="yc-1",
                source="yc",
                url="https://example.com",
                claim="Acme: AI workflow tool",
                category="product",
            )
        ],
    )

    normalized = normalize_score_and_recommendation(analysis, packet)

    assert normalized.score_breakdown.total == 100
    assert normalized.recommendation == "Watch"
