# Main — pusat koordinasi DealCompass

Pemilik: Boy + AI pada chat koordinasi. Tanggal: 9 Oktober 2026, WIB.
Deadline: 10 Oktober 2026 09.00 WIB. CP2 20.00-22.00, CP3 08.00-09.00.

## Aktivasi Jev live — 10 Oktober 2026 01:10 WIB

Pengguna memberikan key untuk build testing dan mengonfirmasi belum dipakai.
Key hanya berada di `.env` lokal, tidak dicommit. Smoke Jev PASS; P01–P04 live
PASS, P02 UI menampilkan Analisis dengan Jev dan approval tetap wajib. P05 rules,
0 request. SQLite ledger tim: 31 request / 17.840 input token / 1.657 output;
batas 100 juta input, tidak ada pending. Guard transaksi/reservasi/fail-closed aktif.
Semua anggota wajib memakai backend/ledger yang sama, bukan counter per laptop.
Rincian: [panduan Jev](../../backend/integrations/JEV_LIVE.md), handoff Main.
Catatan status di bawah adalah riwayat sebelum aktivasi ini.

## Status produk

PR Boy #14, Ical #15, dan API #16 sudah MERGED. R9 dan R8 VERIFIED; revisi API
R8 dikerjakan Ical atas penugasan pengguna, implementasi awal oleh Bima.
Main 8581de8 menyediakan analisis rules, ranking dan diagnostic API nyata P01-P05.
Review final R8: 144/144 backend, 34/34 frontend, build/handoff/CI lulus.
Priorities dan seluruh diagnostic asli200; unknown deal404. API siap dipakai UI.
UI ranking/diagnostic BOY-04 sudah VERIFIED/MERGED #22 (ea96e23). Main mengulang
52/52 frontend, build, API nyata dan sampling browser; [review BOY-04](../reviews/2026-10-09-boy04.md).
[Review R8](../reviews/2026-10-09-ical-r8.md). Jev live belum diuji.
BIMA-04 VERIFIED/MERGED #23 (2585bb3): 164/164 backend, setup bersih dan
smoke15/15 cold/warm sebelum/sesudah restart lulus. [Review BIMA-04](../reviews/2026-10-09-bima04.md).
ICAL-04 VERIFIED/MERGED #26 (a635ccc):174/174tes, decision34/35 (E15 tetap gagal),
ranking15/15 dan baseline direproduksi. [Review ICAL-04](../reviews/2026-10-09-ical04.md).
Tidak ada komunikasi otomatis antar-chat AI.

## Progres kesiapan tim

Snapshot mentor 9 Oktober20:57WIB: **tim92/100; Boy100/100, Bima100/100, Ical95/100**.
Riwayat75→81 UI,81→86 operasional,86→92 paket pembuktian. Rehearsal belum diberi kredit.
Bukan rubric panitia atau peluang menang. Bobot, bukti, batas dan target berikutnya
ada di [TEAM_PROGRESS.md](TEAM_PROGRESS.md). Angka anggota bukan rata-rata total.
BOY-04/BIMA-04/ICAL-04 selesai. Rehearsal tim dan submission belum diverifikasi.

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
| TEAM-02 | Semua | IN_PROGRESS | Engine/API/UI ranking dan diagnostic merged; rehearsal final belum |
| ICAL-03 | Ical | MERGED #15 | Ranking rules, sumber/path dan referensi terbaru; evaluasi 15/15 |
| BIMA-03 / R8 | Bima; revisi oleh Ical | MERGED #16; R8 VERIFIED | Priorities/diagnostic asli200; 144 backend dan 34 frontend lulus |
| BOY-04 | Boy | MERGED #22; VERIFIED | Ranking/diagnostic API, sumber→graph; 52 frontend/build dan sampling browser lulus |
| BIMA-04 | Bima | MERGED #23; VERIFIED | 164backend, setup bersih, smoke15/15 cold/warm + restart, temuan sumber diperiksa |
| ICAL-04 | Ical | MERGED #26; VERIFIED | Baseline aktual, eval per sumber, brief/claims; Jev live tetap BLOCKED terpisah |
| MAIN-JEV-LIVE | Main | Implementasi VERIFIED lokal; provider BLOCKED | Launcher/check/smoke/analyze/serve;188tes PASS, key belum tersedia; [panduan](../../backend/integrations/JEV_LIVE.md) |
| MAIN-02 | Main | IN_PROGRESS | UI/runbook/paket pitch terverifikasi; rehearsal, kecocokan brief dan submission tersisa |

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
| phase3 validators/resource, Phase3Panels, Dashboard dan DealWorkspace | Boy | MERGED #22; VERIFIED | Ranking/diagnostic nyata, sumber dan error isolation; review BOY-04 |
| backend.api.smoke_demo, DEMO_RUNBOOK, DATA_FINDINGS | Bima | MERGED #23; VERIFIED | GET15endpoint, stop harus gagal, PID baru lulus, fakta dibanding sumber asli |
| evaluation.baseline_crm/run_eval, MENTOR_BRIEF/DEMO_CLAIMS | Ical; koreksi dokumen Main | MERGED #26; VERIFIED | Baseline identik,34/35+15/15, hasil tersimpan cocok; review ICAL-04 |
| scripts/check_handoff.py | Main | Implementasi awal | tests/test_handoff.py |

## Coverage wajib sebelum produk final selesai

`[ ]` acceptance final tim belum dicentang, `[x]` sudah diverifikasi dengan bukti pada PR/commit.
Tabel ini gerbang rehearsal final; tidak membatalkan status implementasi/evaluasi
yang sudah VERIFIED pada inventaris fungsi dan review BOY-04.

| Deal | Konteks | Hambatan/unknowns | Tindakan | Graph/bukti | Preseden diperiksa | UI detail | Ranking | Uji |
|---|---|---|---|---|---|---|---|---|
| P01 | [x] | [ ] | [ ] | [x] | [ ] | [x] | [ ] | [ ] |
| P02 | [x] | [ ] | [ ] | [x] | [ ] | [x] | [ ] | [ ] |
| P03 | [x] | [ ] | [ ] | [x] | [ ] | [x] | [ ] | [ ] |
| P04 | [x] | [ ] | [ ] | [x] | [ ] | [x] | [ ] | [ ] |
| P05 | [x] | [ ] | [ ] | [x] | [ ] | [x] | [ ] | [ ] |

## Tugas sekarang dan dependency

- Boy: BOY-04 selesai. Sync main, latihan demo3–5menit memakai frontend/TESTING.md;
  catat bug nyata bila ditemukan, jangan membuka ulang #22 atau menambah fitur.
- Bima: BIMA-04 selesai. Sync main; jalankan runbook/smoke di mesin demo bersama
  Boy, siapkan pemulihan dan penjelasan data. Catat masalah latihan bila ada.
- Ical: ICAL-04 selesai. Latihan alasan ranking/policy/baseline dan batas E15
  memakai evaluation/MENTOR_BRIEF.md dan DEMO_CLAIMS.md yang dikoreksi Main.
- Main: verifikasi rehearsal akhir,
  kecocokan brief dan submission. UI kini tidak lagi menghalangi latihan demo.
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
Catatan historis: tanda centang konteks hanya membuktikan struktur/sumber tersedia; kolom tindakan,
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

2026-10-09 20:28 WIB: #22 merged ea96e23, BOY-04 VERIFIED. Main52/52frontend, build, CI dan sampling browser lulus; review BOY-04 membedakan tes Main/Boy. Kesiapan81/100, Boy100/Bima90/Ical85. PR Bima#23 belum direview.

2026-10-09 20:43 WIB: #23 merged2585bb3, BIMA-04 VERIFIED. Main164/164backend, setup bersih/pip check, empat15/15socket dan exit1 saat server mati. Fakta DATA_FINDINGS dicocokkan produsen/row asli. Kesiapan86/100; Boy100/Bima100/Ical85.

2026-10-09 20:57 WIB: #26 mergeda635ccc, ICAL-04 VERIFIED. Main174tes,decision34/35 (E15 diketahui),ranking15/15,baseline identik. Panah/prosa demo diperjelas Main. Kesiapan92/100; Boy100/Bima100/Ical95; rehearsal/submission terbuka.

2026-10-09 21:16 WIB: Main menyiapkan aktivasi Jev sesuai instruksi pengguna.
188/188tes PASS termasuk14tes baru (mock); check lokal missing_key,0request.
Pengguna mengonfirmasi belum punya akses/key TypeSafe. Provider live belum
VERIFIED, progress inti92/100 tetap. P05 nol panggilan sekarang tidak dilabeli
Jev; rules/policy/ranking tetap. Lihat JEV_LIVE.md dan handoff Main.
