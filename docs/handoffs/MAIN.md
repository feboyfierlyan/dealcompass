# Handoff MAIN

## Task dan status
MAIN-JEV-LIVE: implementasi dan tes lokal VERIFIED; PR/CI menyusul. Provider live
BLOCKED: pengguna mengonfirmasi belum punya akses/API key TypeSafe. Tidak ada
request provider nyata. Status bonus terpisah dari kesiapan inti92/100.

## Branch dan commit
integrator/jev-live dari main2f1a79b6a799ef8bffb5290de9402c0f73223d08. Main
mengerjakan aktivasi Jev atas instruksi langsung pengguna. Repo tidak memiliki
PR terbuka lain saat pemeriksaan sebelum pengiriman perubahan.

## File dan fungsi
backend/integrations/jev_live.py: loader .env eksplisit, konfigurasi endpoint resmi,
check tanpa network, smoke satu request Choice/Score/Noul, analyze P02 dengan
invariant/policy checks, serve loopback dan receipt metadata aman.
backend/decision/analyze.py: nol request baru tidak boleh berlabel Jev; trace hanya
mencatat panggilan analisis saat ini meski client dipakai ulang. JEV_LIVE.md,
.env.example, README, koordinasi Main dan14tes baru melengkapi perubahan.

## Kontrak dan dependency
Kontrak APIv1, ranking, formula, policy approval dan dataset tidak berubah.
Tidak ada dependency baru. Base URL launcher dibatasi endpoint resmi TypeSafe.
Env budget launcher maksimal15detik untuk UI timeout20detik; batas per operasi
HTTP bukan jaminan waktu dinding mutlak. Key hanya backend/env, tidak dicommit.

## Cara menjalankan
Dari root repo terbaru dengan requirements terpasang:
python -m backend.integrations.jev_live --env-file .env check
Lalu smoke, analyze --deal DL-002 dan serve --port 8000. Panduan lengkap: backend/integrations/JEV_LIVE.md. Backend/frontend
Boy yang sedang berjalan tidak dihentikan atau diganti pada pekerjaan ini.

## Pengujian aktual
Main menjalankan188/188 unittest PASS dalam38.069detik pada venv bersih yang
dipakai review BIMA-04. Empat belas tes baru memakai MockTransport, tanpa
provider: missing key/endpoint/timeout/env, format dan semantik respons, receipt,
P02 approval pending/fallback dan P05 nol request termasuk client reuse.
Pengecekan lokal9Oktober21:15WIB: BLOCKED missing_key, request_count0, exit1.
Git diff --check PASS. Handoff/CI diverifikasi saat pengiriman PR.

## Fixture dan keterbatasan
Semua respons Jev pada tes baru adalah MOCK, bukan akses provider. Belum ada
latency/token usage provider nyata atau verifikasi browser mode live. Adapter
dasar telah ada; perubahan ini menyiapkan aktivasi dan pembuktian yang eksplisit.
Benchmark sebelumnya34/35 denganE15known limitation tidak diklaim menjadi35/35.
P05 tidak punya pertanyaan eligible sehingga rules/insufficient_evidence benar.

## Blocker
Pengguna belum punya akses/key TypeSafe. Perlu panitia atau console.typesafe.ai.
Tidak ada pembelian/pendaftaran otomatis, dan tidak meminta key dikirim ke chat.
File .env lokal ignored tersedia di checkout utama untuk diisi melalui editor.

## Tugas berikutnya
Boy memperoleh key lalu mengisi.env lokal. Main menjalankan smoke satu request;
jika PASS, uji P02 lengkap dan browser sebelum menyatakan Jev live VERIFIED.
Bima menjaga backend yang dipakai UI port8000, Ical memeriksa makna/policy hasil
live. Tidak ada pesan otomatis ke anggota. Rehearsal/submission inti tetap lanjut.

## Update WIB
2026-10-09 21:16 WIB — implementasi diuji lokal; live menunggu kredensial.
