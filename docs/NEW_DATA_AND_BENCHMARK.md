# New data, public access and evaluation

Updated 10 October 2026, WIB. Integrator, PR #36.

## What a sales user does

Open **Your data** → download **example JSON** or **CSV + transcript kit** → replace
example records → upload → **Validate data** → inspect the summary → **Open workspace**.
The first-visit tour explains the priority queue, next action, evidence/graph and
upload. **Quick tour** replays it. The desktop interface uses light mode.

CRM and conversations are joined by stable account/contact/employee IDs. Each
workspace rebuilds its own context graph, ranking, findings and recommendations.
The built-in P01–P05 dataset remains unchanged at its 2026-10-01 snapshot. Uploaded
workspaces use their supplied snapshot and arbitrary valid entity IDs. A changed
conversation changes the analysis fingerprint; a changed deal value can change
its priority. Uploading a revision creates a new isolated workspace, not an append
to the public demo. Return to demo is always available.

## Formats and boundaries

- JSON: `{name, snapshot_date, tables}`. Tables use the canonical filenames and
  columns in the downloadable template; values are strings or whole numbers.
- ZIP: canonical CSV tables, `interactions.jsonl`, and `manifest.json` at the root.
  Manifest contains `name` and `snapshot_date`. No folders or arbitrary filenames.
- Core: accounts, deals and employees; contacts/conversations provide useful
  evidence. Optional decision history, support, usage and product tables preserve
  their existing provenance. Missing sources are explicitly missing.
- 1–20 open deals, one open deal per account, 2,000 rows total, 2 MB upload,
  8 MB decompressed ZIP. Transcripts are text records, not PDF/audio ingestion.
- Columns and enum values remain the canonical dataset format (for example,
  `status=Terbuka`, `stage=Negosiasi`, account `tipe=prospek`). UI labels are English;
  original source text is preserved for audit. This is not an arbitrary CSV mapper.
- KasirNusa pricing, packages, IDR thresholds and >10% VP Sales approval policy
  still apply. New data does not train a model or infer another company's policy.
  Rules use the existing language patterns; arbitrary-language accuracy is not
  claimed. Jev can assist when explicitly enabled and available.

## Storage, consent and public operation

Production is configured with `DEALCOMPASS_PUBLIC_ACCESS=1`: no login required.
Upload records live on `/data/uploads`, separate from original sources. A random
workspace handle is kept in this browser tab's session storage and passed in the
`X-DealCompass-Workspace` header. No public workspace directory is exposed.
Access expires after 24 hours; expired directories are cleaned during later
uploads. Keep the original file. This is a temporary demo workspace, not account
management, team sharing, or an enterprise access-control system.

Upload validation and default analysis use rules. **Use Jev with this upload** is
explicit opt-in: relevant transcript/evidence text is sent to TypeSafe only after
that choice. Uploaded analysis caches are scoped to their workspace. All paid
calls still share the existing persistent team usage ledger and 100M input-token
budget. No second ledger, counter reset, or API key reaches the browser.

Public mode caps write requests at 60/minute and imports at 6/minute for the single
process; at most 40 stored workspaces. Cached analysis is reused even when a public
request asks to refresh. These are demo controls, not a distributed abuse system.

## Reference and what was actually evaluated

Reference: [Endgame-Labs/SalesTranscriptQA](https://github.com/Endgame-Labs/SalesTranscriptQA#readme).
It evaluates answers grounded in sales-call transcripts, including questions that
require multiple calls from an opportunity. Its stable IDs, evidence spans and
separation of question/answer labels from retrieval data inform our test design.
Its reported accuracy is **not** DealCompass accuracy. We did not import its full
corpus, run its benchmark, or reproduce its published scores.

Current tests use explicitly fictional CRM/conversations derived from our template:

- unseen account, owner, contact and deal IDs plus a different snapshot;
- source/edge IDs resolve and approval requests never become approvals;
- changed conversation changes the fingerprint and approval-related result;
- changed annual value changes a two-deal ranking;
- six-deal ranking and findings remove old fixed-five assumptions;
- concurrent workspace reads remain isolated and the original demo stays at five;
- upload consent defaults to no provider export, even when server mode is Jev;
- ZIP round-trip, malformed references/dates/IDs, oversized files and path traversal;
- frontend API validators accept one/six new deals with the correct snapshot.

These are functional regression tests, not statistical accuracy or sales-outcome
benchmarks. A future SalesTranscriptQA evaluation must keep answer labels out of
retrieval, use a held-out question set, measure answer/evidence correctness and
multi-call consistency, report failures and token usage, and respect dataset terms.
No conversion uplift or predicted closing probability is claimed.

## Explain it to the mentor

“Data lomba adalah demo awal, bukan jawaban yang ditulis tetap. Kita bisa upload CRM
plus percakapan baru menggunakan template. Sistem memvalidasi ID, membuat graph dan
menghitung ulang prioritas serta langkah berikutnya untuk workspace itu. Kita sudah
menguji ID baru, tanggal baru, perubahan percakapan, perubahan nilai deal, dan enam
deal sekaligus. Yang masih tetap adalah kebijakan penjualan KasirNusa; belum otomatis
mempelajari kebijakan perusahaan lain atau menerima semua format file.”
