# Handoff ICAL

## Task dan status
ICAL-01 (issue #3): READY_FOR_REVIEW (sebagian). Main yang memverifikasi.
- [x] `analyze_deal(context) -> Recommendation` sesuai kontrak v1; P02 sebagai kasus integrasi pertama.
- [x] Policy gate deterministik: diskon >10% butuh approval VP Sales + pencatatan; permintaan (I0348) bukan approval.
- [x] Preseden P02: D-2025-02 (20% ditolak) dan D-2025-06 (Starter tanpa diskon, pilot 6 outlet) dibandingkan; Starter (maks 10) tidak menampung 15 outlet; pilot ditandai SKENARIO_USULAN.
- [x] Adapter Jev (TypeSafe) sesuai dokumentasi resmi; mode jev/rules/replay eksplisit.
- [x] 21 kasus evaluasi dengan hasil aktual (20/20 inti lulus; 1 batas diketahui gagal).
- [x] Analisis awal P01, P03, P04, P05 pada fixture (rules).
- [ ] Integrasi live Jev: BELUM DIUJI (tidak ada TYPESAFE_API_KEY).
- [ ] Uji ulang dengan graph Bima (`build_deal_context` masih stub di main dan `origin/bima/data-graph`).
- [ ] Ranking lintas deal: belum; menunggu persetujuan Main atas perubahan kontrak.

## Branch dan commit
Branch `ical/decision-jev`, basis `a914cad` (main sudah di-merge, "Already up to date").
Commit pekerjaan ini dibuat setelah catatan ini; hash dilihat di PR. Tidak ada hash rekaan.

## File dan fungsi
- `backend/decision/analyze.py`
  - `analyze_deal(context: DealContext) -> Recommendation` (fungsi kontrak).
  - `analyze_deal_trace(context, mode=None, client=None) -> (Recommendation, DecisionTrace)`: jejak lengkap (facts, interpretations, proposals, scenarios, calculations, obstacles, precedents, validation_issues, jev_calls, analysis_status).
  - `resolve_mode()`, `validate_context()`; playbook hambatan `harga`, `pengambil_keputusan`, `referensi`; selain itu discovery + `insufficient_evidence`.
- `backend/decision/policy.py`: harga Rp350.000/outlet/bulan (contracts_billing), batas paket Starter 10/Growth 25/Enterprise tanpa batas (README dataset), ambang diskon 10% → VP Sales; hitungan rupiah integer dan tanggal stage.
- `backend/decision/signals.py`: klasifikasi hambatan per pesan (kriteria juga dipakai Choice Jev), ekstraksi permintaan diskon, selisih harga kompetitor, keputusan diskon untuk deal; jabatan VP Sales diverifikasi dari bukti employees.csv di konteks.
- `backend/decision/precedents.py`: `assess()` per candidate decision → fit cocok/sebagian/tidak_cocok + fakta/interpretasi/skenario.
- `backend/integrations/jev.py`: `JevClient`, `ReplayClient`, `client_from_env`, builder `choice/score/noul`, `JevError`.
- `evaluation/fixtures/*.json`, `evaluation/cases.py`, `evaluation/run_eval.py`, `evaluation/results/latest.{json,md}`, `evaluation/README.md`.
- `tests/ical/test_decision.py`: 15 tes (policy, provenance fixture, kasus evaluasi, mode, adapter Jev, route analyze dengan fixture).

Pemisahan keluaran pada kontrak v1: `action` diawali `USULAN:`; `precedent_comparison` berisi baris `FAKTA | …`, `INTERPRETASI | […]`, `SKENARIO | …`; celah bukti/kegagalan mesin di `unknowns`.

Hasil P02 (rules, fixture): hambatan harga; approval VP Sales tertunda untuk 20% (I0348); 15 × Rp350.000 × 12 = Rp63.000.000 → diskon 20% = Rp50.400.000 (turun Rp12.600.000); paket minimum Growth; skenario pilot maks 10 outlet Starter = Rp42.000.000/tahun, 5 outlet sisanya butuh Growth; batas 15% di D-2025-02 dicatat bukan aturan universal.

## Kontrak dan dependency
Kontrak v1 (`backend/contracts.py`) tidak diubah. Tidak ada dependency baru (pakai `httpx` yang sudah ada).
Usulan ke Main (belum diterapkan):
1. Field `facts/interpretations/scenarios` terpisah di Recommendation atau endpoint trace; sekarang memakai prefix teks.
2. `analysis_status` dari `DecisionTrace` (ready/insufficient_evidence) dipetakan Bima ke DealSummary.
3. Tambah ke `.env.example` (nama saja): `DEALCOMPASS_ENGINE_MODE` (auto|rules|jev|replay), `TYPESAFE_BASE_URL`, `TYPESAFE_TIMEOUT_S`, `DEALCOMPASS_REPLAY_DIR`, `DEALCOMPASS_RECORD_DIR`. Sudah ada: `TYPESAFE_API_KEY`, `TYPESAFE_MODEL`.
4. Untuk Bima, engine membaca dari DealContext: node `type` competitor/kompetitor; relasi edge `pengambil_keputusan`, `pernah_bekerja_di`, `kandidat_referensi`, `overlap_kerja`; evidence employees.csv berisi jabatan VP Sales; evidence `crm_deals.csv` untuk deal preseden (kolom kompetitor). Nama relasi perlu disepakati; jika berbeda, engine disesuaikan.

## Cara menjalankan
```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt   # Windows; Linux: .venv/bin/python
python -m unittest discover -s tests -v
python -m evaluation.run_eval                     # tulis evaluation/results/latest.*
python -m backend.decision.analyze evaluation/fixtures/DL-002.json   # cetak rekomendasi + trace
```
Jev live (belum diuji): set `TYPESAFE_API_KEY` di env backend (jangan di repo), `DEALCOMPASS_ENGINE_MODE=jev`; rekam respons dengan `DEALCOMPASS_RECORD_DIR`, putar ulang dengan `DEALCOMPASS_ENGINE_MODE=replay DEALCOMPASS_REPLAY_DIR=<dir>`.

## Pengujian aktual
2026-10-09 ±16:23 WIB, Windows, Python 3.11.9 (CI memakai 3.12; belum dijalankan di CI):
- `python -m unittest discover -s tests -v` → `Ran 25 tests … OK` (10 bootstrap/handoff + 15 ical).
- `python -m evaluation.run_eval` → 20/21 lulus; inti 20/20; E12 (parafrase "lebih ramah di kantong") gagal = batas rules diketahui; invarian lima fixture benar (evidence_ids valid, precedent_ids dari candidate_decisions, action berlabel USULAN).
- `python scripts/check_handoff.py --all` → `Handoff valid.`
- Belum dijalankan: Jev live, graph Bima, CI GitHub, build frontend (bukan area Ical).

## Fixture dan keterbatasan
- Konteks = `FIXTURE_ICAL_SEMENTARA` (DL-001..DL-005) dari record asli, bukan graph Bima. Excerpt direct terverifikasi verbatim; satu evidence inferred (overlap K028–K116) diberi label inferred.
- Mode aktual seluruh hasil: `rules`. Kasus `jev`/`replay` memakai transport mock dan bukan bukti integrasi live.
- Jev hanya: Choice hambatan per pesan, Score kecocokan preseden, Noul klaim approval eksplisit. Confidence/score Jev tidak ditampilkan sebagai probabilitas closing. Policy diskon tidak pernah diserahkan ke Jev.
- Klasifikasi rules berbasis kata kunci; parafrase tanpa kata kunci terlewat (E12).
- P03/P04: kandidat referensi dari fixture adalah inferensi; tiket/usage C06, C09, C17 belum diperiksa. P05: bukti tidak cukup; kemiripan nama dengan C11 sengaja tidak dipakai.
- Tidak ada ranking, probabilitas closing, atau tanggal target rekaan.

## Blocker
- `build_deal_context` belum tersedia (Bima). Dampak: integrasi end-to-end dan coverage MAIN.md belum dapat diverifikasi.
- `TYPESAFE_API_KEY` tidak tersedia di lingkungan ini. Dampak: Jev live belum diuji. Butuh key di env backend Main/Ical.

## Tugas berikutnya
1. Uji ulang `analyze_deal` dengan `build_deal_context` Bima untuk DL-001..DL-005; sesuaikan nama relasi; ulangi `run_eval`.
2. Uji Jev live dengan key; rekam replay; catat model/latensi aktual; bandingkan rules vs Jev pada E11/E12.
3. Usulan ranking lintas deal transparan (setelah persetujuan Main atas kontrak).
4. Tambah pembanding CRM-only dan set holdout.

## Update WIB
2026-10-09 16:25 WIB (Ical via Claude).
