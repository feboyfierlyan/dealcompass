# Prompt AI Boy — BOY-01

Kamu membantu Boy membangun frontend DealCompass. Baca AGENTS.md, MAIN.md,
API_CONTRACT.md. Branch boy/frontend. Area frontend/ dan docs/handoffs/BOY.md.
Scope final P01-P05; P02 hanya kasus integrasi pertama.

## Kerjakan sekarang
1. Lanjutkan fondasi React; tampilkan semua deal dari GET /api/deals.
2. Buat detail deal, hambatan/unknowns, tindakan, owner dan milestone.
3. Buat graph interaktif; klik node/edge membuka sumber bukti dan tanggalnya.
4. Bedakan direct vs inferred; bandingkan preseden dan perbedaan kasus.
5. Tangani loading, 404, 501, gangguan API dan label engine_mode.
6. Integrasikan P02 lalu seluruh lima deal. Ranking null jangan ditampilkan sebagai 0.
7. Catat uji alur dan jalankan npm run build.

Detail API menunggu Bima. Jika memakai fixture dari sumber asli, beri label
fixture dan isolasikan adapter. Tes ulang dengan backend nyata sebelum menyatakan
integrasi selesai. Jangan menanam rekomendasi/aturan diskon di UI.
Usulkan dependency graph kepada Main; jangan ubah package manifest/lock sendiri.

## Catatan WAJIB
Perbarui docs/handoffs/BOY.md pada milestone dan setiap PR. Semua heading template
wajib diisi: tugas, branch/commit, checklist, file/fungsi beserta input-output,
kontrak/dependency, cara menjalankan, hasil uji aktual, fixture, blocker, next tasks,
dan waktu WIB. Jangan mengedit handoff orang lain atau docs/coordination/.

## Penyerahan
PR menuju main. Sertakan acceptance yang lulus/belum, cara mengecek, file catatan
dan commit. Status maksimal READY_FOR_REVIEW. Main menetapkan VERIFIED/MERGED.
Jika ChatGPT hanya dapat memberi teks, hasilkan isi file/diff untuk disimpan
Boy dan catat bahwa eksekusi masih harus dijalankan manusia.

