# Eval Notes

Evaluation is intentionally lightweight.

Automated checks:

- Pydantic validates model shape and score ranges.
- Score totals must equal component sums.
- Recommendations are thresholded from deterministic totals.
- Citation validation checks that cited evidence IDs exist.
- Memo rendering is covered by a focused test.
- HN relevance tests cover generic names, compacted-word false positives, multi-word substring false positives, and domain/subdomain matches.
- Recommendation override tests cover high-score analyses with weak evidence packets.

Manual check to perform after the sample run:

- Open one memo and verify it is skimmable in about 60 seconds.
- Confirm all cited claim IDs exist in the matching evidence packet.
- Confirm the recommendation matches the score threshold.
- Confirm missing data appears as an open question rather than a fabricated fact.

Manual check performed on the final sample:

- Opened `memos/cotool.md`, `memos/fiber-ai.md`, `memos/mount.md`, and `memos/lumari.md`.
- Confirmed inline citations map to stored evidence IDs.
- Confirmed HN evidence includes submitted URLs when HN hits are used.
- Confirmed the `Fiber AI` memo no longer treats an unrelated carbon-fiber story as traction.
- Confirmed generated candidate raw paths are relative to the run directory.
- Confirmed `validation_report.json` has no errors.
- Confirmed recommendations match deterministic score thresholds.

Remaining caveat: because no OpenAI key was available locally, the sample evaluates the deterministic fallback path. The OpenAI path is implemented but not exercised in the committed sample.
