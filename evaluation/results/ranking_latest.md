# Hasil evaluasi ranking ICAL-03 (2026-10-09 18:37 WIB)

Sumber: build_deal_context + analyze_deal_initial nyata (Bima, dataset asli); kasus mutasi sintetis berlabel. Ranking tidak memakai Jev (rules). Tidak ada mock/replay/live pada ranking.

Kasus ranking: 15/15 lulus. rank_deals lima deal (konteks sudah dibangun): 78 ms.

## Urutan aktual

| Rank | Deal | Tier | Status | Skor | Tahap | Nilai | Hambatan pelanggan | Preseden | Gate |
|---|---|---|---|---|---|---|---|---|---|
| 1 | DL-004/P04 | acceleration | ready | 8 | Negosiasi | 147000000 | pelanggan menyatakan penundaan/syarat | 0 | kesediaan/izin kandidat referensi belum ada |
| 2 | DL-001/P01 | acceleration | ready | 8 | Proposal | 252000000 | pelanggan menyatakan hambatan | 2 | identitas pengambil keputusan masih inferred |
| 3 | DL-002/P02 | acceleration | ready | 5 | Demo | 63000000 | pelanggan menyatakan hambatan | 5 | approval VP Sales tertunda |
| 4 | DL-003/P03 | acceleration | ready | 2 | Discovery | 37800000 | pelanggan menyatakan hambatan | 0 | kesediaan/izin kandidat referensi belum ada |
| 5 | DL-005/P05 | discovery | insufficient_evidence | - | Lead | 168000000 | unknown | 0 | discovery belum dilakukan |

## Sensitivitas bobot (urutan lengkap)

| Variasi | Urutan | Skor acceleration |
|---|---|---|
| dasar (semua bobot 1) | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | DL-004 8, DL-001 8, DL-002 5, DL-003 2 |
| tanpa tahap_deal | DL-001 > DL-004 > DL-002 > DL-003 > DL-005 | DL-001 5, DL-004 4, DL-002 3, DL-003 1 |
| tanpa nilai_potensi_tahunan | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | DL-004 6, DL-001 5, DL-002 4, DL-003 2 |
| tanpa hambatan_dinyatakan_pelanggan | DL-001 > DL-004 > DL-002 > DL-003 > DL-005 | DL-001 7, DL-004 6, DL-002 4, DL-003 1 |
| tanpa preseden_relevan | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | DL-004 8, DL-001 7, DL-002 4, DL-003 2 |
| nilai x2 | DL-001 > DL-004 > DL-002 > DL-003 > DL-005 | DL-001 11, DL-004 10, DL-002 6, DL-003 2 |
| tahap x2 | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | DL-004 12, DL-001 11, DL-002 7, DL-003 3 |
| hambatan pelanggan x2 | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | DL-004 10, DL-001 9, DL-002 6, DL-003 3 |

## Kasus

| ID | Kategori | Lulus | Urutan | Pemeriksaan gagal |
|---|---|---|---|---|
| K01 | lima deal nyata | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
| K02 | input diacak | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
| K03 | ID diganti | ya | DL-001 > DL-004 > DL-002 > DL-003 > DL-005 | - |
| K04 | tie | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-903 > DL-005 | - |
| K05 | nilai besar bukti kurang | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
| K06 | faktor berubah | ya | DL-004 > DL-001 > DL-003 > DL-002 > DL-005 | - |
| K07 | faktor berubah | ya | DL-001 > DL-004 > DL-002 > DL-003 > DL-005 | - |
| K08 | approval gate | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
| K09 | approval gate R6 | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
| K10 | approval gate R7 | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
| K11 | approval gate kontrol | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
| K12 | missing data | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
| K13 | tanpa Jev | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
| K14 | referensi | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
| K15 | sensitivitas | ya | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
