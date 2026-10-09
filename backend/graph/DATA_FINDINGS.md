# Fenomena data P01–P05 — jawaban mentor

**Snapshot 2026-10-01.** Dibaca ulang dari produsen tervalidasi dan row asli pada 2026-10-09. Fenomena: kewenangan belum terkonfirmasi, harga/approval, referensi dan kurang discovery—bukan sekadar deal tua. `file:source_id` adalah evidence ID; file berada di `dataset_kasirnusa/`.

## Umur dan aktivitas tercatat

| Akun/deal | Umur deal (hari) | Umur tahap (hari) | External | Terakhir external | Internal | Terakhir internal |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| P01/DL-001 | 61 | 20 | 4 | 2026-09-24 | 0 | null |
| P02/DL-002 | 68 | 45 | 3 | 2026-09-05 | 1 | 2026-09-28 |
| P03/DL-003 | 16 | 10 | 1 | 2026-09-21 | 0 | null |
| P04/DL-004 | 57 | 30 | 3 | 2026-09-22 | 0 | null |
| P05/DL-005 | 5 | 5 | 0 | null | 0 | null |

Sumber umur: `crm_deals.csv:<deal_id>`; scope aktivitas: account fokus, sejak deal dibuat sampai snapshot. External mencakup meeting/email keluar; `interactions.jsonl:I0322` bukan balasan buyer. Nol = record terhitung; null tanggal = tidak tersedia. Seluruh ID terhitung/query scope ada di diagnostic API.

## Anomalinya apa → bukti → pengaruh ke deal

- **P01 — jalur kewenangan (business_anomaly). Fakta/bukti:** `interactions.jsonl:I0343`: Fajar hanya teknis, keputusan pada GM Operations baru. `crm_contacts.csv:K017` + `contact_employment_history.csv:K017|Grup Ritel Mandala|2026-09-01` mengarah ke Rina. **Interpretasi:** inferred, bukan mandat terkonfirmasi. Anomali rekonsiliasi: `crm_accounts.csv:C01` masih champion K017 meski `contact_employment_history.csv:K017|Kopi Lintas Nusantara|2021-03-01` berakhir 2026-08-15; alias historis I0290 bukan alamat aktif P01. **Kurang:** identitas/mandat/kriteria pembelian. **Dampak:** E06 meminta perkenalan dari Fajar, mengonfirmasi wewenang; account owner memeriksa CRM/history, bukan memilih dari jabatan tertinggi/champion saja.

- **P02 — harga ≠ approval (business_anomaly). Fakta/bukti:** `interactions.jsonl:I0296` menyebut harga tinggi/kompetitor sekitar 20% lebih murah; `interactions.jsonl:I0348` meminta diskon 20% kepada VP Sales (`employees.csv:E01`). Lookup 30 row decision_log dengan P02/DL-002 sampai snapshot menemukan nol log fokus; scope tercatat, tidak ada ID keputusan rekaan. **Interpretasi:** harga didukung percakapan, umur tahap bukan sebab tunggal, permintaan bukan approval. **Kurang:** anggaran/cakupan pembanding/keputusan sah. **Dampak:** E07 klarifikasi nilai; E01 putuskan dan log sebelum menawarkan diskon >10%.

- **P03 — referensi diminta, belum bukti tertunda. Fakta/bukti:** `interactions.jsonl:I0334` meminta referensi modul apotek untuk 9 klinik; `crm_accounts.csv:P03`, akun C03/C09/C17/C27 dan FEAT-05 memberi kandidat. Bukti bulan lengkap terbaru (usage kandidat, bukan P03):

  | Evidence ID | Pengguna aktif September |
  | --- | ---: |
  | `feature_usage_monthly.csv:2026-09\|C03\|FEAT-05` | 14 |
  | `feature_usage_monthly.csv:2026-09\|C09\|FEAT-05` | 11 |
  | `feature_usage_monthly.csv:2026-09\|C17\|FEAT-05` | 22 |
  | `feature_usage_monthly.csv:2026-09\|C27\|FEAT-05` | 48 |

  **Interpretasi:** kandidat bersumber, bukan eligibility/consent. **Kurang:** kriteria, pengalaman terbaru, kesediaan/izin. **Dampak:** E08/account owner memeriksa kecocokan dan meminta izin sebelum perkenalan; jangan mengganti latest zero/missing dengan usage positif lama.

- **P04 — penundaan eksplisit. Fakta/bukti:** `interactions.jsonl:I0335` menunda sampai ada referensi. History `K028|PT Sentosa Abadi Group|2015-01-01` + `K116|PT Sentosa Abadi Group|2015-02-01` pada `contact_employment_history.csv` overlap 2015-02-01–2019-11-30; `crm_contacts.csv:K116` + history `K116|Saiyo Group|2020-01-02` mengarah ke C06. **Interpretasi:** overlap adalah jalur kandidat, bukan kenalan/consent. **Kurang:** arti “mirip”, pengalaman, hubungan pribadi/izin. **Dampak:** E06/account owner validasi kriteria dan izin pengantar; bukan langsung menjanjikan referensi.

- **P05 — data_gap. Fakta/bukti:** `crm_deals.csv:DL-005`, `crm_accounts.csv:P05` dan query aktivitas kosong; champion/NPS/health blank, bukan nol. **Interpretasi:** diagnosis belum cukup, bukan loss/tidak berminat/closing nol. **Kurang:** kontak, kebutuhan, hambatan, otoritas/proses. **Dampak:** E07 discovery dan pencatatan dahulu; priorities memberi discovery/insufficient_evidence, unknowns dan skor null.

## Batas dan reproduksi

Statistik **not_assessed**: lima tahap berbeda, tanpa cohort/SLA; method/threshold/outlier_deal_ids null. Maksimum umur P02 bukan bukti outlier statistik. Ranking heuristik adalah urutan perhatian, bukan probabilitas closing; ready bukan approval/consent. Metode/sensitivitas milik Ical.

Read-only dari root (perintah produsen yang dipakai untuk menyusun temuan, bukan bukti lifecycle):
```sh
python -c "import json; from backend.api.phase3 import pipeline_initial_analysis,pipeline_priorities; print(json.dumps({'diagnostic':pipeline_initial_analysis(),'priorities':pipeline_priorities()},ensure_ascii=True))"
```
API lengkap: GET `/api/pipeline/initial-analysis`, `/api/pipeline/priorities` dan `/api/deals/{deal_id}/initial-analysis` menyimpan source_file/source_id/excerpt dan paths asli. Bukti HTTP/restart ada di handoff BIMA; dokumen ini tidak membuktikan UI/Jev/submission.
