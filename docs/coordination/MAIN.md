# Main — pusat koordinasi DealCompass

Pemilik: Boy + AI pada chat koordinasi. Tanggal: 9 Oktober 2026, WIB.
Deadline: 10 Oktober 2026 09.00 WIB. CP2 20.00-22.00, CP3 08.00-09.00.

## Status produk

PR Boy #14, Ical #15, dan API #16 sudah MERGED. R9 dan R8 VERIFIED; revisi API
R8 dikerjakan Ical atas penugasan pengguna, implementasi awal oleh Bima.
Main 8581de8 menyediakan analisis rules, ranking dan diagnostic API nyata P01-P05.
Review final R8: 144/144 backend, 34/34 frontend, build/handoff/CI lulus.
Priorities dan seluruh diagnostic asli200; unknown deal404. API siap dipakai UI.
UI ranking/diagnostic belum diimplementasikan: tugas BOY-04 tersedia.
[Review R8](../reviews/2026-10-09-ical-r8.md). Jev live belum diuji.
Tidak ada komunikasi otomatis antar-chat AI.

## Progres kesiapan tim

Baseline mentor 9 Oktober19:36WIB: **tim75/100; Boy70/100, Bima90/100, Ical85/100**.
Bukan rubric panitia atau peluang menang. Bobot, bukti, batas dan target berikutnya
ada di [TEAM_PROGRESS.md](TEAM_PROGRESS.md). Angka anggota bukan rata-rata total.
BOY-04, BIMA-04 dan ICAL-04 bisa berjalan paralel; semua baru TODO saat penugasan.

## Checklist tugas

| ID | Pemilik | Status | Hasil / acceptance |
|---|---|---|---|
| MAIN-00 | Main | VERIFIED | Repo, dataset, kontrak, CI, branch, undangan dan task issues |
| BOY-01/02 | Boy | MERGED #5; R4 VERIFIED | UI lima deal, detail, graph klik, panel bukti, uji UI dan handoff |
| BIMA-01 | Bima | MERGED #6 | Ingest seluruh sumber, graph temporal dan konteks P02, API dan handoff |
| ICAL-01/02 | Ical | MERGED #7; R6/R7 VERIFIED | Analisis rules P01-P05, policy gate, adapter Jev mock/replay dan evaluasi |
| BIMA-02 | Bima | MERGED #10 | Metrik, diagnosis bersumber dan verifikasi identitas/referensi internal P01-P05 |
| BOY-03 | Boy | MERGED #14; R9 VERIFIED | 34/34 tes frontend, build dan CI lulus; sumber ke graph dan status sesi |
| MAIN-01 | Main | VERIFIED untuk smoke rules | HTTP dan browser P01-P05 menghasilkan analisis; persiapan demo final lanjut |
| TEAM-02 | Semua | IN_PROGRESS | Engine dan API ranking/diagnostic merged; UI BOY-04 belum selesai |
| ICAL-03 | Ical | MERGED #15 | Ranking rules, sumber/path dan referensi terbaru; evaluasi 15/15 |
| BIMA-03 / R8 | Bima; revisi oleh Ical | MERGED #16; R8 VERIFIED | Priorities/diagnostic asli200; 144 backend dan 34 frontend lulus |
| BOY-04 | Boy | TODO; prompt siap | UI ranking, diagnostic/anomali dan jalur bukti dari API fase3 |
| BIMA-04 | Bima | TODO; prompt siap | Runbook/smoke/restart demo dan ringkasan fenomena data |
| ICAL-04 | Ical | TODO; prompt siap | Baseline/pembuktian metode/bahan mentor; Jev live conditional terpisah |
| MAIN-02 | Main | TODO | Integrasi UI final, rehearsal, kecocokan brief dan submission |

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
| analyze_deal | Ical | MERGED #7 | R1-R3/R5/R6/R7 lulus; evaluasi inti 34/34 |
| GET detail / POST analyze | Bima + Ical | 200 untuk P01-P05; mode rules teruji | Evidence IDs resolvable; HTTP dan browser sukses |
| analyze_deal_initial / analyze_pipeline_initial | Bima | MERGED #10/#16 | Produsen sumber teruji; diagnostic API asli200 seluruh deal/pipeline |
| Dashboard, AnalysisReport, analysisSession dan graphView | Boy | MERGED #14; R9 VERIFIED | 34/34 frontend; lima GET/POST/render nyata; uji browser historis terpisah |
| rank_deals | Ical | MERGED #15 | P04/P01/P02/P03/P05; heuristik, bukan probabilitas closing |
| GET initial-analysis / priorities | Bima; revisi Ical | MERGED #16 | Asli200; source/path valid, pending P02 dan discovery P05 terjaga |
| scripts/check_handoff.py | Main | Implementasi awal | tests/test_handoff.py |

## Coverage wajib sebelum produk final selesai

`[ ]` belum diverifikasi, `[x]` sudah diverifikasi dengan bukti pada PR/commit.

| Deal | Konteks | Hambatan/unknowns | Tindakan | Graph/bukti | Preseden diperiksa | UI detail | Ranking | Uji |
|---|---|---|---|---|---|---|---|---|
| P01 | [x] | [ ] | [ ] | [x] | [ ] | [x] | [ ] | [ ] |
| P02 | [x] | [ ] | [ ] | [x] | [ ] | [x] | [ ] | [ ] |
| P03 | [x] | [ ] | [ ] | [x] | [ ] | [x] | [ ] | [ ] |
| P04 | [x] | [ ] | [ ] | [x] | [ ] | [x] | [ ] | [ ] |
| P05 | [x] | [ ] | [ ] | [x] | [ ] | [x] | [ ] | [ ] |

## Tugas sekarang dan dependency

- Boy: jalankan [BOY-04](../prompts/BOY-04.md) dari main terbaru di branch baru
  boy/priorities-diagnostics dan PR baru. API fase3 sudah siap; jangan buka ulang #14.
- Ical: jalankan [ICAL-04](../prompts/ICAL-04.md) sekarang di branch baru
  ical/evidence-demo-pack: baseline, bukti, jawaban mentor; Jev conditional/timebox.
- Bima: jalankan [BIMA-04](../prompts/BIMA-04.md) sekarang di branch baru
  bima/demo-readiness: runbook, smoke/restart dan fenomena data. Jangan ulang R8.
- Ketiganya paralel; kontrak API/metode dibekukan selama UI diintegrasikan. Uji
  browser end-to-end dan rehearsal final baru menunggu BOY-04 siap.
- Main: review BOY-04 setelah PR tersedia; selanjutnya demo akhir dan submission.
  Status request sesi, status analisis, approval dan ranking harus tetap berbeda.
- Semua: WAJIB handoff .md pada PR sendiri; status maksimal READY_FOR_REVIEW.
  Pengguna meneruskan prompt; tidak ada pesan otomatis antar-chat AI.

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

2026-10-09 17:53 WIB: PR #5 Boy merged 3b8cc87; R4 ditutup. Graph/bukti dan UI detail P01-P05 dicentang berdasarkan review nyata. Centang UI tidak berarti analisis, ranking, atau keseluruhan acceptance bisnis sudah selesai.

2026-10-09 18:05 WIB: #7/#10 merged. R6/R7 ditutup; 99 tes gabungan dan smoke rules P01-P05 lulus. Coverage uji bisnis final tetap terbuka; kolom UI sebelumnya hanya detail/graph, bukan seluruh acceptance BOY-03.

2026-10-09 18:11 WIB: kontrak dan prompt ICAL-03/BIMA-03 tersedia. Status implementasi tetap TODO, bukan VERIFIED. Boy tetap BOY-03; tidak menunggu dua PR baru untuk merapikan analisis nyata yang sudah ada.

2026-10-09 19:02 WIB: #15 merged c7582a6. #14 ditahan R9; #16 ditahan R8. Kontrak traversal diperjelas Main. Bukti gabungan dan prompt revisi ada di review PR14-16.

2026-10-09 19:09 WIB: atas permintaan pengguna, R8 dialihkan ke AI Ical terlebih
dahulu. PR #16 tetap digunakan. Handoff BIMA.md wajib mencatat pelaksana Ical;
status revisi belum diverifikasi. Boy tetap R9 di PR #14. Pengguna meneruskan
prompt ke chat Claude Ical; penugasan tertulis bukan bukti chat itu sudah bekerja.

2026-10-09 19:22 WIB: #14 merged b059bad, R9 VERIFIED. Main mengulang 34/34 frontend dan build pada c6c368e; CI lulus. Komponen UI tidak berubah pada delta R9; smoke browser Boy dilaporkan terpisah. R8 tetap ditangani Ical.

2026-10-09 19:30 WIB: #16 merged 8581de8, R8 VERIFIED. Main mengulang144 backend/34 frontend dan smoke socket API asli200. BOY-04 kini ditugaskan; endpoint siap bukan berarti UI sudah selesai.

2026-10-09 19:36 WIB: baseline kesiapan75/100 ditetapkan beserta bobot terbuka. BIMA-04 dan ICAL-04 ditugaskan paralel dengan BOY-04; penugasan bukan klaim pekerjaan telah dimulai.
