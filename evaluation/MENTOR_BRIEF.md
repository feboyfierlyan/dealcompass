# DealCompass — brief mentor (ICAL-04)

Snapshot bisnis 2026-10-01. Semua angka/ID di bawah berasal dari output aktual
`rank_deals` (`deal-priority-heuristic-v1`, mode rules) dan
`python -m evaluation.baseline_crm` → [results/baseline_latest.md](results/baseline_latest.md).
Klaim yang boleh/tidak boleh dipresentasikan: [DEMO_CLAIMS.md](DEMO_CLAIMS.md).

## 1. Masalah bisnis (bahasa sederhana)

KasirNusa punya lima prospek terbuka P01–P05 (total potensi Rp667,8 jt/tahun).
Sales perlu menjawab tiga hal tiap pagi: **deal mana dikerjakan dulu, apa langkah
konkretnya, dan apa yang belum boleh dilakukan** (misalnya diskon >10% tanpa
approval VP Sales). Jawabannya tersebar di email/meeting, decision log, riwayat
kerja kontak, usage dan tiket — bukan di satu baris CRM.

## 2. Kenapa CRM saja belum cukup

Kami membuat baseline CRM-only yang transparan: hanya `stage`, `nilai_tahunan`,
`umur tahap`, `owner` dari `list_deals()` (data kanonis yang sama).

**Temuan jujur: urutan baseline "tahap lalu nilai" sama persis dengan graph+rules**
(DL-004 > DL-001 > DL-002 > DL-003 > DL-005). Jadi nilai tambah kami **bukan**
"urutan yang lebih benar". Nilai tambahnya ada pada alasan, tindakan, gate dan
sumber:

| Deal | CRM-only melihat | Graph+rules menambahkan (sumber) |
|---|---|---|
| P04 | Negosiasi, Rp147 jt → "dorong tanda tangan" | Pelanggan menunda sampai ada referensi (`interactions.jsonl:I0335`); kandidat C06 Saiyo Group lewat overlap kerja K028–K116, izin kontak belum ada |
| P01 | Proposal, Rp252 jt → "follow up kontak" | Keputusan pindah ke GM Operations baru (`I0343`); kandidat K017 Rina Hapsari (inferred); janji FEAT-07 belum ditepati di perusahaan lamanya (`D-2025-11`, `D-2026-08`) |
| P02 | Demo, Rp63 jt, kompetitor KasirPro → "kirim penawaran" | Keberatan harga (`I0296`), **permintaan** diskon 20% (`I0348`) yang wajib diputus VP Sales E01; 0 log keputusan untuk DL-002; preseden 20% ditolak (`D-2025-02`, `D-2024-02`, `D-2026-04`) |
| P03 | Discovery, Rp37,8 jt → "lanjut discovery" | Pelanggan minta referensi apotek (`I0334`); kandidat C17/C09/C27 dengan usage FEAT-05 Sep 2026; C03 dicek belakangan (6 tiket terbuka) |
| P05 | Lead, Rp168 jt → "kualifikasi" | Tidak ada interaksi: status `insufficient_evidence`, tindakan discovery; tidak ada sumber tambahan (jujur: graph tidak menambah apa pun di sini) |

Ringkasan terukur dari script: gate approval VP Sales terlihat CRM 0 vs graph+rules 1
(P02); hambatan bersumber 4/5 deal; jumlah bukti per deal CRM 2 → graph+rules
10/9/15/23/2 (P04/P01/P02/P03/P05). Ini jumlah bukti, **bukan** skor kualitas.

Baseline lain juga ditampilkan agar pilihan terlihat: "nilai saja" menempatkan P05
(Rp168 jt, belum divalidasi) di rank 2; "paling lama di tahap" menempatkan P02 di rank 1.

## 3. Bagaimana graph memberi alasan dan riwayat

Graph Bima menghubungkan record asli (deal, akun, kontak, interaksi, keputusan, fitur)
dengan edge yang membawa provenance (`direct` vs `inferred`). Setiap alasan ranking
menunjuk path edge asli, misalnya:

- P02: `DL-002 → P02 ← I0348 → email:andi@kasirnusa.id → E01` — permintaan diskon
  ditujukan ke VP Sales; permintaan **bukan** approval.
- P02: `DL-002 → D-2025-02 → DL-006` — owner yang sama (E07) pernah minta 20% untuk
  C23, ditolak; deal itu kalah. `D-2025-06 → DL-007`: pilot Starter tanpa diskon
  disetujui dan menang — satu keberhasilan lama, bukan jaminan.
- P01: `K017 → C01 → D-2025-11 → FEAT-07` — riwayat kerja kandidat pengambil
  keputusan bertemu janji fitur yang belum ditepati (inferensi, perlu konfirmasi).

Path tidak membuat edge baru; validator menolak edge/node palsu dan shortcut (R8).

## 4. Arti ranking

Rank = **urutan perhatian/tindakan sales pada snapshot**, bukan probabilitas closing,
bukan prediksi urutan closing, bukan nilai pelanggan.

1. Tier: `ready` → acceleration (diskor); `insufficient_evidence` → discovery (setelah
   acceleration, tanpa skor).
2. Skor 0–10 = tahap (0–4) + nilai potensi bin (0–3) + hambatan dinyatakan pelanggan
   (0–2) + preseden relevan (0–1).
3. Tie-break: hambatan pelanggan → tahap → nilai → deal_id (determinisme saja).
4. Gate approval/izin **tidak** menaikkan/menurunkan skor dan tidak dihapus rank.

| Rank | Deal | Skor | Tahap | Nilai | Hambatan pelanggan | Preseden | Gate | Owner |
|---|---|---|---|---|---|---|---|---|
| 1 | DL-004/P04 | 8 | 4 | 2 | 2 (I0335 tunda) | 0 | izin referensi C06 | E06 |
| 2 | DL-001/P01 | 8 | 3 | 3 | 1 (I0343) | 1 | identitas K017 inferred | E06 |
| 3 | DL-002/P02 | 5 | 2 | 1 | 1 (I0296) | 1 | approval VP Sales E01 | E07 |
| 4 | DL-003/P03 | 2 | 1 | 0 | 1 (I0334) | 0 | izin referensi | E08 |
| 5 | DL-005/P05 | – | Lead | Rp168 jt | unknown | 0 | discovery belum | E07 |

## 5. Tindakan P01–P05 (ringkas dari Recommendation v1)

- **P04 (E06):** konfirmasi kriteria "pengguna serupa" (I0335), AM E04 cek pengalaman
  terbaru dan tanyakan kesediaan + izin kontak Saiyo Group (C06). Overlap kerja bukan
  bukti saling kenal; industri Resto Padang ≠ Hospitality perlu dicek.
- **P01 (E06):** minta kontak teknis (pengirim I0343) memperkenalkan ke Rina Hapsari
  (K017, inferred). Jangan menjanjikan tanggal FEAT-07.
- **P02 (E07):** jangan tawarkan diskon 20% sebelum VP Sales E01 memutuskan dan mencatat.
  Opsi tanpa diskon: 15 outlet Growth Rp63 jt; pilot ≤10 outlet Starter (Rp42 jt) hanya
  skenario yang butuh persetujuan.
- **P03 (E08):** konfirmasi kriteria; AM cek C17, C09, C27 (FEAT-05 Sep 2026: 22/11/48
  pengguna aktif); C03 belakangan karena 6 tiket terbuka (3 bug, 1 Tinggi).
- **P05 (E07):** jadwalkan discovery: pengambil keputusan, kebutuhan, jumlah outlet, anggaran.

## 6. Jawaban pertanyaan mentor

**Kenapa P04 di atas P01?**
Skor keduanya 8. P04: Negosiasi 4 + nilai 2 + hambatan pelanggan 2 + preseden 0.
P01: Proposal 3 + nilai 3 + hambatan 1 + preseden 1. Tie-break pertama = hambatan yang
dinyatakan pelanggan: I0335 *"Kami tunda dulu sampai ada referensi"* (deal berhenti
sampai syarat dipenuhi) vs I0343 (deal masih bergerak, perlu verifikasi pengambil
keputusan). Ini **pilihan desain**, bukan temuan statistik. Sensitivitas aktual:
tanpa faktor tahap, tanpa hambatan pelanggan, atau nilai ×2 → P01 naik ke rank 1.
Rank 3–5 stabil di semua variasi. Owner keduanya sama (E06), jadi urutan ini
memang menentukan mana yang dikerjakan dulu.

**Kenapa P02 bukan otomatis pertama meski paling lama di tahap (45 hari)?**
(1) Umur tahap tidak dibandingkan lintas tahap: lima deal berada di lima tahap
berbeda (masing-masing 1 deal), tidak ada SLA per tahap, dan diagnostic Bima
`statistical_assessment = not_assessed`. 45 hari di Demo tidak sebanding dengan
30 hari di Negosiasi. (2) Skor P02 5 (Demo 2, nilai 1, hambatan 1, preseden 1).
(3) Langkah utamanya memang **menunggu keputusan VP Sales** atas I0348; rank tidak bisa
dan tidak boleh melompati gate itu. P02 tidak diabaikan: owner E07 berbeda dari E06,
eskalasi ke E01 bisa berjalan paralel. Baseline "paling lama di tahap" memang menaruh
P02 di rank 1 — itu sah sebagai sudut pandang "deal macet", tetapi bukan yang kami pilih.

**Kenapa P05 discovery?**
Tidak ada interaksi P05 dalam sumber; kebutuhan, hambatan dan pengambil keputusan
belum diketahui → `insufficient_evidence`. Rp168 jt adalah potensi CRM yang belum
divalidasi percakapan. Discovery **bukan** peluang buruk/kalah/risiko rendah; skor
tidak dihitung karena faktor pembandingnya unknown, bukan nol. Kasus K05: nilai P05
dinaikkan ke Rp10 miliar secara sintetis tetap discovery.

**Apa batas bobot/heuristik?**
Bobot dan bin dipilih tim, tidak dilatih, belum divalidasi terhadap hasil closing
historis; satu snapshot, tanpa backtest dan tanpa holdout independen. Deteksi
hambatan/tunda leksikal: parafrase sulit seperti E15 *"KasirPro lebih ramah di
kantong"* masih gagal (batas diketahui). Rank 1–2 sensitif terhadap bobot. Nilai =
potensi CRM, bukan pendapatan. Kandidat referensi: kesesuaian, kesediaan, izin null.

**Apa beda business anomaly vs statistical outlier?**
*Business anomaly* (diagnostic Bima) = hambatan/ketidakselarasan yang didukung
percakapan: `price_objection:DL-002:I0296`, `discount_request:DL-002:I0348:20`,
`DL-001:authority:I0343`, `reference_requirement:DL-003:I0334`,
`reference_requirement:DL-004:I0335`; P05 hanya `data_gap`. *Statistical outlier*
butuh distribusi pembanding (per tahap/segmen), metode dan ambang. Dengan 5 deal di 5
tahap, statusnya `not_assessed`, `method/threshold/outlier_deal_ids = null`. Kami
tidak menyebut deal mana pun outlier.

**Apakah ini AI/ML?** Engine yang dipresentasikan adalah rules deterministik di atas
context graph. Adapter Jev (typesafe.ai) ada dan diuji mock/replay; live belum
diverifikasi, jadi tidak diklaim.

**Apa buktinya graph+rules lebih baik dari CRM?** Kami tidak mengklaim lebih akurat.
Yang dapat ditunjukkan: alasan bersumber, gate approval yang tidak terlihat di CRM,
tindakan dengan owner/milestone, dan unknown yang dinyatakan. Dampak bisnis adalah
hipotesis untuk diuji (lihat DEMO_CLAIMS.md).

## 7. Bahan pitching (30 detik)

"Sales KasirNusa melihat lima prospek di CRM, tapi alasan deal macet ada di email,
decision log dan riwayat kontak. DealCompass menyatukan sumber itu dalam context graph,
lalu rules yang transparan memberi urutan perhatian, langkah berikutnya, dan gate yang
tidak boleh dilompati. Contoh: CRM hanya melihat P02 di tahap Demo; DealCompass melihat
ada permintaan diskon 20% yang belum diputus VP Sales, plus tiga keputusan lama atas
diskon 20% yang semuanya ditolak. Setiap alasan bisa diklik sampai record aslinya."
