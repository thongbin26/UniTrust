# Step 18H Post-Fix Development Comparison

## 1. Purpose

Measure the two narrow verification-safety fixes against the unchanged 18h-v1 inputs.

## 2. Methodological Warning

> **THIS IS A SAME-SET DEVELOPMENT COMPARISON, NOT AN INDEPENDENT TEST SET.**

The product fixes were selected using pre-fix 18h-v1 failures. These results establish causal regression coverage, not independent performance or generalization.

## 3. Product Fixes Under Evaluation

1. Reviewed normalized official deadline takes precedence over a raw range's first date.
2. Explicit normalized action incompatibility cannot be overridden by raw lexical fallback.

## 4. Frozen Pre-Fix Baseline

- Pre-fix run: `18h-v1`
- Post-fix run: `18h-v1-postfix-dev`
- Inputs: 49 immutable v1 cases
- Pre-fix commit: `37ef617bc1a84e5acc8094d84f4757064340930d`
- Post-fix commit: `70f5fd6f174663ee697d0fae91009f120e192d9e`

## 5. Post-Fix Same-Set Results

Post-fix source-derived outcome distribution: {'VERIFIED': 16, 'PARTIALLY_VERIFIED': 0, 'CONFLICT': 0, 'INSUFFICIENT_EVIDENCE': 2}.

## 6. Before / After Comparison

| Metric | Pre-fix v1 | Post-fix same-set | Delta |
|---|---:|---:|---:|
| Positive VERIFIED | 11 | 16 | +5 |
| Positive CONFLICT | 5 | 0 | -5 |
| Positive INSUFFICIENT | 2 | 2 | +0 |
| Positive expected-outcome rate | 61.11% | 88.89% | +27.78% |
| Unsupported safe abstention | 88.89% | 100.00% | +11.11% |
| Unsupported PARTIALLY_VERIFIED | 1 | 0 | -1 |
| Cross-obligation false conflicts | 0 | 0 | +0 |
| Retrieval Hit@1 / Hit@3 / MRR | 0.8889 / 1.0000 / 0.9444 | 0.8889 / 1.0000 / 0.9444 | same product retrieval |

## 7. Five Range-End Cases

| Case | Pre-fix | Post-fix |
|---|---|---|
| step18h-positive-001 | CONFLICT | VERIFIED |
| step18h-positive-002 | CONFLICT | VERIFIED |
| step18h-positive-003 | CONFLICT | VERIFIED |
| step18h-positive-005 | CONFLICT | VERIFIED |
| step18h-positive-016 | CONFLICT | VERIFIED |

## 8. Unsupported False-Assertion Case

`step18h-unsupported-001`: pre-fix `PARTIALLY_VERIFIED`, post-fix `INSUFFICIENT_EVIDENCE`.

## 9. Deferred Top-1 Limitations

`positive-009` and `positive-012` remain explicitly classified as deferred top-1 limitations when their post-fix outcome remains insufficient evidence.

## 10. Deferred Same-Action Ambiguity

`conflict-011`, `conflict-012`, `conflict-013`, and `conflict-015` remain explicitly classified as deferred ambiguity limitations when they safely abstain.

## 11. Retrieval / Extraction Stability

Retrieval: N=18, Hit@1=0.8889, Hit@3=1.0000, MRR=0.9444. Action extraction: 18/18; deadline extraction: 12/12.

## 12. Safety Stability

Cross-obligation false conflicts: 0/7. New regressions: 0.

## 13. New Regression Check

New regression case IDs: [].

## 14. Limitations

The comparison remains same-set development evidence. Top-1 retrieval misses and same-action ambiguity are deliberately deferred. No OCR accuracy, public-web accuracy, temporal accuracy, or independent PARTIALLY_VERIFIED benchmark is claimed.

## 15. Competition Reporting Guidance

Use safety properties, retrieval metrics, and scoped latency as primary evidence. Treat the same-set before/after result only as technical causal evidence.

## 16. Claims We Can Make

On the same frozen 18h-v1 development cases, the targeted fixes changed the documented failure mechanisms while preserving the specified safety checks.

## 17. Claims We Cannot Make

This does not establish independent accuracy, real-world generalization, or an unbiased post-fix benchmark result.

## 18. Reproduction

Run `.venv\Scripts\python evaluation\step18h\postfix\run_postfix_evaluation.py` with local artifacts and `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`. The runner writes only `evaluation/step18h/postfix/reports/`.
