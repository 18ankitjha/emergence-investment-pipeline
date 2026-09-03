# AI usage

This project was built with AI assistance throughout. Nothing here was written
without it. This file is the honest split.

## Architecture chat (LLM, before code)

Fed the assignment brief to an LLM and iterated on scope: what to cut (DB,
queue, vector store, frontend, multi-source scraping), which sources to use,
where the LLM boundary sits. Output was the module list and the thesis.
Human calls: one primary source not six; LLM cites evidence IDs only; Python
owns the score arithmetic and the final recommendation threshold.

## Codex — implementation (commit 46905a7)

Wrote the first working version end to end from the agreed design: models,
adapters, evidence builder, analysis (OpenAI + fallback), scoring, memo
rendering, tests, first sample run. Roughly the whole `src/` tree and `tests/`
in one session.

Human direction during that session: keep it CLI-only; YC primary, HN for
freshness; persist every intermediate artifact; deterministic score totals;
don't fabricate a development history.

## Claude Code — review, fixes, docs (commits df374d9 onward)

Used to read the whole repo, find what was wrong, and fix it in separate
commits:

- Found and fixed the dead batch-recency filter (`selection.py`).
- Found and fixed identical per-company risks/questions in the offline analyser.
- Found and fixed the OpenAI strict-schema bug before it could fail on a real call.
- Rewrote these docs against what the commits actually show.
- Regenerated the committed sample run.

Claude Code also made the repo private and added the collaborator.

## What the AI did not decide

- The thesis and the seven scoring weights.
- That "Take a meeting" needs product + buyer + traction evidence, not just a
  high number (`scoring.py:has_take_meeting_evidence`).
- Which findings were real bugs worth a commit vs. cosmetic.
- That the committed sample would ship in fallback mode with that stated
  plainly rather than waiting on a funded API key.

## Prompts

The analysis prompts are in `prompts/analysis_system.md` and
`prompts/analysis_user.md` — the exact text sent to the model, not a summary.

## Honesty note for the reviewer

The reflective "how I worked" narrative and the walkthrough video are the
owner's, in their own words. This file records what happened; it is not a
substitute for that.
