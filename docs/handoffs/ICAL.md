# Handoff ICAL

## Current update — ICAL-05 Rules + Jev default deal analysis, 2026-10-10 03:50 WIB
Status **READY_FOR_REVIEW** (pelaksana Ical atas penugasan pengguna). Main menetapkan VERIFIED/MERGED.

### Audit sebelum perubahan (kondisi main 103cfe0)
- Sudah hybrid: `analyze_deal_trace` (mode rules|jev|replay, Choice hambatan, Noul klaim approval,
  Score preseden, anggaran 15 dtk, fallback penuh ke rules), `JevClient` + `UsageLedger` (reservasi,
  fail-closed), `ReplayClient`, `jev_live` (check/smoke/analyze/serve).
- Belum tersambung ke pengalaman default: POST `/analyze` hanya dari tombol; tanpa diagnostic Bima
  (hasil bisa beda dari ranking); tanpa cache/dedup (setiap klik = workflow provider baru); respons
  tidak membedakan rules-only vs Jev gagal kecuali lewat teks unknowns; tanpa jalur graph untuk
  hasil POST (UI memakai jalur ranking); PR #32 menambah Agent/chat yang kini dihapus.
- Ranking pipeline tetap rules (`rank_deals`), tidak disentuh.

### Alur rules → Jev → validasi → UI (`backend/decision/hybrid.py`)
1. Rules `analyze_deal_trace(mode='rules', diagnostic)` selalu dihitung (identik dengan rekomendasi ranking; diuji).
2. Mode rules → `rules_only`; bukti tidak cukup (P05) → `not_eligible`; keduanya nol client/request.
3. Cache key = sha256(deal_id, fingerprint konteks+diagnostic, `analysis_version`, konfigurasi model).
   `analysis_version` = `rules+jev/1` + hash kode `backend/decision/{analyze,signals,precedents,policy,records,hybrid}.py`
   (termasuk teks pertanyaan Jev). Konfigurasi = mode, `TYPESAFE_MODEL`, base URL (replay: direktori). **API key tidak ikut.**
4. Cache hit (memori → SQLite `DEALCOMPASS_ANALYSIS_CACHE_DB`, default `analysis-cache.sqlite3` di folder ledger,
   **file terpisah dari ledger**) → disajikan `cache: hit`, `generated_at`/`provider_requests`/model asli tidak diubah.
5. Single-flight: permintaan bersamaan key sama menunggu satu workflow (`cache: shared`).
6. Workflow `analyze_deal_trace(mode=jev)` lewat `JevClient` default = `UsageLedger` tim yang sama (tidak ada counter baru).
   Satu workflow = beberapa request (per pesan + per preseden), bukan satu request.
7. Rules memeriksa hasil Jev: semua request sukses, bukti/preseden resolvable, label USULAN, approval rules ⊆ approval
   hasil, gate kandidat referensi & pengambil keputusan tidak hilang. Gagal → rekomendasi rules + unknown alasan.
8. Kegagalan apa pun (timeout, 401/429/529, invalid_response, `usage_budget_blocked`, gate dropped) →
   `jev_unavailable` + `fallback_reason`; disimpan di negative cache memori `DEALCOMPASS_JEV_RETRY_AFTER_S` (default 300 dtk)
   sehingga navigasi tidak retry. Hanya `refresh=true` (tombol) yang mencoba ulang. Tanpa retry otomatis.
9. Hanya hasil `jev_applied` yang disimpan persisten. Hasil tetap Recommendation v1 + metadata.

### Kontrak (aditif, diusulkan ke Main)
- Endpoint baru `POST /api/deals/{deal_id}/analysis[?refresh=true]` (route di PR Bima-area
  `bima/hybrid-analysis-route`) → `{schema_version, deal_id, snapshot_date, recommendation: Recommendation, analysis: AnalysisMeta}`.
- `AnalysisMeta`: `analysis_id`, `analysis_version`, `context_fingerprint`, `engine_mode`,
  `outcome: jev_applied|rules_only|jev_unavailable|not_eligible`, `analysis_status`, `fallback_reason`,
  `cache: fresh|hit|shared|none`, `generated_at` (UTC), `provider_requests`, `model`, `gate`
  (teks sama dengan faktor ranking `gate_approval_izin`), `evidence_paths` (jalur edge asli dari trace aktif,
  pencari jalur ranking + `path_is_valid`), `path_limitations`.
- `Recommendation`/`engine_mode` enum **tidak diubah**; label UI "Rules + Jev" = `outcome=jev_applied` & `engine_mode=jev`;
  replay diberi label replay. Validator: Pydantic `AnalysisEnvelope` (backend) + `isAnalysisEnvelope` (frontend).
- `DecisionTrace.fallback_reason` (field baru, opsional). `POST /analyze` lama memakai workflow/cache yang sama.
- `jev_live` loader menerima `DEALCOMPASS_ANALYSIS_CACHE_DB`, `DEALCOMPASS_JEV_RETRY_AFTER_S`.
- Usulan untuk Main: catat endpoint/metadata ini di `API_CONTRACT.md` (tidak diedit Ical).

### Pengujian ICAL-05 (Windows, Python 3.11.9, 03:00–03:45 WIB)
- `tests/ical/test_hybrid.py` 17/17 (MockTransport/replay; nol token berbayar): rules-only nol request; Jev sukses
  jadi versi aktif + approval VP Sales + jalur valid; cache hit tanpa request baru dan provenance sama; cache persisten
  lintas restart + ledger hanya bertambah sekali; fingerprint konteks berubah (snapshot sama) → miss; versi/model berubah → miss;
  key API berbeda → hit; 4 permintaan bersamaan → 1 workflow; timeout/401/invalid_response → fallback jujur, tidak retry
  tanpa refresh; jendela retry kedaluwarsa; ledger terblokir → `usage_budget_blocked`, 0 request transport; P05 tidak membuat
  client; Jev yang menghapus gate approval ditolak (`approval_gate_dropped`); izin referensi P03/P04 tetap; replay berlabel
  replay; isolasi DL-002/DL-004; gate & rekomendasi rules identik dengan ranking untuk lima deal.
- `env -u TYPESAFE_API_KEY python -m unittest discover -s tests` → `Ran 217 tests, OK` (branch ini);
  branch route → `Ran 220 tests, OK`.
- `python -m evaluation.run_eval` → decision 34/35 (E15 batas diketahui, sama seperti sebelumnya), ranking 15/15.
  File hasil yang ter-regenerasi tidak di-commit (hanya timestamp/latensi berubah).
- `scripts/check_handoff.py --all` dan `--branch ical/hybrid-deal-analysis` → valid.
- **Live Jev tidak dijalankan**: laptop ini tidak punya `.env`/key maupun ledger tim
  (`~/.local/share/dealcompass` tidak ada). Tidak membuat ledger baru. Pemakaian token: 0. Verifikasi live
  harus dilakukan Main di host ledger tim: `jev_live usage` sebelum/sesudah, buka P02 sekali, buka lagi (harus cache hit).
- Browser memakai backend MOCK (MockTransport) — lihat docs/handoffs/BOY.md; bukan bukti live.

### Keterbatasan / sisa
- Negative cache hanya di memori (restart backend mengizinkan satu percobaan baru per deal).
- Single-flight per proses; beberapa worker uvicorn tidak berbagi in-flight (cache SQLite tetap berbagi hasil).
- `analysis_version` berubah bila kode keputusan berubah → cache lama tidak dipakai (disengaja, konservatif).
- Rules memeriksa gate, bukan kebenaran semantik klasifikasi Jev; E15 (parafrase) tetap batas rules.

## Task dan status
ICAL-05 (analisis default Rules + Jev, cache/dedup): **READY_FOR_REVIEW** — rincian di bagian Current update di atas.
Riwayat ICAL-04 di bawah tetap.

ICAL-04 (pembuktian metode dan paket penjelasan mentor, `docs/prompts/ICAL-04.md`): **READY_FOR_REVIEW**. Main memutuskan VERIFIED/MERGED.
- [x] `evaluation/MENTOR_BRIEF.md`: masalah bisnis, kenapa CRM saja belum cukup, graph sebagai alasan/riwayat, arti ranking, tindakan P01–P05, jawaban P04>P01, P02 bukan otomatis pertama, P05 discovery, batas bobot, business anomaly vs statistical outlier. Semua ID dari output aktual.
- [x] Pembanding CRM-only vs graph+rules (`evaluation/baseline_crm.py`, hasil `evaluation/results/baseline_latest.{json,md}`), lima deal kanonis yang sama, faktor yang sengaja tidak dipakai didokumentasikan.
- [x] Evaluasi decision/ranking dijalankan ulang di atas main `be628d7`; semua kasus dilaporkan termasuk E15 gagal; kasus dipisah dataset asli / sintetis / mock Jev / replay mock.
- [x] `evaluation/DEMO_CLAIMS.md`: matriks klaim → bukti → batas, klaim terlarang, dampak bisnis sebagai hipotesis, skrip demo 3–5 menit, tanya jawab.
- [x] Smoke HTTP rules lokal (lihat Pengujian aktual).
- [ ] Jev live: **BLOCKED** (lihat Blocker). Tidak menghambat empat deliverable utama.
- Formula ranking, kontrak dan Recommendation v1 **tidak diubah** (freeze selama BOY-04).

Riwayat: ICAL-01/02 merged #7; ICAL-03 merged #15; revisi R8 pada #16 merged 8581de8 (VERIFIED).

## Branch dan commit
ICAL-05: branch `ical/hybrid-deal-analysis` dari `origin/main` 103cfe0 (commit engine 21911c4, 6b255cd, cef5f21 + commit handoff). Route: `bima/hybrid-analysis-route` (stacked). UI: `boy/ical-agent-workspace` (PR #32 diperbarui). Merge berurutan: engine → route → UI.

Branch `ical/evidence-demo-pack` dari `origin/main` `be628d7` (berisi #14/#15/#16/#20/#21). Pekerjaan disusun di sesi Claude cloud; push dari sesi itu ditolak GitHub (403, akses integrasi), sehingga commit dipindahkan ke checkout lokal Ical lewat `git am` dan di-push dari sana. Ownership dicek dengan `scripts/check_handoff.py --branch ical/evidence-demo-pack` (valid). Hash commit dicantumkan di PR/laporan, bukan di sini.
Saat dipasang di laptop Ical, `origin/main` sudah maju ke `2585bb3` (berisi #23 Bima); `git am --3way` bersih tanpa konflik.

## File dan fungsi
ICAL-05: `backend/decision/hybrid.py` (baru: `AnalysisService.analyze`, `AnalysisCache`, `analysis_version`, `context_fingerprint`, `cache_key`, `gate_summary`, `evidence_paths`, `analyze_deal_envelope`); `backend/decision/analyze.py` (`DecisionTrace.fallback_reason`); `backend/integrations/jev_live.py` (2 env key); `backend/integrations/JEV_LIVE.md`; `tests/ical/test_hybrid.py` (17).

- `evaluation/baseline_crm.py` (baru)
  - `rank_crm(rows: list[DealSummary], baseline='stage_value') -> list[dict]`: baseline CRM-only. Hanya membaca baris `list_deals()` (tahap, nilai, umur tahap, owner). Baseline: `stage_value` (utama: tahap lalu nilai), `value_only`, `stage_age` (paling lama di tahap). Tindakan = template generik per tahap (`GENERIC_ACTION`) buatan Ical; `approval_visible`/`obstacle_visible` = None.
  - `graph_rules(deal_ids) -> (envelope, obstacles)`: `rank_deals` production di atas `build_deal_context` + `analyze_deal_initial` nyata; `main_obstacle` dari `analyze_deal_trace(mode='rules')`.
  - `compare(rows, envelope, obstacles) -> dict`: per deal rank CRM vs G+R, tindakan, hambatan + bukti, gate, approval, preseden, jumlah bukti/path, file sumber tambahan; ringkasan dan `limits`. `same_order_as_graph_rules` dihitung, bukan diklaim.
  - `run()`, `to_markdown()`, CLI `python -m evaluation.baseline_crm [--no-write]`.
- `evaluation/run_eval.py`: `decision_source(case)`, `ranking_source(case)`, `by_source(rows)`; field `source` per kasus dan tabel per sumber di markdown; kalimat "bukan holdout independen". Hitungan dan pemeriksaan kasus tidak berubah.
- `evaluation/MENTOR_BRIEF.md`, `evaluation/DEMO_CLAIMS.md` (baru); `evaluation/README.md` diperbarui.
- `evaluation/results/*`: dihasilkan ulang (latest, ranking_latest, baseline_latest).
- `tests/ical/test_baseline.py` (8 tes), `tests/ical/test_eval_sources.py` (2 tes).
- Tidak ada perubahan di `backend/decision/`, `backend/integrations/`, kontrak, route, frontend, dataset.

### Hasil pembanding (aktual)
| Metode | Urutan |
|---|---|
| graph+rules | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 |
| CRM tahap lalu nilai (utama) | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 (**sama**) |
| CRM nilai saja | DL-001 > DL-005 > DL-004 > DL-002 > DL-003 |
| CRM paling lama di tahap | DL-002 > DL-004 > DL-001 > DL-003 > DL-005 |

Perbedaan graph+rules vs baseline utama: hambatan bersumber 4/5 deal (I0335, I0343, I0296+I0348, I0334; P05 tidak ada), gate approval VP Sales 1 (DL-002) vs 0, jumlah bukti CRM 2 → G+R 10/9/15/23/2 (P04/P01/P02/P03/P05), sumber tambahan pada DL-004/001/002/003; P05 tidak mendapat sumber tambahan.

## Kontrak dan dependency
Kontrak v1 dan `PHASE3_CONTRACT.md` diikuti tanpa perubahan. Baseline memakai `backend.ingestion.deals.list_deals` (Bima) dan produsen konteks/diagnostic Bima hanya lewat import; tidak ada ingest duplikat. Tidak ada dependency baru. Tidak ada permintaan perubahan kontrak.
Catatan untuk Main/Boy: bila UI menampilkan pembanding, sumber datanya `evaluation/results/baseline_latest.json` (offline, bukan endpoint). Tidak ada usulan endpoint baru selama freeze.

## Cara menjalankan
```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m evaluation.run_eval
python -m evaluation.baseline_crm
# demo rules (tanpa key):
DEALCOMPASS_ENGINE_MODE=rules python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
curl -s http://127.0.0.1:8000/api/pipeline/priorities | python -m json.tool | head -60
cd frontend && npm ci && npm run dev
```
Env: `DEALCOMPASS_ENGINE_MODE` (rules/jev/replay/auto), `TYPESAFE_API_KEY`, `TYPESAFE_MODEL`, `TYPESAFE_BASE_URL`, `TYPESAFE_TIMEOUT_S`, `DEALCOMPASS_REPLAY_DIR`, `DEALCOMPASS_RECORD_DIR` (nama saja; tidak ada nilai di repo). Windows: `PYTHONUTF8=1` untuk `check_handoff.py`.

## Pengujian aktual
2026-10-09 ±19:57–20:05 WIB, Linux, Python 3.13.16 (CI memakai 3.12):
- `DEALCOMPASS_ENGINE_MODE=rules python -m unittest discover -s tests` → `Ran 154 tests, OK` (144 sebelumnya + 10 baru). Diulang tanpa env mode → `Ran 154 tests, OK`.
- `python -m evaluation.run_eval` → decision **34/35** (inti 34/34; **E15 gagal**: "KasirPro lebih ramah di kantong" tidak terdeteksi harga, batas parafrase diketahui); ranking **15/15**.
  - Decision per sumber: dataset asli 7/7 (E01, E09, E11, E12, E27, E29, E30); sintetis 16/17 (gagal E15); mock Jev 9/9 (E16–E24); replay mock 2/2 (E25, E26).
  - Ranking per sumber: dataset asli 5/5 (K01, K02, K13, K14, K15); sintetis 10/10 (K03–K12).
  - Benchmark disusun bersama pengembangan rules: **bukan holdout independen**, bukan validasi closing.
- `python -m evaluation.baseline_crm` → hasil di atas; `tests/ical/test_baseline.py` 8/8, `tests/ical/test_eval_sources.py` 2/2.
- Smoke HTTP lokal uvicorn port 8131, `DEALCOMPASS_ENGINE_MODE=rules`, tanpa key: `/health` 200; `/api/pipeline/priorities` 200 (3,95 dtk request pertama, cold); `/api/pipeline/initial-analysis` 200 (0,75 dtk); `/api/deals/DL-002/initial-analysis` 200; `DL-999` 404; `POST /api/deals/DL-002/analyze` 200 `engine_mode=rules` dengan approval VP Sales. Urutan HTTP P04→P01→P02→P03→P05. Server dihentikan. Observasi lokal, bukan SLA.
- `python scripts/check_handoff.py --all` dan `--base origin/main --head HEAD --branch ical/evidence-demo-pack` → valid.
- Ulang di laptop Ical (Windows, Python 3.11.9, di atas `2585bb3`, ±20:25 WIB): `DEALCOMPASS_ENGINE_MODE=rules python -m unittest discover -s tests` → `Ran 174 tests, OK` (main kini memuat tes tambahan); `python -m evaluation.baseline_crm --no-write` → urutan sama seperti di atas; `check_handoff.py --all` dan `--base origin/main --head HEAD --branch ical/evidence-demo-pack` → valid.
- Belum: browser/UI ranking (menunggu BOY-04), Jev live, CI pada PR.

## Fixture dan keterbatasan
- Mode yang benar: ranking selalu **rules**; decision rules untuk lima deal nyata; Jev hanya **mock** (E16–E24) dan **replay** rekaman mock (E25–E26); **live tidak pernah dieksekusi**.
- Tidak ada fixture tulisan tangan; mutasi kasus diberi label sintetis pada salinan konteks. Dataset asli tidak diubah.
- Baseline: lima deal, satu snapshot, tanpa label hasil; urutan sama/berbeda bukan bukti akurasi; tindakan baseline template buatan Ical, bukan perilaku CRM/sales nyata; kolom `kompetitor` sengaja tidak dipakai.
- Bobot ranking pilihan desain, belum dikalibrasi sales/closing; rank 1–2 sensitif bobot; deteksi hambatan leksikal (E15).
- Dampak bisnis di DEMO_CLAIMS adalah hipotesis H1–H4, belum diukur.

## Blocker
ICAL-05: live Jev tidak dapat diverifikasi dari laptop ini (tidak ada key/ledger tim); butuh Main di host ledger tim.

- **Jev live — BLOCKED.** `TYPESAFE_API_KEY` dan `TYPESAFE_BASE_URL` tidak di-set di environment sesi ini (dicek hanya ada/tidak, nilai tidak ditampilkan), tidak ada `.env` (hanya `.env.example` kosong), dan tidak ada credential resmi atau izin provider yang diberikan. Smoke live tidak dijalankan; tidak ada request ke provider (request count 0). Dampak: tidak ada klaim Jev live/confidence; core rules dan empat deliverable tidak terdampak. Butuh: credential uji resmi diset di env backend oleh pihak berwenang, lalu smoke terbatas ≤20 menit via `analyze_deal` (bukan GET priorities/diagnostic).
- Tidak ada blocker lain untuk deliverable utama ICAL-04.

## Tugas berikutnya
ICAL-05: Main review & merge engine → route → UI; live smoke terkontrol P02 di host ledger (usage sebelum/sesudah, kunjungan kedua harus cache hit, P05 nol request); catat di API_CONTRACT.

1. Main: review paket ICAL-04 (MENTOR_BRIEF, DEMO_CLAIMS, baseline, eval per sumber); putuskan apakah pembanding ditampilkan di demo/UI.
2. Ical: rehearsal bagian alasan ranking/policy bersama tim setelah BOY-04; latih jawaban P04/P01, P02, P05.
3. Ical: Jev live smoke bila credential resmi tersedia; catat request count, mode, error, latensi tanpa header auth.
4. Setelah lomba (opsional): holdout terpisah, masukan sales untuk bobot, perbaikan parafrase E15 — bukan sebelum demo (freeze).

## Update WIB
2026-10-10 03:50 WIB (Ical via Claude) — ICAL-05 READY_FOR_REVIEW.
2026-10-09 20:05 WIB (Ical via Claude).
