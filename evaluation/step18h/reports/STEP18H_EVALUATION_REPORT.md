# Step 18H Evaluation Report — 18h-v1

## 1. Executive Summary

This is a small, offline, provenance-aware diagnostic of the current UniTrust pipeline. It is not an overall real-world accuracy claim.

## 2. Benchmark Scope

Current production Hybrid RRF retrieval and `VerificationService` were evaluated without product changes, network, OCR runtime, or LLM providers.

## 3. Dataset Composition

- Source-derived positives: N=18
- Controlled deadline conflicts: N=15
- Unsupported diagnostics: N=9
- Controlled action-incompatibility safety stress: N=7

## 4. Provenance / Case Construction

Source positives are **curated source-derived paraphrases** labeled from REVIEWED/GOLD obligations before execution. Conflicts are deterministic +7-day deadline perturbations. Unsupported and safety cases are controlled diagnostics.

## 5. Historical Step13 Baseline

Step13 is frozen historical evidence and was not run. Its retrieval N=58 Hybrid RRF values (Hit@1 0.9483, Hit@3 1.0000, MRR 0.9741) are not comparable with this new query set.

## 6. Step18H New Retrieval Results

On a new source-derived query set (N=18), Hybrid retrieval achieved Hit@1=88.89%, Hit@3=100.00%, MRR=0.9444.

## 7. Source-Derived Positive Verification

On this small source-derived diagnostic set (N=18), expected-outcome rate was 61.11%. Distribution: {'VERIFIED': 11, 'PARTIALLY_VERIFIED': 0, 'CONFLICT': 5, 'INSUFFICIENT_EVIDENCE': 2}.

## 8. Controlled Synthetic Conflict Results

On controlled synthetic deadline perturbations (N=15), expected-outcome rate was 60.00%. This is not real-world conflict accuracy.

## 9. Unsupported / Abstention Results

On unsupported diagnostic claims (N=9), safe abstention rate was 88.89%; false VERIFIED rate was 0.00%; false CONFLICT rate was 0.00%.

## 10. Cross-Obligation Safety Results

On controlled action-incompatibility safety stress cases (N=7), false conflict rate was 0.00%. This forces an action-incompatible reviewed candidate and is not an end-to-end retrieval metric.

## 11. Structured Extraction

Action: N=18, correct=18, accuracy=100.00%. Deadline: N=12, correct=12, accuracy=100.00%. Amount: NOT AVAILABLE (reviewed amount annotations N=0).

## 12. Local Warm Latency

Warmed local text verification only: N=54, p50=26.93 ms, p95=41.15 ms, min=19.91 ms, max=42.05 ms. Not production latency.

## 13. Temporal Coverage

No confirmed real temporal transitions are available; temporal accuracy is not measured.

## 14. OCR Functional Status

One qualification image and functional tests exist; no OCR accuracy benchmark is claimed.

## 15. URL Functional/Security Status

Mocked security/extraction tests and an accepted one-site runtime smoke provide functional/security evidence; no public-web accuracy is claimed.

## 16. Error Analysis

Observable failure classifications: {'FIELD_COMPARISON': 5, 'APPLICABILITY_ABSTENTION': 8, 'UNSUPPORTED_FALSE_ASSERTION': 1}.

## 17. Limitations

Small curated sets, no independent PARTIALLY_VERIFIED ground truth, no reviewed amount support, no temporal transitions, no OCR accuracy, and no public-web accuracy. Latency percentiles were computed from 54 in-run samples, but the current per-case trace does not persist all three timing repetitions, so the stored p50/p95 values cannot be independently reconstructed from the trace alone.

## 18. Claims We Can Make

Only scoped claims with the N and strata above: new-query retrieval, controlled outcome rates, controlled safety rate, extraction results, and local warmed latency.

## 19. Claims We Cannot Make

We cannot claim overall university-announcement accuracy, real-world conflict accuracy, scam detection, OCR accuracy, temporal accuracy, production latency, all-university generalization, universal URL safety, or amount extraction accuracy.

## 20. Reproduction Instructions

Run `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, then `.venv\Scripts\python evaluation/step18h/run_evaluation.py`. The runner reads current production data/cache and writes only this directory's reports.

## Recommended competition-facing metrics

1. Hybrid retrieval Hit@1/Hit@3/MRR on the new source-derived N=18 set.
2. Source-derived positive expected-outcome rate (small-sample diagnostic, N=18).
3. Controlled synthetic deadline-conflict expected-outcome rate (N=15).
4. Cross-obligation false-conflict rate (small-sample safety diagnostic, N=7).
5. Unsupported safe-abstention rate (small-sample diagnostic, N=9).
6. Action/deadline extraction accuracy on source-derived cases.
7. Warmed local text-verification p50/p95 (test-machine measurement).
