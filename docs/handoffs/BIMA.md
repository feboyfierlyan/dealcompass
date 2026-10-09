# Handoff BIMA

## Task dan status
**BIMA-04: READY_FOR_REVIEW.** Panduan setup/pemulihan, CLI smoke GET-only, bukti proses baru/restart dan ringkasan fenomena P01–P05 selesai. Snapshot **2026-10-01**; Main yang menetapkan VERIFIED/MERGED dan kredit TEAM_PROGRESS.

**Atribusi tetap:** implementasi awal BIMA-03 oleh Bima; **revisi R8 oleh Ical atas penugasan pengguna**, commit `ebc999951e644d0fc4274089869dcaf4b40e4979`, merge #16 `8581de83d880d0ead72f21c9cfff6873fc3ecb7c`. [Review Main R8](../reviews/2026-10-09-ical-r8.md) menetapkan VERIFIED/MERGED dan traversal dua arah edge asli. BIMA-04 tidak mengulang implementasi R8 atau mengubah API/metode ranking. Histori BIMA-01/#6, BIMA-02/#10 dan BIMA-03/#16 tetap selesai; bukti historis tersedia pada PR/review tersebut.

## Branch dan commit
Branch baru **`bima/demo-readiness`** dari `origin/main` **`be628d7`** setelah fetch; checkout awal bersih. Branch lama `bima/diagnostics-api` dan pekerjaan lokal dipertahankan. Prompt BIMA-04 dibaca dari fetched main sebelum branch dibuat, lalu koordinasi/TEAM_PROGRESS/kontrak/review/handoff dibaca di checkout terbaru.

Tes dan lifecycle di bawah dijalankan pada base tersebut + perubahan BIMA-04 yang akan dicommit; tidak ada perubahan kode setelah suite final. SHA kode dan receipt PR ditambahkan sesudah publikasi berhasil. Tidak cherry-pick, force push, deploy atau merge sendiri.

## File dan fungsi
| File/fungsi | Input → output / tanggung jawab |
| --- | --- |
| `backend/api/DEMO_RUNBOOK.md` | Setup bersih Windows/POSIX dari requirements, interpreter/env rules, start/stop/restart proses sendiri, health + urutan endpoint, pemulihan port/dependency/404/501/503/data mismatch dan batas UI. Root README tidak diubah. |
| `backend/api/smoke_demo.py:main(argv=None)` | `--base-url HTTP(S)` + `--timeout` positif ≤60 s (default 15) → CLI exit 0 hanya jika seluruh pemeriksaan lulus; argumen invalid/transport/service/validation gagal nonzero. |
| `smoke_demo.py:run_checks(base_url, timeout, opener=None, output=None)` | 15 GET asli → validasi snapshot/deal/list/detail/diagnostic/pipeline/priorities/unknown404, output ringkas status/durasi. Opener injection hanya untuk tes terisolasi, bukan fallback. Tidak menjalankan rank/recommendation lokal, POST atau Jev. |
| `smoke_demo.py:_detail/_diagnostic/_priorities/_sources` | Payload HTTP dibandingkan produsen/sumber checkout lokal dan validator existing, bukan percaya graph yang mungkin dipalsukan response. Memeriksa source raw/aggregate registry, pipeline vs single, P02 VP Sales pending/I0348 dan P05 discovery/insufficient/null score/business gaps. |
| `backend/graph/DATA_FINDINGS.md` | Ringkasan mentor satu halaman: facts/source IDs, inferred interpretation, missing dan dampak sales seluruh P01–P05; metrics/source scope, consent/approval/data gap/outlier distinctions dan reproduksi dari produsen/API. |
| `tests/bima/test_smoke_demo.py` | 20 tes CLI/transport berlabel sintetis, source/path/list corruption, invalid/incomplete/nonfinite/501/503, freshness, pending approval/discovery, P05 business gaps vs metric errors, unknown404 dan secret redaction. Tidak menilai formula ranking. |

Checker memakai `list_deals`, `build_deal_context`, `get_context_graph`, `validate_deal_diagnostic`, `validate_pipeline_diagnostic` dan `validate_priorities` existing. R8 bidirectional traversal digunakan apa adanya; source/target/relation/evidence edge tidak diganti. Daftar canonical P01–P05 dibaca dari sumber, tidak membuat ranking contoh atau hardcode urutan skor. Format hasil sumber asli tidak diubah.

## Kontrak dan dependency
API v1/fase 3 dan metode ranking **dibekukan**, tidak ada perubahan route/model/wire/dependency/CI/frontend/dataset/coordination. CLI stdlib urllib/argparse/time/json + dependency repo existing untuk validator/produsen.

Instalasi venv baru dari `requirements.txt` **benar-benar dijalankan**, selesai 56.214 s. Backend belum mempunyai lockfile; NetworkX memakai range Main. Runtime aktual: **Windows 11 / win32 build 10.0.26300 x64; Python 3.14.7; FastAPI 0.127.0; Pydantic 2.12.5; uvicorn 0.40.0; httpx 0.28.1; NetworkX 3.7**. `python -m pip check` pada interpreter awal dan venv baru sama-sama lulus (no broken requirements); suite dan lifecycle menggunakan venv baru.

Server sendiri diberi `DEALCOMPASS_ENGINE_MODE=rules`, `PYTHONUTF8=1` dan **TYPESAFE_API_KEY tidak diteruskan** pada env child. Tidak mencetak key/env penuh. URL checker menolak credentials/query/fragment, redirect dianggap gagal. Server target harus satu versi/dataset dengan checkout checker; tidak cocok memang harus nonzero. Timeout per socket/request, bukan SLA/global-budget.

## Cara menjalankan
Lihat [runbook lengkap](../../backend/api/DEMO_RUNBOOK.md). Dari root, terminal server sendiri, env rules eksplisit:

```powershell
$env:DEALCOMPASS_ENGINE_MODE = 'rules'
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Terminal checker, interpreter venv sama:

```powershell
.\.venv\Scripts\python.exe -m backend.api.smoke_demo --base-url http://127.0.0.1:8000 --timeout 30
$LASTEXITCODE
```

POSIX: `DEALCOMPASS_ENGINE_MODE=rules .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`, kemudian `.venv/bin/python -m backend.api.smoke_demo --base-url http://127.0.0.1:8000 --timeout 30`.

Stop Ctrl+C di terminal server sendiri, cek checker gagal saat mati, start baru dan smoke ulang. Tidak membunuh python/port milik orang lain. Runbook menjelaskan port occupied, wrong interpreter, snapshot/source mismatch dan service errors tanpa melewati validator atau memakai dummy. POST analyze hanya opsional pada server rules milik sendiri yang diketahui; checker tidak melakukan POST.

## Pengujian aktual
BIMA-04, 2026-10-09 WIB, venv baru + mode rules; bukan klaim hasil Main/Ical:

1. Setup venv baru dan `pip install -r requirements.txt` berhasil; runtime di atas diamati langsung. Tidak menambah dependency.
2. Run pertama `python -m unittest discover -s tests`: **163 tes, 25 failure subcases, 120.532 s**. Root cause di checker baru: mengharuskan `metrics.unknowns` P05 nonempty, padahal metrik lengkap/valid sehingga array kosong sah; kurangnya discovery ada pada `findings.missing_information`. Producer fresh membuktikan kedua field. Tidak mengubah API untuk menyembunyikan kesalahan checker.
3. Fix memilih data_gap + missing_information, bukan metric error. Tambahan regresi missing business info. Suite final perintah sama pada venv: **164/164 lulus, 127.595 s**, termasuk 20 tes baru BIMA-04. Tidak ada perubahan kode setelah suite final.
4. **CLI/socket nyata tanpa mock**, server uvicorn baru port **8769**, server dan checker masing-masing proses interpreter venv. Seluruh 15 GET lulus pada empat invokasi: health/list, detail + diagnostic all5, pipeline diagnostic, priorities asli200, unknown404. Sumber/graph/rank lengkap, P02 tetap pending VP Sales/I0348, P05 discovery/insufficient_evidence dengan business unknowns dan skor null. Tidak memaksa urutan ranking atau menganggap ready = approval.
5. Server pertama dihentikan lewat handle proses milik sendiri. Checker saat server mati **exit1**, FAIL transport /health, passed0; tidak mengklaim restart hanya dari cache atau health200.
6. Server baru dengan PID uvicorn berbeda, command/env sama: cold dan warm smoke kembali exit0/all15. Startup log membuktikan identitas uvicorn, bukan menyamakan PID launcher Windows venv dengan PID server.
7. Harness awal sempat gagal assertion karena menganggap PID launcher = uvicorn. Investigasi log menemukan launcher33472 → uvicorn25504; health sesudah stop tidak terjangkau. Hanya instrumentation diperbaiki; dua smoke pertama yang sudah lulus tidak diulang klaimnya. Proses kedua launcher22092 → uvicorn34804. Tidak ada produk/API bug yang ditutupi. Kedua server milik sendiri telah dihentikan; tidak ada proses anggota lain dihentikan.

### Bukti restart dan durasi aktual

| Observasi | PID uvicorn | Exit | Durasi checker (s) | Wall subprocess (s) |
| --- | ---: | ---: | ---: | ---: |
| Proses baru, cold | 25504 | 0 | 15.303 | 17.006 |
| PID sama, warm | 25504 | 0 | 8.693 | 10.560 |
| Setelah stop, negative | tidak hidup | 1 | 6.636 | 8.516 |
| Setelah restart, cold | 34804 | 0 | 15.423 | 17.157 |
| PID restart sama, warm | 34804 | 0 | 8.649 | 10.426 |

Cold/warm mengacu pada **cache server**, setiap invokasi CLI tetap proses baru dan memuat sumber lokal untuk validasi. Total checker mencakup validasi canonical/local, bukan murni latency HTTP; wall mencakup startup/import CLI. Health readiness sebelum smoke tidak menghangatkan dataset/graph. Ini observasi lokal satu sampel tiap tahap, bukan benchmark/SLA. Bukti lifecycle selesai **20:14:56 WIB**.

`python scripts/check_handoff.py --all` lulus pada venv dengan PYTHONUTF8=1. Ownership diff dan receipt publication ditambahkan setelah perintah aktual berhasil. UI/browser/mobile/Jev live/submission tidak diuji. Uji transport sintetis tidak disebut bukti HTTP/restart; lifecycle di atas menggunakan API dan ranking Ical asli, bukan mock.

## Fixture dan keterbatasan
Tests CLI memakai response dari produsen nyata tetapi transport/corruption **SYNTHETIC**; tidak membuka socket. Yang membuktikan socket/lifecycle adalah invokasi CLI pada uvicorn proses baru/baru setelah stop, dengan subprocess exit/status/log PID diamati. Checker tidak menghitung ranking lokal; generator fixture tes boleh memanggil engine rules untuk payload test berlabel.

[DATA_FINDINGS](../../backend/graph/DATA_FINDINGS.md) disusun dari produsen tervalidasi dan source rows fresh, bukan ingatan. Pengamatan tambahan nyata: C01 masih menunjuk K017 champion meski employment berakhir 2026-08-15 (rekonsiliasi sumber, bukan mandat); P01 I0343 → kandidat Rina inferred; P02 I0296/I0348 request tanpa focus approval; P03 latest FEAT-05 kandidat bukan consent; P04 I0335 menunda dan overlap K028/K116 bukan kenalan; P05 missing champion/NPS/health bukan nol/loss. Setiap temuan memuat informasi kurang dan dampak pemeriksaan sales. Statistik not_assessed, deal tertua bukan outlier tanpa cohort/SLA.

Runbook/checker ini membuktikan kesiapan backend lokal, bukan kualitas model ranking, prediksi closing, deployment, kredit tim atau UI BOY-04. API/engine tetap read-only/frozen. Caller harus menyamakan checkout/dataset dan memiliki dependency; checker bukan probe health tanpa sumber lokal. Venv sementara untuk pembuktian dibuat di luar repo; script lifecycle throwaway tidak dicommit.

## Blocker
Tidak ada blocker backend untuk BIMA-04. Acceptance browser/end-to-end UI ranking/diagnostic dan rehearsal final menunggu pekerjaan Boy/Main; tidak ditunggu untuk menyelesaikan backend. Jev live bukan bukti yang diklaim dan tidak dipanggil untuk pemulihan core rules. Main tetap review/merge dan memperbarui status/progres, bukan Bima.

## Tugas berikutnya
1. Bima: commit/push dan PR baru BIMA-04, kirim SHA/runbook/perintah smoke; tanggapi review Main dengan handoff setiap perubahan.
2. Main: review source findings/runbook/lifecycle/CLI, hanya Main menetapkan VERIFIED/MERGED dan kredit kesiapan tim.
3. Boy/Main: jalankan browser end-to-end UI BOY-04 dengan backend rules fresh; backend smoke tidak menggantikan acceptance UI.
4. Tim: rehearsal 3–5 menit; gunakan temuan source/interpretation/missing untuk menjawab mentor, bukan menganggap rank/ready sebagai approval/consent atau probabilitas closing.
5. Jangan deploy/merge/membuat key/submission dari pekerjaan ini. Scope akhir P01–P05 dan attribution R8 Ical tetap.

## Update WIB
2026-10-09 **20:23:04 WIB** (waktu aktual pemeriksaan handoff/dependency; restart selesai 20:14:56, UTC+07:00). Status BIMA-04 READY_FOR_REVIEW; tidak menetapkan VERIFIED/MERGED sendiri.
