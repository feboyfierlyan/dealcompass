# Handoff MAIN

## Task dan status
MAIN-RAILWAY-SETUP: VERIFIED local application boundary; deployment preparation only. User has a Railway account and requested preparation first. No Railway resources, public deployment, paid hosting subscription, or cloud Jev cutover created. Docker image build remains unverified (local daemon unavailable).

MAIN-PARAPHRASE-EVAL: evaluation completed, improvement not yet implemented. Twelve prelabelled synthetic messages: rules 6/12, live Jev 10/12. E15 idiom still fails; discount/authority category confusion also found.

MAIN-CLEAN-INSIGHTS: VERIFIED lokal. Priority methodology becomes Why this priority (four compact expandable factor rows); Data findings becomes What to check (readable finding titles, action-first detail, collapsed metrics/provenance/reference candidates).

MAIN-ENGLISH-GRAPH-RUNTIME: VERIFIED lokal. English presentation P01–P05, graph exploration integrated, and live Jev 404 recovery. Earlier entries below are historical.

MAIN-HYBRID-REVIEW: tiga perbaikan PR #32/#33/#34 VERIFIED pada commit yang tercantum di [review hybrid](../reviews/2026-10-10-hybrid-default.md). MERGED berurutan #33 de4cf7e, #34 69272f6, #32 6779cea setelah required CI lulus. Catatan lama di bawah merupakan riwayat aktivasi Jev.

MAIN-JEV-USAGE: implementasi dan provider live VERIFIED lokal; siap review PR/CI.
Pengguna memberikan credential untuk testing dengan batas tim 100.000.000 input token,
dan mengonfirmasi belum pernah dipakai. Smoke, P01–P04, dan UI P02 berhasil memakai Jev.
P05 tetap rules karena insufficient evidence; tidak diklaim sebagai live.

## Branch dan commit
Railway setup remains local on `integrator/english-graph-runtime`; earlier uncommitted UI/evaluation changes preserved. No new commit/PR/merge claimed in this turn.

Current work: `integrator/english-graph-runtime`, based on main `e44aee7`. Changes are local; no new PR/merge claimed.

Dokumentasi review/integrasi: `integrator/hybrid-review-record`. PR aplikasi menggunakan commit terbaru yang dicatat dalam review hybrid.

`integrator/jev-usage-live` dari main b766770. PR terpisah dari redesign UI #29.
Backend live berjalan dari checkout utama; frontend 5174 tetap dari worktree PR #29.
Tidak mengubah atau menggabungkan branch UI.

## File dan fungsi
`Dockerfile`, `.dockerignore`, `railway.json`: multi-stage build and Railway health/restart setup, excluding credentials/databases. `backend/deployment.py`: same-origin built UI + existing API, demo Basic Auth, cross-origin POST rejection, production startup validation, one worker. `tests/test_deployment.py`: ten deployment boundary/ledger tests. `docs/DEPLOY_RAILWAY.md`, `.env.example`, README: setup, secret placement, controlled ledger cutover, monitoring and rollback.

`evaluation/paraphrases.py`: opt-in metered live classification probe with production prompt drift guard, fixed labels, no retries, no dataset mutation. `evaluation/results/paraphrases_{rules,live}.{json,md}`: separate results and receipts; existing decision benchmark unchanged.

Latest UI: `Phase3Panels.tsx`, `DealWorkspace.tsx`, `style.css`. Existing API values, full findings, limitations and source links remain available through disclosures. Desktop scope; reduced-motion respected.

Current: `english.ts` reviewed display translations; presentation components translate ranking, diagnosis, source labels and operational conditions. `ContextGraph` integrates search, selection and neighbor expansion into the canvas controls. `api.ts`, `activeAnalysis.ts`, `Notice.tsx` and `DealTabs.tsx` distinguish missing backend routes from provider fallback. `backend/main.py` uses an English unknown-deal error.

- `docs/reviews/2026-10-10-hybrid-default.md`: hasil review dan checklist tiga regresi.
- `docs/coordination/MAIN.md`: status integrasi hybrid terbaru.

- `backend/integrations/usage.py`: SQLite ledger, initialize eksklusif, summary,
  reserve atomik, finish receipt input/output; unknown/pending menghentikan spending.
- `jev.py`: wajib ledger untuk transport nyata, pencatatan sebelum validasi jawaban,
  endpoint resmi saja, error/fallback tetap eksplisit.
- `jev_live.py`: CLI init-budget dan usage; loader TYPESAFE_USAGE_DB.
- `.env.example`, `.gitignore`: contoh setting non-secret, abaikan DB lokal.
- `tests/ical/test_usage.py`: 12 uji guard/storage/concurrency/HTTP tanpa provider.
- `JEV_LIVE.md`, koordinasi Main: prosedur satu ledger tim dan batas keandalannya.

## Kontrak dan dependency
Deployment wrapper preserves API v1 and local `backend.main:app`. No runtime dependencies added. Image targets Node 24 / Python 3.12. Jev cloud mode requires explicit absolute ledger/cache paths within the attached Railway volume and an existing unblocked ledger; never initializes or resets usage. Rules is the deployment default.

Current changes preserve v1, source datasets, IDs, amounts, decision rules, approvals and dependencies. Display translations are exact reviewed mappings, not provider-generated substitutions.

Tidak ada dependency atau kontrak v1/ranking/dataset baru. SQLite stdlib.
Cap 100 juta input; output dicatat terpisah. Reservasi konservatif 1 juta per request,
payload max64KiB/16questions. Ini guard lokal, bukan tokenizer/provider hard cap.
Satu request in-flight; permintaan paralel lain fallback rules. Semua proses/anggota
harus melalui host dan ledger yang sama. Pemakaian di luar jalur ini tidak terukur.

## Cara menjalankan
Production: set process env `DEALCOMPASS_DEMO_PASSWORD` (at least 16 characters), optional username, and explicit rules/jev mode; run `python -m backend.deployment`. Does not load .env automatically. Railway supplies PORT, `/data` must be attached for live mode. Follow [deployment guide](../DEPLOY_RAILWAY.md); existing local 8000/5174 runtime remains in place.

Current runtime: primary checkout backend port 8000 and frontend port 5174, both on current source. Backend: `python -m backend.integrations.jev_live --env-file .env serve --port 8000`; frontend: `npm --prefix frontend run dev -- --port 5174 --strictPort`. The old Python process lacked `/analysis`; restart after pulling backend changes. Existing credential and usage ledger preserved.

Host demo telah dikonfigurasi `.env` backend-only (0600), ledger absolut di
`.local/typesafe-usage.sqlite3` (0600). Keduanya ignored Git. Jangan ulang inisialisasi.

```bash
python -m backend.integrations.jev_live --env-file .env usage
python -m backend.integrations.jev_live --env-file .env serve --port 8000
```

Backend rules milik Main PID72643 dihentikan dan diganti backend live PID28657.
Preview http://127.0.0.1:5174/ → P02 → Jalankan analisis ulang. GET ranking tetap rules;
POST eksplisit memakai Jev. Tidak menyimpan key di frontend/PR/log maupun pesan tim.

## Pengujian aktual
Railway preparation: 232/232 backend tests PASS (54.620s), including 10 new deployment tests; TypeScript/Vite production build PASS. Actual temporary production server on 8082: built HTML + both assets, all five deal graphs, forwarded HTTPS same-origin analysis POST PASS, 0 provider requests. Server stopped after test. Logs: `/tmp/dealcompass-deploy-tests.log`, `/tmp/dealcompass-production-smoke.log`. Latest read-only team ledger snapshot: 85 requests / 47,048 input / 5,167 output, no pending/reserved, not blocked; no paid call made by deployment verification.

Paraphrase run: 12 live requests, 5914 input / 970 output tokens; model jev-1.13.0. Team ledger after run: 46540 input, pending 0. No prompt tuning or production logic change. Five rules misses improved, one rules success regressed in Jev (PAR-10).

Latest clean panels: 49/49 API/component regression tests PASS against isolated rules API; production build PASS. Browser: summary/detail views verified at desktop size; meaningful finding titles, four factor rows, closed technical sections and intact action/uncertainty detail. No paid refresh requested.

Current: backend 222/222 PASS; frontend modules 38/38 PASS; compiled API/components 49/49 PASS (87 frontend total); TypeScript/Vite build PASS. Browser: English search Procurement -> I0335 -> Show connections reveals two recorded email nodes on the same graph; View evidence opens its translated source. Live P02 HTTP: `jev_applied`, model `jev-1.13.0`, 10 requests; VP Sales approval remains required. Browser P04 shows Rules + Jev (3 requests). Ledger after these tests: 66 requests, 37,199 input / 3,749 output, pending 0, remaining 99,962,801 input. This turn added 7,428 input tokens. Unit/HTTP regression tests use isolated rules backend, no paid provider.

Review hybrid terbaru: gabungan engine + route + UI lulus 222/222 backend, 85/85 frontend, build TypeScript/Vite dan handoff. Reproduksi race tetap 10 request mock/satu workflow; browser graph berpindah ke jalur versi baru. Tidak memakai provider berbayar dalam review.

- 26 targeted tests PASS (12 usage +14 live mock).
- Seluruh backend `python -m unittest discover -s tests -v`: 200/200 PASS, 46.565s.
  Run awal menemukan non-JSON HTTP error berubah menjadi invalid_response; sudah
  diperbaiki dan suite diulang. Unit tests tidak memuat .env / tidak memanggil provider.
- LIVE smoke: 1 request, model jev-1.13.0, 475ms, input550/output77. Choice harga,
  Noul approval0.04, Score kejelasan2.0. Semantic/shape PASS.
- LIVE P02 CLI: 10 request, invariant valid dan VP Sales pending, PASS.
- LIVE P02 browser: tombol analisis menghasilkan Analisis dengan Jev; request selesai,
  target keputusan VP Sales dan persetujuan yang diperlukan tetap terlihat.
- LIVE P01:6 request PASS; P03:1 PASS; P04:3 PASS; P05:0, rules,
  NOT_LIVE_SUCCESS yang diharapkan (insufficient evidence). Semua invariant true.
- Total ledger setelah seluruh tes live:31 request, input17.840/output1.657,
  remaining99.982.160 input; pending0, reserved0, blockedfalse.
- Screenshot UI lokal: `/tmp/dealcompass-jev-live/p02-live.png`.
- Receipt operasional lokal P01/P03/P04/P05 di `.local/live-proof/`, ignored Git.

## Fixture dan keterbatasan
Deployment tests use temporary credentials/ledgers and rules/mock analysis; they do not prove live cloud connectivity or container build success. Basic Auth is an HTTPS demo gate, not per-user RBAC. One instance/worker is required. Persistent volume/cutover still must be verified on Railway before live activation.

Paraphrase eval is a small developer-labelled synthetic diagnostic set, one observation each, not a holdout or closing benchmark. Automatic approval review rejected the optional full copied-context live E15 workflow because it would export dataset-derived context; the approved safer run sends only invented strings. Thus full hybrid/policy preservation is not claimed from these 12 calls.

Mobbin references inspected visually: [Linear issue detail](https://mobbin.com/screens/d0f8ebba-34b7-469c-a708-1069e55a3e02) (short title, readable body, secondary properties) and [Mixpanel report](https://mobbin.com/screens/f4ec7f64-cba0-48e5-87c1-056a7626d949) (grouped collapsible sections). Adaptation to sales findings, not a copied analytics editor. Labels describe finding types; no changed scores or generated findings.

Current: English interface and reviewed P01–P05 operational text; proper names and original-language evidence/analysis remain available for audit. Unknown source text is preserved rather than guessed. Graph reveals existing recorded relationships only, direct/inferred labels retained, bounded to 24 visible nodes. This is a local runtime fix, not a hosted deployment.

Unit guard memakai MockTransport; hasil live disebut terpisah. Rules ranking tidak
berubah menjadi ranking Jev. Jev tidak memberi approval bisnis atau probabilitas closing.
Ledger menyimpan whitelist usage, bukan body provider. Reservasi bukan tokenisasi resmi;
usage di luar backend bersama tidak dapat dipantau. Tidak ada jaminan biaya global dari
provider hanya melalui counter lokal. Benchmark kualitas semua kasus belum dijalankan
ulang ke provider berbayar; invariant lima deal bukan klaim akurasi sempurna.

## Blocker
Railway CLI 5.64.2 is installed in `/tmp/dealcompass-railway-cli` but whoami reports Unauthorized. User explicitly chose preparation first. Docker daemon is unavailable locally; attempting to open OrbStack by application name failed. No cloud provisioning or image build success claimed.

Current: no blocker for local preview. Provider and route failures have distinct fallback labels; unknown routes include restart guidance. Shared team ledger must remain the single spending path.

Tidak ada blocker live saat uji. Pemakaian tim selanjutnya harus lewat backend/ledger
bersama; tidak ada deploy/public access baru. Tidak ada reset otomatis untuk receipt
unknown/pending: perlu rekonsiliasi berdasarkan usage provider agar tidak menghapus biaya.

## Tugas berikutnya
Review/publish the prepared application revision; authenticate Railway, select workspace and approve hosting budget, create one service + /data volume, deploy rules and verify public HTTPS. Then stop old live callers, back up/transfer the complete existing ledger, compare totals, activate Jev on the cloud only, and verify restart persistence. Never resume the old local ledger after cloud spending begins.

Current: team rehearsal on http://127.0.0.1:5174/; review these local changes before a new PR. Do not restart older worktree servers over the repaired preview.

Status terbaru: PR aplikasi #32/#33/#34 sudah merged. Tim sinkronkan main; rehearsal memakai backend/ledger bersama. Daftar di bawah adalah riwayat tugas aktivasi Jev.

1. Review dan integrasikan PR Jev ini secara terpisah dari UI #29.
2. Tim memakai backend bersama; cek usage sebelum/sesudah sesi demo/testing.
3. Rehearsal/demo/submission; jangan rerun batch evaluasi besar tanpa kebutuhan.
4. Jika provider gagal, tampilkan fallback rules; jangan klaim live dari label ranking.

## Update WIB
2026-10-10 05:55 WIB — Railway deployment preparation and local production verification complete; cloud login/provisioning/cutover pending.

2026-10-10 WIB — English, integrated graph controls and current live runtime verified. See current entries above; earlier token totals/PIDs below are historical.

2026-10-10 — review hybrid VERIFIED; #33/#34/#32 MERGED dengan required checks lulus. Catatan review dipublikasikan lewat PR dokumentasi integrator.
2026-10-10 01:10 WIB — live verified dengan monitoring persisten. Key/DB tidak masuk Git.
