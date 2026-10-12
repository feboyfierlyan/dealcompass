# Architecture

DealCompass connects source records to sales actions while retaining the evidence behind each relationship. This document describes the implemented hackathon prototype, not a proposed distributed platform.

![System architecture](assets/architecture.svg)

## Source model

The loader consumes 15 canonical CSV/JSONL files. Five groups explain their business purpose:

| Source group | Records | Contribution |
| --- | --- | --- |
| CRM and people | Accounts, deals, contacts, employment history, employees | Deal identity, owner, stage, value and relationship context |
| Conversations | External/internal emails and meeting notes | Requests, blockers, participants and timing |
| Product and support | Outlets, daily/monthly usage, tickets, bugs, releases, features | Product experience, operational context and candidate-reference checks |
| Billing | Contracts and billing | Package limits, commercial context and historical terms |
| Decision history | `decision_log.csv` | Recorded approvals, rejections, exceptions and promises |

`decision_log.csv` is canonical. The accompanying spreadsheet is not ingested as extra decisions. Original source files are immutable, with business snapshot **2026-10-01**. Demo scope is P01–P05; uploaded workspaces can supply other IDs and snapshots.

## Data and request flow

1. **Resolve the workspace.** `backend/main.py` resolves an optional `X-DealCompass-Workspace` handle into request-local dataset scope. Without it, requests use the original demo. Expired or unknown handles fail explicitly.
2. **Load records.** `backend/ingestion/dataset.py` validates keys, types and dates while retaining original rows, source IDs and file locators. `scope.py` selects the active dataset and snapshot.
3. **Build context.** `backend/graph/store.py` builds a NetworkX multigraph. `context.py` selects the deal context and candidate decisions. Edges retain source evidence, relationship type, direct/inferred classification and validity dates.
4. **Prioritize and diagnose.** `decision/ranking.py` computes the deterministic priority heuristic. `graph/analysis.py` and the diagnostic API supply findings. Ranking is independent of Jev calls.
5. **Analyze.** `decision/hybrid.py` starts with a rules recommendation. If Jev is enabled and the context is eligible, the adapter can enrich the analysis. Returned recommendations are checked for evidence integrity and preservation of policy requirements; failure produces a labelled fallback.
6. **Present and inspect.** React renders the next step, its owner and target. Evidence and graph views expose the source records and paths; a follow-up plan can be reviewed and copied.

## Ranking is an explicit heuristic

The method is `deal-priority-heuristic-v1`. Deals with sufficient context enter the acceleration tier; insufficient-context deals enter discovery without a fabricated score. For eligible acceleration deals, the score has four components:

- Stage: up to 4 points.
- Annual potential: up to 3 points, using value bands.
- Customer-stated blocker: up to 2 points.
- Relevant precedent: up to 1 point.

Ties use blocker strength, stage, value and finally deal ID for determinism. Stage age and approval needs provide context rather than extra score. The score is an order of attention, not a learned probability of winning a deal. The current demo ordering matches the simple CRM baseline; see the evaluation receipts before claiming a ranking advantage.

## Graph and evidence contracts

A node has an ID, label and type. An edge has source/target IDs, a relation, evidence IDs, a direct/inferred marker and optional temporal bounds. Evidence includes its source file, source row ID, date and excerpt.

A recommendation carries an action, owner, milestone, evidence IDs, precedent IDs/comparisons, required approvals, unknowns and engine mode. The analysis envelope adds version/fingerprint, provider outcome, cache status and supporting paths.

The graph is useful because these objects join on stable IDs. A displayed line is not proof of causation: employment overlap is an inferred connection, and a candidate customer is not an approved reference. Structural provenance validation is also distinct from semantic correctness.

## API entry points

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/health` | Service health and active snapshot |
| GET | `/api/deals` | Active workspace deal list |
| GET | `/api/deals/{deal_id}` | Deal context, graph and evidence |
| GET | `/api/pipeline/priorities` | Deterministic ranking with factors and paths |
| GET | `/api/pipeline/initial-analysis` | Pipeline diagnostic findings |
| GET | `/api/deals/{deal_id}/initial-analysis` | Deal diagnostic findings |
| POST | `/api/deals/{deal_id}/analysis` | Recommendation plus analysis/cache metadata |
| POST | `/api/deals/{deal_id}/analyze` | Compatibility response: Recommendation v1 |
| GET | `/api/import/template` | JSON example |
| GET | `/api/import/template.zip` | CSV + transcript kit |
| POST | `/api/import?allow_jev=false` | Validate input and create a temporary workspace |

Use `deal_id` (for example `DL-004`) rather than `account_id` (`P04`) in deal routes. Upload receipts return the workspace handle for subsequent requests. Source contracts are in [`backend/contracts.py`](../backend/contracts.py), the [v1 contract](coordination/API_CONTRACT.md) and [phase 3 contract](coordination/PHASE3_CONTRACT.md). Historical status paragraphs in those documents describe their integration stage at the time; route implementations are authoritative for the current surface.

## Optional provider and persistent state

Jev is called only from the backend. An analysis may require multiple provider requests. Concurrent requests for the same context share an in-flight workflow; completed analyses use a fingerprinted cache, and failures have a short negative-cache window.

- **Analysis cache:** a dedicated SQLite file stores reusable results.
- **Usage ledger:** a separate SQLite file records reservations and provider usage receipts against the team ceiling. Missing receipts fail closed.
- **Uploads:** bounded source files live under a separate directory, with expiry and request-scoped access.

The supported deployment is one service, region and worker. Cache coordination and rate limits are process-local; a horizontally scaled deployment would need additional coordination. The persistent Railway volume is the canonical location of the team's live ledger after cutover. A cache can be rebuilt; billing history must not be reset.

## Boundaries

The app proposes actions. It does not contact customers, execute discounts, update an external CRM or infer another company's sales policy. Public workspace handles are temporary access mechanisms, not user accounts or enterprise tenant authorization. See [new-data behavior](NEW_DATA_AND_BENCHMARK.md) and [known gaps](PROJECT_STATUS.md).
