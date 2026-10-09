# Mixpanel-inspired desktop workspace — 10 Oktober 2026

## Tujuan dan batas
Melanjutkan PR #29 atas permintaan Boy: pengguna sales baru harus mengenali deal prioritas,
langkah berikutnya, penanggung jawab dan syarat sebelum bertindak. Desktop 1280×720 dan
1440×900 menjadi target. Semua P01–P05, provenance, aturan approval dan snapshot tetap.
Ini adaptasi pola UI Mixpanel, bukan salinan produk atau bukti kemenangan/kegunaan manusia.

## Riset langsung Mobbin MCP
Dua pencarian screen mode deep + satu flow; empat screen dan tiga preview flow diperiksa
secara visual. Canonical link dipakai agar tidak tergantung URL gambar sementara.

| Referensi | Observasi dari gambar | Adaptasi DealCompass |
| --- | --- | --- |
| [Mixpanel home](https://mobbin.com/screens/87498414-a8e5-47f7-8d0c-9ee26aa8e55c) | Sidebar netral, area putih, ringkasan metrik di atas dan judul pendek | Sidebar berisi lima deal; tiga kartu tahap, usia tahap, nilai tahunan dari API |
| [Main dashboard dark](https://mobbin.com/screens/1a7d8d86-f0e8-456a-a60c-65c6eb13a252) | Kartu memiliki label/deskripsi dan visual utama; ungu mengikat analisis | Hierarki label → nilai; ungu menandai pilihan/CTA/jalur. Tema terang mengikuti referensi pengguna |
| [Flow dengan inspector](https://mobbin.com/screens/80308183-f1d0-43e5-a35e-2c0df3312c31) | Canvas tetap jadi konteks; detail pengguna muncul di kanan | Peta fokus + drawer sumber; pengguna bisa kembali ke node asal |
| [Flow dengan query controls](https://mobbin.com/screens/8cfa1581-ddb4-4c34-a83e-ceb1cdc47544) | Canvas dominan, kontrol dikelompokkan, pengaturan rinci terbuka kontekstual | Atur tampilan/cari-perluas tetap disclosure; zoom mudah dijangkau; label node bahasa manusia |
| [Filtering a board](https://mobbin.com/flows/0c7166e7-4edf-4700-9832-413197d788a2) | Preview langkah 1/3/4 menunjukkan konteks board bertahan, popover filter, lalu empty state satu kartu | Pertahankan deal saat inspeksi, error lokal, detail progresif; tidak menambah filter dashboard yang tak dibutuhkan lima deal |

Flow yang dikembalikan bernama Filtering a board, bukan perjalanan opening report yang
awalnya dicari. Hanya tiga preview yang ditampilkan MCP dikaji; tidak mengklaim semua
langkah internal sudah diuji.

Dokumentasi produk primer: [Mixpanel Boards](https://mixpanel.com/blog/boards-collaborate-cards-mixpanel-feature-update/)
menjelaskan kartu teks untuk konteks dan susunan kartu. Ini mendukung pilihan menyandingkan
saran tindakan dengan bukti; tidak membuktikan layout kita sudah optimal bagi pengguna.

## Keputusan UI/UX
1. Satu sidebar berisi pekerjaan nyata: P01–P05 sesuai rank API. Tidak menambahkan navigasi
   Home/Reports/Settings yang tidak memiliki fungsi.
2. Panduan awal tiga langkah dapat ditutup. Deal teratas terbuka secara default; pilihan
   pengguna tetap dipertahankan ketika ranking tiba.
3. Kartu ringkasan memakai tahap, usia tahap dan nominal asli. Nilai disebut potensi tahunan,
   belum pendapatan. Tidak ada sparkline, conversion rate, persentase closing atau funnel rekaan.
4. Kartu tindakan dominan: judul singkat, pemilik, hasil yang dituju, syarat, CTA persiapan.
   Usulan lengkap tetap tersedia. Panel pendukung menunjukkan jumlah bukti unik dan jalur
   prioritas dari payload; jumlah sumber bukan confidence. Ketika rekomendasi sesi dipakai,
   jalur tetap jelas berlabel dari analisis prioritas.
5. Detail lanjutan: alasan/bukti, graph, seluruh bukti, metode, temuan, teknis. Tidak ada
   fungsi dihapus agar screenshot tampak sederhana.
6. Graph memakai node/edge asli dan arah asli. Ungu tebal berarti jalur prioritas; dashed tetap
   inferred. Chart arus Mixpanel tidak disalin menjadi Sankey sebab dataset bukan aliran event.
7. Skala visual konsisten: white/gray/lilac, border ringan, radius 7–10px, angka tabular,
   tombol 36–40px, focus ring, teks+warna untuk status. Ukuran kecil dipakai pada metadata;
   judul/tindakan tetap dominan. Kontras penuh belum diaudit ulang secara otomatis.
8. Micro-interaction: hover/active/focus, selected tab/row, dialog fokus/Escape, transisi
   singkat dengan reduced-motion. Animasi masuk hanya transform, supaya tab background yang
   menunda frame tidak meninggalkan teks transparan.

## Inventaris yang disentuh / dipertahankan
- Appbar + workspace identity + queue: layout dan style baru, callback/API tetap.
- Deal header + tabs: metadata ringkas, ringkasan tiga kartu; keyboard tabs tetap.
- Action + proof panel: grid desktop, CTA review/copy tetap; rencana bukan kirim/CRM update.
- Reasons/evidence cards, search, pagination, source drawer: visual sistem yang sama.
- Graph canvas, nodes, edge highlight, controls, relationship list: palette/label diperbarui.
- Plan dialog + error/loading/empty + developer fixture: menggunakan token bersama;
  banner fixture dan label mode rules/replay/Jev tetap.
- Tidak ada backend, dataset, dependency, endpoint, scoring atau permission baru.

## Verifikasi aktual
- 77/77 frontend: 31 kontrak/graph/session/present + 46 API/analysis/phase3/redesign.
- Build TypeScript + Vite lulus. Percobaan awal sandbox tidak bisa mengakses localhost;
  diulang dengan akses yang sesuai dan lulus; bukan bug aplikasi.
- Browser API rules nyata: kelima deal; P01 identitas inferred; P02 VP Sales pending;
  P03/P04 izin referensi; P05 discovery dan bukan bebas risiko.
- P04 graph awal 3 jalur, 6 titik / 147 dan 9 relasi / 297. Node I0335 membuka sumber;
  tombol sumber memfokuskan 3 titik / 2 relasi. Tidak membuat relasi baru.
- Dialog P04/P02 terbuka, Tab dari Salin kembali ke Tutup, Escape menutup. Pada 1280×720,
  dialog top32/bottom688 dan tidak meluap horizontal. Clipboard OS tidak diuji ulang.
- Layout 1440×900 dan 1280×720 tidak overflow horizontal. Halaman dapat scroll vertikal;
  screenshot full-page bukan klaim semua konten berada di atas fold.
- Screenshot hasil ada di tests/screenshots/mixpanel-*.png.
- Belum dilakukan usability test manusia, audit aksesibilitas penuh, mobile QA, atau Jev live.

## Uji tim sebelum presentasi
Minta satu anggota yang tidak mengimplementasikan layar: pilih deal yang perlu didahulukan,
jelaskan tindakan/pemilik/syarat, buka sumber, lalu siapkan rencana. Catat waktu dan titik
bingung. Target 10 detik mengenali prioritas dan 30 detik memahami tindakan adalah sasaran
uji, bukan hasil yang sudah terbukti. Demo tetap menunjukkan sumber dan gate bisnis.
