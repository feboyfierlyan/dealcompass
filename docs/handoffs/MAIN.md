# Handoff MAIN

## Task dan status
PR #16 (implementasi Bima, revisi R8 oleh Ical) MERGED 8581de8. R8 VERIFIED.
Engine/API ranking dan diagnostic siap; UI BOY-04 TODO, prompt sudah dibuat.
Boy #14/R9 dan Ical #15 tetap selesai. Jev live belum diuji.

## Branch dan commit
integrator/verify-r8-assign-boy04 dari main 8581de8. Revisi Ical ebc9999, head final
845d9bc setelah sync main 398c67e. Main menguji head final pada checkout terisolasi
integrator/review-r8-ical. Merge #16: 8581de83d880d0ead72f21c9cfff6873fc3ecb7c.

## File dan fungsi
Review ical-r8 menyimpan bukti, atribusi dan batas verifikasi. MAIN.md menutup R8
serta menugaskan BOY-04. API_CONTRACT dan PHASE3_CONTRACT memperbarui status API
tersedia. BOY-04.md mengatur integrasi UI, source union, graph, unknowns dan tes.
Tidak ada kode aplikasi/dataset/dependency berubah pada PR Main dokumentasi ini.

## Kontrak dan dependency
Wire contract tetap. R8 menerima traversal dua arah melalui edge asli, menjaga
validasi sumber/pasangan endpoint dan tidak mengubah graph. UI baru wajib join
per deal_id/snapshot, memakai rank/rekomendasi dari API dan mempertahankan bukti
context + diagnostic + priorities tanpa konflik. API daftar lama tidak dimutasi.

## Cara menjalankan
Main menjalankan backend rules tanpa key Jev pada port8126, 144 unittest dan
34 tes frontend/build sesuai review. Server dihentikan. Boy sync main lalu
branch baru boy/priorities-diagnostics, ikuti docs/prompts/BOY-04.md dan buat PR baru.

## Pengujian aktual
144/144 backend (30,076 detik), 34/34 frontend, build/handoff/ownership/diff lulus.
CI head845d9bc SUCCESS. Socket HTTP asli: priorities200, pipeline diagnostic200,
diagnostic lima deal200, unknown404. P02 approval tetap pending; P05 discovery,
insufficient_evidence/skor null. Semua sumber/path diperiksa tes integrasi asli.
Perubahan dokumentasi Main dicek handoff/diff dan CI gate; bukan tes UI BOY-04.

## Fixture dan keterbatasan
Kasus korupsi/error transport/lifecycle memakai mock, empat tes priorities baru
serta smoke socket memakai dataset/engine asli. Tidak mengulang browser pada
revisi API. Ranking heuristik bukan prediksi closing; latency satu request lokal
bukan SLA. Jev live dan UI ranking/diagnostic belum diuji atau diimplementasikan.

## Blocker
Tidak ada blocker R8 setelah review. BOY-04 kini dapat mulai; status TODO bukan
klaim sudah dikerjakan. Unknowns bisnis/approval/izin referensi tetap perlu manusia.

## Tugas berikutnya
Pengguna meneruskan BOY-04 ke AI Boy. Ical selesai takeover R8, siapkan penjelasan
metode/sensitivitas untuk mentor. Bima tidak perlu mengulang R8. Main review UI
setelah PR baru, lalu demo akhir/submission. Semua pekerjaan baru wajib handoff.

## Update WIB
2026-10-09 19:30 WIB
