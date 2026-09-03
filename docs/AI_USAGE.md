# AI Usage

Codex assisted with implementation during the September 3, 2026 build session.

AI was used for:

- Turning the agreed architecture into a minimal Python CLI project.
- Drafting Pydantic models, source adapters, validation logic, memo rendering, tests, and docs.
- Making tradeoffs explicit, especially around source scope and replayability.

Human direction supplied:

- Keep the project small and CLI-only.
- Use YC as the primary source and HN as traction/freshness enrichment.
- Avoid frontend, database, queue, vector DB, auth, and agent frameworks.
- Persist intermediate artifacts.
- Make AI workflow visible honestly.

Important implementation note:

- `OPENAI_API_KEY` was not present in the local shell during implementation, so the code includes a deterministic fallback analysis path. This is not presented as LLM output. It is clearly marked in generated memos and manifests. With `OPENAI_API_KEY` set, the pipeline calls OpenAI's Responses API with a structured JSON schema.
- During the handoff pass, Codex was used to inspect the existing work, run tests and CLI samples, identify HN evidence pollution, improve team-signal extraction, add a conservative recommendation override, regenerate the final sample run, and update documentation. These notes reflect actual actions in the repo, not a fabricated development history.
