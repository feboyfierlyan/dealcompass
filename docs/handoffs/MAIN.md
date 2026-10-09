# Handoff MAIN

## Task dan status
MAIN-01 IN_PROGRESS. Review ulang ICAL-02 selesai pada 7919550: R1-R3/R5 lulus, R6/R7 NEEDS_REVISION. PR #7 belum merged; BIMA-01 tetap MERGED #6.

## Branch dan commit
integrator/ical-r2-review-notes dari main ddf7a2a. Kode Ical diperiksa pada checkout terpisah integrator/review-ical-r2, head 79195504dd9d877d9bc3cc98b3a219744da77b21.

## File dan fungsi
Catatan docs/reviews/2026-10-09-pr7-r2.md dan checklist docs/coordination/MAIN.md diperbarui. Kode anggota tidak diubah. Fungsi yang bermasalah: ContextIndex.focus_decisions dan _price.

## Kontrak dan dependency
Schema v1 dan dependency tetap. Approval harus cocok cakupan deal dan persentasenya terbukti; nilai unknown bukan approval.

## Cara menjalankan
Pada head Ical, jalankan unittest discover dan python -m evaluation.run_eval --no-write. Reproduksi R6/R7 lengkap ada dalam dokumen review; gunakan dependency requirements.txt.

## Pengujian aktual
48/48 unittest lulus. Evaluasi 29/30, inti 29/29; E15 dikenal sebagai keterbatasan rules. Dua probe sintetis pada salinan konteks P02 menghasilkan approvals_needed kosong dan klaim 20% disetujui yang keliru. CI verify head Ical sukses. Validasi catatan Main dilakukan sebelum commit.

## Fixture dan keterbatasan
R6/R7 direproduksi melalui helper evaluasi yang menambah decision/evidence sintetis; bukan temuan pada dataset asli. Konteks asli P02 tetap memerlukan VP Sales. Jev live, ranking, dan UI end-to-end belum diverifikasi. Main masih belum memiliki kode Ical.

## Blocker
R6 menerima approval deal lain pada akun sama. R7 menerima approval persentase kosong sebagai persetujuan request 20%. Keduanya perlu regresi dan revisi PR #7; review ulang ini tidak mengubah status Boy/Bima.

## Tugas berikutnya
Ical memperbaiki R6/R7 pada PR yang sama, memperbarui handoff/evaluasi. Main memeriksa SHA baru sebelum merge. Boy melanjutkan R4, Bima melanjutkan analisis anomali bersumber sesuai MAIN.md.

## Update WIB
2026-10-09 17:38 WIB
