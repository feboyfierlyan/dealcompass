# Handoff BIMA

## Task dan status
**BIMA-03: READY_FOR_REVIEW.** API diagnostic P01–P05 selesai dan adapter priorities siap sesuai `docs/coordination/PHASE3_CONTRACT.md` / `docs/prompts/BIMA-03.md`. Snapshot tetap **2026-10-01**. Main yang menetapkan VERIFIED/MERGED.

- GET diagnostic deal dan pipeline menggunakan fungsi BIMA-02 nyata, tanpa data statis atau Jev.
- Metrics, findings, reference_candidates, unknowns/missing_information, query scopes, boundaries, statistical_assessment dan seluruh field provenance dipertahankan. Null/zero tidak diubah.
- GET priorities hanya memanggil fungsi ranking milik Ical. Bima tidak menghitung skor/bobot/ranking bisnis.
- Lima input lengkap, rank, snapshot, sumber dan path graph divalidasi sebelum respons sukses. Output gagal/invalid/incomplete adalah 503, bukan ranking contoh.
- **Ranking Ical belum tersedia pada main yang difetch (`712acf9`)**: respons nyata priorities 501. Success/error ranking dengan engine sintetis secara eksplisit berlabel SYNTHETIC/MOCK, bukan integrasi ranking nyata.
- Endpoint lama tetap kompatibel; rank/analysis_status daftar lama tidak diubah. Tidak mengubah decision engine, shared contracts, frontend, dataset, dependency, CI atau koordinasi.

Histori: BIMA-01 [PR #6](https://github.com/feboyfierlyan/dealcompass/pull/6) dan BIMA-02 [PR #10](https://github.com/feboyfierlyan/dealcompass/pull/10) sudah merged oleh Main. Inventaris/sumber serta temuan mentor BIMA-02 tetap tersedia pada histori #10 dan produsen internal; keduanya tidak dibuka ulang.

## Branch dan commit
Branch baru **`bima/diagnostics-api`** dibuat dari `origin/main` `712acf9` setelah `git status --short --branch` menunjukkan checkout bersih dan `git fetch origin` berhasil. Branch lama `bima/data-graph` dipertahankan.

Refresh kedua `git fetch origin && git merge --ff-only origin/main` menghasilkan “Already up to date.” Tidak cherry-pick branch Ical. Commit/push/PR BIMA-03 belum dibuat pada pembaruan ini; receipt SHA dan URL ditambahkan setelah publikasi berhasil.

## File dan fungsi
| File/fungsi | Input → output / tanggung jawab |
| --- | --- |
| `backend/main.py` | Menambah tiga GET fase 3; diagnostic single memakai `require_deal` yang sama untuk 404. Route v1 lama tidak diubah. |
| `backend/api/phase3.py:deal_initial_analysis(deal_id)` | Konteks kanonis + `analyze_deal_initial` → envelope `{schema_version:'v1', ...report}` tervalidasi; kegagalan diagnostic 503 DIAGNOSTICS_UNAVAILABLE. |
| `phase3.py:pipeline_initial_analysis()` / `_pipeline_inputs()` | `list_deals`, `build_deal_context`, `analyze_pipeline_initial` → lima konteks/report lengkap dan statistik utuh. Tidak bergantung pada klik analyze. |
| `phase3.py:load_rank_deals()` / `pipeline_priorities()` | Lazy import `backend.decision.ranking.rank_deals(contexts, diagnostics)` → hasil Ical tervalidasi. Exact missing module/function atau explicit engine NotImplementedError: 501 PRIORITIES_NOT_IMPLEMENTED. Nested dependency, engine failure atau invalid output: 503 PRIORITIES_UNAVAILABLE. |
| `backend/api/diagnostics.py:validate_deal_diagnostic` / `validate_pipeline_diagnostic` | Report + konteks → dict asli, tanpa response-model truncation. Validasi required fields, canonical metrics/scope, kelengkapan lima deal, statistik dan registry sumber. Row direct di luar graph di-resolve hanya yang diminta melalui by_id, bukan scan 226300 usage harian setiap GET. |
| `backend/api/provenance.py:validate_json`, `collect_evidence_ids`, `validate_evidence_registry` | JSON strict, seluruh nested evidence_ids, schema/core sumber kanonis, duplicate/missing/corrupt records; tambahan provenance dipertahankan. |
| `backend/api/phase3_models.py:PrioritiesResponse` dan model nested | Schema ranking strict, rank integer bukan bool/float, factor finite number/string/null, readiness/kind/rules literals, required methodology/recommendation/path fields. Extra fields diizinkan dan tidak dibuang. |
| `backend/api/priorities.py:validate_priorities` | Output Ical + konteks/diagnostic asli → dict utuh. Exact set deal/account, ordered contiguous rank 1..N, snapshot v1/rules, union sumber tanpa conflicting content, recommendation/precedent identity, seluruh ID item/envelope/metodologi, serta original directed graph paths. |
| `tests/bima/test_diagnostics_api.py` | 12 tes diagnostic/source/null/scope/statistical/provenance dan korupsi sintetis. |
| `tests/bima/test_priorities_api.py` | 8 tes kontrak ranking sintetis, pairing ID, rank/schema/source/path dan envelope provenance. Fixture `mock_priorities` diberi label SYNTHETIC/MOCK dan tidak masuk kode production. |
| `tests/bima/test_phase3_routes.py` | 11 tes HTTP TestClient: 404, clock external/internal, complete pipeline/P05, 501 vs dependency503, valid mock, invalid mock, input mutation dan redaksi error/log. |

Engine menerima salinan input terisolasi; validasi memakai graph/konteks asli sehingga engine tidak dapat menyisipkan edge lalu mengesahkannya sendiri. Error/log hanya memuat kategori operasi dan kelas exception, bukan exception text/traceback/provider payload/secret.

## Kontrak dan dependency
Kontrak v1 lama dan fase 3 milik Main diikuti tanpa mengedit `backend/contracts.py` atau `docs/coordination/`. Tidak ada database, persistent state atau dependency baru. Menggunakan FastAPI/Pydantic/NetworkX yang sudah ada dan stdlib.

| Endpoint baru | Respons |
| --- | --- |
| GET `/api/deals/{deal_id}/initial-analysis` | 200 `{schema_version:'v1', ...analyze_deal_initial(context)}`; unknown/account ID/closed historical deal 404 DEAL_NOT_FOUND. |
| GET `/api/pipeline/initial-analysis` | 200 `{schema_version:'v1', ...analyze_pipeline_initial()}`; lima reports, statistik not_assessed dan method/threshold/outlier_deal_ids null. Nested reports tidak diberi field tambahan buatan route. |
| GET `/api/pipeline/priorities` | 200 hanya hasil ranking Ical lengkap/valid; 501 PRIORITIES_NOT_IMPLEMENTED bila belum ada; 503 PRIORITIES_UNAVAILABLE bila gagal/invalid/incomplete. Saat ini hasil production yang diamati adalah 501. |

Error `{detail:{code,message}}`. Diagnostic service/source corruption menggunakan 503 DIAGNOSTICS_UNAVAILABLE; sahnya data gap tetap 200. Bima menvalidasi schema/readiness literal, bukan menentukan readiness/ranking bisnis sendiri. Source registry output ranking harus mencakup item/factors/recommendation/paths dan tambahan provenance. Directed path wajib sesuai node/edge asli, edge sources tercakup; reverse/shortcut/injection ditolak.

Input priorities dipasangkan per deal_id. Shared source ID dengan isi berbeda ditolak, tidak overwrite diam-diam. GET baru tidak memanggil Jev; ranking Ical harus rules sesuai kontrak. API keys tidak dicetak/disimpan. Tidak ada hasil ranking, confidence, approval atau probabilitas closing buatan Bima.

## Cara menjalankan
Dari root dengan dependency repo terpasang:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8767
curl http://127.0.0.1:8767/api/deals/DL-002/initial-analysis
curl http://127.0.0.1:8767/api/pipeline/initial-analysis
curl http://127.0.0.1:8767/api/pipeline/priorities
python -m unittest discover -s tests
python scripts/check_handoff.py --all
```

Proyeksi respons nyata DL-002: schema_version v1; deal/account DL-002/P02; age 68 hari, stage age 45; customer count 3/last_date 2026-09-05; internal count 1/last_date 2026-09-28. I0322 adalah follow-up outbound, bukan buyer reply. I0348 adalah satu permintaan diskon 20%, bukan approval; focus_log_evidence_ids kosong dengan filter/account/deal/snapshot dan inspected count tersimpan.

Pipeline tetap membedakan P01 procurement inference K017, P02 harga/approval, P03 C03/C09/C17/C27 referensi FEAT-05 terbaru, P04 C06 overlap bukan acquaintance, P05 zero/null/data gap. Kandidat bukan suitability/willingness/consent. Snapshot/metrics/evidence sama dengan produsen BIMA-02; tidak menetapkan deal paling lama sebagai outlier.

## Pengujian aktual
Eksekusi 2026-10-09 WIB pada checkout BIMA-03:

1. Integration run awal `python -m unittest discover -s tests -v`: **129 tes lulus, 23.804 s**.
2. Review menemukan ID tambahan pada envelope/metodologi ranking belum diperiksa. Regression `test_envelope_and_methodology_sources_must_also_be_registered` sebelum fix: **1 tes gagal, 2 subcase** (`ValueError not raised`). Root cause: traversal hanya per item. Fix mencakup union registry dan traversal seluruh envelope.
3. Suite final `python -m unittest discover -s tests`: **130 tes lulus, 23.596 s**; 96 Bima (31 baru BIMA-03), 24 Ical, 10 bootstrap/handoff. Tidak ada perubahan kode setelah run final ini.
4. **HTTP nyata** server uvicorn port 8767, stdlib urllib (bukan TestClient), selesai 18:31:01 WIB: diagnostic DL-001–DL-005 dan pipeline 200, seluruh payload sama dengan produsen kanonis + top-level schema_version; setiap direct excerpt sama dengan row raw, source_file/source_id tepat. Unknown DL-999, account P02 dan closed DL-006 404. Priorities tanpa engine Ical nyata 501. Health/list 200, list tetap lima rank null; detail kelima deal 200/DealContext valid dan POST analyze kelima deal 200/Recommendation valid mode rules.
5. **HTTP socket nyata dengan engine SYNTHETIC/MOCK**, server in-memory terpisah port 8768, selesai 18:32:20 WIB: mock lengkap 200, lima ranks/readiness/schema, seluruh records cocok union canon dan seluruh paths cocok directed edges asli. Incomplete/source fabricated/path reversed/nonfinite/engine exception/nested missing dependency →503 PRIORITIES_UNAVAILABLE. Diagnostic corruption →503 DIAGNOSTICS_UNAVAILABLE. Secret placeholder tidak muncul pada respons; unit test juga memeriksa log redaction.
6. Smoke HTTP regression final pada **18:35:22 WIB**: unresolved source pada methodology →503; source terdaftar pada extra methodology provenance →200 dan field retained. Tetap SYNTHETIC/MOCK, bukan ranking bisnis nyata.
7. `python scripts/check_handoff.py --all` lulus: “Handoff valid. Main tetap memverifikasi kebenaran laporan dan integrasi.” Validasi ownership diff committed dicatat setelah commit berhasil. Server production smoke port 8767 juga sudah dihentikan.

### Latency aktual
Client wall-clock mencakup HTTP/serialisasi. Cold adalah request pertama diagnostic pada server baru; warm median adalah tiga request berurutan. Ini pengukuran lokal, bukan SLA/benchmark produksi. Pipeline cold dan ranking bisnis nyata belum diukur.

| Endpoint/mode | Cold ms | Warm ms | Sampel warm |
| --- | ---: | ---: | ---: |
| DL-002 initial-analysis nyata 200 | 2680.974 | 114.158 | 3, median |
| Pipeline initial-analysis nyata 200 | tidak diukur | 537.737 | 3, median |
| Priorities nyata tanpa engine 501 | tidak diukur | 1.746 | 3, median |
| Priorities SYNTHETIC/MOCK 200 | tidak diukur | 612.859 | 1, bukan latency ranking bisnis |

Script smoke/server mock tidak disimpan dalam repo; mock servers dihentikan setelah pemeriksaan. Tidak menjalankan frontend/browser, Jev live atau mengevaluasi kualitas metode ranking. HTTP production ranking 200 **belum diuji** karena fungsi Ical belum merged/tersedia.

## Fixture dan keterbatasan
Diagnostic dan legacy HTTP memakai dataset/konteks kanonis nyata (dataset sintetis proyek), bukan payload statis. Corruption cases dan seluruh ranking sukses di tes/smoke adalah **SYNTHETIC/MOCK**. Mock memakai sumber/graph nyata dan rekomendasi rules nyata, tetapi urutan reverse-input sengaja arbitrer, bukan peringkat sales atau penilaian kualitas ranking.

Validation menolak finite/schema/source/path errors dan incomplete output, tidak menilai formula/bobot bisnis Ical. Field tambahan preserved tanpa response-model dump. Copy input menambah biaya adapter; hanya mock latency tersedia, belum profil/benchmark ranking Ical. Produsen diagnostic lexical/fixed snapshot; unknown business facts tetap membutuhkan manusia. Kelayakan/izin referensi dan procurement inference tidak otomatis berubah menjadi confirmed karena HTTP 200.

## Blocker
Tidak ada blocker untuk diagnostic API dan adapter validation. **Dependency integrasi nyata:** `backend.decision.ranking.rank_deals` milik ICAL-03 belum tersedia di origin/main `712acf9` pada refresh kedua. Respons honest 501 sudah dibuktikan. Kontrak mengizinkan PR Bima diajukan sebelum Ical; tidak menyalin/cherry-pick kode yang belum merged atau membuat ranking sendiri.

Jev live/UI BOY-04/kualitas ranking bukan klaim verifikasi BIMA-03. Main perlu merge/review Ical dan melakukan integrasi ranking nyata; sesudah itu Bima sync main, restart dan smoke priorities/source/paths tanpa mock.

## Tugas berikutnya
1. Bima: commit/push dan PR BIMA-03 baru, tambah receipt SHA/URL; tanggapi review Main.
2. Main: review endpoints/validation/provenance/HTTP evidence dan dependency. Hanya Main menetapkan VERIFIED/MERGED; PR #10 tetap selesai.
3. Setelah ICAL-03 merged: sync origin/main tanpa cherry-pick, restart server; smoke priorities 200 nyata P01–P05, rank/readiness/union sources/original paths dan latency. Jangan menyebut mock sebagai integrasi ini.
4. Main/Boy: integrasikan diagnostic/priorities setelah review, join per deal_id; status daftar v1 tidak diubah oleh pekerjaan ini.
5. Tim: konfirmasi authority/approval/reference criteria/consent/discovery yang masih unknown. Scope final tetap P01–P05, bukan hanya P02.

## Update WIB
2026-10-09 18:35:22 WIB (waktu aktual smoke regression BIMA-03, UTC+07:00). READY_FOR_REVIEW; bukan approval Main atau ranking bisnis nyata.
