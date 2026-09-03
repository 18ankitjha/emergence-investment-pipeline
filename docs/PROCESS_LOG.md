# Process log

Chronological, tied to commits. Times are IST, 2026-09-03.

## Design (before any code)

The pipeline shape was settled in an architecture chat with an LLM before
writing code. Input was the assignment brief; output was the module breakdown
now in `src/investment_pipeline/` and the thesis in `docs/THESIS.md`.

Decisions made there, with reasoning in `docs/DECISIONS.md`:

- CLI + flat JSON/Markdown files. No DB, queue, vector store, or frontend.
- One primary source (YC) + one enrichment source (HN). Go deep, not wide.
- The LLM sees a frozen evidence packet and may only cite evidence IDs.
  Python owns fetching, scoring arithmetic, thresholds, and citation checks.

## 21:23 — MVP implementation (commit 46905a7)

Built with Codex in one session: Pydantic models, YC + HN adapters, website
scrape, evidence packet builder, OpenAI Responses call + deterministic
fallback, scoring, memo/rankings rendering, 15 tests, first sample run.
Committed as a single commit. See `docs/AI_USAGE.md` for the split of work.

Known state at handoff: tests green, CLI runs end to end, one sample run
committed. `OPENAI_API_KEY` was not available, so the sample used the
deterministic fallback.

## 21:40 — Switched to Claude Code for review and finish

Full read of the repo before changing anything: every source file, the tests,
the committed sample memos and evidence packets, `git log`, repo settings.

Findings:

1. `RECENT_BATCH_PREFIXES` in `selection.py` used `"W25"`-style codes, but the
   YC API returns `"Winter 2025"`. The recency branch never fired. A Winter
   2023 company with an 18-person team (Inkeep) was ranking first against a
   seed-stage thesis.
2. Every memo's Risks and Open Questions were byte-identical — the offline
   analyser emitted fixed lists.
3. The OpenAI path would 400 on the first real call: `rationale_by_component`
   was an open-ended object, which `strict: true` json_schema forbids.
4. The repo was public. The brief asks for a private repo with two collaborators.

## 21:49 — Fix selection (commit df374d9)

Parse the year from the batch string; score by recency delta; penalise Growth
stage, acquired/inactive status, and teams over 60. Re-ran sourcing: the top 10
is now Spring 2025 – Summer 2026 companies.

## 21:55 — Fix analysis (commit 884d7b6)

`derive_risks` / `derive_open_questions` now read the evidence packet, so each
memo's risks are specific (missing website, thin HN, no founder signal, tiny
team, regulated domain, data-layer positioning, self-reported revenue). Every
generated sentence's citations are filtered to IDs actually in the packet.
OpenAI schema pinned to the seven component keys; OpenAI errors degrade to the
offline path per candidate instead of killing the run.

## Repo settings

Flipped to private. Added `chiragmakkar` as a read collaborator via the GitHub
API. `hari@emsoft.com` is an email, not a username — that invite has to be sent
from the GitHub web UI and is left for the repo owner.

## Wiring a working model

OpenAI key: `insufficient_quota`. Gemini key: the older models 404 for "new
user" keys.

- Split `analyze_packet` into a Gemini path and an OpenAI path behind
  `config.resolve_provider`; shared `render_prompts` + `finalize_llm_analysis`.
- Transformed the OpenAI strict schema into Gemini's dialect (`to_gemini_schema`
  drops `additionalProperties`, adds `propertyOrdering`).
- Raised the YC description evidence cap from 700 to 1800 chars so founder and
  traction facts are in the packet the model cites, not just the first paragraph.
- Added `asyncio` fan-out (semaphore, `PIPELINE_CONCURRENCY`, default 3) and a
  retry loop in the Gemini call that honours the API's `retryDelay`.
- `gemini-3.6-flash` turned out to be **20 requests per day** on the free tier
  (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`), and the day's testing
  had already burned it. Switched to `gemini-3.1-flash-lite`, which has real
  daily headroom. Same schema, same post-processing; the memo prose is a little
  plainer.

## LLM path

Started on the OpenAI Responses API with structured outputs. The OpenAI key
this session returned `insufficient_quota`; the Gemini key was "new user"-gated
off the older models and `gemini-3.6-flash` is 20 requests/day on the free
tier. The working combination is `gemini-3.1-flash-lite`.

`analysis/llm.py` dispatches to a Gemini path or an OpenAI path from
`config.resolve_provider`. Both render the same prompt, both use the same
schema (the OpenAI strict schema, run through `to_gemini_schema` for Gemini's
`responseSchema` dialect), and both return through `finalize_llm_analysis`,
which re-clamps every component score, recomputes the total, re-derives the
recommendation, and strips citations to unknown evidence IDs.

The committed sample is a real Gemini run — `analysis_mode: gemini` in the
manifest and a line in every memo. The offline fallback still runs when no
key is set.
