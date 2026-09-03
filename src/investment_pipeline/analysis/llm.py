from __future__ import annotations

import json
from pathlib import Path

import httpx
from pydantic import ValidationError

from investment_pipeline.config import Settings, THESIS
from investment_pipeline.models import (
    AnalysisResult,
    CitedClaim,
    EvidencePacket,
    ScoreBreakdown,
    deterministic_total,
    recommendation_for_score,
)


async def analyze_packet(settings: Settings, packet: EvidencePacket, prompts_dir: Path) -> AnalysisResult:
    if not settings.openai_api_key:
        return deterministic_fallback_analysis(packet)

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
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post("https://api.openai.com/v1/responses", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    text = extract_response_text(data)
    parsed = json.loads(text)
    try:
        analysis = AnalysisResult.model_validate(parsed)
    except ValidationError:
        parsed["analysis_mode"] = "openai"
        parsed["score_breakdown"]["total"] = deterministic_total(parsed["score_breakdown"])
        parsed["recommendation"] = recommendation_for_score(parsed["score_breakdown"]["total"])
        analysis = AnalysisResult.model_validate(parsed)
    return analysis


def extract_response_text(data: dict) -> str:
    if data.get("output_text"):
        return data["output_text"]
    for output in data.get("output", []):
        for content in output.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]
    raise ValueError("OpenAI response did not include output text")


def deterministic_fallback_analysis(packet: EvidencePacket) -> AnalysisResult:
    candidate = packet.candidate
    ids = packet.evidence_ids
    has_web = any(item.source == "website" for item in packet.evidence)
    hn_items = [item for item in packet.evidence if item.source == "hn" and "No HN story traction" not in item.claim]
    text = " ".join(item.claim.lower() for item in packet.evidence)
    is_acquired_or_inactive = "acquired" in text or "inactive" in text
    yc_product = evidence_claim(packet, "YC2") or evidence_claim(packet, "YC1") or candidate.one_liner
    yc_meta = evidence_claim(packet, "YC3") or "YC metadata unavailable."
    yc_team_signal = evidence_claim(packet, "YC4")
    web_claim = evidence_claim(packet, "WEB1") or "Website text unavailable."
    hn_summary = (
        f"{len(hn_items)} relevant HN item(s) were found in the top filtered search results."
        if hn_items
        else "No relevant HN traction was found in the top filtered search results."
    )

    team = 6
    if candidate.team_size and candidate.team_size <= 10:
        team += 2
    if candidate.batch:
        team += 2
    if yc_team_signal:
        team += 5

    product = 8
    if "ai" in text or "agent" in text or "automate" in text:
        product += 5
    if "workflow" in text or "operation" in text or "back-office" in text:
        product += 3
    if has_web:
        product += 2

    market = 6
    if "business" in text or "b2b" in text or "smb" in text or "companies" in text:
        market += 4
    if "finance" in text or "sales" in text or "support" in text or "compliance" in text:
        market += 3

    traction = 4 + min(6, len(hn_items) * 2)
    if candidate.batch:
        traction += 3
    if has_web:
        traction += 2

    why_now = 4 + (4 if ("ai" in text or "agent" in text or "llm" in text) else 0)
    defensibility = 4 + (2 if "integrat" in text or "workflow" in text else 0)
    risk_adjustment = 4 + (2 if has_web else 0) + (1 if hn_items else 0)
    if is_acquired_or_inactive:
        traction = min(traction, 6)
        risk_adjustment = 0

    components = {
        "team": min(team, 20),
        "product": min(product, 20),
        "market": min(market, 15),
        "traction_freshness": min(traction, 15),
        "why_now": min(why_now, 10),
        "defensibility": min(defensibility, 10),
        "risk_adjustment": min(risk_adjustment, 10),
    }
    total = deterministic_total(components)
    recommendation = recommendation_for_score(total)
    if is_acquired_or_inactive and total >= 55:
        recommendation = "Pass"
    yc_product_ids = [evidence_id for evidence_id in ("YC1", "YC2") if evidence_id in ids]
    yc_meta_ids = [evidence_id for evidence_id in ("YC3",) if evidence_id in ids]
    yc_team_ids = [evidence_id for evidence_id in ("YC4",) if evidence_id in ids]
    web_ids = ["WEB1"] if "WEB1" in ids else []
    hn_ids = [evidence_id for evidence_id in sorted(ids) if evidence_id.startswith("HN")][:2]
    team_evidence_note = (
        f"YC description adds team signal: {shorten(yc_team_signal, 260)} [{', '.join(yc_team_ids)}]"
        if yc_team_signal and yc_team_ids
        else "Founder-background details are insufficient in the collected evidence."
    )

    return AnalysisResult(
        candidate_id=candidate.id,
        product_summary=(
            f"{candidate.name} is described as '{candidate.one_liner}'. "
            f"The strongest product evidence says: {shorten(yc_product, 320)} [{', '.join(yc_product_ids or ['YC1'])}]"
        ),
        team_assessment=(
            f"YC metadata lists the company as {candidate.status or 'status unknown'} / "
            f"{candidate.stage or 'stage unknown'} with team size "
            f"{candidate.team_size if candidate.team_size is not None else 'Unknown'}. "
            f"{team_evidence_note} [{', '.join(yc_meta_ids or ['YC3'])}]"
        ),
        market_assessment=(
            f"The market read is based on the described workflow and buyer context: {shorten(yc_product, 260)} "
            f"Website text adds: {shorten(web_claim, 220)} Precise market size still needs outside research. [YC2, WEB1]"
        ),
        why_now=(
            "The why-now case is strongest where the evidence shows AI agents moving from advice into operational execution. "
            f"Current freshness/traction signal: {hn_summary} [HN1]"
        ),
        risks=[
            "Founder backgrounds and customer traction are not deeply verified from the available public evidence.",
            "HN traction may be absent or noisy for B2B companies.",
            "The product could be a thin AI interface unless workflow depth is confirmed.",
            "If the company is acquired or inactive, it is outside the seed-stage sourcing target.",
        ],
        open_questions=[
            "Who is the budget owner and how urgent is the workflow pain?",
            "What evidence exists for repeat usage, retention, or paid customers?",
            "What proprietary data, integrations, or workflow lock-in create defensibility?",
        ],
        score_breakdown=ScoreBreakdown(
            **components,
            total=total,
            rationale_by_component={
                "team": "YC metadata provides limited team signal; founder-background evidence is mostly missing.",
                "product": "Product score reflects explicit AI/workflow language and website support where available.",
                "market": "Market score reflects B2B/SMB/workflow hints, not a full market-sizing exercise.",
                "traction_freshness": "Freshness comes from YC batch metadata and any HN stories found.",
                "why_now": "Higher where AI/agent/LLM language appears in evidence.",
                "defensibility": "Conservative unless workflow depth or integrations are visible.",
                "risk_adjustment": "Rewards accessible evidence and penalizes missing traction/founder data.",
            },
        ),
        recommendation=recommendation,
        recommendation_rationale=(
            f"{recommendation} based on a deterministic evidence-only fallback because OPENAI_API_KEY was not set. "
            f"The decision leans on YC/company-site evidence and treats HN as a weak freshness signal. Metadata: {yc_meta}"
        ),
        why_we_care=(
            f"It maps to the thesis if the product owns a repeated operating workflow rather than a thin assistant layer. "
            f"The available evidence points to: {shorten(candidate.one_liner, 120)} [YC1]"
        ),
        what_would_change_mind=[
            "Verified customer traction or revenue from the target buyer.",
            "Founder-background evidence showing strong domain or technical fit.",
            "Proof that the product executes an end-to-end workflow with integrations or proprietary data.",
        ],
        cited_claims=[
            CitedClaim(claim="Company product description comes from YC metadata.", evidence_ids=yc_product_ids or ["YC1"]),
            CitedClaim(claim="YC metadata provides company stage and team-size context.", evidence_ids=yc_meta_ids or ["YC3"]),
            CitedClaim(claim="Founder or team background signal was extracted when available.", evidence_ids=yc_team_ids or yc_meta_ids or ["YC3"]),
            CitedClaim(claim="Website evidence availability was recorded during enrichment.", evidence_ids=web_ids or ["WEB1"]),
            CitedClaim(claim="HN traction/freshness evidence was recorded during enrichment.", evidence_ids=hn_ids or ["HN1"]),
        ],
        analysis_mode="deterministic_fallback",
    )


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
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": [
                    "team",
                    "product",
                    "market",
                    "traction_freshness",
                    "why_now",
                    "defensibility",
                    "risk_adjustment",
                    "total",
                    "rationale_by_component",
                ],
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
