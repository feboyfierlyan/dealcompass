# Main — pusat koordinasi DealCompass

Pemilik: Boy + AI pada chat koordinasi. Tanggal: 9 Oktober 2026, WIB.
Deadline: 10 Oktober 2026 09.00 WIB. CP2 20.00-22.00, CP3 08.00-09.00.

## Status produk

PR Boy #5, Ical #7, dan Bima #10 sudah MERGED. Main pada 41cee67 memiliki
frontend graph, analisis keputusan rules P01-P05, serta fungsi internal diagnostic Bima.
Gabungan 99/99 unittest lulus; evaluasi Ical 34/35 (inti 34/34), E15 dikenal terbatas.
R6/R7 approval sudah diperbaiki dan diverifikasi independen. POST analyze P01-P05
200 dan smoke browser kelima rekomendasi berhasil. [Review final](../reviews/2026-10-09-pr7-pr10-final.md).
Jev live, ranking lintas deal, pemetaan analysis_status, API diagnostic dan UX final
belum selesai. Diagnostic Bima masih internal, belum otomatis tampil di UI.
Tidak ada komunikasi otomatis antar-chat AI.

## Checklist tugas

| ID | Pemilik | Status | Hasil / acceptance |
|---|---|---|---|
| MAIN-00 | Main | VERIFIED | Repo, dataset, kontrak, CI, branch, undangan dan task issues |
| BOY-01/02 | Boy | MERGED #5; R4 VERIFIED | UI lima deal, detail, graph klik, panel bukti, uji UI dan handoff |
| BIMA-01 | Bima | MERGED #6 | Ingest seluruh sumber, graph temporal dan konteks P02, API dan handoff |
| ICAL-01/02 | Ical | MERGED #7; R6/R7 VERIFIED | Analisis rules P01-P05, policy gate, adapter Jev mock/replay dan evaluasi |
| BIMA-02 | Bima | MERGED #10 | Metrik, diagnosis bersumber dan verifikasi identitas/referensi internal P01-P05 |
| BOY-03 | Boy | TODO; prompt siap | Penyajian analisis nyata, alur sumber ke graph, status sesi dan demo |
| MAIN-01 | Main | VERIFIED untuk smoke rules | HTTP dan browser P01-P05 menghasilkan analisis; persiapan demo final lanjut |
| TEAM-02 | Semua | IN_PROGRESS | Ranking/diagnostic ditugaskan melalui kontrak fase 3; implementasi belum tersedia |
| ICAL-03 | Ical | TODO; prompt siap | Ranking seluruh deal + rationale/factors/paths; referensi terbaru; rules deterministik |
| BIMA-03 | Bima | TODO; prompt siap | API diagnostic dan adapter priorities sesuai PHASE3_CONTRACT.md |
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
| analyze_deal | Ical | MERGED #7 | R1-R3/R5/R6/R7 lulus; evaluasi inti 34/34 |
| GET detail / POST analyze | Bima + Ical | 200 untuk P01-P05; mode rules teruji | Evidence IDs resolvable; HTTP dan browser sukses |
| analyze_deal_initial / analyze_pipeline_initial | Bima | MERGED #10; fungsi internal | JSON strict dan setiap excerpt cocok sumber; belum endpoint |
| frontend/src/main.tsx dan graphView.ts | Boy | MERGED #5; R4 VERIFIED | 20 tes frontend; UI nyata desktop/mobile P01-P05 |
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

- Boy / BOY-03: kerjakan [prompt lengkap](../prompts/BOY-03.md) sekarang pada branch baru boy/analysis-demo. Rapikan analisis nyata, telusuri sumber ke graph, bedakan status request sesi dari status bisnis, uji P01-P05 dan siapkan demo. Tidak perlu menunggu endpoint Bima untuk cakupan ini.
- Bima / BIMA-03: jalankan [prompt](../prompts/BIMA-03.md). Kontrak sudah ditetapkan di [PHASE3_CONTRACT.md](PHASE3_CONTRACT.md). Diagnostic API bisa dikerjakan sekarang; adapter priorities memakai mock berlabel sampai fungsi Ical tersedia, lalu smoke nyata.
- Ical / ICAL-03: jalankan [prompt](../prompts/ICAL-03.md). Implementasikan rank_deals sesuai kontrak fase 3, seluruh P01-P05 dengan rationale/factors/paths; selaraskan verifikasi referensi Bima. Ranking rules tidak menunggu Jev live. Metode heuristik bukan probabilitas closing.
- Main: kontrak fase 3 sudah ditetapkan; review metode/ranking Ical dan API Bima, smoke hasil gabungan, lalu tugas BOY-04 untuk menampilkan diagnostic/priorities. analysis_status bisnis baru disertakan di priorities, status daftar lama tidak diubah sepihak. Ranking masih output wajib yang belum terimplementasi.
- Semua: fetch origin/main; PR lama selesai, pekerjaan baru memakai branch/PR baru serta handoff masing-masing. Boy meneruskan prompt ke AI anggota; tidak ada pesan otomatis antar-chat.

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
