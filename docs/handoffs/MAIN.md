# Handoff MAIN

## Task dan status
Review #14/#15/#16 selesai. Ical #15 MERGED c7582a6. Boy #14 BLOCKED R9;
Bima #16 BLOCKED R8. Belum mengklaim integrasi ranking/API/UI selesai.

## Branch dan commit
integrator/review-pr14-16 dari main c7582a6. Head yang diuji: Boy 07df905,
Ical cc8102c, Bima 9454e87. Gabungan lokal terisolasi integrator/review-phase3;
tidak dipush sebagai implementasi. Catatan ini adalah PR Main dokumentasi.

## File dan fungsi
MAIN.md, API_CONTRACT.md, PHASE3_CONTRACT.md diperbarui; review pr14-16 dan
prompt BOY-03-R9/BIMA-03-R8 ditambahkan. Tidak ada kode aplikasi/dataset berubah.

## Kontrak dan dependency
Klarifikasi Main: evidence path boleh menelusuri kedua arah, tetapi pasangan node
harus memakai edge asli dengan source/target/relation/provenance tetap. Kontrak
awal ambigu mengenai traversal; Bima harus menyesuaikan validator dan tes.
Tidak ada dependency baru atau perubahan API lama.

## Cara menjalankan
Boy dan Bima sync main lalu ikuti prompt revisi pada PR yang sama. Jalankan backend
mode rules; endpoint priorities diuji tanpa mock engine setelah revisi Bima.
Main memakai Python venv review dan backend 8126/frontend 5177 untuk smoke lokal.

## Pengujian aktual
Gabungan: 139/139 unittest; eval decision 34/35 (inti 34/34, E15 known limitation),
ranking 15/15; frontend build lulus, 32/34 tes lulus (P03/P04 regex lama gagal).
HTTP priorities asli 503. Diagnostic pipeline/DL-002 200. Browser P02 analisis →
sumber I0348 → graph 3 node/2 edge berhasil. Handoff/diff checks dijalankan untuk
PR dokumentasi; CI tetap gate merge. Rincian/perintah ada di dokumen review.

## Fixture dan keterbatasan
Ranking rules, bukan probabilitas closing. Jev live belum diuji. Tes lifecycle dan
transport frontend memakai mock; tes graph/analisis memakai HTTP asli. Probe arah
validator hanya di memori untuk diagnosis, tidak menjadi kode fix. Review ini
tidak mengulang seluruh pemeriksaan mobile/manual Boy.

## Blocker
R8: validator path Bima menolak 12 traversal sah, sehingga endpoint asli 503.
R9: assertion teks frontend P03/P04 belum kompatibel rekomendasi terbaru Ical.
UI ranking/diagnostic menunggu kedua PR diverifikasi; jangan hardcode ranking.

## Tugas berikutnya
Teruskan prompt R8/R9 ke Bima/Boy; keduanya WAJIB handoff .md pada PR yang sama.
Main review ulang dan merge jika lulus, lalu tugas BOY-04. Ical dapat menyiapkan
penjelasan metode dari evaluation/ranking.md; belum ada tugas kode baru.

## Update WIB
2026-10-09 19:02 WIB
