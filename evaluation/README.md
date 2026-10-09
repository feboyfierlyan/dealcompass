# Evaluasi — Ical

Simpan pertanyaan, label manusia, bukti rujukan, dan hasil aktual.
Pisahkan contoh pengembangan prompt dan holdout. Laporkan jumlah sampel,
dukungan bukti, tindakan yang sesuai, abstain, pelanggaran policy dan latensi.
Bandingkan CRM-only, graph + rules, graph + Jev saat implementasi siap.

## Isi

- `cases.py`: 30 kasus (label manusia = pemeriksaan per kasus) di atas
  `build_deal_context` nyata (graph Bima, dataset asli). Kasus mutasi/parafrase
  menambah/mengubah record SINTETIS pada salinan konteks dengan format produsen
  (excerpt JSON). Kasus Jev memakai transport mock, bukan panggilan live.
- `run_eval.py`: menjalankan kasus + invarian lima deal nyata dan menulis
  `results/latest.json` dan `results/latest.md`.

Fixture tulisan tangan ICAL-01 dihapus pada ICAL-02 karena berbeda dari
representasi produsen (review R2/R3).

```bash
python -m evaluation.run_eval
```

## Status

Hasil terakhir: `results/latest.md` (graph nyata + rules). Belum ada pembanding
CRM-only, belum ada holdout terpisah, dan belum ada panggilan Jev live; hasil
ini tidak boleh dilaporkan sebagai akurasi Jev. E15 adalah batas aturan yang
diketahui (parafrase tanpa kata kunci harga).
