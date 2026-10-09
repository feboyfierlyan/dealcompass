# DealCompass

Context Graph untuk Deal Acceleration, Hackathon PENS 2026.
Tim: **Boy (@feboyfierlyan), Bima (@bimadji), Ical (@IXALS)**.

## Mulai di sini

1. Baca [checklist Main](docs/coordination/MAIN.md).
2. Baca [kontrak API v1](docs/coordination/API_CONTRACT.md).
3. Buka prompt peran: [Boy](docs/prompts/BOY.md), [Bima](docs/prompts/BIMA.md), [Ical](docs/prompts/ICAL.md).
4. Ikuti [cara kontribusi](CONTRIBUTING.md); setiap PR wajib catatan `.md`.

## Status awal

Fondasi tersedia: dataset, daftar lima deal dari CSV, endpoint health,
frontend React, kontrak, tugas, catatan handoff, serta pemeriksaan CI.
Graph detail dan analisis **belum diimplementasikan**: endpoint-nya memberi 501.
Tidak ada Jev live, ranking, atau rekomendasi yang diklaim sudah berjalan.
P02 adalah uji integrasi pertama; produk final wajib **P01-P05**.

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
adapter Jev berikutnya wajib membaca secret dari lingkungan backend.

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

