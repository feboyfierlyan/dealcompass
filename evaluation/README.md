# Evaluasi — Ical

Simpan pertanyaan, label manusia, bukti rujukan, dan hasil aktual.
Pisahkan contoh pengembangan prompt dan holdout. Laporkan jumlah sampel,
dukungan bukti, tindakan yang sesuai, abstain, pelanggaran policy dan latensi.
Bandingkan CRM-only, graph + rules, graph + Jev saat implementasi siap.

## Isi

- `fixtures/DL-00{1..5}.json`: DealContext sementara berlabel
  `FIXTURE_ICAL_SEMENTARA`, disusun dari record asli. Excerpt `direct`
  diverifikasi verbatim terhadap dataset oleh `tests/ical/test_decision.py`.
  Bukan output graph Bima; wajib diganti/diuji ulang dengan `build_deal_context`.
- `cases.py`: 21 kasus (label manusia = pemeriksaan per kasus). Kasus mutasi dan
  parafrase adalah variasi sintetis, bukan record baru. Kasus Jev memakai mock.
- `run_eval.py`: menjalankan kasus + invarian lima fixture dan menulis
  `results/latest.json` dan `results/latest.md`.

```bash
python -m evaluation.run_eval
```

## Status

Hasil terakhir ada di `results/latest.md` (graph + rules pada fixture).
Belum ada pembanding CRM-only, belum ada holdout terpisah, dan belum ada
panggilan Jev live; hasil ini tidak boleh dilaporkan sebagai akurasi Jev.
E12 adalah batas aturan yang diketahui (parafrase tanpa kata kunci harga).
