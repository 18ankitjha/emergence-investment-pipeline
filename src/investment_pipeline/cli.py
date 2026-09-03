from __future__ import annotations

from pathlib import Path

import typer

from investment_pipeline.config import load_settings
from investment_pipeline.pipeline import run_pipeline_sync

app = typer.Typer(help="AI-augmented investment pipeline.")


@app.callback()
def main() -> None:
    """Run investment sourcing and memo generation commands."""


@app.command()
def run(
    topic: str = typer.Argument(..., help="Investment sourcing topic query."),
    limit: int = typer.Option(10, "--limit", "-n", min=1, max=20, help="Number of startups to analyze."),
) -> None:
    """Source startups, enrich evidence, analyze, score, and write memos."""
    settings = load_settings()
    run_dir = run_pipeline_sync(settings, topic, limit=limit)
    typer.echo(f"Run complete: {run_dir}")


if __name__ == "__main__":
    app()
