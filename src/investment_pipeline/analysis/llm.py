from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
from pydantic import ValidationError

from investment_pipeline.analysis.scoring import QUANTIFIED_TRACTION
from investment_pipeline.config import THESIS, Settings
from investment_pipeline.models import (
    AnalysisResult,
    CitedClaim,
    EvidenceItem,
    EvidencePacket,
    ScoreBreakdown,
    deterministic_total,
    recommendation_for_score,
)

SCORE_COMPONENTS = (
    "team",
    "product",
    "market",
    "traction_freshness",
    "why_now",
    "defensibility",
    "risk_adjustment",
)

REGULATED_TERMS = ("insurance", "insurer", "lending", "lender", "compliance", "regulatory", "fintech", "bank", "kyc", "aml")


async def analyze_packet(settings: Settings, packet: EvidencePacket, prompts_dir: Path) -> AnalysisResult:
    if not settings.openai_api_key:
        return deterministic_fallback_analysis(packet, "OPENAI_API_KEY was not set for this run")
    try:
        return await openai_analysis(settings, packet, prompts_dir)
    except Exception as exc:  # noqa: BLE001 - any failure here must degrade to the offline path
        return deterministic_fallback_analysis(packet, f"OpenAI analysis failed and was replaced by the offline path: {exc}")


async def openai_analysis(settings: Settings, packet: EvidencePacket, prompts_dir: Path) -> AnalysisResult:
    system_prompt = (prompts_dir / "analysis_system.md").read_text(encoding="utf-8")
    user_prompt = (prompts_dir / "analysis_user.md").read_text(encoding="utf-8").format(
        thesis=THESIS,
        evidence_packet=json.dumps(packet.model_dump(mode="json"), indent=2),
    )
    payload = {
        "model": settings.openai_model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "startup_analysis",
                "strict": True,
                "schema": analysis_json_schema(),
            }
        },
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post("https://api.openai.com/v1/responses", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    parsed = json.loads(extract_response_text(data))
    parsed["candidate_id"] = packet.candidate.id
    parsed["analysis_mode"] = "openai"
    parsed = clamp_parsed_scores(parsed)
    parsed["score_breakdown"]["total"] = deterministic_total(parsed["score_breakdown"])
    parsed["recommendation"] = recommendation_for_score(parsed["score_breakdown"]["total"])
    parsed["cited_claims"] = drop_unknown_citations(parsed.get("cited_claims", []), packet.evidence_ids)
    try:
        return AnalysisResult.model_validate(parsed)
    except ValidationError as exc:
        return deterministic_fallback_analysis(packet, f"OpenAI response did not match the analysis schema: {exc}")


def extract_response_text(data: dict) -> str:
    if data.get("output_text"):
        return data["output_text"]
    for output in data.get("output", []):
        for content in output.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]
    raise ValueError("OpenAI response did not include output text")


def clamp_parsed_scores(parsed: dict) -> dict:
    limits = {"team": 20, "product": 20, "market": 15, "traction_freshness": 15, "why_now": 10, "defensibility": 10, "risk_adjustment": 10}
    breakdown = parsed.get("score_breakdown", {})
    for component, ceiling in limits.items():
        raw = breakdown.get(component, 0)
        breakdown[component] = max(0, min(int(raw), ceiling))
    parsed["score_breakdown"] = breakdown
    return parsed


def drop_unknown_citations(cited_claims: list[dict], known_ids: set[str]) -> list[dict]:
    cleaned = []
    for claim in cited_claims:
        ids = [evidence_id for evidence_id in claim.get("evidence_ids", []) if evidence_id in known_ids]
        if ids:
            cleaned.append({"claim": claim.get("claim", ""), "evidence_ids": ids})
    return cleaned


def deterministic_fallback_analysis(packet: EvidencePacket, reason: str) -> AnalysisResult:
    candidate = packet.candidate
    ids = packet.evidence_ids
    text = " ".join(item.claim.lower() for item in packet.evidence)
    has_web = any(item.source == "website" for item in packet.evidence)
    hn_items = [item for item in packet.evidence if item.source == "hn" and "No HN story traction" not in item.claim]
    is_acquired_or_inactive = "acquired" in text or "inactive" in text
    yc_product = evidence_claim(packet, "YC2") or evidence_claim(packet, "YC1") or candidate.one_liner
    yc_meta = evidence_claim(packet, "YC3") or "YC metadata unavailable."
    yc_team_signal = evidence_claim(packet, "YC4")
    web_claim = evidence_claim(packet, "WEB1") or "Website text unavailable."

    yc_product_ids = [evidence_id for evidence_id in ("YC1", "YC2") if evidence_id in ids] or ["YC1"]
    yc_meta_ids = [evidence_id for evidence_id in ("YC3",) if evidence_id in ids] or ["YC1"]
    yc_team_ids = [evidence_id for evidence_id in ("YC4",) if evidence_id in ids]
    web_ids = [evidence_id for evidence_id in ("WEB1",) if evidence_id in ids]
    hn_ids = [evidence_id for evidence_id in sorted(ids) if evidence_id.startswith("HN")]
    freshness_ids = (hn_ids or web_ids or yc_meta_ids)[:2]

    does_work = any(term in text for term in ("workflow", "operations", "back-office", "back office", "automate", "execute", "takes action", "system of action"))
    is_thin_layer = any(term in text for term in ("context layer", "data layer", "data infrastructure", "api for", "apis for", "developer platform")) and not does_work

    team = 6
    if candidate.team_size is not None and candidate.team_size <= 10:
        team += 2
    if candidate.batch:
        team += 2
    if yc_team_signal:
        team += 5

    product = 5
    if any(term in text for term in ("ai", "agent", "automate")):
        product += 4
    if does_work:
        product += 4
    if has_web:
        product += 2
    if is_thin_layer:
        product -= 3

    market = 5
    if any(term in text for term in ("smb", "small business", "mid-market", "small and medium")):
        market += 5
    elif any(term in text for term in ("business", "b2b", "companies", "teams", "enterprise")):
        market += 3
    if any(term in text for term in ("finance", "accounting", "bookkeeping", "sales", "support", "compliance", "supply chain", "insurance", "procurement", "hr", "payroll")):
        market += 3

    hn_points = top_hn_points(hn_items)
    traction = 3 + min(4, len(hn_items) * 2)
    if candidate.batch:
        traction += 2
    if has_web:
        traction += 2
    if hn_points >= 20:
        traction += 3
    if hn_points >= 100:
        traction += 2
    if QUANTIFIED_TRACTION.search(text):
        traction += 3

    why_now = 3 + (3 if any(term in text for term in ("ai", "agent", "llm")) else 0) + (2 if does_work else 0)
    defensibility = 3 + (2 if "integrat" in text else 0) + (2 if does_work else 0)
    risk_adjustment = 4 + (2 if has_web else 0) + (1 if hn_items else 0)
    if is_thin_layer:
        why_now -= 2
    if is_acquired_or_inactive:
        traction = min(traction, 6)
        risk_adjustment = 0

    components = {
        "team": clamp(team, 20),
        "product": clamp(product, 20),
        "market": clamp(market, 15),
        "traction_freshness": clamp(traction, 15),
        "why_now": clamp(why_now, 10),
        "defensibility": clamp(defensibility, 10),
        "risk_adjustment": clamp(risk_adjustment, 10),
    }
    total = deterministic_total(components)
    recommendation = recommendation_for_score(total)
    if is_acquired_or_inactive and total >= 55:
        recommendation = "Pass"

    hn_summary = summarize_hn(candidate.name, hn_items)
    team_evidence_note = (
        f"YC description adds a team signal: {shorten(yc_team_signal, 260)} [{', '.join(yc_team_ids)}]"
        if yc_team_signal and yc_team_ids
        else "Founder backgrounds are not described in the collected evidence."
    )

    return AnalysisResult(
        candidate_id=candidate.id,
        product_summary=(
            f"{candidate.name} is described as “{candidate.one_liner}”. "
            f"The fullest product evidence reads: {shorten(yc_product, 320)} [{', '.join(yc_product_ids)}]"
        ),
        team_assessment=(
            f"YC lists {candidate.name} as {candidate.status or 'status unknown'} / "
            f"{candidate.stage or 'stage unknown'}, team size "
            f"{candidate.team_size if candidate.team_size is not None else 'undisclosed'}. "
            f"{team_evidence_note} [{', '.join(yc_meta_ids)}]"
        ),
        market_assessment=market_assessment_text(yc_product, web_claim, yc_meta_ids, web_ids),
        why_now=(
            "AI agents are moving from advice to execution inside operational workflows, which is where this thesis looks. "
            f"Freshness/traction read: YC {candidate.batch or 'batch unknown'}; {hn_summary} "
            f"[{', '.join(freshness_ids)}]"
        ),
        risks=derive_risks(packet, has_web, hn_items, is_acquired_or_inactive, bool(yc_team_signal)),
        open_questions=derive_open_questions(packet, has_web, hn_items, bool(yc_team_signal)),
        score_breakdown=ScoreBreakdown(
            **components,
            total=total,
            rationale_by_component={
                "team": team_evidence_note,
                "product": (
                    "Positioned as a data/context layer rather than a system of action; scored down."
                    if is_thin_layer
                    else f"AI plus workflow-execution language; website support {'available' if has_web else 'missing'}."
                ),
                "market": "SMB/mid-market and operational-domain hints only; no market sizing was attempted from the packet.",
                "traction_freshness": hn_summary + f" YC {candidate.batch or 'batch unknown'} is the main freshness anchor.",
                "why_now": "Scored on AI/agent language plus evidence that the product executes work, not just answers.",
                "defensibility": "Conservative unless workflow depth, integrations, or proprietary data are visible.",
                "risk_adjustment": "Rewards a reachable website and any real HN discussion; penalises missing evidence.",
            },
        ),
        recommendation=recommendation,
        recommendation_rationale=(
            f"{recommendation}: deterministic evidence-only scoring. {reason}. "
            f"The call leans on YC and company-site evidence and treats HN as a weak freshness signal. YC metadata: {shorten(yc_meta, 200)}"
        ),
        why_we_care=(
            f"Fits the thesis only if {candidate.name} owns a repeated operating workflow rather than a thin assistant layer. "
            f"The evidence points to: {shorten(candidate.one_liner, 120)} [{yc_product_ids[0]}]"
        ),
        what_would_change_mind=[
            f"Named paying customers or usage numbers for {candidate.name} beyond the YC blurb.",
            "Founder-background evidence showing strong domain or technical fit for this workflow.",
            "Proof the product executes an end-to-end workflow with integrations or proprietary data, not just chat.",
        ],
        cited_claims=[
            CitedClaim(claim="Product description is taken from YC metadata.", evidence_ids=yc_product_ids),
            CitedClaim(claim="Company stage, status, and team size come from YC metadata.", evidence_ids=yc_meta_ids),
            CitedClaim(
                claim="Founder/team background signal was extracted from the YC description where present.",
                evidence_ids=yc_team_ids or yc_meta_ids,
            ),
            CitedClaim(
                claim="Website evidence availability was recorded during enrichment.",
                evidence_ids=web_ids or yc_meta_ids,
            ),
            CitedClaim(
                claim="HN traction/freshness evidence was recorded during enrichment.",
                evidence_ids=hn_ids[:2] or freshness_ids,
            ),
        ],
        analysis_mode="deterministic_fallback",
    )


def market_assessment_text(yc_product: str, web_claim: str, yc_meta_ids: list[str], web_ids: list[str]) -> str:
    citations = ", ".join(dict.fromkeys(yc_meta_ids + web_ids))
    website_line = f" Website text adds: {shorten(web_claim, 220)}" if web_ids else " No website text was available to corroborate the market."
    return (
        f"The market read rests on the described workflow and buyer: {shorten(yc_product, 260)}"
        f"{website_line} Market size is not estimated from the packet and stays an open question. [{citations}]"
    )


def derive_risks(
    packet: EvidencePacket,
    has_web: bool,
    hn_items: list[EvidenceItem],
    is_acquired_or_inactive: bool,
    has_team_signal: bool,
) -> list[str]:
    candidate = packet.candidate
    text = " ".join(item.claim.lower() for item in packet.evidence)
    risks: list[str] = []

    if is_acquired_or_inactive:
        risks.append(f"YC lists {candidate.name} as {candidate.status}; it is outside the seed-stage sourcing target.")
    if not has_web:
        risks.append("No public website text was retrieved (WEB1), so product depth rests on the YC blurb alone.")
    if not hn_items:
        risks.append(f"No Hacker News discussion was found for {candidate.name}; external traction is unverified.")
    elif top_hn_points(hn_items) < 20:
        risks.append(f"HN interest is thin (top story {top_hn_points(hn_items)} points); not yet a real demand signal.")
    if not has_team_signal:
        risks.append("Founder backgrounds are not in the evidence (no YC4); team quality is unassessed.")
    if candidate.team_size is not None and candidate.team_size <= 2:
        risks.append(f"{candidate.team_size}-person team (YC3) against a broad platform ambition; execution risk.")
    if any(term in text for term in REGULATED_TERMS):
        risks.append("Operates in a regulated domain; licensing, audits, and long enterprise sales cycles apply.")
    if any(term in text for term in ("chatbot", "assistant", "copilot")) and "workflow" not in text:
        risks.append("Positioning leans on assistant/chat language; may be a thin interface rather than a system of action.")
    if any(term in text for term in ("context layer", "data layer", "infrastructure", "data infrastructure")) and "automate" not in text:
        risks.append("Positioned as a data/context layer; the thesis wants a system of action, so workflow pull is unproven.")
    if re.search(r"\$\d|\bmrr\b|\barr\b|week-on-week|month-on-month|\d+%\s*(?:wow|mom|growth)", text):
        risks.append("Revenue and growth figures are self-reported in the YC profile (YC2) and not independently verified.")

    baseline = "Evidence is limited to YC metadata plus a short website scrape; customer, retention, and funding facts are unverified."
    if baseline not in risks and len(risks) < 3:
        risks.append(baseline)
    return risks[:4]


def derive_open_questions(
    packet: EvidencePacket, has_web: bool, hn_items: list[EvidenceItem], has_team_signal: bool
) -> list[str]:
    candidate = packet.candidate
    text = " ".join(item.claim.lower() for item in packet.evidence)
    questions = ["Who is the economic buyer, and which manual budget line or headcount does this replace?"]

    if not hn_items:
        questions.append(f"Are there paying customers or usage numbers for {candidate.name} beyond the YC description?")
    else:
        questions.append("Does the HN interest convert into retained, paying accounts or is it launch-day attention?")
    if not has_team_signal:
        questions.append("What are the founders' backgrounds, and why are they the right team for this workflow?")
    if any(term in text for term in REGULATED_TERMS):
        questions.append("What licenses, carrier partners, or regulatory approvals are required, and are they in place?")
    if any(term in text for term in ("platform", "any workflow", "everything")):
        questions.append("What is the initial wedge workflow and the first design-partner customer?")
    if not has_web:
        questions.append("What does the product actually do end to end that the YC blurb does not spell out?")

    return list(dict.fromkeys(questions))[:4]


def summarize_hn(name: str, hn_items: list[EvidenceItem]) -> str:
    if not hn_items:
        return f"No Hacker News discussion was found for {name}."
    return f"{len(hn_items)} Hacker News item(s) matched {name}; top story {top_hn_points(hn_items)} points."


def top_hn_points(hn_items: list[EvidenceItem]) -> int:
    return max((points_from_hn_claim(item.claim) for item in hn_items), default=0)


def points_from_hn_claim(claim: str) -> int:
    match = re.search(r"had\s+(\d+)\s+points", claim)
    return int(match.group(1)) if match else 0


def analysis_json_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "candidate_id": {"type": "string"},
            "product_summary": {"type": "string"},
            "team_assessment": {"type": "string"},
            "market_assessment": {"type": "string"},
            "why_now": {"type": "string"},
            "risks": {"type": "array", "items": {"type": "string"}},
            "open_questions": {"type": "array", "items": {"type": "string"}},
            "score_breakdown": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "team": {"type": "integer", "minimum": 0, "maximum": 20},
                    "product": {"type": "integer", "minimum": 0, "maximum": 20},
                    "market": {"type": "integer", "minimum": 0, "maximum": 15},
                    "traction_freshness": {"type": "integer", "minimum": 0, "maximum": 15},
                    "why_now": {"type": "integer", "minimum": 0, "maximum": 10},
                    "defensibility": {"type": "integer", "minimum": 0, "maximum": 10},
                    "risk_adjustment": {"type": "integer", "minimum": 0, "maximum": 10},
                    "total": {"type": "integer", "minimum": 0, "maximum": 100},
                    "rationale_by_component": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {component: {"type": "string"} for component in SCORE_COMPONENTS},
                        "required": list(SCORE_COMPONENTS),
                    },
                },
                "required": [*SCORE_COMPONENTS, "total", "rationale_by_component"],
            },
            "recommendation": {"type": "string", "enum": ["Pass", "Watch", "Take a meeting"]},
            "recommendation_rationale": {"type": "string"},
            "why_we_care": {"type": "string"},
            "what_would_change_mind": {"type": "array", "items": {"type": "string"}},
            "cited_claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "claim": {"type": "string"},
                        "evidence_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["claim", "evidence_ids"],
                },
            },
            "analysis_mode": {"type": "string", "enum": ["openai", "deterministic_fallback"]},
        },
        "required": [
            "candidate_id",
            "product_summary",
            "team_assessment",
            "market_assessment",
            "why_now",
            "risks",
            "open_questions",
            "score_breakdown",
            "recommendation",
            "recommendation_rationale",
            "why_we_care",
            "what_would_change_mind",
            "cited_claims",
            "analysis_mode",
        ],
    }


def clamp(value: int, ceiling: int) -> int:
    return max(0, min(value, ceiling))


def evidence_claim(packet: EvidencePacket, evidence_id: str) -> str | None:
    for item in packet.evidence:
        if item.evidence_id == evidence_id:
            return item.claim
    return None


def shorten(value: str, max_chars: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."
