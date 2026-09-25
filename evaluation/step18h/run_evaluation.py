"""Offline, provenance-aware evaluation for the current UniTrust pipeline.

This module intentionally reuses the shipped retrieval and verification code
without changing it.  It never writes benchmark inputs, annotations, the
production SQLite database, or the published dense cache.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
CASE_DIR = Path(__file__).resolve().parent / "cases"
REPORT_DIR = Path(__file__).resolve().parent / "reports"
VERSION = "18h-v1"
PROVENANCE_TYPES = {
    "REVIEWED_SOURCE_DERIVED",
    "CONTROLLED_SYNTHETIC_CONFLICT",
    "UNSUPPORTED_DIAGNOSTIC",
    "SAFETY_STRESS",
}
OUTCOME_KEYS = (
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "CONFLICT",
    "INSUFFICIENT_EVIDENCE",
)

# Direct ``python evaluation/step18h/run_evaluation.py`` execution places the
# script directory, rather than the repository root, on ``sys.path``.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def normalize_for_duplicate_check(text: str) -> str:
    """Normalization used only to reject exact textual leakage from Step 13."""
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_case_sets(case_dir: Path = CASE_DIR) -> dict[str, list[dict[str, Any]]]:
    return {
        "source_positive": read_jsonl(case_dir / "source_derived_positive.jsonl"),
        "controlled_conflict": read_jsonl(case_dir / "controlled_deadline_conflict.jsonl"),
        "unsupported": read_jsonl(case_dir / "unsupported_diagnostic.jsonl"),
        "cross_obligation_safety": read_jsonl(case_dir / "cross_obligation_safety.jsonl"),
    }


def step13_input_texts(root: Path = ROOT) -> set[str]:
    """Read frozen inputs only; this runner never executes Step 13 scripts."""
    texts: set[str] = set()
    for name in ("controlled_verification.jsonl", "source_derived_supported.jsonl"):
        for item in read_jsonl(root / "data" / "benchmark" / "step13" / name):
            value = item.get("input_text") or item.get("claim_text")
            if isinstance(value, str):
                texts.add(normalize_for_duplicate_check(value))
    return texts


def case_file_hashes(case_dir: Path = CASE_DIR) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(case_dir.glob("*.jsonl"))
    }


def reviewed_obligations(root: Path = ROOT) -> dict[tuple[int, int, str], dict[str, Any]]:
    items: dict[tuple[int, int, str], dict[str, Any]] = {}
    for path in (root / "data" / "annotations" / "batch_001").glob("*.json"):
        annotation = json.loads(path.read_text(encoding="utf-8"))
        if annotation["annotation_status"] not in {"REVIEWED", "GOLD"}:
            continue
        for obligation in annotation["obligations"]:
            items[(annotation["notice_id"], annotation["version_id"], obligation["obligation_id"])] = {
                "annotation": annotation,
                "obligation": obligation,
            }
    return items


def _date_only(value: str | None) -> str | None:
    return value[:10] if isinstance(value, str) and len(value) >= 10 else None


def validate_cases(
    case_sets: dict[str, list[dict[str, Any]]], root: Path = ROOT,
) -> dict[str, Any]:
    """Validate labels against reviewed evidence before product output is read."""
    reviewed = reviewed_obligations(root)
    frozen_texts = step13_input_texts(root)
    seen: set[str] = set()
    duplicates: list[str] = []
    title_leaks: list[str] = []
    identity_overlaps: set[tuple[int, int]] = set()

    for group, cases in case_sets.items():
        for case in cases:
            assert case.get("benchmark_version") == VERSION
            assert case.get("provenance_type") in PROVENANCE_TYPES
            assert case["case_id"] not in seen
            seen.add(case["case_id"])
            if group == "source_positive":
                if normalize_for_duplicate_check(case["input_text"]) in frozen_texts:
                    duplicates.append(case["case_id"])
                key = (case["source_notice_id"], case["source_version_id"], case["source_obligation_id"])
                assert key in reviewed
                source = reviewed[key]
                obligation = source["obligation"]
                assert case["expected_verdict"] == "VERIFIED"
                assert case["mutation"] is None
                assert case["expected_fields"]["action"] == obligation["action"]["action_type"]
                if "deadline" in case["expected_fields"]:
                    assert _date_only((obligation.get("deadline") or {}).get("normalized")) == case["expected_fields"]["deadline"]
                identity_overlaps.add((case["source_notice_id"], case["source_version_id"]))
                title = normalize_for_duplicate_check(source["annotation"]["title"])
                query = normalize_for_duplicate_check(case["input_text"])
                if title and title in query:
                    title_leaks.append(case["case_id"])
            elif group == "controlled_conflict":
                key = (case["source_notice_id"], case["source_version_id"], case["source_obligation_id"])
                assert key in reviewed
                obligation = reviewed[key]["obligation"]
                mutation = case["mutation"]
                assert case["expected_verdict"] == "CONFLICT"
                assert mutation and mutation["field"] == "deadline"
                assert mutation["original_value"] != mutation["mutated_value"]
                assert case["expected_fields"]["action"] == obligation["action"]["action_type"]
                assert _date_only((obligation.get("deadline") or {}).get("normalized")) == mutation["original_value"]
                assert case["expected_fields"]["deadline"] == mutation["mutated_value"]
            elif group == "unsupported":
                assert case["expected_verdict"] == "INSUFFICIENT_EVIDENCE"
                assert case.get("source_notice_id") is None
                assert case.get("expected_notice_identity") is None
            else:
                forced = case["forced_candidate_identity"]
                source_key = (case["source_notice_id"], case["source_version_id"], case["source_obligation_id"])
                forced_key = (forced["notice_id"], forced["version_id"], forced["obligation_id"])
                assert source_key in reviewed and forced_key in reviewed
                assert case["expected_non_conflict"] is True
                assert reviewed[source_key]["obligation"]["action"]["action_type"] != reviewed[forced_key]["obligation"]["action"]["action_type"]

    return {
        "case_count": len(seen),
        "exact_step13_duplicates": duplicates,
        "full_title_leaks": title_leaks,
        "target_identity_overlap_count": len(identity_overlaps),
    }


def collapse_identities(results: Iterable[Any]) -> list[tuple[int, int]]:
    seen: set[tuple[int, int]] = set()
    collapsed: list[tuple[int, int]] = []
    for result in results:
        identity = (result.chunk.notice_id, result.chunk.version_id)
        if identity not in seen:
            seen.add(identity)
            collapsed.append(identity)
    return collapsed


def retrieval_metrics(rank_lists: list[list[tuple[int, int]]], expected: list[tuple[int, int]]) -> dict[str, Any]:
    ranks: list[int | None] = []
    for identities, target in zip(rank_lists, expected, strict=True):
        ranks.append((identities.index(target) + 1) if target in identities else None)
    count = len(ranks)
    return {
        "n": count,
        "hit_at_1": sum(rank == 1 for rank in ranks) / count if count else None,
        "hit_at_3": sum(rank is not None and rank <= 3 for rank in ranks) / count if count else None,
        "mrr": sum(1 / rank if rank else 0 for rank in ranks) / count if count else None,
    }


def distribution(outcomes: Iterable[str]) -> dict[str, int]:
    counts = Counter(outcomes)
    return {key: counts.get(key, 0) for key in OUTCOME_KEYS}


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * fraction
    low, high = math.floor(rank), math.ceil(rank)
    return ordered[low] if low == high else ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


class ForcedRetriever:
    """Evaluation-local retriever for action-incompatible safety stress only."""

    def __init__(self, chunk: Any):
        self.chunk = chunk

    def search(self, query: str, top_k: int = 5) -> list[Any]:
        from app.retrieval.base import RetrievalResult
        return [RetrievalResult(chunk=self.chunk, rank=1, score=1.0, retrieval_method="step18h_forced_safety")]


class ForcedObligationRepository:
    """Evaluation-local repository limiting a forced candidate to one obligation."""

    def __init__(self, obligation: Any):
        self.obligation = obligation

    def get_reviewed_official_obligations(self, notice_id: int, version_id: int) -> list[Any]:
        return [self.obligation]


def normalized_verdict(result: Any) -> str:
    value = result.verdict.value
    return "INSUFFICIENT_EVIDENCE" if value == "ABSTAINED" else value


def predicted_fields(text: str, decomposer: Any) -> dict[str, str | int | None]:
    claims = decomposer.decompose(text)
    if not claims:
        return {}
    claim = claims[0]
    return {
        name: field.normalized_value
        for name in ("action", "deadline")
        if (field := getattr(claim, name)) is not None
    }


def classify_failure(case: dict[str, Any], trace: dict[str, Any]) -> str | None:
    if trace["pass_expected_outcome"]:
        return None
    if case["provenance_type"] == "UNSUPPORTED_DIAGNOSTIC":
        return "UNSUPPORTED_FALSE_ASSERTION"
    expected_identity = case.get("expected_notice_identity")
    if expected_identity and (expected_identity["notice_id"], expected_identity["version_id"]) not in [tuple(x.values()) for x in trace["retrieved_notice_identities"]]:
        return "RETRIEVAL_MISS"
    if any(trace["predicted_fields"].get(key) != value for key, value in case.get("expected_fields", {}).items()):
        return "EXTRACTION_MISS"
    if trace["predicted_verdict"] == "INSUFFICIENT_EVIDENCE":
        return "APPLICABILITY_ABSTENTION"
    return "FIELD_COMPARISON"


def build_runtime() -> tuple[Any, Any, list[Any]]:
    """Load current published cache; fail rather than rebuild it."""
    from app.retrieval.bm25 import BM25Retriever
    from app.retrieval.chunking import build_corpus
    from app.retrieval.dense import DenseRetriever
    from app.retrieval.hybrid import HybridRetriever
    from app.verification.abstention import AbstentionPolicy
    from app.verification.decomposer import ClaimDecomposer
    from app.verification.repository import OfficialStructuredRepository
    from app.verification.service import VerificationService

    chunks = build_corpus()
    dense = DenseRetriever(local_files_only=True)
    if not dense.load_cache(chunks):
        raise RuntimeError("Published dense cache is unavailable or does not match current corpus; refusing to rebuild.")
    bm25 = BM25Retriever()
    bm25.index(chunks)
    hybrid = HybridRetriever([bm25, dense])
    hybrid.chunks = chunks
    decomposer = ClaimDecomposer()
    service = VerificationService(hybrid, decomposer, OfficialStructuredRepository(), AbstentionPolicy())
    return service, decomposer, chunks


def execute_case(case: dict[str, Any], service: Any, decomposer: Any, retriever: Any, latency_ms: float | None = None) -> dict[str, Any]:
    retrieved = retriever.search(case["input_text"], top_k=5)
    identities = collapse_identities(retrieved)
    started = time.perf_counter()
    results = service.verify(case["input_text"], top_k=5)
    elapsed = (time.perf_counter() - started) * 1000 if latency_ms is None else latency_ms
    result = results[0] if results else None
    verdict = normalized_verdict(result) if result else "INSUFFICIENT_EVIDENCE"
    trace = {
        "case_id": case["case_id"],
        "provenance_type": case["provenance_type"],
        "input_text": case["input_text"],
        "expected_verdict": case["expected_verdict"],
        "predicted_verdict": verdict,
        "expected_notice_identity": case.get("expected_notice_identity"),
        "retrieved_notice_identities": [{"notice_id": n, "version_id": v} for n, v in identities],
        "expected_fields": case.get("expected_fields", {}),
        "predicted_fields": predicted_fields(case["input_text"], decomposer),
        "abstention_reason": result.abstention_reason.value if result and result.abstention_reason else None,
        "latency_ms": round(elapsed, 3),
        "mutation": case.get("mutation"),
        "forced_candidate_identity": case.get("forced_candidate_identity"),
    }
    if case.get("expected_non_conflict"):
        trace["pass_expected_outcome"] = verdict != "CONFLICT"
        trace["expected_non_conflict"] = True
    else:
        trace["pass_expected_outcome"] = verdict == case["expected_verdict"]
    trace["failure_classification"] = classify_failure(case, trace)
    return trace


def report_markdown(metrics: dict[str, Any], traces: list[dict[str, Any]]) -> str:
    def pct(value: float | None) -> str:
        return "NOT AVAILABLE" if value is None else f"{value:.2%}"
    errors = Counter(trace["failure_classification"] for trace in traces if trace["failure_classification"])
    return f"""# Step 18H Evaluation Report — 18h-v1

## 1. Executive Summary

This is a small, offline, provenance-aware diagnostic of the current UniTrust pipeline. It is not an overall real-world accuracy claim.

## 2. Benchmark Scope

Current production Hybrid RRF retrieval and `VerificationService` were evaluated without product changes, network, OCR runtime, or LLM providers.

## 3. Dataset Composition

- Source-derived positives: N={metrics['dataset_composition']['source_derived_positive_n']}
- Controlled deadline conflicts: N={metrics['dataset_composition']['controlled_conflict_n']}
- Unsupported diagnostics: N={metrics['dataset_composition']['unsupported_n']}
- Controlled action-incompatibility safety stress: N={metrics['dataset_composition']['cross_obligation_safety_n']}

## 4. Provenance / Case Construction

Source positives are **curated source-derived paraphrases** labeled from REVIEWED/GOLD obligations before execution. Conflicts are deterministic +7-day deadline perturbations. Unsupported and safety cases are controlled diagnostics.

## 5. Historical Step13 Baseline

Step13 is frozen historical evidence and was not run. Its retrieval N=58 Hybrid RRF values (Hit@1 0.9483, Hit@3 1.0000, MRR 0.9741) are not comparable with this new query set.

## 6. Step18H New Retrieval Results

On a new source-derived query set (N={metrics['retrieval']['n']}), Hybrid retrieval achieved Hit@1={pct(metrics['retrieval']['hit_at_1'])}, Hit@3={pct(metrics['retrieval']['hit_at_3'])}, MRR={metrics['retrieval']['mrr']:.4f}.

## 7. Source-Derived Positive Verification

On this small source-derived diagnostic set (N={metrics['source_positive']['n']}), expected-outcome rate was {pct(metrics['source_positive']['expected_outcome_rate'])}. Distribution: {metrics['source_positive']['outcome_distribution']}.

## 8. Controlled Synthetic Conflict Results

On controlled synthetic deadline perturbations (N={metrics['controlled_conflict']['n']}), expected-outcome rate was {pct(metrics['controlled_conflict']['expected_outcome_rate'])}. This is not real-world conflict accuracy.

## 9. Unsupported / Abstention Results

On unsupported diagnostic claims (N={metrics['unsupported']['n']}), safe abstention rate was {pct(metrics['unsupported']['safe_abstention_rate'])}; false VERIFIED rate was {pct(metrics['unsupported']['false_verified_rate'])}; false CONFLICT rate was {pct(metrics['unsupported']['false_conflict_rate'])}.

## 10. Cross-Obligation Safety Results

On controlled action-incompatibility safety stress cases (N={metrics['cross_obligation_safety']['n']}), false conflict rate was {pct(metrics['cross_obligation_safety']['false_conflict_rate'])}. This forces an action-incompatible reviewed candidate and is not an end-to-end retrieval metric.

## 11. Structured Extraction

Action: N={metrics['extraction']['action']['n']}, correct={metrics['extraction']['action']['correct']}, accuracy={pct(metrics['extraction']['action']['accuracy'])}. Deadline: N={metrics['extraction']['deadline']['n']}, correct={metrics['extraction']['deadline']['correct']}, accuracy={pct(metrics['extraction']['deadline']['accuracy'])}. Amount: NOT AVAILABLE (reviewed amount annotations N=0).

## 12. Local Warm Latency

Warmed local text verification only: N={metrics['latency']['n']}, p50={metrics['latency']['p50_ms']:.2f} ms, p95={metrics['latency']['p95_ms']:.2f} ms, min={metrics['latency']['min_ms']:.2f} ms, max={metrics['latency']['max_ms']:.2f} ms. Not production latency.

## 13. Temporal Coverage

No confirmed real temporal transitions are available; temporal accuracy is not measured.

## 14. OCR Functional Status

One qualification image and functional tests exist; no OCR accuracy benchmark is claimed.

## 15. URL Functional/Security Status

Mocked security/extraction tests and an accepted one-site runtime smoke provide functional/security evidence; no public-web accuracy is claimed.

## 16. Error Analysis

Observable failure classifications: {dict(errors) if errors else 'none'}.

## 17. Limitations

Small curated sets, no independent PARTIALLY_VERIFIED ground truth, no reviewed amount support, no temporal transitions, no OCR accuracy, and no public-web accuracy.

## 18. Claims We Can Make

Only scoped claims with the N and strata above: new-query retrieval, controlled outcome rates, controlled safety rate, extraction results, and local warmed latency.

## 19. Claims We Cannot Make

We cannot claim overall university-announcement accuracy, real-world conflict accuracy, scam detection, OCR accuracy, temporal accuracy, production latency, all-university generalization, universal URL safety, or amount extraction accuracy.

## 20. Reproduction Instructions

Run `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, then `.venv\\Scripts\\python evaluation/step18h/run_evaluation.py`. The runner reads current production data/cache and writes only this directory's reports.

## Recommended competition-facing metrics

1. Hybrid retrieval Hit@1/Hit@3/MRR on the new source-derived N={metrics['retrieval']['n']} set.
2. Source-derived positive expected-outcome rate (small-sample diagnostic, N={metrics['source_positive']['n']}).
3. Controlled synthetic deadline-conflict expected-outcome rate (N={metrics['controlled_conflict']['n']}).
4. Cross-obligation false-conflict rate (small-sample safety diagnostic, N={metrics['cross_obligation_safety']['n']}).
5. Unsupported safe-abstention rate (small-sample diagnostic, N={metrics['unsupported']['n']}).
6. Action/deadline extraction accuracy on source-derived cases.
7. Warmed local text-verification p50/p95 (test-machine measurement).
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the offline Step 18H evaluation once.")
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--skip-latency", action="store_true")
    args = parser.parse_args(argv)
    case_sets = load_case_sets()
    integrity = validate_cases(case_sets)
    if integrity["exact_step13_duplicates"] or integrity["full_title_leaks"]:
        raise RuntimeError(f"Case leakage check failed: {integrity}")
    service, decomposer, chunks = build_runtime()
    chunk_by_identity = {(chunk.notice_id, chunk.version_id): chunk for chunk in chunks}
    hybrid = service.retriever
    traces: list[dict[str, Any]] = []
    latency_samples: list[float] = []

    positive = case_sets["source_positive"]
    retrieval_rank_lists = [collapse_identities(hybrid.search(case["input_text"], top_k=3)) for case in positive]
    retrieval = retrieval_metrics(retrieval_rank_lists, [(case["source_notice_id"], case["source_version_id"]) for case in positive])

    if positive and not args.skip_latency:
        service.verify(positive[0]["input_text"], top_k=5)  # excluded warm-up
    for case in positive:
        samples: list[float] = []
        for _ in range(3 if not args.skip_latency else 1):
            started = time.perf_counter()
            result = service.verify(case["input_text"], top_k=5)
            samples.append((time.perf_counter() - started) * 1000)
        latency_samples.extend(samples if not args.skip_latency else [])
        trace = execute_case(case, service, decomposer, hybrid, latency_ms=samples[0])
        traces.append(trace)

    for group in ("controlled_conflict", "unsupported"):
        for case in case_sets[group]:
            traces.append(execute_case(case, service, decomposer, hybrid))

    for case in case_sets["cross_obligation_safety"]:
        forced = case["forced_candidate_identity"]
        chunk = chunk_by_identity[(forced["notice_id"], forced["version_id"])]
        forced_obligation = reviewed_obligations()[
            (forced["notice_id"], forced["version_id"], forced["obligation_id"])
        ]["obligation"]
        from app.models.obligation import StudentObligation
        original_retriever, original_repository = service.retriever, service.repository
        service.retriever = ForcedRetriever(chunk)
        service.repository = ForcedObligationRepository(StudentObligation(**forced_obligation))
        try:
            traces.append(execute_case(case, service, decomposer, service.retriever))
        finally:
            service.retriever, service.repository = original_retriever, original_repository

    grouped = {name: [trace for trace in traces if trace["provenance_type"] == provenance] for name, provenance in {
        "source_positive": "REVIEWED_SOURCE_DERIVED",
        "controlled_conflict": "CONTROLLED_SYNTHETIC_CONFLICT",
        "unsupported": "UNSUPPORTED_DIAGNOSTIC",
        "cross_obligation_safety": "SAFETY_STRESS",
    }.items()}
    source_outcomes = [trace["predicted_verdict"] for trace in grouped["source_positive"]]
    conflict_outcomes = [trace["predicted_verdict"] for trace in grouped["controlled_conflict"]]
    unsupported_outcomes = [trace["predicted_verdict"] for trace in grouped["unsupported"]]
    safety_outcomes = [trace["predicted_verdict"] for trace in grouped["cross_obligation_safety"]]
    action_cases = [trace for trace in grouped["source_positive"] if "action" in trace["expected_fields"]]
    deadline_cases = [trace for trace in grouped["source_positive"] if "deadline" in trace["expected_fields"]]
    metrics = {
        "benchmark_version": VERSION,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_composition": {
            "source_derived_positive_n": len(grouped["source_positive"]),
            "controlled_conflict_n": len(grouped["controlled_conflict"]),
            "unsupported_n": len(grouped["unsupported"]),
            "cross_obligation_safety_n": len(grouped["cross_obligation_safety"]),
        },
        "integrity": integrity,
        "retrieval": retrieval,
        "source_positive": {
            "n": len(source_outcomes), "expected_verified_count": source_outcomes.count("VERIFIED"),
            "expected_outcome_rate": source_outcomes.count("VERIFIED") / len(source_outcomes),
            "outcome_distribution": distribution(source_outcomes),
        },
        "controlled_conflict": {
            "n": len(conflict_outcomes), "expected_conflict_count": conflict_outcomes.count("CONFLICT"),
            "expected_outcome_rate": conflict_outcomes.count("CONFLICT") / len(conflict_outcomes),
            "outcome_distribution": distribution(conflict_outcomes), "dataset_label": "CONTROLLED SYNTHETIC",
        },
        "unsupported": {
            "n": len(unsupported_outcomes),
            "safe_abstention_rate": unsupported_outcomes.count("INSUFFICIENT_EVIDENCE") / len(unsupported_outcomes),
            "false_verified_rate": unsupported_outcomes.count("VERIFIED") / len(unsupported_outcomes),
            "false_conflict_rate": unsupported_outcomes.count("CONFLICT") / len(unsupported_outcomes),
            "outcome_distribution": distribution(unsupported_outcomes),
        },
        "cross_obligation_safety": {
            "n": len(safety_outcomes), "false_conflict_count": safety_outcomes.count("CONFLICT"),
            "false_conflict_rate": safety_outcomes.count("CONFLICT") / len(safety_outcomes),
            "safe_abstention_count": safety_outcomes.count("INSUFFICIENT_EVIDENCE"),
            "other_non_conflict_count": sum(outcome not in {"CONFLICT", "INSUFFICIENT_EVIDENCE"} for outcome in safety_outcomes),
            "outcome_distribution": distribution(safety_outcomes), "dataset_label": "SAFETY STRESS",
        },
        "extraction": {
            "action": {"n": len(action_cases), "correct": sum(t["predicted_fields"].get("action") == t["expected_fields"]["action"] for t in action_cases), "accuracy": sum(t["predicted_fields"].get("action") == t["expected_fields"]["action"] for t in action_cases) / len(action_cases)},
            "deadline": {"n": len(deadline_cases), "correct": sum(t["predicted_fields"].get("deadline") == t["expected_fields"]["deadline"] for t in deadline_cases), "accuracy": sum(t["predicted_fields"].get("deadline") == t["expected_fields"]["deadline"] for t in deadline_cases) / len(deadline_cases)},
            "amount": {"n": 0, "status": "NOT_AVAILABLE", "reason": "Zero reviewed amount annotations."},
        },
        "latency": {"measurement_scope": "warmed local text verification; initialization and one warm-up excluded", "n": len(latency_samples), "p50_ms": percentile(latency_samples, .50), "p95_ms": percentile(latency_samples, .95), "min_ms": min(latency_samples) if latency_samples else None, "max_ms": max(latency_samples) if latency_samples else None, "cold_initialization_ms": None},
        "limitations": ["No temporal accuracy: zero confirmed real transitions.", "No OCR accuracy benchmark.", "No public-web URL accuracy benchmark.", "No amount extraction metric: reviewed amount N=0.", "No independent PARTIALLY_VERIFIED benchmark."],
        "case_file_sha256": case_file_hashes(),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "step18h_v1_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "step18h_v1_cases.jsonl").write_text("".join(json.dumps(trace, ensure_ascii=False) + "\n" for trace in traces), encoding="utf-8")
    (args.output_dir / "STEP18H_EVALUATION_REPORT.md").write_text(report_markdown(metrics, traces), encoding="utf-8")
    print(json.dumps({"status": "completed", "reports": str(args.output_dir), "case_count": len(traces)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
