# UniTrust V2 Step 13 Evaluation Report

## 1. FILES CREATED
- `scripts/build_step13_benchmark.py`: Generates the controlled and source-derived benchmark using deterministic mutations (offset deadline, fixed alternative location).
- `scripts/run_step13_evaluation.py`: Runs retrieval, verification, and temporal evaluation using the reusable pipeline components without invoking the FastAPI server.
- `scripts/analyze_step13_errors.py`: Processes the output traces to compute precision, recall, F1, accuracy, field metrics, latency, and attributes errors deterministically.
- `tests/test_step13_benchmark.py`: Validates deterministic benchmark generation, accuracy computation, correct zero-support metric handling, and error attribution rules.
- `data/benchmark/step13/controlled_verification.jsonl`: The synthetic benchmark mutations.
- `data/benchmark/step13/source_derived_supported.jsonl`: The natural source-derived evaluation set.
- `data/benchmark/step13/evaluation_traces.jsonl`: Verbose pipeline traces per case.
- `data/benchmark/step13/retrieval_metrics.json`: Layer A output.
- `data/benchmark/step13/verification_metrics.json`: Verification, Temporal, and Latency metrics.
- `data/benchmark/step13/field_metrics.json`: Evaluates per-field performance.
- `data/benchmark/step13/error_analysis.json` & `error_cases.jsonl`: Aggregated error taxonomy counts and detailed cases.
- `docs/STEP13_EVALUATION_REPORT.md`: This report.

## 2. FILES MODIFIED
- No production product files (Steps 1-12) were modified.

## 3. EVALUATION POPULATIONS
- **STEP 7 PRIMARY SOURCE-DERIVED RETRIEVAL BENCHMARK**: N = 58 queries. (The earlier draft incorrectly reported N=29 due to a reporting error based on an arithmetic fraction. The generated query population is exactly 58 queries derived from the 18 exact obligations.)
- **CONTROLLED SYNTHETIC BENCHMARK**: N = 50 verification cases.
- **REVIEWED SOURCE-DERIVED CLAIM SET**: N = 18 exact supported claims from reviewed annotations.

## 4. CONTROLLED BENCHMARK CONSTRUCTION
The `CONTROLLED SYNTHETIC BENCHMARK` is derived strictly from human-reviewed DUT evidence. Deterministic generation rules construct `WRONG_DEADLINE` (adding exactly 4 days to parsed ISO strings), `WRONG_LOCATION` (replacing valid physical locations with "Tầng 2 Thư viện mới"), and an explicit unrelated claim representing `UNSUPPORTED_CLAIM`.
N = 50.

## 5. REVIEWED SOURCE-DERIVED SET
The `REVIEWED SOURCE-DERIVED CLAIM SET` combines fields with explicitly present explicit text (e.g. `[audience_text] [action_text] trước [deadline_text] tại [location_text] và [required_documents]`). The expected state is strictly limited to `VERIFIED`.
N = 18.

## 6. PRIMARY RETRIEVAL METRICS (STEP 7 BENCHMARK)
**Population**: STEP 7 PRIMARY SOURCE-DERIVED RETRIEVAL BENCHMARK (N=58)
- **BM25Plus**: 
  - Hit@1: 0.9310, Hit@3: 1.0000, Hit@5: 1.0000
  - Recall@1: 0.9310, Recall@3: 1.0000, Recall@5: 1.0000
  - MRR: 0.9655
  - Latency: Mean 1.43 ms, Median 1.06 ms, p95 2.53 ms
- **Dense E5**:
  - Hit@1: 0.9310, Hit@3: 0.9655, Hit@5: 1.0000
  - Recall@1: 0.9310, Recall@3: 0.9655, Recall@5: 1.0000
  - MRR: 0.9532
  - Latency: Mean 30.52 ms, Median 27.41 ms, p95 38.64 ms
- **Hybrid RRF**:
  - Hit@1: 0.9483, Hit@3: 1.0000, Hit@5: 1.0000
  - Recall@1: 0.9483, Recall@3: 1.0000, Recall@5: 1.0000
  - MRR: 0.9741
  - Latency: Mean 40.97 ms, Median 30.78 ms, p95 84.39 ms

## 7. VERIFICATION METRICS
**Population 1**: CONTROLLED SYNTHETIC BENCHMARK DERIVED FROM HUMAN-REVIEWED DUT EVIDENCE (N=50)
- **Accuracy**: 0.78
- **VERIFIED**: Precision = 0.7059, Recall = 0.6667, F1 = 0.6857, Support = 18
- **PARTIALLY_VERIFIED**: Precision = null, Recall = null, F1 = null, Support = 0
- **CONFLICT**: Precision = 0.7727, Recall = 0.7727, F1 = 0.7727, Support = 22
- **INSUFFICIENT_EVIDENCE**: Precision = 0.9091, Recall = 1.0000, F1 = 0.9524, Support = 10
- *All four classes strictly retained in schema; zero-support metrics evaluated to null.*

**Population 2**: REVIEWED SOURCE-DERIVED CLAIM SET (N=18)
- **Accuracy**: 0.6667
- **VERIFIED**: Precision = 1.0000, Recall = 0.6667, F1 = 0.8000, Support = 18
- **PARTIALLY_VERIFIED**: Precision = null, Recall = null, F1 = null, Support = 0
- **CONFLICT**: Precision = null, Recall = null, F1 = null, Support = 0
- **INSUFFICIENT_EVIDENCE**: Precision = null, Recall = null, F1 = null, Support = 0

## 8. EXPLICIT FIELD-LEVEL METRICS
Based purely on evaluation traces:
- **Action**: N = 56 | Correct = 44 | Incorrect = 12 | Accuracy = 78.57%
- **Deadline**: N = 52 | Correct = 34 | Incorrect = 18 | Accuracy = 65.38%
- **Audience**: N = 0 (Not implemented in field comparator logic)
- **Location**: N = 0 (Not implemented in field comparator logic)
- **Required Documents**: N = 0 (Not implemented in field comparator logic)

## 9. EXACT END-TO-END LATENCY
Based on per-case `service.verify()` execution timings (zero-shot deterministic path):
- **CONTROLLED SYNTHETIC BENCHMARK (N=50)**:
  - Mean: 31.00 ms
  - Median: 32.66 ms
  - p95: 50.22 ms
- **REVIEWED SOURCE-DERIVED CLAIM SET (N=18)**:
  - Mean: 29.42 ms
  - Median: 30.66 ms
  - p95: 43.43 ms

## 10. TEMPORAL COVERAGE REPORT
**REAL TEMPORAL COVERAGE** (Database state):
- Current Versions: 30
- Historical Versions: 0
- Confirmed Temporal Relations: 0

**SYNTHETIC TEMPORAL BEHAVIOR TESTS** (Mock resolution):
- Evaluated `CURRENT`, `SUPERSEDED_OUTDATED`, and `UNKNOWN`. Verified that the synthetic tests accurately return temporal labels for the service logic.

## 11. ERROR TAXONOMY CONSISTENCY
**Total Failed Cases:** 17
- Controlled Synthetic Errors (N=50, 78% acc) = 11 errors
- Reviewed Source-Derived Errors (N=18, 66.6% acc) = 6 errors
- **Total = 17** (Sums exactly)

**Taxonomy Distribution (N=17):**
1. **ACTION_NORMALIZATION_FAILURE**: 8 (47.06%)
2. **OTHER (Unhandled Fields/Constraints)**: 5 (29.41%)
3. **CLAIM_DECOMPOSITION_FAILURE**: 2 (11.76%)
3. **DATE_NORMALIZATION_FAILURE**: 2 (11.76%) *(Tied for 3rd)*

## 12. DATABASE & ANNOTATION HASH INTEGRITY
- **unitrust.db**:
  - SHA256 BEFORE: `21293A1AE6C2139CEC71FACFF01F2AD2CACB890538DB66CD000A125E0DA562AE`
  - SHA256 AFTER: `E11218854760480C526E743145C3367CB69A29112BCBF118E941651D38DB0E4A`
  - *Are they byte-identical?* **No.**
  - *Integrity Conclusion:* The SQLite file was not byte-identical after evaluation. Row-count and read-only workflow checks found no evidence of semantic data mutation, but row-by-row identity cannot be proven retrospectively because a pre-evaluation content digest was not recorded.
  - *ROW-COUNT SUMMARY DIGEST:*
    - `alembic_version` count: 1
    - `notices` count: 30
    - `notice_versions` count: 30
    - `temporal_relations` count: 0
    - (`annotation_documents` does not exist as a database table; these are strictly JSON files).
- **Reviewed Annotations (`data/annotations/batch_001/`)**:
  - Evaluated byte-for-byte.
  - BEFORE == AFTER. Hash match perfectly. No alterations occurred.

## 13. AUTOMATED TEST RESULTS
- 54 passed (including 4 new validation tests for benchmark generation/attribution logic, zero-support handling, and deterministic constraints), 1 warning, in 4 minutes 56 seconds.

## 14. GIT STATUS
- Unmodified working tree for all production product files. Only `scripts/`, `docs/`, and `tests/test_step13_benchmark.py` are untracked.

## 15. LIMITATIONS
- Only 10 reviewed notices and 18 reviewed obligations comprise the dataset.
- The evaluation utilizes 0 real historical versions for temporal metrics.
- Missing field comparator logic for Location, Audience, and Required Documents guarantees `OTHER` or `INSUFFICIENT_EVIDENCE` fallback for claims heavily relying on them.
- Accuracy for `action` (78.57%) and `deadline` (65.38%) indicates that stringent literal token matching frequently conflicts with syntactically valid permutations.
