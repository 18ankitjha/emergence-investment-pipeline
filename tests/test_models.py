import pytest
from pydantic import ValidationError

from investment_pipeline.enrichment.evidence import build_evidence_packet
from investment_pipeline.models import CandidateStartup, EvidenceItem, ScoreBreakdown


def test_candidate_requires_name_and_one_liner():
    candidate = CandidateStartup(id="yc-1", name="Acme", one_liner="Automates invoices")
    assert candidate.name == "Acme"


def test_candidate_rejects_empty_name():
    with pytest.raises(ValidationError):
        CandidateStartup(id="yc-1", name=" ", one_liner="Automates invoices")


def test_evidence_id_prefix_validation():
    with pytest.raises(ValidationError):
        EvidenceItem(
            evidence_id="BAD1",
            candidate_id="yc-1",
            source="yc",
            url="https://example.com",
            claim="Claim",
            category="product",
        )


def test_score_total_must_match_components():
    with pytest.raises(ValidationError):
        ScoreBreakdown(
            team=1,
            product=1,
            market=1,
            traction_freshness=1,
            why_now=1,
            defensibility=1,
            risk_adjustment=1,
            total=99,
        )


def test_evidence_packet_extracts_yc_team_signal():
    candidate = CandidateStartup(
        id="yc-1",
        name="Acme",
        one_liner="Automates invoices",
        description="Founded by engineers from Stripe. The product automates invoice workflows.",
    )

    packet = build_evidence_packet(candidate, website_text=None, hn_hits=[])

    assert any(item.evidence_id == "YC4" and item.category == "team" for item in packet.evidence)
