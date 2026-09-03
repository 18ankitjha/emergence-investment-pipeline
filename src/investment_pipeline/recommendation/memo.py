from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from investment_pipeline.models import AnalysisResult, EvidencePacket


def render_memo(packet: EvidencePacket, analysis: AnalysisResult, template_dir: Path) -> str:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(default_for_string=False, default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("memo.md.j2")
    return template.render(candidate=packet.candidate, evidence=packet.evidence, analysis=analysis)


def render_rankings(rows: list[tuple[EvidencePacket, AnalysisResult]]) -> str:
    lines = [
        "# Startup Rankings",
        "",
        "| Rank | Company | Score | Recommendation | One-liner |",
        "|---:|---|---:|---|---|",
    ]
    for index, (packet, analysis) in enumerate(
        sorted(rows, key=lambda row: row[1].score_breakdown.total, reverse=True), start=1
    ):
        one_liner = packet.candidate.one_liner.replace("|", "\\|")
        lines.append(
            f"| {index} | {packet.candidate.name} | {analysis.score_breakdown.total} | "
            f"{analysis.recommendation} | {one_liner} |"
        )
    lines.append("")
    return "\n".join(lines)

