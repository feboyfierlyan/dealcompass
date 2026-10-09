# DealCompass: aturan semua AI

- Scope wajib P01-P05. P02 adalah uji integrasi awal, bukan batas produk.
- Baca `docs/coordination/MAIN.md`, `API_CONTRACT.md`, dan prompt peranmu.
- Main adalah peran integrator Boy + AI pada chat koordinasi, bukan produk AI lain.
- Kerjakan satu branch/checkout per anggota. Jangan berpindah branch bersama.
- Branch: `boy/*`, `bima/*`, `ical/*`; integrator memakai `integrator/*`.
- WAJIB update `docs/handoffs/<PERAN>.md` di setiap PR pekerjaan.
- Gunakan semua heading template; catat fungsi, bukti uji, blocker, dan waktu WIB.
- Status pelaksana maksimal READY_FOR_REVIEW. Main menetapkan VERIFIED/MERGED.
- Hanya Main mengedit `docs/coordination/`, kontrak bersama, CI dan dependency.
- Boy: frontend. Bima: ingestion, graph, API. Ical: decision, Jev, evaluation.
- Jangan ubah dataset asli. Snapshot bisnis 2026-10-01.
- CSV keputusan adalah sumber ingest kanonis; XLSX bukan tambahan record.
- Simpan provenance setiap bukti/edge dan bedakan direct dengan inferred.
- Nilai kurang, API gagal, atau modul belum siap wajib dinyatakan eksplisit.
- Tidak ada ranking, confidence Jev, approval, hasil uji, atau closing rekaan.
- Diskon >10% butuh approval VP Sales dan log. Permintaan bukan approval.
- API key hanya di backend/env, tidak di repo, frontend, laporan, atau log.
- Ikuti kontrak `v1`; perubahan lintas modul diusulkan lewat handoff.
- Jalankan pemeriksaan relevan sebelum PR; sertakan perintah dan hasil aktual.
- ChatGPT/Claude tidak otomatis berkomunikasi; manusia meneruskan tugas/laporan.

