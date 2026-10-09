# Handoff MAIN

## Task dan status
ICAL-04 VERIFIED/MERGED #26. Tim92/100, Boy100/Bima100/Ical95; kredit rehearsal
belum diberikan. Koreksi dokumentasi demo Main menyertai review.

## Branch dan commit
integrator/review-ical04-notes dari maina635ccc. Head Icalf95b34b setelah update
branch, mergea635ccc7b24d8efd249df8fdbbae99087445f0a9. Evaluation tidak berubah
pada update dari1fcbab7; Main hanya menambahkan koreksi prosa, bukan formula.

## File dan fungsi
Review ICAL-04 mencatat174tes,34/35decision,15/15ranking dan baseline identik.
MENTOR_BRIEF/DEMO_CLAIMS: arah edge P01, urutan baca dua sumber P02, harga pilot,
field baseline dan status UI diperjelas. MAIN/TEAM_PROGRESS/README diperbarui.

## Kontrak dan dependency
API/backend/metode/dataset/dependency tidak berubah. Snapshot2026-10-01,
P01–P05; baseline sengaja terbatas dan bukan ukuran seluruh produk CRM.

## Cara menjalankan
python -m evaluation.run_eval --no-write; python -m evaluation.baseline_crm
--no-write. Gunakan runbook Bima untuk start backend rules dan UI Boy.

## Pengujian aktual
Main174/174tests50.117s pada venv bersih. Run evaluasi/baseline dibandingkan
JSON tersimpan: identik kecuali timestamp/durasi. E15 tetap gagal; inti34/34.
CI PR26 PASS. Handoff/ownership/diff PASS. Panah diperiksa terhadap graph asli;
harga skenario/preseden diperiksa producer/row asli. PR docs diuji checks danCI.

## Fixture dan keterbatasan
Decision dataset7/7,sintetis16/17,mock9/9,replay2/2; ranking asli5/5,mutasi10/10.
Tidak ada Jev live/holdout/labelclosing/uplift. Unit suite174PASS tidak berarti
benchmark35/35. Browser/lifecycle merujuk review Boy/Bima sebelumnya, tidak diulang.

## Blocker
Tidak ada blocker paket ICAL-04. Jev live BLOCKED khusus bonus menurut handoff
Ical; tidak menghambat rules. Rehearsal dan penyerahan belum terverifikasi.

## Tugas berikutnya
Tim latihan3–5menit: Boy produk, Bima data/startup, Ical alasan/policy/batas.
Main verifikasi latihan, cocokkan brief dan paket penyerahan. Jangan ubah ranking
agar berbeda dari baseline atau mengklaim probabilitas closing.

## Update WIB
2026-10-09 20:57 WIB — review ICAL-04 dan koreksi dokumen Main.
