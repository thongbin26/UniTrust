"""Run the immutable 18h-v1 inputs against the post-fix product once.

This is deliberately a same-set development comparison.  It imports v1
execution helpers but writes only to ``evaluation/step18h/postfix/reports``.
It never writes cases, annotations, SQLite, or the published retrieval cache.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.step18h import run_evaluation as v1


POSTFIX_ROOT = Path(__file__).resolve().parent
REPORT_DIR = POSTFIX_ROOT / "reports"
PRE_FIX_COMMIT = "37ef617bc1a84e5acc8094d84f4757064340930d"
POST_FIX_COMMIT = "70f5fd6f174663ee697d0fae91009f120e192d9e"
RUN_ID = "18h-v1-postfix-dev"
COMPARISON_TYPE = "SAME_SET_DEVELOPMENT_COMPARISON"
RANGE_END_CASE_IDS = {
    "step18h-positive-001",
    "step18h-positive-002",
    "step18h-positive-003",
    "step18h-positive-005",
    "step18h-positive-016",
}
TOP1_CASE_IDS = {"step18h-positive-009", "step18h-positive-012"}
AMBIGUITY_CASE_IDS = {
    "step18h-conflict-011",
    "step18h-conflict-012",
    "step18h-conflict-013",
    "step18h-conflict-015",
}


def frozen_v1_hashes() -> dict[str, str]:
    """Hashes for every immutable v1 input/report named in the protocol."""
    files = list(sorted(v1.CASE_DIR.glob("*.jsonl"))) + [
        v1.REPORT_DIR / "step18h_v1_metrics.json",
        v1.REPORT_DIR / "step18h_v1_cases.jsonl",
        v1.REPORT_DIR / "STEP18H_EVALUATION_REPORT.md",
        v1.REPORT_DIR.parent / "README.md",
    ]
    import hashlib

    return {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
    }


def read_pre_fix_metrics() -> dict[str, Any]:
    return json.loads((v1.REPORT_DIR / "step18h_v1_metrics.json").read_text(encoding="utf-8"))


def read_pre_fix_traces() -> dict[str, dict[str, Any]]:
    return {
        item["case_id"]: item
        for item in v1.read_jsonl(v1.REPORT_DIR / "step18h_v1_cases.jsonl")
    }


def normalized_verdict(result: Any) -> str:
    return v1.normalized_verdict(result)


def classify_change(case_id: str, pre: dict[str, Any], post: dict[str, Any]) -> str:
    if pre["pass_expected_outcome"] and not post["pass_expected_outcome"]:
        return "NEW_REGRESSION"
    if case_id in RANGE_END_CASE_IDS and pre["predicted_verdict"] == "CONFLICT" and post["predicted_verdict"] == "VERIFIED":
        return "FIXED_FALSE_CONFLICT"
    if case_id == "step18h-unsupported-001" and pre["predicted_verdict"] == "PARTIALLY_VERIFIED" and post["predicted_verdict"] == "INSUFFICIENT_EVIDENCE":
        return "FIXED_FALSE_ASSERTION"
    if case_id in TOP1_CASE_IDS and post["predicted_verdict"] == "INSUFFICIENT_EVIDENCE":
        return "UNCHANGED_RETRIEVAL_LIMITATION"
    if case_id in AMBIGUITY_CASE_IDS and post["predicted_verdict"] == "INSUFFICIENT_EVIDENCE":
        return "UNCHANGED_AMBIGUITY_LIMITATION"
    if post["pass_expected_outcome"]:
        return "UNCHANGED_PASS"
    if post["predicted_verdict"] == "INSUFFICIENT_EVIDENCE":
        return "UNCHANGED_SAFE_ABSTENTION"
    return "PERSISTING_LIMITATION"


def execute_postfix_cases(skip_latency: bool = False) -> tuple[list[dict[str, Any]], list[float]]:
    case_sets = v1.load_case_sets()
    integrity = v1.validate_cases(case_sets)
    if integrity["exact_step13_duplicates"] or integrity["full_title_leaks"]:
        raise RuntimeError(f"Frozen input validation failed: {integrity}")
    pre_traces = read_pre_fix_traces()
    service, decomposer, chunks = v1.build_runtime()
    hybrid = service.retriever
    chunk_by_identity = {(chunk.notice_id, chunk.version_id): chunk for chunk in chunks}
    traces: list[dict[str, Any]] = []
    samples: list[float] = []

    for group_name in ("source_positive", "controlled_conflict", "unsupported"):
        for case in case_sets[group_name]:
            raw = v1.execute_case(case, service, decomposer, hybrid)
            pre = pre_traces[case["case_id"]]
            trace = {
                "case_id": case["case_id"],
                "provenance_type": case["provenance_type"],
                "expected_verdict": case["expected_verdict"],
                "expected_notice_identity": case.get("expected_notice_identity"),
                "pre_fix_verdict": pre["predicted_verdict"],
                "post_fix_verdict": raw["predicted_verdict"],
                "post_fix_retrieved_identities": raw["retrieved_notice_identities"],
                "post_fix_extracted_fields": raw["predicted_fields"],
                "post_fix_field_results": {
                    name: result.state.value
                    for name, result in (service.verify(case["input_text"], top_k=5)[0].field_results.items())
                },
                "post_fix_abstention_reason": raw["abstention_reason"],
                "pass_expected_outcome": raw["pass_expected_outcome"],
                "change_classification": classify_change(case["case_id"], pre, raw),
            }
            traces.append(trace)

    for case in case_sets["cross_obligation_safety"]:
        forced = case["forced_candidate_identity"]
        chunk = chunk_by_identity[(forced["notice_id"], forced["version_id"])]
        obligation = v1.reviewed_obligations()[
            (forced["notice_id"], forced["version_id"], forced["obligation_id"])
        ]["obligation"]
        from app.models.obligation import StudentObligation

        original_retriever, original_repository = service.retriever, service.repository
        service.retriever = v1.ForcedRetriever(chunk)
        service.repository = v1.ForcedObligationRepository(StudentObligation(**obligation))
        try:
            raw = v1.execute_case(case, service, decomposer, service.retriever)
            pre = pre_traces[case["case_id"]]
            traces.append({
                "case_id": case["case_id"],
                "provenance_type": case["provenance_type"],
                "expected_verdict": case["expected_verdict"],
                "expected_notice_identity": case.get("expected_notice_identity"),
                "pre_fix_verdict": pre["predicted_verdict"],
                "post_fix_verdict": raw["predicted_verdict"],
                "post_fix_retrieved_identities": raw["retrieved_notice_identities"],
                "post_fix_extracted_fields": raw["predicted_fields"],
                "post_fix_field_results": {},
                "post_fix_abstention_reason": raw["abstention_reason"],
                "pass_expected_outcome": raw["pass_expected_outcome"],
                "change_classification": classify_change(case["case_id"], pre, raw),
            })
        finally:
            service.retriever, service.repository = original_retriever, original_repository

    if not skip_latency:
        for case in case_sets["source_positive"]:
            for _ in range(3):
                started = time.perf_counter()
                service.verify(case["input_text"], top_k=5)
                samples.append((time.perf_counter() - started) * 1000)
    return traces, samples


def _outcomes(traces: list[dict[str, Any]], provenance: str) -> list[str]:
    return [item["post_fix_verdict"] for item in traces if item["provenance_type"] == provenance]


def post_fix_metrics(traces: list[dict[str, Any]], latency_samples: list[float]) -> dict[str, Any]:
    case_sets = v1.load_case_sets()
    service, decomposer, _ = v1.build_runtime()
    rank_lists = [v1.collapse_identities(service.retriever.search(case["input_text"], top_k=3)) for case in case_sets["source_positive"]]
    retrieval = v1.retrieval_metrics(
        rank_lists,
        [(case["source_notice_id"], case["source_version_id"]) for case in case_sets["source_positive"]],
    )
    source = _outcomes(traces, "REVIEWED_SOURCE_DERIVED")
    conflicts = _outcomes(traces, "CONTROLLED_SYNTHETIC_CONFLICT")
    unsupported = _outcomes(traces, "UNSUPPORTED_DIAGNOSTIC")
    safety = _outcomes(traces, "SAFETY_STRESS")
    action_cases = case_sets["source_positive"]
    deadline_cases = [case for case in action_cases if "deadline" in case["expected_fields"]]
    action_correct = sum(v1.predicted_fields(case["input_text"], decomposer).get("action") == case["expected_fields"]["action"] for case in action_cases)
    deadline_correct = sum(v1.predicted_fields(case["input_text"], decomposer).get("deadline") == case["expected_fields"]["deadline"] for case in deadline_cases)
    return {
        "dataset_composition": {"source_derived_positive_n": len(source), "controlled_conflict_n": len(conflicts), "unsupported_n": len(unsupported), "cross_obligation_safety_n": len(safety)},
        "retrieval": retrieval,
        "source_positive": {"n": len(source), "expected_outcome_rate": source.count("VERIFIED") / len(source), "outcome_distribution": v1.distribution(source)},
        "controlled_conflict": {"n": len(conflicts), "expected_outcome_rate": conflicts.count("CONFLICT") / len(conflicts), "outcome_distribution": v1.distribution(conflicts)},
        "unsupported": {"n": len(unsupported), "safe_abstention_rate": unsupported.count("INSUFFICIENT_EVIDENCE") / len(unsupported), "false_verified_rate": unsupported.count("VERIFIED") / len(unsupported), "false_partially_verified_count": unsupported.count("PARTIALLY_VERIFIED"), "false_partially_verified_rate": unsupported.count("PARTIALLY_VERIFIED") / len(unsupported), "false_conflict_rate": unsupported.count("CONFLICT") / len(unsupported), "outcome_distribution": v1.distribution(unsupported)},
        "cross_obligation_safety": {"n": len(safety), "false_conflict_count": safety.count("CONFLICT"), "false_conflict_rate": safety.count("CONFLICT") / len(safety), "safe_abstention_count": safety.count("INSUFFICIENT_EVIDENCE"), "other_outcomes": v1.distribution(safety)},
        "extraction": {"action": {"n": len(action_cases), "correct": action_correct, "accuracy": action_correct / len(action_cases)}, "deadline": {"n": len(deadline_cases), "correct": deadline_correct, "accuracy": deadline_correct / len(deadline_cases)}},
        "latency": {"measurement_scope": "warmed local text verification; three samples per source-derived case", "samples_ms": latency_samples, "n": len(latency_samples), "p50_ms": v1.percentile(latency_samples, .50), "p95_ms": v1.percentile(latency_samples, .95)},
    }


def comparison_markdown(document: dict[str, Any]) -> str:
    pre, post = document["pre_fix_metrics"], document["post_fix_metrics"]
    def pct(value: float) -> str:
        return f"{value:.2%}"
    def dist(metrics: dict[str, Any], name: str) -> dict[str, int]:
        return metrics[name]["outcome_distribution"]
    range_rows = "\n".join(f"| {case_id} | {document['pre_fix_cases'][case_id]['predicted_verdict']} | {document['post_fix_cases'][case_id]['post_fix_verdict']} |" for case_id in sorted(RANGE_END_CASE_IDS))
    return f"""# Step 18H Post-Fix Development Comparison

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
- Post-fix run: `{RUN_ID}`
- Inputs: 49 immutable v1 cases
- Pre-fix commit: `{PRE_FIX_COMMIT}`
- Post-fix commit: `{POST_FIX_COMMIT}`

## 5. Post-Fix Same-Set Results

Post-fix source-derived outcome distribution: {dist(post, 'source_positive')}.

## 6. Before / After Comparison

| Metric | Pre-fix v1 | Post-fix same-set | Delta |
|---|---:|---:|---:|
| Positive VERIFIED | {dist(pre, 'source_positive')['VERIFIED']} | {dist(post, 'source_positive')['VERIFIED']} | {dist(post, 'source_positive')['VERIFIED'] - dist(pre, 'source_positive')['VERIFIED']:+d} |
| Positive CONFLICT | {dist(pre, 'source_positive')['CONFLICT']} | {dist(post, 'source_positive')['CONFLICT']} | {dist(post, 'source_positive')['CONFLICT'] - dist(pre, 'source_positive')['CONFLICT']:+d} |
| Positive INSUFFICIENT | {dist(pre, 'source_positive')['INSUFFICIENT_EVIDENCE']} | {dist(post, 'source_positive')['INSUFFICIENT_EVIDENCE']} | {dist(post, 'source_positive')['INSUFFICIENT_EVIDENCE'] - dist(pre, 'source_positive')['INSUFFICIENT_EVIDENCE']:+d} |
| Positive expected-outcome rate | {pct(pre['source_positive']['expected_outcome_rate'])} | {pct(post['source_positive']['expected_outcome_rate'])} | {post['source_positive']['expected_outcome_rate'] - pre['source_positive']['expected_outcome_rate']:+.2%} |
| Unsupported safe abstention | {pct(pre['unsupported']['safe_abstention_rate'])} | {pct(post['unsupported']['safe_abstention_rate'])} | {post['unsupported']['safe_abstention_rate'] - pre['unsupported']['safe_abstention_rate']:+.2%} |
| Unsupported PARTIALLY_VERIFIED | {dist(pre, 'unsupported')['PARTIALLY_VERIFIED']} | {dist(post, 'unsupported')['PARTIALLY_VERIFIED']} | {dist(post, 'unsupported')['PARTIALLY_VERIFIED'] - dist(pre, 'unsupported')['PARTIALLY_VERIFIED']:+d} |
| Cross-obligation false conflicts | {pre['cross_obligation_safety']['false_conflict_count']} | {post['cross_obligation_safety']['false_conflict_count']} | {post['cross_obligation_safety']['false_conflict_count'] - pre['cross_obligation_safety']['false_conflict_count']:+d} |
| Retrieval Hit@1 / Hit@3 / MRR | {pre['retrieval']['hit_at_1']:.4f} / {pre['retrieval']['hit_at_3']:.4f} / {pre['retrieval']['mrr']:.4f} | {post['retrieval']['hit_at_1']:.4f} / {post['retrieval']['hit_at_3']:.4f} / {post['retrieval']['mrr']:.4f} | same product retrieval |

## 7. Five Range-End Cases

| Case | Pre-fix | Post-fix |
|---|---|---|
{range_rows}

## 8. Unsupported False-Assertion Case

`step18h-unsupported-001`: pre-fix `{document['pre_fix_cases']['step18h-unsupported-001']['predicted_verdict']}`, post-fix `{document['post_fix_cases']['step18h-unsupported-001']['post_fix_verdict']}`.

## 9. Deferred Top-1 Limitations

`positive-009` and `positive-012` remain explicitly classified as deferred top-1 limitations when their post-fix outcome remains insufficient evidence.

## 10. Deferred Same-Action Ambiguity

`conflict-011`, `conflict-012`, `conflict-013`, and `conflict-015` remain explicitly classified as deferred ambiguity limitations when they safely abstain.

## 11. Retrieval / Extraction Stability

Retrieval: N={post['retrieval']['n']}, Hit@1={post['retrieval']['hit_at_1']:.4f}, Hit@3={post['retrieval']['hit_at_3']:.4f}, MRR={post['retrieval']['mrr']:.4f}. Action extraction: {post['extraction']['action']['correct']}/{post['extraction']['action']['n']}; deadline extraction: {post['extraction']['deadline']['correct']}/{post['extraction']['deadline']['n']}.

## 12. Safety Stability

Cross-obligation false conflicts: {post['cross_obligation_safety']['false_conflict_count']}/{post['cross_obligation_safety']['n']}. New regressions: {document['new_regression_count']}.

## 13. New Regression Check

New regression case IDs: {document['new_regression_case_ids']}.

## 14. Limitations

The comparison remains same-set development evidence. Top-1 retrieval misses and same-action ambiguity are deliberately deferred. No OCR accuracy, public-web accuracy, temporal accuracy, or independent PARTIALLY_VERIFIED benchmark is claimed.

## 15. Competition Reporting Guidance

Use safety properties, retrieval metrics, and scoped latency as primary evidence. Treat the same-set before/after result only as technical causal evidence.

## 16. Claims We Can Make

On the same frozen 18h-v1 development cases, the targeted fixes changed the documented failure mechanisms while preserving the specified safety checks.

## 17. Claims We Cannot Make

This does not establish independent accuracy, real-world generalization, or an unbiased post-fix benchmark result.

## 18. Reproduction

Run `.venv\\Scripts\\python evaluation\\step18h\\postfix\\run_postfix_evaluation.py` with local artifacts and `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`. The runner writes only `evaluation/step18h/postfix/reports/`.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the 18h-v1 same-set post-fix development comparison once.")
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--skip-latency", action="store_true")
    args = parser.parse_args(argv)
    before_hashes = frozen_v1_hashes()
    traces, latency_samples = execute_postfix_cases(skip_latency=args.skip_latency)
    after_hashes = frozen_v1_hashes()
    if before_hashes != after_hashes:
        raise RuntimeError("Frozen v1 inputs or reports changed during post-fix evaluation.")
    pre_metrics = read_pre_fix_metrics()
    post_metrics = post_fix_metrics(traces, latency_samples)
    pre_cases = read_pre_fix_traces()
    post_cases = {item["case_id"]: item for item in traces}
    if set(pre_cases) != set(post_cases):
        raise RuntimeError("Pre-fix and post-fix case IDs do not align exactly.")
    new_regressions = sorted(item["case_id"] for item in traces if item["change_classification"] == "NEW_REGRESSION")
    document = {
        "run_id": RUN_ID,
        "benchmark_input_version": v1.VERSION,
        "comparison_type": COMPARISON_TYPE,
        "pre_fix_commit": PRE_FIX_COMMIT,
        "post_fix_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "frozen_v1_hashes": before_hashes,
        "pre_fix_metrics": pre_metrics,
        "post_fix_metrics": post_metrics,
        "deltas": {
            "positive_expected_outcome_rate": post_metrics["source_positive"]["expected_outcome_rate"] - pre_metrics["source_positive"]["expected_outcome_rate"],
            "unsupported_safe_abstention_rate": post_metrics["unsupported"]["safe_abstention_rate"] - pre_metrics["unsupported"]["safe_abstention_rate"],
            "unsupported_partially_verified": post_metrics["unsupported"]["outcome_distribution"]["PARTIALLY_VERIFIED"] - pre_metrics["unsupported"]["outcome_distribution"]["PARTIALLY_VERIFIED"],
        },
        "fix_validation": {
            "range_end_cases": {case_id: post_cases[case_id]["post_fix_verdict"] for case_id in sorted(RANGE_END_CASE_IDS)},
            "unsupported_false_assertion": post_cases["step18h-unsupported-001"]["post_fix_verdict"],
        },
        "deferred_limitations": {"top1_cases": sorted(TOP1_CASE_IDS), "ambiguity_cases": sorted(AMBIGUITY_CASE_IDS)},
        "new_regression_count": len(new_regressions),
        "new_regression_case_ids": new_regressions,
        "limitations": ["Same-set development comparison, not independent evidence.", "Frozen v1 limitations are retained unless explicitly fixed."],
        "pre_fix_cases": pre_cases,
        "post_fix_cases": post_cases,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "step18h_v1_postfix_dev_metrics.json").write_text(json.dumps({key: value for key, value in document.items() if key not in {"pre_fix_cases", "post_fix_cases"}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "step18h_v1_postfix_dev_cases.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in traces), encoding="utf-8")
    (args.output_dir / "STEP18H_POSTFIX_DEVELOPMENT_COMPARISON.md").write_text(comparison_markdown(document), encoding="utf-8")
    print(json.dumps({"status": "completed", "case_count": len(traces), "new_regression_count": len(new_regressions)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
