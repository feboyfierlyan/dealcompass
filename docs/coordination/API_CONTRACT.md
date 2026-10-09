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

Bootstrap mengimplementasikan health dan daftar deal. Dua endpoint detail dan
analyze memberi 501 sampai Bima/Ical melengkapinya. ID tidak dikenal memberi 404.
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

