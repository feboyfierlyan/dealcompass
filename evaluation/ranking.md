# Ranking prioritas deal — ICAL-03

Metode `deal-priority-heuristic-v1` di `backend/decision/ranking.py:rank_deals(contexts, diagnostics)`,
mengikuti `docs/coordination/PHASE3_CONTRACT.md`. Rules deterministik pilihan desain, **bukan model
terlatih dan bukan probabilitas closing**. Rank = urutan perhatian/tindakan sales pada snapshot
2026-10-01, bukan prediksi urutan closing.

## Input dan batas

- `contexts`: `DealContext` dari `build_deal_context` (Bima); `diagnostics`: laporan
  `analyze_deal_initial` (Bima). Dipasangkan per `deal_id`, bukan urutan array.
- Ditolak dengan `ValueError`: list kosong/bukan list, deal_id duplikat, set deal berbeda,
  snapshot campuran atau selain 2026-10-01, `account_id` diagnostic ≠ konteks, evidence ID sama
  dengan isi berbeda antar-sumber, evidence yang dirujuk tidak dapat di-resolve.
- Tidak membaca dataset, tidak HTTP, tidak memanggil Jev, tidak mengubah input (input disalin).
- Analisis bisnis per deal: `analyze_deal_trace(context, mode='rules', diagnostic)`. Approval/izin
  dihitung di sana dan **tidak** diubah oleh skor.

## Metode

1. **Tier.** `analysis_status` dari trace rules: `ready` → `acceleration`;
   `insufficient_evidence` → `discovery`. Semua acceleration sebelum discovery. Deal discovery
   tidak diberi skor karena faktor pembandingnya belum diketahui; unknown bukan nol dan bukan
   peluang buruk. Discovery tetap mendapat tindakan (jadwal discovery).
2. **Skor acceleration 0–10** (jumlah poin):

| Faktor | Poin | Aturan | Alasan desain |
|---|---|---|---|
| `tahap_deal` | 0–4 | Lead 0, Discovery 1, Demo 2, Proposal 3, Negosiasi 4 | Tindakan pada tahap lanjut lebih dekat ke keputusan. |
| `nilai_potensi_tahunan` | 0–3 | ≥ Rp200jt 3; ≥ Rp100jt 2; ≥ Rp50jt 1; lainnya 0 | Yang dipertaruhkan; di-bin agar nominal tidak mendominasi. |
| `hambatan_dinyatakan_pelanggan` | 0–2 | pesan pelanggan menyatakan tunda/syarat 2; pelanggan menyatakan hambatan 1; hanya pesan internal 0 | Hambatan dari pelanggan memberi tindakan pembuka yang jelas. |
| `preseden_relevan` | 0–1 | ≥ 1 preseden decision_log fit cocok/sebagian | Tindakan punya pembanding historis yang dapat dijelaskan. |

   "Pelanggan" ditentukan dari tipe interaksi dan pengirim/peserta (catatan meeting dengan kontak
   akun fokus, atau email dari domain non-karyawan), bukan dari subjek. Deteksi tunda/syarat
   bersifat leksikal pada `isi`.
3. **Tie-break:** (1) poin hambatan pelanggan, (2) tahap, (3) nilai, (4) `deal_id` leksikografis
   — yang terakhir hanya untuk determinisme, bukan prioritas bisnis.
4. **Discovery** diurutkan nilai potensi menurun lalu tahap (urutan jadwal discovery, tanpa skor).
5. **Konteks, tidak dihitung:** `umur_tahap_hari` (lintas tahap tidak dibandingkan; bukan SLA/outlier),
   `interaksi_eksternal_terakhir` (termasuk outbound sales, bukan balasan pembeli),
   `gate_approval_izin` (approval VP Sales, izin referensi, identitas inferred).
6. **Unknown:** faktor tidak diketahui = 0 poin dan dinyatakan; bila nilai maksimumnya dapat
   melewati deal di atasnya, item mencatat "dapat naik melewati …".

Faktor yang dipertimbangkan tetapi **tidak** dipakai: umur tahap (lima deal berada di lima tahap
berbeda; Bima `statistical_assessment = not_assessed`), jumlah interaksi (outbound bukan respons
pembeli), health/NPS akun (milik pelanggan, bukan prospek).

## Hasil aktual (graph + diagnostic nyata, mode rules)

| Rank | Deal | Tier | Skor | Tahap | Nilai | Hambatan pelanggan | Preseden | Gate |
|---|---|---|---|---|---|---|---|---|
| 1 | DL-004/P04 | acceleration | 8 | Negosiasi (4) | Rp147jt (2) | I0335 "tunda dulu sampai ada referensi" (2) | 0 | izin/kesediaan referensi C06 |
| 2 | DL-001/P01 | acceleration | 8 | Proposal (3) | Rp252jt (3) | I0343 keputusan di GM Operations baru (1) | D-2025-11, D-2026-08 (1) | identitas K017 inferred |
| 3 | DL-002/P02 | acceleration | 5 | Demo (2) | Rp63jt (1) | I0296 harga terlalu tinggi (1) | 5 preseden (1) | approval VP Sales (E01) diskon 20% |
| 4 | DL-003/P03 | acceleration | 2 | Discovery (1) | Rp37,8jt (0) | I0334 minta referensi (1) | 0 | izin/kesediaan referensi |
| 5 | DL-005/P05 | discovery | – | Lead | Rp168jt (belum divalidasi) | unknown | 0 | discovery belum dilakukan |

Tindakan per deal (Recommendation v1 rules, ringkas):

- **P04:** E06 mengonfirmasi kriteria "pengguna serupa" (I0335), lalu AM E04 memeriksa pengalaman
  terbaru dan menanyakan kesediaan + izin kontak Saiyo Group (C06). Overlap K028–K116 di PT Sentosa
  Abadi Group bukan bukti saling kenal; industri Resto Padang ≠ Hospitality perlu dicek.
- **P01:** E06 meminta kontak teknis (pengirim I0343) memperkenalkan ke K017 Rina Hapsari
  (GM Operations, inferred; konsisten dengan verifikasi kewenangan Bima). Jangan menjanjikan tanggal FEAT-07 (D-2025-11 belum ditepati, D-2026-08
  menunggu, di C01 tempat K017 bekerja sebelumnya).
- **P02:** jangan tawarkan diskon 20% sebelum VP Sales (E01) memutuskan dan mencatat (I0348 adalah
  permintaan). Opsi tanpa diskon 15 outlet Growth Rp63jt; pilot ≤10 outlet Starter hanya skenario.
- **P03:** E08 mengonfirmasi kriteria; AM memeriksa C17, C09, C27 (FEAT-05 Sep 2026: 22/11/48
  pengguna aktif). C03 dicek belakangan: 6 tiket terbuka (3 bug, 1 prioritas Tinggi) soal sinkronisasi/laporan.
- **P05:** E07 menjadwalkan discovery (pengambil keputusan, kebutuhan, jumlah outlet, anggaran).

**Tradeoff utama.** P04 dan P01 seri 8 poin; P04 menang tie-break hambatan pelanggan karena
pelanggan menyatakan menunda sampai ada referensi (deal berhenti sampai syarat dipenuhi), sedangkan
P01 masih bergerak tetapi perlu verifikasi pengambil keputusan. P01 bernilai lebih besar; bila nilai
diberi bobot lebih, P01 naik ke rank 1. Ini pilihan desain yang terbuka untuk diperdebatkan, bukan
temuan statistik.

## Sensitivitas (aktual)

| Variasi bobot | Urutan |
|---|---|
| dasar | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 |
| tanpa tahap | DL-001 > DL-004 > DL-002 > DL-003 > DL-005 |
| tanpa nilai | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 |
| tanpa hambatan pelanggan | DL-001 > DL-004 > DL-002 > DL-003 > DL-005 |
| tanpa preseden | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 |
| nilai ×2 | DL-001 > DL-004 > DL-002 > DL-003 > DL-005 |
| tahap ×2 | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 |
| hambatan pelanggan ×2 | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 |

Hanya urutan rank 1–2 (P04/P01) yang berubah antarvariasi; P02, P03, P05 stabil. Tabel lengkap
beserta skor ada di `results/ranking_latest.md`; envelope ranking juga memuat ringkasan
sensitivitas di `limitations`.

## Evaluasi

`python -m evaluation.run_eval` menjalankan 15 kasus ranking (`ranking_cases.py`) dan menulis
`results/ranking_latest.{json,md}`. Pemisahan sumber:

| Jenis | Isi | Status |
|---|---|---|
| Dataset nyata | K01, K02, K13–K15 dan urutan aktual: konteks + diagnostic Bima apa adanya | lulus |
| Mutasi sintetis | K03 tukar ID, K04 tie (salinan DL-003 → DL-903), K05 nilai P05 Rp10M, K06 tahap P03, K07 I0335 tanpa "tunda", K08–K11 approval gate (nilai besar, R6, R7, kontrol sah), K12 data hilang | lulus |
| Mock / replay Jev | tidak dipakai ranking; tetap ada pada evaluasi decision (E16–E26) | — |
| Live Jev | tidak dijalankan; `TYPESAFE_API_KEY` tidak tersedia | belum diuji |

Pemeriksaan tiap kasus: kontrak envelope/item, rank 1..N, Recommendation v1 rules, setiap evidence
ID yang dirujuk ada di `evidence` dan cocok row sumber, setiap path memakai edge asli graph konteks.

## Keterbatasan

- Bobot/bin adalah pilihan desain; belum divalidasi terhadap hasil closing historis.
- Deteksi hambatan pelanggan dan tunda/syarat leksikal; parafrase dapat terlewat (lihat E15 decision).
- Nilai deal adalah potensi CRM; pada P05 belum divalidasi percakapan.
- Gate approval/izin tidak memengaruhi rank; rank tinggi tidak mengesahkan diskon atau perkenalan.
- Kandidat referensi = hasil pencarian bersumber; kesesuaian, kesediaan, izin kontak null.
- Hanya satu snapshot; tidak ada backtest.
