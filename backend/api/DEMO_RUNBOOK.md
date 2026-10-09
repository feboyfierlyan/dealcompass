# Backend demo runbook — DealCompass

Scope P01–P05; snapshot bisnis **2026-10-01**, bukan tanggal laptop. Gunakan mode **rules** tanpa key Jev. Ini panduan lokal, bukan deployment/submission atau bukti UI final. R8 traversal graph diperbaiki **Ical**, diverifikasi Main pada PR #16; jangan mengembalikan validator lama.

## 1. Setup checkout dan environment bersih

Dari root checkout milik sendiri, simpan/commit pekerjaan lokal sebelum menyinkronkan branch. Jangan reset/force-push atau berpindah branch pada checkout anggota lain. Prasyarat Python **3.11+**, akses repo private serta akses installer dependency pada setup pertama.

Backend memakai `requirements.txt` (FastAPI/Pydantic/uvicorn/httpx pinned; NetworkX range); **belum ada lockfile backend**. Jangan membuat pin baru saat demo. Catat versi runtime hasil instalasi. Lockfile frontend `frontend/package-lock.json` milik Boy/Main; bila menjalankan UI ikuti README (`npm ci`), jangan mengubah dependency.

PowerShell Windows, tanpa activation script/ExecutionPolicy bypass:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
$env:DEALCOMPASS_ENGINE_MODE = 'rules'
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

POSIX, dari root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
export DEALCOMPASS_ENGINE_MODE=rules
export PYTHONUTF8=1
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Server foreground, **tanpa --reload** agar lifecycle satu proses jelas. Simpan PID startup dari log uvicorn dan port yang dipilih. Jangan menampilkan env lengkap atau key; mode rules tidak membutuhkan credential. Ulangi env mode pada setiap terminal server baru. Jika port 8000 dipakai proses lain, koordinasikan atau pilih port sendiri; jangan menghentikannya. Proxy UI default mengikuti konfigurasi Boy/README—backend di port lain tidak otomatis mengubah proxy.

## 2. Health dan pemeriksaan otomatis

Terminal kedua dari root, interpreter venv yang sama:

```powershell
curl.exe http://127.0.0.1:8000/health
.\.venv\Scripts\python.exe -m backend.api.smoke_demo --base-url http://127.0.0.1:8000 --timeout 30
$LASTEXITCODE
```

POSIX: `.venv/bin/python -m backend.api.smoke_demo --base-url http://127.0.0.1:8000 --timeout 30`, lalu `echo $?`.

Health wajib status ok/v1/snapshot. Checker melakukan GET asli: health → daftar lima deal → detail + diagnostic kelima deal → pipeline diagnostic → priorities → diagnostic DL-999 (404 yang diharapkan). Ia memeriksa kelengkapan/akun/snapshot/rank, source registry dan graph/path terhadap produsen kanonis checkout lokal, P02 pending VP Sales/I0348 serta P05 discovery/insufficient_evidence. Traversal boleh melalui kedua arah **edge asli**, bukan membuat atau mengganti edge.

**Exit 0 hanya bila semua pemeriksaan lulus**; transport/JSON/HTTP501/503/invalid payload menghasilkan nonzero. Output PASS/FAIL dan durasi aktual, bukan payload/exception rahasia. Checker GET-only, tidak mengklik analyze atau memanggil Jev/rank lokal. Jalankan dari checkout/dataset yang sama dengan server; beda versi/sumber memang harus dianggap gagal.

Urutan manual untuk mentor: `/api/deals`, `/api/deals/DL-002`, `/api/deals/DL-002/initial-analysis`, `/api/pipeline/initial-analysis`, `/api/pipeline/priorities`, lalu ganti DL-001/003/004/005. List/detail lama masih rank null/not_analyzed; priorities sumber rank/readiness. HTTP200/ready tidak berarti approval atau izin referensi. POST analyze opsional **hanya pada server rules yang operator sendiri jalankan dan ketahui**; checker tidak melakukan POST otomatis.

## 3. Stop → cek mati → restart → cek ulang

1. Catat hasil smoke pertama dan PID server sendiri. Cold = invokasi smoke pertama pada proses server baru; warm = invokasi berikutnya pada PID yang sama. Keduanya tetap membaca HTTP, bukan memakai hasil smoke lama.
2. **Ctrl+C pada terminal server sendiri**, tunggu shutdown/exited. Jangan `taskkill /IM python.exe`, `pkill python`, atau membunuh pemilik port yang belum diketahui.
3. Jalankan checker sekali ketika server sudah mati: harus exit nonzero. Jika masih sukses, ada proses lain/auto-reloader; identifikasi sebelum mengklaim restart.
4. Start lagi dengan command setup/start dan env rules yang sama, tanpa --reload. Catat PID baru, **harus berbeda** dari proses pertama.
5. Jalankan smoke lagi: seluruh endpoint harus lulus dari cache server baru. Jalankan satu warm smoke tambahan dan catat durasi. Bandingkan validitas sumber/gates/status, bukan mengharapkan waktu identik.
6. Setelah rehearsal, stop hanya proses yang dimulai sendiri. Bukti BIMA-04 aktual (PID, commit/runtime, cold/warm, exit mati/restart) dicatat di `docs/handoffs/BIMA.md`, bukan dianggap otomatis dari instruksi ini.

Bila perlu identifikasi listener: PowerShell `Get-NetTCPConnection -LocalPort 8000 -State Listen` dan `Get-Process -Id <OwningProcess>`; POSIX `lsof -nP -iTCP:8000 -sTCP:LISTEN`. **Hanya setelah identitas milik sendiri terkonfirmasi**, gunakan Ctrl+C atau terminasi PID spesifik, bukan nama proses global.

## 4. Pemulihan gangguan

| Gejala | Tindakan aman dan bukti sesudahnya |
| --- | --- |
| Connection refused / timeout | Pastikan terminal server hidup, host/port benar dan root checkout. Health dulu, lalu smoke penuh. Timeout bukan bukti sukses; cold ingest dapat lebih lambat dari warm. Jangan menutupi kegagalan dengan exit0. |
| Address already in use | Identifikasi owner port. Pilih port bebas untuk server sendiri + ubah base-url checker; koordinasikan proxy UI jika diperlukan. Jangan bunuh proses anggota lain. |
| Module/dependency tidak ditemukan | Gunakan interpreter venv yang sama, jalankan `-m pip install -r requirements.txt` dan `-m pip check`, start dari root. Jangan memasang dependency baru secara ad hoc. |
| Priorities 501 | Checkout lama/fungsi ranking tidak tersedia. Sinkronkan main sesuai prosedur branch/PR, pastikan engine Ical merged, restart. **Tidak** mengganti ranking dengan mock/dummy untuk demo. |
| Priorities/diagnostic 503 atau source/path invalid | Catat endpoint/status/commit dan log server yang aman. Jalankan suite backend, laporkan reproduksi ke pemilik/Main. Jangan melewati validator, mengubah graph/mode ranking atau menghapus approval agar 200. |
| 404 saat memakai P02 atau historical deal | API memakai DL-002, bukan account_id P02. DL-999 memang harus 404; historical DL-006 bukan prospek. |
| Health hidup tetapi data berbeda/checker gagal | Periksa versi checkout/server, snapshot dan dataset kanonis yang sama. Restart setelah perubahan kode/data fixture; jangan edit dataset asli untuk membuat checker lulus. |
| Gagal baca/serialisasi JSON / NaN | Perlakukan sebagai gagal. Pertahankan pesan aman; jangan cetak raw response/credential. Reproduksi dengan suite dan eskalasi Main. |
| POST terasa lambat/masuk Jev | Stop server sendiri, set rules eksplisit, restart; tidak perlu key. Jangan menjalankan Jev otomatis sebagai cara memulihkan demo core. |
| Backend lulus tetapi UI belum benar | Jalankan pemeriksaan frontend/proxy bersama Boy. Backend smoke tidak membuktikan browser/mobile atau end-to-end UI final. |

Setelah pemulihan, wajib health + smoke penuh, bukan hanya satu endpoint. Pemeriksaan backend: `python -m unittest discover -s tests`; handoff: `python scripts/check_handoff.py --all`. Simpan hasil aktual di handoff. Jangan deploy/merge/submission dari runbook ini.

## 5. Jawaban mentor dan batas

Buka [`../graph/DATA_FINDINGS.md`](../graph/DATA_FINDINGS.md): “fenomena → bukti → dampak tindakan” seluruh P01–P05, dengan missing dan inference eksplisit. API diagnostic menyimpan query scope dan ID asli; priorities adalah heuristik urutan perhatian sales, bukan probabilitas closing. Deal paling lama bukan outlier tanpa cohort/SLA/metode statistik. Referensi/overlap bukan consent atau kenalan terkonfirmasi.
