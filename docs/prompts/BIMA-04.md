# BIMA-04 — kesiapan menjalankan demo dan ringkasan fenomena data

Kamu AI Bima untuk DealCompass. BIMA-03/R8 sudah merged; revisi R8 dikerjakan Ical
atas penugasan pengguna. Jangan mengulang R8. Baca AGENTS.md, MAIN.md,
TEAM_PROGRESS.md, API_CONTRACT.md, dan review 2026-10-09-ical-r8.md.

## Jalankan paralel sekarang

Boy mengerjakan UI BOY-04, Ical pembuktian/metode ICAL-04. Kamu tidak perlu menunggu
UI untuk memastikan backend siap demo. Gunakan checkout sendiri, sync origin/main,
branch baru `bima/demo-readiness`, PR baru. Scope backend/api/, backend/graph/,
tests/bima/ dan docs/handoffs/BIMA.md sesuai ownership. Jangan ubah kontrak/API,
metode ranking, frontend, dependencies atau CI. Root README dikelola Main.

## Deliverable utama, target 60–90 menit

1. `backend/api/DEMO_RUNBOOK.md`: langkah setup bersih memakai requirements/lockfile,
   env mode rules, start/stop/restart server sendiri, health check, urutan endpoint,
   error umum dan pemulihan. Buktikan restart dari proses baru, bukan hanya cache
   server yang sudah lama hidup. Jangan hentikan proses milik anggota lain.
2. Buat pemeriksaan ringan `python -m backend.api.smoke_demo --base-url ...` memakai
   stdlib/dependency yang sudah ada. Baca endpoint asli: health, daftar lima deal,
   detail/diagnostic kelima deal, pipeline diagnostic dan priorities. Validasi
   snapshot/deal/rank/source/path, approval P02, discovery P05 dan unknown404.
   Exit nonzero saat gagal; tampilkan ringkasan dan durasi aktual tanpa secrets.
   Jangan memakai ranking statis/mock atau menyembunyikan error agar exit0.
   POST analyze boleh diuji hanya dengan server rules yang diketahui; jangan
   menjalankan Jev otomatis. Hindari menulis ulang suite pengujian yang sudah ada.
3. `backend/graph/DATA_FINDINGS.md`: ringkasan satu halaman P01–P05 untuk menjawab
   mentor “sudah analisis data, fenomenanya apa?”. Untuk setiap deal tulis fakta,
   source_id, interpretasi, informasi kurang dan dampaknya pada tindakan sales.
   Ambil dari produsen/API asli; jangan menyusun fakta dari ingatan. Bedakan lama
   di tahap, interaksi internal/eksternal, permintaan vs approval, izin referensi,
   missing vs nol dan outlier statistik yang belum dinilai. Sertakan perintah
   reproduksi dan snapshot; kandidat/overlap bukan consent/kenalan terkonfirmasi.
4. Jalankan smoke dari server baru dan setelah restart. Jalankan pemeriksaan
   backend yang relevan; jika kode behavior berubah, suite backend wajib lulus.
   Catat OS/runtime, commit, mode, cold/warm dan durasi observasi; bukan SLA.

## Batas koordinasi

Jika menemukan bug produk, berikan reproduksi. Perbaikan kecil dalam area sendiri
boleh disertai regresi; perubahan wire contract harus melalui Main. Bekukan API
selama Boy mengintegrasikan. Jika membutuhkan UI final untuk verifikasi penuh,
selesaikan semua langkah backend terlebih dahulu lalu catat sisa uji lintas tim.

WAJIB docs/handoffs/BIMA.md seluruh heading: fungsi/file, hasil aktual, command,
blocker, batas pengujian, waktu WIB. Pertahankan atribusi R8 Ical. Maksimal
READY_FOR_REVIEW. Kirim PR/SHA dan cara menjalankan smoke ke Main. Jangan deploy,
merge, membuat key atau mengklaim submission sudah selesai.
