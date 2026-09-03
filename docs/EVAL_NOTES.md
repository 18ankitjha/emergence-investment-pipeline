# Eval notes

Evaluation is deliberately light: schema checks, arithmetic checks, citation
checks, and a manual read of a few memos per run.

## Automated (`uv run pytest`, 21 tests)

- **Models** — required fields, evidence-ID prefix rules, score total must equal
  the component sum.
- **Selection** — batch-recency scoring, a recent seed company outranks an old
  Growth company, acquired companies are pushed out.
- **HN filtering** — generic short names need a domain hit; compacted-word and
  multi-word substring false positives are rejected; subdomain URLs match.
- **Offline analysis** — every cited ID exists in the packet; risks differ
  between a regulated company and a generic one; a missing website is flagged.
- **Scoring** — recommendation is thresholded from the deterministic total; a
  high score with a weak evidence packet is downgraded to Watch.
- **Citation validation** — unknown IDs and empty citation lists are errors.
- **Memo rendering** — template renders with citations and score table.

## Per-run validation (`validation_report.json`)

Written for every run. Flags, per candidate:

- cited evidence IDs that are not in the packet, or claims with no citation;
- a score total that does not match its components;
- a recommendation more bullish than the score allows;
- a "Take a meeting" resting on four or fewer evidence items.

A clean run has `"issues": []`.

## Manual check on the committed sample

- Opened `memos/cotool.md`, `memos/definite.md`, `memos/mount.md`,
  `memos/corvera.md`.
- Every inline `[YCn]` / `[HNn]` maps to an entry in the Sources list.
- Risks and Open Questions read differently per company.
- Recommendations match the score thresholds (with the documented Watch
  downgrade where evidence is thin).
- Missing data ("no HN discussion", "market size not estimated") shows up as an
  open question, not a made-up fact.

## Caveat

The committed sample runs the deterministic fallback (no funded API key this
session), so it exercises the rule-based analyser, not the model. The OpenAI
path has unit-level schema coverage but no end-to-end run in the repo.
