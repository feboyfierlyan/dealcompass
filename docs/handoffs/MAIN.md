# Handoff MAIN

## Task dan status
Penugasan ICAL-03/BIMA-03 siap. Kontrak fase 3 disepakati Main; implementasi ranking/API baru masih TODO. BOY-03 tetap berjalan independen. Review #7/#10 sebelumnya tetap berlaku.

## Branch dan commit
integrator/assign-ranking-diagnostics dari main 36c0312. Tidak ada PR anggota terbuka pada pemeriksaan awal tugas ini. Branch pekerjaan baru Ical/Bima ditulis pada prompt, belum dibuat oleh Main.

## File dan fungsi
PHASE3_CONTRACT.md menetapkan rank_deals dan wire contract tiga endpoint diagnostic/priorities. Prompt ICAL-03.md dan BIMA-03.md siap diteruskan. MAIN.md/API_CONTRACT.md mencatat status spec, bukan endpoint live. Tidak ada kode aplikasi berubah.

## Kontrak dan dependency
Tambahan API v1 direncanakan dengan snapshot 2026-10-01. Model respons baru Bima di backend/api/phase3_models.py diizinkan sesuai kontrak; tipe bersama lama tidak berubah. Ranking rules deterministik milik Ical; Bima hanya transport/validasi. Tidak ada dependency baru.

## Cara menjalankan
Baca docs/prompts/ICAL-03.md atau BIMA-03.md dari main terbaru pada checkout anggota masing-masing. Buat branch/PR baru. Kedua prompt merujuk kontrak fase 3 yang sama. Fungsi/endpoint baru belum dapat dijalankan sebelum implementasi.

## Pengujian aktual
Perubahan hanya dokumentasi. check_handoff --all, validasi diff/ownership Main dan git diff --check dijalankan sebelum penyerahan; CI menjadi gate merge. Tidak mengklaim tes ranking/endpoint baru sudah berjalan. Bukti 99 tes gabungan historis ada pada review final #7/#10.

## Fixture dan keterbatasan
Bima memakai mock berlabel untuk contract test sampai ranking Ical merged; wajib smoke nyata setelah integrasi. Jev live tidak menjadi dependency ranking; status credential tidak diasumsikan. Output ranking akan berupa heuristik, belum tervalidasi closing historis.

## Blocker
Tidak ada blocker penugasan. Diagnostic dapat dibangun sekarang. Integrasi priorities bergantung implementasi Ical; sebelum tersedia harus 501, bukan dummy ranking. Kontrak lama tidak berubah sepihak dan Boy belum diberi klaim endpoint baru live.

## Tugas berikutnya
Pengguna meneruskan prompt ke Ical/Bima. Main review metode, bukti/path dan API, kemudian koordinasikan UI BOY-04. Boy lanjut BOY-03 sekarang. Setiap PR anggota wajib handoff sendiri, status maksimal READY_FOR_REVIEW.

## Update WIB
2026-10-09 18:11 WIB
