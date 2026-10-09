# Verifikasi frontend Boy — BOY-03

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
8. Analisis pada base main 712acf9 menghasilkan 200 mode rules. Status request sesi
   menjadi Respons diterima, sementara status bisnis API tetap terpisah. Unknowns
   dan approval wajib tetap terlihat/terjangkau; HTTP 200 bukan bukti cukup.

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

## Analisis nyata dan regresi BOY-03

Gunakan mode rules tanpa key Jev untuk pemeriksaan ini:

```bash
env -u TYPESAFE_API_KEY DEALCOMPASS_ENGINE_MODE=rules python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Setelah backend dan Vite menyala, tambahkan tes berikut ke 20 tes sebelumnya:

```bash
node --test frontend/tests/session.test.mjs
frontend/node_modules/.bin/tsc frontend/src/components/AnalysisReport.tsx frontend/src/lib/graphView.ts --target ES2022 --module commonjs --jsx react-jsx --outDir /tmp/dealcompass-boy03-tests --skipLibCheck --strict
NODE_PATH="$PWD/frontend/node_modules" ANALYSIS_TEST_BUILD=/tmp/dealcompass-boy03-tests node --test frontend/tests/analysis.test.cjs
```

Enam tes sesi menggunakan promise terkontrol (mock), termasuk respons yang sengaja
mengabaikan abort. Delapan tes analisis mencakup lima GET/POST nyata + render React
server atas komponen yang sama; seluruh action/milestone/approval/penjelasan/unknowns
harus tetap utuh. Tiga tes lainnya memeriksa prefix, sumber tanpa node, dan batas
jalur panjang secara sintetis. Total **34 tes frontend**. Tes real API mengharuskan
mode rules; tidak diam-diam mengganti respons dengan fixture.

### Acceptance P01–P05

Ekspektasi berikut khusus pengujian snapshot 2026-10-01, bukan aturan yang ditanam
ke komponen. Pada desktop 1440x1000 dan mobile 390x844, jalankan analisis setiap deal:

| Deal | Respons nyata yang harus dipertahankan UI | Bukti / batas |
| --- | --- | --- |
| P01 | Tindakan menyebut Rina Hapsari sebagai identitas inferensi yang perlu konfirmasi. | I0343, K017 dan employment; bukan decision-maker terkonfirmasi otomatis. |
| P02 | Usulan tidak menawarkan diskon 20% sebelum VP Sales memutuskan dan mencatat. | I0348 request; pending approval E01 tetap terlihat. Preseden D-2025-02/06 bukan approval P02. |
| P03 | Kandidat referensi perlu izin account owner, verifikasi kepuasan dan kesediaan. | I0334; shortlist dari API, tidak ditimpa laporan internal Bima. |
| P04 | Calon referensi perlu izin dan verifikasi; overlap tidak membuktikan saling kenal. | I0335; employment K028/K116 menuju overlap graph inferred. |
| P05 | Discovery sebelum menawarkan harga/paket; bukti interaksi belum cukup. | DL-005; 200 tetap mempunyai unknowns, bukan low risk/loss/closing. |

Urutan panel: tindakan → owner → milestone → approval → penjelasan/preseden →
unknowns → sumber. Semua teks API dipertahankan; prefix FAKTA/INTERPRETASI/SKENARIO
hanya menjadi kelompok visual. Pernyataan tanpa prefix berada di Penjelasan lainnya.
Owner tetap ID sumber. Approval kosong tidak berarti sudah disetujui. Unknowns dari
konteks berada pada disclosure dengan jumlah; unknowns tambahan analisis tampil langsung.

### Alur sumber ke graph

1. Dari sumber rekomendasi P02, buka `interactions.jsonl:I0348`. Panel harus menampilkan
   record yang sama, 28 Sep 2026, kutipan request, source_file/source_id, dan JSON asli.
2. Tekan Fokus graph: I0348 (klik/Enter). Jalur DL-002 → P02 ← I0348 memakai 3/1305
   node dan 2/2895 relasi. Batas 24/search/expand/akses seluruh 1361 bukti tetap ada.
3. Kembali ke analisis, buka D-2025-06 lalu fokus graph: 2 node/3 relasi kandidat
   inferred dari backend. Bukti historis tidak berubah menjadi approval sekarang.
4. P04: buka sumber employment K028. Karena source_id berupa locator baris, tidak
   ada node unik. Buka Relasi yang memakai sumber ini, pilih overlapping_employment.
   Endpoint K028/K116, tanggal 1 Feb 2015–30 Nov 2019, status inferred dan kedua
   record sumber harus tepat. Tidak ada node baru dibuat dari locator baris.
5. Jika record tidak punya pemetaan/relasi, UI menyatakan hal itu; record tetap bisa
   dibaca. Sumber tidak ditemukan, endpoint hilang dan jalur >24 node diuji sintetis.

### Request sesi: browser mock terpisah

Buka `http://127.0.0.1:5173/tests/session-harness.html` hanya pada Vite development.
Banner MOCK REQUEST TEST wajib terlihat. Harness memakai **Dashboard/DealWorkspace
produksi yang sama**, dengan transport sintetis. Ini bukan hasil bisnis/backend nyata.

- Pilih Gagal 503, jalankan: status Gagal + Coba lagi. Ganti Sukses segera, retry:
  Respons diterima dan action MOCK deal yang benar.
- Pilih Sukses terlambat, Analisis ulang: Sedang berjalan. Segera ganti P01 → P05:
  Belum dijalankan dan tetap tidak ada hasil setelah 2,5 detik.
- Pilih Gagal terlambat, mulai P05 lalu Muat ulang konteks: status kembali Belum
  dijalankan; error lama tidak muncul setelah 2,5 detik.
- Setelah hasil diterima, Muat ulang dashboard dan reload halaman menghapus hasil
  sesi. Status tidak diklaim tersimpan pada backend; analysis_status/rank tidak diubah.
- Uji 404/501/503, network, timeout dan cancellation tetap pada tujuh transport tests;
  jangan menyebutnya sebagai outage backend nyata yang berhasil direproduksi.

Build produksi hanya memakai index.html; harness dan fixture development tidak
masuk dist. Tidak ada dependency atau endpoint tambahan.

## Naskah demo mentor (sekitar 4 menit)

**0:00–0:30 — masalah dan batas.** “Lima deal punya hambatan berbeda. DealCompass
menampilkan usulan tindakan dan bukti yang dapat ditelusuri. Ini snapshot 1 Oktober,
mode rules; ranking masih belum tersedia.” Pilih P02 dan jalankan analisis.

**0:30–1:15 — mulai dari permintaan.** Buka sumber I0348 dari bagian Sumber pendukung.
“Ini email permintaan diskon 20%, belum persetujuan.” Tunjukkan tanggal, record dan
JSON asli, lalu Fokus graph: I0348. Jelaskan jumlah terlihat/total; graph sengaja fokus.

**1:15–2:15 — preseden dan usulan.** Kembali ke analisis, buka D-2025-02 dan D-2025-06
pada preseden. “Ada keputusan historis menolak diskon dan contoh pilot tanpa diskon,
namun itu tidak otomatis berlaku di P02.” Buka interpretasi/skenario bila dibutuhkan.
Tunjukkan action, E07 sebagai owner, milestone dan pending approval VP Sales.
Bila mentor bertanya asal hubungan, buka sumber preseden → graph inferred.

**2:15–3:30 — cakupan lima deal.** Jalankan P01: “Identitas Rina masih perlu
konfirmasi.” P03/P04: “Calon referensi perlu verifikasi dan izin; overlap kerja
bukan bukti saling kenal.” P05: “Informasi belum cukup, sehingga langkahnya discovery.”
Tunjukkan unknowns P05 agar respons 200 tidak disalahartikan sebagai bukti cukup.

**3:30–4:00 — tutup dengan batas yang jelas.** “Respons diterima adalah status
request sesi, bukan status bisnis. Semua usulan tetap perlu ditinjau orang terkait.
Jev live belum diuji; ranking dan diagnostic Bima belum terintegrasi di layar ini.”
Tidak mengklaim peningkatan closing, efisiensi persen, atau akurasi yang belum diukur.
