# BIMA-03 R8 — perbaiki integrasi ranking asli

Penugasan terbaru 9 Oktober 2026: pengguna mengalihkan pelaksanaan R8 ke AI Ical.
Gunakan [prompt takeover Ical](ICAL-R8-TAKEOVER.md). Bima tidak mengerjakan R8
bersamaan. Checklist teknis di bawah tetap berlaku; nama BIMA adalah modul/branch,
bukan klaim bahwa pelaksana revisi adalah Bima.

Kamu pelaksana revisi modul Bima untuk DealCompass. Baca AGENTS.md, docs/coordination/MAIN.md,
PHASE3_CONTRACT.md dan docs/reviews/2026-10-09-pr14-16.md.
Lanjutkan branch bima/diagnostics-api dan PR #16, jangan buat PR pengganti.
Fetch lalu merge origin/main (Ical #15 sudah merged); jangan reset pekerjaan.

## Tugas

1. Perbaiki backend/api/priorities.py: validasi setiap edge menghubungkan pasangan
   node berurutan dalam salah satu arah. Traversal boleh dua arah, tetapi edge
   source/target/relation/evidence tetap milik graph asli. Jangan menonaktifkan
   validasi, mengubah graph, mengurutkan ulang ranking, atau memotong payload.
2. Sesuaikan tes yang saat ini menolak reverse path. Tambahkan kasus positif
   traversal terbalik dengan edge asli; kasus negatif harus benar-benar tidak
   terhubung/palsu atau provenance rusak. Tes engine yang memutasi input tetap gagal.
3. Tambahkan regresi HTTP nyata tanpa mock load_rank_deals/rank_deals. Panggil
   GET /api/pipeline/priorities melalui TestClient dengan dataset asli dan engine
   Ical; harus 200, tepat P01-P05, rank 1..5, gate P02 dan discovery P05 terjaga.
   Periksa seluruh path terhadap graph dan evidence registry, bukan hanya status.
4. Jalankan semua unittest dan smoke ketiga endpoint baru, termasuk diagnostics
   kelima deal. Pertahankan tes 501 modul hilang serta 503 output cacat/provider
   dependency gagal. Jangan menulis secrets ke log.
5. WAJIB update docs/handoffs/BIMA.md: commit, fungsi berubah, perintah/hasil aktual,
   bedakan tes mock dari integrasi asli, blocker dan waktu WIB. Maksimal status
   READY_FOR_REVIEW; Main menetapkan VERIFIED/MERGED.

## Bukti yang harus dikirim

Link PR #16, commit terbaru, jumlah tes aktual, HTTP priorities asli 200, daftar
kelima deal dari respons dan status gate/unknowns. Tidak perlu implementasi ulang
ranking Ical atau UI Boy. Scope hanya backend/api, tests/bima, handoff Bima.
