# Ical mengambil alih revisi R8 pada PR #16

Penugasan pengguna melalui Main, 2026-10-09 19:09 WIB.

Kamu AI Ical (Claude) untuk DealCompass. Pengguna secara eksplisit meminta kamu
mengerjakan revisi R8 milik modul Bima terlebih dahulu. ICAL-03 / PR #15 sudah
merged. Ini penugasan sementara sebagai pelaksana modul Bima, bukan tugas ranking
baru atau izin mengubah seluruh backend.

## Mulai dari kode yang benar

1. Baca AGENTS.md, docs/coordination/MAIN.md, PHASE3_CONTRACT.md,
   docs/reviews/2026-10-09-pr14-16.md dan docs/prompts/BIMA-03-R8.md.
2. Gunakan checkout sendiri. Lanjutkan remote branch `bima/diagnostics-api` dan
   PR #16 yang masih terbuka. Fetch keadaan terbaru lalu merge origin/main untuk
   mendapat ranking Ical dan klarifikasi kontrak Main. Jangan memakai PR #15 lama,
   membuat PR duplikat, reset pekerjaan, atau force-push.
3. Penamaan branch tetap karena PR #16 sudah memuat API yang perlu diperbaiki.
   Bima diminta tidak mengerjakan R8 bersamaan. Jika head berubah selama bekerja,
   baca perubahan baru dan gabungkan secara aman sebelum push biasa.

## Perbaikan yang diminta

Bug: `GET /api/pipeline/priorities` asli mengembalikan 503 karena validator
backend/api/priorities.py menolak traversal yang berlawanan arah dengan edge.
Contoh jalur sah: DL-002 → P02 ← I0348; node_ids berurutan DL-002, P02, I0348.

- Terima edge asli yang menghubungkan dua node berurutan dalam salah satu arah.
  Pertahankan source/target, relation, ID, evidence dan arah panah aslinya.
- Tetap tolak node/edge palsu, shortcut tidak terhubung, panjang path salah,
  missing evidence, dan engine yang memutasi graph input. Jangan menghapus validasi.
- Sesuaikan tes lama yang menganggap setiap reverse traversal tidak valid.
  Tambahkan kasus positif reverse traversal dan kasus negatif graph/provenance rusak.
- Tambahkan tes HTTP integrasi dengan dataset asli dan `rank_deals` nyata, tanpa
  mock engine/loader. Endpoint harus 200, tepat P01-P05, rank unik 1..5,
  gate approval P02 tetap ada, dan P05 discovery/insufficient_evidence.
  Periksa seluruh path dan sumber pada graph asli, bukan sekadar status 200.
- Jalankan semua unittest serta smoke pipeline diagnostic, diagnostic kelima
  deal, dan priorities. Pertahankan 501 modul hilang dan 503 output cacat.
- Jangan ubah metode ranking, dataset, frontend, dependency, CI atau kontrak
  bersama untuk meloloskan validasi. Scope revisi: backend/api dan tests/bima.

## Catatan .md WAJIB

Update `docs/handoffs/BIMA.md` karena PR ini tetap branch/modul Bima dan CI
memeriksa handoff tersebut. Nyatakan jelas: **Pelaksana revisi R8: Ical, atas
penugasan pengguna melalui Main**. Pertahankan atribusi dan bukti kerja Bima
sebelumnya. Jangan mengaku bahwa pengujian Ical dilakukan oleh Bima.

Gunakan seluruh heading wajib. Catat fungsi/file berubah, commit, perintah dan
hasil aktual, mock vs integrasi nyata, blocker, langkah berikutnya dan waktu WIB.
Status maksimal READY_FOR_REVIEW. Jangan mengubah docs/handoffs/ICAL.md pada PR
branch Bima ini karena ownership CI berbasis branch. Catatan pelaksana Ical ada
di handoff BIMA.md dan penugasan Main ini; CI tidak perlu dilemahkan.

## Kirim kembali

Link PR #16, commit terbaru, jumlah tes aktual, hasil HTTP priorities nyata,
daftar lima deal dari respons, serta path handoff. Jangan merge sendiri;
Main akan review ulang. Bila ada blocker akses GitHub, laporkan secara konkret.
