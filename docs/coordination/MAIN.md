# Main — pusat koordinasi DealCompass

Pemilik: Boy + AI pada chat koordinasi. Tanggal: 9 Oktober 2026, WIB.
Deadline: 10 Oktober 2026 09.00 WIB. CP2 20.00-22.00, CP3 08.00-09.00.

## Status produk

Fondasi lulus 9 tes lokal, build frontend dan GitHub Actions; repo sudah terunggah. Data dan daftar P01-P05 tersedia; graph detail,
rekomendasi, Jev dan ranking final masih tugas berikutnya. P02 bukan scope akhir.
Tidak ada komunikasi otomatis antar-chat AI.

## Checklist tugas

| ID | Pemilik | Status | Hasil / acceptance |
|---|---|---|---|
| MAIN-00 | Main | VERIFIED | Repo, dataset, kontrak, CI, branch, undangan dan task issues |
| BOY-01 | Boy | TODO | UI lima deal, detail, graph klik, panel bukti, uji UI dan handoff |
| BIMA-01 | Bima | TODO | Ingest seluruh sumber, graph temporal dan konteks P02, API dan handoff |
| ICAL-01 | Ical | TODO | Analisis P02, policy gate, adapter Jev, evaluasi dan handoff |
| MAIN-01 | Main | TODO | Verifikasi satu alur P02 dari frontend sampai keputusan dan sumber |
| TEAM-02 | Semua | TODO | Analisis P01-P05 dan ranking lintas deal, bukti terverifikasi |
| MAIN-02 | Main | TODO | Pertanyaan baru, cross-track, fallback, restart, demo dan submission |

Status: TODO / IN_PROGRESS / BLOCKED / READY_FOR_REVIEW / VERIFIED / MERGED.
Centang selesai hanya setelah verifikasi. Jangan otomatis mengubah status
ketika anggota hanya mengatakan selesai.

## Inventaris fungsi / endpoint

| Lokasi / fungsi | Pemilik | Status awal | Verifikasi |
|---|---|---|---|
| backend/ingestion/deals.py:list_deals | Bima | Dasar teruji | tests/test_bootstrap.py |
| GET /health | Bima | Dasar teruji | tests/test_bootstrap.py |
| GET /api/deals | Bima | Implementasi dasar | Lima prospek, total Rp667.800.000, umur stage |
| build_deal_context | Bima | Stub / belum selesai | BIMA-01 |
| analyze_deal | Ical | Stub / belum selesai | ICAL-01 |
| GET detail / POST analyze | Bima + Ical | 501 sampai modul siap | Tes error dan ID tidak dikenal |
| frontend/src/main.tsx | Boy | Daftar CRM awal | Build; detail/graph belum ada |
| scripts/check_handoff.py | Main | Implementasi awal | tests/test_handoff.py |

## Coverage wajib sebelum produk final selesai

`[ ]` belum diverifikasi, `[x]` sudah diverifikasi dengan bukti pada PR/commit.

| Deal | Konteks | Hambatan/unknowns | Tindakan | Graph/bukti | Preseden diperiksa | UI detail | Ranking | Uji |
|---|---|---|---|---|---|---|---|---|
| P01 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P02 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P03 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P04 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P05 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

## Tugas sekarang dan dependency

- Boy: issue BOY-01, `boy/frontend`; GET /api/deals sudah dasar; detail menunggu Bima.
- Bima: issue BIMA-01, `bima/data-graph`; kontrak v1 siap; implementasikan konteks dahulu.
- Ical: issue ICAL-01, `ical/decision-jev`; gunakan kontrak dan bukti dataset untuk fixture
  berlabel sementara; tes lagi dengan konteks graph Bima saat tersedia.
- Target integrasi awal sekitar 90 menit setelah anggota mulai. Sebelum CP2,
  kelima deal tampil dengan analisis awal dan status bukti yang jujur.
- Selesai P02: Main menugaskan cakupan lainnya, bukan menyatakan aplikasi selesai.

## Integrasi dan akses

- Repo private: https://github.com/feboyfierlyan/dealcompass
- Bima @bimadji dan Ical @IXALS sudah terverifikasi sebagai collaborator dengan akses write.
- Issue [Boy #1](https://github.com/feboyfierlyan/dealcompass/issues/1), [Bima #2](https://github.com/feboyfierlyan/dealcompass/issues/2), [Ical #3](https://github.com/feboyfierlyan/dealcompass/issues/3) sudah ditetapkan ke akun masing-masing.
- Branch `boy/frontend`, `bima/data-graph`, `ical/decision-jev` sudah tersedia dari commit fondasi `76eda95`. Sinkronkan main sebelum mulai.
- Proteksi main aktif: PR wajib, status `verify` wajib dan harus mutakhir; berlaku juga untuk admin; force push dan penghapusan main dilarang.
- GitHub tidak mewajibkan jumlah approval reviewer; review Main tetap prosedur tim. CI memeriksa struktur laporan, bukan kebenaran isinya.
- [CI fondasi lulus](https://github.com/feboyfierlyan/dealcompass/actions/runs/37907339161): backend, handoff dan frontend build.

## Bukti review / merge

Bootstrap `76eda95` terunggah; 9 tes dan build lulus secara lokal dan CI.
PR penyelesaian bootstrap mencatat bukti akses, proteksi dan tugas; handoff Main
menjadi contoh pelaporan. Aplikasi lengkap belum selesai: cakupan final di atas tetap terbuka.

