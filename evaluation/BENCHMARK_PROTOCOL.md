# Benchmark protocol: usefulness and accuracy

Owner: Main. 10 October 2026. Current measured evidence:
[scorecard](results/scorecard_latest.md), with machine-readable receipts beside it.

## Does SalesTranscriptQA fit?

[SalesTranscriptQA](https://github.com/Endgame-Labs/SalesTranscriptQA#readme) evaluates
sales-dialogue question answering: single-call questions and two-call B2B questions,
with reference answers, source IDs and evidence spans. Its README explicitly calls
the cohort synthetic and automatically reviewed, not independent human gold.
Gold answers/supporting-call labels must not enter retrieval. It is useful for an
additional transcript QA/retrieval component. It does not supply ground truth for
KasirNusa deal priorities, approval policy or next-best sales actions.

DealCompass currently returns structured deal recommendations, not answers to the
benchmark's arbitrary questions. Feeding its transcripts into our upload screen
and checking HTTP200 would be an ingestion test, not that benchmark. A comparable
external run needs a separate QA/retrieval adapter, full selected-domain corpus,
pinned release, answer submissions and evidence evaluation. We have not run it.
Do not borrow its published accuracy for this project.

## Evidence we can present now

Reproduce without new paid calls:

```bash
DEALCOMPASS_ENGINE_MODE=rules python -m evaluation.run_eval
DEALCOMPASS_ENGINE_MODE=rules python -m evaluation.baseline_crm
python -m evaluation.scorecard
```

- Rules decision scenarios: **23/24**. Seven original-data checks pass; 16/17
  developer-authored synthetic checks pass. E15 remains a recorded failure.
- Ranking conformance: **15/15**, comprising 5 original-data and 10 synthetic
  scenarios. This validates the declared heuristic, not optimal prioritization.
- Demo recommendation integrity: **5/5** for references/account scope/proposal
  labels. Resolving an evidence ID does not establish semantic support of a claim.
- Mock/replay Jev: **11/11** integration cases; excluded from provider accuracy.
- Historical live obstacle-classification diagnostic: **10/12 Jev versus 6/12
  rules** on the same synthetic messages, run at 05:28 WIB on10October. It tests
  message labels only and is not an independent holdout. Raw failures remain in
  `paraphrases_live.json`; no reruns or prompt tuning were used to replace them.

Primary CRM stage/value baseline has the same deal ordering as graph+rules on the
five demo records. The demonstrated gain is the exposed context, approval gate and
traceable reasoning, not a proven improvement in closing prediction. Do not average
these measures into one overall percentage or hide E15 in a 'core accuracy' figure.

## Stronger DealCompass-specific accuracy benchmark

1. Freeze engine/prompt/code before collecting evaluation labels. Split by account
   or opportunity, not random messages, so calls from one deal cannot leak across
   development and evaluation. Include unseen IDs/dates and multi-call cases.
2. Have two people independently annotate source records **without seeing the
   app's output**. Include clear facts, negation, conflicting/stale information,
   missing evidence, discounts above10%, authority, reference consent and precedent
   exceptions. Resolve disagreements with a third reviewer and retain disagreements.
   Team-reviewed labels are useful but are not external expert validation.
3. For each case record: expected obstacle, acceptable next actions, owner, required
   approvals, relevant precedent or explicit absence, exact source spans, node IDs,
   and directed relation paths. Allow several valid next actions; do not force one
   exact wording for a semantically valid recommendation.
4. Run identical frozen cases through CRM-only, graph+rules and graph+Jev. Record
   fallback separately, and report both end-to-end results including fallback and
   the subset actually completed by Jev. Never silently drop failed requests.
5. Report separate measures:
   - **Fact correctness:** supported factual claims / factual claims reviewed.
   - **Citation support:** cited claims actually supported by their cited records /
     cited claims reviewed. A working link is not sufficient.
   - **Graph fidelity:** cited paths with real endpoints, directed edges, provenance
     and correct direct/inferred labels / cited paths reviewed.
   - **Action acceptability:** recommendations satisfying the pre-labelled action,
     owner, evidence and prerequisite rubric / evaluated recommendations.
   - **Policy violations:** unauthorized approval/discount/consent claims / cases
     where the relevant gate applies. Show numerator and denominator, including0.
   - **Precedent handling:** correctly applied precedent or justified departure /
     cases with an annotated precedent decision. Track missing history separately.
   - **Abstention:** correctly asks for missing information on insufficient cases;
     also report unjustified abstention when evidence was sufficient.
   - **Ranking agreement:** compare to independently graded sales priorities using
     nDCG@3 or pairwise agreement, accepting expert ties. This is preference
     agreement, not closing probability or causal revenue uplift.
6. Publish the case count, label origin, split, frozen version, failures, latency,
   provider receipts and exclusions. Keep tuning on a separate development split;
   new tuning requires another untouched evaluation set.

This protocol is prepared; new independent annotations and that evaluation have
not yet been collected. Existing 243 software tests are reliability checks, not a
replacement for human-labelled task accuracy.

## Usefulness: a short test the team can actually run

Recruit five people unfamiliar with the product if available. This is formative
usability evidence, not a statistically powered study. After the onboarding, ask:

1. Find the deal to work on next and explain its main blocker.
2. Identify the owner and prepare a follow-up plan.
3. Open one supporting record and explain its connection in the graph.
4. Recognize a required approval or unconfirmed reference consent.
5. Upload the provided new case and find its recommendation.

Record task completion, elapsed seconds, assistance, wrong claims/actions and one
short difficulty rating. Record failures too. For a comparison with raw CRM/data,
use equivalent cases and counterbalance order to limit learning effects. Do not
claim time saved until the measured paired timings exist. The assistant's browser
smoke test verifies interaction behavior; it is not a novice-user study.

## Suggested pitch, with defensible wording

“Usefulness kami tunjukkan lewat alur prioritas → tindakan → bukti → graph, lalu
kasus baru. Untuk accuracy, kami memisahkan kepatuhan skenario, dukungan bukti dan
kualitas Jev. Rules lulus23/24 skenario keputusan; satu kegagalan tetap dilaporkan.
Jev mengenali10/12 parafrase sintetis, dibanding6/12 untuk rules. Itu belum akurasi
produksi. SalesTranscriptQA relevan untuk QA percakapan; benchmark keputusan kami
harus menilai approval, preseden dan tindakan sales dengan rubric terpisah.”
