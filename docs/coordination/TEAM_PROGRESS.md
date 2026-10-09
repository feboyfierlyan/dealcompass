# Progres tim — baseline kesiapan lomba

Snapshot: 9 Oktober 2026 20:28 WIB. Main ea96e23 mencakup BOY-04 PR #22.
PR Bima#23 terlihat menunggu review; ICAL-04 belum diverifikasi. Pekerjaan lokal
anggota tidak diasumsikan. [Bukti review BOY-04](../reviews/2026-10-09-boy04.md).

## Makna angka

**Estimasi kesiapan keseluruhan: 81/100. Boy100/100, Bima90/100, Ical85/100.**
Angka adalah penilaian mentor berbasis bobot deliverable internal, bukan rubric
resmi panitia, jam kerja, persentase baris kode, nilai kemampuan anggota, akurasi
AI, atau peluang juara. Angka anggota tidak dirata-rata untuk menghasilkan total:
kesiapan tim juga mencakup pitch, integrasi final dan submission. Pembobotan ini
baseline perencanaan yang baru ditetapkan, bukan metrik yang sudah diukur sebelumnya.

## Bobot kesiapan tim (jumlah100)

| Area | Bobot maksimum | Kredit saat ini | Dasar / sisa |
|---|---:|---:|---|
| Dataset, ingestion, context graph, provenance |20|20|Implementasi kanonis dan sumber/path sudah diverifikasi |
| Analisis keputusan, policy gate, ranking P01–P05 |20|20|Rules/approval dan ranking merged; bukan validasi akurasi closing |
| API/integrasi engine |15|15|Priorities/diagnostic asli200, R8 ditutup |
| Pengalaman aplikasi dan integrasi UI |20|20|UI ranking/diagnostic merged #22; 52 tes frontend, build dan sampling browser Main |
| Pengujian serta kesiapan operasional demo |10|5|144backend historis/52frontend terbaru/build lulus; restart/runbook final belum |
| Pitch, pembuktian perbandingan dan rehearsal |10|1|Naskah demo BOY-03 ada; paket pembuktian/rehearsal tim belum diverifikasi |
| Paket penyerahan final |5|0|Artefak/link sesuai ketentuan serta bukti penyerahan belum diverifikasi |
| TOTAL |100|81|19poin tersisa: operasional5, pitch9, submission5 |

100 berarti fitur wajib pada scope yang disepakati tampil end-to-end, acceptance
lulus, demo dapat diulang, tim telah rehearsal, dan penyerahan sesuai ketentuan
panitia telah dikonfirmasi. Main masih harus mencocokkan checklist final dengan
brief resmi; bila scope wajib berbeda, perubahan denominator dijelaskan terbuka.
Jev live dipantau terpisah sebagai calon bonus, tidak menjadi alasan menahan core
rules atau mengklaim juara. Jika panitia ternyata mewajibkannya, scope harus direvisi.

## Progres per anggota

- **Boy100/100 pada scope UI yang ditugaskan**: fondasi25, graph+source20,
  analisis/approval15, tes UI10, integrasi ranking+diagnostic20, acceptance UI10.
  BOY-04 VERIFIED/MERGED #22. Ini bukan kesiapan keseluruhan produk100; Boy
  tetap memimpin demo dan memperbaiki bug jika ditemukan saat rehearsal.
- **Bima90/100**: ingestion25, graph/provenance25, diagnostic20, API20. Sisa10
  runbook, smoke dari proses baru/restart dan kesiapan backend demo. Angka berbasis
  deliverable modul, bukan kontribusi personal; revisi API R8 tetap dikreditkan
  kepada pelaksana Ical. BIMA-04 PR #23 menunggu review; tambahan kredit belum diberikan.
- **Ical85/100**: analisis rules30, ranking25, policy/provenance20, evaluasi existing10.
  Sisa15 paket pembuktian/baseline/penjelasan/rehearsal. ICAL-03 dan takeover R8
  selesai; ICAL-04 TODO. Jev: adapter+mock/replay ada, live belum diverifikasi,
  dipantau terpisah dari85poin core.

## Kerjakan paralel sekarang

1. Boy → BOY-04 selesai; sync main dan latihan demo menggunakan frontend/TESTING.md.
   Catat bug nyata saja; tidak ada tugas fitur baru yang perlu dimulai sekarang.
2. Bima → [BIMA-04](../prompts/BIMA-04.md): backend demo/runbook/smoke/restart dan
   ringkasan fenomena data bersumber. Branch baru bima/demo-readiness.
3. Ical → [ICAL-04](../prompts/ICAL-04.md): pembuktian CRM-only vs graph+rules,
   jawaban mentor, keterbatasan/eval; Jev live hanya jika credential/akses tersedia.
   Branch baru ical/evidence-demo-pack.
4. Main review setiap PR saat siap; tidak menunggu tiga PR sekaligus. Semua WAJIB
   handoff .md. Freeze kontrak/metode sementara; perubahan lintas modul ke Main.

UI Boy kini siap untuk rehearsal final. Pekerjaan paralel yang masih tersisa: smoke backend, penjelasan metode, baseline,
ringkasan data, dokumentasi operasional dan pengecekan kesiapan Jev.

## Rencana waktu tim (target internal, bukan jadwal baru panitia)

- Mulai sekarang, 60–90menit: tiga tugas paralel. CP2 tetap jendela20.00–22.00WIB;
  ikuti slot mentor yang diberikan panitia, jangan menunda CP2 menunggu semua fitur.
- Setelah PR siap: Main review/merge bertahap; jalankan integrasi UI+API dan satu
  latihan demo 3–5menit bersama. Boy demo/alur produk, Bima data/graph, Ical alasan
  ranking/policy; semua wajib memahami P02 dan keterbatasan.
- Target sebelum00.00: alur wajib dapat didemokan; sesudahnya utamakan bug,
  rehearsal dan bahan penyerahan, bukan fitur baru yang berisiko.
- 10Oktober07.00–08.00: restart/demo final, verifikasi link/artefak dan backup.
  CP3 08.00–09.00; target internal penyerahan08.30 jika mekanisme panitia memungkinkan,
  deadline yang diberikan pengguna09.00. Konfirmasi detail mekanisme dari brief/panitia.

## Aturan pembaruan

Main memperbarui snapshot setelah verifikasi PR/acceptance, bukan karena anggota
mengatakan selesai. BOY-04 lulus memberi hingga6poin area UI, lalu area operasional,
pitch dan submission naik hanya dengan bukti masing-masing. Satu hasil boleh
mendukung area berbeda tetapi tidak menambah poin dua kali dalam area yang sama.
Laporan ini statis/manual, bukan monitor otomatis. Status runtime deployment,
credential dan submission tidak diasumsikan dari keberhasilan tes lokal.

Riwayat: baseline19:36WIB75/100 → snapshot20:28WIB81/100 (+6 area UI). Bobot lain tetap; Bima/Ical tidak diberi kredit hanya karena PR atau klaim selesai.
