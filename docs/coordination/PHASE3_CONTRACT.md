# Kontrak penugasan fase 3 — ranking dan diagnostic

Pemilik kontrak: Main. Disepakati 2026-10-09 18:11 WIB untuk ICAL-03/BIMA-03.
**Status: spesifikasi implementasi; endpoint/fungsi baru di bawah belum tersedia.**
Tidak mengubah semantik endpoint v1 yang sudah berjalan. Snapshot 2026-10-01.

## Pembagian area dan urutan integrasi

- Ical: fungsi ranking di backend/decision/ranking.py; decision/reference, evaluation,
  tests/ical dan handoff ICAL. Tidak mengubah route, kontrak bersama atau graph Bima.
- Bima: diagnostic/priorities routes di backend/api/ atau backend/main.py, adapter,
  model respons baru di backend/api/phase3_models.py, tests/bima dan handoff BIMA.
  Main mengizinkan model baru di area API sesuai wire contract dokumen ini;
  backend/contracts.py lama tidak diubah pada fase ini.
- Boy: tetap BOY-03, kemudian integrasi endpoint fase 3 setelah Main review.
- Bima dapat menyelesaikan diagnostic dan mock contract test prioritas tanpa menunggu
  ranking Ical. Ranking belum tersedia -> HTTP 501 PRIORITIES_NOT_IMPLEMENTED,
  bukan ranking dummy 200. PR boleh dikirim dengan status dependency jelas.
- Main merge Ical dan Bima setelah review; lakukan smoke integrasi nyata sebelum
  memberi tahu Boy bahwa endpoint prioritas siap. Jangan cherry-pick kerja anggota lain.

## Fungsi internal milik Ical

`backend.decision.ranking.rank_deals(contexts: list[DealContext], diagnostics: list[dict]) -> dict`

Input contexts dan diagnostics berasal dari produsen Bima, dipasangkan berdasarkan
`deal_id`, bukan urutan array. Tolak mismatch snapshot/akun, duplikasi dan set deal
berbeda dengan ValueError yang jelas. Engine tidak meng-hardcode P01-P05 atau ID
sumber sebagai aturan peringkat. Route Bima menyediakan lima prospek terbuka.
Tidak membaca dataset kedua, tidak melakukan HTTP, tidak memakai Jev untuk menghitung
peringkat. Boleh memakai analyze_deal_trace(context, mode='rules') untuk trace bisnis.
Jangan mengubah konteks/input. Ketiadaan informasi bukan nol atau bukti peluang buruk.

Output adalah dict JSON-safe dengan field berikut:

- schema_version: 'v1'; snapshot_date: '2026-10-01'; engine_mode: 'rules'.
- methodology: object berisi id (mis. 'deal-priority-heuristic-v1'), label,
  description, ordered_rules: string[], tie_breakers: string[], limitations: string[].
  Jika memakai angka bobot/score, formula dan bobot wajib tercantum dalam description
  atau field tambahan weights. Metode adalah pilihan desain, bukan model terlatih.
- items: PriorityItem[], diurutkan rank naik, satu item untuk setiap input.
- limitations: string[] berisi batas lintas pipeline, termasuk belum tervalidasi
  terhadap hasil closing historis dan bukan probabilitas closing.

PriorityItem wajib:

- deal_id, account_id, rank: integer 1..N unik dan berurutan.
- priority_kind: 'acceleration' | 'discovery'. Rank berarti urutan perhatian/tindakan
  sales pada snapshot, bukan prediksi urutan closing. Item discovery tetap masuk.
- analysis_status: 'ready' | 'insufficient_evidence', dari trace bisnis rules;
  HTTP sukses tidak menentukan kecukupan bukti.
- rationale: string[]: alasan pembandingan, bukan hanya mengulang nilai score.
- factors: array object {name: string, value: number|string|null, effect: string,
  evidence_ids: string[]}. Effect menjelaskan bagaimana faktor memengaruhi urutan;
  unknown wajib dinyatakan, angka finite, tidak ada confidence rekaan.
- recommendation: Recommendation v1 yang valid, termasuk action/owner/milestone/
  approvals_needed/unknowns/precedent_comparison dan engine_mode='rules'.
- evidence_ids: string[]; evidence: EvidenceRecord[] mencakup SEMUA ID yang dirujuk
  item, factors, recommendation dan paths. Gunakan union sumber context/diagnostic;
  ID sama dengan isi berbeda adalah kesalahan, bukan diam-diam overwrite.
- evidence_paths: array {node_ids: string[], edge_ids: string[], evidence_ids: string[]}
  dari graph konteks deal. Setiap pasangan node berurutan harus dihubungkan edge
  asli yang sesuai; arah asli edge tidak diubah. Gunakan jalur untuk alasan utama
  ranking/tindakan; jangan membuat edge baru. Bila sumber tidak punya jalur, tampilkan
  record dan keterbatasan eksplisit, bukan hubungan rekaan.
- limitations: string[] khusus deal, termasuk batas cakupan bukti dan faktor unknown.

Ical memilih metode deterministik yang sederhana dan bisa dijelaskan. Pertimbangkan
kelengkapan bukti, hambatan/kejelasan tindakan berikutnya, kebutuhan approval/izin,
kemiripan preseden, nilai deal dan umur tahap. Jangan menjadikan nominal/umur satu-
satunya dasar. Jelaskan tradeoff dan sensitivity, jangan menetapkan urutan ID yang
harus keluar terlebih dahulu. Umur tahap lintas tahap bukan bukti outlier/SLA.
Jika faktor tidak dipakai dalam ordering, nyatakan sebagai konteks, bukan mengklaim
bahwa faktor itu dihitung. Semua P01-P05 wajib dievaluasi, termasuk P05 discovery.

## HTTP milik Bima

1. `GET /api/deals/{deal_id}/initial-analysis`
   Respons 200: `{schema_version: 'v1', ...analyze_deal_initial(context)}`.
   Pertahankan deal_id, account_id, snapshot_date, metrics, findings,
   reference_candidates, boundaries, evidence beserta seluruh field bukti turunannya.
   ID deal tidak dikenal: 404 DEAL_NOT_FOUND. Tidak menjalankan Jev.

2. `GET /api/pipeline/initial-analysis`
   Respons 200: `{schema_version: 'v1', ...analyze_pipeline_initial()}`.
   Memuat deals kelima prospek dan statistical_assessment utuh, termasuk
   not_assessed, method/threshold/outlier_deal_ids null. Tidak menjalankan Jev.

3. `GET /api/pipeline/priorities`
   Kumpulkan konteks dan diagnostic kanonis kelima prospek; panggil rank_deals.
   Respons 200 persis envelope ranking di atas. Jangan membuat ranking dalam route.
   Ranking belum terimplementasi: 501 PRIORITIES_NOT_IMPLEMENTED.
   Hasil gagal/incomplete/tidak valid: 503 PRIORITIES_UNAVAILABLE dengan pesan jelas,
   bukan daftar parsial dengan rank yang terlihat lengkap. Jangan menelan bug dependency
   sebagai sekadar belum diimplementasikan; catat exception secara aman tanpa secrets.

Error: `{detail: {code, message}}`. Respons JSON harus menolak NaN/Infinity,
ID sumber tak terselesaikan, duplicate/missing items, invalid rank/path dan snapshot
campuran. Data gap yang sah tetap 200 dengan null/unknown, bukan service failure.
Model response/adapter tidak boleh membuang field provenance yang sudah tersedia.

GET /api/deals, detail, dan POST analyze v1 tetap kompatibel. Fase ini tidak membuat
state persisten: rank/analysis_status pada daftar lama tidak diubah sepihak.
Endpoint priorities adalah sumber ranking dan readiness pipeline baru; sesudah
review, Main/Boy akan menggabungkan per deal_id untuk tampilan. Refresh tidak
bergantung pada urutan siapa yang pernah menekan tombol analyze. Jangan menjalankan
Jev dari GET diagnostic/priorities atau menambah lima panggilan Jev berantai.
Cache hanya bila perlu; key mencakup versi metode/snapshot/dataset, tidak mengubah
input atau menyimpan key/provider response sensitif. Tidak perlu database baru.

## Acceptance lintas modul

- Semua lima deal, rank 1..5 unik; alasan, action, approval, sumber dan jalur terbaca.
- Shuffle input tidak mengubah ranking; tie break stabil dan dijelaskan. Ganti ID
  fixture tidak boleh mempertahankan prioritas karena daftar ID hardcoded.
- P05: insufficient_evidence, discovery, unknowns; tidak dianggap low risk/loss.
- P02 request bukan approval, termasuk regresi R6/R7. Nilai deal besar atau preseden
  sukses tidak boleh menghapus approval gate. Tes approval gate terpisah dari rank.
- P03/P04: reference candidate bukan permission; gunakan verifikasi BIMA-02 terkini.
  Usage bulan lengkap terbaru, missing/zero berbeda, overlap bukan saling kenal.
- Setiap evidence ID dapat diselesaikan ke sumber; setiap path cocok graph asli.
- Bima: HTTP 200 nyata diagnostic semua deal; unknown 404; priorities missing 501;
  ranking invalid/incomplete 503; synthetic mocks diberi label dan dipisah dari live smoke.
- Ical: evaluasi aturan ranking, sensitivitas faktor, tie, missing, seluruh lima deal;
  rules tetap berjalan tanpa key, hasil Jev mock/replay tidak disebut live.
- Kedua PR wajib update handoff masing-masing dengan semua heading dan bukti aktual.
