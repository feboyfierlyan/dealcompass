# Prompt AI Ical — ICAL-03

Kamu AI pendamping Ical, pemilik decision engine/Jev/evaluasi DealCompass.
Kerjakan sampai READY_FOR_REVIEW, bukan hanya rencana.

## Mulai
PR #7 sudah merged, R6/R7 selesai. Fetch origin/main terbaru; pertahankan perubahan
lokal dan gunakan checkout sendiri. Buat branch baru ical/priority-ranking dari
origin/main dan PR baru, jangan buka ulang #7. Baca AGENTS.md, MAIN.md, API_CONTRACT.md,
docs/coordination/PHASE3_CONTRACT.md, handoff BIMA/ICAL, dan review final #7/#10.
Kontrak PHASE3_CONTRACT.md sudah disepakati Main untuk tugas ini; implementasikan
persis signature dan envelope-nya. Bima menyiapkan route secara paralel.

## Prioritas 1 — output wajib lomba: ranking dan langkah berikutnya
Implementasikan backend/decision/ranking.py:rank_deals(contexts, diagnostics).
Bandingkan seluruh P01-P05 berdasarkan bukti dan kesiapan tindakan, bukan nominal
terbesar saja atau daftar ID hardcoded. Pilih metode rules deterministik sederhana,
jelaskan alasan desain/bobot/tie-break, dan bedakan faktor yang dihitung dari konteks.
Baca semua detail input/output/validasi pada kontrak fase 3. Output harus memuat
ranking 1..5, alasan perbandingan, faktor bersumber, Recommendation v1, approval,
status bukti, limitations dan jalur graph asli. Jangan membuat probabilitas closing.
P05 tetap discovery dengan bukti kurang; bukan otomatis peluang buruk.

Tidak memanggil Jev untuk ranking dan tidak membaca dataset kedua. Gunakan konteks
Bima serta diagnostic yang diberikan. Jangan ubah API/backend milik Bima.

## Prioritas 2 — selaraskan bukti referensi terbaru
Manfaatkan reference_candidates/verifikasi BIMA-02 sebagai pemeriksaan kelayakan
bukti, bukan izin pelanggan. Hindari menganggap usage bulan lama membuktikan kondisi
terbaru. Missing/zero tetap berbeda; suitability/consent yang null tetap unknown.
Jaga P01 identitas inferred, P02 approval gate, P03/P04 verifikasi dan izin, P05 discovery.
Jika perlu memperbaiki fungsi decision yang sudah ada, pertahankan analyze_deal(context)
dan kontrak Recommendation v1, hindari duplikasi ingest/API, dokumentasikan perubahan.

## Pengujian wajib
Tes kelima deal nyata, input diacak, tie stabil, ID fixture diubah, nilai besar dengan
bukti kurang, faktor berubah secara terkontrol, invalid input, evidence/path valid,
serta regresi approval R1-R3/R5/R6/R7. Jelaskan sensitivity metode; hasil berbeda saat
bukti berubah itu wajar, jangan memaksa peringkat tertentu demi demo.
Jalankan unittest dan evaluasi aktual. Pisahkan dataset nyata, mutasi sintetis, mock,
replay, dan live dalam catatan hasil. Jangan mengklaim score sebagai validasi closing.

## Jev setelah ranking berfungsi
Jev live adalah pekerjaan lanjutan, bukan blocker ranking rules. Jangan mencari atau
mencetak API key. Jika credential uji sudah tersedia melalui mekanisme aman yang
berwenang, lakukan smoke kecil dan catat mode/latency/fallback tanpa key. Jika belum,
catat blocker credential secara spesifik dan lanjutkan mock/replay/fallback. Jangan
menambah credential/dependency atau mengklaim Jev live tanpa eksekusi nyata.

## Penyerahan dan .md WAJIB
Area: backend/decision/, backend/integrations/, evaluation/, tests/ical/ dan
 docs/handoffs/ICAL.md. Jangan edit kontrak bersama, route, graph Bima, frontend,
manifest/CI atau dataset. Usulan perubahan kontrak dicatat untuk Main.
Update handoff dengan seluruh heading template, fungsi dan input-output, metode
ranking, sumber, tes aktual, limitations, blocker, tugas lanjut dan waktu WIB.
Simpan metode/evaluasi ranking di evaluation/README.md atau evaluation/ranking.md.
Push branch dan buka PR baru beserta SHA, handoff dan bukti uji. Status maksimal
READY_FOR_REVIEW. Jangan merge sendiri. Main melakukan review integrasi.
