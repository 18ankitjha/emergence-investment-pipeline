from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from investment_pipeline.config import Settings
from investment_pipeline.models import CandidateStartup, SourceRef
from investment_pipeline.storage import slugify, write_json


async def fetch_yc_companies(settings: Settings, raw_dir: Path) -> list[dict[str, Any]]:
    raw_path = raw_dir / "yc_fetch_manifest.json"
    async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": settings.user_agent}) as client:
        response = await client.get(settings.yc_api_url)
        response.raise_for_status()
        companies = response.json()
    write_json(
        raw_path,
        {
            "source_url": settings.yc_api_url,
            "record_count": len(companies),
            "note": "Full YC response was fetched for deterministic filtering but not committed to avoid repository noise.",
        },
    )
    return companies


def normalize_yc_company(raw: dict[str, Any], raw_source_path: str | None = None) -> CandidateStartup | None:
    name = (raw.get("name") or "").strip()
    one_liner = (raw.get("one_liner") or raw.get("oneLiner") or "").strip()
    if not name or not one_liner:
        return None

    yc_url = raw.get("url") or f"https://www.ycombinator.com/companies/{raw.get('slug', slugify(name))}"
    industries = raw.get("industries") or []
    industry = raw.get("industry") or (industries[0] if industries else None)

    return CandidateStartup(
        id=f"yc-{raw.get('id') or slugify(name)}",
        name=name,
        website=raw.get("website") or None,
        one_liner=one_liner,
        description=raw.get("long_description") or raw.get("description") or None,
        batch=raw.get("batch") or None,
        industry=industry,
        status=raw.get("status") or None,
        stage=raw.get("stage") or None,
        tags=[str(tag) for tag in raw.get("tags") or []],
        team_size=raw.get("team_size") if isinstance(raw.get("team_size"), int) else None,
        source_refs=[
            SourceRef(
                id="YC_SOURCE",
                source_type="yc",
                title=f"YC profile for {name}",
                url=yc_url,
                raw_path=raw_source_path,
            )
        ],
        raw_source_path=raw_source_path,
    )
