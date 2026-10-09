# Verifikasi frontend Boy — BOY-02

Jalankan dari root repo, dengan Node 24+ dan dependency dari lockfile yang sudah ada.
Tidak ada perubahan dependency atau kontrak API.

## Build dan tes frontend

```bash
npm --prefix frontend run build
node --test frontend/tests/contracts.test.mjs
frontend/node_modules/.bin/tsc frontend/src/lib/api.ts --target ES2022 --module commonjs --outDir /tmp/dealcompass-boy-api-tests --skipLibCheck --strict
API_TEST_BUILD=/tmp/dealcompass-boy-api-tests node --test frontend/tests/api.test.cjs
```

Lima tes kontrak dan tujuh tes transport mencakup rank null, schema v1, referensi
bukti hilang, 404/501/503, JSON invalid, jaringan, cancellation, timeout, dan respons
salah deal. Build produksi tidak menyertakan mode fixture.

## Tes graph memakai API nyata

Jalankan backend Bima dari main dengan environment yang sudah memenuhi requirements:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# terminal kedua, dari root repo
node --test frontend/tests/graph.test.mjs
npm --prefix frontend run dev -- --port 5173 --strictPort
```

Delapan tes graph mengambil GET detail untuk DL-001 sampai DL-005, tanpa fallback
fixture. GRAPH_API_URL dapat mengganti alamat backend. Tes memeriksa node fokus,
pencarian seluruh node, jalur valid, provenance, batas 24 node, direct/inferred,
layout 320/760 px, missing endpoint dan kutipan JSON producer. Ekspektasi jumlah
P02 mengikuti snapshot dataset 2026-10-01: 1.305 node, 2.895 relasi, 1.361 bukti.

## Pemeriksaan browser nyata

Buka http://127.0.0.1:5173, tanpa mengaktifkan fixture. Ulangi di desktop 1440x1000
dan mobile 390x844:

1. Pilih setiap P01–P05, buka Peta relasi. Node awal masing-masing 7, 7, 4, 6, 3.
   Jumlah total node masing-masing 749, 1305, 443, 147, 3. Label 13 px pada zoom 100%;
   kanvas bergulir, tidak menyusut mengikuti jumlah seluruh node. Halaman tidak overflow.
2. P02: klik I0296 dan I0348; cocokkan kutipan, tanggal dan source_id pada panel bukti.
   Klik kurva interaction_for I0348 → P02; pastikan bukti I0348 dan status langsung.
3. Pilih Kandidat preseden: D-2025-02 dan D-2025-06 tersedia, dengan relasi asli.
   Cari salah satu ID tersebut, klik hasilnya: jalur ke DL-002 tampil. Pencarian
   meliputi seluruh graph, termasuk node yang belum dirender. Tidak ada rekomendasi UI.
4. Klik kurva inferred menuju D-2025-06 atau gunakan daftar relasi/Enter. Periksa
   evidence_ids sumber dan tanggal, bedakan inferensi relasi dari bukti sumber langsung.
   Beberapa relasi paralel memiliki bukti berbeda: jangan menggabungkannya.
5. Perluas node; maksimal enam tetangga ditambahkan per klik, maksimal 24 node
   per tampilan. Fokuskan node / pencarian tetap membuka bagian graph lain.
6. Filter jenis node, pagination hasil pencarian, filter direct/inferred, zoom/reset,
   daftar relasi dan pagination bukti. Jumlah terlihat/total dan batas tetap eksplisit.
7. Tab Bukti: cari I0296/I0348 atau ID preseden; hapus pencarian dan buka halaman
   berikutnya. Panel sumber memuat enam record per halaman dan pencarian sendiri.
   Record JSON asli tetap dapat dibuka; isi percakapan diambil persis dari field isi.
8. Analisis pada base main ddf7a2a masih 501: tampilkan Analisis belum tersedia.
   Jangan menyebut integrasi Ical/Jev sudah selesai.

## Fixture dan script browser opsional

Fixture development memakai proyeksi kecil node/relasi/bukti dari payload backend
P02. Banner fixture tetap wajib; rekomendasi replay adalah contoh UI manual, bukan
hasil Jev. Fixture bukan bukti pengujian skala graph. Produksi tidak memuatnya.

`tests/browser.mjs` adalah skenario opsional untuk environment yang memiliki
Playwright beserta browsernya. Script ini belum dijalankan pada penyerahan BOY-02;
pemeriksaan browser aktual memakai Codex In-app Browser. Jangan menganggap hasil
script opsional tersebut sudah lulus.

```bash
PLAYWRIGHT_MODULE=/path/to/playwright node frontend/tests/browser.mjs
```

Bukti uji aktual, keterbatasan dan tugas Main dicatat di docs/handoffs/BOY.md.
