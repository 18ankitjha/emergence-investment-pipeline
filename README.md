# Emergence AI-Augmented Investment Pipeline

CLI pipeline for the Emergence take-home assignment:

```text
topic query -> YC sourcing -> website + HN enrichment -> evidence packets -> structured analysis -> Markdown memos
```

The project is intentionally small: no frontend, database, queue, vector DB, auth, or agent framework.

## Setup

Requires Python 3.12+ and `uv`.

```bash
uv sync --extra dev
```

Optional OpenAI analysis:

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY
```

If `OPENAI_API_KEY` is absent, the pipeline still runs using a clearly marked deterministic fallback so artifacts remain inspectable and replayable.

## Run

```bash
uv run invest-pipeline run "AI agents for SMB back-office workflows"
```

Optional limit:

```bash
uv run invest-pipeline run "AI agents for SMB back-office workflows" --limit 10
```

Each run writes:

```text
data/runs/<run_id>/
  run_manifest.json
  raw/
  candidates.json
  evidence/
  analyses/
  analyses.json
  memos/
  rankings.md
  validation_report.json
```

A committed sample run is available at:

```text
data/runs/20260903T155128Z_ai-agents-for-smb-back-office-workflows/
```

## Test

```bash
uv run pytest
```

## Sources

- YC company API mirror: https://yc-oss.github.io/api/companies/all.json
- HN Algolia API: https://hn.algolia.com/api
- Public company websites when accessible

## Walkthrough

For a 5-minute walkthrough, open one committed sample run under `data/runs/`, then show:

1. `run_manifest.json` for topic, thesis, sources, and analysis mode.
2. `candidates.json` for normalized sourcing.
3. One `evidence/<company>.json` file for traceable evidence IDs.
4. The matching `analyses/<company>.json` file for structured scoring.
5. The matching `memos/<company>.md` file for the partner-facing output.

Note: the committed sample was generated without `OPENAI_API_KEY`, so it uses the deterministic fallback analysis mode. The OpenAI structured-analysis path is implemented and will run when the key is set.
