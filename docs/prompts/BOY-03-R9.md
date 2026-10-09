# BOY-03 R9 — sesuaikan tes dengan rekomendasi Ical terbaru

Kamu AI Boy untuk DealCompass. Baca AGENTS.md, docs/coordination/MAIN.md,
docs/reviews/2026-10-09-pr14-16.md dan handoff Boy.
Lanjutkan branch boy/analysis-demo serta PR #14. Fetch lalu merge origin/main
yang sudah memuat Ical #15; jangan reset pekerjaan atau mengubah backend.

## Tugas

1. Perbaiki assertion P03/P04 dalam frontend/tests/analysis.test.cjs. Regex kalimat
   lama tidak cocok rekomendasi baru walaupun gate tetap benar. Periksa terpisah:
   verifikasi pengalaman terbaru, kesediaan, izin kontak sebelum perkenalan.
   Gunakan assertion yang jelas terhadap output sekarang; jangan menggantinya
   dengan pemeriksaan string tidak kosong atau menghapus gate bisnis.
2. Pertahankan pemeriksaan semua action/milestone/approval/unknowns/penjelasan
   ditampilkan utuh dari API, bukti resolvable dan fokus graph dari sumber asli.
   P04 harus tetap menyatakan overlap tidak membuktikan saling kenal.
3. Jalankan build dan semua 34 tes menurut frontend/TESTING.md dengan backend
   main terbaru, mode rules tanpa key Jev. Lima kasus HTTP/render harus benar-benar
   memakai endpoint nyata. Jika wording lain berubah, evaluasi makna dahulu.
4. Smoke browser P03/P04 setelah analisis; tindakan baru dan informasi belum
   diketahui harus terbaca, dan sumber masih bisa dibuka ke graph.
5. WAJIB update docs/handoffs/BOY.md: perintah, hasil aktual, commit, batas mock/live,
   blocker dan waktu WIB. Maksimal READY_FOR_REVIEW. Kirim link PR #14 dan commit.

Ini revisi kecil pengujian integrasi, bukan desain ulang UI. BOY-04 ranking/diagnostic
belum dimulai sampai Main memverifikasi API Bima. Jangan hardcode ranking ke layar.
