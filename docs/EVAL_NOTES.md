# Eval notes

Evaluation is deliberately light: schema checks, arithmetic checks, citation
checks, and a manual read of a few memos per run.

## Automated (`uv run pytest`, 23 tests)

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

The committed run is a real Gemini run (`analysis_mode: gemini`). Checked:

- every inline `[YCn]` / `[HNn]` in a memo maps to an entry in that memo's
  Sources list, and the claim is actually supported by that source;
- risks and open questions read differently per company and name real
  domain concerns (e.g. "full carrier vs MGA backed by a reinsurer" for Mount);
- recommendations match the score thresholds, with the documented Watch
  downgrade where product/buyer/traction evidence is thin;
- missing data ("no HN discussion", "market size not estimated") shows up as an
  open question, not a fabricated fact;
- `validation_report.json` is `{"issues": []}`.

## Note

The pipeline post-processes whatever the model returns — component scores are
re-clamped, the total is recomputed, the recommendation is re-derived from the
threshold, and any citation to an evidence ID not in the packet is dropped
before the memo is written. So a model that drifts on the schema or invents a
citation cannot move the final call. The deterministic fallback runs when no
key is set and has its own test coverage.
