# Handoff ICAL

## Task dan status
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
Branch `ical/evidence-demo-pack` dari `origin/main` `be628d7` (berisi #14/#15/#16/#20/#21). Pekerjaan disusun di sesi Claude cloud; push dari sesi itu ditolak GitHub (403, akses integrasi), sehingga commit dipindahkan ke checkout lokal Ical lewat `git am` dan di-push dari sana. Ownership dicek dengan `scripts/check_handoff.py --branch ical/evidence-demo-pack` (valid). Hash commit dicantumkan di PR/laporan, bukan di sini.

## File dan fungsi
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
- Belum: browser/UI ranking (menunggu BOY-04), Jev live, CI pada PR.

## Fixture dan keterbatasan
- Mode yang benar: ranking selalu **rules**; decision rules untuk lima deal nyata; Jev hanya **mock** (E16–E24) dan **replay** rekaman mock (E25–E26); **live tidak pernah dieksekusi**.
- Tidak ada fixture tulisan tangan; mutasi kasus diberi label sintetis pada salinan konteks. Dataset asli tidak diubah.
- Baseline: lima deal, satu snapshot, tanpa label hasil; urutan sama/berbeda bukan bukti akurasi; tindakan baseline template buatan Ical, bukan perilaku CRM/sales nyata; kolom `kompetitor` sengaja tidak dipakai.
- Bobot ranking pilihan desain, belum dikalibrasi sales/closing; rank 1–2 sensitif bobot; deteksi hambatan leksikal (E15).
- Dampak bisnis di DEMO_CLAIMS adalah hipotesis H1–H4, belum diukur.

## Blocker
- **Jev live — BLOCKED.** `TYPESAFE_API_KEY` dan `TYPESAFE_BASE_URL` tidak di-set di environment sesi ini (dicek hanya ada/tidak, nilai tidak ditampilkan), tidak ada `.env` (hanya `.env.example` kosong), dan tidak ada credential resmi atau izin provider yang diberikan. Smoke live tidak dijalankan; tidak ada request ke provider (request count 0). Dampak: tidak ada klaim Jev live/confidence; core rules dan empat deliverable tidak terdampak. Butuh: credential uji resmi diset di env backend oleh pihak berwenang, lalu smoke terbatas ≤20 menit via `analyze_deal` (bukan GET priorities/diagnostic).
- Tidak ada blocker lain untuk deliverable utama ICAL-04.

## Tugas berikutnya
1. Main: review paket ICAL-04 (MENTOR_BRIEF, DEMO_CLAIMS, baseline, eval per sumber); putuskan apakah pembanding ditampilkan di demo/UI.
2. Ical: rehearsal bagian alasan ranking/policy bersama tim setelah BOY-04; latih jawaban P04/P01, P02, P05.
3. Ical: Jev live smoke bila credential resmi tersedia; catat request count, mode, error, latensi tanpa header auth.
4. Setelah lomba (opsional): holdout terpisah, masukan sales untuk bobot, perbaikan parafrase E15 — bukan sebelum demo (freeze).

## Update WIB
2026-10-09 20:05 WIB (Ical via Claude).
