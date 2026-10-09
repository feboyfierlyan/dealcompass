# Handoff BOY

## Task dan status
BOY-01: READY_FOR_REVIEW untuk implementasi frontend. Integrasi graph/analisis
backend nyata belum selesai; bukan klaim aplikasi lengkap.
- [x] P01-P05 dibaca dari GET /api/deals; pencarian dan pemilihan deal berfungsi.
- [x] Panel tindakan, owner, milestone, approvals, unknowns dan preseden mengikuti v1.
- [x] Graph SVG interaktif, klik node/edge, tanggal, direct/inferred dan sumber bukti.
- [x] Rank null tetap belum tersedia; label engine mengikuti respons, tanpa ranking buatan.
- [x] Loading, 404, 501, gangguan jaringan, timeout, JSON/schema invalid dan retry.
- [x] Build, 12 tes frontend, 10 tes repo dan pemeriksaan UI nyata/fixture.
- [ ] Analisis P02 end-to-end dengan backend Bima/Ical.
- [ ] Analisis nyata seluruh P01-P05 dan ranking lintas deal.

## Branch dan commit
Branch: boy/frontend. Base: a914cad. Implementasi pada checkout terpisah
`/Users/feboyfierlyan/.codex/worktrees/dealcompass-boy-ui/HACKATHON PENS 2026`.
Commit penyerahan tersedia pada PR branch ini; Main memverifikasi sebelum merge.

## File dan fungsi
- frontend/src/main.tsx: Dashboard menerima DealApi, memuat daftar nyata, memilih
  deal, mencari kartu, menampilkan nilai/rank/status, dan memisahkan fixture.
- frontend/src/components/DealWorkspace.tsx: konteks -> panel ringkasan, unknowns,
  rekomendasi, persetujuan, preseden; memanggil POST analyze ketika diminta.
- frontend/src/components/ContextGraph.tsx: nodes/edges -> SVG, node/edge selection,
  zoom/reset/drag, keyboard dan daftar relasi; relasi tanpa node ditandai.
- frontend/src/components/EvidencePanel.tsx: selection + context -> bukti, source
  file/record, tanggal dan direct/inferred; referensi hilang ditampilkan.
- frontend/src/lib/api.ts: liveApi, timeout 20 detik, AbortController, error HTTP,
  validasi payload dan kecocokan deal_id untuk mencegah hasil silang deal.
- frontend/src/lib/contracts.ts: tipe mirror v1, guards payload dan resolveEvidence.
- frontend/src/lib/format.ts, components/Icon.tsx, style.css: format IDR/tanggal,
  ikon SVG dan layout responsif; tidak memuat font/asset eksternal.
- frontend/src/dev/fixture.ts: fixture P02 eksplisit untuk menguji panel siap-data.
- frontend/tests/: 5 tes kontrak, 7 tes adapter, skenario browser opsional.
- frontend/TESTING.md: prosedur verifikasi, fixture dan batas integrasi.

## Kontrak dan dependency
Tetap API v1 dan backend/contracts.py. Tidak mengubah package.json, lockfile,
backend, dataset, CI atau dokumen koordinasi. Graph menggunakan SVG/React tanpa
library tambahan. GET context mendahului POST analyze. Data graph/keputusan
diharapkan dari Bima/Ical. Tidak membuat aturan bisnis di adapter live/UI.

## Cara menjalankan
Ikuti README untuk backend port 8000. Frontend: `npm --prefix frontend ci`,
`npm --prefix frontend run dev -- --port 5173 --strictPort`.
Buka http://127.0.0.1:5173. Panduan tes lengkap: frontend/TESTING.md.
Fixture: tombol Pratinjau fixture pengembangan -> P02 -> Analisis langkah berikutnya.

## Pengujian aktual
- `npm --prefix frontend run build`: lulus; import/data fixture tidak masuk build produksi.
- `node --test frontend/tests/contracts.test.mjs`: 5/5 lulus.
- Kompilasi adapter API ke /tmp lalu `node --test frontend/tests/api.test.cjs`
  dengan API_TEST_BUILD: 7/7 lulus. Termasuk 404/501/503, timeout, cancel, invalid JSON,
  schema dan respons deal yang salah. Perintah lengkap ada di frontend/TESTING.md.
- `python3 -m unittest discover -s tests -v`: 10/10 lulus pada checkout Boy.
- Browser nyata (Codex In-app Browser): semua 5 kartu/detail 501; analisis disabled;
  pencarian kosong/reset; fixture berlabel; rekomendasi/preseden; node/edge evidence;
  keyboard tab/Enter; zoom/reset; kembali ke API nyata. Lebar 390 px: content width
  390 px, graph dan panel bukti bisa digunakan. Viewport sudah dikembalikan.
- Script Playwright opsional belum dieksekusi tuntas: browser runtime belum tersedia.
  Jangan menganggap skenario mock/race browser dalam script tersebut sudah lulus.
- `git diff --check`: lulus. Handoff/ownership diperiksa sebelum push.

## Fixture dan keterbatasan
Default selalu API nyata. Backend saat pemeriksaan menyediakan daftar; detail dan
analyze masih 501. Belum ada Jev live, ranking atau hasil rekomendasi nyata.
Fixture memuat salinan bukti I0296/I0348 dan D-2025-02/06. Graph fixture disusun
manual; pendekatan pilot adalah skenario UI berlabel, bukan keputusan pelanggan.
Banner melekat ketika scroll; mode fixture tidak bisa aktif pada build produksi.
Owner tetap ID; v1 belum memberi nama. Panel hambatan memakai unknowns karena
kontrak belum memiliki blockers terpisah. Daftar kartu mengikuti urutan sumber.

## Blocker
Verifikasi integrasi nyata menunggu GET detail dari Bima dan POST analyze dari Ical.
Tidak ada blocker build frontend. UI dengan payload valid siap untuk integrasi.

## Tugas berikutnya
Main review PR Boy dan hasil uji; jangan menandai cakupan analisis semua deal selesai.
Bima/Ical menyelesaikan konteks/analisis. Setelah merge modul tersedia, Boy menguji
alur nyata P02 lalu P01/P03/P04/P05, membandingkan evidence_ids/precedent_ids dengan
dataset dan memperbaiki mismatch melalui kontrak bersama. Usulan untuk Main:
field blockers terstruktur serta label owner bila diperlukan produk.

## Update WIB
2026-10-09 16:48 WIB.
