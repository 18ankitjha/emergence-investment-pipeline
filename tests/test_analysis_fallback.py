from investment_pipeline.analysis.llm import deterministic_fallback_analysis
from investment_pipeline.analysis.validation import validate_analysis
from investment_pipeline.enrichment.evidence import build_evidence_packet
from investment_pipeline.models import CandidateStartup

WEB_TEXT = "We help mid-market finance teams automate month-end close across their books and ERP."


def packet_for(name: str, one_liner: str, description: str | None = None, website: str | None = "https://acme.example", website_text: str | None = WEB_TEXT):
    candidate = CandidateStartup(id=f"yc-{name}", name=name, one_liner=one_liner, description=description, website=website, batch="Spring 2026")
    return build_evidence_packet(candidate, website_text=website_text, hn_hits=[])


def test_fallback_only_cites_evidence_ids_in_the_packet():
    packet = packet_for("NoWeb", "AI agents for lenders", description=None, website=None, website_text=None)
    analysis = deterministic_fallback_analysis(packet, "test")
    known = packet.evidence_ids
    for claim in analysis.cited_claims:
        assert claim.evidence_ids
        assert set(claim.evidence_ids) <= known
    assert validate_analysis(packet, analysis) == []


def test_fallback_risks_differ_between_companies():
    regulated = deterministic_fallback_analysis(
        packet_for("Lend", "AI workforce for lenders", description="Compliance automation for lending teams."),
        "test",
    )
    generic = deterministic_fallback_analysis(
        packet_for("Ops", "AI agents for scheduling", description="We automate calendar work."),
        "test",
    )
    assert regulated.risks != generic.risks
    assert any("regulated" in risk for risk in regulated.risks)


def test_fallback_flags_missing_website():
    packet = packet_for("Dark", "AI agents for ops teams", description="AI agents for ops teams.", website=None, website_text=None)
    analysis = deterministic_fallback_analysis(packet, "test")
    assert any("website" in risk.lower() for risk in analysis.risks)
