# Deal Acceleration challenge v1

An executable internal benchmark for the actual upload → ingestion → graph →
recommendation workflow. Sixteen new fictional accounts/deals, including positive
and negative controls. Expected checks and input hashes were frozen before running
any case. Labels were written by the project AI, **not independent human experts**.
The author could inspect the engine: this is a challenge set, not a blind holdout.

## Reproduce and inspect

- `input.json`: importable synthetic CRM + transcript + decision-log package.
- `cases.json`: predeclared expectations and label provenance.
- `frozen.json`: hashes and tested source commit. Never edit labels after seeing results.
- `results/rules.json`: local API run, explicit rules only, zero provider calls.
- `results/hybrid.json`: existing Railway API run, uploaded-data Jev enabled, shared
  persistent provider ledger and budget guard. No API key needed in this runner.
- `results/REPORT.md` and `summary.json`: generated comparisons, including failures.
- `human_gold_template.json`: unfilled independent annotation form.
- `PITCH.md`: what can be said to judges, including known limits.

```bash
python -m unittest tests.ical.test_deal_benchmark -v
python -m evaluation.deal_benchmark.run --report
```

The first-run commands were `--local` and
`--live-cloud https://dealcompass-production.up.railway.app`. They refuse to
replace an existing receipt. To run a new experiment, create a versioned suite;
do not delete inconvenient outputs or silently retry paid cases. Network errors
stay in the denominator. No `.env` loader or local Jev client is used.

Only the input package, without expected labels, was uploaded. Local/cloud
contexts are identical after replacing their workspace-access-handle prefix with
`[workspace]`. Receipts retain evidence records, graph, actions, source mode, cache,
version, provider request count and timestamps. Access handles are not published.
The API does not expose exact paid token receipts; the canonical Railway SQLite
ledger owns usage. Request counts are not token counts.

## How to read the measures

- Action-family screen recognizes the current action templates (price, reference,
  discovery). It is intentionally a mechanical regression screen, not a judge of
  every semantically acceptable sales action. B09/B13's conservative discovery
  expectation must be adjudicated; another non-blocking follow-up may be valid.
- Approval-gate screen compares the explicit `approvals_needed` field to the
  predeclared expectation. A missing explicit gate is **not proof** the app approved
  a discount: some outputs warn in `unknowns` and propose safe normal-price options.
- Citation/graph checks validate real IDs, endpoints, adjacent path edges and their
  sources. They do not prove that a factual sentence is entailed by its citation.
- Precedent explanation screens check recorded comparison/exception language,
  not full semantic relevance. Empty IDs are valid but are not judged precedents.
- No closing-rate, revenue, optimal-ranking or time-saving ground truth exists here.

## Complete human evaluation before claiming task accuracy

Bima and Ical each independently copy `human_gold_template.json`, read `input.json`,
and fill all 16 labels **before reading app outputs or cases.json**. Use a reviewer
name, acceptable action (allow multiple valid actions), approval need, exact source
spans and reason. Boy reconciles disagreements, retaining both originals. Reviewers
who already saw expected labels/outputs must disclose that and cannot be called blind.

Then review output receipts against the adjudicated labels: factual correctness,
semantic citation support, action acceptability, prerequisite/approval compliance,
precedent relevance and justified departure. Keep these scores separate. Do not
convert unfinished cells to passes. Team review is still not external validation.

For usefulness, ask people unfamiliar with the app to find a priority, identify an
owner/action, open its evidence path, recognize a prerequisite, and upload a new case.
Record task success, elapsed time, help and errors. Compare equivalent raw-CRM tasks
with counterbalanced order. Browser automation is not a novice-user study.
