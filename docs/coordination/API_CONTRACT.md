# API contract v1

Pemilik: Main. Sumber tipe Python: `backend/contracts.py`.
Snapshot bisnis tetap `2026-10-01`; nominal IDR berupa integer.
`deal_id` adalah DL-001 s.d. DL-005, sedangkan `account_id` adalah P01-P05.
Jangan menukar keduanya pada path endpoint.

## Endpoint

- `GET /health`: `{status: "ok", schema_version: "v1", snapshot_date: "2026-10-01"}`.
- `GET /api/deals`: `{schema_version, snapshot_date, items: DealSummary[]}`.
- `GET /api/deals/{deal_id}`: `DealContext`.
- `POST /api/deals/{deal_id}/analyze`: tanpa body, respons `Recommendation`.
- `POST /api/ask`: fase berikutnya; belum menjadi endpoint v1 dan belum diimplementasikan.

Setelah PR #7 dan #10 merged, health, daftar deal, detail graph dan POST analyze
tersedia di main. Main memverifikasi analyze 200 untuk P01-P05 dalam mode rules.
ID tidak dikenal memberi 404; analyzer yang tidak tersedia tetap dapat memberi 501.
Diagnostic BIMA-02 tersedia melalui endpoint initial-analysis setelah #16 merged.
analysis_status daftar belum dipetakan ke hasil analisis dan rank masih null.
Error berbentuk `{detail: {code, message}}`. Jangan mengembalikan 200 berisi
analisis palsu ketika mesin belum tersedia. Gangguan layanan berikutnya harus
memakai error yang jelas atau mode fallback yang eksplisit.

## DealSummary

`deal_id`, `account_id`, `account_name`, `stage`, `stage_age_days: int`,
`annual_value: int`, `owner_id`, `rank: int|null`,
`analysis_status: not_analyzed|ready|insufficient_evidence`.

Urutan bootstrap adalah urutan sumber, bukan prioritas. `rank=null` sampai ada
perbandingan kelima deal. Rank bukan probabilitas closing.

## DealContext

`schema_version: "v1"`, `snapshot_date`, `deal: DealSummary`,
`evidence: EvidenceRecord[]`, `graph: {nodes, edges}`,
`candidate_decisions: object[]`, `unknowns: string[]`.

Candidate decisions menyimpan field CSV asli (string), termasuk decision_id,
tanggal, alasan, keputusan, nilai, deal_id, fitur_dijanjikan, status_janji.
Relasi semantik dan hasil perhitungan tambahan harus memiliki provenance.

## Bukti dan graph

EvidenceRecord: `id`, `source_file` (relatif repo), `source_id` (PK atau locator
baris yang dapat dibuka), `date: string|null`, `excerpt`,
`evidence_type: direct|inferred`.

GraphNode: `id`, `label`, `type`.
GraphEdge: `id`, `source`, `target`, `relation`, `evidence_ids: string[]`,
`evidence_type: direct|inferred`, `valid_from`, `valid_to` (ISO date atau null).

Semua endpoint edge harus menunjuk node yang tersedia. Semua evidence_ids
harus dapat di-resolve. Inferensi overlap kerja tidak membuktikan saling kenal.

## Recommendation

`schema_version: "v1"`, `deal_id`, `action`, `owner_id: string|null`,
`milestone`, `evidence_ids: string[]`, `precedent_ids: string[]`,
`precedent_comparison: string[]`, `approvals_needed: string[]`,
`unknowns: string[]`, `engine_mode: jev|rules|replay`.

Precedent IDs merujuk keputusan yang benar-benar ada dalam candidate_decisions.
Tidak ada preseden relevan: array boleh kosong, tetapi jelaskan keterbatasannya
di unknowns. Bukti kurang tidak berarti tidak ada risiko.

## Antarmodul dan kepemilikan

- Bima: `backend.graph.context.build_deal_context(deal_id, snapshot_date) -> DealContext`.
- Ical: `backend.decision.analyze.analyze_deal(context: DealContext) -> Recommendation`.
- Bima menghubungkan route ke kedua fungsi; Boy memanggil endpoint HTTP.
- Ical menggunakan konteks Bima, tidak membuat ingest kedua.
- Laporan perubahan kontrak melalui handoff; Main mengubah kontrak dan tipe bersama.

## Persyaratan bisnis

Hitung rupiah dan tanggal dalam kode. Diskon >10% memerlukan approval VP Sales
dan pencatatan. I0348 adalah permintaan, bukan approval. Jika digunakan untuk
pilot, jumlah/durasi yang diusulkan harus ditandai skenario. Pisahkan fakta,
inferensi, dan rekomendasi. Seluruh produk final mencakup P01-P05.


## Klarifikasi Main setelah review PR #5-#7

Struktur v1 tetap. Produsen konteks kanonis adalah implementasi Bima di main:

- Untuk row sumber, excerpt adalah string JSON object dari field row asli. Untuk interaksi, baca field isi sebagai pesan dan account_id sebagai pemilik; subjek adalah metadata terpisah. Jangan parse row memakai split koma.
- Agregat usage memiliki evidence_type inferred dan excerpt JSON hasil agregasi; source_id berupa locator baris. Jangan menganggap setiap excerpt adalah pesan pelanggan.
- Konteks memuat prospek fokus dan akun referensi. Sinyal hambatan/request/approval prospek harus terkait context.deal.account_id/deal_id. Bukti akun lain hanya mendukung preseden atau pembandingan, kecuali hubungan lintas akun dijelaskan eksplisit sebagai inferensi.
- Relasi aktual: interaction_for (interaction -> account), employed_at (contact -> account/organization), overlapping_employment (contact -> contact), related_account_shared_industry/feature_usage/work_overlap/prior_employment/same_competitor (deal -> account), candidate_precedent_* (deal -> decision).
- related_account_* berarti kandidat pencarian bersumber, belum membuktikan kelayakan atau kesediaan menjadi referensi. Konsumen tidak boleh mengatakan kandidat tidak tersedia hanya karena mencari nama relasi fixture yang berbeda.
- Tidak ada relasi pengambil_keputusan eksplisit saat ini. Penetapan identitas membutuhkan bukti interaksi dan resolusi kontak/masa kerja; jabatan tertinggi saja tidak cukup.
- Frontend boleh membuat tampilan subgraph fokus, tetapi harus menyatakan jumlah/lingkup yang ditampilkan dan tetap menyediakan akses ke bukti lengkap.
- Fixture pengembangan harus mengikuti representasi produsen nyata. Fixture bukan kontrak semantik alternatif.

Lihat docs/reviews/2026-10-09-pr5-7.md untuk reproduksi dan acceptance perbaikan.

## Fase 3: engine dan API siap, UI belum terintegrasi

Kontrak tambahan ada di [PHASE3_CONTRACT.md](PHASE3_CONTRACT.md). Engine #15 dan
API #16 sudah merged/verified. Main membuktikan priorities, pipeline diagnostic
serta diagnostic kelima deal asli200; unknown deal404. Endpoint tambahan:

- GET /api/pipeline/priorities: ranking rules, alasan/faktor/rekomendasi/sumber/path.
- GET /api/pipeline/initial-analysis: diagnostic lima deal + statistical_assessment.
- GET /api/deals/{deal_id}/initial-analysis: diagnostic satu deal.

Endpoint lama tetap; rank/status daftar lama tidak diubah. BOY-04 menggabungkan
priorities berdasarkan deal_id/snapshot untuk UI. Rank bukan probabilitas closing;
ready bukan approval. Lihat [review final R8](../reviews/2026-10-09-ical-r8.md).
