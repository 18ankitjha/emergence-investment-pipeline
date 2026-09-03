from __future__ import annotations

import asyncio
from pathlib import Path

from investment_pipeline.analysis.llm import analyze_packet
from investment_pipeline.analysis.scoring import normalize_score_and_recommendation
from investment_pipeline.analysis.validation import validate_analysis
from investment_pipeline.config import THESIS, Settings
from investment_pipeline.enrichment.evidence import build_evidence_packet
from investment_pipeline.enrichment.hn import search_hn
from investment_pipeline.enrichment.website import fetch_website_text
from investment_pipeline.models import AnalysisResult, CandidateStartup, RunManifest, ValidationReport
from investment_pipeline.recommendation.memo import render_memo, render_rankings
from investment_pipeline.sourcing.selection import select_candidates
from investment_pipeline.sourcing.yc import fetch_yc_companies, normalize_yc_company
from investment_pipeline.storage import ensure_run_dirs, run_id_for_topic, slugify, write_json, write_text


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

    analyses: list[AnalysisResult] = []
    rows = []
    validation_report = ValidationReport()
    prompts_dir = settings.project_root / "prompts"
    template_dir = settings.project_root / "src" / "investment_pipeline" / "recommendation" / "templates"

    for candidate in selected:
        website_text, _website_raw_path = await fetch_website_text(settings, candidate, run_dir / "raw")
        hn_hits = await search_hn(settings, candidate, run_dir / "raw")
        packet = build_evidence_packet(candidate, website_text, hn_hits)
        write_json(run_dir / "evidence" / f"{slugify(candidate.name)}.json", packet)

        analysis = await analyze_packet(settings, packet, prompts_dir)
        analysis = normalize_score_and_recommendation(analysis, packet)
        issues = validate_analysis(packet, analysis)
        validation_report.issues.extend(issues)
        analyses.append(analysis)
        write_json(run_dir / "analyses" / f"{slugify(candidate.name)}.json", analysis)

        memo = render_memo(packet, analysis, template_dir)
        write_text(run_dir / "memos" / f"{slugify(candidate.name)}.md", memo)
        rows.append((packet, analysis))

    write_json(run_dir / "analyses.json", analyses)
    write_text(run_dir / "rankings.md", render_rankings(rows))
    write_json(run_dir / "validation_report.json", validation_report)
    manifest = RunManifest(
        run_id=run_id,
        topic=topic,
        thesis=THESIS,
        selected_count=len(selected),
        analysis_mode="openai" if settings.openai_api_key else "deterministic_fallback",
        sources=["YC companies API", "HN Algolia API", "company websites"],
        command=f'uv run invest-pipeline run "{topic}"',
    )
    write_json(run_dir / "run_manifest.json", manifest)
    return run_dir


def run_pipeline_sync(settings: Settings, topic: str, limit: int = 10) -> Path:
    return asyncio.run(run_pipeline(settings, topic, limit=limit))
