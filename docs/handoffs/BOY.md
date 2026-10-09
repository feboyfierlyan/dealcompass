# Handoff BOY

## Task dan status
BOY-02: READY_FOR_REVIEW. Revisi PR #5 yang sama untuk temuan R4.
Frontend graph menggunakan backend Bima dari main; status ini bukan VERIFIED/MERGED.

- [x] Checkout Boy diperiksa bersih sebelum sinkronisasi, sehingga tidak ada pekerjaan
  lokal yang perlu disimpan ulang. git fetch origin dan git merge origin/main selesai
  tanpa konflik, dengan merge commit 10385b0 (base main ddf7a2a).
- [x] Baca R4 dalam docs/reviews/2026-10-09-pr5-7.md dan klarifikasi API v1.
- [x] Fokus awal terbatas; pencarian seluruh graph, filter, jalur, expand dan count.
- [x] P02, I0296, I0348, D-2025-02, D-2025-06 dan hubungan/buktinya terjangkau.
- [x] Klik node/kurva relasi membuka sumber asli, tanggal dan direct/inferred.
- [x] Uji payload nyata P01–P05, desktop/mobile, 20 tes frontend dan production build.
- [ ] Analisis/ranking/Jev nyata P01–P05: menunggu revisi Ical; bukan cakupan selesai.

## Branch dan commit
Branch: boy/frontend; PR https://github.com/feboyfierlyan/dealcompass/pull/5.
Checkout terpisah: /Users/feboyfierlyan/.codex/worktrees/dealcompass-boy-ui/HACKATHON PENS 2026.
Merge main: 10385b0. Commit BOY-02 adalah commit revisi frontend yang memuat handoff ini;
SHA final tercatat pada head PR agar tidak menciptakan referensi SHA diri sendiri.

## File dan fungsi
- frontend/src/lib/graphView.ts: indexGraph membangun adjacency sekali; scopeNodes
  memilih deal/akun/percakapan sumber atau kandidat preseden; pathToDeal menelusuri
  hubungan yang tersedia; searchNodes mencari seluruh payload; expandNodes menambah
  tetangga; visibleGraph menjaga edge ID/provenance; layoutGraph mempertahankan pixel.
  evidenceExcerpt membaca isi percakapan JSON, bukan menganggap seluruh record sebagai ucapan.
- frontend/src/components/ContextGraph.tsx: batas awal 12 node, perluasan 6 per klik,
  batas tampilan 24; actual P02 awal 7 node/9 relasi. Scope preseden, pencarian ID/nama,
  filter jenis node/direct/inferred, pagination hasil/relasi, zoom/scroll, node/edge
  selection keyboard dan klik. Kurva paralel tetap terpisah sesuai ID bukti.
- frontend/src/components/EvidenceBrowser.tsx: pencarian seluruh bukti; 12 record
  per halaman, jumlah cocok/total, pilihan record asli.
- frontend/src/components/EvidencePanel.tsx: bukti terhubung dari seluruh payload,
  6 per halaman dan pencarian; tanggal, ID/file sumber, excerpt isi dan raw JSON.
  Relasi inferred dapat bertumpu pada record direct; kedua status tetap dibedakan.
- frontend/src/components/DealWorkspace.tsx: menggunakan EvidenceBrowser.
- frontend/src/style.css: kanvas scroll intrinsik, kartu node/label terbaca,
  kontrol responsif dan batas tinggi panel bukti desktop.
- frontend/src/dev/fixture.ts: proyeksi kecil graph backend memakai ID/relation/excerpt
  producer sebenarnya; rekomendasi replay tetap contoh manual dengan banner fixture.
- frontend/tests/graph.test.mjs: 8 tes integrasi GET payload backend nyata.
- frontend/tests/contracts.test.mjs: ID bukti fixture disesuaikan producer.
- frontend/tests/browser.mjs: skenario browser opsional diperbarui ke backend detail 200;
  belum dieksekusi (berbeda dari pemeriksaan browser aktual di bawah).
- frontend/TESTING.md: perintah reproduksi dan alur demo/pengujian.

## Kontrak dan dependency
Tetap API v1, tanpa perubahan dependency/package.json/lockfile, backend, CI,
dataset asli atau docs/coordination. Tidak menanam ranking/rekomendasi bisnis.
Urutan percakapan mengikuti tanggal sumber untuk tampilan, bukan prioritas sales.
Kandidat preseden dari backend tidak diklaim sebagai rekomendasi. Rank null tetap
belum tersedia; analisis 501 tetap eksplisit. Snapshot 2026-10-01.

## Cara menjalankan
Dari root repo, gunakan Python environment yang memenuhi requirements backend:
`python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`.
`npm --prefix frontend run dev -- --port 5173 --strictPort`.
Buka http://127.0.0.1:5173. Default API nyata. Saat verifikasi memakai environment
backend yang sudah tersedia di /tmp/dealcompass-review-venv; tidak mengubah dependency.

Alur demo: P02 → Peta relasi → klik I0348/I0296 → Kandidat preseden atau cari
D-2025-02/D-2025-06 → klik hasil/relasi → buka sumber. Perluas/Fokuskan node untuk
menelusuri graph; tab Bukti menelusuri semua 1.361 record secara mandiri.

## Pengujian aktual
- `npm --prefix frontend run build`: lulus TypeScript dan Vite production build.
- `node --test frontend/tests/contracts.test.mjs frontend/tests/graph.test.mjs`:
  13/13 lulus (5 kontrak + 8 graph). Graph test melakukan GET API nyata, tanpa fixture.
  Cakupan: semua node dapat dicari, jalur valid, evidence_ids resolvable, target demo,
  cap 24, filter, ukuran layout dan endpoint yang hilang. Test awal salah menganggap
  edge deal_for memakai source_id P02; diperbaiki agar memeriksa record DL-002 asli.
- `frontend/node_modules/.bin/tsc frontend/src/lib/api.ts --target ES2022 --module commonjs --outDir /tmp/dealcompass-boy-api-tests --skipLibCheck --strict`
  lalu `API_TEST_BUILD=/tmp/dealcompass-boy-api-tests node --test frontend/tests/api.test.cjs`:
  7/7 lulus. Total frontend 20/20.
- Browser aktual Codex In-app Browser: semua P01–P05 pada 1440x1000 dan 390x844;
  lebar dokumen sama dengan viewport, label graph 13 px pada 100%. Initial counts:

| Deal | Node terlihat / total | Relasi terlihat / total | Total bukti |
| --- | --- | --- | --- |
| P01 | 7 / 749 | 9 / 1647 | 763 |
| P02 | 7 / 1305 | 9 / 2895 | 1361 |
| P03 | 4 / 443 | 5 / 941 | 476 |
| P04 | 6 / 147 | 8 / 297 | 147 |
| P05 | 3 / 3 | 3 / 3 | 3 |

- Browser P02: klik I0296/I0348 cocok source_id dan isi; klik langsung kurva
  interaction_for I0348 → P02 cocok tanggal 28 Sep 2026. Preset preseden memuat
  D-2025-02/06; pencarian D-2025-06 menampilkan jalur 2 node/3 relasi. Klik kurva
  candidate_precedent_shared_industry membuka C23/P02/D-2025-06 dengan status inferensi
  dan tanggal 12 Agu 2025. Kurva dipilih pada garis aktual, bukan pusat bounding box SVG.
- Filter direct pada jalur preseden menghasilkan 0/2895 relasi; reset semua memulihkan
  3 relasi. Expand D-2025-06 menghasilkan 6 node/13 relasi. Zoom menjadi 115%.
- Mobile: pencarian I0348 → jalur DL-002/P02/I0348 → klik bukti berhasil. Filter
  decision menghasilkan 13 hasil; pagination bergerak 1–6 ke 7–12.
- Tab Bukti: pencarian I0296 menghasilkan 1/1361; klik sumber benar; halaman berikut
  menampilkan record 13–24. Analisis nyata P02 menampilkan Analisis belum tersedia (501).
- Screenshot aktual lokal: /tmp/dealcompass-boy02-desktop.png dan
  /tmp/dealcompass-boy02-mobile.png. Override viewport telah dikembalikan.
- `node --check frontend/tests/browser.mjs`: syntax lulus. Script browser opsional
  TIDAK dijalankan; pemeriksaan UI aktual di atas melalui In-app Browser.
- `git diff --check`: lulus. Pemeriksaan ownership hanya frontend dan handoff Boy.

## Fixture dan keterbatasan
Dataset/API lengkap tetap dimuat di memori. Graph memvisualisasikan subset eksplisit,
bukan membuang payload: seluruh node dicari lewat search, evidence lewat tab Bukti,
dan hubungan diperluas dari node terkait. Maksimal 24 node per tampilan; gunakan fokus
atau pencarian untuk berpindah. Jalur lebih dari 24 node dipotong dengan pemberitahuan;
node tanpa jalur tidak diberi hubungan rekaan. Jenis relasi dapat difilter tanpa
mengubah sumber. Label panjang dipotong visual; judul node/inspector dan search tetap
menyimpan nama lengkap. Graph berupa tata letak kartu, bukan simulasi fisika.

Fixture tidak dipakai untuk klaim skala/integrasi BOY-02. Graph fixture sekarang
proyeksi backend; rekomendasi replay masih manual, hanya development. Produksi
meniadakan import dan tombol fixture. Owner tetap ID dan hambatan memakai unknowns
sesuai v1. Analisis/Jev/ranking nyata belum selesai.

## Blocker
Tidak ada blocker frontend graph BOY-02. POST analyze pada base main masih 501;
integrasi analisis nyata menunggu Ical. Keputusan penutupan R4 dan merge ada pada Main.

## Tugas berikutnya
Main review revisi PR #5 terhadap R4 menggunakan backend nyata, cek target demo dan
provenance lalu tetapkan VERIFIED/MERGED bila memenuhi. Setelah revisi Ical masuk,
Boy menguji panel analisis, perbandingan preseden dan ranking seluruh P01–P05.
Jangan mengubah kontrak/dependency tanpa koordinasi Main.

## Update WIB
2026-10-09 17:38 WIB.
