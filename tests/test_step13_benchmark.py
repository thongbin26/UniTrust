import json
from pathlib import Path
import pytest
from scripts.analyze_step13_errors import calculate_metrics, attribute_error

def test_metric_computation_and_zero_support():
    traces = [
        {"expected_trust_state": "VERIFIED", "actual_trust_state": "VERIFIED"},
        {"expected_trust_state": "VERIFIED", "actual_trust_state": "CONFLICT"},
        {"expected_trust_state": "CONFLICT", "actual_trust_state": "CONFLICT"}
    ]
    classes = ["VERIFIED", "PARTIALLY_VERIFIED", "CONFLICT", "INSUFFICIENT_EVIDENCE"]
    
    metrics = calculate_metrics(traces, classes)
    
    assert metrics["accuracy"] == 2 / 3
    
    # Zero support checks
    assert metrics["class_metrics"]["PARTIALLY_VERIFIED"]["support"] == 0
    assert metrics["class_metrics"]["PARTIALLY_VERIFIED"]["precision"] is None
    
    assert metrics["class_metrics"]["INSUFFICIENT_EVIDENCE"]["support"] == 0
    assert metrics["class_metrics"]["INSUFFICIENT_EVIDENCE"]["precision"] is None
    
    assert metrics["class_metrics"]["VERIFIED"]["support"] == 2
    assert metrics["class_metrics"]["VERIFIED"]["precision"] == 1.0
    assert metrics["class_metrics"]["VERIFIED"]["recall"] == 0.5
    
def test_error_attribution():
    # RETRIEVAL_MISS
    t1 = {
        "expected_trust_state": "VERIFIED",
        "actual_trust_state": "INSUFFICIENT_EVIDENCE",
        "retrieved_notices": [],
        "benchmark_case_id": "n1_v1_o1"
    }
    assert attribute_error(t1) == "RETRIEVAL_MISS"
    
    # WRONG_NOTICE_RANKED
    t2 = {
        "expected_trust_state": "VERIFIED",
        "actual_trust_state": "INSUFFICIENT_EVIDENCE",
        "retrieved_notices": [{"notice_id": 2, "version_id": 2}, {"notice_id": 1, "version_id": 1}],
        "benchmark_case_id": "n1_v1_o1"
    }
    assert attribute_error(t2) == "WRONG_NOTICE_RANKED"
    
    # DATE_NORMALIZATION_FAILURE
    t3 = {
        "expected_trust_state": "VERIFIED",
        "actual_trust_state": "CONFLICT",
        "retrieved_notices": [{"notice_id": 1, "version_id": 1}],
        "benchmark_case_id": "n1_v1_o1",
        "field_comparison_states": {"action": "MATCH", "deadline": "CONFLICT"}
    }
    assert attribute_error(t3) == "DATE_NORMALIZATION_FAILURE"

def test_no_annotation_mutation():
    p = Path("data/annotations/batch_001")
    # Just asserting the script didn't delete them
    assert p.exists()
    assert len(list(p.glob("*.json"))) > 0

def test_deterministic_generation():
    # Calling the builder deterministically
    from scripts.build_step13_benchmark import apply_wrong_deadline
    class MockDeadline:
        normalized = "2026-06-26T16:00:00+07:00"
    m = apply_wrong_deadline(MockDeadline())
    assert m == "16:00 ngày 30/06/2026"
    
    class MockDeadline2:
        normalized = "2026-06-15"
    m2 = apply_wrong_deadline(MockDeadline2())
    assert m2 == "ngày 19/06/2026"
