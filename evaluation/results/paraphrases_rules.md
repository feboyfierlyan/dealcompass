# Synthetic paraphrase evaluation

Run: 2026-10-09T22:29:04.841559+00:00
Live: False. Rules 6/12; Jev None/12.

| Case | Message | Expected | Rules | Jev |
|---|---|---|---|---|
| PAR-01 | Pak Teddy merasa KasirPro lebih ramah di kantong. | harga | bukti_kurang | not run |
| PAR-02 | Biaya langganan ini sulit masuk alokasi dana kami. | harga | bukti_kurang | not run |
| PAR-03 | Paket pesaing lebih terjangkau untuk usaha kami. | harga | bukti_kurang | not run |
| PAR-04 | Harganya terlalu mahal dibanding KasirPro. | harga | harga | not run |
| PAR-05 | Harga sudah cocok, tinggal menunggu referensi pelanggan serupa. | referensi | referensi | not run |
| PAR-06 | Bukan anggaran yang menghambat. Kami masih menunggu pengambil keputusan yang baru. | pengambil_keputusan | harga | not run |
| PAR-07 | Harganya sudah sesuai dan kami tidak punya keberatan. Terima kasih. | tanpa_hambatan | tanpa_hambatan | not run |
| PAR-08 | Kami membutuhkan modul apotek untuk sembilan klinik. | kebutuhan_produk | kebutuhan_produk | not run |
| PAR-09 | Kami masih mempertimbangkannya. | bukti_kurang | bukti_kurang | not run |
| PAR-10 | Saya mengusulkan diskon 20%. Mohon keputusan VP Sales; belum ada persetujuan. | harga | harga | not run |
| PAR-11 | Bisa pertemukan kami dengan pelanggan yang sudah memakai sistem ini? | referensi | bukti_kurang | not run |
| PAR-12 | Saya hanya mengecek teknis; keputusan pembelian ada pada kepala operasional. | pengambil_keputusan | bukti_kurang | not run |

## Full E15 workflow

```json
{
  "status": "not_run",
  "reason": "No dataset-derived context transmitted. This run evaluates message classification only."
}
```

## Usage

This run: 0 input / 0 output tokens.

## Limits

- Developer-labelled diagnostic set, not independent holdout.
- One observation per case; no stability or production accuracy claim.
- E15 rules benchmark remains separate; no closing-time claim.
