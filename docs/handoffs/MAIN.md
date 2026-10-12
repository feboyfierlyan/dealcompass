# Handoff MAIN

## Task dan status
MAIN-CLOSEOUT: documentation VERIFIED locally, 2026-10-12 11:20 WIB. The user requested
professional final documentation/assets, push and merge to main, then local storage
cleanup. PR #36 is already merged as 98780f5; this is a new documentation-only change.
Remote CI/merge and destructive cleanup are pending at the time of this handoff.
Earlier handoffs and runtime verification receipts remain in Git history.

## Branch dan commit
`integrator/project-closeout`, based on `origin/main` at `98780f5`.
No runtime/engine/source-dataset change. Final PR reference will be recorded by GitHub.

## File dan fungsi
- README: English product overview, real screenshots, architecture, quickstart,
  upload/provider boundaries, benchmark comparison, team and documentation links.
- CONTRIBUTING: English contribution/handoff and evaluation rules.
- docs/README, ARCHITECTURE, PROJECT_STATUS, MAINTENANCE: navigable documentation,
  implemented system/route map, honest gaps, restore and safe cleanup procedures.
- docs/assets: original banner and architecture PNG/SVG, deterministic Matplotlib
  renderer, actual local rules-only dashboard and context-graph screenshots.
- evaluation/deal_benchmark/figures: prior pitch charts now included in Git, with
  reproducible renderer and interpretation. Saved first-run receipts are unchanged.
- docs/DEPLOY_RAILWAY and coordination/MAIN: correct merged-PR status, preserve
  historical deployment branch/accounting facts and mark competition complete.

## Kontrak dan dependency
No API or runtime dependency change. Matplotlib is optional for rerendering docs;
static assets require no renderer on the application server. Original dataset is
unchanged. No key, private environment file or usage database is staged.

## Cara menjalankan
Follow README rules-only setup. Fresh checkout: Python venv + requirements.txt,
`npm --prefix frontend ci`; separate uvicorn and Vite or built same-origin runtime.
Restore instructions in docs/MAINTENANCE.md. Existing Railway ledger remains the
canonical counter; local historical databases must never replace it.

## Pengujian aktual
2026-10-12, local:
- `python -m unittest tests.ical.test_deal_benchmark -v`: 8/8 PASS.
- `python scripts/check_handoff.py --all`: PASS before and after handoff update.
- `npm --prefix frontend run build`: TypeScript/Vite PASS, 49 modules.
- Documentation checker: 58 relative link/image references resolve; both new SVG
  assets parse. New asset/document secret-signature scan PASS (not a full audit).
- Both graphic renderers PASS. Benchmark counts asserted from saved receipts:
  rules [16,12,12,10], hybrid [16,12,12,11]. No new provider calls.
- Browser local rules runtime8091: actual P04 next step and context graph captured;
  exported screenshots, banner and architecture visually reviewed without clipping.
- GitHub README browser check: all primary images load. README embeds PNGs to
  preserve typography on machines without DejaVu Sans; editable SVGs include a
  standard sans-serif fallback.
- Public HTTPS /health200 with v1 and 2026-10-01 snapshot. Health only, not new
  live semantic/provider validation.
- `git diff --check`: PASS. Full backend CI runs on the PR; not rerun locally for
  this documentation-only change.

## Fixture dan keterbatasan
Documentation uses actual fictional demo data and saved synthetic benchmark results.
16-case labels are AI-authored and independent human review is pending. No external
benchmark run, closing uplift, enterprise readiness or winning placement is claimed.
Known engine gaps remain documented. No software license is invented.
Local cleanup does not stop Railway, revoke provider credentials or delete cloud
volume data. The historical source branch is retained until separately reconfigured.

## Blocker
No documentation blocker. CI/remote merge verification must finish before deleting
local project files. Private local-only state and local-only merge history require
an owner-readable recovery archive outside the removed checkout.

## Tugas berikutnya
Push final docs, create PR, verify required CI, merge without bypassing branch
protection, fetch/verify main, then clean local project directories and project-owned
scratch environments. Preserve a minimal private recovery archive and report actual
space reclaimed. Do not publish that archive or reset provider usage.

## Update WIB
2026-10-12 11:20 WIB — final documentation/assets verified locally; remote CI/merge
and cleanup are the remaining closeout steps.
