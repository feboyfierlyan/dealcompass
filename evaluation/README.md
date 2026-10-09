# Evaluasi — Ical

Simpan pertanyaan, label manusia, bukti rujukan, dan hasil aktual.
Pisahkan contoh pengembangan prompt dan holdout. Laporkan jumlah sampel,
dukungan bukti, tindakan yang sesuai, abstain, pelanggaran policy dan latensi.
Bandingkan CRM-only, graph + rules, graph + Jev saat implementasi siap.

## Isi

- `cases.py`: 35 kasus decision (label manusia = pemeriksaan per kasus) di atas
  `build_deal_context` nyata. Mutasi/parafrase = record SINTETIS pada salinan konteks
  dengan format produsen (excerpt JSON). Kasus Jev memakai transport mock, bukan live.
- `ranking_cases.py`: 15 kasus ranking ICAL-03 di atas konteks + diagnostic nyata Bima;
  mutasi sintetis berlabel (tukar ID, tie, nilai/tahap/pesan, approval gate, data hilang).
  Ranking tidak memakai Jev.
- `ranking.md`: metode, bobot, tie-break, tradeoff, sensitivitas dan hasil ranking.
- `run_eval.py`: menjalankan keduanya dan menulis `results/latest.{json,md}` (decision) serta
  `results/ranking_latest.{json,md}` (ranking).

```bash
python -m evaluation.run_eval
```

## Status

Decision: 34/35 (inti 34/34); E15 batas parafrase rules yang diketahui. Ranking: 15/15.
Belum ada pembanding CRM-only, holdout terpisah, backtest closing, atau panggilan Jev live;
hasil tidak boleh dilaporkan sebagai akurasi Jev atau validasi closing.
