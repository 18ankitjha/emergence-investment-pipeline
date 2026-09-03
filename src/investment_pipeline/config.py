from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


THESIS = (
    "We are looking for seed-stage AI companies that automate high-frequency "
    "operational workflows for SMBs or lean mid-market teams, where the product "
    "can become a system of action rather than a thin chatbot interface."
)

SCORE_WEIGHTS = {
    "team": 20,
    "product": 20,
    "market": 15,
    "traction_freshness": 15,
    "why_now": 10,
    "defensibility": 10,
    "risk_adjustment": 10,
}


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    openai_api_key: str | None
    openai_model: str
    yc_api_url: str = "https://yc-oss.github.io/api/companies/all.json"
    hn_api_url: str = "https://hn.algolia.com/api/v1/search"
    user_agent: str = "emergence-investment-pipeline/0.1"


def load_settings() -> Settings:
    root = Path.cwd()
    env_file = load_env_file(root / ".env")
    return Settings(
        project_root=root,
        data_dir=root / "data" / "runs",
        openai_api_key=os.getenv("OPENAI_API_KEY") or env_file.get("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL") or env_file.get("OPENAI_MODEL") or "gpt-4.1-mini",
    )


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values
