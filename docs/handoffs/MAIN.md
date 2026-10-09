# Handoff MAIN

## Task dan status
MAIN-00: IN_PROGRESS. Repo private tersedia; ketiga anggota memiliki akses; fondasi lulus tes lokal.

## Branch dan commit
Bootstrap awal main; commit awal akan menjadi referensi fondasi bersama.

## File dan fungsi
Fondasi FastAPI, list_deals, frontend React, kontrak, checker handoff, aturan AI, workflow dan catatan.

## Kontrak dan dependency
API v1 ditetapkan pada API_CONTRACT.md dan backend/contracts.py. Node/npm serta Python dependencies dicatat dalam manifest.

## Cara menjalankan
Lihat README.md. python3 -m unittest discover -s tests -v; python3 scripts/check_handoff.py --all; npm --prefix frontend run build.

## Pengujian aktual
9 tes unittest lulus; validasi empat handoff lulus; TypeScript dan Vite production build lulus. GitHub Actions menunggu push pertama.

## Fixture dan keterbatasan
Daftar CRM nyata tersedia; detail/analyze 501, rank null. Belum ada graph, rekomendasi, Jev live, atau uji UI browser.

## Blocker
Tidak ada blocker akses: bimadji dan IXALS sudah memiliki write. Proteksi merge belum diverifikasi.

## Tugas berikutnya
Selesaikan verifikasi bootstrap, push, CI, branch dan issue; kemudian BOY-01/BIMA-01/ICAL-01.

## Update WIB
2026-10-09 15:48 WIB
