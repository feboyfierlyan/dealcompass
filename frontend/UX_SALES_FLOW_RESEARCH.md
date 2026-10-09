# Riset UX: dari pembaca laporan menjadi sales yang siap menindaklanjuti

Status: implementasi desktop PR #29, lanjutan Main/Codex setelah feedback pengguna bahwa
versi sebelumnya masih membingungkan. Riset ini membahas seluruh alur aplikasi yang tersedia,
bukan seluruh aplikasi CRM atau klaim desain terbaik secara universal. Mobile di luar scope.

## Masalah dan ukuran keberhasilan

Feedback pengguna adalah bukti bahwa merapikan tampilan saja belum cukup. Versi sebelumnya
menampilkan usulan panjang, ID sumber, penjelasan aturan dan beberapa tombol pemeriksaan.
Tombol paling menonjol membuka bukti, bukan membantu menyiapkan tindak lanjut.

Pekerjaan sales: pilih deal yang perlu perhatian, pahami hambatannya, ketahui siapa yang
bertindak dan apa yang perlu dipastikan, lalu siapkan rencana yang bisa dipakai. Untuk juri,
setiap rekomendasi harus dapat dijelaskan lewat sumber dan jalur relasi, termasuk preseden
keputusan dan batas inferensi. Desain harus melayani kedua kebutuhan dengan kedalaman berbeda.

Target uji berikutnya: pengguna baru menemukan deal prioritas dan tombol berikutnya tanpa
bantuan, bisa menjelaskan target/owner/batasannya, dan dapat menunjukkan bukti. Ukur waktu,
jumlah salah klik, kebutuhan bantuan, serta salah tafsir approval. Target 10/30 detik bukan
hasil riset pengguna; belum ada sesi usability dengan sales sungguhan.

## Riset Mobbin MCP

Diperiksa: **5 flow dan 7 screen**, dari 6 pencarian yang masing-masing fokus satu pertanyaan.
Flow dinilai dari preview yang dikembalikan MCP (sampel beberapa langkah), bukan klaim telah
mengoperasikan produk tersebut atau melihat semua langkah intermediate. Tidak mengunduh
aset atau menyalin brand. Referensi awal lima screen di UX_DESKTOP_RESEARCH.md tetap berlaku.

| Referensi | Yang benar-benar terlihat pada preview | Penerapan / yang tidak diambil |
| --- | --- | --- |
| [Pipedrive — Setup guide](https://mobbin.com/flows/d3a47328-3a55-4659-a7ab-80cd09ec34be) | Kelompok tugas setup, progres, tombol ke aktivitas terkait, bagian lanjutan terlipat. | Panduan tiga langkah yang bisa ditutup/dibuka. Tidak menambah checklist setup akun atau progres palsu. |
| [Apollo — Onboarding hub](https://mobbin.com/flows/82115006-b783-44f9-8638-7fd6dd43d298) | Recommended setup dengan satu tugas terbuka dan CTA; konten eksplorasi terpisah. | Tugas utama diberi satu CTA. Tidak mengambil reward, upsell, dan navigasi panjang. |
| [HubSpot — Sending an email](https://mobbin.com/flows/e5e8d83d-30b2-4f04-b971-968964b1c6f7) | Record kontak tetap menjadi konteks ketika composer dibuka. | Nama deal tetap terlihat; rencana dibuka dari deal terpilih. Tidak menambahkan tombol Send karena API belum mendukungnya. |
| [Attio — Composing an email](https://mobbin.com/flows/582cf0af-91c5-44b0-8df2-4c335203c5a6) | Empty state dengan CTA, composer terfokus, informasi penerima/isi, feedback sesudah tindakan. | Modal persiapan dan feedback salin yang spesifik. Bukan meniru pengiriman email atau status tugas selesai. |
| [ClickUp — Creating a task](https://mobbin.com/flows/4132f63b-0377-47ba-a79f-7a5f626a21e8) | Form tugas terfokus, nama/deskripsi, assignee, properti opsional, hasil berupa detail tugas. | Owner, tindakan, target dan syarat dipisah secara visual. Tidak membuat form due date atau persistensi tugas yang tidak ada. |
| [Unify — Tasks](https://mobbin.com/screens/cc79cbb0-992e-4584-bb91-755cf5ec91ea) | Daftar tugas dengan priority, assignee dan deskripsi; baris kerja ringkas. | Antrean ringkas dengan satu pilihan aktif. Tidak menambah filter atau kolom untuk sekadar lima deal. |
| [HubSpot — Open tasks](https://mobbin.com/screens/46f872bc-5277-412c-bea3-482bf03ff2a0) | Filter tugas, daftar kerja, CTA membuat/memulai tugas. | CTA bekerja harus lebih jelas daripada tombol inspeksi. Filter lanjutan tidak dibawa ke overview. |
| [Zoho CRM — Activities](https://mobbin.com/screens/52ca76be-1b95-4f34-bd3c-aa0eab83cdb8) | Aktivitas ditautkan ke record, pemilik, status dan waktu. | Pertahankan hubungan tindakan–deal–owner. Tidak mengarang deadline/tugas overdue dari umur tahap deal. |
| [ChatGPT — Answer and sources](https://mobbin.com/screens/73833b79-1dd5-4354-8fc4-a2e99c33a75e) | Jawaban di area utama, sumber/aktivitas di panel terpisah. | Bukti dibuka sesuai kebutuhan sambil mempertahankan konteks keputusan; tidak membuat chat sebagai pintu masuk wajib. |
| [Gemini Notebook — Sources and workspace](https://mobbin.com/screens/b102da47-7fa9-4356-8b85-493a5eab06e7) | Sumber, percakapan dan hasil kerja dipisah dalam panel. | Bedakan bukti, usulan, dan rencana. Tiga kolom permanen ditolak karena mempersempit desktop laptop. |
| [Retool — Workflow](https://mobbin.com/screens/e3b951fe-fa7d-4f92-82da-a4e45bf024da) | Node terhubung, detail kode dan blok di sisi canvas. | Ambil koneksi yang bisa diperiksa; tolak kode/configuration terbuka untuk pengguna sales. |
| [Langdock — Workflow](https://mobbin.com/screens/354a7252-81c1-4d4d-b523-b081fa98bd10) | Canvas nodes terfokus, konfigurasi node terpilih di sisi kanan dan feedback perubahan. | Fokus jalur relevan lalu buka sumber. Tidak mengubah context graph menjadi editor workflow yang bisa dijalankan. |

## Prinsip yang dipakai

- NN/g menyarankan fungsi utama didahulukan dan detail sekunder dimunculkan saat diminta.
  Di sini overview menjawab target dan syarat; proposal lengkap, provenance, metode dan
  eksplorasi tersedia setelah pilihan pengguna. [Progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
- Label dan petunjuk kontekstual mengurangi kebutuhan mengingat istilah atau langkah.
  Panduan menyebut apa yang harus dilakukan pada layar yang sedang terbuka.
  [Recognition and recall](https://www.nngroup.com/articles/recognition-and-recall/)
- Modal memindahkan fokus ke judul, menahan Tab/Shift+Tab di dalamnya, ditutup dengan Escape,
  dan mengembalikan fokus ke pemicu. Native dialog plus wrap eksplisit digunakan dan diuji.
  [W3C modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)

Referensi memberi dasar pola. Pilihan layout, copy dan durasi animasi berikut merupakan
keputusan desain untuk DealCompass, bukan hasil eksperimen produk referensi.

## Alur final

1. **Masuk:** panduan singkat Pilih deal → Pahami langkahnya → Siapkan tindak lanjut.
   Panduan bisa ditutup dan dibuka lagi; tidak menghalangi pekerjaan dengan onboarding modal.
2. **Pilih:** urutan API tetap; nama deal, tahap, nilai tahunan dan badge relevan terlihat.
   Peringkat bukan peluang closing. Pilihan pengguna tetap dipertahankan.
3. **Pahami:** judul tugas singkat, nama pemilik, target API, dan batas tindakan. Judul hanya
   menerjemahkan nilai gate API yang dikenali, bukan klasifikasi atau ranking baru. Gate
   tidak dikenali memakai judul generik; hasil analisis ulang tidak mewarisi judul prioritas lama.
4. **Siapkan:** satu CTA membuka rencana. Usulan utuh, target, persetujuan dan ketidakpastian
   spesifik bisa dibaca sebelum menyalin. Nama karyawan hanya dari record yang cocok.
5. **Salin:** output memuat seluruh action/approval/unknowns asli, snapshot, mode, preseden,
   source file/ID/date/type. Pesan berhasil mengatakan disalin, bukan dikirim atau dikerjakan.
   Clipboard ditolak → teks dipilih agar dapat disalin manual. Tidak ada data ditulis ke CRM.
6. **Periksa bila perlu:** alasan → kutipan pelanggan → record asli → titik/relasi graph.
   Graph default memfokuskan jalur API; navigasi dari suatu sumber tetap mengutamakan sumber
   tersebut. Garis inferred tetap dibedakan, panah asli dan provenance dipertahankan.

## Inventaris layar, komponen dan state

| Area | Keputusan final | Bukti / status |
| --- | --- | --- |
| Header/panduan | Petunjuk kontekstual, tiga langkah, dapat ditutup | Implementasi baru; browser |
| Antrean | 276 px desktop, surface tenang, pilihan aktif jelas, no KPI dekoratif | Diperbaiki; API order tests |
| Overview | Satu tugas utama, owner, target, batas; primary action persiapan | Baru; P01–P05 browser + render |
| Usulan lengkap | Disclosure, teks asli dan syarat tersedia | Dipertahankan; regression tests |
| Rencana | Modal dengan tindakan/target/conditions dan export opsional | Baru; render, keyboard, success UI |
| Bukti/alasan | Percakapan penyebab di awal, empat record per halaman, preview singkat | Diperbaiki; record asli via drawer |
| Preseden | Satu keputusan dibuka sesuai kebutuhan | Dipertahankan; bukan approval deal baru |
| Inspector sumber | Label manusiawi, tanggal/pengirim, JSON opsional, route ke graph | Dipertahankan; browser I0335 |
| Graph | Jalur API default; kontrol tampilan dan pencarian lanjutan terlipat | Diperbaiki; source focus 3 node P04 |
| Semua bukti | Search bahasa pengguna, no-results dengan hapus pencarian | Diperbaiki; empty/recovery diperiksa |
| Metode & diagnostic | Tetap di eksplorasi, data/fakta/inferensi/unknown terpisah | Dipertahankan; render tests |
| Rincian teknis | Backend mode, request dan JSON tetap dapat diaudit | Dipertahankan; bukan layar awal |
| Loading/error | Loading nyata, retry per-resource, tidak mengganti gagal dengan sukses | Dipertahankan; nyata 502 → retry pulih |
| Navigasi panjang | Nama deal dan tab sticky di desktop | Baru; mencegah kehilangan konteks |
| Aksesibilitas | Fokus terlihat, dialog labels, keyboard wrap, Escape, reduced motion | Uji terarah; bukan audit WCAG penuh |

## Micro-interactions

Transisi masuk 180 ms dan tekanan tombol 1 px hanya jika tidak meminta reduced motion.
Hover/selected tidak bergantung pada animasi untuk pemahaman. Fokus berpindah ke konteks baru,
loading tetap diberi teks, tombol salin berubah saat pending dan memberi status spesifik.
Tidak memakai confetti, typewriter, carousel, motion graph terus-menerus, atau progress sukses
palsu. Tidak menambah library animasi/dependency.

## Verifikasi dan batas

- 77 frontend tests: 31 helper/graph/session/presentation + 46 transport/render; build lulus.
- Browser: overview lima deal, P02 approval, P04 consent, modal P02/P04, copy-success UI,
  focus wrap dua arah, Escape/focus return, sumber I0335 → graph sumber spesifik, pencarian
  tanpa hasil, dan pemulihan error nyata setelah backend lokal mati.
- 1440×900 desktop; 1280×720 CSS px melalui viewport harness iframe aplikasi nyata.
  Tidak ada overflow horizontal; footer modal pada laptop berada dalam viewport.
- Clipboard API resolved dan status sukses diuji. API clipboard alat browser mengembalikan
  string kosong ketika mencoba membaca ulang; isi clipboard OS lintas aplikasi belum bisa
  diverifikasi melalui alat tersebut. Isi export diuji lengkap terhadap API di unit/render tests.
- Tidak ada Jev live, pengiriman pesan, simpan task CRM, atau perubahan status deal.
- Tidak ada usability test sales manusia, ukuran peningkatan closing, audit WCAG penuh,
  atau pengujian mobile baru. Hasil ini siap dicoba, bukan jaminan juara atau klaim terbaik universal.

## Rehearsal pengguna baru (5 menit)

Tanpa memberi petunjuk UI, minta rekan: “Pilih deal yang perlu dikerjakan lebih dulu. Jelaskan
apa yang ingin dicapai dan siapa pemiliknya. Siapkan rencananya. Tunjukkan alasan kita tidak
langsung memperkenalkan referensi. Lalu tunjukkan apakah diskon Teras Kafe sudah disetujui.”
Catat waktu, bantuan yang diperlukan, salah klik, dan salah tafsir. Ulangi satu tugas dengan
panduan ditutup. Perbaiki titik ragu yang teramati; jangan menambah fitur untuk menutupi kebingungan.
