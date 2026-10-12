# Contributing to DealCompass

The hackathon is complete. Keep future changes focused, reproducible and honest about what the product can establish. Start with [project status](docs/PROJECT_STATUS.md), [architecture](docs/ARCHITECTURE.md) and [AGENTS.md](AGENTS.md).

## Branches and ownership

| Role | Branch prefix | Primary area |
| --- | --- | --- |
| Boy | `boy/` | Frontend |
| Bima | `bima/` | Ingestion, graph and API |
| Ical | `ical/` | Decision logic, Jev and evaluation |
| Main / integrator | `integrator/` | Cross-module integration, shared contracts, dependencies and CI |

Start from current `main`. Use a separate checkout/worktree for each concurrent contributor; do not switch a shared working directory underneath another person or agent. Coordinate cross-module changes with Main and preserve other contributors' work.

## Required handoff

Every work PR must update `docs/handoffs/<ROLE>.md` using **all headings** in [the template](docs/handoffs/TEMPLATE.md). Record:

- Implemented functions/files and intended behavior.
- Actual commands, test results, fixtures and limitations.
- Contract/dependency changes, blockers and next steps.
- The update time in Asia/Jakarta (WIB).

Contributors report at most `READY_FOR_REVIEW`; Main assigns `VERIFIED` or `MERGED` after checking the evidence. Historical coordination documents remain available, but old task assignments are not current completion claims.

## Verification before a PR

```bash
python -m unittest discover -s tests -v
python scripts/check_handoff.py --all
npm --prefix frontend run build
python scripts/check_handoff.py --base origin/main --head HEAD --branch integrator/your-task
```

Use your actual branch name. The last command checks committed PR differences; run it after committing the handoff. CI also checks ownership and protects original dataset files. Add focused frontend/API checks when changing those areas; build success alone does not prove business correctness.

## Data and evaluation rules

- Preserve the original dataset and its snapshot. Test changes with separate synthetic inputs.
- Keep provenance and distinguish direct relationships from inference.
- An approval request is not approval. Discounts above 10% need the applicable VP Sales approval and decision-log record.
- Never invent ranking, confidence, approvals, test passes or closing outcomes.
- Keep first-run benchmark receipts. Fixes evaluated on those cases are regression tests, not a fresh blind benchmark.
- Keep real secrets, private uploads and live usage ledgers out of the repository and frontend.
- Use rules/mock tests by default. Paid Jev calls must use the canonical shared ledger; never fork or reset accounting.

## AI-assisted contributions

AI tools do not communicate across team chats automatically. The human owner forwards tasks and verifies the resulting files, tests and handoff. Proposed text is not evidence that a repository change has been made. PR descriptions should explain the concrete behavior change and actual validation.
