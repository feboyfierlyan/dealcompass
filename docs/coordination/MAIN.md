# Main — pusat koordinasi DealCompass

Pemilik: Boy + AI pada chat koordinasi. Tanggal: 9 Oktober 2026, WIB.
Deadline: 10 Oktober 2026 09.00 WIB. CP2 20.00-22.00, CP3 08.00-09.00.

## Status produk

PR #6 Bima sudah MERGED (73fb045): ingestion dan konteks P01-P05 tersedia.
PR #5 Boy dan #7 Ical sudah direview pada worktree gabungan, tetapi perlu
perbaikan sebelum merge. Review awal: 42 tes gabungan dan 12 tes frontend lulus. Review ulang Ical
7919550: 48 tes lulus, evaluasi 29/30 (inti 29/29), R1-R3/R5 diperbaiki.
PR #7 belum merged: dua celah approval R6/R7 terkonfirmasi pada kasus sintetis.
[Review ulang Ical](../reviews/2026-10-09-pr7-r2.md). Graph Boy R4 masih menunggu review revisi.
[Review dan tugas koreksi](../reviews/2026-10-09-pr5-7.md).
Jev live, ranking, dan aplikasi end-to-end yang benar belum diverifikasi.
Tidak ada komunikasi otomatis antar-chat AI.

## Checklist tugas

| ID | Pemilik | Status | Hasil / acceptance |
|---|---|---|---|
| MAIN-00 | Main | VERIFIED | Repo, dataset, kontrak, CI, branch, undangan dan task issues |
| BOY-01 | Boy | READY_FOR_REVIEW; revisi R4 | UI lima deal, detail, graph klik, panel bukti, uji UI dan handoff |
| BIMA-01 | Bima | MERGED #6 | Ingest seluruh sumber, graph temporal dan konteks P02, API dan handoff |
| ICAL-01 | Ical | READY_FOR_REVIEW; revisi R6/R7 | Analisis P02, policy gate, adapter Jev, evaluasi dan handoff |
| MAIN-01 | Main | IN_PROGRESS; ditemukan blocker | Verifikasi satu alur P02 dari frontend sampai keputusan dan sumber |
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
| build_deal_context | Bima | MERGED; P01-P05 teruji | 17 tes Bima dan review konteks nyata |
| analyze_deal | Ical | PR #7; belum merged | R1-R3/R5 lulus pada 7919550; R6/R7 perlu revisi |
| GET detail / POST analyze | Bima + Ical | Detail 200; analyze main masih 501 | Review gabungan P02 menemukan R1 |
| frontend/src/main.tsx | Boy | PR #5 UI/graph; belum merged | 12 tes frontend; graph nyata perlu R4 |
| scripts/check_handoff.py | Main | Implementasi awal | tests/test_handoff.py |

## Coverage wajib sebelum produk final selesai

`[ ]` belum diverifikasi, `[x]` sudah diverifikasi dengan bukti pada PR/commit.

| Deal | Konteks | Hambatan/unknowns | Tindakan | Graph/bukti | Preseden diperiksa | UI detail | Ranking | Uji |
|---|---|---|---|---|---|---|---|---|
| P01 | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P02 | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P03 | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P04 | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| P05 | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

## Tugas sekarang dan dependency

- Boy / BOY-02: revisi PR #5 untuk graph fokus yang terbaca pada payload nyata P02, expand/filter dan akses sumber lengkap. Uji ulang setelah sinkron main.
- Ical / ICAL-02: R1-R3/R5 sudah diverifikasi pada 7919550. Revisi PR #7 yang sama untuk R6 (approval deal lain pada akun sama) dan R7 (persentase approval kosong/tidak terbaca). Tambahkan regresi dan perbarui evaluasi/handoff. Detail di review ulang PR #7.
- Bima / BIMA-02: pertahankan ingestion yang sudah merged; bantu jalur bukti identitas P01 dan kandidat referensi P03/P04. Siapkan temuan anomali bersumber (umur tahap, kelengkapan interaksi, status request vs approval); jangan menganggap outlier hanya dari lima deal beda tahap. Endpoint/schema baru dibahas dengan Main dahulu.
- Main: kontrak semantik diperjelas di API_CONTRACT.md. Review ulang SHA baru, lalu merge PR yang memenuhi acceptance. Ranking lintas deal dan pemetaan analysis_status tetap tugas bersama berikutnya.
- Semua: fetch dan sinkron origin/main, isi handoff masing-masing, push revisi ke PR yang sama. Main belum mengirim pesan ke chat AI lain; Boy meneruskan instruksi ini.

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


## Review terbaru

2026-10-09 17:10 WIB: PR #6 merged, #5/#7 menunggu perbaikan yang direproduksi di review.
Tanda centang konteks hanya membuktikan struktur/sumber tersedia; kolom tindakan,
UI, ranking dan uji acceptance bisnis tetap belum selesai.

2026-10-09 17:38 WIB: review ulang Ical 7919550 selesai; 48 tes dan 29 kasus inti lulus. R6/R7 menahan merge; dataset asli P02 tetap meminta approval dengan benar. Main tidak menganggap kasus sintetis sebagai anomali dataset.
