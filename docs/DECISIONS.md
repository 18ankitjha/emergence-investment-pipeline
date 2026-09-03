# Decisions

## CLI and flat files, no services

The brief rewards a replayable pipeline and skimmable memos. A frontend or a
database buys nothing against that and costs time. Each run writes JSON and
Markdown under `data/runs/<run_id>/`, which a reviewer can open directly and
diff between runs.

## One source deep: YC primary, HN for freshness

YC's public company export gives structured records (name, site, one-liner,
long description, batch, industry, tags, team size, status, stage). That is
enough to build a candidate and most of an evidence packet without scraping.
HN Algolia is keyless and public; it is the freshness/traction signal. We
rejected Product Hunt, Crunchbase, LinkedIn, and Twitter/X — each adds auth or
scraping fragility, and the anti-pattern list calls out shallow multi-source
sourcing explicitly.

## LLM boundary: evidence in, structured JSON out

The model never browses. It receives a frozen evidence packet with stable IDs
(`YC1`, `WEB1`, `HN1`, ...) and must attach evidence IDs to every claim.
Python does the fetching, the score total, the recommendation threshold, and
the citation validation. This keeps the final call auditable and stops prompt
changes from silently moving the bar.

## Provider is swappable; the contract is not

`analysis/llm.py` has a Gemini path and an OpenAI path behind one dispatch.
Both send the same rendered prompt and the same schema (the OpenAI strict
schema, transformed for Gemini's `responseSchema` dialect), and both funnel
through `finalize_llm_analysis`, which re-clamps scores, recomputes the total,
re-derives the recommendation, and strips unknown citations. Swapping models
cannot change what the pipeline guarantees. Gemini is the default because its
free tier needs no card.

## Deterministic total and threshold

The model proposes component scores. `models.deterministic_total` recomputes
the sum and `recommendation_for_score` picks Pass/Watch/Take a meeting from
fixed cutoffs. The model's own `total` and `recommendation` fields are
overwritten.

## "Take a meeting" needs evidence, not just a number

`scoring.has_take_meeting_evidence` requires the packet to show a product
(YC1 + YC2/website), a named buyer type, and a traction signal. A 78 with a
dead website and no traction is downgraded to Watch. This is the brief's
explicit override.

## Recency is part of the thesis

The thesis says seed-stage. `selection.batch_recency_score` scores companies by
how recent their YC batch is and penalises Growth stage and large teams, so
sourcing holds the thesis rather than leaving it to the memo.

## Offline analyser is rule-based, and says so

When there is no key, `deterministic_fallback_analysis` scores from keyword and
metadata signals and writes per-company risks from the packet. It is labelled
`deterministic_fallback` in every memo and the manifest. It is a floor for
replayability, not a stand-in for the model.
