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
    llm_provider: str
    openai_api_key: str | None
    openai_model: str
    gemini_api_key: str | None
    gemini_model: str
    yc_api_url: str = "https://yc-oss.github.io/api/companies/all.json"
    hn_api_url: str = "https://hn.algolia.com/api/v1/search"
    user_agent: str = "emergence-investment-pipeline/0.1"


def load_settings() -> Settings:
    root = Path.cwd()
    env_file = load_env_file(root / ".env")

    def value(key: str) -> str | None:
        return os.getenv(key) or env_file.get(key) or None

    openai_key = value("OPENAI_API_KEY")
    gemini_key = value("GEMINI_API_KEY")

    return Settings(
        project_root=root,
        data_dir=root / "data" / "runs",
        llm_provider=resolve_provider(value("LLM_PROVIDER"), openai_key, gemini_key),
        openai_api_key=openai_key,
        openai_model=value("OPENAI_MODEL") or "gpt-4.1-mini",
        gemini_api_key=gemini_key,
        gemini_model=value("GEMINI_MODEL") or "gemini-3.1-flash-lite",
    )


def resolve_provider(requested: str | None, openai_key: str | None, gemini_key: str | None) -> str:
    choice = (requested or "").strip().lower()
    if choice in {"gemini", "openai"}:
        return choice
    if gemini_key:
        return "gemini"
    if openai_key:
        return "openai"
    return "none"


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw = line.split("=", 1)
        key = key.strip()
        value = raw.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values
