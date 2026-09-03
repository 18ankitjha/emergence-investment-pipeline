# Failures and tradeoffs

## Bugs that shipped in the first commit and were fixed later

- **Batch-recency filter was dead code.** `selection.py` matched `"W25"` against
  YC batches named `"Winter 2025"`. Nothing matched, so recency never affected
  ranking and a Winter 2023 company led the list. Fixed in df374d9.
- **Every memo had the same risks.** The offline analyser returned a fixed list
  of three risks and three open questions for all companies. A reviewer opening
  two memos would have seen identical text. Fixed in 884d7b6.
- **OpenAI path would have failed on first use.** `rationale_by_component` was an
  open object; OpenAI `strict: true` rejects that. It was never caught because
  no key was available to run it. Fixed in 884d7b6.

## Provider churn

Built on OpenAI first. That key came back `insufficient_quota`. Tried Gemini;
the older models are gated off "new user" keys, but `gemini-3.6-flash` on the
AI Studio free tier works. Made the analysis layer provider-agnostic (one
dispatch, one schema, one post-processing path) rather than hard-swapping, so
the OpenAI path stays. Committed sample is now a real Gemini run.

## Constraints not solved

- **Run time.** A `--limit 12` Gemini run takes a few minutes even with four
  candidates in flight at once — the model reasons for ~1–2k tokens per call.
  Fine for a batch job whose output is committed; not interactive.
- **HN is thin for B2B.** Most seed B2B startups have no Hacker News thread.
  Absence is reported as "no traction found", not scored as a negative.
- **HN name collisions.** Early runs matched "Mount" and "Fiber AI" to unrelated
  stories. Matching now requires a domain hit or a token-boundary name match;
  we accept missing HN evidence over wrong HN evidence.
- **Website scrape is shallow.** One page, 4k characters, no JS rendering.
  JS-only sites yield weak text; the memo then leans on the YC blurb and says so.
- **No founder verification.** Founder signal is whatever the YC description
  states. No LinkedIn or Crunchbase lookup — it would add fragility and an
  auth dependency for little gain at this scope.
- **No market sizing.** The analyser will not invent a TAM. Market size is left
  as an open question in every memo.

## Things left for the owner

- Send the `hari@emsoft.com` collaborator invite from the GitHub web UI
  (`chiragmakkar` is already added).
- Record the walkthrough video.
