# Handoff MAIN

## Task dan status
MAIN-PUBLIC-UPLOAD-TOUR: VERIFIED locally; production deployment pending. Public
access without credentials, light desktop UI, first-use tour and isolated CRM +
transcript uploads requested by user. Preserves P01–P05 demo and existing live ledger.
Earlier cutover is VERIFIED: one Railway service/worker, 500 MB volume, live P04,
persistent cache and ledger; temporary SSH key revoked. Historical handoffs remain
in Git history. They must not be used to restart an obsolete local live ledger.

## Branch dan commit
`integrator/english-graph-runtime`, [PR #36](https://github.com/feboyfierlyan/dealcompass/pull/36).
This revision builds on 857bac5. Railway follows this branch; not main yet.

## File dan fungsi
- `backend/api/uploads.py`: bounded JSON/CSV ZIP ingestion, templates, validation,
  workspace receipt, expiry, distinct sources and explicit Jev consent.
- `backend/ingestion/scope.py`, dataset/graph/metrics/context/ranking/diagnostics:
  request-scoped dataset and snapshot, complete current-pipeline validation.
- `backend/decision/analyze.py`, `hybrid.py`: rules-only uploads without consent;
  separate workspace analysis caches and existing shared paid usage ledger.
- `backend/main.py`, `deployment.py`: workspace header, public access, same-origin
  writes, write/import limits and cached public analysis.
- `ImportWorkspace.tsx`, `Onboarding.tsx`, `main.tsx`: upload/preview/open workspace,
  return to demo, first-use four-step tour, replay and reduced motion support.
- CSS and `Dashboard.tsx`: light desktop presentation, dynamic pipeline count.
- `lib/api.ts`, `phase3.ts`: workspace transport, variable deal counts and dates,
  complete 1..N ranks, exact-list joins and diagnostic sample-size validation.
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
`DEALCOMPASS_UPLOAD_DIR=/data/uploads`. New source deployment must finish before
claiming public access. Keep existing `/data/typesafe-usage.sqlite3` and cache.
Local tests: rules-only uvicorn on8000; production preview8083. Never use the old
local Jev launcher/ledger now that the cloud ledger is canonical.
See [deploy guide](../DEPLOY_RAILWAY.md) and [upload guide](../NEW_DATA_AND_BENCHMARK.md).

## Pengujian aktual
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
No local implementation blocker. Production source deployment and anonymous smoke
verification pending; no public success claimed until checked.

## Tugas berikutnya
Publish PR revision, check CI and Railway build, anonymously verify all five demo
contexts, new upload, light mode and tour. Then team rehearsal and submission.
After eventual PR merge, deliberately switch Railway branch to main and verify.
Use one shared live backend; never reset or fork the token ledger.

## Update WIB
2026-10-10 07:42 WIB — local implementation and regression verification complete;
public/upload variables configured, production source publish next.
