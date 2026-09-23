# Step 18H offline evaluation (`18h-v1`)

This directory is a separate, versioned benchmark for the current UniTrust
pipeline. It is **not** Step 13, and it does not rewrite or re-run frozen
Step 13 assets.

## Scope

The benchmark measures four explicitly separate diagnostic strata:

- `REVIEWED_SOURCE_DERIVED`: one curated Vietnamese paraphrase per reviewed
  obligation (maximum 18), with labels fixed from REVIEWED/GOLD annotations.
- `CONTROLLED_SYNTHETIC_CONFLICT`: deterministic seven-day deadline changes
  that retain the reviewed obligation's action.
- `UNSUPPORTED_DIAGNOSTIC`: plausible claims checked against the reviewed
  corpus before labelling as insufficient evidence.
- `SAFETY_STRESS`: action-incompatible reviewed obligations injected through
  an evaluation-local retriever and repository. This measures the
  applicability gate, not natural retrieval.

Source-derived paraphrases are curated source-derived text, not collected
real-user messages. Expected labels are set before system execution; system
output is never used to label a case.

## Reproduction

From the repository root, with the locally prepared E5 model and accepted B7
cache present:

```powershell
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
.venv\Scripts\python evaluation/step18h/run_evaluation.py
```

The runner reads the production corpus and published dense cache. It refuses
to rebuild the cache, makes no network/OCR/LLM calls, and writes only the
three files under `evaluation/step18h/reports/`.

## Deliberate limits

There is no overall accuracy headline, amount accuracy (reviewed amount N=0),
temporal accuracy (zero confirmed transitions), OCR accuracy, public-web URL
accuracy, or independent `PARTIALLY_VERIFIED` quantitative benchmark.

Step 13 metrics are historical baseline only. Different inputs make the two
benchmarks non-comparable as a longitudinal performance series.
