# DealCompass — matriks klaim → bukti → batas (ICAL-04)

Snapshot 2026-10-01. Mode yang dipresentasikan: **rules**. Penjelasan mentor:
[MENTOR_BRIEF.md](MENTOR_BRIEF.md). Hasil aktual: [results/](results/).

Status: **BOLEH** = didukung output/tes yang dapat diulang; **BOLEH + batas** = wajib
disertai kalimat batas; **JANGAN** = belum terbukti.

## Klaim yang boleh dipresentasikan

| # | Klaim | Bukti (source/path/test) | Batas yang wajib diucapkan | Status |
|---|---|---|---|---|
| C1 | Kelima prospek P01–P05 dianalisis dan diurutkan dari data kanonis yang sama | `rank_deals`; `GET /api/pipeline/priorities` 200; `tests/ical/test_ranking.py`, `tests/bima/test_priorities_real_http.py`; eval K01 | Satu snapshot 2026-10-01 | BOLEH |
| C2 | Setiap alasan menunjuk record sumber dan path edge asli graph | evidence_ids + evidence_paths per item; `path_is_valid`; review R8 (validator menolak edge/node palsu, shortcut) | Path menunjukkan hubungan record, bukan kausalitas; edge `inferred` tetap inferensi | BOLEH |
| C3 | P02: permintaan diskon 20% (I0348) dideteksi sebagai permintaan, bukan approval; VP Sales E01 wajib memutuskan | `approvals_needed` DL-002; path `I0348 → email:andi@kasirnusa.id → E01`; eval E01–E06, E31–E35; K08–K11 | Rules policy deterministik pada format data ini; bukan validasi hukum/kebijakan di luar dataset | BOLEH |
| C4 | Gate approval/izin tidak bisa dihapus oleh rank, nilai besar, atau preseden sukses | K08 (nilai P02 Rp10 miliar), K09/K10 (approval tidak sah), K11 (kontrol sah) | Diuji pada mutasi sintetis, bukan kejadian nyata | BOLEH + batas |
| C5 | Rank = urutan perhatian sales, metode transparan dan deterministik | `methodology.weights`, `tie_breakers`; K02 input diacak hasil identik; K03 tukar ID | Bobot pilihan desain; bukan probabilitas closing | BOLEH + batas |
| C6 | P04 di atas P01 karena tie-break hambatan pelanggan (I0335 "tunda sampai ada referensi") | rationale DL-004/DL-001; factor `hambatan_dinyatakan_pelanggan` 2 vs 1 | Sensitif: tanpa tahap, tanpa hambatan pelanggan, atau nilai ×2 → P01 rank 1 (`results/ranking_latest.md`) | BOLEH + batas |
| C7 | P05 discovery karena bukti percakapan belum ada; bukan peluang buruk | `analysis_status=insufficient_evidence`, skor null; finding `customer_information_gap:DL-005` (data_gap); eval E12, K05 | Nilai Rp168 jt belum divalidasi | BOLEH |
| C8 | Dibanding baseline CRM-only, graph+rules menambah hambatan bersumber (4/5 deal), gate VP Sales (1 vs 0) dan sumber lintas tabel | `python -m evaluation.baseline_crm` → `results/baseline_latest.md`; `tests/ical/test_baseline.py` | Urutan baseline "tahap lalu nilai" **sama** dengan graph+rules; jumlah bukti bukan ukuran akurasi; tindakan baseline = template buatan Ical | BOLEH + batas |
| C9 | Tidak ada deal yang dinyatakan outlier statistik | `statistical_assessment.status = not_assessed`, method/threshold null | 5 deal di 5 tahap; tidak ada SLA | BOLEH |
| C10 | Referensi P03/P04: kandidat bersumber (usage, overlap kerja), izin/kesediaan belum diketahui | Recommendation DL-003/DL-004; eval E29, E30, K14 | Overlap kerja bukan bukti saling kenal; health/NPS indikator CRM | BOLEH + batas |
| C11 | P01: kandidat pengambil keputusan K017 dan risiko janji FEAT-07 di C01 | path `K017 → C01 → D-2025-11 → FEAT-07`; eval E27, E28 | Identitas K017 **inferred**; pengetahuan K017 atas janji itu belum dikonfirmasi | BOLEH + batas |
| C12 | Evaluasi: decision 34/35 (inti 34/34), ranking 15/15 | `python -m evaluation.run_eval`; `results/latest.md`, `results/ranking_latest.md` | E15 gagal (parafrase sulit, batas diketahui); benchmark disusun bersama pengembangan, bukan holdout | BOLEH + batas |
| C13 | Adapter Jev ada dengan fallback rules saat gagal/timeout/respons rusak | eval E16–E26 (mock/replay); `backend/integrations/jev.py` | **Mock/replay, bukan live**. Jev tidak dipakai ranking | BOLEH + batas |

## Klaim yang JANGAN dipresentasikan

| Klaim | Alasan belum terbukti |
|---|---|
| "DealCompass meningkatkan closing/penjualan X%" | Tidak ada eksperimen, kontrol atau data hasil setelah pemakaian |
| "Ranking lebih akurat dari CRM" | Tidak ada label hasil; urutan baseline utama identik; lima kasus |
| "Rank = peluang closing / probabilitas menang" | Heuristik perhatian, tidak dikalibrasi |
| "Model AI dilatih dari data historis" | Tidak ada training; rules deterministik |
| "Jev live berjalan / confidence Jev" | `TYPESAFE_API_KEY` tidak tersedia; live belum pernah dieksekusi |
| "P02 outlier / deal macet secara statistik" | `not_assessed`; umur lintas tahap tidak sebanding |
| "Diskon P02 akan/tidak akan disetujui" | Keputusan wewenang VP Sales; preseden bukan izin otomatis |
| "Saiyo Group/Apotek X bersedia jadi referensi" | Kesediaan dan izin kontak null |
| "Rina Hapsari pasti pengambil keputusan" | Inferred dari I0343 + jabatan CRM |
| "Pilot Starter P02 sudah disepakati" | Skenario usulan; Starter maks 10 outlet |
| "Bobot sudah divalidasi sales" | Belum ada kalibrasi dengan masukan sales |

## Dampak bisnis — hipotesis, bukan hasil

| Hipotesis | Indikator yang bisa diukur nanti | Status |
|---|---|---|
| H1 Gate eksplisit mengurangi penawaran diskon >10% tanpa approval | Jumlah penawaran diskon >10% tanpa log decision_log per bulan | Belum diukur |
| H2 Tindakan bersumber mempercepat deal yang tertahan syarat (P04/P03) | Hari dari permintaan referensi sampai referensi terkonfirmasi | Belum diukur |
| H3 Discovery lebih awal mencegah salah prioritas nilai CRM yang belum valid (P05) | Selisih nilai CRM awal vs setelah discovery | Belum diukur |
| H4 Riwayat keputusan/janji mengurangi janji fitur berulang (P01) | Jumlah janji fitur tanpa keputusan tercatat | Belum diukur |

Validasi yang jujur: pilot dengan tim sales, bandingkan periode sebelum/sesudah atau
kelompok kontrol, dan kumpulkan label hasil per deal. Lima deal tidak cukup untuk klaim uplift.

## Skrip demo 3–5 menit (mode rules)

Persiapan (lokal, tanpa key):

```bash
python -m pip install -r requirements.txt
DEALCOMPASS_ENGINE_MODE=rules python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
cd frontend && npm ci && npm run dev   # http://localhost:5173
# cadangan tanpa UI:
curl -s http://127.0.0.1:8000/api/pipeline/priorities | python -m json.tool | head -60
python -m evaluation.baseline_crm --no-write
```

UI ranking/diagnostic bergantung BOY-04; bila belum merged, pakai endpoint + tabel
`results/baseline_latest.md` sebagai cadangan.

| Menit | Yang ditampilkan | Kalimat kunci |
|---|---|---|
| 0:00–0:30 | Masalah: 5 prospek, Rp667,8 jt potensi, bukti tersebar | "CRM tahu tahapnya, bukan alasannya." |
| 0:30–1:15 | Baseline CRM-only vs graph+rules (`baseline_latest.md`) | "Urutannya sama; yang berbeda alasan, tindakan dan gate." |
| 1:15–2:30 | P02: I0296 → I0348 → E01, preseden D-2025-02/D-2025-06 | "Permintaan bukan approval. Rank tidak bisa melompati VP Sales." |
| 2:30–3:15 | P04 vs P01: skor seri 8, tie-break I0335; sensitivitas | "Ini pilihan desain yang terbuka, bukan hasil statistik." |
| 3:15–3:45 | P05 discovery | "Unknown bukan nol, bukan peluang buruk." |
| 3:45–4:30 | Batas: rules, mock Jev, tanpa uplift, E15 | "Dampak bisnis kami sebut hipotesis yang siap diuji." |

## Tanya jawab cepat

- **Kenapa tidak pakai ML?** Lima deal dan tanpa label hasil; rules bisa diaudit dan cocok untuk policy approval.
- **Bagaimana kalau bobot diubah?** Hanya rank 1–2 (P04/P01) yang berubah pada variasi yang diuji; P02, P03, P05 stabil.
- **Bagaimana menangani teks yang tidak terdeteksi?** Saat ini leksikal; E15 contoh gagal. Jalur Jev disiapkan, belum live.
- **Kenapa P02 tidak didahulukan?** Lihat MENTOR_BRIEF §6: umur tidak sebanding lintas tahap, gate VP Sales, owner berbeda.
- **Apa yang terjadi bila VP Sales menyetujui?** Kasus K11: gate hilang, rank tidak berubah; tindakan berikutnya menyesuaikan.
- **Apakah data asli diubah?** Tidak. Mutasi hanya pada salinan konteks dan diberi label sintetis.
