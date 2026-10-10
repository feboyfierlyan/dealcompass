# Deal Acceleration challenge v1 — actual results

16 frozen synthetic cases. Labels written by AI before execution; not independent human gold. Action and policy results are automated screens, not whole-app accuracy.

| Measure | hybrid | rules |
|---|---|---|
| identity | 16/16 | 16/16 |
| owner | 16/16 | 16/16 |
| action_and_target | 16/16 | 16/16 |
| citation_ids_resolve | 16/16 | 16/16 |
| precedent_ids_resolve | 16/16 | 16/16 |
| graph_edges_resolve | 16/16 | 16/16 |
| supporting_paths_resolve | 16/16 | 16/16 |
| action_family_screen | 12/16 | 12/16 |
| approval_gate_screen | 12/16 | 12/16 |
| precedent_explanation_screen | 4/4 | 4/4 |
| capacity_exception_screen | 1/1 | 1/1 |

## hybrid
All applicable screens passed: 11/16. Referenced precedent IDs checked: 5. Outcomes: {'jev_applied': 13, 'not_eligible': 3}. API-reported provider requests: 30. Median context + analysis roundtrip: 1120.0 ms (different local/cloud environments; not a speed comparison).

Failures:
- B07: action_family_screen, approval_gate_screen
- B10: action_family_screen, approval_gate_screen
- B11: action_family_screen
- B13: action_family_screen, approval_gate_screen
- B14: approval_gate_screen

## rules
All applicable screens passed: 10/16. Referenced precedent IDs checked: 5. Outcomes: {'rules_only': 16}. API-reported provider requests: 0. Median context + analysis roundtrip: 3.0 ms (different local/cloud environments; not a speed comparison).

Failures:
- B07: approval_gate_screen
- B09: action_family_screen
- B10: action_family_screen, approval_gate_screen
- B11: action_family_screen
- B13: action_family_screen, approval_gate_screen
- B14: approval_gate_screen

## Claim limits
- Normalized local/cloud context pairs equal: 16/16. Only access-handle prefixes redacted.
- Empty precedent lists satisfy ID integrity vacuously; do not interpret this as 16 precedent correctness judgments.
- Human adjudication: pending. Do not call these expert-labelled results.
- No SalesTranscriptQA run or external benchmark score.
- Graph and citation scores check referential structure, not semantic support.
- Include fallback/not-eligible cases in the deployed-app denominator.
- This suite measures decision-readiness checks; no measured closing uplift.
