# Handoff MAIN

## Task dan status
MAIN-HYBRID-REVIEW: tiga perbaikan PR #32/#33/#34 VERIFIED pada commit yang tercantum di [review hybrid](../reviews/2026-10-10-hybrid-default.md). MERGED berurutan #33 de4cf7e, #34 69272f6, #32 6779cea setelah required CI lulus. Catatan lama di bawah merupakan riwayat aktivasi Jev.

MAIN-JEV-USAGE: implementasi dan provider live VERIFIED lokal; siap review PR/CI.
Pengguna memberikan credential untuk testing dengan batas tim 100.000.000 input token,
dan mengonfirmasi belum pernah dipakai. Smoke, P01–P04, dan UI P02 berhasil memakai Jev.
P05 tetap rules karena insufficient evidence; tidak diklaim sebagai live.

## Branch dan commit
Dokumentasi review/integrasi: `integrator/hybrid-review-record`. PR aplikasi menggunakan commit terbaru yang dicatat dalam review hybrid.

`integrator/jev-usage-live` dari main b766770. PR terpisah dari redesign UI #29.
Backend live berjalan dari checkout utama; frontend 5174 tetap dari worktree PR #29.
Tidak mengubah atau menggabungkan branch UI.

## File dan fungsi
- `docs/reviews/2026-10-10-hybrid-default.md`: hasil review dan checklist tiga regresi.
- `docs/coordination/MAIN.md`: status integrasi hybrid terbaru.

- `backend/integrations/usage.py`: SQLite ledger, initialize eksklusif, summary,
  reserve atomik, finish receipt input/output; unknown/pending menghentikan spending.
- `jev.py`: wajib ledger untuk transport nyata, pencatatan sebelum validasi jawaban,
  endpoint resmi saja, error/fallback tetap eksplisit.
- `jev_live.py`: CLI init-budget dan usage; loader TYPESAFE_USAGE_DB.
- `.env.example`, `.gitignore`: contoh setting non-secret, abaikan DB lokal.
- `tests/ical/test_usage.py`: 12 uji guard/storage/concurrency/HTTP tanpa provider.
- `JEV_LIVE.md`, koordinasi Main: prosedur satu ledger tim dan batas keandalannya.

## Kontrak dan dependency
Tidak ada dependency atau kontrak v1/ranking/dataset baru. SQLite stdlib.
Cap 100 juta input; output dicatat terpisah. Reservasi konservatif 1 juta per request,
payload max64KiB/16questions. Ini guard lokal, bukan tokenizer/provider hard cap.
Satu request in-flight; permintaan paralel lain fallback rules. Semua proses/anggota
harus melalui host dan ledger yang sama. Pemakaian di luar jalur ini tidak terukur.

## Cara menjalankan
Host demo telah dikonfigurasi `.env` backend-only (0600), ledger absolut di
`.local/typesafe-usage.sqlite3` (0600). Keduanya ignored Git. Jangan ulang inisialisasi.

```bash
python -m backend.integrations.jev_live --env-file .env usage
python -m backend.integrations.jev_live --env-file .env serve --port 8000
```

Backend rules milik Main PID72643 dihentikan dan diganti backend live PID28657.
Preview http://127.0.0.1:5174/ → P02 → Jalankan analisis ulang. GET ranking tetap rules;
POST eksplisit memakai Jev. Tidak menyimpan key di frontend/PR/log maupun pesan tim.

## Pengujian aktual
Review hybrid terbaru: gabungan engine + route + UI lulus 222/222 backend, 85/85 frontend, build TypeScript/Vite dan handoff. Reproduksi race tetap 10 request mock/satu workflow; browser graph berpindah ke jalur versi baru. Tidak memakai provider berbayar dalam review.

- 26 targeted tests PASS (12 usage +14 live mock).
- Seluruh backend `python -m unittest discover -s tests -v`: 200/200 PASS, 46.565s.
  Run awal menemukan non-JSON HTTP error berubah menjadi invalid_response; sudah
  diperbaiki dan suite diulang. Unit tests tidak memuat .env / tidak memanggil provider.
- LIVE smoke: 1 request, model jev-1.13.0, 475ms, input550/output77. Choice harga,
  Noul approval0.04, Score kejelasan2.0. Semantic/shape PASS.
- LIVE P02 CLI: 10 request, invariant valid dan VP Sales pending, PASS.
- LIVE P02 browser: tombol analisis menghasilkan Analisis dengan Jev; request selesai,
  target keputusan VP Sales dan persetujuan yang diperlukan tetap terlihat.
- LIVE P01:6 request PASS; P03:1 PASS; P04:3 PASS; P05:0, rules,
  NOT_LIVE_SUCCESS yang diharapkan (insufficient evidence). Semua invariant true.
- Total ledger setelah seluruh tes live:31 request, input17.840/output1.657,
  remaining99.982.160 input; pending0, reserved0, blockedfalse.
- Screenshot UI lokal: `/tmp/dealcompass-jev-live/p02-live.png`.
- Receipt operasional lokal P01/P03/P04/P05 di `.local/live-proof/`, ignored Git.

## Fixture dan keterbatasan
Unit guard memakai MockTransport; hasil live disebut terpisah. Rules ranking tidak
berubah menjadi ranking Jev. Jev tidak memberi approval bisnis atau probabilitas closing.
Ledger menyimpan whitelist usage, bukan body provider. Reservasi bukan tokenisasi resmi;
usage di luar backend bersama tidak dapat dipantau. Tidak ada jaminan biaya global dari
provider hanya melalui counter lokal. Benchmark kualitas semua kasus belum dijalankan
ulang ke provider berbayar; invariant lima deal bukan klaim akurasi sempurna.

## Blocker
Tidak ada blocker live saat uji. Pemakaian tim selanjutnya harus lewat backend/ledger
bersama; tidak ada deploy/public access baru. Tidak ada reset otomatis untuk receipt
unknown/pending: perlu rekonsiliasi berdasarkan usage provider agar tidak menghapus biaya.

## Tugas berikutnya
Status terbaru: PR aplikasi #32/#33/#34 sudah merged. Tim sinkronkan main; rehearsal memakai backend/ledger bersama. Daftar di bawah adalah riwayat tugas aktivasi Jev.

1. Review dan integrasikan PR Jev ini secara terpisah dari UI #29.
2. Tim memakai backend bersama; cek usage sebelum/sesudah sesi demo/testing.
3. Rehearsal/demo/submission; jangan rerun batch evaluasi besar tanpa kebutuhan.
4. Jika provider gagal, tampilkan fallback rules; jangan klaim live dari label ranking.

## Update WIB
2026-10-10 — review hybrid VERIFIED; #33/#34/#32 MERGED dengan required checks lulus. Catatan review dipublikasikan lewat PR dokumentasi integrator.
2026-10-10 01:10 WIB — live verified dengan monitoring persisten. Key/DB tidak masuk Git.
