# ai usage

built this with AI the whole way. writing down what actually happened so you don't have to guess from the diff.

## planning

put the assignment into an LLM first and argued about scope — what to cut, which sources, where the model sits vs where plain python sits. what came out:

- one primary source (YC), one enrichment source (HN). not six half-working scrapers.
- the model never browses. it gets a frozen evidence packet with ids (`YC1`, `WEB1`, `HN1`) and may only cite those.
- python owns the fetch, the score sum, the pass/watch/meeting cutoff, the citation check. the model proposes component scores, nothing else.

thesis and the seven weights are mine.

## first cut — Codex

Codex wrote the first working version end to end from that plan: models, YC + HN adapters, website scrape, evidence builder, the OpenAI call + the offline fallback, scoring, memo rendering, 15 tests, first sample run. roughly all of `src/` and `tests/` in one sitting, one commit (`46905a7`).

what i told it while it worked: CLI only, YC primary / HN for freshness, persist every intermediate file, deterministic score totals, don't invent a git history.

## review + finish — Claude Code

used Claude Code to read the repo cold, find what was wrong, fix each thing as its own commit:

- `df374d9` — batch-recency filter was dead code. it matched `"W25"` but YC returns `"Winter 2025"`, so recency never applied and an old Winter-2023 company with 18 people ranked first against a seed thesis.
- `884d7b6` — every memo had the same three risks / three questions. rewrote it to read the packet per company. also the OpenAI schema would have 400'd on the first real call — `rationale_by_component` was an open map and strict mode rejects that.
- `d8560cc` — offline scorer handed "take a meeting" to five of twelve. tightened it so the call needs verifiable traction (a real Launch HN thread or a quantified revenue/customer claim), not soft words.
- `f055ed2` — selection + fallback tests, a threshold guardrail in `validate_analysis`, docs rewritten against the commits.

Claude Code also flipped the repo to private and added the collaborator.

## what the model did not decide

- the thesis and the scoring weights.
- that "take a meeting" needs product + buyer + hard traction, not just a high number.
- which findings were real bugs worth a commit vs cosmetic.
- shipping the sample in fallback mode with that stated plainly instead of waiting on a funded key.

## model

first tried OpenAI — the key i had was out of credits (`insufficient_quota`). switched the analysis layer to be provider-agnostic and pointed it at Gemini. `gemini-3.6-flash` turned out to be 20 requests/day on the free tier and the day's testing had burned it, so the committed sample runs on `gemini-3.1-flash-lite`. both paths (and the model swap) send the same prompt and schema and get re-clamped and re-thresholded by python afterward, so the guarantees don't move. the committed sample is a real Gemini run — `analysis_mode: gemini` in the manifest and every memo.

if no key is set at all it still runs, on the rule-based fallback, labelled everywhere.

prompts are in `prompts/` — the exact text sent to the model, not a summary.
