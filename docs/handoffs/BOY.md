# Handoff BOY

Pelaksana tugas redesign: Ical, atas penugasan pengguna/Main; area frontend sebelumnya dikerjakan Boy.

## Task dan status
**Redesign UI/UX frontend untuk sales non-teknis: IN_PROGRESS — diserahkan ke Codex
untuk dilanjutkan.** Pelaksana Ical (GitHub IXALS) dibantu Claude Code. Implementasi inti,
tes dan dokumentasi sudah ada; sisa pekerjaan di bagian “Tugas berikutnya”. Main menetapkan
VERIFIED/MERGED. Tidak merge sendiri, tidak deploy.

Instruksi terbaru pengguna di tengah pengerjaan: fokus **desktop**, tampilan bersih dan
profesional, buang informasi yang tidak penting, lewati masalah mobile. Tata letak mobile
tetap ada sebagai dukungan dasar, tetapi tidak dipoles atau diverifikasi ulang setelah
penyederhanaan terakhir.

Riwayat yang tetap milik Boy: BOY-02..04 dikerjakan Boy; BOY-04 MERGED #22 (ea96e23) dan
VERIFIED oleh Main menurut `docs/coordination/MAIN.md`. Catatan lengkap BOY-04 ada di riwayat
git file ini (commit a392907) dan `docs/reviews/2026-10-09-boy04.md`. Hasil uji Boy tidak
diklaim ulang di sini; angka di bawah adalah run Ical.

- [x] Mulai dari origin/main terbaru b766770; branch baru; checkout sendiri.
- [x] Membaca AGENTS.md, MAIN.md, API_CONTRACT.md, BOY.md, ICAL.md, frontend/TESTING.md,
  evaluation/MENTOR_BRIEF.md dan DEMO_CLAIMS.md.
- [x] Beranda prioritas, detail “saran dulu”, tiga lapisan informasi, panel bukti saat
  diminta, peta hubungan sebagai bukti saran.
- [x] Tanpa POST otomatis; versi saran eksplisit; state loading/gagal tidak tampil sebagai sukses.
- [x] 70/70 tes frontend, build produksi, browser nyata desktop, screenshot sebelum/sesudah.
- [ ] Uji kegunaan dengan rekan tim: **belum dilakukan** (target 10 detik/30 detik/≤2 interaksi
  belum diukur).

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
| Kartu deal lima kolom + pencarian deal | Daftar prioritas vertikal (nomor, nama, tahap, potensi, syarat utama). Pencarian dihapus: hanya lima deal. |
| Header ruang keputusan + “Analisis langkah berikutnya” | Header deal ringkas; “Jalankan analisis ulang” di bawah kartu tindakan |
| Status request sesi / status konteks CRM | Baris asal saran; status CRM, endpoint dan status request di Jelajahi data › Rincian teknis |
| Tab Ringkasan, PriorityPanel, langkah bernomor | Tab Saran tindakan (lapisan 1) + Alasan & bukti (lapisan 2) |
| Faktor, keterbatasan, sumber prioritas | Jelajahi data › Cara prioritas dihitung |
| Tab Peta relasi | Jelajahi data › Peta hubungan; tombol jalur dari kartu tindakan |
| Tab Bukti (jumlah) | Jelajahi data › Semua bukti (jumlah) |
| Inspector kanan permanen | Panel “Bukti & sumber” saat dipilih (samping ≥1200 px, sheet modal di bawahnya) |
| Diagnostic | Jelajahi data › Temuan dari data (+ “Muat ulang temuan deal ini”) |
| Muat ulang konteks / dashboard | Rincian teknis › “Muat ulang data deal”; “Muat ulang daftar” di bawah daftar |
| Tombol versi Rekomendasi ranking / Analisis sesi | Toggle “Saran dari urutan prioritas” / “Hasil analisis ulang · jam”, muncul hanya bila ada hasil |
| Sidebar + toggle fixture | Header ringkas; “Pratinjau fixture (dev)” hanya di mode dev |

## Branch dan commit
Branch **boy/ical-uiux-redesign** dari origin/main **b766770** (Merge PR #28), di-fetch ulang
sebelum push. Checkout sendiri `C:\Users\4nemy\Downloads\Coding\HACKATHON-2026\dealcompass`.
Satu commit redesign; SHA tercantum di PR. Checkout, branch dan server demo anggota lain tidak
disentuh.

## File dan fungsi
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
  ExplanationGroups, UnknownList. Teks API utuh.
- `frontend/src/components/Phase3Panels.tsx`: PriorityRationale (terlipat), EvidencePaths
  (rantai bernama, arah relasi asli, “dugaan”), PriorityFactors, Methodology, DiagnosticPanel,
  Statistics, Sources, DetailData.
- `frontend/src/components/EvidencePanel.tsx`: EvidenceInspector, EvidenceCard, EvidenceDrawer
  (panel samping non-modal atau `dialog` modal).
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
- `frontend/tests/present.test.mjs` (12) dan `redesign.test.cjs` (6) baru; `analysis.test.cjs`
  dan `phase3.test.cjs` memakai komponen baru tanpa menghapus assertion bisnis/provenance/
  lifecycle; `browser.mjs` diperbarui (belum dijalankan); `viewport.html` alat bantu dev;
  `screenshots/` sebelum/sesudah.
- `frontend/TESTING.md`: prosedur 70 tes, langkah browser, harness MOCK, naskah demo.

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
- **0:15–0:40** Kutipan pelanggan, syarat utama, tindakan (cek pengalaman terbaru, kesediaan dan
  izin kontak Saiyo Group sebelum perkenalan), Bagus Prakoso (E06), target; persetujuan kosong
  bukan berarti disetujui.
- **0:40–0:55** “Lihat bukti I0335” → email asli 22 Sep, pengirim; Esc menutup.
- **0:55–1:10** “Lihat hubungan yang mendukung saran ini” → tiga jalur disorot; garis putus =
  dugaan, overlap kerja bukan kenalan terkonfirmasi.
- **1:10–1:25** #3 Teras Kafe: permintaan diskon 20% bukan persetujuan; VP Sales (E01) harus
  memutuskan dan mencatat di decision_log.
- **1:25–1:30** #5: “Lengkapi informasi”, bukan gagal/kalah/bebas risiko. “Mode rules, bukan Jev live.”

## Pengujian aktual
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
Mock/sintetis/STATIC di tes diberi label; harness MOCK dan fixture dev berbanner dan tidak
masuk build produksi. Ekspektasi P01–P05 hanya di tes, tidak ditanam di komponen.

Keterbatasan yang disengaja: teks tindakan tetap verbatim sehingga masih memuat “USULAN:” dan
ID (E06, I0335); beberapa unknowns API memakai nama field (candidate_decisions) dan tidak
ditulis ulang. Label titik peta bisa terpotong “…” (nama penuh di tooltip, aria-label dan
panel). Pratinjau di Semua bukti dipotong dua baris; teks penuh di panel. Daftar prioritas
bergulir sendiri bila tinggi layar kecil; pada 1280×720 item #5 baru terlihat sebagian. Total
pipeline dan pencarian deal dihapus dari tampilan utama. Mobile hanya dukungan dasar.
Prioritas heuristik belum tervalidasi terhadap closing historis; approval, identitas dan izin
tetap memerlukan konfirmasi manusia.

## Blocker
Tidak ada blocker implementasi. Menunggu review Main; tidak merge sendiri.

## Tugas berikutnya
Untuk Codex (lanjutan langsung dari branch ini):

1. **Sedang dikerjakan saat diserahkan:** penyederhanaan desktop “dumb-user friendly” sesuai
   instruksi terakhir pengguna (bersih, profesional, minim info tidak penting). Sudah: daftar
   tanpa label jenis berulang dan tanpa total pipeline, baris asal saran satu baris, approval
   kosong satu baris, rasional skor terlipat, detail sumber/JSON terlipat, catatan dugaan hanya
   bila relevan. Kandidat lanjutan: sembunyikan chip locator panjang (mis. `K116|Saiyo Group|…`)
   di daftar bukti lapisan 2; pertimbangkan header deal lebih ringkas; cek ulang semua tab
   P01–P05 di 1440×900 dan 1280×720 setelah tiap perubahan.
2. **Belum dikerjakan:** uji kegunaan dengan 1–2 rekan tim (target 10 detik prioritas, 30 detik
   tindakan, ≤2 interaksi ke bukti) — catat hasil nyata, jangan diklaim bila tidak dilakukan.
3. **Belum dijalankan:** `frontend/tests/browser.mjs` (butuh Playwright); Jev live.
4. **Di luar fokus (instruksi pengguna):** mobile. Dukungan dasar ada (list → detail, sheet
   modal) tapi tidak diverifikasi ulang setelah penyederhanaan terakhir; screenshot mobile
   dihapus dari `frontend/tests/screenshots/`.
5. Setelah selesai: jalankan 70 tes + build (`frontend/TESTING.md`), `python scripts/check_handoff.py
   --all` (Windows: `PYTHONUTF8=1`), perbarui bagian ini dan Update WIB, ubah status ke
   READY_FOR_REVIEW. Jangan merge sendiri.

Catatan teknis untuk pelanjut: fokus dipindah via `pendingFocus` + `useEffect` (bukan
requestAnimationFrame) karena tab otomasi browser bisa berstatus hidden; jangan kembalikan ke
rAF. POST analisis hanya dari `analyze()` di `DealWorkspace.tsx` (dijaga tes STATIC di
`redesign.test.cjs`). Teks API selalu verbatim; jangan regex/potong/ringkas teks bisnis.

## Update WIB
2026-10-09 22:55 WIB — redesign UI/UX IN_PROGRESS, diserahkan ke Codex (pelaksana Ical atas
penugasan pengguna/Main). BOY-04 tetap MERGED #22/VERIFIED milik Boy.
