from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlparse

import httpx

from investment_pipeline.config import Settings
from investment_pipeline.models import CandidateStartup
from investment_pipeline.storage import slugify, write_json


GENERIC_ONE_WORD_NAMES = {
    "mount",
    "fiber",
    "diligent",
    "basis",
    "tempo",
    "atlas",
    "linear",
    "pilot",
    "clay",
    "mint",
}


async def search_hn(settings: Settings, candidate: CandidateStartup, raw_dir: Path) -> list[dict]:
    queries = [candidate.name]
    if candidate.website:
        domain = urlparse(candidate.website).netloc.replace("www.", "")
        if domain:
            queries.append(domain)
    else:
        domain = ""

    raw_path = raw_dir / f"hn_{slugify(candidate.name)}.json"
    payloads = []
    hits_by_id: dict[str, dict] = {}
    try:
        async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": settings.user_agent}) as client:
            for query in queries:
                params = {
                    "query": query,
                    "tags": "story",
                    "hitsPerPage": "8",
                }
                response = await client.get(settings.hn_api_url, params=params)
                response.raise_for_status()
                payload = response.json()
                payloads.append({"query": query, "payload": payload})
                for hit in payload.get("hits", []):
                    if is_relevant_hn_hit(candidate, domain, hit):
                        hits_by_id[str(hit.get("objectID") or hit.get("url") or hit.get("title"))] = hit
    except Exception as exc:
        payloads.append({"error": str(exc), "hits": []})

    write_json(raw_path, {"queries": payloads, "filtered_hits": list(hits_by_id.values())})
    return list(hits_by_id.values())[:5]


def is_relevant_hn_hit(candidate: CandidateStartup, domain: str, hit: dict) -> bool:
    haystack = " ".join(
        str(hit.get(field) or "")
        for field in ("title", "story_title", "url", "story_url", "story_text")
    ).lower()
    name = candidate.name.lower()
    if domain and hit_matches_domain(domain, hit):
        return True
    if is_generic_name(name):
        return False
    return phrase_matches(name, haystack)


def is_generic_name(name: str) -> bool:
    stripped = name.strip().lower()
    return (" " not in stripped and len(stripped) <= 5) or stripped in GENERIC_ONE_WORD_NAMES


def hit_matches_domain(domain: str, hit: dict) -> bool:
    normalized_domain = domain.strip().lower().removeprefix("www.")
    if not normalized_domain:
        return False
    for field in ("url", "story_url"):
        value = str(hit.get(field) or "").strip()
        if not value:
            continue
        netloc = urlparse(value).netloc.lower().removeprefix("www.")
        if netloc == normalized_domain or netloc.endswith(f".{normalized_domain}"):
            return True
    return False


def phrase_matches(phrase: str, text: str) -> bool:
    tokens = re.findall(r"[a-z0-9]+", phrase.lower())
    if not tokens:
        return False
    pattern = r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(re.escape(token) for token in tokens) + r"(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None
