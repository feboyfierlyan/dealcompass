# Prompt AI Bima — BIMA-01

Kamu membantu Bima mengerjakan data, graph dan API. Baca AGENTS.md, README dataset,
MAIN.md, API_CONTRACT.md. Branch bima/data-graph. Area backend/ingestion/,
backend/graph/, backend/api/, backend/main.py, tests/bima/, docs/handoffs/BIMA.md.
Scope final P01-P05; loader seluruh sumber, bukan hanya record P02.

## Kerjakan sekarang
1. Perluas list_deals menjadi ingest seluruh CSV/JSONL. Jaga data asli.
2. Normalisasi ID, nilai kosong, angka dan tanggal. Snapshot 2026-10-01.
3. Ingest decision_log.csv saja; XLSX adalah salinan, bukan keputusan tambahan.
4. Bangun NetworkX MultiDiGraph dengan provenance dan masa berlaku relasi.
5. Implementasikan build_deal_context(deal_id, snapshot_date) -> DealContext.
6. Kaitkan bukti dan keputusan lintas akun. Implementasikan lookup bukti/subgraph
   sebagai fungsi internal; usulkan endpoint baru bila dibutuhkan.
7. Simpan usage lengkap untuk query; agregat harus dapat ditelusuri ke sumber.
8. Hubungkan endpoint detail dan analyze ke konteks dan fungsi milik Ical.

Kasus integrasi awal: P02/DL-002, I0296, I0348, C23, DL-006/007,
D-2025-02/06. Baca record nyata, jangan hardcode jawaban P02 sebagai mesin.
Kemudian jalankan konteks P01, P03, P04, P05 dan tandai informasi yang kurang.

Simpan relasi temporal dan bedakan inferred/direct. Email lama perlu resolusi
identitas dengan bukti. Keputusan tanpa bukti_interaction_id tidak diberi email
rekaan. Overlap kerja tidak membuktikan saling kenal. Gejala bukan sebab pasti.

## Acceptance
Seluruh sumber termuat dan volume dilaporkan; semua deal dapat ditanyakan;
P02 memiliki dua preseden bersumber; graph edge/evidence tidak menggantung;
ID tak dikenal 404; hitungan tepat; schema v1 valid; tes di tests/bima/.

## Catatan WAJIB
Perbarui docs/handoffs/BIMA.md pada milestone dan setiap PR. Catat semua heading
template, fungsi/input-output, file termuat dan volumenya, node/relasi, isu data,
perintah/hasil uji aktual, dependency, blocker, langkah integrasi dan waktu WIB.
Jangan edit kontrak bersama, decision engine, frontend atau handoff orang lain.

## Penyerahan
PR ke main; status READY_FOR_REVIEW. Jika ChatGPT tidak bisa mengedit repo,
berikan isi file/diff dan catatan untuk Bima simpan, jalankan, commit dan push.
Jangan mengklaim pengujian dijalankan jika hanya menyarankan perintah.

