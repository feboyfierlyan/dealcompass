# Pembanding CRM-only vs graph+rules ICAL-04 (2026-10-10 08:17 WIB)

Snapshot 2026-10-01; lima deal prospek terbuka dari `list_deals()` (data kanonis sama). Graph+rules = `deal-priority-heuristic-v1` production, mode rules, tanpa Jev.

Field CRM yang dipakai baseline: stage, annual_value, stage_age_days, owner_id.

Sengaja tidak dipakai baseline:

- interactions.jsonl: isi email/meeting (hambatan, permintaan diskon, syarat referensi)
- decision_log.csv: preseden dan approval VP Sales
- crm_contacts.csv + contact_employment_history.csv: pengambil keputusan dan riwayat kerja
- feature_usage_monthly.csv, features.csv, support_tickets.csv: bukti kandidat referensi
- employees.csv: siapa pemegang approval
- crm_deals.kompetitor: kolom CRM yang terlihat tetapi tidak dipakai baseline utama; tidak memuat permintaan diskon atau status approval
- Edge graph/provenance dan diagnostic Bima

## Urutan

| Metode | Urutan | Sama dengan graph+rules |
|---|---|---|
| graph+rules | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | - |
| CRM: Tahap lanjut dulu, lalu nilai potensi terbesar (baseline utama) | DL-004 > DL-001 > DL-002 > DL-003 > DL-005 | ya |
| CRM: Nilai potensi terbesar saja | DL-001 > DL-005 > DL-004 > DL-002 > DL-003 | tidak |
| CRM: Paling lama di tahap saat ini (deal "macet") | DL-002 > DL-004 > DL-001 > DL-003 > DL-005 | tidak |

## Per deal (baseline utama: tahap lalu nilai)

| Deal | Rank CRM | Rank G+R | Tindakan CRM | Hambatan G+R (bukti) | Gate G+R | Owner | Preseden | Bukti CRM→G+R | Path | Sumber tambahan |
|---|---|---|---|---|---|---|---|---|---|---|
| DL-004/P04 | 1 | 1 (acceleration) | Follow up negosiasi dan dorong tanda tangan kontrak. | referensi (interactions.jsonl:I0335) | kesediaan/izin kandidat referensi belum ada | E06 | - | 2→10 | 3 | contact_employment_history.csv, crm_contacts.csv, interactions.jsonl, support_tickets.csv |
| DL-001/P01 | 2 | 2 (acceleration) | Follow up proposal ke kontak yang tercatat. | pengambil_keputusan (interactions.jsonl:I0343) | identitas pengambil keputusan masih inferred | E06 | D-2025-11, D-2026-08 | 2→9 | 6 | contact_employment_history.csv, crm_contacts.csv, decision_log.csv, interactions.jsonl |
| DL-002/P02 | 3 | 3 (acceleration) | Follow up hasil demo dan kirim penawaran harga. | harga (interactions.jsonl:I0296, interactions.jsonl:I0348) | approval VP Sales tertunda | E07 | D-2025-02, D-2025-06, D-2024-02, D-2025-12, D-2026-04 | 2→15 | 6 | decision_log.csv, employees.csv, interactions.jsonl |
| DL-003/P03 | 4 | 4 (acceleration) | Lanjutkan discovery lalu jadwalkan demo. | referensi (interactions.jsonl:I0334) | kesediaan/izin kandidat referensi belum ada | E08 | - | 2→23 | 7 | decision_log.csv, feature_usage_monthly.csv, features.csv, interactions.jsonl, support_tickets.csv |
| DL-005/P05 | 5 | 5 (discovery) | Kualifikasi lead dan jadwalkan kontak pertama. | bukti_kurang (tidak ada) | discovery belum dilakukan | E07 | - | 2→2 | 1 | tidak ada |

## Tindakan graph+rules (Recommendation v1, apa adanya)

- **DL-004** (E06): USULAN: E06 mengonfirmasi kriteria "pengguna serupa" atas permintaan I0335, lalu meminta account manager memeriksa pengalaman terbaru dan menanyakan kesediaan serta izin kontak Saiyo Group (C06, AM E04) sebelum perkenalan ke Nirwana Hotel & Resto.
- **DL-001** (E06): USULAN: E06 meminta kontak teknis memperkenalkan dan menjadwalkan pertemuan langsung dengan Rina Hapsari (GM Operations, identitas inferensi yang perlu dikonfirmasi); sesuaikan proposal dengan prioritas operasional. Jawab jujur status fitur yang belum rilis dan jangan menjanjikan tanggal fitur tanpa keputusan tercatat.
- **DL-002** (E07): USULAN: Jangan menawarkan atau menjanjikan diskon 20% ke Teras Kafe Group sebelum VP Sales memutuskan dan mencatatnya. E07 membawa permintaan tersebut ke VP Sales bersama pembanding preseden. Siapkan opsi tanpa diskon: 15 outlet paket Growth harga normal Rp63.000.000/tahun; pilot sebagian outlet hanya sebagai skenario usulan yang butuh persetujuan. Tanggapi keberatan harga dengan nilai produk berdasar kebutuhan yang tercatat, bukan menyamai harga kompetitor.
- **DL-003** (E08): USULAN: E08 mengonfirmasi kriteria "pengguna serupa" atas permintaan I0334, lalu meminta account manager memeriksa pengalaman terbaru dan menanyakan kesediaan serta izin kontak Apotek Bunda Sehat (C17, AM E05), Apotek Medika Farma (C09, AM E03), Apotek Kimia Sejahtera (C27, AM E04) sebelum perkenalan ke Klinik Pratama Medika. Kandidat lain dicek belakangan karena catatan: C03 (6 tiket terbuka (3 bug, 1 prioritas Tinggi/Kritis; T0521, T0523, T0526, T0566, T0608, T0616; judul: Laporan tidak sesuai/Selisih transaksi/Sinkronisasi)).
- **DL-005** (E07): USULAN: E07 menjadwalkan discovery dengan PT Distribusi Sumber Rejeki untuk mengidentifikasi pengambil keputusan, kebutuhan, jumlah outlet dan anggaran sebelum menawarkan harga atau paket.

## Ringkasan

- Rank berubah vs baseline utama: tidak ada.
- Gate approval VP Sales terlihat: CRM 0, graph+rules 1.
- Deal dengan hambatan bersumber: graph+rules 4/5; CRM tidak membaca percakapan.
- Deal yang mendapat sumber tambahan: DL-004, DL-001, DL-002, DL-003.

## Batas

- Lima deal, satu snapshot; tidak ada label hasil closing sehingga tidak ada klaim akurasi atau uplift.
- Urutan yang sama atau berbeda bukan bukti salah satu metode lebih akurat.
- Tindakan baseline adalah template generik buatan Ical, bukan perilaku CRM atau sales nyata.
- Graph+rules memakai formula production deal-priority-heuristic-v1 tanpa perubahan; bobot tetap pilihan desain.
