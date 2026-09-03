# Lua Global Inc

**Watch** · **59/100**
https://heylua.ai/ · YC Fall 2025 · B2B

## What They Do
Lua is an 'agentOS' platform designed to help mid-market companies and developer agencies build and deploy AI agents for sales, support, and operations. It provides a developer-centric interface (TypeScript/Zod) alongside a no-code 'Agent Builder' to abstract infrastructure complexity and ensure enterprise-grade reliability.

## Team
Founded by Lorcan O Cathain (CEO) and Stefan Kruger (CTO), who are described as experienced founders with 15-20 years of experience scaling technology companies in emerging markets. The team size is currently 5.

## Market
Targets mid-market enterprises ($50M-$1B revenue) and developer agencies. The company utilizes a dual-motion strategy: self-serve for SMBs and direct sales for mid-market to refine the platform.

## Why Now
The proliferation of AI agents creates a need for an 'OS' layer to manage reliability, memory, and governance, moving beyond simple chatbot wrappers to integrated systems of action.

## Risks
- High competition in the agent orchestration/platform space.
- Unclear differentiation from existing low-code/no-code automation platforms.
- Reliance on channel partners (developer agencies) for distribution may limit direct customer feedback loops.
- Lack of specific traction metrics (revenue, active users, or retention) provided in the evidence.

## Open Questions
- What is the current ARR or number of active paying customers?
- How many developer agencies are currently using the platform?
- What specific 'systems of action' have been successfully deployed by customers to date?
- How does the 'AgentOS' architecture prevent vendor lock-in compared to native cloud AI services?

## Score Breakdown
| Area | Score |
|---|---:|
| Team | 15/20 |
| Product | 14/20 |
| Market | 10/15 |
| Traction / Freshness | 3/15 |
| Why Now | 7/10 |
| Defensibility | 5/10 |
| Risk Adjustment | 5/10 |

## Cited Claims
- Lua is the mid-market agent platform. [YC1, YC2]
- Founded by Lorcan O Cathain and Stefan Kruger, with 15-20 years of experience scaling tech companies. [YC2, YC4]
- Targets mid-market businesses ($50M-$1B) and developer agencies. [YC2]
- Product allows for TypeScript-based agent development with Zod validation. [WEB1]

## Sources
- **YC1** (yc, high): Lua Global Inc: The mid-market agent platform — https://www.ycombinator.com/companies/lua-global-inc
- **YC2** (yc, high): Lua is the mid-market agent platform. We deliver enterprise reliability with the speed, flexibility, and economics that mid-market companies demand - helping them deploy AI agents that drive sales, support, and operations across everyday channels and tools. We scale through developer agencies and channel partners, enabling rapid distribution without a large enterprise sales motion or scaled forward deployed teams. We think of Lua as an agentOS that abstracts all of the complexity required to launch enterprise grade agents and combine it with the tools needed for these agents to succeed in the real world. Lua was founded by Lorcan O Cathain (CEO) and Stefan Kruger (CTO)- experienced founders who have spent 15 - 20 years each scaling technology companies across emerging markets. We sell to mid-market enterprises and developer agencies in the US and internationally. Developers are increasingly our primary ICP but we run SMB & enterprise sales motions to accelerate our learnings and further develop our product: - SMB ($25- 1k per month): fully automated self-serve agents that handle sales and support for eCommerce companies, hotels, restaurants and general service businesses. If you’ve been on our website you’ve likely seen this. - Enterprise: We directly sell to mid-market (~ $50M- $1BN) businesses across the US and internationally to eat our own dog food and strengthen our platform. — https://www.ycombinator.com/companies/lua-global-inc
- **YC3** (yc, high): YC batch: Fall 2025; Industry: B2B; Status: Active; Stage: Early; Team size: 5 — https://www.ycombinator.com/companies/lua-global-inc
- **YC4** (yc, high): Lua was founded by Lorcan O Cathain (CEO) and Stefan Kruger (CTO)- experienced founders who have spent 15 - 20 years each scaling technology companies across emerging markets. — https://www.ycombinator.com/companies/lua-global-inc
- **WEB1** (website, medium): Lua AI - The Agent OS Backed by Combinator The AI workforce that companies actually run on. One workspace where people and agents work together — same rooms, same memory, governed on every action. Schedule a demo Join the waitlist Built with the world's leading AI providers. No lock-in Deploy real AI agents that solve real problems Written in TypeScript by your engineers, or composed using our Agent Builder by everyone else — same platform, production-grade either way. 01 · Developers I'm a developer. Real TypeScript, not YAML. Write actual code with Zod validation, proper testing, and a modern dev workflow. Quick start 1 import { LuaTool } from "lua-cli" ; 2 import { z } from "zod" ; 3 4 export class CheckOrderStatus implements LuaTool { 5 name = "check_order_status" ; 6 - description = "Look up a customer’s order" ; + description = "Look up a customer’s order (yes, even that one)" ; 7 8 inputSchema = z. object ( { 9 orderId: z. string (), + politeness: z. enum ([ "nice" , "extra-nice — https://heylua.ai/
- **HN1** (hn, medium): No HN story traction found for 'Lua Global Inc' or 'heylua.ai' in the top search results. — https://hn.algolia.com/

## The Call: Watch
Lua shows promise by targeting the mid-market with a developer-first 'AgentOS' approach, which aligns well with our thesis. However, the lack of concrete traction data makes it difficult to move to a meeting immediately. We need to see evidence of successful deployments or agency adoption to validate that this is a system of action rather than just a developer tool.

Thesis fit: The shift from 'chatbots' to 'agents' requires an orchestration layer that handles state, memory, and governance—Lua is positioning itself exactly there.

What would change our mind:
- Evidence of 5+ mid-market customers using the platform for core operational workflows.
- Data on agency partner adoption and the number of agents deployed through those channels.
- Case studies demonstrating the 'system of action' capability (e.g., agents executing multi-step workflows across disparate tools).

---
_Analysis mode: gemini. The model proposed component scores and prose from the evidence packet; the pipeline then recomputed the total, re-derived the recommendation from the score threshold, and dropped any citation to an evidence ID not in the packet. See `run_manifest.json` for the exact model._
