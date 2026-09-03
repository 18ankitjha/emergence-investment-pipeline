from __future__ import annotations

import re
from urllib.parse import urlparse

from investment_pipeline.models import CandidateStartup, EvidenceItem, EvidencePacket

TEAM_SIGNAL_PATTERNS = (
    r"\bfounded by\b",
    r"\bfounder\b",
    r"\bco-?founder\b",
    r"\bpreviously\b",
    r"\bex-[a-z0-9]",
    r"\bengineers? from\b",
    r"\boperators? from\b",
    r"\bbuilt\b.*\bat\b",
    r"\bscaled\b.*\bat\b",
    r"\bfrom (google|tesla|amazon|stripe|salesforce|doordash|airwallex|nerdwallet)\b",
)


def build_evidence_packet(
    candidate: CandidateStartup,
    website_text: str | None,
    hn_hits: list[dict],
) -> EvidencePacket:
    evidence: list[EvidenceItem] = []
    yc_url = candidate.source_refs[0].url if candidate.source_refs else "https://www.ycombinator.com/companies"

    evidence.append(
        EvidenceItem(
            evidence_id="YC1",
            candidate_id=candidate.id,
            source="yc",
            url=yc_url,
            claim=f"{candidate.name}: {candidate.one_liner}",
            category="product",
            confidence="high",
        )
    )
    if candidate.description:
        evidence.append(
            EvidenceItem(
                evidence_id="YC2",
                candidate_id=candidate.id,
                source="yc",
                url=yc_url,
                claim=clean_claim(candidate.description, 700),
                category="product",
                confidence="high",
            )
        )
    if candidate.batch or candidate.industry or candidate.tags or candidate.team_size is not None:
        parts = []
        if candidate.batch:
            parts.append(f"YC batch: {candidate.batch}")
        if candidate.industry:
            parts.append(f"Industry: {candidate.industry}")
        if candidate.status:
            parts.append(f"Status: {candidate.status}")
        if candidate.stage:
            parts.append(f"Stage: {candidate.stage}")
        if candidate.team_size is not None:
            parts.append(f"Team size: {candidate.team_size}")
        if candidate.tags:
            parts.append(f"Tags: {', '.join(candidate.tags[:8])}")
        evidence.append(
            EvidenceItem(
                evidence_id="YC3",
                candidate_id=candidate.id,
                source="yc",
                url=yc_url,
                claim="; ".join(parts),
                category="source",
                confidence="high",
            )
        )
    team_signal = extract_team_signal(candidate.description or "")
    if team_signal:
        evidence.append(
            EvidenceItem(
                evidence_id="YC4",
                candidate_id=candidate.id,
                source="yc",
                url=yc_url,
                claim=team_signal,
                category="team",
                confidence="high",
            )
        )

    if website_text:
        evidence.append(
            EvidenceItem(
                evidence_id="WEB1",
                candidate_id=candidate.id,
                source="website",
                url=candidate.website or "",
                claim=clean_claim(website_text, 1000),
                category="website",
                confidence="medium",
            )
        )
    else:
        evidence.append(
            EvidenceItem(
                evidence_id="WEB1",
                candidate_id=candidate.id,
                source="pipeline",
                url=candidate.website or yc_url,
                claim="Company website text was unavailable or inaccessible during this run.",
                category="risk",
                confidence="high",
            )
        )

    hn_evidence_id = 1
    for hit in hn_hits[:5]:
        title = hit.get("title") or hit.get("story_title")
        if not title:
            continue
        points = hit.get("points") or 0
        comments = hit.get("num_comments") or 0
        created_at = hit.get("created_at") or "unknown date"
        object_id = hit.get("objectID")
        submitted_url = hit.get("url") or hit.get("story_url") or ""
        url = f"https://news.ycombinator.com/item?id={object_id}" if object_id else hit.get("url") or ""
        submitted_note = f" Submitted URL: {submitted_url}." if submitted_url else ""
        evidence.append(
            EvidenceItem(
                evidence_id=f"HN{hn_evidence_id}",
                candidate_id=candidate.id,
                source="hn",
                url=url,
                claim=(
                    f"HN story '{title}' had {points} points and {comments} comments as of source fetch; "
                    f"created_at={created_at}.{submitted_note}"
                ),
                category="traction" if points or comments else "freshness",
                confidence="medium",
            )
        )
        hn_evidence_id += 1

    if hn_evidence_id == 1:
        domain = urlparse(candidate.website or "").netloc.replace("www.", "")
        evidence.append(
            EvidenceItem(
                evidence_id="HN1",
                candidate_id=candidate.id,
                source="hn",
                url="https://hn.algolia.com/",
                claim=f"No HN story traction found for '{candidate.name}' or '{domain}' in the top search results.",
                category="traction",
                confidence="medium",
            )
        )
    return EvidencePacket(candidate=candidate, evidence=evidence)


def clean_claim(text: str, max_chars: int) -> str:
    normalized = " ".join(text.split())
    return normalized[:max_chars].rstrip()


def extract_team_signal(description: str, max_chars: int = 700) -> str | None:
    if not description:
        return None
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(description.split()))
    matches = [
        sentence
        for sentence in sentences
        if any(re.search(pattern, sentence.lower()) for pattern in TEAM_SIGNAL_PATTERNS)
    ]
    if not matches:
        return None
    return clean_claim(" ".join(matches[:3]), max_chars)
