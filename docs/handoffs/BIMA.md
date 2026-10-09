# Handoff BIMA

## Task dan status
**BIMA-02: READY_FOR_REVIEW.** Analisis awal internal dan bersumber untuk P01–P05 pada snapshot **2026-10-01**. Bima tidak menetapkan VERIFIED/MERGED; keputusan itu milik Main.

BIMA-01 / Issue #2 / [PR #6](https://github.com/feboyfierlyan/dealcompass/pull/6) sudah merged oleh Main (`73fb045`), bukan PR yang dibuka ulang. Acuan BIMA-02: `docs/coordination/MAIN.md`, `API_CONTRACT.md`, dan `docs/reviews/2026-10-09-pr5-7.md`.

- Umur deal/tahap, jumlah dan tanggal terakhir interaksi dihitung dari sumber.
- Setiap temuan mempunyai fakta, evidence IDs, interpretasi inferred, informasi kurang, dan implikasi pemeriksaan tindak lanjut.
- Identitas P01 serta kandidat referensi P03/P04 ditelusuri; kandidat bukan kelayakan atau izin.
- Business anomaly, data gap, dan outlier statistik dibedakan. Tidak ada ranking, approval, confidence Jev, atau closing rekaan.
- Kontrak API, engine Ical, frontend, dependency, koordinasi, dan dataset asli tidak diubah.

## Branch dan commit
Branch `bima/data-graph`; checkout awal BIMA-02 bersih. `git fetch origin` dan fast-forward `origin/main` ke `ddf7a2a` berhasil; pekerjaan BIMA-01 dipertahankan.

Commit kode BIMA-02 beserta handoff: [`3b172621eee3a4f19738c4d57a668a2faad099bf`](https://github.com/feboyfierlyan/dealcompass/commit/3b172621eee3a4f19738c4d57a668a2faad099bf). `git push origin bima/data-graph` berhasil tanpa force. **[PR #10](https://github.com/feboyfierlyan/dealcompass/pull/10)** baru dibuka, base `main`, status open, review diminta ke Main (`feboyfierlyan`). Pembaruan receipt ini disertakan pada commit handoff terpisah, bukan klaim approval review.

Histori BIMA-01: commit kode `642d97fec3c524f888d1d3d9430fc5cf863f2659`, catatan publikasi `c5e8820f3a76cd6d1669b665efd961233490fd5e`, kemudian PR #6 merged oleh Main.

## File dan fungsi
| File/fungsi baru | Input → output dan batas |
| --- | --- |
| `backend/ingestion/metrics.py:summarize_deal(deal_id, snapshot_date='2026-10-01', dataset=...)` | Deal prospek terbuka → umur deal/tahap, bucket external/internal/unclassified, tanggal terakhir beserta seluruh tied IDs, query scope dan unknowns. Umur tidak valid/missing tetap null; nol valid tidak diubah menjadi missing. |
| `metrics.py:evidence_id(record)` | SourceRecord → ID kanonis `filename:source_id`. |
| `backend/graph/verification.py:verify_authority_paths(context, dataset=...)` | Konteks v1 → temuan kewenangan dari percakapan fokus + role + employment aktif. Kandidat ambigu/tidak cocok tetap unknown; bukan memilih jabatan tertinggi. |
| `verification.py:reference_request_rows(context, dataset=...)` | Konteks v1 → record permintaan referensi pelanggan yang bertanggal, dalam jendela deal dan terhubung melalui edge kanonis. Parser yang sama digunakan analisis dan verifikasi. |
| `verification.py:verify_reference_candidates(context, dataset=...)` | Konteks v1 → kandidat pelanggan melalui `related_account_*`, kontak/history/overlap dan usage bulan lengkap terbaru; suitability/willingness/consent tetap null. |
| `backend/graph/analysis.py:analyze_deal_initial(context, dataset=...)` | DealContext → report internal berisi metrics, findings, reference_candidates, boundaries dan registry EvidenceRecord. Harga pelanggan dan usulan diskon internal dipisahkan; sumber akun lain tidak menjadi diagnosis fokus. |
| `analysis.py:analyze_pipeline_initial(snapshot_date='2026-10-01', dataset=...)` | Dataset/konteks kanonis → laporan seluruh prospek terbuka dan statistical_assessment `not_assessed`. Tidak menghasilkan Recommendation Ical. |
| `tests/bima/test_metrics.py` | 12 tes perhitungan, cutoff, ties, missing/zero, akun fokus, tanggal invalid dan gate snapshot. |
| `tests/bima/test_verification.py` | 27 tes jalur identitas/referensi, vocabulary kanonis, ambiguity, temporal overlap, negatif/subject-only/outbound, latest usage zero/missing/future. |
| `tests/bima/test_analysis.py` | 9 tes diagnosis/source IDs, isolasi akun, request bukan approval, P05 gap, dan tidak mengarang outlier. |

Fondasi BIMA-01 tetap dipakai: `load_dataset/get_dataset`, `Dataset.query/inventory/by_id`, `ContextGraph.lookup_evidence/subgraph/deal_context`, dan `build_deal_context`. Inventaris sumber tetap 15 CSV/JSONL dan 229627 record, termasuk 226300 usage harian serta 30 keputusan CSV; XLSX bukan sumber tambahan. Rincian inventaris BIMA-01 tersedia pada histori PR #6.

### Ringkasan untuk mentor
Umur adalah selisih hari kalender pada snapshot. Interaksi dihitung hanya untuk akun fokus sejak deal dibuat sampai snapshot, inklusif. External mencakup email keluar dan meeting, **bukan jumlah balasan buyer**. Email internal tidak mengubah tanggal terakhir external. `null` berarti tidak ada tanggal tersedia dalam query, bukan tanggal buatan.

| Deal/akun | Umur deal | Umur tahap | External | Internal | Total | Terakhir external | Terakhir internal | Terakhir semua |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| DL-001/P01 | 61 | 20 | 4 | 0 | 4 | 2026-09-24 | null | 2026-09-24 |
| DL-002/P02 | 68 | 45 | 3 | 1 | 4 | 2026-09-05 | 2026-09-28 | 2026-09-28 |
| DL-003/P03 | 16 | 10 | 1 | 0 | 1 | 2026-09-21 | null | 2026-09-21 |
| DL-004/P04 | 57 | 30 | 3 | 0 | 3 | 2026-09-22 | null | 2026-09-22 |
| DL-005/P05 | 5 | 5 | 0 | 0 | 0 | null | null | null |

Umur bersumber `crm_deals.csv:DL-001` sampai `DL-005`. Set interaksi external: P01 I0279/I0310/I0325/I0343; P02 I0269/I0296/I0322; P03 I0334; P04 I0284/I0314/I0335; P05 kosong. Internal P02 I0348; seluruh ID interaksi memakai prefix `interactions.jsonl:`. I0322 adalah follow-up sales, tidak dianggap respons pelanggan.

**P01 — jalur kewenangan pengadaan**
- Fakta: I0343/Fajar menyatakan proposal diteruskan ke GM Operations baru yang bergabung awal September, keputusan pengadaan pada orang tersebut, sedangkan dirinya teknis. CRM K017/Rina Hapsari berjabatan GM Operations P01 dengan employment mulai 2026-09-01.
- Bukti: `interactions.jsonl:I0343`, `crm_contacts.csv:K052`, `crm_contacts.csv:K017`, `contact_employment_history.csv:K017|Grup Ritel Mandala|2026-09-01` dan deal DL-001.
- Interpretasi: gabungan isi percakapan, role dan interval mengarah ke K017; **inferred**, bukan edge decision-maker eksplisit atau pilihan otomatis CEO K089.
- Kurang: konfirmasi identitas pemegang kewenangan, mandat dan proses pengadaan terkini.
- Implikasi: verifikasi kepada Fajar dan identifikasi jalur pengadaan sebelum memperlakukan kandidat sebagai pengambil keputusan yang terkonfirmasi.
- Jalur identitas historis: employment K017 di C01 mulai 2021-03-01 sampai 2026-08-15 (`contact_employment_history.csv:K017|Kopi Lintas Nusantara|2021-03-01`) + kontak K017 + I0051/I0066/I0159/I0223/I0224/I0290 mendukung alias `rina.hapsari@kopilintas.co.id`. Setiap path mempunyai tiga record sumber dan interval; alias tetap inferred, bukan alamat baru atau konfirmasi langsung.

**P02 — harga berbeda dari approval**
- Fakta: I0296 menyebut harga tinggi dan KasirPro sekitar 20% lebih murah. I0348 adalah Citra mengusulkan diskon 20% kepada Andi/VP Sales. Pencarian 30 record `decision_log.csv` dengan account_id P02, deal_id DL-002 dan tanggal ≤ snapshot menemukan nol log fokus.
- Bukti: `interactions.jsonl:I0296`, `interactions.jsonl:I0348`, `employees.csv:E01`, `crm_deals.csv:DL-002`; report menyimpan filter, file sumber dan inspected_record_count pencarian log.
- Interpretasi: keberatan harga didukung percakapan; email sales adalah permintaan, bukan approval. Angka diskon tidak diduplikasi dari subjek. Log C01 tidak mengesahkan P02.
- Kurang: batas anggaran, kesetaraan lingkup kompetitor, keputusan permintaan serta justifikasi komersial. Nol log dalam dataset tidak membuktikan keputusan tidak pernah ada di luar sumber.
- Implikasi: klarifikasi harga/lingkup dan periksa keputusan + log sebelum menawarkan diskon; >10% memerlukan VP Sales dan pencatatan sesuai kontrak tim.
- Preseden D-2025-02/D-2025-06 tetap tersedia di konteks BIMA-01: penolakan diskon 20% dan pilot tanpa diskon pada C23 adalah preseden historis, **bukan** approval P02. Pemilihan applicability tetap milik Ical.

**P03 — permintaan referensi apotek**
- Fakta: I0334/Ratna meminta referensi apotek. Kandidat C03/C09/C17/C27 ditelusuri dari akun fokus melalui industri/FEAT-05; usage September 2026 adalah bulan lengkap terbaru.
- Bukti: `interactions.jsonl:I0334`, `crm_accounts.csv:C03/C09/C17/C27` (empat ID terpisah), `feature_usage_monthly.csv:2026-09|C03|FEAT-05` dan key setara C09/C17/C27; relasi dan source IDs lengkap ada dalam report.
- Interpretasi: permintaan perlu dijawab, tetapi tidak otomatis membuktikan deal sudah tertunda. Usage hanya bukti pemakaian fitur, bukan kualitas implementasi atau kesediaan menjadi referensi.
- Kurang: kriteria kemiripan yang diterima Ratna, pengalaman terkini, suitability serta izin kandidat/contact.
- Implikasi: validasi kebutuhan referensi, periksa kandidat dengan account owner, lalu minta izin sebelum perkenalan. Tidak memilih pemenang atau membuat ranking.

| Kandidat | Akun | Outlet CRM | Pengguna aktif FEAT-05 September |
| --- | --- | ---: | ---: |
| C03 | Apotek Sehat Sentosa | 18 | 14 |
| C09 | Apotek Medika Farma | 15 | 11 |
| C17 | Apotek Bunda Sehat | 10 | 22 |
| C27 | Apotek Kimia Sejahtera | 22 | 48 |

**P04 — referensi menjadi syarat, jalur network belum izin**
- Fakta: I0335/Yuli menyatakan direktur meminta rekomendasi pengguna mirip sebelum tanda tangan dan menunda sampai ada referensi. K028/Hartono dan K116/Budi pernah bekerja di PT Sentosa Abadi Group, overlap 2015-02-01–2019-11-30. Budi kini CFO C06/Saiyo Group, history mulai 2020-01-02.
- Bukti: `interactions.jsonl:I0335`, kontak K028/K116, akun P04/C06, dan `contact_employment_history.csv:K028|PT Sentosa Abadi Group|2015-01-01`, `...:K116|PT Sentosa Abadi Group|2015-02-01`, `...:K116|Saiyo Group|2020-01-02` (prefix file sama).
- Interpretasi: percakapan mendukung hambatan referensi; overlap memberi jalur kandidat C06, **bukan** bukti saling kenal. P04 Hospitality dan C06 Resto Padang tidak otomatis memenuhi kriteria mirip.
- Kurang: acquaintance, kesesuaian pengalaman/operasi, willingness dan consent.
- Implikasi: pastikan kriteria dengan Yuli, verifikasi jalur melalui account owner dan minta izin; jangan menjanjikan endorsement direktur atau kandidat.

**P05 — informasi belum cukup**
- Fakta: tidak ada interaksi external/internal bertanggal untuk P05 dalam jendela deal-snapshot; last_date null. Bukti `crm_deals.csv:DL-005`, `crm_accounts.csv:P05`, plus query scope `interactions.jsonl`/P05/2026-09-26–2026-10-01 dalam report.
- Interpretasi: **data_gap**, bukan bukti tidak berminat, kalah atau outlier.
- Kurang: kebutuhan, kontak, hambatan, kewenangan dan proses pengadaan yang didukung percakapan.
- Implikasi: lengkapi discovery dan pencatatan, bukan membuat diagnosis komersial dari kekosongan.

**Klasifikasi:** business_anomaly berarti hambatan/ketidakselarasan yang didukung percakapan, bukan pelanggaran SLA. Data_gap adalah batas pengetahuan. Statistical outlier **not_assessed**: lima prospek berada pada lima tahap berbeda, tidak tersedia cohort pembanding per tahap/segmen atau SLA; method/threshold/outlier_deal_ids null. Umur maksimum hanya deskripsi, bukan dasar memberi label outlier.

## Kontrak dan dependency
Tetap **v1**; `backend/contracts.py` dan `docs/coordination/` tidak diubah. Menggunakan `interaction_for`, `employed_at`, `overlapping_employment` dan `related_account_*` kanonis. EvidenceRecord memakai JSON row asli di excerpt; `isi` adalah pesan, subjek metadata. Semua source IDs report dapat diselesaikan ke record direct. Identitas/hubungan/interpretasi tetap diberi batas inferred.

Tidak menambah dependency atau endpoint. Usulan kepada Main (belum disetujui/diimplementasikan): **GET `/api/deals/{deal_id}/initial-analysis`** untuk laporan diagnostik bersumber, terpisah dari Recommendation Ical. Field yang diperlukan: snapshot; umur deal/tahap beserta age_evidence_ids; jumlah/latest per tipe beserta query_scope dan unknowns; findings dengan fact/evidence_ids/interpretation/missing_information/follow_up_implication; kandidat dengan jalur/usage/latest period dan null suitability/willingness/consent; evidence registry. Main menentukan bentuk/versi kontrak, akses UI dan apakah endpoint ini diperlukan; Bima tidak melakukan cutover sepihak.

## Cara menjalankan
Dari root repo, dengan dependency proyek terpasang:

```bash
python -m unittest discover -s tests -v
python scripts/check_handoff.py --all
python -c "import json; from backend.graph.analysis import analyze_pipeline_initial; print(json.dumps(analyze_pipeline_initial(), ensure_ascii=False, indent=2, allow_nan=False))"
```

Single deal: panggil `analyze_deal_initial(build_deal_context('DL-002'))`; bukan Recommendation dan tidak dipanggil oleh route analyze yang ada. Lookup sumber: `get_dataset().by_id['interactions.jsonl']['I0348']` atau `get_context_graph().lookup_evidence('interactions.jsonl:I0348')`. Snapshot lain ditolak, bukan replay historis palsu. Dataset/cache tidak dimodifikasi; fixture memakai temporary directory.

## Pengujian aktual
2026-10-09, WIB; berikut eksekusi BIMA-02, bukan klaim hasil integrator:

- Integration run awal: `python -m unittest discover -s tests -v` — **75 tes lulus, 12.824 s**.
- Run final setelah pembersihan assertion incidental: perintah sama — **75 tes lulus, 10.683 s**. Total 65 tes Bima (48 baru BIMA-02), 10 bootstrap/handoff; tidak ada perubahan kode setelah run ini.
- Smoke fungsi internal aktual pada **17:47:08 WIB**: canonical contexts → metrics/findings → serialisasi JSON strict dan round-trip consumer → EvidenceRecord validation → lookup sumber. Semua excerpt sama dengan row raw, source_file/source_id tepat, lima akun lengkap; setiap temuan memiliki komponen wajib dan evidence resolvable. Kandidat suitability/willingness/consent null; statistik not_assessed. Output `SMOKE PASS: canonical contexts -> metrics/findings -> JSON consumer -> original source rows`.
- Smoke sebelumnya pada 17:43:22 WIB juga memeriksa jalur identity/overlap dan setiap sumber laporan. Tidak membuat file smoke permanen atau mengubah dataset.
- `python scripts/check_handoff.py --all` — lulus: “Handoff valid. Main tetap memverifikasi kebenaran laporan dan integrasi.”
- `python scripts/check_handoff.py --base origin/main --head HEAD --branch bima/data-graph` pada commit kode `3b17262` — lulus terhadap diff committed; hanya tujuh file Bima/handoff berubah.

BIMA-01 historis: 27 tes, HTTP detail seluruh DL-001–DL-005 200, unknown 404 dan analyzer unavailable 501 pernah diamati sebelum merge PR #6. **Bukan** smoke HTTP baru BIMA-02. Frontend/UI, Jev live, rekomendasi/ranking Ical dan end-to-end produk tidak diuji pada BIMA-02.

## Fixture dan keterbatasan
Sumber sintetis kanonis digunakan untuk smoke dan regression nyata. Small fixtures terisolasi menguji batas tanggal inklusif, akun lain, tanggal/type missing, zero, ties, title-only, negated/subject-only/outbound/internal claims, ID yang berubah, employment ambigu/berakhir, vocabulary nonkanonis, dan latest usage zero/missing/future tanpa fallback positif lama.

Parser percakapan adalah aturan lexical untuk isi pesan kanonis; bukan NLP umum atau verifikasi mandat hukum. Kandidat unik dari role/history tetap inference. Overlap kerja tidak membuktikan acquaintance. Usage FEAT-05 tidak membuktikan eligibility/consent. External count bukan buyer-response count. Absence memiliki query scope, bukan bukti universal tidak ada aktivitas. Tidak memvalidasi/mengeluarkan approval, SLA, Jev confidence atau statistik outlier.

CRM adalah snapshot 2026-10-01; tidak mendukung tanggal lain. Laporan internal tidak menambah schema API dan belum ditampilkan UI. Temuan diagnostic tidak menggantikan analisis/policy Ical. Masalah Ical/Boy yang dicatat review Main tetap di area mereka; Bima tidak mengubah implementasi itu atau mengklaim sudah memperbaikinya.

## Blocker
Tidak ada blocker untuk analisis internal P01–P05 dan sumbernya. Integrasi field/endpoint/UI menunggu keputusan Main atas usulan kontrak; suitability/izin referensi dan konfirmasi procurement membutuhkan informasi bisnis di luar dataset, dinyatakan unknown bukan diisi rekaan. Jev/ranking/evaluasi tetap milik Ical.

## Tugas berikutnya
1. Bima: PR #10 sudah dibuka dan review Main diminta; tanggapi review pada branch yang sama dan sertakan handoff di setiap perubahan. PR #6 tetap selesai.
2. Main: review metrik, source paths, klasifikasi, batas izin/approval dan usulan endpoint; hanya Main menetapkan VERIFIED/MERGED serta mengubah kontrak/koordinasi.
3. Ical: konsumsi konteks kanonis; jangan memakai C01 sebagai sinyal fokus P02, menganggap I0348 approval, atau kandidat sebagai reference permission. Diagnostic internal bukan keputusan penawaran.
4. Boy/Main: tentukan penyajian metrik dan bukti yang dapat dibaca mentor, beserta unknowns P05, setelah kontrak UI disepakati.
5. Tim/manusia: konfirmasi kewenangan P01, keputusan harga P02, kriteria/izin kandidat P03/P04 dan discovery P05. Scope akhir tetap P01–P05.

## Update WIB
2026-10-09 17:52:08 WIB (waktu aktual PR #10 dibuat dan review Main diminta; UTC+07:00). Status penyerahan READY_FOR_REVIEW, belum verifikasi Main.
