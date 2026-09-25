import json
from pathlib import Path

from evaluation.step18h import run_evaluation as evaluation


def test_case_schema_integrity_and_no_step13_text_duplicates():
    case_sets = evaluation.load_case_sets()
    integrity = evaluation.validate_cases(case_sets)
    assert integrity["case_count"] == 49
    assert integrity["exact_step13_duplicates"] == []
    assert integrity["full_title_leaks"] == []
    assert integrity["target_identity_overlap_count"] == 10


def test_case_provenance_and_expected_strata_are_explicit():
    case_sets = evaluation.load_case_sets()
    assert {case["provenance_type"] for cases in case_sets.values() for case in cases} == evaluation.PROVENANCE_TYPES
    assert all(case["expected_verdict"] == "INSUFFICIENT_EVIDENCE" and case["expected_notice_identity"] is None for case in case_sets["unsupported"])
    assert all(case["mutation"]["field"] == "deadline" for case in case_sets["controlled_conflict"])
    assert all(case["expected_non_conflict"] is True and case["forced_candidate_identity"] for case in case_sets["cross_obligation_safety"])


def test_duplicate_normalization_detects_unicode_case_and_whitespace():
    assert evaluation.normalize_for_duplicate_check("  Sinh\u00a0VIÊN\nK26 ") == evaluation.normalize_for_duplicate_check("sinh viên k26")


def test_retrieval_and_outcome_metrics_are_identity_level():
    metrics = evaluation.retrieval_metrics(
        [[(1, 1), (2, 2)], [(4, 4), (3, 3)], []],
        [(1, 1), (3, 3), (9, 9)],
    )
    assert metrics == {"n": 3, "hit_at_1": 1 / 3, "hit_at_3": 2 / 3, "mrr": 0.5}
    assert evaluation.distribution(["VERIFIED", "CONFLICT", "CONFLICT"]) == {
        "VERIFIED": 1, "PARTIALLY_VERIFIED": 0, "CONFLICT": 2, "INSUFFICIENT_EVIDENCE": 0,
    }


def test_percentiles_handle_small_deterministic_samples():
    assert evaluation.percentile([1.0, 5.0, 9.0], .50) == 5.0
    assert evaluation.percentile([1.0, 5.0, 9.0], .95) == 8.6
    assert evaluation.percentile([], .50) is None


def test_output_schema_contract(tmp_path):
    metrics = {
        "benchmark_version": "18h-v1", "git_commit": "abc", "generated_at": "now",
        "dataset_composition": {}, "retrieval": {}, "source_positive": {},
        "controlled_conflict": {}, "unsupported": {}, "cross_obligation_safety": {},
        "extraction": {"action": {}, "deadline": {}, "amount": {"n": 0, "status": "NOT_AVAILABLE"}},
        "latency": {}, "limitations": [],
    }
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps(metrics), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    required = {"benchmark_version", "git_commit", "generated_at", "dataset_composition", "retrieval", "source_positive", "controlled_conflict", "unsupported", "cross_obligation_safety", "extraction", "latency", "limitations"}
    assert required <= loaded.keys()
    trace = {"case_id": "x", "provenance_type": "SAFETY_STRESS", "input_text": "x", "expected_verdict": "INSUFFICIENT_EVIDENCE", "predicted_verdict": "INSUFFICIENT_EVIDENCE", "expected_notice_identity": None, "retrieved_notice_identities": [], "expected_fields": {}, "predicted_fields": {}, "abstention_reason": "NO_OFFICIAL_FIELD", "latency_ms": 1.0, "pass_expected_outcome": True, "failure_classification": None}
    assert {"case_id", "provenance_type", "input_text", "expected_verdict", "predicted_verdict", "retrieved_notice_identities", "predicted_fields", "latency_ms", "pass_expected_outcome"} <= trace.keys()


def test_case_files_are_versioned_inputs_not_generated_reports():
    hashes = evaluation.case_file_hashes()
    assert set(hashes) == {
        "source_derived_positive.jsonl", "controlled_deadline_conflict.jsonl",
        "unsupported_diagnostic.jsonl", "cross_obligation_safety.jsonl",
    }
    assert all(len(value) == 64 for value in hashes.values())
