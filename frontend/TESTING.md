# Verifikasi frontend Boy — BOY-04

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
8. Analisis backend main terbaru dalam mode rules menghasilkan 200. Status request sesi
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
jalur panjang secara sintetis. Subtotal **34 tes lama**. BOY-04 menambah 18 tes di bawah sehingga total 52. Tes real API mengharuskan
mode rules; tidak diam-diam mengganti respons dengan fixture.

### Acceptance P01–P05

Ekspektasi berikut khusus pengujian snapshot 2026-10-01, bukan aturan yang ditanam
ke komponen. Pada desktop 1440x1000 dan mobile 390x844, jalankan analisis setiap deal:

| Deal | Respons nyata yang harus dipertahankan UI | Bukti / batas |
| --- | --- | --- |
| P01 | Tindakan menyebut Rina Hapsari sebagai identitas inferensi yang perlu konfirmasi. | I0343, K017 dan employment; bukan decision-maker terkonfirmasi otomatis. |
| P02 | Usulan tidak menawarkan diskon 20% sebelum VP Sales memutuskan dan mencatat. | I0348 request; pending approval E01 tetap terlihat. Preseden D-2025-02/06 bukan approval P02. |
| P03 | Account manager memeriksa pengalaman terbaru, menanyakan kesediaan dan izin kontak sebelum perkenalan. Kesesuaian dan consent kandidat masih belum diketahui. | I0334; shortlist dari API, tidak ditimpa laporan internal Bima. |
| P04 | Pengalaman terbaru diverifikasi, kesediaan dan izin kontak ditanyakan sebelum perkenalan; overlap tidak membuktikan saling kenal. | I0335; employment K028/K116 menuju overlap graph inferred. |
| P05 | Discovery sebelum menawarkan harga/paket; bukti interaksi belum cukup. | DL-005; 200 tetap mempunyai unknowns, bukan low risk/loss/closing. |

Urutan panel: tindakan → owner → milestone → approval → penjelasan/preseden →
unknowns → sumber. Semua teks API dipertahankan; prefix FAKTA/INTERPRETASI/SKENARIO
hanya menjadi kelompok visual. Pernyataan tanpa prefix berada di Penjelasan lainnya.
Owner tetap ID sumber. Approval kosong tidak berarti sudah disetujui. Unknowns dari
konteks berada pada disclosure dengan jumlah; unknowns tambahan analisis tampil langsung.

R9: tiga gate referensi P03/P04 diperiksa dengan assertion terpisah terhadap action
API terbaru. Tes juga memastikan unknowns tidak berubah menjadi consent, seluruh
teks laporan tetap utuh, dan bukti tetap membuka node/relasi asli. Tidak ada aturan
bisnis baru pada komponen UI.

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

## Fase3 BOY-04 — ranking dan diagnostic

Backend dan Vite sama seperti di atas, rules tanpa key Jev. Tambahkan suite ini:

```bash
frontend/node_modules/.bin/tsc frontend/src/components/Phase3Panels.tsx frontend/src/components/AnalysisReport.tsx frontend/src/lib/graphView.ts frontend/src/lib/api.ts frontend/src/lib/resource.ts --target ES2022 --module commonjs --jsx react-jsx --outDir /tmp/dealcompass-boy04-tests --skipLibCheck --strict
NODE_PATH="$PWD/frontend/node_modules" PHASE3_TEST_BUILD=/tmp/dealcompass-boy04-tests node --test frontend/tests/phase3.test.cjs
```

Total **52 tes** = kontrak5 + transport7 + graph8 + sesi6 + analisis8 + fase3 18.
Suite fase3 memanggil GET priorities, pipeline initial-analysis, diagnostic setiap
deal dan detail konteks secara nyata melalui liveApi. Tujuh kasus real HTTP/render
memeriksa urutan/join, lima acceptance dan statistik. Sebelas lainnya memakai
corruption dari payload fetched, sumber tambahan sintetis, transport/lifecycle mock.
Tidak ada fallback fixture saat backend gagal. GRAPH_API_URL mengganti host tes.

### Acceptance ranking/diagnostic P01–P05

Urutan ini adalah ekspektasi tes snapshot, **bukan konstanta komponen**:

| Deal | Prioritas API | Gate yang harus tetap terlihat |
| --- | --- | --- |
| P04 | #1 acceleration / ready | Referensi C06 perlu verifikasi pengalaman terbaru, kesediaan dan izin. Overlap K028/K116 bukan kenalan terkonfirmasi. |
| P01 | #2 acceleration / ready | Identitas Rina inferensi; konfirmasi wewenang dan status fitur sebelum janji. |
| P02 | #3 acceleration / ready | I0348 request20%, belum approval VP Sales. Preseden bukan approval sekarang. |
| P03 | #4 acceleration / ready | Kandidat bukan izin; catatan C03 bertiket/bermasalah tidak hilang. |
| P05 | #5 discovery / insufficient_evidence | Skor null bukan0, bukan kalah/low risk; lakukan discovery. |

Pada desktop1440x1000 dan mobile390x844:

1. Muat dashboard: daftar sumber tetap tersedia saat ranking loading. Setelah
   respons valid, kartu diurutkan rank1..5 dari API, join berdasarkan ID/snapshot.
   Buka Metode & keterbatasan; formula, bobot, aturan/tie-break dan sensitivitas ada.
2. Pilih setiap deal: alasan/rationale → faktor/value/effect → tindakan/owner →
   milestone → approval → unknowns. Label sumber **GET ranking pipeline · rules**.
   Status CRM not_analyzed tetap dibedakan dari readiness priorities.
3. Jalankan tombol analisis sesi secara eksplisit, periksa label **POST analisis sesi**,
   empat status request lama serta rank yang tidak berubah. Gunakan tombol versi
   untuk kembali ke rekomendasi yang dipakai ranking. Tidak ada POST otomatis lima deal.
4. Buka Jalur bukti ranking. P02 harus **DL-002 → P02 ← I0348**; tombol relasi
   menampilkan **I0348 → P02**, interaction_for/direct, tanggal28Sep dan sumber asli.
   Traversal terbalik tidak membalik source/target. Periksa juga preseden D-2025-02/06.
5. Ranking → Sumber → pilih I0343(P01), I0348(P02), I0334(P03), I0335(P04),
   DL-005(P05). Record/JSON tepat lalu Fokus graph. Coba Enter di mobile.
   Cap24, jumlah terlihat/total, search/expand/filter dan seluruh evidence tetap tersedia.
6. Diagnostic memakai pipeline response yang sama saat berganti deal; tidak otomatis
   mengulang request satu deal. Tombol **Muat ulang diagnostic deal** melakukan GET
   satu deal saat diminta. Metrics lengkap/cakupan/sumber tersedia pada disclosure.
7. Buka temuan: fact, interpretation/inferred, missing_information, follow_up_implication
   terpisah. Implikasi diagnostic bukan Recommendation Ical. Kandidat P03/P04 dan
   semua provenance turunannya tetap bisa dibuka, termasuk consent/willingness null.
8. Diagnostic P04 → sumber employment K028 → overlapping_employment K028/K116,
   inferred, 1Feb2015–30Nov2019 dan kedua record. Sumber tanpa node tetap terbaca;
   hubungan baru tidak dibuat. Sumber statistik milik deal lain tetap record saja
   jika graph terpilih tidak mempunyai node/edge terkait.
9. Statistik: **not_assessed** beserta reason API. Method/threshold/outlier IDs null.
   Anomali bisnis bukan outlier statistik/SLA. Interaksi eksternal terakhir termasuk
   outbound, bukan otomatis balasan pelanggan. Missing bukan nol atau bebas risiko.
10. Periksa tidak overflow; action panjang, unknowns, source ID/locator dan disclosure
    tetap terbaca pada mobile. Kembalikan viewport sesudah smoke.

### Failure isolation dan stale response — browser MOCK terpisah

`http://127.0.0.1:5173/tests/phase3-harness.html` (Vite dev saja). Banner
**MOCK TRANSPORT TEST** wajib terlihat. Dashboard produksi sama; error503 dan delay
2,5 detik sintetis, respons sukses mengambil backend lokal nyata. Jangan menyebut
skenario ini outage backend. Harness tidak termasuk entry build produksi.

- Target Ranking, Gagal503, Muat ulang ranking: rank lama hilang; lima deal sumber
  tetap bisa dipilih dan diagnostic valid tetap tersedia. Sukses API → Coba lagi pulih.
- Target Diagnostic, Gagal503, Muat ulang diagnostic deal: diagnostic gagal tanpa
  menghapus ranking/rekomendasi. Sukses API → Coba lagi pulih.
- Diagnostic Gagal terlambat → refresh satu deal → segera ganti deal: error lama
  tidak tampil. Sukses terlambat → Muat ulang konteks: hasil lama tidak menimpa reset.
- Ranking Sukses terlambat → Muat ulang ranking → segera ganti deal: rank unavailable
  selama loading; respons baru dipasang per deal_id, bukan pada posisi pilihan lama.
- Muat ulang dashboard/reset halaman membersihkan hasil request lama. Validasi
  nonfinite/schema/snapshot/duplikat/mismatch, konflik registry, fake edge, source
  hilang dan timeout/501/network diuji otomatis; jangan klaim semuanya smoke browser.

## Naskah demo mentor (sekitar 4 menit)

**0:00–0:40 — prioritas pipeline.** “Ini lima deal dengan urutan perhatian dari
aturan deterministik: P04, P01, P02, P03, P05. Ranking bukan probabilitas closing.”
Buka metode: skor, tie-break dan keterbatasan berasal dari API, belum tervalidasi
terhadap closing historis. Semua deal tetap masuk, termasuk discovery.

**0:40–1:30 — mengapa P04/P01.** Pilih P04, baca alasan di atas P01 dan faktor
hambatan. “Pelanggan menunda sampai ada referensi. Langkahnya memeriksa pengalaman,
kesediaan dan izin kandidat C06.” Tunjukkan owner/milestone. Pilih P01: “Rina masih
identitas inferensi yang perlu dikonfirmasi; jabatan saja bukan kepastian.”

**1:30–2:20 — gate P02.** Pilih P02. “Request20% belum approval. Nilai/skor/preseden
historis tidak menggantikan keputusan VP Sales dan pencatatan.” Tampilkan approval
terbuka. Buka jalur DL-002 → P02 ← I0348 lalu klik edge asli I0348 → P02. Periksa
28Sep, kutipan dan JSON. Graph fokus menyebut jumlah terlihat dari total1305node.

**2:20–3:20 — diagnostic dan bukti.** Kembali ringkasan, buka temuan diagnostic.
“Fakta sumber, interpretasi, informasi kurang, dan implikasi pemeriksaan dipisah.”
Tunjukkan alasan statistical not_assessed: umur beda tahap bukan distribusi/SLA.
Opsional P04 employment → overlap inferred; bukan kenalan terkonfirmasi. P03 catatan
kandidat bermasalah tetap terlihat, kandidat bukan izin.

**3:20–4:00 — discovery dan batas.** Pilih P05: skor null, insufficient_evidence,
discovery dengan unknowns. “Data kosong bukan berarti tidak ada risiko.” Bila menjalankan
POST, tunjukkan label analisis sesi vs ranking dan rank yang tetap. “Demo ini rules,
bukan Jev live. Usulan memerlukan tinjauan manusia; kami belum mengukur dampak closing.”

Hasil aktual, screenshot lokal, keterbatasan dan waktu WIB ada di docs/handoffs/BOY.md.
