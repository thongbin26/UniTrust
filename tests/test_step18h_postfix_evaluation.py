import json

from evaluation.step18h.postfix import run_postfix_evaluation as postfix


def test_frozen_hash_inventory_covers_cases_and_v1_reports():
    hashes = postfix.frozen_v1_hashes()
    assert len(hashes) == 8
    assert all(len(value) == 64 for value in hashes.values())
    assert all("postfix" not in path for path in hashes)


def test_change_classification_marks_fixes_and_regressions():
    pre = {"predicted_verdict": "CONFLICT", "pass_expected_outcome": False}
    post = {"predicted_verdict": "VERIFIED", "pass_expected_outcome": True}
    assert postfix.classify_change("step18h-positive-001", pre, post) == "FIXED_FALSE_CONFLICT"
    pre_unsupported = {"predicted_verdict": "PARTIALLY_VERIFIED", "pass_expected_outcome": False}
    post_unsupported = {"predicted_verdict": "INSUFFICIENT_EVIDENCE", "pass_expected_outcome": True}
    assert postfix.classify_change("step18h-unsupported-001", pre_unsupported, post_unsupported) == "FIXED_FALSE_ASSERTION"
    assert postfix.classify_change("any", {"pass_expected_outcome": True}, {"pass_expected_outcome": False}) == "NEW_REGRESSION"


def test_postfix_output_contract_is_separate_from_frozen_v1(tmp_path):
    metrics = {"run_id": postfix.RUN_ID, "comparison_type": postfix.COMPARISON_TYPE}
    output = tmp_path / "postfix" / "reports"
    output.mkdir(parents=True)
    target = output / "step18h_v1_postfix_dev_metrics.json"
    target.write_text(json.dumps(metrics), encoding="utf-8")
    assert json.loads(target.read_text(encoding="utf-8"))["run_id"] == "18h-v1-postfix-dev"
    assert target.name != "step18h_v1_metrics.json"


def test_deferred_limitations_are_explicit_and_disjoint_from_fixed_cases():
    assert postfix.RANGE_END_CASE_IDS.isdisjoint(postfix.TOP1_CASE_IDS)
    assert postfix.RANGE_END_CASE_IDS.isdisjoint(postfix.AMBIGUITY_CASE_IDS)
    assert len(postfix.RANGE_END_CASE_IDS) == 5


def test_generated_postfix_outputs_align_with_frozen_v1_and_delta_arithmetic():
    report_dir = postfix.REPORT_DIR
    metrics = json.loads(
        (report_dir / "step18h_v1_postfix_dev_metrics.json").read_text(encoding="utf-8")
    )
    traces = [
        json.loads(line)
        for line in (report_dir / "step18h_v1_postfix_dev_cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    pre_ids = set(postfix.read_pre_fix_traces())
    post_ids = {trace["case_id"] for trace in traces}

    assert post_ids == pre_ids
    assert metrics["frozen_v1_hashes"] == postfix.frozen_v1_hashes()
    assert metrics["deltas"]["positive_expected_outcome_rate"] == (
        metrics["post_fix_metrics"]["source_positive"]["expected_outcome_rate"]
        - metrics["pre_fix_metrics"]["source_positive"]["expected_outcome_rate"]
    )
    assert metrics["new_regression_count"] == len(metrics["new_regression_case_ids"])
    assert {
        "run_id", "benchmark_input_version", "comparison_type", "pre_fix_metrics",
        "post_fix_metrics", "deltas", "fix_validation", "new_regression_count",
    } <= metrics.keys()
    assert all(trace["change_classification"] for trace in traces)
