from __future__ import annotations

from investment_pipeline.models import CandidateStartup


AI_TERMS = {"ai", "agent", "agents", "automation", "automate", "copilot", "assistant", "llm", "workflow"}
SMB_TERMS = {"smb", "small", "business", "businesses", "mid-market", "startup", "teams"}
OPS_TERMS = {
    "back-office",
    "finance",
    "accounting",
    "sales",
    "support",
    "operations",
    "workflow",
    "workflows",
    "compliance",
    "hr",
    "admin",
    "documents",
}
RECENT_BATCH_PREFIXES = ("W26", "S26", "F26", "Sp26", "W25", "S25", "F25", "Sp25", "W24", "S24", "F24")


def select_candidates(candidates: list[CandidateStartup], topic: str, limit: int = 10) -> list[CandidateStartup]:
    ranked = sorted(
        ((candidate, candidate_relevance_score(candidate, topic)) for candidate in candidates),
        key=lambda item: item[1],
        reverse=True,
    )
    selected = [candidate for candidate, score in ranked if score > 0]
    return selected[:limit] if selected else [candidate for candidate, _ in ranked[:limit]]


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

    if candidate.batch and candidate.batch in RECENT_BATCH_PREFIXES:
        score += 8
    if candidate.website:
        score += 2
    if candidate.team_size and candidate.team_size <= 20:
        score += 2
    if "consumer" in haystack and "b2b" not in haystack:
        score -= 5
    if "acquired" in haystack or "inactive" in haystack:
        score -= 50
    return score
