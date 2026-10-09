# Hasil evaluasi ICAL-01 (2026-10-09 16:23 WIB)

Sumber konteks: FIXTURE_ICAL_SEMENTARA (record asli; bukan graph Bima). Jev: Tidak ada panggilan live. Kasus Jev memakai transport mock.

Kasus: 20/21 lulus; inti 20/20; batas diketahui: E12 (lulus: tidak ada). Invarian lima fixture: semua benar.

| ID | Kategori | Lulus | Mode | Hambatan | Pemeriksaan gagal |
|---|---|---|---|---|---|
| E01 | P02 dasar | ya | rules | harga | - |
| E02 | request vs approval | ya | rules | harga | - |
| E03 | request vs approval | ya | rules | harga | - |
| E04 | request vs approval | ya | rules | harga | - |
| E05 | hitungan diskon | ya | rules | harga | - |
| E06 | hitungan diskon | ya | rules | harga | - |
| E07 | hitungan diskon | ya | rules | harga | - |
| E08 | preseden tidak cocok | ya | rules | harga | - |
| E09 | bukti kurang | ya | rules | bukti_kurang | - |
| E10 | ID tidak valid | ya | rules | harga | - |
| E11 | parafrase | ya | rules | harga | - |
| E12 | parafrase (batas diketahui) | TIDAK | rules | harga | I0296 terdeteksi harga |
| E13 | Jev timeout | ya | rules | harga | - |
| E14 | Jev gagal | ya | rules | harga | - |
| E15 | Jev mock | ya | jev | harga | - |
| E16 | Jev mock | ya | jev | harga | - |
| E17 | Jev gagal | ya | rules | harga | - |
| E18 | replay | ya | replay | harga | - |
| E19 | P01 | ya | rules | pengambil_keputusan | - |
| E20 | P04 | ya | rules | referensi | - |
| E21 | P03 | ya | rules | referensi | - |

## Lima deal (mode rules, fixture)

| Deal | Status | Hambatan | Preseden | Approval |
|---|---|---|---|---|
| DL-001 | ready | pengambil_keputusan | D-2025-11, D-2026-08 | 0 |
| DL-002 | ready | harga | D-2025-02, D-2025-06 | 1 |
| DL-003 | ready | referensi | - | 0 |
| DL-004 | ready | referensi | - | 0 |
| DL-005 | insufficient_evidence | bukti_kurang | - | 0 |
