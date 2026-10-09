# BOY-04 — tampilkan ranking dan diagnostic asli

Kamu AI Boy untuk DealCompass. BOY-03/R9 dan PR #14 sudah merged. Backend fase3
sudah VERIFIED/MERGED melalui PR #16 (revisi Ical R8), main minimal 8581de8.
Baca AGENTS.md, docs/coordination/MAIN.md, API_CONTRACT.md, PHASE3_CONTRACT.md,
docs/reviews/2026-10-09-ical-r8.md dan handoff Boy.

## Branch dan scope

Gunakan checkout sendiri, sync origin/main lalu buat branch baru
`boy/priorities-diagnostics` dan PR baru ke main. Jangan membuka ulang PR #14.
Scope frontend/ dan docs/handoffs/BOY.md; dependency/CI/backend/kontrak bersama
milik Main. Pertahankan desain dan fungsi BOY-03, tanpa rewrite menyeluruh.

## Hasil yang harus terlihat

1. Dashboard menampilkan prioritas kelima deal dari GET /api/pipeline/priorities.
   Gabungkan dengan GET /api/deals berdasarkan deal_id dan snapshot, bukan posisi
   array. Urutkan sesuai rank API; jangan hardcode urutan atau menghitung skor baru.
   Semua P01-P05 tetap dapat dipilih. Label jenis acceleration/discovery dan
   analysis_status dari priorities jelas; ready bukan approval atau janji closing.
2. Pada deal terpilih, tampilkan alasan prioritas, faktor/value/effect, tindakan,
   owner, milestone, approval tertunda, unknowns, keterbatasan dan metode ranking.
   Gunakan recommendation dari item priorities sebagai rekomendasi ranking rules,
   dengan label sumber yang jelas. POST analyze lama tetap boleh dijalankan user;
   hasil/status request-nya terpisah dan tidak mengganti rank atau menyamarkan
   versi rekomendasi yang sedang ditampilkan. Jangan otomatis POST lima analisis.
3. Tampilkan diagnostic memakai GET /api/pipeline/initial-analysis atau GET
   /api/deals/{deal_id}/initial-analysis. Hindari request duplikat yang tidak perlu.
   Tampilkan metrics, findings dan reference_candidates; bedakan fact dari
   interpretation, missing_information dan follow_up_implication. Pertahankan
   seluruh rincian/provenance pada detail yang dapat dibuka, tanpa menimpa
   Recommendation Ical dengan implikasi diagnostic.
4. Beri penjelasan singkat anomali bisnis vs outlier statistik. statistical_assessment
   berstatus not_assessed; tampilkan reason dari API. Null/missing bukan nol,
   nihil risiko, tidak ada outlier, atau SLA terlanggar. Interaksi eksternal terakhir
   bukan otomatis balasan terakhir pelanggan. Kandidat referensi belum berizin.
5. Semua evidence IDs dari ranking dan diagnostic membuka record sumber yang tepat.
   Registry dapat memuat bukti tambahan di luar context.evidence: gabungkan berdasarkan
   ID, tolak konflik isi, jangan diam-diam menimpa. Detail sumber tetap bisa dibaca
   walaupun tidak memiliki node/edge. Gunakan graph konteks asli untuk fokus path;
   tampilkan path API dan arah panah asli setiap edge. Traversal terbalik tidak
   membalik arti relasi. Pertahankan label direct/inferred, jumlah/batas graph24,
   akses ke seluruh sumber, pencarian, keyboard dan mobile.

## Keandalan dan kontrak

- Tambahkan tipe/validasi respons frontend untuk fase3 tanpa mengubah backend.
  Periksa v1/snapshot, deal/account matching, tepat lima ID/rank unik, enum,
  nilai finite/null, struktur wajib dan resolusi bukti. Payload tidak lengkap,
  duplikat atau mismatch jangan ditampilkan sebagai ranking valid sebagian.
- Loading/error/retry untuk priorities dan diagnostic harus eksplisit. Jika ranking
  gagal 501/503/network/timeout, daftar sumber tetap dapat dipakai tanpa rank palsu.
  Jangan mempertahankan ranking lama seolah refresh baru berhasil. Kegagalan
  diagnostic tidak boleh menghapus analisis yang masih valid dari endpoint lain.
- Abort dan generation guard untuk switch/refresh cepat. Reset/pisahkan data sesuai
  deal_id/snapshot agar respons lama tidak tampil pada deal baru.
- Jev live belum diuji. Jangan klaim confidence, persen closing, akurasi atau
  peningkatan penjualan. Ranking heuristik deterministik, bukan model terlatih.

## Acceptance data asli dan pengujian

- Snapshot saat ini: ranking P04/P01/P02/P03/P05, hanya sebagai ekspektasi tes,
  bukan konstanta UI. Tampilkan metode dan keterbatasan dari respons.
- P02: permintaan20% I0348 tetap pending VP Sales; preseden bukan approval sekarang.
  Bukti ke graph harus dapat membuka DL-002 → P02 ← I0348.
- P03/P04: pengalaman terbaru/kesediaan/izin sebelum perkenalan; overlap P04 bukan
  kenalan terkonfirmasi. Jangan menghilangkan catatan kandidat bermasalah.
- P05: discovery, insufficient_evidence, skor null, unknowns terlihat.
- 34 tes lama/build harus tetap lulus. Tambahkan tes bermakna untuk validasi/join
  fase3, payload invalid, stale response, sumber tambahan/konflik, path asli,
  error/retry. Pisahkan mock dari HTTP nyata.
- Jalankan integrasi ketiga endpoint fase3 yang dipakai, graph dan analisis lama
  terhadap backend main rules tanpa key Jev. Smoke browser desktop/mobile kelima
  deal, ranking→alasan→sumber→graph, diagnostic serta ketidakpastian. Catat yang
  benar-benar diuji; jangan menyebut API-only test sebagai pengujian browser.

## Penyerahan WAJIB .md

Update docs/handoffs/BOY.md dengan semua heading: branch/commit, fungsi/file,
kontrak, cara menjalankan, perintah/hasil tes aktual, real vs mock, keterbatasan,
blocker dan waktu WIB. Update frontend/TESTING.md serta naskah demo 3–5 menit:
prioritas pipeline → alasan P04/P01 → gate P02 → diagnostic/anomali → bukti graph
→ discovery P05. Status maksimal READY_FOR_REVIEW. Kirim PR baru dan SHA ke Main;
Main memutuskan VERIFIED/MERGED. Jangan deploy atau merge sendiri.
