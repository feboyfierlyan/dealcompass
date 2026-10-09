# Prompt AI Bima — BIMA-03

Kamu AI pendamping Bima, pemilik ingestion/graph/API DealCompass.
Kerjakan sampai READY_FOR_REVIEW, bukan hanya rencana.

## Mulai
PR #10 sudah merged dan BIMA-02 terverifikasi. Fetch origin/main terbaru, pertahankan
perubahan lokal, gunakan checkout sendiri, lalu branch baru bima/diagnostics-api.
Buka PR baru, jangan buka ulang #10. Baca AGENTS.md, MAIN.md, API_CONTRACT.md,
docs/coordination/PHASE3_CONTRACT.md dan handoff BIMA/ICAL.
Kontrak fase 3 telah ditetapkan Main, bukan lagi usulan yang harus menunggu izin.

## Prioritas 1 — bawa analisis Bima ke HTTP
Implementasikan dua GET endpoint sesuai PHASE3_CONTRACT.md:
- /api/deals/{deal_id}/initial-analysis
- /api/pipeline/initial-analysis
Gunakan analyze_deal_initial dan analyze_pipeline_initial yang sudah merged.
Pertahankan metrik, findings, kandidat, missing information, query_scope, registry
bukti dan seluruh provenance. Jangan menyalin data statis atau menjalankan Jev.
P02 external terakhir 5 September berbeda dari internal 28 September; external
mencakup outbound, bukan otomatis balasan buyer. P05 null/data gap bukan loss.
Statistical not_assessed tetap jelas; umur tertinggi tidak otomatis outlier.
Ekspektasi ini untuk tes snapshot, bukan hardcode route.

## Prioritas 2 — adapter API ranking Ical
Siapkan GET /api/pipeline/priorities. Kumpulkan konteks/diagnostic dari produsen
kanonis dan panggil backend.decision.ranking.rank_deals(contexts, diagnostics).
Seluruh signature/envelope/validasi tersedia pada kontrak fase 3.
Ranking adalah kode Ical; jangan implementasikan skor, bobot atau approval sendiri.
Saat fungsi belum tersedia, kembalikan 501 PRIORITIES_NOT_IMPLEMENTED, bukan dummy.
Saat hasil gagal/invalid/incomplete, gunakan 503 PRIORITIES_UNAVAILABLE.
Gunakan mock berlabel untuk contract test selama Ical bekerja; diagnostic tetap
bisa selesai dan PR boleh diajukan. Setelah Main merge Ical, sinkron main dan jalankan
smoke ranking nyata. Jangan mengklaim mock sebagai integrasi nyata.

## Validasi dan kompatibilitas
Model/adapter baru boleh di backend/api/phase3_models.py sesuai persetujuan Main pada
kontrak. Jangan edit backend/contracts.py atau mengubah endpoint v1 lama sepihak.
Pertahankan null, zero, field sumber dan batas unknown; pastikan serialisasi JSON strict.
Validasi lima item lengkap, unique rank, snapshot, ID sumber dan path graph. Jangan
membuang field tambahan diagnostik saat memakai response model. Tidak perlu database
atau dependency baru; GET tidak memanggil Jev atau bergantung pada riwayat klik analyze.

## Pengujian wajib
HTTP nyata diagnostic P01-P05 dan pipeline, 404 unknown ID, 501 engine belum ada,
503 ranking invalid/incomplete dan fallback error yang jujur. Cocokkan setiap excerpt
ke row sumber, serta setiap path ke graph. Uji rank/analysis_status dan registry bukti
lewat contract tests; itu validasi schema, bukan menilai logika bisnis milik Ical.
Pastikan health, daftar deal, detail dan POST analyze existing tetap lulus.
Ukur latency aktual diagnostic/priorities yang benar-benar tersedia; laporkan cold
versus warm bila diukur, tanpa menciptakan angka performa. Jangan print secrets.

## Penyerahan dan .md WAJIB
Area: backend/ingestion/, backend/graph/, backend/api/, backend/main.py, tests/bima/
dan docs/handoffs/BIMA.md. Jangan edit decision Ical, frontend, kontrak bersama,
manifest/CI atau dataset. Semua heading template handoff wajib lengkap.
Catat endpoint/fungsi selesai, bentuk respons dan ID bukti, tes/latency aktual,
mock vs nyata, dependency ranking, blocker, next task dan waktu WIB.
Sertakan contoh request dan ringkasan respons secukupnya dalam handoff, tanpa
menyalin payload besar. Push branch, buat PR baru dengan SHA dan hasil uji.
Status maksimal READY_FOR_REVIEW; Main melakukan VERIFIED/MERGED.
