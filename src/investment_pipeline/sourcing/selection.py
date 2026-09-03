from __future__ import annotations

import re

from investment_pipeline.models import CandidateStartup

AI_TERMS = {"ai", "agent", "agents", "automation", "automate", "copilot", "assistant", "llm", "workflow"}
SMB_TERMS = {"smb", "small", "business", "businesses", "mid-market", "startup", "teams"}
OPS_TERMS = {
    "back-office",
    "back office",
    "finance",
    "accounting",
    "bookkeeping",
    "sales",
    "support",
    "operations",
    "workflow",
    "workflows",
    "compliance",
    "hr",
    "payroll",
    "admin",
    "invoicing",
    "procurement",
    "documents",
}
CONSUMER_TERMS = {"consumer", "for individuals", "everyday people", "personal finance for", "dating", "gaming"}
CURRENT_YEAR = 2026


def select_candidates(candidates: list[CandidateStartup], topic: str, limit: int = 10) -> list[CandidateStartup]:
    ranked = sorted(
        ((candidate, candidate_relevance_score(candidate, topic)) for candidate in candidates),
        key=lambda item: item[1],
        reverse=True,
    )
    positive = [candidate for candidate, score in ranked if score > 0]
    chosen = positive[:limit] if positive else [candidate for candidate, _ in ranked[:limit]]
    return chosen


def candidate_relevance_score(candidate: CandidateStartup, topic: str) -> int:
    haystack = " ".join(
        [
            candidate.name,
            candidate.one_liner,
            candidate.description or "",
            candidate.industry or "",
            candidate.status or "",
            candidate.stage or "",
            " ".join(candidate.tags),
        ]
    ).lower()
    topic_terms = {token for token in topic.lower().replace("/", " ").replace("-", " ").split() if len(token) > 2}

    score = 0
    score += 4 * sum(1 for term in topic_terms if term in haystack)
    score += 6 * sum(1 for term in AI_TERMS if term in haystack)
    score += 4 * sum(1 for term in SMB_TERMS if term in haystack)
    score += 3 * sum(1 for term in OPS_TERMS if term in haystack)
    score += batch_recency_score(candidate.batch)

    if candidate.website:
        score += 2
    if candidate.team_size is not None and candidate.team_size <= 20:
        score += 3
    if candidate.team_size is not None and candidate.team_size > 60:
        score -= 6
    if (candidate.stage or "").lower() == "growth":
        score -= 8
    if (candidate.status or "").lower() in {"acquired", "inactive", "public"}:
        score -= 60
    if any(term in haystack for term in CONSUMER_TERMS) and "b2b" not in haystack:
        score -= 6
    return score


def batch_recency_score(batch: str | None) -> int:
    if not batch:
        return 0
    match = re.search(r"(?:19|20)\d{2}", batch)
    if not match:
        return 0
    delta = CURRENT_YEAR - int(match.group())
    if delta <= 0:
        return 12
    if delta == 1:
        return 8
    if delta == 2:
        return 3
    if delta >= 5:
        return -8
    return 0
