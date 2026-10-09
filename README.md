# DealCompass

Context Graph untuk Deal Acceleration, Hackathon PENS 2026.
Tim: **Boy (@feboyfierlyan), Bima (@bimadji), Ical (@IXALS)**.

## Mulai di sini

1. Baca [checklist Main](docs/coordination/MAIN.md).
2. Baca [kontrak API v1](docs/coordination/API_CONTRACT.md).
3. Buka prompt peran: [Boy](docs/prompts/BOY.md), [Bima](docs/prompts/BIMA.md), [Ical](docs/prompts/ICAL.md).
4. Ikuti [cara kontribusi](CONTRIBUTING.md); setiap PR wajib catatan `.md`.

## Status saat ini

Analisis rules P01–P05, context graph, ranking, diagnostic dan UI sudah merged/verified.
Review BIMA-04 #23:164/164 backend, setup bersih dan smoke15/15 cold/warm serta
restart lulus. Review BOY-04 #22:52/52 frontend, build dan sampling browser lulus.
Paket ICAL-04 #26:174/174tes, decision34/35 (E15 diketahui),ranking15/15; baseline
CRM tahap→nilai menghasilkan urutan sama. [Brief mentor](evaluation/MENTOR_BRIEF.md)
dan [klaim demo](evaluation/DEMO_CLAIMS.md) tersedia. Jev live, rehearsal tim dan
submission belum terverifikasi.
[Runbook demo](backend/api/DEMO_RUNBOOK.md) · [Fenomena data](backend/graph/DATA_FINDINGS.md).

Pantau [progres berbobot](docs/coordination/TEAM_PROGRESS.md) dan [checklist Main](docs/coordination/MAIN.md).
Tugas paralel: [Boy04](docs/prompts/BOY-04.md), [Bima04](docs/prompts/BIMA-04.md),
[Ical04](docs/prompts/ICAL-04.md). Penugasan tidak berarti pekerjaan sudah diverifikasi.
P02 adalah contoh integrasi, produk tetap mencakup P01–P05.

## Jalankan

Prasyarat: Python 3.11+ dan Node 22.12+ (atau Node 24 LTS).

```bash
git clone https://github.com/feboyfierlyan/dealcompass.git
cd dealcompass
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal kedua:

```bash
cd frontend
npm ci
npm run dev
```

Buka http://localhost:5173. Dokumentasi API: http://127.0.0.1:8000/docs.
Frontend memakai proxy `/api` Vite. `.env.example` berisi nama konfigurasi;
adapter Jev membaca secret dari lingkungan backend; gunakan DEALCOMPASS_ENGINE_MODE=rules
untuk demo rules tanpa key. Jangan memasukkan secret ke frontend atau repo.

## Verifikasi

```bash
python -m unittest discover -s tests -v
python scripts/check_handoff.py --all
npm --prefix frontend run build
```

Pemeriksaan PR menambahkan validasi catatan handoff dan kepemilikan file.
Hasil build bukan bukti graph, Jev, atau analisis bisnis sudah selesai.

## Sumber

- `dataset_kasirnusa/`: sumber sintetis asli; jangan diedit.
- `Studi Kasus Hackathon_PESERTA.pdf`: brief dan kriteria lomba.
- `1.pdf`: cuplikan dashboard sumber.
- `output/pdf/playbook-deal-acceleration-boy-bima-ical.pdf`: panduan awal.

Snapshot bisnis 1 Oktober 2026; deadline tim 10 Oktober 2026 09.00 WIB.
Nilai deal adalah potensi tahunan, bukan pendapatan yang sudah diperoleh.

