# Riset dan keputusan UX desktop — PR #29

Pelaksana awal Ical/Claude; lanjutan desktop Main/Codex, 9 Oktober 2026.
> Versi ini adalah iterasi awal. Feedback berikutnya dan alur final ada di
> [UX_SALES_FLOW_RESEARCH.md](UX_SALES_FLOW_RESEARCH.md).

Target: sales nonteknis mampu memilih prioritas, memahami tindakan berikutnya, dan memeriksa
alasan tanpa harus membaca formula atau menguasai graph. Scope P01–P05; fokus desktop.

## Metode dan sumber

Dua pencarian **Mobbin MCP**, platform web, deep search; lima preview screen dibaca.
Query pertama: CRM deal detail with a record list on the left and a focused details panel
showing next tasks and activity. Query kedua: Linear issue detail showing a focused task
description with status and assignee beside it and a compact list navigation.
Ini studi pola antarmuka, bukan pengujian kegunaan atau bukti peningkatan konversi.

| Referensi Mobbin | Pengamatan | Keputusan untuk DealCompass |
| --- | --- | --- |
| [HubSpot](https://mobbin.com/screens/6739614d-ffc5-4073-87bd-21de2cbeb640) | Daftar record dan detail terpilih menjaga konteks pekerjaan. | Pertahankan master-detail Ical; ringkas antrean menjadi nomor, nama, tahap, nilai, dan badge yang perlu perhatian. |
| [Apollo](https://mobbin.com/screens/b809b741-ce96-4add-bd43-72246042e9d7) | Informasi deal dipisahkan dari aktivitas; banyak navigasi dan properti. | Ambil pemisahan tugas/detail; jangan menambah navigasi, kolom CRM, atau toolbar untuk lima deal. |
| [Bonsai](https://mobbin.com/screens/239c6c69-20bb-467d-998c-d924d2e76f12) | Tugas dipilih dari daftar, rincian di panel khusus. | Panel sumber muncul hanya saat diminta; gunakan overlay di laptop agar area tindakan tidak menyempit. |
| [Linear issue](https://mobbin.com/screens/d0f8ebba-34b7-469c-a708-1069e55a3e02) | Judul/deskripsi menjadi pusat; status dan assignee ringkas. | Tindakan lebih dahulu, penanggung jawab dan target dekat dengannya; metadata sekunder tenang. |
| [Linear project](https://mobbin.com/screens/7fef18f2-1c32-4bc6-9d27-21241a65e0e4) | Overview terfokus dengan properti dan detail tambahan. | Tiga lapisan informasi, buka satu keputusan lama atau jalur bukti sesuai kebutuhan. Hindari duplikasi properti. |

Tidak menyalin aset, merek, atau keseluruhan layar. Pola dipilih sesuai tugas sales, bukan
karena aplikasi referensi populer. Identitas hijau gelap, ivory, terakota tetap dipertahankan.

## Temuan saat meninjau WIP Ical

Fondasi master-detail, pilihan prioritas API, tiga tab, dan inspector on-demand sudah tepat.
Namun kutipan/penjelasan mendahului tindakan; tombol bukti berada setelah blok panjang;
syarat teknis berulang di antrean; inspector samping mempersempit isi pada 1280/1440 px;
record nonpercakapan tampil sebagai JSON; preseden dan jalur panjang terbuka bersamaan.

## Implementasi lanjutan

1. Tindakan → penanggung jawab/target → persetujuan/ketidakpastian → kutipan penyebab.
   Tombol bukti dan hubungan ditempatkan di bagian atas kartu agar langsung ditemukan.
2. Antrean 296 px, kartu lebih ringkas, nomor pilihan aktif paling menonjol. Peringatan
   persetujuan hanya bila dicantumkan API; discovery tetap “Lengkapi informasi”. Semua syarat
   lengkap tetap di detail. Tidak mengubah skor, rank, default API, atau pilihan pengguna.
3. ID karyawan dan interaksi dalam tindakan menjadi tautan nama/tanggal **hanya jika sumber
   cocok**. ID interaksi ambigu atau tidak cocok tetap literal. Teks asli selalu tersedia;
   semua kata tindakan, negasi, syarat dan kebutuhan izin tetap utuh.
4. Inspector overlay 480 px pada desktop <1800 px; panel samping hanya pada layar lebih lebar.
   Sumber terstruktur menjadi pasangan label/nilai; JSON asli tetap dapat dibuka. Null bukan 0.
5. Keputusan terdahulu dan setiap jalur memakai disclosure native; detail tidak ditampilkan
   semua sekaligus. Provenance, arah asli, inferred/direct dan navigasi graph tetap ada.
6. Kartu bukti dua kolom desktop; locator teknis pindah ke inspector. Alat fixture dev terlipat;
   jika fixture aktif, bannernya tetap jelas. Tidak ada kontrol dev di produksi.
7. Tipografi, jarak, warna pilihan dan fokus dirapikan. Tidak menambah library, animasi berat,
   chat AI, fitur backend, atau proyek desain mobile.

## Penerimaan dan bukti

- 73 tes frontend lulus (31 helper/graph/session/presentation + 42 transport/render); build lulus.
- Browser nyata: P01–P05; gate P02, izin kandidat P03/P04, identitas inferensi P01,
  discovery P05 tetap terlihat. Tidak ada scroll horizontal pada 1280×720 dan 1440×900.
- P04: tombol graph membuka tiga jalur API; relasi overlap diperiksa melalui daftar relasi,
  label dugaan dan dua sumber employment tetap ada; Escape mengembalikan fokus ke pemicu.
- P02: keputusan D-2024-02 dan Jalur 1 dapat dibuka; Enter pada disclosure jalur bekerja.
- Sumber E06 ditampilkan sebagai field manusiawi dan sumber asli masih tersedia.
- Log browser warn/error yang tersedia saat pengecekan akhir kosong.
- Screenshot Main: `tests/screenshots/main-desktop-1440.jpg`, `main-desktop-1280.jpg`,
  `main-source-1440.jpg`, `main-graph-p04-1440.jpg`.

## Batas yang harus disampaikan

Belum ada uji dengan pengguna nonteknis. Target mengenali prioritas dalam 10 detik,
menjelaskan tindakan dalam 30 detik, dan membuka bukti dalam ≤2 interaksi masih target,
bukan hasil terukur. Sebelum demo, minta satu anggota yang tidak mengimplementasikan UI
mencoba tiga tugas tersebut dan catat tempat ia ragu.

Teks bisnis masih relatif panjang karena syarat persetujuan dan izin tidak boleh hilang.
Beberapa field API seperti candidate_decisions tetap literal. UI tidak menjamin closing,
peringkat heuristik belum tervalidasi historis. Jev live tidak diuji. Tidak ada klaim audit
aksesibilitas penuh atau uji mobile terbaru. Interaksi SVG langsung tidak berhasil diautomasi
oleh alat browser; daftar relasi alternatif berhasil diuji. Jangan menyebut itu lulus klik SVG.
