# Evaluasi — Ical

Simpan pertanyaan, label manusia, bukti rujukan, dan hasil aktual.
Pisahkan contoh pengembangan prompt dan holdout. Laporkan jumlah sampel,
dukungan bukti, tindakan yang sesuai, abstain, pelanggaran policy dan latensi.
Bandingkan CRM-only, graph + rules, graph + Jev saat implementasi siap.

## Isi

- `cases.py`: 35 kasus decision (ekspektasi pengembangan = pemeriksaan per kasus) di atas
  `build_deal_context` nyata. Mutasi/parafrase = record SINTETIS pada salinan konteks
  dengan format produsen (excerpt JSON). Kasus Jev memakai transport mock, bukan live.
- `ranking_cases.py`: 15 kasus ranking ICAL-03 di atas konteks + diagnostic nyata Bima;
  mutasi sintetis berlabel (tukar ID, tie, nilai/tahap/pesan, approval gate, data hilang).
  Ranking tidak memakai Jev.
- `ranking.md`: metode, bobot, tie-break, tradeoff, sensitivitas dan hasil ranking.
- `run_eval.py`: menjalankan keduanya dan menulis `results/latest.{json,md}` (decision) serta
  `results/ranking_latest.{json,md}` (ranking), dipisah per sumber kasus (dataset asli,
  sintetis, mock Jev, replay mock).
- `baseline_crm.py` (ICAL-04): baseline CRM-only (tahap/nilai/umur tahap dari `list_deals()`)
  vs graph+rules production pada lima deal yang sama → `results/baseline_latest.{json,md}`.
- `MENTOR_BRIEF.md`: penjelasan mentor dan jawaban P04/P01, P02, P05, bobot, anomaly vs outlier.
- `DEMO_CLAIMS.md`: matriks klaim → bukti → batas, klaim terlarang, hipotesis dampak, skrip demo.

```bash
python -m evaluation.run_eval
python -m evaluation.baseline_crm
```

## Current measured evidence — 10 October 2026

[Scorecard](results/scorecard_latest.md) separates 23/24 rules decision scenarios,
15/15 ranking conformance and 11/11 mock/replay transport scenarios. Original-data
recommendation integrity is5/5. The historical live synthetic classification
probe is10/12 Jev versus6/12 rules (`paraphrases_live.json`,05:28WIB).
These are different measures, not whole-app or independent holdout accuracy.
E15 remains visible. CRM-only primary ordering equals graph+rules on the five deals.

[Benchmark protocol](BENCHMARK_PROTOCOL.md) explains SalesTranscriptQA fit,
independent annotation, policy/evidence/action measures and novice-user testing.
Run `python -m evaluation.scorecard` after the two evaluation commands above to
regenerate the summary from receipts. No paid provider request is made by this command.

## New end-to-end challenge: actual local + cloud run

[Deal Acceleration benchmark](deal_benchmark/README.md):16 frozen synthetic new
cases uploaded through the actual pipeline, with rules and deployed hybrid receipts.
[Pitch-ready evidence and limits](deal_benchmark/PITCH.md), [results](deal_benchmark/results/REPORT.md).
Internal AI-authored expectations, human adjudication pending; not an external score.
