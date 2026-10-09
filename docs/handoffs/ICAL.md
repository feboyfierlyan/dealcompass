# Handoff ICAL

## Task dan status
ICAL-03 (ranking prioritas, `docs/prompts/ICAL-03.md`, kontrak `docs/coordination/PHASE3_CONTRACT.md`): **READY_FOR_REVIEW**. Main yang memverifikasi dan merge; Ical tidak merge sendiri.
- [x] `backend/decision/ranking.py:rank_deals(contexts, diagnostics) -> dict` sesuai signature dan envelope kontrak fase 3 (schema_version, snapshot_date, engine_mode `rules`, methodology + weights, items, limitations).
- [x] Kelima deal nyata P01–P05 dibandingkan dengan metode deterministik `deal-priority-heuristic-v1`; faktor, bobot, tie-break, tradeoff dan sensitivitas dijelaskan (output + `evaluation/ranking.md`). Tidak ada daftar ID atau urutan hardcoded; tidak memakai nominal saja.
- [x] Tiap item memuat rank 1..N, priority_kind, analysis_status (dari trace rules), rationale pembandingan, factors bersumber, Recommendation v1 (`engine_mode='rules'`), approval/gate, evidence lengkap dan evidence_paths dari edge asli graph konteks.
- [x] P05 = discovery + insufficient_evidence + tindakan discovery; dinyatakan bukan peluang buruk/kalah/risiko rendah. Rank bukan probabilitas closing.
- [x] Referensi P03/P04 diselaraskan dengan verifikasi BIMA-02 (lihat File dan fungsi). Kandidat dan overlap kerja bukan izin/saling kenal.
- [x] Regresi approval R1–R3/R5/R6/R7 tetap lulus; gate approval diuji terpisah dari rank (nilai besar, R6, R7, kontrol sah).
- [x] Tes: input diacak, tie, ID ditukar, nilai besar dengan bukti kurang, faktor berubah, missing data, input invalid, evidence/path, tanpa Jev, lima deal nyata.
- [ ] Jev live: BELUM DIUJI. Ranking tidak memakai Jev (sesuai kontrak).
- [ ] Integrasi HTTP `GET /api/pipeline/priorities`: milik Bima (BIMA-03); belum diuji bersama dari sisi Ical.

Riwayat: ICAL-01/02 merged di PR #7 (`cef7e7c`), R6/R7 VERIFIED Main pada `3e90711`.

## Branch dan commit
Branch `ical/priority-ranking` dibuat dari `origin/main` `712acf9` (berisi kontrak fase 3 dan BIMA-02 merged). Checkout lokal bersih sebelum mulai; branch lama `ical/decision-jev` tidak punya commit yang belum masuk main. Commit kode ICAL-03 dibuat bersama catatan ini; hash dicantumkan di PR baru (bukan PR #7).

## File dan fungsi
- `backend/decision/ranking.py` (baru)
  - `rank_deals(contexts: list[DealContext], diagnostics: list[dict]) -> dict`. Input: DealContext (atau dict valid) dan laporan `analyze_deal_initial` Bima, dipasangkan per `deal_id`. Output: envelope kontrak fase 3, JSON strict (`allow_nan=False`).
  - Validasi `ValueError`: list kosong/bukan list, deal_id duplikat, set deal berbeda, snapshot campuran/selain 2026-10-01, account_id diagnostic ≠ konteks, evidence ID sama isi berbeda (registry union context+diagnostic), evidence dirujuk tak ter-resolve, diagnostic tanpa deal_id.
  - `path_is_valid(graph, path)`: setiap pasangan node berurutan dihubungkan edge asli yang disebut (arah edge tidak diubah; boleh dilalui berlawanan), bukti path ⊆ bukti edge.
  - Jalur yang dibangun (BFS deterministik, relasi dibatasi): deal→akun→interaksi hambatan; permintaan→email→VP Sales; deal→keputusan preseden (`candidate_precedent_*`)→deal preseden; deal→akun→kontak pengambil keputusan→akun sebelumnya→keputusan→fitur; deal→kandidat referensi (`related_account_*`); permintaan→fitur→usage bulan lengkap→kandidat; akun→kontak→kontak overlap→kandidat.
- `backend/decision/analyze.py`
  - `analyze_deal_trace(context, mode=None, client=None, diagnostic=None)`: parameter baru opsional `diagnostic` (laporan Bima deal yang sama; deal_id beda → ValueError). `analyze_deal(context)` dan Recommendation v1 tidak berubah.
  - Referensi (`_reference_candidates`, `_reference`): kandidat dari `related_account_*`; tidak lagi menolak berdasarkan health dashboard saja. Catatan material (tiket bug/prioritas Tinggi terbuka, komitmen terbuka, usage 0 bulan lengkap terakhir) → dicek belakangan; catatan minor (health non-Hijau sebagai indikator CRM, industri berbeda, tiket non-bug terbuka, usage missing) → tetap dicek. Status `cek_pertama`/`cadangan`/`cek_dengan_catatan` = urutan pemeriksaan AM, bukan kelayakan. Usage = bulan lengkap terakhir (2026-09), recorded/zero/missing dibedakan; dengan diagnostic dicocokkan ke `feature_usage` Bima (Bima menang bila beda, dicatat). Overlap dari `work_overlap_paths` Bima, `acquaintance_confirmed` null. `suitability`/`reference_willingness`/`contact_consent` diteruskan null → unknown.
  - Pengambil keputusan: bila diagnostic ada, dicek terhadap `authority_contact_id` Bima (P01: sama, K017, tetap inferred). Harga: ringkasan `decision_lookup` Bima ditampilkan (P02: 0 log fokus).
- `evaluation/ranking_cases.py` (baru): 15 kasus ranking + helper (`real_inputs`, `swap_ids`, `clone_deal`, `set_isi`, `contract_violations`, `sensitivity_table`).
- `evaluation/ranking.md` (baru): metode, bobot, tie-break, tradeoff, hasil, sensitivitas, keterbatasan.
- `evaluation/run_eval.py`: menulis juga `results/ranking_latest.{json,md}`. `evaluation/cases.py`: E29/E30 disesuaikan ke perilaku referensi baru. `evaluation/README.md` diperbarui.
- `tests/ical/test_ranking.py` (baru, 9 tes); `tests/ical/test_decision.py` (status referensi baru, izin null).

### Metode ranking (ringkas)
Tier: `ready` → acceleration (diskor), `insufficient_evidence` → discovery (setelah acceleration, tanpa skor). Skor acceleration 0–10 = tahap (Lead 0 … Negosiasi 4) + nilai potensi (≥200jt 3, ≥100jt 2, ≥50jt 1) + hambatan dinyatakan pelanggan (tunda/syarat 2, hambatan 1, internal saja 0) + preseden relevan (0/1). Tie-break: hambatan pelanggan, tahap, nilai, deal_id (determinisme saja). Konteks tidak dihitung: umur tahap, interaksi eksternal terakhir, gate approval/izin. Unknown = 0 poin + dicatat, termasuk kemungkinan naik rank.

Hasil aktual (graph + diagnostic nyata): 1 DL-004/P04 (8), 2 DL-001/P01 (8, kalah tie-break hambatan pelanggan 1 vs 2), 3 DL-002/P02 (5, gate VP Sales E01 untuk diskon 20% I0348), 4 DL-003/P03 (2), 5 DL-005/P05 (discovery). Sensitivitas: tanpa tahap, tanpa hambatan pelanggan, atau nilai ×2 → P01 menjadi rank 1; rank 3–5 stabil di semua variasi.

## Kontrak dan dependency
Kontrak v1 dan `PHASE3_CONTRACT.md` diikuti; `backend/contracts.py`, route, graph Bima, frontend, CI, manifest dan dataset tidak diubah. Tidak ada dependency baru. Fungsi Ical memakai produsen Bima (`build_deal_context`, `analyze_deal_initial`) hanya lewat input; tes memakai keduanya untuk data nyata.
Catatan integrasi untuk Bima/Main:
- Item hanya memuat field wajib kontrak (tanpa field tambahan); skor ada di factor `skor_prioritas` dan bobot di `methodology.weights`.
- Registry bukti ketat: record dengan ID sama tetapi isi beda antara context dan diagnostic → ValueError (adapter sebaiknya memetakan ke 503 PRIORITIES_UNAVAILABLE). Pada data nyata tidak ada konflik.
- Usulan (belum diterapkan): tampilkan `priority_kind` dan gate di UI terpisah dari rank; `analysis_status` daftar lama tetap tidak diubah sepihak.

## Cara menjalankan
```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m evaluation.run_eval
python -c "import json; from backend.graph.context import build_deal_context as b; from backend.graph.analysis import analyze_deal_initial as a; from backend.decision.ranking import rank_deals; c=[b(f'DL-00{i}') for i in range(1,6)]; print(json.dumps(rank_deals(c,[a(x) for x in c]), ensure_ascii=False, indent=2)[:3000])"
```
Windows: set `PYTHONUTF8=1` untuk `scripts/check_handoff.py --all` (decode cp1252; CI Linux tidak terdampak). Tidak ada env tambahan untuk ranking; ranking selalu rules.

## Pengujian aktual
2026-10-09 ±18:40 WIB, Windows, Python 3.11.9 (CI Python 3.12 berjalan saat PR dibuka):
- `DEALCOMPASS_ENGINE_MODE=rules python -m unittest discover -s tests` → `Ran 108 tests, OK` (Bima 65, Ical 33 = decision 24 + ranking 9, bootstrap/handoff 10). Diulang tanpa env mode → `Ran 108 tests, OK`.
- `python -m evaluation.run_eval` → decision 34/35 (inti 34/34; E15 batas parafrase diketahui); ranking 15/15. Hasil di `evaluation/results/latest.md` dan `ranking_latest.md`.
- Pemisahan: **dataset nyata** (lima deal, shuffle, tanpa Jev, referensi, sensitivitas, kontrak/path/bukti ke row sumber via `lookup_evidence`); **mutasi sintetis** (tukar ID DL-001↔DL-004/P01↔P04, tie salinan DL-003→DL-903, nilai P05 Rp10M, tahap P03 Negosiasi, I0335 tanpa "tunda", nilai P02 Rp10M, R6 DL-OLD, R7 nilai kosong, kontrol approval sah, tahap tidak dikenal + metrics hilang); **mock/replay Jev** hanya pada evaluasi decision E16–E26; **live** tidak dijalankan.
- Waktu terukur: konteks lima deal cold ±2,2 dtk (Bima), diagnostic ±0,01 dtk, `rank_deals` ±0,17–0,21 dtk.
- `PYTHONUTF8=1 python scripts/check_handoff.py --all` dan `--base origin/main --head HEAD --branch ical/priority-ranking` → valid (dijalankan sebelum push).
- Belum: HTTP `/api/pipeline/priorities` (route Bima), UI, Jev live.

## Fixture dan keterbatasan
- Tidak ada fixture tulisan tangan; semua data dari produsen Bima. Mutasi kasus diberi label sintetis.
- Mode: ranking selalu `rules`. Jev mock/replay hanya di evaluasi decision; Jev live belum pernah dieksekusi.
- Bobot/bin pilihan desain, belum divalidasi terhadap hasil closing historis; satu snapshot, tidak ada backtest.
- Rank 1–2 (P04/P01) sensitif terhadap bobot; dicatat di output dan `evaluation/ranking.md`.
- Deteksi hambatan pelanggan, tunda/syarat dan hambatan pesan bersifat leksikal.
- Kandidat referensi: kesesuaian, kesediaan, izin kontak null; health dashboard hanya indikator CRM. Identitas P01 inferred.
- Nilai deal = potensi CRM; P05 belum divalidasi percakapan.

## Blocker
- Jev live: `TYPESAFE_API_KEY` tidak ada di environment sesi ini dan tidak ada `.env`; tidak ada mekanisme credential uji yang diberikan. Dampak: smoke live belum bisa; ranking tidak terdampak (rules). Butuh: credential uji melalui env backend oleh pihak berwenang.
- Tidak ada blocker kode untuk ICAL-03.

## Tugas berikutnya
1. Main: review metode/bobot/rationale ranking dan PR baru; smoke gabungan dengan route priorities Bima.
2. Bima: hubungkan `GET /api/pipeline/priorities` ke `rank_deals`; ValueError → 503 PRIORITIES_UNAVAILABLE.
3. Boy: tampilkan rank + priority_kind + gate + path setelah Main merge (BOY-04).
4. Ical: Jev live smoke bila credential tersedia; holdout/pembanding CRM-only; bila Main meminta, kalibrasi bobot dengan masukan sales (bukan demi urutan demo).

## Update WIB
2026-10-09 18:45 WIB (Ical via Claude).
