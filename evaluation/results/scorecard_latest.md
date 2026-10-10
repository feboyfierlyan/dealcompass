# DealCompass — accuracy evidence scorecard

Generated: 2026-10-10 08:18 WIB. Decision/ranking suite rerun: 2026-10-10 08:16 WIB.

Use the individual metrics below. There is no single validated whole-app accuracy score.

## Rules decision scenario acceptance: 23/24 (95.8%)

Original-data and developer-authored synthetic scenarios. Excludes mock/replay Jev.
Specified action, approval, precedent and evidence checks; not human-rated answer accuracy.
Receipt: `latest.json`.

## Ranking rule conformance: 15/15 (100.0%)

5 original-data + 10 synthetic scenarios.
Ordering obeys declared heuristic and preserves gates/provenance; not best-deal prediction.
Receipt: `ranking_latest.json`.

## Demo recommendation integrity: 5/5 (100.0%)

Five built-in deals; rules mode.
Citations resolve, precedents belong to candidate records, account scope and proposal labels hold. Does not prove that every citation entails each claim.
Receipt: `latest.json`.

## Mock/replay Jev integration checks: 11/11 (100.0%)

Transport mocks/replay only.
Fallback and policy integration behavior, not provider quality.
Receipt: `latest.json`.

## Historical paraphrases: rules: 6/12 (50.0%)

12 pre-labelled synthetic messages, historical run 2026-10-09T22:28:15.317184+00:00.
Exact match to the developer-assigned obstacle label; classification only.
Receipt: `paraphrases_live.json`.

## Historical paraphrases: live Jev: 10/12 (83.3%)

Same messages and labels, historical run 2026-10-09T22:28:15.317184+00:00; no new provider call.
Exact match for obstacle classification only, not whole-app accuracy.
Receipt: `paraphrases_live.json`.

## Visible failure

- E15: Sintetis sulit: "KasirPro lebih ramah di kantong". Batas rules diketahui.. Failed checks: I0296 terdeteksi harga.

## CRM-only comparison

On the five demo deals, the primary stage/value CRM baseline and graph+rules have the same ordering. This does not establish better ranking accuracy.
Graph+rules exposes 1 approval gate versus 0 in the deliberately limited CRM baseline, and named obstacles for 4/5 deals. This measures surfaced context, not measured sales-team usefulness.

## Claim boundaries

- Not an independent holdout. Development cases and synthetic labels may favor the implementation.
- No benchmark-wide SalesTranscriptQA run and no comparable external accuracy score.
- No measured sales uplift, time-to-close improvement, novice-user study or independent ranking ground truth.
- Do not average these percentages: they measure different things, with overlapping inputs.

Benchmark protocol and next human evaluation: `evaluation/BENCHMARK_PROTOCOL.md`.
