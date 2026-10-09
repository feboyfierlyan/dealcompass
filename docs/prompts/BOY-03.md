# Prompt AI Boy — BOY-03: analisis nyata siap demo

Kamu AI pendamping Boy, pemilik frontend DealCompass untuk Hackathon PENS 2026.
Kerjakan implementasi dan pengujian sampai READY_FOR_REVIEW, bukan hanya rencana.

## Kondisi terbaru yang wajib dipahami

- PR Boy #5, Ical #7, dan Bima #10 sudah MERGED. Sinkronkan origin/main terbaru.
- Main memverifikasi gabungan: 99 tes backend/handoff lulus; evaluasi Ical 34/35,
  inti 34/34. E15 masih keterbatasan parafrase rules. Jev live belum diuji.
- POST /api/deals/{deal_id}/analyze sekarang menghasilkan Recommendation v1 nyata.
  Main menjalankan P01-P05 lewat HTTP dan browser dalam mode rules, semuanya berhasil.
- BIMA-02 menyediakan fungsi internal analisis awal; belum ada endpoint diagnostic.
  Jangan memanggil endpoint /initial-analysis yang belum ada atau menyalin laporan
  Bima/dataset sebagai konten statis UI. Itu dependency berikutnya, bukan alasan
  menunda tugas di bawah yang sudah bisa dikerjakan.
- Ranking belum tersedia. rank=null tetap tampil belum tersedia. analysis_status
  daftar masih not_analyzed; jangan menganggap respons 200 berarti cukup bukti.
- Snapshot bisnis 2026-10-01. P02 hanya contoh demo; scope tetap P01-P05.

## Mulai bekerja

Baca AGENTS.md, docs/coordination/MAIN.md, docs/coordination/API_CONTRACT.md,
docs/handoffs/{BOY,BIMA,ICAL}.md dan docs/reviews/2026-10-09-pr7-pr10-final.md.
Periksa git status. Pertahankan pekerjaan lokal; jangan reset paksa. Gunakan checkout
Boy sendiri, fetch origin, lalu buat branch baru boy/analysis-demo dari origin/main.
PR #5 sudah selesai; pekerjaan ini memakai PR baru. Area perubahan hanya frontend/
dan docs/handoffs/BOY.md. Kontrak, backend, dataset, manifest/lock dan CI milik Main/anggota lain.

## Tugas prioritas

1. Rapikan penyajian Recommendation nyata agar mudah dijelaskan ke mentor.
   Tampilkan berurutan: tindakan usulan, penanggung jawab, milestone, persetujuan
   yang masih diperlukan, penjelasan/preseden, informasi yang belum diketahui, sumber.
   Gunakan label Indonesia yang jelas dan detail yang dapat dibuka untuk teks panjang.
   Teks sumber/API tetap utuh dan dapat diakses; jangan meringkas dengan klaim baru,
   mengubah inferensi menjadi fakta, atau menyembunyikan approval/unknowns penting.
   Prefix eksplisit FAKTA/INTERPRETASI/SKENARIO dalam respons boleh diberi gaya visual;
   string tanpa prefix tetap ditampilkan sebagai penjelasan, bukan ditebak jenisnya.
   Badge engine_mode harus sesuai API: rules/jev/replay. Owner ID boleh tetap ID jika
   nama bersumber belum tersedia; jangan membuat peta nama manual.

2. Selesaikan alur tindakan -> bukti -> graph.
   Tombol evidence_ids rekomendasi membuka record yang tepat, tanggal, file/source_id,
   kutipan dan JSON asli. Sediakan perpindahan ke graph yang fokus pada sumber/node
   melalui ID serta relasi yang benar-benar ada. Untuk evidence non-interaksi yang
   tidak punya node unik, tampilkan record dan pilihan relasi terkait atau jelaskan
   tidak ada pemetaan; jangan membuat hubungan rekaan. Pertahankan batas graph 24 node,
   search seluruh payload, direct/inferred, sumber lengkap dan akses keyboard/mobile.

3. Hilangkan ambiguitas status sesi tanpa mengubah kontrak.
   Tampilkan jelas belum dijalankan / sedang berjalan / respons diterima / gagal.
   Status ini hanya status request sesi, terpisah dari analysis_status bisnis API.
   Jangan memberi label ready atau bukti cukup dari HTTP 200; P05 tetap memuat unknowns
   dan discovery. Pastikan retry, ganti deal cepat, refresh dan hasil terlambat tidak
   menampilkan rekomendasi deal lain. Jangan mengklaim status tersimpan di backend.

4. Uji data nyata kelima deal dan catat hasil aktual.
   P01: Rina sebagai identitas inferensi yang perlu konfirmasi.
   P02: I0348 adalah request 20%, bukan approval; VP Sales tetap diperlukan.
   P03/P04: kandidat referensi memerlukan verifikasi dan izin; overlap bukan saling kenal.
   P05: data kurang -> discovery, bukan low risk, loss atau pasti closing.
   Ini ekspektasi pengujian dari snapshot, bukan konten yang ditanam ke komponen.
   Uji desktop 1440x1000 dan mobile 390x844, termasuk panel analisis panjang dan bukti.
   Mode rules harus tetap memberi hasil ketika tidak ada key Jev. Jangan memakai API
   key nyata untuk tes ini atau mengklaim mode rules/replay sebagai Jev live.
   Uji 404/501/503, network/timeout/cancellation melalui transport test atau mock berlabel,
   dan bedakan dengan smoke browser backend nyata. Pertahankan semua tes/build yang ada.
   Tambah regresi yang bermakna untuk perubahan perilaku, bukan tes yang menyalin implementasi.

5. Perbarui frontend/TESTING.md: langkah menjalankan, acceptance P01-P05, dan naskah
   demo 3-5 menit. Demo menelusuri request P02 -> bukti -> preseden -> usulan/approval,
   kemudian menunjukkan kebutuhan berbeda P01/P03/P04/P05. Nyatakan ranking dan
   diagnostic Bima belum tampil jika memang belum terintegrasi. Jangan mengarang
   peningkatan closing, penghematan waktu, persentase akurasi atau status live Jev.

## Catatan .md WAJIB dan penyerahan

Update docs/handoffs/BOY.md dengan SEMUA heading template: Task dan status; Branch
dan commit; File dan fungsi; Kontrak dan dependency; Cara menjalankan; Pengujian
aktual; Fixture dan keterbatasan; Blocker; Tugas berikutnya; Update WIB.
Catat fungsi yang selesai, file, hasil tes aktual, coverage kelima deal, sumber
pengujian nyata vs mock, keterbatasan dan dependency API Bima/ranking. Status maksimal
READY_FOR_REVIEW. Main yang menetapkan VERIFIED/MERGED.

Push branch dan buka PR baru ke main; lampirkan handoff, SHA, perintah/hasil uji dan
langkah demo. Jangan merge sendiri. Jika API baru diperlukan, tulis usulan field
beserta manfaat dan tetap selesaikan pekerjaan yang memakai kontrak v1 saat ini.
