# Handoff MAIN

## Task dan status
BIMA-04 VERIFIED/MERGED #23. Kesiapan tim86/100, Boy100/Bima100 pada scope tugas,
Ical85. Rehearsal/paket bukti final dan submission belum diverifikasi.

## Branch dan commit
integrator/review-bima04-notes dari main2585bb3. Bima awalebe9c78 disinkronkan
ke head34022b6596472e40b3c8edda2cb0f8e379751389 tanpa perubahan kode miliknya.
Merge2585bb34ee9bb161394014ded392e1ec1a00d17a. Catatan ini tidak mengubah produk.

## File dan fungsi
Review BIMA-04 mencatat suite164, setup bersih, lifecycle dan verifikasi temuan.
MAIN/TEAM_PROGRESS memperbarui tugas/inventaris/kredit, README menautkan runbook
dan fenomena data. Handoff ini diperbarui untuk audit Main.

## Kontrak dan dependency
Tidak mengubah API/metode/CI/dependency/dataset. Scope P01–P05, snapshot2026-10-01.
Revisi R8 milik Ical; tidak diatribusikan ulang kepada Bima.

## Cara menjalankan
Ikuti backend/api/DEMO_RUNBOOK.md. Checker python -m backend.api.smoke_demo
--base-url http://127.0.0.1:8000 --timeout 30.
Jalankan backend rules sendiri; stop/restart hanya proses sendiri.

## Pengujian aktual
Main164/164backend PASS48.822s; CI head34022b6 PASS. Setup requirements venv
bersih dan pip check PASS; empat smoke15/15 pada PID50659→50776, saat mati exit1.
Handoff --all/ownership/diff PASS. Row asli/producer cocok dengan DATA_FINDINGS.
Catatan docs ini diuji handoff/ownership/diff dan CI required sebelum merge.

## Fixture dan keterbatasan
20 tes baru transport/corruption sintetis terpisah dari socket/restart nyata.
Suite lokal memakai venv review lama; konflik paket eksternal ditemukan saat
pip check sehingga setup+restart diulang di venv bersih, lulus. CI juga lulus.
Frontend52 tes/browser adalah review BOY-04 sebelumnya, tidak diulang kali ini.
Tidak mengklaim Jev live, deployment, rehearsal tim atau submission.

## Blocker
Tidak ada blocker BIMA-04. Paket ICAL-04 dan latihan/paket penyerahan masih perlu
verifikasi; kesiapan86 adalah bobot internal, bukan peluang juara.

## Tugas berikutnya
Boy demo3–5menit, Bima startup/recovery dan penjelasan sumber, Ical paket evaluasi/
mentor ICAL-04. Main review paket Ical, periksa brief dan rehearsal lalu submission.

## Update WIB
2026-10-09 20:43 WIB — review BIMA-04 dan progres berbobot.
