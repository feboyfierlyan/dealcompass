# ICAL-04 — pembuktian metode dan paket penjelasan mentor

Kamu AI Ical untuk DealCompass. ICAL-03 serta takeover R8 sudah merged; kembali
ke area Ical. Baca AGENTS.md, MAIN.md, TEAM_PROGRESS.md, evaluation/ranking.md,
evaluation/README.md, dan review R8. Boy sedang mengintegrasikan UI, Bima menyiapkan
backend demo; kamu bisa mulai sekarang tanpa menunggu keduanya.

Gunakan checkout sendiri, sync main, branch baru `ical/evidence-demo-pack`, PR baru.
Scope evaluation/, backend/decision/, backend/integrations/, tests/ical/ dan
handoff ICAL.md. Prioritas pekerjaan ini evaluasi/penjelasan, bukan rewrite engine.
Bekukan formula ranking dan kontrak saat Boy mengintegrasikan. Jika menemukan
bug, laporkan reproduksi; perubahan behavior perlu tes dan koordinasi Main.

## Deliverable utama, target 60–90 menit

1. `evaluation/MENTOR_BRIEF.md`: jelaskan dalam bahasa sederhana masalah bisnis,
   mengapa CRM saja belum cukup, bagaimana graph memberi alasan/riwayat keputusan,
   arti ranking dan tindakan P01–P05. Pakai output dan source_id aktual, bukan
   cerita yang dibuat. Siapkan jawaban: kenapa P04 di atas P01; kenapa P02 bukan
   otomatis pertama meski paling lama di tahap; kenapa P05 discovery; apa batas
   bobot/heuristik; apa beda business anomaly vs statistical outlier.
2. Susun pembanding sederhana CRM-only vs graph+rules pada lima deal yang sama.
   Definisikan baseline transparan (misalnya tahap/nilai saja), gunakan data
   kanonis yang sama, dokumentasikan faktor yang sengaja tidak dipakai. Simpan
   script/hasil di evaluation/. Tunjukkan perubahan alasan/tindakan dan sumber
   tambahan; perbedaan urutan saja bukan bukti model lebih akurat. Jangan melatih
   model, mengubah formula production, atau mengklaim uplift closing dari lima kasus.
3. Jalankan ulang evaluasi decision/ranking setelah main sinkron; laporkan semua
   kasus dan E15 yang diketahui, tanpa menghilangkan kegagalan. Pisahkan kasus
   dataset asli dari mutasi/sintetis; benchmark ini belum holdout independen.
4. Buat matriks klaim→bukti→batas di `evaluation/DEMO_CLAIMS.md`: klaim yang boleh
   dipresentasikan, source/path/test yang mendukung, dan klaim yang belum terbukti.
   Siapkan bahan demo 3–5 menit dan tanya jawab mentor, termasuk dampak bisnis
   sebagai hipotesis, bukan hasil peningkatan penjualan yang sudah diukur.

## Jev: jalur bonus terpisah, tidak menghambat rules

Adapter sekarang ada, mock/replay diuji; live belum diverifikasi. Nilai bonus Jev
belum dikonfirmasi dalam penugasan ini. Jangan menjanjikan poin penilaian.

Periksa kesiapan konfigurasi backend tanpa menampilkan nilai secret. Jika credential
resmi sudah tersedia dan akses/provider memang diizinkan, verifikasi dokumentasi
resmi terkini sebelum smoke live terbatas, target maksimal 20 menit. Pakai input
minimal dari dataset fiktif yang relevan, catat request count, mode/error/latency dan
hasil validasi tanpa key/auth headers; jangan merekam raw credential atau membuat
pembelian/akun baru. Jangan menjalankan live dari GET priorities atau diagnostic.

Jika credential/akses tidak tersedia, tulis BLOCKED khusus subtask Jev dengan alasan
konkret; selesaikan empat deliverable utama. Jangan meminta key ditempel di chat,
menganggap mock sebagai live, atau mengubah tampilan rules menjadi label Jev.
Tunjukkan cara menjalankan demo rules yang sudah berfungsi. Tidak perlu menunggu
credential untuk mengirim PR paket evaluasi.

## Penyerahan WAJIB

Update docs/handoffs/ICAL.md seluruh heading: file/fungsi, hasil aktual, batas
baseline/eval, mode rules/mock/replay/live yang benar, blocker Jev jika ada, waktu
WIB. Maksimal READY_FOR_REVIEW; Main memutuskan VERIFIED/MERGED. Kirim PR baru,
SHA, ringkasan temuan dan link bahan mentor. Jangan mengerjakan PR #16 lagi.
