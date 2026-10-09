# Kerja tim dan handoff wajib

## Branch dan tugas

- Boy: `boy/frontend`, area `frontend/`.
- Bima: `bima/data-graph`, area `backend/api/`, `backend/graph/`, `backend/ingestion/`, `backend/main.py`, `tests/bima/`.
- Ical: `ical/decision-jev`, area `backend/decision/`, `backend/integrations/`, `evaluation/`, `tests/ical/`.
- Main: branch `integrator/<tugas>`, kontrak bersama, dependency, CI, checklist dan integrasi.

Branch pertama disiapkan dari fondasi yang sama. Setiap anggota clone sendiri.
Pada mesin bersama gunakan checkout/worktree berbeda, bukan git switch bersamaan.

```bash
git fetch origin
git switch --track origin/bima/data-graph
# Setelah membuat perubahan:
git add backend/graph docs/handoffs/BIMA.md
git commit -m "feat: bangun konteks deal dengan sumber bukti"
git push
```

Sesuaikan branch dan file dengan peran. Buat PR menuju `main`; PR kecil lebih
mudah diperiksa. Setelah perubahan main masuk, sinkronkan sebelum pekerjaan baru.
Selesaikan konflik bersama pemilik file. Jangan force-push branch anggota lain.

## Catatan WAJIB

Setiap PR pekerjaan wajib mengubah `docs/handoffs/<PERAN>.md` milik sendiri.
Main/integrator memakai `docs/handoffs/MAIN.md` dan memperbarui checklist pusat.
Template: `docs/handoffs/TEMPLATE.md`. Isi fakta aktual, bukan rencana yang
ditandai selesai. Handoff mencantumkan commit kode sebelumnya; tidak perlu
mencantumkan hash commit handoff itu sendiri.

PR dengan perubahan lintas kepemilikan diajukan kepada Main. Perubahan kontrak
atau dependency dikerjakan Main pada PR terpisah, kemudian anggota sinkronkan.
Jangan membuat loader, schema, atau aturan diskon duplikat di frontend.

```bash
python scripts/check_handoff.py --base origin/main --head HEAD --branch bima/data-graph
```

CI mengecek file handoff berubah, heading wajib, scope file, serta dataset asli
tidak ikut diubah. CI tidak dapat membuktikan isi laporan benar: Main tetap
memeriksa kode, bukti pengujian, dan integrasi. Status proteksi merge aktual
dicatat di `docs/coordination/MAIN.md`.

## ChatGPT atau Claude tanpa akses repo langsung

Berikan AGENTS.md, prompt peran, kontrak, dan file yang relevan kepada AI.
Minta isi file lengkap/diff dan catatan handoff. Pemilik manusia menyimpan,
menjalankan pemeriksaan, commit, push, dan membuka PR. Jangan mengklaim AI
sudah mengubah repo jika hanya memberikan teks di chat.

