# Decisions

## CLI Instead Of Frontend

The assignment asks for a replayable pipeline and partner-skimmable memos. A frontend would consume time without improving the core evaluation criteria.

## Files Instead Of Database

Intermediate JSON and Markdown files are easier for reviewers to inspect than a local database. They also make reruns and debugging straightforward.

## YC As Primary Source

YC company data provides structured startup records: name, website, one-liner, description, batch, industry, tags, and team size where available.

## HN As Traction/Freshness Source

HN Algolia is public and no-key. It is noisy, but useful for public launch/discussion signals.

## Deterministic Score Total

The LLM may assign component scores, but Python recomputes the total and recommendation. This avoids hidden policy drift in the final call.

## Citation IDs

Every evidence item receives a stable ID such as `YC1`, `WEB1`, or `HN1`. Analysis must cite these IDs so memo claims can be traced back to stored evidence.

