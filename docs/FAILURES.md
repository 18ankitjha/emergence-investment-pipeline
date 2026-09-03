# Failures And Tradeoffs

- No OpenAI key was available in the implementation shell. The code supports OpenAI, but the sample run may use deterministic fallback if no key is supplied.
- HN traction is uneven for B2B startups. Absence of HN discussion is not strong negative evidence.
- HN search initially produced false positives for common or compacted names. The final implementation uses conservative filtering and accepts missing HN traction over polluted traction evidence.
- Website scraping is best-effort. JavaScript-heavy sites may produce weak text extraction.
- Founder-background enrichment is intentionally shallow because LinkedIn/Twitter scraping would hurt reliability and replayability.
- Market sizing is not automated. The memo treats market claims conservatively unless supported by the evidence packet.
