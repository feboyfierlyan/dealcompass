# Handoff MAIN

## Task dan status
MAIN-BENCHMARK-16: VERIFIED execution, 2026-10-10 08:20 WIB. Sixteen frozen synthetic
cases run through local rules API and deployed Rules + Jev API. Business/human
accuracy remains unverified. Product decision code unchanged during experiment.
MAIN-ACTION-TOUR-ACCURACY: VERIFIED locally (08:04 WIB); production verification pending this revision.
Prior MAIN-PUBLIC-UPLOAD-TOUR: VERIFIED locally and on public production (07:43 WIB). Public
access without credentials, light desktop UI, first-use tour and isolated CRM +
transcript uploads requested by user. Preserves P01–P05 demo and existing live ledger.
Earlier cutover is VERIFIED: one Railway service/worker, 500 MB volume, live P04,
persistent cache and ledger; temporary SSH key revoked. Historical handoffs remain
in Git history. They must not be used to restart an obsolete local live ledger.

## Branch dan commit
`integrator/english-graph-runtime`, [PR #36](https://github.com/feboyfierlyan/dealcompass/pull/36).
This revision builds on 78e8009. Railway follows this branch; not main yet.

## File dan fungsi
- `evaluation/deal_benchmark/`: frozen inputs/labels/hashes, end-to-end runner, raw
  redacted receipts, score report, pitch script and empty human review/ranking forms.
- `tests/ical/test_deal_benchmark.py`: reject broken provenance, wrong gates/owners,
  unnamed/duplicate reviews and counting unfinished reviews as correct.
- `backend/api/uploads.py`: bounded JSON/CSV ZIP ingestion, templates, validation,
  workspace receipt, expiry, distinct sources and explicit Jev consent.
- `backend/ingestion/scope.py`, dataset/graph/metrics/context/ranking/diagnostics:
  request-scoped dataset and snapshot, complete current-pipeline validation.
- `backend/decision/analyze.py`, `hybrid.py`: rules-only uploads without consent;
  separate workspace analysis caches and existing shared paid usage ledger.
- `backend/main.py`, `deployment.py`: workspace header, public access, same-origin
  writes, write/import limits and cached public analysis.
- `ImportWorkspace.tsx`, `Onboarding.tsx`, `main.tsx`: upload/preview/open workspace,
  return to demo, six-step action-driven tour, replay and reduced motion support.
- `lib/tour.ts`: adjacent placement with viewport bounds; overlay spotlight and smooth
  card movement. Actions: deal → Evidence → Context graph → root node → Your data →
  template download. No Next button; Skip/Escape remain available. SVG keyboard
  activation is supported alongside native buttons/links.
- `corporate.css`: selected/hover/focused graph labels use dark text on pale green;
  normal root retains white on dark green.
- `evaluation/scorecard.py`, results and `BENCHMARK_PROTOCOL.md`: separate actual
  rules scenarios from mocked Jev and historical live classification receipts.
- CSS and `Dashboard.tsx`: light desktop presentation, dynamic pipeline count.
- `lib/api.ts`, `phase3.ts`: workspace transport, variable deal counts and dates,
  complete 1..N ranks, exact-list joins, diagnostic sample-size validation and
  rejection of mixed snapshot dates inside one diagnostic response.
- `tests/test_uploads.py`, deployment tests and frontend tests: unseen IDs/dates,
  changing inputs, isolation, consent and malformed input; original demo regressions.
- `docs/NEW_DATA_AND_BENCHMARK.md`: supported formats, reference and honest limits.

## Kontrak dan dependency
Additive upload endpoints and optional X-DealCompass-Workspace header; existing v1
shapes and built-in snapshot remain intact. No new dependency. Original dataset
unchanged. Canonical CSV decisions remain the sole decision-log ingestion source.
Public mode explicitly configured by user; API key remains backend only.

## Cara menjalankan
Production: https://dealcompass-production.up.railway.app.
Railway variables configured with skip-deploys: `DEALCOMPASS_PUBLIC_ACCESS=1` and
`DEALCOMPASS_UPLOAD_DIR=/data/uploads`. Deployment 425bbe49-2b48-47e7-904a-b6dc407ab944 succeeded. Keep existing `/data/typesafe-usage.sqlite3` and cache.
Local tests: rules-only uvicorn on8000; production preview8083. Never use the old
local Jev launcher/ledger now that the cloud ledger is canonical.
See [deploy guide](../DEPLOY_RAILWAY.md) and [upload guide](../NEW_DATA_AND_BENCHMARK.md).

## Pengujian aktual
Benchmark run 2026-10-10 08:20 WIB:
- 16/16 normalized contexts equal between local and cloud; same decision version
  `rules+jev/1+5ecd9ec8b69f`. Original P01–P05 data untouched.
- Both arms: citation IDs/graph structure16/16; action-family12/16; explicit VP
  approval-gate screen12/16. All applicable screens: hybrid11/16, rules10/16.
- Comparison/exception wording4/4, capacity-exception screen1/1. These are
  mechanical screens, not independent semantic correctness judgments.
- Cloud:13 jev_applied,3 not_eligible,30 API-reported provider requests. Existing
  shared Railway ledger handles token receipts/budget. No local provider calls.
- Eight evaluator/review tests PASS. Existing decision suite34/35 including
  mocked cases (actual rules23/24); ranking15/15 rerun.
- Human review0 completed,32 case/arm ratings pending per criterion. No external
  benchmark score, no observed closing uplift or measured user time saving.

Latest revision, 08:04 WIB:
- Frontend regressions: 38 module +52 compiled API/component/upload +15 desktop
  tour placement tests PASS (105 total). First graph test attempt was sandbox-blocked
  on localhost; rerun with local-network access passed. TypeScript/Vite build PASS.
- Local browser: all six steps completed using mouse and keyboard; no Next control.
  Actual Evidence/graph/upload views open before the next step. Replay, Shift+Tab
  from the heading and Escape/focus restoration pass in the final build.
- Computed graph colors: root label5.63:1/type5.41:1; selected/hover/focus
  label10.87:1/type6.75:1; ordinary secondary text6.01:1. These graph text checks
  exceed4.5:1; this is not a full-application accessibility audit.
- Decision rerun: rules23/24 (original7/7 +synthetic16/17); E15 remains failing.
  Mock/replay11/11 excluded from that score. Ranking heuristic15/15; demo citation
  integrity5/5. No independent human correctness or ranking labels collected.
- Historical live paraphrase receipt: Jev10/12 vs rules6/12, classification only.
  No new paid provider calls for these evaluations. SalesTranscriptQA not run.

Earlier verified regression/deployment evidence:
Production 897db05: anonymous home and assets200, all five contexts/graphs200,
new OPP01 snapshot2026-10-10/ranking/findings/analysis200, rules_only with zero
provider requests, original demo unchanged and unknown OPP01 in demo404. Browser
confirmed four-step onboarding, light dashboard and Rules + Jev on P04; live
upload → validation → Open workspace passed without credentials.

- `python -m unittest discover -s tests -q`: 243/243 PASS (59.179s), rules/mocks.
- Node module tests (contracts/graph/present/english/analysis-store): 38/38 PASS.
- Compiled API/analysis/phase3/redesign/uploads tests: 52/52 PASS against local rules
  HTTP API, including one and six new deals through actual frontend validators.
- `npm --prefix frontend run build`: TypeScript/Vite PASS, 48 modules.
- Browser local8083: all four tutorial steps, file selection, validation, workspace
  activation and Northstar graph PASS. New OPP01 snapshot2026-10-10, stage age9,
  IDR33.6M and 15% discount gate; original five deals stay separate.
- No paid provider calls made by these regression tests. Earlier cloud ledger
  snapshot at07:15: 88requests/48,549input/5,407output, pending0, reserved0.
  This historical count is not a current count after later public usage.
- Logs: `/tmp/dealcompass-final-tests.log`, `/tmp/dealcompass-front-modules.log`,
  `/tmp/dealcompass-front-compiled.log`. Source data diff is empty.

## Fixture dan keterbatasan
New-data tests use fictional template records, not a claimed SalesTranscriptQA
benchmark run. No benchmark accuracy/closing uplift claim. Upload accepts canonical
structured JSON/CSV/JSONL, not arbitrary spreadsheets/PDF/audio. 1–20 open deals,
one per account; 2MB file/2,000rows. KasirNusa pricing/packages/approval policy and
existing rule patterns still apply. Missing decision history/evidence is explicit.
Access expires after24h; old files cleaned on later imports. No user accounts or
enterprise RBAC. Single-process global rate limits and shared token guard remain.
Public refresh does not bypass cached analysis. Trial hosting charges/expiry still
need owner attention. Ledger inspection over SSH needs a newly authorized key;
the temporary cutover key has been removed.

## Blocker
Benchmark gaps: B07/B14 lack explicit approval gates for unlogged claims; B10/B11
miss hybrid eligibility; B13 stale request persists. B09 rules negation fails but
hybrid passes the action-family screen. Unknown warnings mitigate some cases;
missing gates are not proof of unauthorized execution. Independent human labels
are still needed before claiming task accuracy. See benchmark/PITCH findings.

No implementation/deployment blocker. Public production and isolated upload smoke
verified; previous private-login instructions are superseded.

## Tugas berikutnya
Bima + Ical independently annotate source cases; Boy adjudicates and records
semantic reviews. Fix documented engine gaps in a separate revision, preserve
first-run receipts, then use new untouched cases for generalization.
Verify this revision on public production. Use the scoped accuracy scorecard and
benchmark protocol; collect independent labels and novice task evidence before
claiming product accuracy or usability gains.
Team rehearsal and submission using the public URL. Review/merge PR #36.
After eventual PR merge, deliberately switch Railway branch to main and verify.
Use one shared live backend; never reset or fork the token ledger.

## Update WIB
2026-10-10 08:20 WIB — internal benchmark execution and pitch evidence ready;
first-run failures retained; no independent/external accuracy claimed.
2026-10-10 08:04 WIB — action-driven adjacent tour and graph contrast locally
verified;105 frontend checks pass; reproducible scoped accuracy scorecard prepared.
2026-10-10 07:43 WIB — public source deployment and anonymous HTTP/browser checks
verified; local 243 backend +90 frontend PASS. New upload flow also passed in cloud.
