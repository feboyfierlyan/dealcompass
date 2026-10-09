# Dataset Hackathon Context Graphs — PT KasirNusa Teknologi

Dataset sintetis untuk challenge "Context Graphs in Customer Success and Sales Track".
Semua perusahaan, orang, email, dan angka fiktif.

- Periode data operasional: 1 Oktober 2025 – 30 September 2026
- Tanggal snapshot: 1 Oktober 2026
- Log keputusan dan riwayat deal mencakup periode lebih panjang (sejak 2024)
- Format: CSV (UTF-8, koma) dan JSON Lines
- Seperti data perusahaan sungguhan, data ini tidak selalu rapi, lengkap, atau mutakhir. Menghubungkan dan memverifikasi antar-sumber adalah bagian dari tantangan.

## Daftar file

| File | Sumber | Baris | Isi |
| --- | --- | --- | --- |
| `crm_accounts.csv` | CRM | 45 | 40 pelanggan + 5 prospek |
| `crm_contacts.csv` | CRM | 160 | Kontak dan jabatan saat ini |
| `contact_employment_history.csv` | CRM | ±200 | Riwayat jabatan dan organisasi setiap kontak |
| `crm_deals.csv` | CRM | ±25 | Deal baru, renewal, ekspansi (terbuka dan tertutup) |
| `employees.csv` | Internal | 10 | Karyawan KasirNusa (Sales, AM, Produk, Support) |
| `interactions.jsonl` | Email & meeting | 350 | Email eksternal, email internal, catatan meeting |
| `outlets.csv` | Product | 620 | Daftar outlet pelanggan |
| `product_usage_daily.csv` | Product usage | ±226 ribu | Transaksi harian per outlet |
| `feature_usage_monthly.csv` | Product usage | ±1.100 | Pengguna aktif per fitur per bulan |
| `support_tickets.csv` | Support | 640 | Tiket support |
| `bugs.csv`, `releases.csv` | Produk | 4 / 3 | Bug yang diketahui dan rilis aplikasi |
| `features.csv` | Produk | 8 | Fitur dan status roadmap |
| `contracts_billing.csv` | Billing | 40 | Kontrak aktif pelanggan |
| `decision_log.csv` | Log keputusan | 30 | Approval diskon, pengecualian, janji fitur, eskalasi |

## Kamus kolom

### crm_accounts.csv
| Kolom | Keterangan |
| --- | --- |
| account_id | C01–C40 pelanggan, P01–P05 prospek |
| tipe | `pelanggan` atau `prospek` |
| paket | Starter (maks. 10 outlet), Growth (maks. 25), Enterprise (tanpa batas) |
| jumlah_outlet | Outlet aktif (pelanggan) atau rencana outlet (prospek) |
| account_owner_id | `employee_id` pemegang akun |
| champion_contact_id | Kontak champion menurut CRM |
| nps_terakhir | Skor NPS survei terakhir |
| health_score_dashboard | Skor kesehatan dari dashboard saat ini |

### crm_contacts.csv
`contact_id`, `nama`, `email` (email kantor saat ini), `account_id_saat_ini`, `jabatan_saat_ini`.

### contact_employment_history.csv
Satu baris per jabatan. `account_id` terisi bila organisasinya pelanggan/prospek KasirNusa; kosong bila organisasi lain (nama di `organisasi`). `selesai` kosong = masih menjabat.

### crm_deals.csv
`deal_id`, `account_id`, `tipe` (baru/renewal/ekspansi), `stage` (Lead, Discovery, Demo, Proposal, Negosiasi, Closed Won, Closed Lost), `stage_sejak`, `dibuat`, `owner_id`, `outlet`, `nilai_tahunan` (Rp), `status`, `alasan_kalah`, `kompetitor`.

### interactions.jsonl
Satu objek JSON per baris:
`interaction_id`, `tanggal`, `tipe` (`email`, `email_internal`, `catatan_meeting`), `account_id` (kosong bila internal umum), `dari`, `ke` (alamat email), `peserta` (untuk meeting: `contact_id` dan `employee_id` dipisah `;`), `subjek`, `isi`, `membalas_id` (ID interaksi yang dibalas).

### product_usage_daily.csv
`tanggal`, `outlet_id`, `account_id`, `versi_aplikasi`, `jumlah_transaksi` (transaksi yang tercatat di server), `transaksi_offline_tersinkron` (kosong bila outlet tidak memakai mode offline).

### outlets.csv
`outlet_id`, `account_id`, `kota`, `mode_offline_aktif` (ya/tidak).

### feature_usage_monthly.csv
`bulan`, `account_id`, `feature_id`, `pengguna_aktif`.

### support_tickets.csv
`ticket_id`, `dibuat`, `account_id`, `outlet_id`, `pelapor_contact_id`, `kategori` (bug, pertanyaan, permintaan_fitur, integrasi, billing, perangkat, pelatihan), `prioritas`, `status`, `versi_aplikasi`, `judul`, `deskripsi`, `bug_id` (bila sudah ditautkan ke bug), `diselesaikan`.

### bugs.csv / releases.csv / features.csv
Bug yang diketahui tim produk, tanggal rilis tiap versi aplikasi, dan status roadmap fitur (`target_awal`, `target_terkini`).

### contracts_billing.csv
`contract_id`, `account_id`, `paket`, `outlet_kontrak`, `batas_outlet_paket`, `mulai`, `tanggal_renewal`, `harga_per_outlet_bulan` (Rp 350.000), `diskon_pct`, `nilai_tahunan`, `keterlambatan_bayar_12bln`, `decision_id`.

### decision_log.csv
`decision_id`, `tanggal`, `tipe` (diskon, pengecualian, janji_fitur, eskalasi), `account_id`, `deal_id`, `diminta_oleh`, `diputuskan_oleh` (`employee_id`), `keputusan` (Disetujui/Ditolak/Menunggu), `nilai`, `alasan`, `bukti_interaction_id`, `fitur_dijanjikan`, `status_janji`.

Aturan perusahaan: diskon di atas 10% wajib disetujui VP Sales dan dicatat di log ini.

## Penghubung antar-file

- `account_id` menghubungkan CRM, outlet, usage, tiket, kontrak, deal, interaksi, dan log keputusan.
- `contact_id` menghubungkan kontak, riwayat kerja, champion akun, pelapor tiket, dan peserta meeting.
- `employee_id` menghubungkan pemilik akun/deal dan pengambil keputusan; email karyawan ada di `employees.csv`.
- Email eksternal di `interactions.jsonl` adalah alamat yang dipakai saat itu; tidak selalu sama dengan email kontak saat ini.
- `versi_aplikasi`, `bug_id`, dan `feature_id` menghubungkan usage, tiket, bug, rilis, dan roadmap.
