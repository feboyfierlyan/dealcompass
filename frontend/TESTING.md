# Verifikasi frontend — redesign UI/UX dan regresi BOY-02..04

Jalankan dari root repo, dengan Node 24+ dan dependency dari lockfile yang sudah ada.
Tidak ada perubahan dependency, kontrak API, dataset, backend, ranking atau aturan approval.
Redesign UI/UX dikerjakan Ical atas penugasan pengguna/Main di area frontend Boy;
riwayat dan hasil uji BOY-02..04 tetap milik Boy (lihat `docs/handoffs/BOY.md`).

## Build dan seluruh tes frontend (73)

Backend lokal **rules** wajib menyala karena sebagian tes memanggil HTTP nyata:

```bash
env -u TYPESAFE_API_KEY DEALCOMPASS_ENGINE_MODE=rules python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Terminal kedua, dari root repo. `UX_BUILD` boleh folder sementara mana pun yang terbaca Node
(di Windows/Git Bash pakai path Windows, bukan `/tmp`).

```bash
UX_BUILD=/tmp/dealcompass-desktop-tests
npm --prefix frontend run build
node --test frontend/tests/contracts.test.mjs frontend/tests/graph.test.mjs frontend/tests/session.test.mjs frontend/tests/present.test.mjs
frontend/node_modules/.bin/tsc frontend/src/components/DealTabs.tsx frontend/src/components/EvidencePanel.tsx frontend/src/components/ContextGraph.tsx frontend/src/components/Phase3Panels.tsx frontend/src/lib/graphView.ts frontend/src/lib/api.ts frontend/src/lib/resource.ts --target ES2022 --module commonjs --jsx react-jsx --outDir "$UX_BUILD" --skipLibCheck --strict
NODE_PATH="$PWD/frontend/node_modules" API_TEST_BUILD="$UX_BUILD/lib" ANALYSIS_TEST_BUILD="$UX_BUILD" PHASE3_TEST_BUILD="$UX_BUILD" REDESIGN_TEST_BUILD="$UX_BUILD" node --test frontend/tests/api.test.cjs frontend/tests/analysis.test.cjs frontend/tests/phase3.test.cjs frontend/tests/redesign.test.cjs
```

| Suite | Tes | Isi | Nyata / mock |
| --- | --- | --- | --- |
| contracts | 5 | schema v1, rank null, bukti hilang | fixture repo sebagai data uji kontrak |
| api (transport) | 7 | 404/501/503, JSON invalid, jaringan, abort, timeout, deal salah | mock transport |
| graph | 8 | fokus, pencarian seluruh node, jalur, batas 24, direct/inferred, layout | GET nyata DL-001..005 |
| session | 6 | lifecycle request analisis, abort, respons terlambat | mock promise |
| present | 12 | pilihan default/pilihan pengguna, versi saran, tab keyboard, unknowns, owner, judul bukti, arah jalur | sintetis murni |
| analysis | 8 | POST rules nyata lima deal dirender ActionTab+ReasonsTab; teks API utuh; urutan lapisan 1; bukti → graph | HTTP nyata + 3 sintetis |
| phase3 | 18 | ranking/diagnostic nyata, join ID/snapshot, corruption, lifecycle | HTTP nyata + mock/sintetis berlabel |
| redesign | 9 | lapisan 1 lima deal, state loading/gagal, versi analisis ulang, panel bukti I0348, jalur di peta, guard tanpa POST otomatis, ID sumber terverifikasi/ambigu, field sumber/null | HTTP nyata (GET saja), MOCK, STATIC berlabel |

Tes real API mengharuskan mode rules; tidak ada fallback fixture diam-diam.
`GRAPH_API_URL` mengganti host backend. Ekspektasi angka mengikuti snapshot 2026-10-01
(P02: 1.305 node, 2.895 relasi, 1.361 bukti) dan berada **di tes saja**, bukan di komponen.

## Struktur tampilan yang diuji

- **Beranda** “Prioritas tindak lanjut”: lima deal dalam urutan API (nomor, nama, tahap,
  potensi tahunan; “Perlu persetujuan” bila API mencantumkan approval dan “Lengkapi
  informasi” untuk discovery). Syarat lengkap tersedia di detail.
  Prioritas #1 terbuka otomatis setelah ranking tiba; pilihan pengguna tidak ditimpa.
  Ranking gagal: daftar tetap bisa dibuka dalam urutan CRM dengan pemberitahuan jelas.
- **Detail, tab Saran tindakan** (lapisan 1): Tindakan yang disarankan, tombol
  “Lihat alasan & bukti” dan “Lihat hubungan yang mendukung saran ini” → teks tindakan →
  Penanggung jawab → Target langkah berikutnya → Persetujuan yang diperlukan →
  Yang masih perlu dipastikan → Mengapa perlu diperhatikan. Asal saran satu baris (“Dari urutan prioritas · data per …”);
  analisis ulang hanya lewat tombol “Jalankan analisis ulang”.
- **Alasan & bukti** (lapisan 2): bukti yang dirujuk, keputusan terdahulu (hanya bila ada di
  data), hubungan data pendukung, alasan urutan termasuk skor (terlipat), penjelasan analisis,
  informasi yang belum diketahui.
- **Jelajahi data** (lapisan 3): Peta hubungan, Semua bukti, Cara prioritas dihitung,
  Temuan dari data, Rincian teknis (ID, status CRM, endpoint, JSON mentah).
- **Panel bukti**: hanya saat dipilih. ≥1800 px panel samping non-modal (Esc menutup);
  <1800 px `dialog` modal (Esc/latar/tombol Tutup). Fokus pindah ke judul panel dan kembali
  ke pemicu saat ditutup.

## Pemeriksaan browser nyata

Buka http://127.0.0.1:5173 tanpa fixture. Fokus penyerahan ini **desktop** 1440×900 dan
1280×720 atas instruksi terbaru pengguna. Tata letak 390×844 dan 200% zoom (640×360 CSS px)
tetap tersedia sebagai dukungan dasar, tidak dipoles lebih lanjut. Alat bantu dev: `/tests/viewport.html?w=390&h=844`
(atau `w=640&h=360`, `w=1280&h=720`, `w=1440&h=900`) merender aplikasi nyata di iframe
berukuran pasti; tidak masuk build produksi.

1. Muat beranda. Network hanya GET `/api/deals`, `/api/pipeline/priorities`,
   `/api/pipeline/initial-analysis` dan detail deal terpilih; **tidak ada POST**.
   Prioritas #1 dari API (snapshot ini P04) terbuka; urutan tidak ditanam di kode.
2. P04: tindakan memeriksa pengalaman terbaru, menanyakan kesediaan dan izin kontak
   Saiyo Group (C06) sebelum perkenalan; penanggung jawab Bagus Prakoso (E06, nama dari
   employees.csv); persetujuan 0 dengan kalimat “Ini tidak berarti tindakan sudah disetujui.”
3. “Lihat bukti I0335” → panel bukti: judul subjek email, 22 Sep 2026, pengirim/penerima,
   kutipan utuh; “Detail sumber · I0335” berisi file, ID dan JSON asli. Esc menutup dan
   fokus kembali ke tautan.
4. “Lihat hubungan yang mendukung saran ini” → Peta hubungan dengan pemberitahuan
   “Menampilkan 3 jalur data…”, relasi jalur berwarna jingga tebal, garis putus = dugaan.
5. P02 (#3): kutipan I0296/I0348, syarat “approval VP Sales tertunda”, tindakan tidak
   menawarkan diskon 20% sebelum VP Sales memutuskan dan mencatat; persetujuan VP Sales (E01)
   tampil di kartu tindakan. Alasan & bukti menampilkan jalur **DL-002 → P02 ← I0348**.
6. P05 (#5): “Lengkapi informasi”; kalimat bukan gagal/kalah/bebas risiko; discovery
   sebelum menawarkan harga; unknown “bukan berarti tidak ada risiko” di kartu tindakan.
7. Analisis eksplisit: “Jalankan analisis ulang” → satu POST untuk deal itu; kalimat
   “Hasil analisis ulang yang Anda minta pukul … · urutan prioritas tidak dihitung ulang”,
   label mode dari respons (rules: “Analisis berbasis aturan”), tombol versi kembali ke
   “Saran dari urutan prioritas”. Nomor prioritas tidak berubah.
8. Keyboard: Tab ke tab detail, panah kiri/kanan/Home/End berpindah tab; Enter pada
   bukti membuka panel; Esc menutup; fokus kembali ke pemicu. Fokus terlihat.
9. Tidak ada scroll horizontal (`document.documentElement.scrollWidth <= innerWidth`).
   Dukungan dasar 390×844: daftar tampil pertama; ketuk deal → detail dengan “Semua deal”;
   panel bukti menjadi sheet bawah modal.

Graph lama tetap: node awal per deal 7, 7, 4, 6, 3 (tanpa jalur), total node 749, 1.305,
443, 147, 3; batas 24 titik, pencarian seluruh peta, perluas maksimal enam tetangga,
filter langsung/dugaan, zoom, daftar relasi dan halaman bukti. Label titik 14 px
(jenis · ID 12 px) pada zoom 100%; kanvas bergulir, tidak menyusut ke seluruh graph.

## Acceptance P01–P05

Ekspektasi khusus snapshot 2026-10-01, **bukan aturan di komponen**. UI hanya mengurutkan
berdasarkan rank API. ID terverifikasi pada tindakan ditampilkan sebagai tautan nama/tanggal;
teks asli API utuh ada di disclosure. Tidak mengubah kata tindakan, syarat atau negasi.

| Deal | Prioritas API | Yang harus tetap terlihat | Bukti / batas |
| --- | --- | --- | --- |
| P04 | #1 acceleration / ready | Pengalaman terbaru, kesediaan dan izin kontak C06 sebelum perkenalan; overlap K028/K116 bukan kenalan terkonfirmasi. | I0335; employment K028/K116 → overlap inferred. |
| P01 | #2 acceleration / ready | Rina Hapsari identitas inferensi yang perlu dikonfirmasi; jangan menjanjikan tanggal fitur tanpa keputusan. | I0343, K017 dan employment. |
| P02 | #3 acceleration / ready | Permintaan diskon 20% bukan approval; VP Sales (E01) memutuskan dan mencatat di decision_log. | I0348 request; preseden D-2025-02/06 bukan approval P02. |
| P03 | #4 acceleration / ready | Pengalaman terbaru, kesediaan, izin kontak sebelum perkenalan; kandidat bukan izin; catatan C03 tetap utuh. | I0334; shortlist dari API. |
| P05 | #5 discovery / insufficient_evidence | Discovery sebelum harga/paket; skor null bukan 0; bukan kalah/low risk. | DL-005; unknowns tetap ada. |

Owner hanya bernama bila record employees.csv dengan employee_id sama ada di data deal;
selain itu tampil “ID karyawan …”. Approval kosong bukan disetujui. Unknowns tambahan
analisis tampil di kartu tindakan; seluruh unknowns ada di Alasan & bukti.

## Alur sumber ke peta hubungan

1. P02 → Alasan & bukti → bukti `interactions.jsonl:I0348` → panel: 28 Sep 2026, kutipan
   permintaan; file/ID dan JSON asli di “Detail sumber · I0348”. “Tampilkan di peta hubungan: I0348” membuka peta pada
   titik tersebut (layar sempit: sheet ditutup, fokus ke peta).
2. Relasi I0348 → P02 (interaction_for, langsung dari data) dapat dipilih dari peta,
   daftar relasi atau “Relasi dalam jalur ini”; panel menampilkan arah asli dan tanggal.
3. Keputusan terdahulu D-2025-06: kandidat inferred, bukan persetujuan untuk deal ini.
4. P04 sumber employment K028: locator baris tidak dijadikan titik; “Relasi yang memakai
   record ini” → overlapping_employment K028/K116, inferred, 1 Feb 2015–30 Nov 2019.
5. Record tanpa relasi menyatakan hal itu; tidak ada hubungan yang dibuat-buat.

## Harness MOCK (Vite development saja)

`/tests/session-harness.html` — banner **MOCK REQUEST TEST** wajib terlihat; komponen
produksi sama, transport sintetis, tanpa ranking (daftar urutan CRM, tidak ada pilihan
otomatis).

- Pilih deal, Respons “Gagal 503”, “Jalankan analisis untuk deal ini”: muncul “Analisis
  belum dapat dimuat” + “Coba lagi”, tanpa hasil. Ganti “Sukses segera”, Coba lagi:
  “MOCK usulan untuk <deal>” berlabel “Rekaman analisis (replay) · fixture”.
- “Sukses terlambat 2,5 detik”, Jalankan analisis ulang, segera pindah deal: setelah
  2,5 detik deal baru tetap “Saran untuk deal ini belum tersedia”.

`/tests/phase3-harness.html` — banner **MOCK TRANSPORT TEST**; respons sukses dari API lokal.

- Endpoint Ranking, Gagal 503, pilih P02 lalu “Muat ulang daftar”: notice “Urutan prioritas
  belum dapat dimuat” + “Muat ulang urutan”; daftar urutan CRM tetap bisa dibuka, P02 tetap
  terbuka. Ganti Sukses API → “Muat ulang urutan”: urutan API kembali, P02 tetap pilihan.
- Endpoint Diagnostic, Gagal 503, Jelajahi data › Temuan dari data › “Muat ulang temuan
  deal ini”: error terisolasi, saran dan urutan tetap.
- Validasi corruption/timeout/501/network diuji otomatis; jangan klaim sebagai outage nyata.

Build produksi hanya memakai index.html; harness, viewport.html dan fixture tidak masuk dist.

## Fixture dan script opsional

Fixture development (tombol “Pratinjau fixture (dev)”) memakai proyeksi kecil P02 dengan
banner wajib; bukan hasil backend/Jev dan bukan bukti skala graph.

`tests/browser.mjs` adalah skenario Playwright opsional (label redesign, cek tanpa POST).
**Belum dijalankan** pada penyerahan redesign karena Playwright tidak terpasang; pemeriksaan
browser aktual memakai Claude in Chrome. Jangan menganggap script ini lulus.

```bash
PLAYWRIGHT_MODULE=/path/to/playwright node frontend/tests/browser.mjs
```

## Naskah demo 90 detik

**0:00–0:15.** “Ini prioritas tindak lanjut dari API. Nomor 1 Nirwana Hotel & Resto sudah
terbuka. Ini urutan perhatian sales, bukan peluang closing.”
**0:15–0:40.** Saran tindakan P04: tindakan (cek pengalaman
terbaru, kesediaan dan izin kontak Saiyo Group sebelum perkenalan), Bagus Prakoso, target,
persetujuan 0 yang bukan berarti disetujui.
**0:40–0:55.** “Lihat bukti I0335” → email asli, tanggal, pengirim. Esc menutup.
**0:55–1:10.** “Lihat hubungan yang mendukung saran ini” → tiga jalur disorot; garis putus
adalah dugaan, overlap kerja bukan kenalan terkonfirmasi.
**1:10–1:25.** Pilih #3 Teras Kafe: permintaan diskon 20% belum disetujui; VP Sales harus
memutuskan dan mencatat.
**1:25–1:30.** Pilih #5: “Lengkapi informasi” — bukan gagal atau bebas risiko. “Demo ini
mode rules, bukan Jev live.”

## Naskah demo mentor (sekitar 4 menit)

**0:00–0:40 — prioritas.** Beranda: lima deal urutan API (P04, P01, P02, P03, P05 pada
snapshot ini). Buka “Bagaimana urutan ini dibuat?”: skor, tie-break, keterbatasan dari API,
belum tervalidasi terhadap closing historis.
**0:40–1:30 — P04/P01.** P04: kutipan “Kami tunda dulu sampai ada referensi”, tindakan dan
penanggung jawab. P01: Rina Hapsari masih identitas inferensi yang perlu dikonfirmasi.
**1:30–2:20 — gate P02.** Persetujuan VP Sales tampil di kartu tindakan. Alasan & bukti →
jalur DL-002 → P02 ← I0348 → “Lihat jalur ini di peta” → pilih relasi I0348 → P02, cek tanggal
28 Sep dan kutipan. Peta menyebut jumlah titik terlihat dari total 1.305.
**2:20–3:20 — temuan dan bukti.** Jelajahi data › Temuan dari data: fakta, interpretasi,
informasi kurang dan hal yang perlu diperiksa terpisah; statistik not_assessed. Opsional
P04 employment → overlap inferred.
**3:20–4:00 — discovery dan batas.** P05: Lengkapi informasi, skor null. Bila menjalankan
analisis ulang, tunjukkan label asal hasil dan nomor prioritas yang tetap. “Usulan perlu
tinjauan manusia; kami belum mengukur dampak closing; demo ini rules, bukan Jev live.”

Hasil aktual, screenshot sebelum/sesudah, keterbatasan dan waktu WIB ada di
`docs/handoffs/BOY.md`.

## Hasil lanjutan Main/Codex — desktop saja

9 Oktober 2026, macOS. **73/73 lulus, build lulus**. Rincian perintah di atas:
31 tes helper/graph/session/presentation + 42 transport/render. Backend rules lokal 8000,
frontend review PR #29 port 5174. Tiga tes baru memeriksa ID terverifikasi, penolakan ID
interaksi ambigu/tidak cocok, dan label sumber yang mempertahankan null/0/JSON asli.
Assertion urutan render di analysis/phase3 diubah mengikuti tindakan lebih dahulu;
assertion bisnis/provenance tetap dipertahankan.

CUA browser nyata: P01–P05, 1280×720 dan 1440×900 tanpa overflow horizontal, sumber E06
berlabel, I0348 dalam drawer, preseden D-2024-02 terbuka, Jalur 1 P02 dengan Enter,
gabungan tiga jalur P04, overlap inferred melalui daftar relasi, Escape dan fokus kembali.
Warn/error log yang tersedia pada pengecekan akhir kosong. Klik SVG via alat otomasi
mengalami timeout; relasi yang sama berhasil dibuka melalui daftar relasi. Tidak mengklaim
seluruh harness atau `browser.mjs` sudah dijalankan; tes lifecycle otomatis tetap lulus.

Screenshot lanjutan: `tests/screenshots/main-desktop-1440.jpg`, `main-desktop-1280.jpg`,
`main-source-1440.jpg`, `main-graph-p04-1440.jpg`. Foto baseline/hasil Ical tetap disimpan.
Riset Mobbin, alasan keputusan dan batas di [UX_DESKTOP_RESEARCH.md](UX_DESKTOP_RESEARCH.md).
Uji kegunaan manusia, mobile terbaru, Jev live dan dampak bisnis belum diukur.
