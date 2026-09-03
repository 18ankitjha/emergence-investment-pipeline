# AI-augmented investment pipeline

A CLI triage pipeline for a seed-stage VC. Give it a topic; it sources startups
from YC, builds a cited evidence packet per company, scores them against a fixed
thesis, and writes a one-page memo ending in Pass / Watch / Take a meeting.

```text
topic query
  -> YC sourcing + relevance filter
  -> website + Hacker News enrichment
  -> evidence packet (stable IDs: YC1, WEB1, HN1, ...)
  -> analysis (OpenAI structured output, or a deterministic fallback)
  -> deterministic scoring + threshold
  -> Markdown memo + rankings + validation report
```

No frontend, database, queue, or vector store. Everything a run produces is a
flat file under `data/runs/<run_id>/`.

## Thesis

> Seed-stage AI companies that automate high-frequency operational workflows for
> SMBs or lean mid-market teams, where the product can become a system of action
> rather than a thin chatbot interface.

Full version, scoring weights, and thresholds: `docs/THESIS.md`.

## Run it

Requires Python 3.12+ and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
uv run invest-pipeline run "AI agents for SMB back-office workflows"
```

`--limit N` (default 10, max 20) sets how many startups are analysed.

Analysis mode is chosen automatically:

- **`OPENAI_API_KEY` set** — each evidence packet goes to the OpenAI Responses
  API with a strict JSON schema. `cp .env.example .env` and add the key.
- **no key** — a deterministic rule-based scorer runs instead, labelled
  `deterministic_fallback` in every memo and the manifest. The pipeline still
  produces a full, inspectable run.

## What a run writes

```text
data/runs/<run_id>/
  run_manifest.json      topic, thesis, sources, analysis mode, command
  candidates.json        normalised startups after the relevance filter
  raw/                   unmodified YC manifest, HN responses, website text
  evidence/<slug>.json   the packet the analyser saw, one file per company
  analyses/<slug>.json   structured analysis + score breakdown
  memos/<slug>.md        the one-page memo
  rankings.md            all companies by score with their call
  validation_report.json citation / score / threshold checks ("issues": [] is clean)
```

## Committed sample

`data/runs/20260903T164242Z_ai-agents-for-smb-back-office-workflows/` is a full
run, committed so it does not need re-running. It was produced without an API
key, so it exercises the deterministic fallback. Start with `rankings.md`, then
open `memos/risely-ai.md` (Take a meeting) and `memos/fiber-ai.md` (Pass) and
check each `[YCn]` / `[HNn]` against that memo's Sources list.

## Tests

```bash
uv run pytest
```

## How this was built

The build used AI throughout and the trail is in the repo:

- `docs/AI_USAGE.md` — which tool did what, and what stayed a human call.
- `docs/PROCESS_LOG.md` — timeline tied to commit hashes.
- `docs/DECISIONS.md` — scoping calls and why.
- `docs/FAILURES.md` — three bugs that shipped in the first commit and were
  fixed after, plus the constraints not solved.
- `docs/EVAL_NOTES.md` — how output is checked.
- `prompts/` — the exact text sent to the model.
- `git log` — one commit per fix, with the finding in the message.

## Sources

- YC company export: `https://yc-oss.github.io/api/companies/all.json`
- HN Algolia search: `https://hn.algolia.com/api`
- Company websites (single page, best effort)
