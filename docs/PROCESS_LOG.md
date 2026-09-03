# Process Log

## 2026-09-03

Read the assignment and scoped the MVP as a CLI pipeline rather than a SaaS app.

Decision: YC + HN only. Product Hunt, Crunchbase, LinkedIn, and Twitter/X were rejected for v1 because they add auth, scraping fragility, or replayability risk.

Decision: LLM boundary is evidence-only. Python owns fetching, artifact storage, score totals, recommendation thresholds, and citation validation.

Implementation constraint discovered: `OPENAI_API_KEY` was not set locally. Added a deterministic fallback analysis mode so the sample run can still be generated honestly without fabricating LLM usage.

Quality concern: deterministic fallback cannot replace true analyst reasoning. It is acceptable for replayability but should be called out as a limitation if the sample run is produced without an API key.

Found during inspection: initial HN enrichment produced false positives for company names like StackAI, Mount, and Cotool. Fixed by filtering HN hits against the submitted URL/domain or exact company name, and by adding regression tests for generic/compacted-name false positives.

Handoff pass: inspected the existing repo, verified tests and CLI execution, found a remaining HN substring false positive for `Fiber AI` vs. "carbon-fiber airfoil", fixed matching with token-boundary phrase checks and URL-domain checks, and added regression tests.

Handoff pass: added `YC4` team evidence extraction from YC descriptions when founder/team-background phrases are present. Narrowed the heuristic after it initially over-matched generic product/team wording.

Handoff pass: added a recommendation override so `Take a meeting` requires enough product, buyer, and traction support in the evidence packet. The score can remain high, but weak/unverifiable evidence downgrades the call to `Watch`.

Final sample run used for submission artifacts: `data/runs/20260903T155128Z_ai-agents-for-smb-back-office-workflows/`.
