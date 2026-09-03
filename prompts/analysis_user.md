Thesis:
{thesis}

Analyze this startup evidence packet and return only structured JSON matching the schema.

Rules:
- Use only this evidence packet.
- Keep prose concise and partner-skimmable.
- Component scores must be within the stated max values.
- The total should be the sum of components. The pipeline will recompute it deterministically.
- Recommendation should follow: 75-100 Take a meeting, 55-74 Watch, 0-54 Pass.
- Every cited_claim evidence_id must exist in the packet.
- If founder, traction, or market evidence is missing, say so explicitly.

Evidence packet:
{evidence_packet}

