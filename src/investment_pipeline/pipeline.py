from __future__ import annotations

import asyncio
import os
from pathlib import Path

from investment_pipeline.analysis.llm import analyze_packet
from investment_pipeline.analysis.scoring import normalize_score_and_recommendation
from investment_pipeline.analysis.validation import validate_analysis
from investment_pipeline.config import THESIS, Settings
from investment_pipeline.enrichment.evidence import build_evidence_packet
from investment_pipeline.enrichment.hn import search_hn
from investment_pipeline.enrichment.website import fetch_website_text
from investment_pipeline.models import AnalysisResult, EvidencePacket, RunManifest, ValidationReport
from investment_pipeline.recommendation.memo import render_memo, render_rankings
from investment_pipeline.sourcing.selection import select_candidates
from investment_pipeline.sourcing.yc import fetch_yc_companies, normalize_yc_company
from investment_pipeline.storage import ensure_run_dirs, run_id_for_topic, slugify, write_json, write_text

DEFAULT_CONCURRENCY = 3


def candidate_concurrency() -> int:
    raw = os.getenv("PIPELINE_CONCURRENCY")
    if raw and raw.isdigit() and int(raw) > 0:
        return int(raw)
    return DEFAULT_CONCURRENCY


async def run_pipeline(settings: Settings, topic: str, limit: int = 10) -> Path:
    run_id = run_id_for_topic(topic)
    run_dir = settings.data_dir / run_id
    ensure_run_dirs(run_dir)

    raw_companies = await fetch_yc_companies(settings, run_dir / "raw")
    candidates = [
        candidate
        for candidate in (
            normalize_yc_company(raw, raw_source_path="raw/yc_fetch_manifest.json")
            for raw in raw_companies
        )
        if candidate is not None
    ]
    selected = select_candidates(candidates, topic, limit=limit)
    write_json(run_dir / "candidates.json", selected)

    prompts_dir = settings.project_root / "prompts"
    template_dir = settings.project_root / "src" / "investment_pipeline" / "recommendation" / "templates"
    semaphore = asyncio.Semaphore(candidate_concurrency())

    async def process(candidate) -> tuple[EvidencePacket, AnalysisResult, list]:
        async with semaphore:
            website_text, _ = await fetch_website_text(settings, candidate, run_dir / "raw")
            hn_hits = await search_hn(settings, candidate, run_dir / "raw")
            packet = build_evidence_packet(candidate, website_text, hn_hits)
            write_json(run_dir / "evidence" / f"{slugify(candidate.name)}.json", packet)

            analysis = await analyze_packet(settings, packet, prompts_dir)
            analysis = normalize_score_and_recommendation(analysis, packet)
            write_json(run_dir / "analyses" / f"{slugify(candidate.name)}.json", analysis)

            memo = render_memo(packet, analysis, template_dir)
            write_text(run_dir / "memos" / f"{slugify(candidate.name)}.md", memo)
            return packet, analysis, validate_analysis(packet, analysis)

    results = await asyncio.gather(*(process(candidate) for candidate in selected))

    analyses = [analysis for _, analysis, _ in results]
    rows = [(packet, analysis) for packet, analysis, _ in results]
    validation_report = ValidationReport()
    for _, _, issues in results:
        validation_report.issues.extend(issues)

    write_json(run_dir / "analyses.json", analyses)
    write_text(run_dir / "rankings.md", render_rankings(rows))
    write_json(run_dir / "validation_report.json", validation_report)
    manifest = RunManifest(
        run_id=run_id,
        topic=topic,
        thesis=THESIS,
        selected_count=len(selected),
        analysis_mode=observed_analysis_mode(analyses),
        analysis_model=configured_model(settings),
        sources=["YC companies API", "HN Algolia API", "company websites"],
        command=f'uv run invest-pipeline run "{topic}"',
    )
    write_json(run_dir / "run_manifest.json", manifest)
    return run_dir


def configured_model(settings: Settings) -> str | None:
    if settings.llm_provider == "gemini":
        return settings.gemini_model
    if settings.llm_provider == "openai":
        return settings.openai_model
    return None


def observed_analysis_mode(analyses: list[AnalysisResult]) -> str:
    modes = {analysis.analysis_mode for analysis in analyses}
    if not modes:
        return "none"
    if len(modes) == 1:
        return modes.pop()
    return "mixed"


def run_pipeline_sync(settings: Settings, topic: str, limit: int = 10) -> Path:
    return asyncio.run(run_pipeline(settings, topic, limit=limit))
