# Verifikasi frontend Boy

Jalankan perintah dari root repository. Node 24 disarankan untuk tes native TypeScript.
Manifest dan lockfile tidak berubah. Tes di bawah menggunakan dependency yang sudah ada.

## Build dan tes kontrak

```bash
npm --prefix frontend ci
npm --prefix frontend run build
node --test frontend/tests/contracts.test.mjs
```

Lima tes memeriksa rank null, schema v1, ID duplikat, struktur konteks/analisis,
dan pelaporan ID bukti yang hilang.

## Tes transport API

Kompilasi adapter ke direktori sementara di luar proyek, lalu jalankan tujuh tes:

```bash
frontend/node_modules/.bin/tsc frontend/src/lib/api.ts --target ES2022 --module commonjs --outDir /tmp/dealcompass-boy-api-tests --skipLibCheck --strict
API_TEST_BUILD=/tmp/dealcompass-boy-api-tests node --test frontend/tests/api.test.cjs
```

Cakupan: 404/501/503, JSON/schema rusak, gangguan jaringan, daftar kosong,
pembatalan request ketika berganti deal, timeout 20 detik, dan respons analisis
untuk deal lain. Fake clock dipakai untuk timeout; tidak perlu menunggu 20 detik.

## Pemeriksaan UI terhadap backend nyata

```bash
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# terminal kedua
npm --prefix frontend run dev -- --port 5173 --strictPort
```

Buka http://127.0.0.1:5173. Periksa:

1. Kelima kartu P01-P05 berasal dari GET /api/deals; rank null tertulis belum tersedia.
2. Memilih kartu mengubah detail dan memakai deal_id DL-xxx pada endpoint.
3. Detail 501 menampilkan status belum tersedia dan menonaktifkan analisis.
4. Pencarian tidak cocok memberi pesan; Tampilkan semua memulihkan kartu.
5. Tombol Muat ulang dan Coba lagi memanggil ulang sumber terkait.

## Fixture pengembangan

Tombol **Pratinjau fixture pengembangan** hanya ada dalam Vite development.
Pilih P02. Banner fixture selalu terlihat saat scroll. Jalankan analisis,
buka preseden, lalu tab Peta relasi atau Bukti.

- `src/dev/fixture.ts` menyimpan salinan record asli: I0296, I0348,
  D-2025-02, D-2025-06, dan ringkasan DL-002.
- Struktur graph dan rekomendasi adalah contoh UI yang disusun manual,
  bukan hasil backend atau Jev. Rekomendasi berlabel fixture dan engine replay.
- Field rank tetap null. P01/P03/P04/P05 tidak diberi analisis fixture rekaan.
- Node memilih bukti dari relasi yang terhubung. Edge menampilkan bukti,
  direct/inferred, valid_from dan valid_to. Bukti hilang ditandai eksplisit.
- Enter/Space dapat memilih node/edge, tombol panah dapat berpindah tab.
- Zoom/reset dan drag mengubah tampilan graph; Daftar relasi memberi alternatif.
- Kembali ke API nyata menghapus konteks, seleksi dan analisis fixture.
- Build produksi menghapus import fixture dan tombolnya. Periksa `frontend/dist`
  bila alur build berubah.

Pada pengujian 9 Oktober 2026: alur nyata dan fixture di atas diperiksa dengan
Codex In-app Browser, termasuk lebar 390 px tanpa overflow horizontal.
Analisis end-to-end nyata belum dapat diuji karena backend bootstrap masih 501.

## Skenario browser otomatis opsional

`tests/browser.mjs` memuat skenario live, fixture, error, race condition dan mobile.
Script ini **belum dijalankan sampai selesai** pada penyerahan awal. Browser
Playwright belum tersedia; pemeriksaan UI dilakukan lewat In-app Browser.
Jika lingkungan pengujian sudah menyediakan Playwright beserta browsernya:

```bash
PLAYWRIGHT_MODULE=/path/to/playwright node frontend/tests/browser.mjs
```

Jangan menambah dependency bersama tanpa koordinasi Main. Skenario live script
mengasumsikan backend bootstrap 501; ubah ekspektasinya saat integrasi nyata siap.

## Integrasi berikutnya

Jalankan ulang dengan output Bima/Ical untuk semua P01-P05. API v1 belum
memiliki field `blockers` tersendiri, jadi panel hambatan menampilkan `unknowns`
yang dikirim layanan, tanpa menebak diagnosis dari kutipan. Owner tampil sebagai
ID karena kontrak belum menyertakan nama. Perubahan tersebut diajukan ke Main.
