# Handoff BOY

Pelaksana tugas redesign: Ical, atas penugasan pengguna/Main; area frontend sebelumnya dikerjakan Boy.

## Task dan status
**Redesign UI/UX frontend untuk sales non-teknis: READY_FOR_REVIEW.**
Fondasi Ical (GitHub IXALS)/Claude Code; WIP 3b683dd dilanjutkan Main/Codex atas instruksi
pengguna, fokus desktop. Implementasi dan verifikasi lokal selesai; PR #29 diperbarui,
belum merged/deployed. Hasil uji Main dipisahkan dari run Ical di bawah.

Instruksi terbaru pengguna di tengah pengerjaan: fokus **desktop**, tampilan bersih dan
profesional, buang informasi yang tidak penting, lewati masalah mobile. Tata letak mobile
tetap ada sebagai dukungan dasar, tetapi tidak dipoles atau diverifikasi ulang setelah
penyederhanaan terakhir.

Riwayat yang tetap milik Boy: BOY-02..04 dikerjakan Boy; BOY-04 MERGED #22 (ea96e23) dan
VERIFIED oleh Main menurut `docs/coordination/MAIN.md`. Catatan lengkap BOY-04 ada di riwayat
git file ini (commit a392907) dan `docs/reviews/2026-10-09-boy04.md`. Hasil uji Boy tidak
diklaim ulang di sini; run awal di bawah milik Ical; run lanjutan Main ditandai terpisah.

- [x] Mulai dari origin/main terbaru b766770; branch baru; checkout sendiri.
- [x] Membaca AGENTS.md, MAIN.md, API_CONTRACT.md, BOY.md, ICAL.md, frontend/TESTING.md,
  evaluation/MENTOR_BRIEF.md dan DEMO_CLAIMS.md.
- [x] Beranda prioritas, detail “saran dulu”, tiga lapisan informasi, panel bukti saat
  diminta, peta hubungan sebagai bukti saran.
- [x] Tanpa POST otomatis; versi saran eksplisit; state loading/gagal tidak tampil sebagai sukses.
- [x] Run awal Ical: 70/70 tes; lanjutan Main: 73/73 tes, build dan browser desktop.
- [x] Riset Mobbin MCP (5 screen), tindakan lebih dahulu, antrean ringkas, sumber manusiawi.
- [x] Catatan riset, screenshot lanjutan, dan instruksi uji diperbarui.
- [ ] Uji kegunaan dengan rekan tim: **belum dilakukan** (target 10 detik/30 detik/≤2 interaksi
  belum diukur).

### Iterasi final berdasarkan feedback sales — Main/Codex

- [x] Mobbin MCP: 5 flow + 7 screen baru; keputusan dan seluruh inventaris UI dicatat di
  `frontend/UX_SALES_FLOW_RESEARCH.md`.
- [x] Panduan kontekstual, overview tugas singkat, satu CTA **Siapkan tindak lanjut**.
- [x] Modal rencana yang bisa diperiksa/disalin; seluruh teks bisnis dan sumber ikut export.
- [x] Nama deal/tab sticky, default graph jalur API, kontrol advanced terlipat, search recovery.
- [x] 77 frontend tests, build; browser desktop, modal keyboard dua arah, sumber → graph.
- [ ] Usability sales manusia dan clipboard lintas aplikasi oleh pengguna belum diverifikasi.

### Iterasi visual Mixpanel — Main/Codex, 10 Oktober 00:57 WIB

- [x] Riset Mobbin MCP: 4 screen Mixpanel + 3 preview flow; observasi dan keputusan dalam
  `frontend/UX_MIXPANEL_RESEARCH.md`, termasuk batas relevansi flow yang dikembalikan.
- [x] Sidebar workspace terang, aksen ungu, tiga kartu ringkasan API, grid tindakan + bukti.
- [x] `frontend/src/mixpanel.css`: token/frame/cards/graph/drawer/dialog/interaksi desktop.
- [x] `Dashboard`, `DealWorkspace`, `ActionOverview`, `main`: hierarki visual dan metadata;
  `ContextGraph`: legenda ungu selaras warna; tidak ada perubahan path/edge/scoring/API.
- [x] 77/77 tes frontend diulang, build PASS, browser 1440×900 dan 1280×720 tanpa overflow
  horizontal; kelima deal diperiksa, sumber I0335 → graph fokus, dialog keyboard/P02 gate.
- [x] Screenshot `frontend/tests/screenshots/mixpanel-*.png`; panduan uji diperbarui.
- [ ] Uji kegunaan manusia, audit aksesibilitas penuh dan Jev live belum dilakukan.

Iterasi ini mengikuti feedback terbaru pengguna untuk inspirasi Mixpanel. Ringkasan tiga
metrik dikembalikan sebagai kartu ringkas; masalah utama tetap diselesaikan dengan judul
langkah, owner, target, syarat dan satu CTA. Halaman dapat scroll vertikal; tidak mengklaim
seluruh informasi/CTA muat tanpa scroll di semua ukuran. Status READY_FOR_REVIEW; PR #29.

### Iterasi compact berdasarkan feedback terbaru — Main/Codex, 10 Oktober 01:29 WIB

Iterasi ini menggantikan keputusan tiga kartu metrik/panel bukti di iterasi 00:57 di atas.

- [x] Riset Mobbin MCP: Linear issue detail + flow, Attio company records; tautan,
  observasi, batas riset dan seluruh perubahan di `frontend/UX_COMPACT_RESEARCH.md`.
- [x] `Dashboard`: hapus banner panduan permanen dan teks sidebar berulang; refresh ikon,
  bantuan opsional. `DealWorkspace`: properti inline, tab pendek, intro graph ringkas.
- [x] `ActionOverview`, `gateLabel`: satu tindakan, owner inline, syarat ringkas tetap
  terlihat, rincian utuh dapat dibuka. Session tidak mewarisi gate prioritas.
- [x] `DealTabs`: kontrol versi/analisis dikelompokkan; pending/error tetap terlihat.
  `AnalysisReport`/`EvidenceBrowser`: daftar sumber ringkas tanpa JSON/ID komposit di preview.
- [x] `ContextGraph`: legenda garis visual; `FollowUpPlan`: dialog singkat, seluruh syarat
  dan sumber tetap utuh. Tidak mengubah ranking/API/graph/dependency/backend.
- [x] 78/78 frontend tests (31 ESM + 47 CJS), build PASS. HTTP regression menggunakan server
  rules sendiri port 8001; tidak memanggil Jev live untuk pekerjaan redesign ini.
- [x] Browser desktop 1280×720 dan 1440×900: tanpa overflow horizontal, CTA default P04
  terlihat tanpa scroll (batas bawah sekitar 620px); kelima deal/gate diperiksa.
- [x] P02 approval lengkap, sumber I0348 → graph fokus 3 titik/2 relasi; P04 modal dengan
  consent, Tab/Escape/focus return; pencarian kosong → hapus → hasil pulih.
- [x] Screenshot `frontend/tests/screenshots/compact-desktop-{1280,1440}.png`.
- [ ] Uji kegunaan manusia dan copy lintas aplikasi belum diverifikasi; mobile di luar scope.

Fungsi baru: `gateLabel(priority, source, approvals)` menerjemahkan syarat API ke label
singkat; teks kondisi asli tetap tersedia. Status **READY_FOR_REVIEW**, PR #29 belum merge.

### Masalah UX utama dan perbaikannya

1. Prioritas tertutup hero, tiga metrik dan kotak ranking; detail deal di bawah lipatan →
   tata letak master-detail: daftar prioritas kiri, saran kanan, langsung di layar pertama.
2. Deal default P01 (urutan CRM) padahal prioritas #1 P04 → default ke rank 1 dari API;
   pilihan pengguna tidak ditimpa saat ranking datang atau dimuat ulang.
3. Status bertentangan (“Status konteks CRM: Belum dianalisis” di samping “Analisis tersedia”,
   “Status request sesi”) → satu baris asal saran; status CRM pindah ke Rincian teknis.
4. Istilah teknis (acceleration, GET/POST, rules, inferred, milestone, preseden) → bahasa
   sehari-hari: Percepat tindak lanjut/Lengkapi informasi, Analisis berbasis aturan, Dugaan dari
   hubungan data, Target langkah berikutnya, Keputusan terdahulu.
5. Tindakan terpecah lima langkah bernomor dan didahului formula skor → satu kartu tindakan:
   tindakan, penanggung jawab (nama dari employees.csv), target, persetujuan, hal yang perlu
   dipastikan. Formula pindah ke Alasan & bukti (terlipat) dan Jelajahi data.
6. Inspector kosong selalu memakan sepertiga lebar; bukti tanpa judul manusiawi → panel bukti
   hanya saat dipilih, judul dari field record, kutipan, tanggal, pengirim; ID/JSON terlipat.
7. Graph terpisah dari saran → “Lihat hubungan yang mendukung saran ini” membuka gabungan jalur
   API yang disorot; arah, langsung/dugaan dan provenance tetap.
8. Informasi ganda/ringan nilai (total pipeline, label jenis berulang, catatan kosong) dibuang
   dari tampilan utama.

### Peta fitur lama → lokasi baru

| Lama | Baru |
| --- | --- |
| Hero “Langkah tepat. Deal bergerak.” + tiga metrik | Dihapus. Potensi per deal tetap di daftar dan header deal; total pipeline tidak ditampilkan. |
| Ranking pipeline · rules + Metode & keterbatasan | Baris status di atas daftar + “Bagaimana urutan ini dibuat?” + Jelajahi data › Cara prioritas dihitung |
| Kartu deal lima kolom + pencarian deal | Daftar prioritas vertikal (nomor, nama, tahap, potensi, badge persetujuan/discovery). Pencarian dihapus: hanya lima deal. |
| Header ruang keputusan + “Analisis langkah berikutnya” | Header deal ringkas; “Jalankan analisis ulang” di bawah kartu tindakan |
| Status request sesi / status konteks CRM | Baris asal saran; status CRM, endpoint dan status request di Jelajahi data › Rincian teknis |
| Tab Ringkasan, PriorityPanel, langkah bernomor | Tab Saran tindakan (lapisan 1) + Alasan & bukti (lapisan 2) |
| Faktor, keterbatasan, sumber prioritas | Jelajahi data › Cara prioritas dihitung |
| Tab Peta relasi | Jelajahi data › Peta hubungan; tombol jalur dari kartu tindakan |
| Tab Bukti (jumlah) | Jelajahi data › Semua bukti (jumlah) |
| Inspector kanan permanen | Panel “Bukti & sumber” saat dipilih (samping ≥1800 px, sheet modal di bawahnya) |
| Diagnostic | Jelajahi data › Temuan dari data (+ “Muat ulang temuan deal ini”) |
| Muat ulang konteks / dashboard | Rincian teknis › “Muat ulang data deal”; “Muat ulang daftar” di bawah daftar |
| Tombol versi Rekomendasi ranking / Analisis sesi | Toggle “Saran dari urutan prioritas” / “Hasil analisis ulang · jam”, muncul hanya bila ada hasil |
| Sidebar + toggle fixture | Header ringkas; “Pratinjau fixture (dev)” hanya di mode dev |

## Branch dan commit
Branch **boy/ical-uiux-redesign** dari origin/main **b766770** (Merge PR #28), di-fetch ulang
sebelum push. Checkout sendiri `C:\Users\4nemy\Downloads\Coding\HACKATHON-2026\dealcompass`.
Commit awal Ical 3b683dd. Main melanjutkan di checkout review tersendiri, branch lokal
`integrator/desktop-ux`, dan push ke head PR yang sama `boy/ical-uiux-redesign`.
Server pratinjau lanjutan 5174; server anggota lain 5173/8000 tidak dihentikan.

## File dan fungsi
- Iterasi final: `ActionOverview.tsx` (judul tujuan/gate, owner, target, persiapan),
  `FollowUpPlan.tsx` (native dialog, salin, error fallback, keyboard wrap), `lib/planning.ts`
  (label gate exact-match, fallback generik, export verbatim dengan provenance).
- `Dashboard.tsx` menambah panduan; `DealWorkspace.tsx` navigasi sticky dan jalur default
  yang tidak menimpa fokus sumber; ContextGraph advanced disclosure; EvidenceBrowser recovery.
- `frontend/UX_SALES_FLOW_RESEARCH.md`: riset 12 referensi, matriks seluruh layar/state,
  micro-interactions, batas produk dan rehearsal. Bagian file awal di bawah adalah riwayat.

- `frontend/src/main.tsx`: header ringkas (merek, konteks, tombol fixture khusus dev).
- `frontend/src/Dashboard.tsx`: master-detail; daftar prioritas; `effectiveSelection`; status
  ranking loading/siap/gagal/tidak tersedia; GET ranking dan temuan saat muat, tanpa POST.
- `frontend/src/components/DealWorkspace.tsx`: tab Saran tindakan / Alasan & bukti / Jelajahi
  data (tablist keyboard), subnav lapisan 3, panel bukti dengan fokus pindah/kembali, analisis
  ulang eksplisit, pilihan versi, peta dengan jalur pendukung. Pembatalan, guard snapshot/akun
  dan isolasi error lama dipertahankan.
- `frontend/src/components/DealTabs.tsx` (baru): WhyBlock, ActionTab, ReasonsTab.
- `frontend/src/components/AnalysisReport.tsx`: ActionSummary satu kartu, OwnerLabel (nama hanya
  dari record employees.csv dengan employee_id sama), RecommendationSources, PrecedentList,
  ExplanationGroups, UnknownList; ReadableAction mengganti ID terverifikasi dengan tautan
  sumber nama/tanggal, seluruh kata/negasi/syarat utuh dan teks asli dapat dibuka.
- `frontend/src/components/Phase3Panels.tsx`: PriorityRationale (terlipat), EvidencePaths
  (rantai bernama, arah relasi asli, “dugaan”), PriorityFactors, Methodology, DiagnosticPanel,
  Statistics, Sources, DetailData.
- `frontend/src/components/EvidencePanel.tsx`: EvidenceInspector, EvidenceCard, EvidenceDrawer
  (panel samping non-modal atau `dialog` modal); SourceContent menyajikan field berlabel,
  data kosong tetap eksplisit, JSON mentah tetap tersedia.
- `frontend/src/components/EvidenceBrowser.tsx`: seluruh bukti dengan judul manusiawi.
- `frontend/src/components/ContextGraph.tsx`: `initialPaths` (gabungan jalur, sorot), label titik
  manusiawi, relasi bahasa biasa, kanvas sebelum kontrol eksplorasi; batas 24 titik, pencarian,
  perluas, filter dan daftar relasi tetap.
- `frontend/src/components/Notice.tsx` (baru), `Icon.tsx`, `lib/format.ts`, `lib/useMedia.ts` (baru).
- `frontend/src/lib/present.ts` (baru): helper presentasi murni (label, pilihan default, versi
  saran, judul bukti, frasa relasi, arah jalur). Tidak menghitung skor/approval.
- `frontend/src/style.css`: ditulis ulang dengan identitas lama (hijau gelap, latar terang,
  terakota untuk aksi utama), skala tipe 12–26 px, target 40–46 px, fokus terlihat, warna
  status selalu bersama teks, reduced motion, selection/scrollbar bertema.
- `frontend/tests/present.test.mjs` (12) dan `redesign.test.cjs` (9) baru; `analysis.test.cjs`
  dan `phase3.test.cjs` memakai komponen baru tanpa menghapus assertion bisnis/provenance/
  lifecycle; `browser.mjs` diperbarui (belum dijalankan); `viewport.html` alat bantu dev;
  `screenshots/` sebelum/sesudah.
- `frontend/TESTING.md`: prosedur 73 tes, langkah browser, harness MOCK, naskah demo.

- `frontend/UX_DESKTOP_RESEARCH.md`: lima referensi Mobbin, keputusan desain dan batas.

## Kontrak dan dependency
API v1 dan snapshot 2026-10-01 tetap. Tidak menyentuh backend/decision, backend/graph, dataset,
ranking, formula, kebijakan approval, kontrak/validasi bersama, package.json, lockfile, CI atau
docs/coordination. Tidak ada dependency baru. Tidak ada aturan bisnis atau aturan per-ID di
komponen; tidak ada ringkasan LLM atau pemotongan yang membuang negasi/syarat/approval.
Label mesin mengikuti `engine_mode` respons (rules → “Analisis berbasis aturan”). Jev live tidak
diuji. Tidak ada kebutuhan backend baru untuk Main.

## Cara menjalankan
Dari root repo, dua terminal:

```bash
env -u TYPESAFE_API_KEY DEALCOMPASS_ENGINE_MODE=rules python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
npm --prefix frontend run dev -- --port 5173 --strictPort
```

Buka http://127.0.0.1:5173. Prioritas #1 terbuka otomatis; pilih deal lain di daftar kiri.
Perintah tes lengkap: `frontend/TESTING.md`.

### Naskah demo 90 detik
- **0:00–0:15** Beranda: “Prioritas tindak lanjut dari API; #1 Nirwana Hotel & Resto sudah
  terbuka. Ini urutan perhatian, bukan peluang closing.”
- **0:15–0:40** Tindakan (cek pengalaman terbaru, kesediaan dan
  izin kontak Saiyo Group sebelum perkenalan), Bagus Prakoso (E06), target; persetujuan kosong
  bukan berarti disetujui.
- **0:40–0:55** “Lihat bukti I0335” → email asli 22 Sep, pengirim; Esc menutup.
- **0:55–1:10** “Lihat hubungan yang mendukung saran ini” → tiga jalur disorot; garis putus =
  dugaan, overlap kerja bukan kenalan terkonfirmasi.
- **1:10–1:25** #3 Teras Kafe: permintaan diskon 20% bukan persetujuan; VP Sales (E01) harus
  memutuskan dan mencatat di decision_log.
- **1:25–1:30** #5: “Lengkapi informasi”, bukan gagal/kalah/bebas risiko. “Mode rules, bukan Jev live.”

## Pengujian aktual

### Run final alur sales Main/Codex
77/77 frontend lulus: 31 helper + 46 transport/render. Build lulus. Browser nyata overview
P01–P05, rencana P02/P04, copy-success UI, Tab/Shift+Tab wrap, Escape/fokus kembali,
source I0335 → graph sumber spesifik, search empty dan retry 502 pulih setelah menyalakan
backend rules pada port kosong 8000. 1440×900 dan viewport harness iframe 1280×720 diverifikasi
ukuran/overflow via DOM; footer modal laptop terlihat. Isi export diuji utuh untuk semua deal.
API baca clipboard alat menghasilkan kosong: belum mengklaim verifikasi clipboard OS.
Run 73/70 di bawah adalah riwayat iterasi sebelumnya, bukan total terbaru.


### Lanjutan Main/Codex (desktop)
73/73 frontend lulus (31 + 42), build TypeScript/Vite lulus. Perintah lengkap di
`frontend/TESTING.md`. Browser nyata P01–P05; screenshot 1280×720 dan 1440×900 tanpa overflow;
source E06 readable; P02 I0348, preseden D-2024-02 dan Jalur 1 dapat diperiksa; keyboard Enter
membuka jalur; P04 tiga jalur graph dan overlap inferred lewat daftar relasi, Escape/fokus
kembali berhasil. Warn/error browser yang tersedia saat akhir kosong. SVG pointer via alat
otomasi timeout; jalur alternatif daftar relasi lulus, tidak diklaim sebagai klik SVG lulus.
Screenshot prefiks `main-` dan riset lima screen Mobbin tercatat di UX_DESKTOP_RESEARCH.md.
Tidak menjalankan uji mobile baru, uji manusia, atau Jev live.

### Run awal Ical

Run Ical, 2026-10-09, Windows 11, Node 24.19, backend lokal rules tanpa TYPESAFE_API_KEY.
**70/70 lulus, 0 gagal/skip; build TypeScript/Vite lulus.** Perintah persis di `frontend/TESTING.md`.

| Suite | Hasil | Catatan |
| --- | --- | --- |
| contracts + graph | 13/13 | graph GET nyata DL-001..005 |
| api transport | 7/7 | mock transport |
| session + present | 18/18 | mock promise; helper sintetis |
| analysis | 8/8 | POST rules nyata lima deal dirender ActionTab+ReasonsTab |
| phase3 | 18/18 | GET nyata + corruption/mock berlabel |
| redesign | 6/6 | GET nyata, MOCK state, STATIC guard tanpa POST otomatis |

- Detektor desain Impeccable pada file UI yang diubah: 0 temuan (satu temuan garis bawah tab
  diperbaiki).
- Browser nyata (Claude in Chrome, backend rules 127.0.0.1:8000, Vite 5173):
  - Muat beranda empat kali: hanya GET `/api/deals`, `/api/pipeline/priorities`,
    `/api/pipeline/initial-analysis`, `/api/deals/DL-004`. Satu-satunya POST
    `/api/deals/DL-005/analyze` (200) muncul setelah klik “Jalankan analisis ulang”.
  - Default P04; P01 menampilkan Rina Hapsari sebagai identitas inferensi; P02 menampilkan
    persetujuan VP Sales (E01) di kartu tindakan; P05 “Lengkapi informasi” dan discovery.
  - Panel bukti I0335/I0348: judul subjek, kutipan, pengirim/penerima, detail sumber; Enter
    membuka, Esc/Tutup menutup, fokus kembali ke pemicu. Tab detail: panah/Home/End.
  - Peta: P04 3 jalur (6 titik, 6 relasi disorot), P02 6 jalur (11 titik, 10 relasi disorot).
  - Harness MOCK: analisis 503 → “Coba lagi” → sukses MOCK berlabel replay; sukses terlambat
    setelah pindah deal tidak menimpa. Ranking 503 → daftar urutan CRM tetap bisa dibuka,
    pilihan P02 tetap; “Muat ulang urutan” memulihkan urutan API tanpa memindah pilihan.
  - Kontras teks HTML di ketiga tab: tidak ada pasangan <4,5:1 (pemindaian JS); teks SVG dicek
    manual. `scrollWidth <= innerWidth` pada 1440×900 dan 1280×720.
  - Catatan lingkungan: tab otomasi berstatus hidden sehingga requestAnimationFrame tertahan;
    pemindahan fokus diganti ke effect setelah commit dan diverifikasi ulang.
  - Mobile 390×844 dan 640×360 (200%) dicek sebelum penyederhanaan desktop terakhir; tidak
    diulang setelahnya karena mobile di luar fokus terbaru.
- Screenshot sebelum (origin/main b766770, server 5174 dengan backend yang sama) dan sesudah,
  di `frontend/tests/screenshots/`:
  - `before-desktop-1440x900.jpg` / `after-desktop-1440x900.jpg` — muat awal, headless Chrome
    viewport persis.
  - `before-laptop-1280x720.jpg` / `after-laptop-1280x720.jpg` — muat awal, headless Chrome.
  - `before-detail-P01-ringkasan.jpg`, `before-detail-P01-tindakan.jpg` (UI lama, jendela
    ±1568×935 diskalakan) / `after-detail-P01-1440x900.jpg` (viewport 1440×900, gambar 1389×868).
  - `after-evidence-drawer-P02-1440x900.jpg`, `after-graph-paths-P02-1440x900.jpg`.

| Deal | Prioritas API | Yang terlihat di lapisan 1 (teks API) | Bukti / batas |
| --- | --- | --- | --- |
| P04 | #1 | Cek pengalaman terbaru, kesediaan, izin kontak C06 sebelum perkenalan; Bagus Prakoso (E06) | I0335; overlap K028/K116 inferred, bukan kenalan |
| P01 | #2 | Rina Hapsari identitas inferensi perlu dikonfirmasi; jangan janji tanggal fitur | I0343; unknown sikap Rina tampil di kartu |
| P02 | #3 | Jangan tawarkan diskon 20% sebelum VP Sales memutuskan/mencatat; approval E01 | I0348 request ≠ approval; preseden bukan approval |
| P03 | #4 | Pengalaman terbaru, kesediaan, izin kontak sebelum perkenalan; consent kandidat belum diketahui | I0334; kandidat bukan izin |
| P05 | #5 | Discovery sebelum harga/paket; “bukan berarti tidak ada risiko” | DL-005; skor null bukan 0 |

Tidak dijalankan: uji kegunaan rekan tim, `frontend/tests/browser.mjs` (Playwright tidak
terpasang), Jev live, 144 tes backend milik Main (tidak diklaim).

## Fixture dan keterbatasan
Mock/sintetis/STATIC di tes diberi label; fixture dev tetap berbanner, kontrolnya terlipat
sebagai Alat pengembang. Tidak masuk build produksi. Tidak ada ranking per-ID di komponen.

Tindakan mempertahankan semua kata bisnis, negasi, dan syarat; ID karyawan/interaksi yang
terverifikasi menjadi nama/tanggal bertaut sumber, sedangkan teks API utuh dapat dibuka.
ID tidak cocok/ambigu tetap literal. Beberapa unknowns API (candidate_decisions) tetap literal.
Pratinjau bukti dapat dipotong, teks lengkap tetap di panel. Target fokus desktop;
mobile hanya dukungan dasar, tidak diuji ulang oleh Main. Tidak ada uji kegunaan manusia,
Jev live, klaim peningkatan closing, atau audit aksesibilitas penuh.

## Blocker
Tidak ada blocker implementasi. Menunggu review Main; tidak merge sendiri.

## Tugas berikutnya
1. Reviewer/tim mencoba pratinjau PR #29, khususnya kemudahan menemukan prioritas dan tindakan.
2. Uji satu anggota non-implementer: temukan deal pertama, jelaskan tindakan/owner/syarat,
   lalu buka bukti; catat waktu dan kebingungan. Target 10/30 detik belum diukur.
3. Setelah review dan CI lulus, integrasikan melalui alur Main; rehearsal 90 detik dan
   submission tetap pekerjaan tim. Tidak ada pekerjaan mobile tambahan untuk tugas ini.
4. Integrasi Jev live dilanjutkan terpisah pada PR #30; perubahan frontend di sini tidak
   mengubah integrasi atau ledger tersebut. Riwayat belum-live di atas merujuk run terdahulu.

Catatan pelanjut: pertahankan pendingFocus + useEffect, POST hanya melalui analyze(),
provenance dan semua gate bisnis. Jangan mengganti saran dengan ringkasan yang membuang syarat.

## Update WIB
2026-10-10 01:29 WIB — iterasi compact desktop READY_FOR_REVIEW pada PR #29. 78/78 frontend,
build dan pemeriksaan browser desktop; catatan riset Mobbin diperbarui. Belum merged/deployed.
Implementasi awal Ical, lanjutan Main; riwayat BOY-04 tetap milik Boy.
