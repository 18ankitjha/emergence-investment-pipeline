from __future__ import annotations

import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from investment_pipeline.config import Settings
from investment_pipeline.models import CandidateStartup
from investment_pipeline.storage import slugify, write_text


async def fetch_website_text(settings: Settings, candidate: CandidateStartup, raw_dir: Path) -> tuple[str | None, str | None]:
    if not candidate.website:
        return None, None
    url = candidate.website
    raw_path = raw_dir / f"website_{slugify(candidate.name)}.txt"
    try:
        async with httpx.AsyncClient(
            timeout=12.0,
            follow_redirects=True,
            headers={"User-Agent": settings.user_agent},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return None, None
            text = extract_main_text(response.text)
    except Exception as exc:
        write_text(raw_path, f"Website fetch failed for {url}: {exc}\n")
        return None, str(raw_path)

    if text:
        write_text(raw_path, text)
        return text, str(raw_path)
    write_text(raw_path, f"No useful text extracted from {url}\n")
    return None, str(raw_path)


def extract_main_text(html: str, max_chars: int = 4000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "svg", "footer", "nav"]):
        element.decompose()
    text = soup.get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]

