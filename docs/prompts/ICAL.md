# Prompt Claude Ical — ICAL-01

Kamu membantu Ical membangun decision engine, Jev dan evaluasi. Baca AGENTS.md,
README dataset, MAIN.md, API_CONTRACT.md. Branch ical/decision-jev. Area
backend/decision/, backend/integrations/, evaluation/, tests/ical/,
docs/handoffs/ICAL.md. Scope final semua P01-P05; P02 hanya integrasi awal.

## Kerjakan sekarang
1. Implementasikan analyze_deal(context: DealContext) -> Recommendation.
2. Gunakan adapter Jev backend; verifikasi dokumentasi resmi provider.
   https://docs.typesafe.ai/introduction/quickstart
3. Choice untuk hambatan satu pesan (termasuk insufficient evidence), Score
   untuk kecocokan satu preseden, Noul untuk pernyataan eksplisit bila berguna.
4. Aturan kode: hitung uang/tanggal, diskon >10% membutuhkan approval VP Sales
   dan pencatatan, permintaan bukan approval, preseden bukan izin otomatis.
5. Gunakan template penjelasan awal berbasis bukti. Validasi evidence_ids dan
   precedent_ids; jangan mengarang sumber atau probabilitas closing.
6. Mode jev/rules/replay harus eksplisit. Catat provider/model aktual, latensi
   dan kegagalan tanpa membocorkan secret. Tidak ada key: label belum diuji live.
7. Uji minimal 10 kasus: request vs approval, preseden cocok/tidak cocok,
   bukti kurang/ID tidak valid, parafrase, timeout, hitungan diskon.

P02: baca I0296 dan I0348, serta D-2025-02/06. Pilot sebagian outlet adalah
usulan skenario, bukan fakta pelanggan; satu keberhasilan lama bukan jaminan.
Jangan menganggap batas 15% pada satu preseden sebagai aturan universal.

Konteks Bima belum siap: fixture berlabel dari record asli sesuai kontrak.
Jangan membuat ingest/schema duplikat. Jalankan ulang dengan graph Bima.
Setelah P02: analisis seluruh deal dan usulkan ranking lintas deal yang
transparan. Perubahan schema/kontrak untuk ranking disetujui Main dahulu.

## Catatan WAJIB
Perbarui docs/handoffs/ICAL.md pada milestone dan setiap PR. Isi semua heading
template, fungsi/input-output, aturan/asumsi, provider/model, live/rules/replay,
nama env tanpa nilainya, evaluasi aktual, blocker, integrasi, next tasks, waktu WIB.
Jangan edit file koordinasi, loader/route Bima, frontend atau handoff orang lain.

## Penyerahan
PR ke main, status READY_FOR_REVIEW. Sertakan perintah run dan hasil uji nyata.
Jika Claude hanya memberi teks, berikan isi file/diff untuk disimpan Ical dan
jelaskan eksekusi yang masih perlu dijalankan manusia.

