# Handoff ICAL

## Task dan status
ICAL-02 (revisi PR #7, review R1/R2/R3/R5): READY_FOR_REVIEW. Main yang memverifikasi.
- [x] R1: hambatan, permintaan, approval hanya dari akun/deal fokus (`account_id` interaksi = `context.deal.account_id`; decision `deal_id`/`account_id` fokus). Bukti akun lain hanya untuk preseden/kandidat referensi. P02 nyata: satu mention `I0348 20% request`; I0054/I0061/I0066 (C01) tidak dipakai.
- [x] R2: excerpt dibaca sebagai JSON object (`backend/decision/records.py`); `isi` = pesan, `account_id` pemilik, `jabatan`/`kompetitor` dari field. Tidak ada split koma. E01 = VP Sales; KasirPro terbaca untuk DL-002, DL-006, DL-007.
- [x] R1: permintaan dideduplikasi per (interaksi, persentase); dibedakan `request` / `approval_claim` / `rejection_claim` (klaim di pesan) vs keputusan tercatat Disetujui/Ditolak/Menunggu di decision_log dengan verifikasi jabatan pemutus.
- [x] R3: relasi produsen (`related_account_*`, `employed_at`, `overlapping_employment`, `interaction_for`, `candidate_precedent_*`). P03: C09/C17 diusulkan, C03/C27 ditolak dengan alasan. P04: C06 (work_overlap) diusulkan, overlap dinyatakan bukan bukti saling kenal. P01: K017 Rina Hapsari sebagai inferensi (I0343 + kontak CRM + riwayat kerja), ambigu → tidak ditebak.
- [x] R5: validasi angka Jev (finite, bukan bool, noul 0..1, score 0..n-1, confidence/probabilities 0..1), respons/rekaman replay rusak → `JevError`, error tak terduga → fallback. Fallback mengulang seluruh analisis dalam rules. Anggaran waktu total `DEALCOMPASS_ANALYSIS_BUDGET_S` default 15 dtk (< batas UI 20 dtk); Jev hanya dipanggil untuk pesan fokus (P02: 4) dan preseden relevan.
- [x] Tes integrasi wajib dengan `build_deal_context` nyata (lihat Pengujian aktual).
- [ ] Jev live: BELUM DIUJI (tidak ada `TYPESAFE_API_KEY`).
- [ ] Ranking lintas deal dan pemetaan `analysis_status`: belum; menunggu Main.

## Branch dan commit
Branch `ical/decision-jev`, PR #7. Commit kode ICAL-01: `9557c83`. Merge `origin/main` (`ddf7a2a`, berisi graph Bima #6) di `96fc7d8`. Commit revisi ICAL-02 dibuat setelah catatan ini; hash dilihat di PR.

## File dan fungsi
- `backend/decision/records.py` (baru): `parse(EvidenceRecord) -> Record` (field JSON, `text`=isi interaksi), `ContextIndex` (focus_interactions, focus_decisions, competitor_of, employee_title, vp_sales_ids, related_accounts, contacts_at, employment).
- `backend/decision/signals.py`: `extract(idx) -> Signals` (obstacles, discount_mentions dedup + kind, competitor_gaps, competitor, discount_decisions dengan approver_title, vp_sales_ids). Kriteria `OBSTACLES` juga dipakai Choice Jev.
- `backend/decision/precedents.py`: `assess(idx, decision, signals, trust_accounts)` → skor transparan (pemohon sama +1, kompetitor sama +2, persentase sama +2 / sama-sama >10% +1, paket +1, komitmen terbuka di akun riwayat pengambil keputusan +2); cocok ≥3, sebagian ≥2. Starter vs outlet → `SKENARIO_USULAN`.
- `backend/decision/analyze.py`: `analyze_deal(context) -> Recommendation`; `analyze_deal_trace(context, mode=None, client=None) -> (Recommendation, DecisionTrace)`; playbook `harga`, `pengambil_keputusan`, `referensi`, selain itu discovery + `insufficient_evidence`. Trace menambah `discount_mentions`, `reference_candidates` (shortlist/ditolak + alasan), `decision_maker` (inferred), `elapsed_ms`.
- `backend/integrations/jev.py`: validasi ketat, `ask(..., timeout_s)` untuk anggaran, replay rusak → `invalid_replay`.
- `evaluation/cases.py`, `evaluation/run_eval.py`, `evaluation/results/latest.{json,md}`, `evaluation/README.md`. `evaluation/fixtures/` dihapus.
- `tests/ical/test_decision.py`: 21 tes (9 integrasi graph nyata).

Keluaran tetap kontrak v1: `action` diawali `USULAN:`; `precedent_comparison` berbaris `FAKTA |`, `INTERPRETASI |`, `SKENARIO |`.

P02 nyata (rules): hambatan harga; approval tertunda `VP Sales (E01)` untuk 20% (I0348); 15 × Rp350.000 × 12 = Rp63.000.000 → Rp50.400.000 (turun Rp12.600.000); paket minimum Growth; preseden D-2025-02 (cocok), D-2025-06 (sebagian, Starter maks 10 → pilot ≤10 Rp42.000.000/th skenario), D-2024-02, D-2025-12, D-2026-04 (sebagian); 8 keputusan lain diperiksa dan tidak dipakai; ringkasan 6 keputusan diskon >10% di konteks: 1 disetujui, 5 ditolak.

## Kontrak dan dependency
Kontrak v1 dan klarifikasi Main (API_CONTRACT.md) diikuti; tidak ada perubahan schema/dependency.
Usulan ke Main (belum diterapkan): field fakta/interpretasi terpisah atau endpoint trace; pemetaan `analysis_status` dari `DecisionTrace`; nama env di `.env.example`: `DEALCOMPASS_ENGINE_MODE`, `DEALCOMPASS_ANALYSIS_BUDGET_S`, `TYPESAFE_BASE_URL`, `TYPESAFE_TIMEOUT_S`, `DEALCOMPASS_REPLAY_DIR`, `DEALCOMPASS_RECORD_DIR` (nilai tidak dicatat).
Untuk Bima: konteks DL-004 tidak memuat `employees.csv:E01`, jadi bila nanti ada permintaan diskon P04 jabatan VP Sales tidak dapat diverifikasi (engine akan menyatakannya di unknowns). Data: `crm_accounts` C01 masih mencatat K017 sebagai champion padahal K017 keluar 2026-08-15 (anomali sumber, belum dipakai sebagai fakta).

## Cara menjalankan
```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m evaluation.run_eval
python -m backend.decision.analyze DL-002      # konteks nyata, cetak rekomendasi + trace
```
Jev live (belum diuji): `TYPESAFE_API_KEY` di env backend, `DEALCOMPASS_ENGINE_MODE=jev`; rekam dengan `DEALCOMPASS_RECORD_DIR`, putar ulang `DEALCOMPASS_ENGINE_MODE=replay DEALCOMPASS_REPLAY_DIR=<dir>`.

## Pengujian aktual
2026-10-09 17:24 WIB, Windows, Python 3.11.9 (CI Python 3.12 dijalankan saat push PR):
- `python -m unittest discover -s tests` → `Ran 48 tests in 7.5s, OK` (17 Bima + 21 Ical + 10 bootstrap/handoff).
- Tes integrasi graph nyata: P02 satu permintaan 20% I0348 dan tanpa 15% C01; E01 VP Sales; KasirPro DL-002/006/007; interaksi C23 sintetis lebih baru tidak mengubah hambatan/aksi P02; P03 C03/C09/C17/C27 dan P04 C06 terbaca; P05 insufficient_evidence; respons Jev rusak (noul string, score string, choice di luar criteria, timeout) → rules dengan alasan; endpoint `POST /api/deals/DL-002/analyze` 200 dengan konteks nyata.
- `python -m evaluation.run_eval` → 29/30 lulus; inti 29/29; E15 (parafrase "lebih ramah di kantong") gagal = batas rules diketahui; invarian lima deal nyata benar.
- Waktu: build graph pertama ±2,05 dtk (cache Bima); analisis rules <20 ms per deal. E24: anggaran 0,8 dtk dengan mock 0,4 dtk/panggilan → `budget_exceeded`, selesai <2 dtk.
- Belum: Jev live, browser/UI gabungan dengan Boy.

## Fixture dan keterbatasan
- Fixture tulisan tangan dihapus; semua tes/evaluasi memakai konteks Bima nyata. Mutasi kasus berlabel sintetis.
- Mode aktual hasil: `rules`. Kasus `jev`/`replay` memakai mock; bukan bukti integrasi live.
- Klasifikasi pesan berbasis kata kunci; parafrase tanpa kata kunci terlewat (E15).
- Kandidat referensi disaring dengan health dashboard dan keputusan eskalasi/komitmen terbuka di konteks; tiket/usage kandidat belum dinilai. Kelayakan dan kesediaan belum dikonfirmasi.
- Identitas pengambil keputusan P01 = inferensi dari jabatan yang disebut di I0343 + satu kontak CRM cocok; bukan konfirmasi.
- Tidak ada ranking, probabilitas closing, atau tanggal target rekaan.

## Blocker
- `TYPESAFE_API_KEY` tidak tersedia. Dampak: Jev live belum diuji. Butuh key di env backend.
- Tidak ada blocker kode lain untuk R1-R3/R5.

## Tugas berikutnya
1. Main review ulang PR #7 pada SHA baru; uji gabungan dengan UI Boy.
2. Jev live dengan key; rekam replay; bandingkan rules vs Jev pada E14/E15.
3. Ranking lintas deal transparan + pemetaan `analysis_status` (setelah keputusan kontrak Main).
4. Nilai tiket/usage kandidat referensi; pembanding CRM-only dan holdout.

## Update WIB
2026-10-09 17:26 WIB (Ical via Claude).
