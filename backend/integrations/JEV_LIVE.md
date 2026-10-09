# Menjalankan Jev Live di DealCompass

Status 10 Oktober 2026: **provider live VERIFIED**. Smoke Choice/Noul/Score
lulus memakai `jev-1.13.0`; analisis P01–P04 lulus invariant, P02 juga diverifikasi
dari UI. P05 tetap rules dengan nol request karena bukti kurang. Pada akhir uji:
31 request, 17.840 input token, 1.657 output token; tidak ada usage tertunda.

## Monitoring dan batas tim 100.000.000 input token

Setiap request nyata wajib melalui `UsageLedger` SQLite, termasuk CLI smoke,
analisis dan backend. MockTransport/replay tidak masuk tagihan. Ledger menyimpan
waktu, ID lokal, status HTTP serta objek usage input/output yang tervalidasi;
tidak menyimpan key, state, jawaban atau header. Angka output dicatat terpisah,
tidak mengurangi kuota input. Tidak ada retry otomatis.

Di host demo, `.env` menunjuk `.local/typesafe-usage.sqlite3` dengan path absolut.
File `.env` dan SQLite diabaikan Git; credential/DB dibuat dengan izin 0600.
Default path bagi setup baru adalah `~/.local/share/dealcompass/typesafe-usage.sqlite3`.
Jangan membuat ledger baru untuk tiap anggota/worktree, menghapusnya, atau meresetnya.

Inisialisasi **sekali** dengan pemakaian sebelumnya yang sudah dikonfirmasi:

```bash
python -m backend.integrations.jev_live --env-file .env init-budget --prior-input-tokens 0
python -m backend.integrations.jev_live --env-file .env usage
```

Host demo sudah diinisialisasi dari 0 setelah pengguna mengonfirmasi key belum dipakai.
`init-budget` menolak menimpa file lama. `usage` tidak mengirim request provider atau
memerlukan key. `recorded_input_tokens` adalah usage asli; `accounted_input_tokens`
juga memasukkan baseline dan reservasi yang belum selesai.

Sebelum kirim, transaksi SQLite mengunci dan menyisihkan **1.000.000 input token**
untuk satu request. Payload dibatasi 64 KiB dan 16 pertanyaan. Ini reservasi
konservatif, **bukan hitungan tokenizer atau batas billing yang dijamin TypeSafe**.
Request baru ditolak jika saldo tidak cukup untuk reservasi, jika ada request
pending, atau ada usage hilang/invalid/melebihi reservasi. Setelah respons, usage
asli direkonsiliasi sebelum jawaban dipakai. Bahkan respons dengan jawaban invalid
tetap dicatat. Timeout/crash/storage error tidak mengembalikan saldo menjadi nol;
request berikutnya berhenti dan aplikasi kembali ke rules berlabel jelas.

Jika terblokir, cek provider console dan ledger, lalu rekonsiliasi receipt dengan
bantuan Main. Jangan menghapus DB atau memulai ulang counter untuk melewati blokir.
Tidak ada tombol reset/release otomatis, sebab request timeout mungkin tetap ditagih.

**Cakupan satu tim:** semua anggota harus mengirim lewat backend pada satu host
pemilik ledger. SQLite ini tidak menggabungkan tiga laptop, penggunaan console,
atau script lain yang langsung memakai key. Untuk host lain, pindahkan layanan
beserta ledger yang sama, jangan menggandakan counter. Key cukup di backend.
Batas provider-side/account yang benar-benar global perlu pengaturan di provider;
dokumentasi API yang diperiksa tidak memberi parameter hard cap token per request.

## Analisis default halaman deal (ICAL-05)

Halaman deal kini memanggil `POST /api/deals/{id}/analysis` **otomatis sekali** untuk deal yang dibuka
(bukan kelima deal). Rekomendasi rules ranking tampil dulu ("Checking context…"). Backend
(`backend/decision/hybrid.py`) menjalankan rules, lalu Jev untuk deal yang eligible, memeriksa hasil
dengan rules dan menyimpan hasil tervalidasi di `DEALCOMPASS_ANALYSIS_CACHE_DB` (default
`analysis-cache.sqlite3` di folder ledger, **file terpisah dari ledger**; boleh dihapus untuk memaksa
analisis ulang — ini bukan ledger). Kunjungan ulang, tab, modal dan permintaan bersamaan tidak memanggil
provider lagi. Gagal → label "Jev unavailable · rules shown"; tidak di-retry selama
`DEALCOMPASS_JEV_RETRY_AFTER_S` (default 300 dtk) kecuali tombol **Refresh analysis**. P05 nol request.
Semua request tetap lewat `UsageLedger` yang sama; jangan reset/salin ledger.

Uji live terkontrol (Main, host ledger tim): `jev_live usage` → buka P02 sekali → tunggu label
"Rules + Jev" → buka P04 lalu kembali ke P02 (harus "Saved analysis…", tanpa request baru) →
`jev_live usage` lagi. Catat selisih request/token di handoff Main.

## Fungsi Jev dalam produk

Context Graph menyediakan pesan dan preseden beserta sumbernya. Jev membantu
membaca makna teks: **Choice** memilih hambatan, **Noul** menilai apakah sebuah
pesan menyatakan approval, **Score** menilai kecocokan preseden. Mesin keputusan
kemudian menyusun usulan tindakan dan bukti. Approval diskon tetap ditentukan
log keputusan dan kewenangan VP Sales, bukan jawaban model. Ranking pipeline
masih memakai aturan transparan yang telah diuji. Skor Jev bukan peluang closing.

GET daftar/ranking/diagnostic tidak memanggil provider. Membuka deal mengirim satu
POST `/analysis` (lihat bagian di atas); jika konfigurasi Jev aktif, backend mencoba Jev. Bila provider
gagal atau anggaran waktu habis, seluruh hasil kembali ke rules dan alasannya
muncul di unknowns. P05 dengan bukti kurang tetap rules; nol panggilan tidak boleh
mendapat label Jev. Scope produk tetap P01–P05; P02 dipakai untuk uji awal karena
memiliki pesan harga dan permintaan diskon yang relevan.

Riset mengacu pada [quickstart resmi](https://docs.typesafe.ai/introduction/quickstart)
dan [referensi API resmi](https://docs.typesafe.ai/api), diperiksa 9 Oktober 2026:
POST `https://api.typesafe.ai/v1/systemone`, Bearer key, model `jev-latest`, body
`state`, `questions`, `model`. Implementasi memakai dependency httpx yang sudah
ada; tidak perlu SDK tambahan.

## 1. Dapatkan key dan siapkan backend

Minta akses/credit hackathon kepada panitia atau gunakan
[console resmi TypeSafe](https://console.typesafe.ai). Ketersediaan akun/credit
harus dicek tim; integrasi ini tidak membuat akun atau melakukan pembelian.

Dari root repo terbaru, gunakan Python environment dengan requirements terpasang.
Buat `.env` dari `.env.example` **hanya jika belum ada**, lalu isi lewat editor:

```dotenv
TYPESAFE_API_KEY=isi_di_file_lokal_saja
TYPESAFE_MODEL=jev-latest
TYPESAFE_BASE_URL=https://api.typesafe.ai/v1
TYPESAFE_TIMEOUT_S=20
DEALCOMPASS_ENGINE_MODE=jev
DEALCOMPASS_ANALYSIS_BUDGET_S=15
```

`.env` diabaikan Git. Jangan taruh key di frontend, chat, argumen terminal,
screenshot atau handoff. Loader hanya membaca file yang disebut eksplisit;
uvicorn biasa tidak otomatis membaca `.env`. Nilai environment proses yang sudah
terisi didahulukan. Loader menerima literal `KEY=value` atau value berpetik tanpa
menjalankan ekspansi shell; hindari komentar setelah value.

## 2. Periksa konfigurasi, lalu satu request kecil

```bash
python -m backend.integrations.jev_live --env-file .env check
python -m backend.integrations.jev_live --env-file .env smoke
```

`check` tidak menghubungi internet: `CONFIGURED_NOT_TESTED` hanya berarti konfigurasi
valid. `smoke` mengirim **satu request** berisi tiga pertanyaan dengan teks asli
fiktif I0296 dan I0348. Pemeriksaan mencakup model, usage, distribusi probabilitas,
legend dan makna: harga sebagai hambatan, permintaan diskon belum berarti approval.
Output memuat jumlah request, latency, model dan token usage tanpa key atau teks
respons mentah. Tidak ada retry otomatis atau perekaman body provider.

| Hasil | Makna / langkah |
|---|---|
| `BLOCKED`, `missing_key` | Isi key di file backend; nol request |
| `CONFIGURED_NOT_TESTED` | Belum membuktikan Jev berhasil |
| `PASS` dari `smoke` | Respons satu request sesuai format dan pemeriksaan makna |
| `REVIEW_REQUIRED` | Format valid, jawaban berbeda dari pemeriksaan; evaluasi sebelum demo |
| `unauthorized` / `rate_limited` / `overloaded` | Cek akses, limit atau coba lagi nanti; tidak ada retry otomatis |
| `timeout` / `budget_exceeded` | Belum berhasil; jangan menyebut fallback sebagai Jev live |
| `incomplete_live_response` | HTTP 200 tetapi bukti respons belum memenuhi format yang diperiksa |

## 3. Uji analisis aplikasi dengan P02

Setelah smoke PASS:

```bash
python -m backend.integrations.jev_live --env-file .env analyze --deal DL-002
```

Ini memanggil beberapa request mengikuti analisis pesan/preseden dan memakai
anggaran analisis 15 detik. Anggaran diperiksa sebelum tiap request; timeout HTTP
berlaku pada operasi jaringan, bukan jaminan waktu dinding mutlak. Kondisi jaringan
nyata tetap harus diuji. Launcher membatasi budget maksimal 15 detik agar sesuai
request timeout UI 20 detik; menaikkan setting tidak melewati batas launcher.

PASS memerlukan mode Jev, panggilan tanpa error, sumber/preseden valid, usulan
berlabel USULAN, dan approval VP Sales P02 tetap pending. `NOT_LIVE_SUCCESS`
berarti analisis tidak lolos sebagai Jev, meskipun rules berhasil memberi hasil.
P05 tanpa pesan menghasilkan status ini secara wajar dengan nol request.

## 4. Aktifkan di aplikasi

Setelah tim siap mengganti backend demo, hentikan backend lama dari terminalnya
(Ctrl+C), lalu jalankan dari checkout terbaru:

```bash
python -m backend.integrations.jev_live --env-file .env serve --port 8000
```

Frontend yang ada memproxy `/api` ke port 8000. Buka http://127.0.0.1:5173,
pilih P02, klik Analisis dan periksa mode hasil **Jev** serta approval VP Sales
masih dibutuhkan. Memuat halaman atau mendapat `/health` 200 tidak membuktikan
provider telah dipanggil. Uji P01–P04 selanjutnya, P05 tetap tampil bukti kurang.

Default port launcher adalah 8001 untuk percobaan terpisah. Frontend default
tidak otomatis terhubung ke 8001. Jangan hentikan proses demo anggota lain tanpa
koordinasi. Untuk kembali ke rules, Ctrl+C backend launcher lalu:

```bash
DEALCOMPASS_ENGINE_MODE=rules python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

## Catatan Main yang wajib setelah uji live

Isi `docs/handoffs/MAIN.md`: commit, waktu WIB, mode, jumlah request, latency,
model, hasil smoke/analisis/browser dan error bila ada. Jangan salin key atau
body provider. Bedakan bukti mock, replay dan provider nyata. Status bonus live
baru VERIFIED setelah uji nyata; tidak otomatis mengubah progres rehearsal atau
submission tim.
