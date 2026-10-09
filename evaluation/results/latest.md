# Hasil evaluasi ICAL-01 (2026-10-09 17:24 WIB)

Sumber konteks: build_deal_context nyata (graph Bima, dataset asli); mutasi kasus sintetis berlabel. Jev: Tidak ada panggilan live. Kasus Jev memakai transport mock.

Kasus: 29/30 lulus; inti 29/29; batas diketahui: E15 (lulus: tidak ada). Invarian lima deal nyata: semua benar.

| ID | Kategori | Lulus | Mode | Hambatan | Pemeriksaan gagal |
|---|---|---|---|---|---|
| E01 | P02 nyata | ya | rules | harga | - |
| E02 | request vs approval | ya | rules | harga | - |
| E03 | request vs approval | ya | rules | harga | - |
| E04 | request vs approval | ya | rules | harga | - |
| E05 | request vs approval | ya | rules | harga | - |
| E06 | request vs approval | ya | rules | harga | - |
| E07 | hitungan diskon | ya | rules | harga | - |
| E08 | hitungan diskon | ya | rules | harga | - |
| E09 | hitungan diskon | ya | rules | harga | - |
| E10 | lintas akun | ya | rules | harga | - |
| E11 | preseden tidak cocok | ya | rules | harga | - |
| E12 | bukti kurang | ya | rules | bukti_kurang | - |
| E13 | ID tidak valid | ya | rules | harga | - |
| E14 | parafrase | ya | rules | harga | - |
| E15 | parafrase (batas diketahui) | TIDAK | rules | harga | I0296 terdeteksi harga |
| E16 | Jev gagal | ya | rules | harga | - |
| E17 | Jev gagal | ya | rules | harga | - |
| E18 | Jev rusak | ya | rules | harga | - |
| E19 | Jev rusak | ya | rules | harga | - |
| E20 | Jev rusak | ya | rules | harga | - |
| E21 | Jev rusak | ya | rules | harga | - |
| E22 | Jev mock | ya | jev | harga | - |
| E23 | Jev mock | ya | jev | harga | - |
| E24 | Jev waktu | ya | rules | harga | - |
| E25 | replay | ya | replay | harga | - |
| E26 | replay | ya | rules | harga | - |
| E27 | P01 nyata | ya | rules | pengambil_keputusan | - |
| E28 | P01 sintetis | ya | rules | pengambil_keputusan | - |
| E29 | P03 nyata | ya | rules | referensi | - |
| E30 | P04 nyata | ya | rules | referensi | - |

## Lima deal (mode rules, graph nyata)

| Deal | Status | Hambatan | Preseden | Approval |
|---|---|---|---|---|
| DL-001 | ready | pengambil_keputusan | D-2025-11, D-2026-08 | 0 |
| DL-002 | ready | harga | D-2025-02, D-2025-06, D-2024-02, D-2025-12, D-2026-04 | 1 |
| DL-003 | ready | referensi | - | 0 |
| DL-004 | ready | referensi | - | 0 |
| DL-005 | insufficient_evidence | bukti_kurang | - | 0 |
