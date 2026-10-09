# Handoff BIMA

## Task dan status
BIMA-01 / [GitHub Issue #2](https://github.com/feboyfierlyan/dealcompass/issues/2): **READY_FOR_REVIEW** untuk pekerjaan Bima. Bukan VERIFIED/MERGED dan bukan klaim seluruh produk selesai.
Scope P01–P05; P02/DL-002 adalah pembuktian pertama.

- [x] Seluruh 15 sumber CSV/JSONL di-ingest; CSV keputusan kanonis, XLSX tidak menambah keputusan.
- [x] Snapshot bisnis 2026-10-01, angka/tanggal dihitung dari sumber, usage lengkap tetap queryable.
- [x] `build_deal_context` mengembalikan schema v1 untuk DL-001–DL-005.
- [x] I0296/I0348 dan D-2025-02/06 dapat ditelusuri; graph tidak membuat approval P02 atau email preseden.
- [x] Graph temporal, direct/inferred, lookup bukti/subgraph, unknowns dan ID asing 404.
- [x] Route detail/analyze yang sudah ada terhubung ke konteks nyata. Analyze tetap 501 karena implementasi Ical belum tersedia.
- [x] 17 tes Bima dan seluruh 27 tes repo lulus; HTTP server aktual diperiksa.
- [x] Catatan ini memakai seluruh heading template dan mencatat batas integrasi.

## Branch dan commit
Branch aktif `bima/data-graph`; checkout awal bersih. `git fetch origin` berhasil; `git rev-list --left-right --count HEAD...origin/main` menghasilkan `0 0` sebelum implementasi.
Perubahan pekerjaan masih lokal; belum dibuat commit, push atau PR. Jangan menganggap catatan ini sebagai bukti merge.
Issue #2 dibaca lewat API GitHub terautentikasi tanpa mencetak/menyimpan credential.

## File dan fungsi

| File/fungsi | Input → output dan perilaku |
| --- | --- |
| `backend/ingestion/dataset.py:load_dataset(data_dir=DATA_DIR)` | Direktori 15 sumber → `Dataset`; seluruh baris dan raw string dipertahankan, lokasi file/ID/baris disimpan. Duplicate key, angka/tanggal/JSON/CSV rusak menghasilkan error berlokasi. |
| `normalize_row(raw, filename, line)` | Raw string → nilai bertipe: kosong `None`, ID uppercase/trim, email lowercase, peserta ID dinormalisasi, integer kuantitas/IDR, `date`, bulan ISO, `Decimal` diskon. Versi aplikasi tetap string; nilai “tanpa batas” bukan nol. |
| `get_dataset()` | Snapshot sumber cached per proses; `cache_clear()` tersedia untuk fixture. Tidak ada ingest kedua di decision engine. |
| `Dataset.tables / by_id / query(filename, **filters) / inventory()` | Seluruh record, indeks PK/composite key, filter nilai normalisasi, daftar kolom/key/count. Filter tanggal memakai `datetime.date`, ID memakai bentuk kanonis. |
| `backend/ingestion/deals.py:deal_summary(record, dataset, snapshot_date=SNAPSHOT_DATE)` | Record deal dan akun → `DealSummary`; umur stage dan annual value dihitung, bukan ranking/pendapatan realized. |
| `list_deals()` | Dataset bersama → lima prospek terbuka, urutan sumber, total potensi tahunan Rp667.800.000; tidak menetapkan rank atau hasil analisis. |
| `backend/graph/store.py:ContextGraph(dataset)` | Dataset → `NetworkX.MultiDiGraph`, evidence registry dan sumber resolvable pada snapshot bisnis. |
| `ContextGraph.lookup_evidence(evidence_id)` | ID evidence → record sumber asli beserta physical line; agregat → seluruh baris pembentuknya, bukan contoh/sampling. ID asing menghasilkan `KeyError`. |
| `ContextGraph.subgraph(account_ids)` | Set ID akun → `(EvidenceGraph, EvidenceRecord[])`; endpoint edge dan semua evidence IDs disertakan. Tidak menelusuri owner bersama ke seluruh akun lain. |
| `ContextGraph.deal_context(deal_id)` / `get_context_graph()` | Deal prospek terbuka → konteks v1; graph cached per proses. ID asing/closed deal bukan konteks prospek dan menghasilkan `KeyError`. |
| `backend/graph/context.py:build_deal_context(deal_id, snapshot_date='2026-10-01')` | Antarmodul v1 → `DealContext`. Snapshot lain ditolak dengan `ValueError`, bukan rekonstruksi historis palsu dari CRM saat ini. |
| `tests/bima/test_ingestion.py` | Inventaris, normalisasi, fixture 15 sumber, missing/zero, error berlokasi, duplicate key dan JSON rusak. |
| `tests/bima/test_context.py` | Lima deal, preseden P02, integrity graph/evidence, identitas temporal, overlap inferred, future event, exact aggregate dan ambiguity. |
| `tests/bima/test_api.py` | Detail asli 200, ID asing 404, unavailable analyzer 501. Hanya skenario analyzer unavailable yang memakai exception mock; konteks tidak di-mock. |

`backend/main.py` tidak perlu diubah: route yang ada sudah mengimpor fungsi graph dan fungsi Ical. Setelah stub graph diganti, detail memakai implementasi nyata; analyze membangun konteks sebelum memanggil Ical. Tidak ada endpoint baru/`ask`, shim, kontrak baru atau perubahan milik anggota lain.

### Inventaris aktual

Sumber relatif repo: `dataset_kasirnusa/`. Jumlah dihitung dari parser, bukan perkiraan README dataset.
Composite key memakai `|`; `SourceRecord.line` adalah physical line awal record, termasuk CSV quoted/multiline.

| Sumber | Record | Key / ID penghubung |
| --- | ---: | --- |
| crm_accounts.csv | 45 | account_id; account_owner_id, champion_contact_id |
| crm_contacts.csv | 160 | contact_id; account_id_saat_ini, email |
| contact_employment_history.csv | 217 | contact_id\|organisasi\|mulai; account_id dan interval mulai–selesai |
| crm_deals.csv | 22 | deal_id; account_id, owner_id, kompetitor |
| employees.csv | 10 | employee_id; email |
| interactions.jsonl | 350 | interaction_id; account_id, email dari/ke, peserta, membalas_id |
| outlets.csv | 620 | outlet_id; account_id |
| product_usage_daily.csv | 226300 | tanggal\|outlet_id; account_id, versi_aplikasi |
| feature_usage_monthly.csv | 1178 | bulan\|account_id\|feature_id |
| support_tickets.csv | 640 | ticket_id; account_id, outlet_id, pelapor_contact_id, bug_id, versi_aplikasi |
| bugs.csv | 4 | bug_id; fitur_terkait, versi_terdampak |
| releases.csv | 3 | versi; tanggal_rilis |
| features.csv | 8 | feature_id; target awal/terkini |
| contracts_billing.csv | 40 | contract_id; account_id, decision_id |
| decision_log.csv | 30 | decision_id; account_id, deal_id, employee IDs, bukti_interaction_id, fitur_dijanjikan |
| **Total** | **229627** | **14 CSV + 1 JSONL; XLSX dikecualikan** |

Kolom lengkap (juga tersedia lewat `Dataset.inventory()`):
- **crm_accounts.csv:** account_id, nama, tipe, industri, kota, paket, jumlah_outlet, account_owner_id, champion_contact_id, nps_terakhir, health_score_dashboard.
- **crm_contacts.csv:** contact_id, nama, email, account_id_saat_ini, jabatan_saat_ini.
- **contact_employment_history.csv:** contact_id, account_id, organisasi, jabatan, mulai, selesai.
- **crm_deals.csv:** deal_id, account_id, tipe, stage, stage_sejak, dibuat, owner_id, outlet, nilai_tahunan, status, alasan_kalah, kompetitor.
- **employees.csv:** employee_id, nama, jabatan, email.
- **interactions.jsonl:** interaction_id, tanggal, tipe, account_id, dari, ke, peserta, subjek, isi, membalas_id.
- **outlets.csv:** outlet_id, account_id, kota, mode_offline_aktif.
- **product_usage_daily.csv:** tanggal, outlet_id, account_id, versi_aplikasi, jumlah_transaksi, transaksi_offline_tersinkron.
- **feature_usage_monthly.csv:** bulan, account_id, feature_id, pengguna_aktif.
- **support_tickets.csv:** ticket_id, dibuat, account_id, outlet_id, pelapor_contact_id, kategori, prioritas, status, versi_aplikasi, judul, deskripsi, bug_id, diselesaikan.
- **bugs.csv:** bug_id, judul, versi_terdampak, status, dibuat, selesai, fitur_terkait.
- **releases.csv:** versi, tanggal_rilis.
- **features.csv:** feature_id, nama, status, target_awal, target_terkini, catatan.
- **contracts_billing.csv:** contract_id, account_id, paket, outlet_kontrak, batas_outlet_paket, mulai, tanggal_renewal, harga_per_outlet_bulan, diskon_pct, nilai_tahunan, keterlambatan_bayar_12bln, decision_id.
- **decision_log.csv:** decision_id, tanggal, tipe, account_id, deal_id, diminta_oleh, diputuskan_oleh, keputusan, nilai, alasan, bukti_interaction_id, fitur_dijanjikan, status_janji.

### Graph dan provenance

Snapshot graph aktual: **3907 node, 8657 edge, 4003 evidence**, termasuk **676 agregat usage**.
Node meliputi akun, kontak, employee, organisasi eksternal, deal, interaksi, email, keputusan, kontrak, outlet, tiket, bug, release, feature, usage bulanan dan agregat usage harian per akun/bulan/versi.
Relasi direct: kepemilikan/CRM champion, employment, current CRM account, deal/account, keputusan/deal/peminta/pengambil keputusan/bukti/janji fitur, kontrak/decision, tiket/outlet/pelapor/bug, bug/feature/versi, email sender/recipient, peserta dan reply, usage/feature/versi. `mentions` hanya rujukan teks, bukan sebab/approval.

Relasi inferred: identitas email lama, overlap masa kerja, lexical feature match, agregat, related-account dan candidate-precedent.
Kandidat lintas akun dicari dari kompetitor yang sama, industri beririsan, employment terdahulu, overlap pekerjaan, atau usage feature yang diminta sebagai referensi. Setiap hubungan mempunyai sumber; hubungan tersebut **bukan** skor relevansi, ranking, acquaintance, persetujuan referensi atau rekomendasi.
Preseden menyimpan semua field CSV asli sebagai string. Source ID bukti direct adalah PK/composite key; source ID agregat `lines:<ranges>` menunjuk tepat baris CSV pembentuknya. Evidence IDs agregat stabil berdasarkan akun/bulan/versi. Ringkasan memisahkan offline missing dan observed zero.
Event setelah snapshot tidak masuk graph; employment historis tetap ada dengan masa berlaku. Total bulanan baru dipakai setelah bulan lengkap. CRM master adalah keadaan snapshot, bukan replay keadaan masa lalu.

## Kontrak dan dependency
Tetap **v1**, `backend/contracts.py` dan `docs/coordination/API_CONTRACT.md` tidak diubah. Semua edge menunjuk node/evidence yang tersedia.
Dependency yang sudah ditetapkan Main dipasang dengan `python -m pip install -r requirements.txt`; tidak mengubah file dependency. Runtime aktual: Python 3.14.7, NetworkX 3.7, FastAPI 0.127.0, Pydantic 2.12.5.
Ical memakai `backend.graph.context.build_deal_context` → `backend.decision.analyze.analyze_deal(context)`; Boy tetap memanggil endpoint v1 yang sama.
Tidak mengusulkan perubahan schema/endpoint. Lookup bukti/subgraph saat ini fungsi internal sesuai prompt Bima.

## Cara menjalankan
Prasyarat proyek Python 3.11+; gunakan dependency repo. Dari root:

```bash
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
python -m unittest discover -s tests -v
python scripts/check_handoff.py --all
```

Detail: `GET http://127.0.0.1:8765/api/deals/DL-002`; ganti dengan DL-001/DL-003/DL-004/DL-005 untuk cakupan lain.
API memakai **deal_id**, bukan P02. Server smoke dimatikan setelah pemeriksaan; port di atas hanya port verifikasi, bukan perubahan konfigurasi produk.
Contoh query internal: `get_dataset().query('product_usage_daily.csv', account_id='C23')`; lookup: `get_context_graph().lookup_evidence('interactions.jsonl:I0296')`.
Cache memuat sumber sekali per proses; restart server jika sumber lokal diganti pada fixture. Dataset asli tidak diubah.

## Pengujian aktual
Tanggal 2026-10-09, WIB; hasil berikut dari eksekusi sesi ini, bukan hasil bootstrap Main.

1. Sebelum implementasi, `python -c "from backend.graph.context import build_deal_context; build_deal_context('DL-002')"` menghasilkan `NotImplementedError` dari stub graph.
2. Run pertama `python -m unittest discover -s tests -v`: 24 tes, 23 lulus, satu error karena industri fixture kosong menjadi `None` lalu `.lower()`. Pencarian diperbaiki agar tidak mencocokkan data kosong dan menambah unknown.
3. Regression spesifik `python -m unittest tests.bima.test_context.SnapshotFixtureTests.test_future_interaction_is_ingested_but_not_graph_evidence -v`: 1 tes lulus.
4. Run setelah integrasi dan tambahan boundary test, `python -m unittest discover -s tests -v`: **27 tes lulus, 4.145 s**; 17 milik Bima. Fixture temporary tidak mengubah sumber asli.
5. Server nyata: `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765`. Python Eval/stdlib `urllib.request` memanggil HTTP aktual, bukan TestClient; respons setiap detail divalidasi `DealContext.model_validate`.

| Runtime path | Hasil aktual |
| --- | --- |
| GET /health | 200; ok, v1, snapshot 2026-10-01 |
| GET /api/deals | 200; lima prospek, jumlah annual value Rp667.800.000 |
| GET /api/deals/DL-001 sampai DL-005 | Seluruhnya 200; schema, keunikan ID, endpoint edge dan evidence IDs diperiksa |
| GET /api/deals/DL-999 | 404 DEAL_NOT_FOUND |
| POST /api/deals/DL-999/analyze | 404 DEAL_NOT_FOUND |
| GET /api/deals/P02 | 404 DEAL_NOT_FOUND; account_id tidak ditukar dengan deal_id |
| GET /api/deals/DL-006 | 404 DEAL_NOT_FOUND; historical deal tersedia sebagai bukti, bukan prospek terbuka |
| POST /api/deals/DL-002/analyze | 501 NOT_IMPLEMENTED dari stub Ical; tidak ada recommendation rekaan |

| Konteks | Node | Edge | Evidence | Candidate decisions | Unknowns |
| --- | ---: | ---: | ---: | ---: | ---: |
| P01 / DL-001 | 749 | 1647 | 763 | 6 | 12 |
| P02 / DL-002 | 1305 | 2895 | 1361 | 13 | 19 |
| P03 / DL-003 | 443 | 941 | 476 | 3 | 8 |
| P04 / DL-004 | 147 | 297 | 147 | 0 | 6 |
| P05 / DL-005 | 3 | 3 | 3 | 0 | 5 |

Smoke internal tambahan memeriksa semua edge graph terhadap evidence registry dan **seluruh** agregat terhadap record sumber: 226300 baris terselesaikan tepat sekali, total 53524240 transaksi server, 215350 nilai offline kosong. Tidak mengubah kosong menjadi nol atau mengklaim jumlah transaksi sebenarnya di kasir.
Script smoke tidak disimpan di repo. Langkah mencatat timestamp awal gagal karena Windows tidak memiliki database `tzdata`; perilaku HTTP dan assertion graph telah selesai sebelumnya. Pencatatan waktu diulang hanya pada langkah gagal dengan UTC+07:00, tanpa perubahan dependency.
`python scripts/check_handoff.py --all`: **lulus**, output “Handoff valid. Main tetap memverifikasi kebenaran laporan dan integrasi.”
`scripts.check_handoff.validate_changes` dengan delapan file yang dibuat/diubah sesi ini dan branch `bima/data-graph`: **lulus**, tanpa pelanggaran heading/ownership. Ini pemeriksaan file hasil sesi, **bukan** diff PR yang sudah committed.
Frontend build, Jev live, rekomendasi Ical, ranking dan UI end-to-end **tidak diuji** pada tugas Bima. Server smoke sudah dihentikan.

### Bukti P02 dan coverage lain
- P02: I0269 discovery, I0296 keberatan harga/kompetitor sekitar 20% lebih murah, I0322 follow-up dan I0348 usulan diskon 20%. I0348 adalah **permintaan**, tidak ada log approval untuk P02.
- C23/DL-006 + D-2025-02: diskon 20% ditolak; deal kalah dengan alasan harga.
- C23/DL-007 + D-2025-06: pengecualian paket Starter tanpa diskon, pilot enam outlet disetujui pada log; deal menang. **Bukan** approval pilot/diskon untuk P02.
- Kedua preseden mempunyai evidence CSV dan hubungan inferred `candidate_precedent_same_competitor`; `bukti_interaction_id` keduanya kosong, tanpa email buatan.
- P01: konteks memuat K017, perpindahan C01 → P01, email lama yang inferred dan status FEAT-07 tanpa tanggal pasti.
- P03: interaksi I0334, permintaan referensi apotek dan usage FEAT-05 sebagai penghubung kandidat, bukan approval referensi.
- P04: I0335 menunda pengadaan sampai ada referensi; graph mencakup network temporal. Tidak ada candidate decision melalui penghubung yang tersedia.
- P05: tidak ada interaksi/kontak kebutuhan/preseden relevan melalui penghubung saat ini; unknowns eksplisit, bukan analisis siap atau closing rekaan.

## Fixture dan keterbatasan
Dataset sumber sintetis asli dipakai untuk konteks dan HTTP smoke. Small fixtures menulis seluruh 15 sumber di temporary directory untuk malformed value, duplicate key, whitespace/case ID, missing versus zero, future interaction, exact aggregate, dan alias email ambigu/di luar employment.
Semua sumber keputusan ditelusuri ke CSV; **29 dari 30** keputusan tidak mempunyai bukti_interaction_id. Tidak menambal kekosongan dengan interaksi sintetis.
Email lama dicocokkan hanya bila local-part sama dan tepat satu identitas memiliki employment pada akun/tanggal interaksi; tetap **inferred**, belum konfirmasi langsung.
Overlap kerja membuktikan periode/organisasi, bukan saling kenal. Gejala/versi/tiket linked_bug bukan bukti penyebab seluruh penurunan usage. Tidak menghasilkan confidence Jev, approval, ranking atau probabilitas closing.
Master CRM bersifat snapshot; tanggal lain sengaja ditolak. Field roadmap quarter/“Belum ditetapkan” tetap string, bukan tanggal rilis palsu.
P02 memiliki 13 kandidat dari graph pencarian, bukan dua preseden terpilih oleh decision engine. Ical harus membandingkan applicability dan menyebut bukti/unknowns.
Payload P02 pada smoke 1687310 byte karena konteks menyertakan sumber terkait dan locator agregat lengkap. Belum melakukan benchmark atau verifikasi renderer frontend; ini batas integrasi UI, bukan klaim UI lulus.

## Blocker
Tidak ada blocker untuk loader, konteks lima prospek dan endpoint detail Bima.
**Integrasi rekomendasi nyata menunggu Ical**: `backend/decision/analyze.py` masih `NotImplementedError`; 501 nyata teramati. Main/Ical perlu menyediakan implementation tanpa mengubah loader/kontrak diam-diam. Tidak ada Jev live yang diuji.
NetworkX awalnya belum terpasang, sudah diselesaikan dari requirements repo. `gh` tidak tersedia dan URL issue private memberi 404 tanpa auth; isi issue berhasil dibaca lewat API authenticated tanpa mencetak secret.

## Tugas berikutnya
1. Bima: commit file miliknya beserta handoff ini, push `bima/data-graph`, buka PR untuk Issue #2; catat hash/PR setelah benar-benar tersedia.
2. Ical: gunakan konteks nyata, pilih/bandingkan preseden yang relevan, policy diskon >10% wajib VP Sales dan log; permintaan I0348 tidak dianggap approval. Candidate/evidence IDs rekomendasi harus resolvable.
3. Main: review sumber dan acceptance; jalankan suite serta smoke ulang setelah mengintegrasikan Ical. Baru Main menetapkan VERIFIED/MERGED dan memperbarui README/status koordinasi yang masih menjelaskan bootstrap.
4. Boy/Main: periksa detail/graph/evidence di UI untuk P01–P05, termasuk unknowns P05 dan ukuran payload; belum ada bukti UI dari pekerjaan ini.
5. Produk final tetap mencakup P01–P05, analisis, ranking lintas deal dan integrasi Jev/evaluasi milik tim. Keberhasilan konteks P02 tidak menutup scope akhir.

## Update WIB
2026-10-09 16:35:59 WIB (waktu aktual pencatatan pemeriksaan handoff/ownership, UTC+07:00).
