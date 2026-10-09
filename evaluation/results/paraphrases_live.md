# Synthetic paraphrase evaluation

Run: 2026-10-09T22:28:15.317184+00:00
Live: True. Rules 6/12; Jev 10/12.

| Case | Message | Expected | Rules | Jev |
|---|---|---|---|---|
| PAR-01 | Pak Teddy merasa KasirPro lebih ramah di kantong. | harga | bukti_kurang | tanpa_hambatan |
| PAR-02 | Biaya langganan ini sulit masuk alokasi dana kami. | harga | bukti_kurang | harga |
| PAR-03 | Paket pesaing lebih terjangkau untuk usaha kami. | harga | bukti_kurang | harga |
| PAR-04 | Harganya terlalu mahal dibanding KasirPro. | harga | harga | harga |
| PAR-05 | Harga sudah cocok, tinggal menunggu referensi pelanggan serupa. | referensi | referensi | referensi |
| PAR-06 | Bukan anggaran yang menghambat. Kami masih menunggu pengambil keputusan yang baru. | pengambil_keputusan | harga | pengambil_keputusan |
| PAR-07 | Harganya sudah sesuai dan kami tidak punya keberatan. Terima kasih. | tanpa_hambatan | tanpa_hambatan | tanpa_hambatan |
| PAR-08 | Kami membutuhkan modul apotek untuk sembilan klinik. | kebutuhan_produk | kebutuhan_produk | kebutuhan_produk |
| PAR-09 | Kami masih mempertimbangkannya. | bukti_kurang | bukti_kurang | bukti_kurang |
| PAR-10 | Saya mengusulkan diskon 20%. Mohon keputusan VP Sales; belum ada persetujuan. | harga | harga | pengambil_keputusan |
| PAR-11 | Bisa pertemukan kami dengan pelanggan yang sudah memakai sistem ini? | referensi | bukti_kurang | referensi |
| PAR-12 | Saya hanya mengecek teknis; keputusan pembelian ada pada kepala operasional. | pengambil_keputusan | bukti_kurang | pengambil_keputusan |

## Full E15 workflow

```json
{
  "status": "not_run",
  "reason": "No dataset-derived context transmitted. This run evaluates message classification only."
}
```

## Usage

This run: 5914 input / 970 output tokens.

## Limits

- Developer-labelled diagnostic set, not independent holdout.
- One observation per case; no stability or production accuracy claim.
- E15 rules benchmark remains separate; no closing-time claim.

## Interpretation and next change to evaluate

- Jev matched 10/12 predeclared labels; rules matched 6/12. Five rules misses were corrected by Jev; one correct rules result became a Jev miss (PAR-10).
- PAR-01 (the E15 idiom): expected harga; rules bukti_kurang; live Jev tanpa_hambatan. E15 is NOT resolved.
- PAR-10: the criteria explicitly include discount requests under harga, but live Jev selected pengambil_keputusan. A discount approval request must be distinguished from uncertainty about decision-maker identity.
- Next experiment: clarify these category boundaries in a separate candidate prompt, retain this baseline, and evaluate untouched paraphrases as well as negative controls. Do not change production rules or claim 100% accuracy from this sample.
- This is the production Choice prompt/criteria evaluated on isolated synthetic messages, not an end-to-end hybrid recommendation benchmark. Approval preservation was not exercised by this live run.
