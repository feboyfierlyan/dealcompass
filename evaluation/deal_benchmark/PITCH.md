# Pitch evidence: Deal Acceleration accuracy

10 October 2026. Tested decision engine: `rules+jev/1+5ecd9ec8b69f`.
Inputs/expected checks frozen before execution at source commit29697df.
[Actual results](results/REPORT.md) · [input dataset](input.json) · [frozen labels](cases.json).

## Slide content — copy this with its footnote

**Evidence-backed next actions, tested on new sales cases**

- **16/16** new synthetic cases have resolvable recommendation citations and
  structurally valid supporting graph paths in the deployed Rules + Jev workflow.
- **12/16** meet the predeclared action-family screen.
- **12/16** match the expected explicit VP-approval gate.
- **4/4** relevant challenge cases expose comparison/exception wording;
  the 30-outlet case explains why a 10-outlet Starter pilot cannot be copied directly.
- **11/16** pass every applicable screen, compared with **10/16** for rules alone.

Footnote, keep visible: Internal AI-authored synthetic challenge set, not independent
human gold. Automated template/policy/provenance screens, not overall product
accuracy. Closing uplift and optimal deal ranking have not been measured.

## 40-second spoken explanation

“Kami menguji bukan hanya apakah aplikasi berjalan, tetapi apakah data baru bisa
menghasilkan tindakan yang dapat ditelusuri. Kami membekukan16 kasus sebelum tes:
approval salah orang, keputusan untuk deal lain, pembatalan permintaan, referensi,
dan preseden paket. Semua16 kasus memiliki ID bukti dan jalur graph yang valid.
Pada pemeriksaan otomatis,12 dari16 cocok dengan jenis tindakan yang diharapkan,
dan12 dari16 cocok dengan gate approval. Kami tetap melaporkan kegagalan—termasuk
parafrase yang belum masuk ke Jev. Ini bukti evaluasi decision readiness; kami
belum mengklaim peningkatan closing atau akurasi produksi.”

## What improved, what did not

Rules and deployed hybrid each pass12/16 action-family and12/16 explicit-gate
screens. Hybrid passes all applicable checks on11/16 cases versus rules10/16.
These paired counts do not establish statistical superiority. Jev was applied on
13 cases;3 were not eligible (including the deliberately empty-conversation case).
Thirty provider requests were reported by fresh cloud workflow receipts, using the
existing shared Railway usage ledger. Exact token totals are not exposed by this
benchmark API and are not guessed.

Existing P01–P05 regression results are separate:23/24 rules decision scenarios,
15/15 ranking-rule checks. The simple CRM baseline has the same demo ordering.
Do not claim the graph has already proven a better ranking, or combine overlapping
old/new cases into an unexplained single percentage.

## Prioritized findings (do not hide these in the pitch Q&A)

1. **B10/B11, eligibility:** English discount wording and an Indonesian price
   paraphrase were considered insufficient by rules, so hybrid made0 provider
   requests. The fallback eligibility decision limits Jev's potential benefit.
2. **B07/B14, explicit gate:** unlogged approval claims do not populate the explicit
   approval list. The outputs still deny that a transcript constitutes approval;
   B07 hybrid proposes discovery and B14 proposes normal-price options. This is a
   missing explicit verification/gate signal, not observed unauthorized execution.
3. **B13, time:** the withdrawn old discount request remains active in the
   recommendation. The next-step logic needs to resolve cancellations/conflicts.
4. **B09, negation:** rules treats “no reference needed” as a reference blocker;
   hybrid corrects that case. A human may prefer a concrete follow-up to generic
   discovery, so the action-family result still needs semantic review.

Fixes must preserve these first-run receipts. A rerun after tuning is a development
regression result; obtain another untouched labelled set for generalization claims.
No product-engine code was changed during this experiment.

## External or internal?

**Internal task benchmark is primary:** KasirNusa deal prioritization, next actions,
approvals and precedent departures need labels from the competition's data/policy.
Independent sales/mentor review is stronger than this initial AI-authored rubric.

**SalesTranscriptQA is supplementary:** it provides sales-dialogue questions,
reference answers and evidence spans. DealCompass has no arbitrary QA endpoint,
so a fair run needs a separate adapter and full-domain retrieval corpus. Feeding
only the labelled supporting calls would leak answers. Its corpus is synthetic;
its published scores are not DealCompass scores. Full benchmark not run.
Source: https://github.com/Endgame-Labs/SalesTranscriptQA#readme

**CRMArena-Pro is a workflow reference:** it covers CRM sales/service/CPQ tasks in
a Salesforce environment. This better motivates testing business-task completion,
but its environment/actions differ from our app; we have not run or reproduced it.
Sources: https://www.salesforce.com/blog/crmarena-pro/ and
https://huggingface.co/datasets/Salesforce/CRMArenaPro/blob/main/README.md

## What Bima, Ical and Boy can do before presenting

- Bima and Ical: independently annotate all16 source cases using
  `human_gold_template.json` before reading outputs. If you saw labels already,
  disclose that; use newly authored cases for a genuinely blind review.
- Boy: reconcile disagreements, preserve both annotations, then collect actual
  ratings in `human_review_template.json`. Record failures and citation spans.
- Ask a mentor/sales reviewer for an independent ranking of P01–P05 using
  `human_ranking_template.json`; ties are allowed. No ranking accuracy yet.
- For usefulness, have novices find a deal, prepare its action and explain an
  evidence path. Record task success, seconds and help. No invented time-saving %.

Score only completed identified reviews:
`python -m evaluation.deal_benchmark.human --score PATH_TO_FILLED_REVIEW.json`
Unfilled ratings remain unreviewed, never counted as correct. No independent human
ratings or novice time measurements have been collected in this run.
