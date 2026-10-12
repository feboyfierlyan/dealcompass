# Project status

**12 October 2026 — hackathon complete; portfolio prototype retained.**

DealCompass was built for Hackathon PENS 2026's Deal Acceleration challenge. The team did not receive a winning placement. The repository preserves the implemented product and measured results without implying an award, enterprise readiness or independently established sales uplift.

## Delivered

- Desktop sales workspace: priority list, next action, evidence, context graph and follow-up preparation.
- All P01–P05 demo prospects, with the original 2026-10-01 source snapshot preserved.
- Data ingestion, source provenance, direct/inferred edges, diagnostic findings and deterministic ranking.
- Rules + Jev workflow, explicit fallback, shared usage accounting and persistent cache.
- Template-based CRM/transcript uploads into isolated temporary workspaces.
- Light English UI and an action-driven onboarding tutorial.
- Docker/Railway deployment, regression tests and retained benchmark receipts.

PR #36 merged into `main` as `98780f5`. The public demo `/health` responded successfully on 12 October 2026. That health check does not revalidate every feature or make a paid Jev request. Hosting availability depends on the Railway account and provider configuration.

## Measured, with scope

The saved 10 October experiment compared rules and live hybrid on 16 synthetic new-data cases. Both returned resolvable citations and valid graph/path structure in 16/16 cases, and passed action-family and explicit-gate screens in 12/16. All applicable screens passed in 10/16 rules cases and 11/16 hybrid cases.

Expected labels were AI-authored before execution. Independent human review remains incomplete. The result is an automated challenge-set screen, not overall semantic accuracy. The 13 Jev-applied and 3 ineligible hybrid cases are all retained, including failures. [Full results](../evaluation/deal_benchmark/results/REPORT.md).

SalesTranscriptQA and CRMArena-Pro were evaluation references, not completed external benchmark runs. No closing uplift, time-saving percentage or superior deal-ranking accuracy has been measured.

## Known product gaps

| Gap | Implication | Follow-up acceptance |
| --- | --- | --- |
| English/idiomatic price requests can miss hybrid eligibility | Jev cannot improve an input that rules exclude first | New held-out paraphrases reach the correct eligible workflow without weakening policy checks |
| Withdrawn requests can remain active | A next action can rely on stale conversation context | Later cancellation supersedes the older request and cites both records |
| Some unlogged approval claims omit an explicit gate | Warnings may exist without a structured required-approval entry | Applicable explicit gate is present; a transcript claim never becomes approval |
| Template-bound import and fixed sales policy | Other companies need mapping and policy configuration | Versioned schema/policy support with validation and migration tests |
| Single-process deployment and public temporary workspaces | Not an enterprise tenant/access-control architecture | Authentication, durable tenant boundaries and coordinated rate/cache behavior before scaling |
| Human semantic evaluation pending | Structural checks do not establish recommendation correctness | Independent reviewers assess acceptable actions, supporting spans and precedent fit |

Preserve the first-run benchmark outputs when fixing these issues. A rerun on known cases is a regression result; generalization claims need a fresh held-out set.

## Closeout scope

The final documentation update adds a product-oriented README, original vector banner, actual product screenshots, architecture diagram, benchmark exports and restore instructions. It does not change the decision engine, reset billing history, disable hosting or remove cloud data. Local cleanup takes place only after the final changes are merged and verified on GitHub.
