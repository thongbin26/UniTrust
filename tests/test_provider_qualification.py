import json

import pytest

from app.verification.gemini_qualification import GeminiQualificationAdapter
from evaluation.v22a_ai_qualification.provider_qualification import (
    EXPECTED_IDS, documents_match, evaluate_cases, load_accepted_cases, offline_extractor, write_reports,
)


def payload_for(case):
    claim = case["claims"][0]
    return {"claims": [{
        "claim_text": claim["claim_text"],
        "audience": claim["audience"],
        "action": claim["action"],
        "action_normalized": claim["action_normalized"],
        "deadline_raw": claim["deadline_raw"],
        "deadline_normalized": claim["deadline_normalized"],
        "amount_raw": claim["amount_raw"],
        "amount_value": claim["amount_value"],
        "required_documents": claim["required_documents"],
    }]}


@pytest.fixture
def cases():
    return load_accepted_cases()


def test_offline_perfect_output_measures_all_samples_without_real_requests(cases):
    payloads = {case["id"]: payload_for(case) for case in cases}
    result = evaluate_cases(cases, offline_extractor(payloads, cases))
    assert result["status"] == "QUALIFIED_FOR_EVALUATED_FIELDS_ONLY"
    assert result["benchmark_ids"] == list(EXPECTED_IDS)
    assert result["request_counts"] == {
        "planned_provider_requests": 0, "attempted_provider_requests": 0,
        "successful_provider_requests": 0, "failed_provider_requests": 0,
    }
    assert result["metrics"]["adapter_success_count"] == 6
    assert result["metrics"]["fields"]["action"]["correct"] == 6


def test_wrong_missing_and_hallucinated_fields_are_audited(cases):
    payloads = {case["id"]: payload_for(case) for case in cases}
    payloads["Q001"]["claims"][0]["action_normalized"] = "submit"
    payloads["Q002"]["claims"][0]["audience"] = None
    # "khảo sát" occurs in Q004, so this exercises a grounded provider field
    # that is nevertheless unsupported by that sample's gold contract.
    payloads["Q004"]["claims"][0]["required_documents"] = ["khảo sát"]
    result = evaluate_cases(cases, offline_extractor(payloads, cases))
    fields = result["metrics"]["fields"]
    assert fields["action"]["incorrect"] == 1
    assert fields["audience"]["missing"] == 1
    assert fields["required_documents"]["hallucinated"] == 1
    assert result["status"] == "MEASURED_REQUIRES_HUMAN_REVIEW"


@pytest.mark.parametrize("sample_id, mutation, expected_error", [
    ("Q001", lambda p: p["claims"][0].update(action_normalized="invalid"), "INVALID_ACTION"),
    ("Q003", lambda p: p["claims"][0].update(deadline_normalized="2026-09-18"), "INVENTED_YEAR"),
    ("Q003", lambda p: p["claims"][0].update(required_documents=["CMND"]), "UNGROUNDED_FIELD"),
])
def test_invalid_action_invented_year_and_ungrounded_fields_are_failures(cases, sample_id, mutation, expected_error):
    payloads = {case["id"]: payload_for(case) for case in cases}
    mutation(payloads[sample_id])
    result = evaluate_cases(cases, offline_extractor(payloads, cases))
    sample = next(item for item in result["sample_results"] if item["id"] == sample_id)
    assert sample["adapter_status"] == "FAILURE"
    assert sample["error_code"] == expected_error
    assert result["status"] == "QUALIFICATION_BLOCKED"


def test_malformed_output_and_adapter_error_do_not_abort(cases):
    payloads = {case["id"]: payload_for(case) for case in cases}
    payloads["Q005"] = {"__error__": "MALFORMED_JSON"}
    result = evaluate_cases(cases, offline_extractor(payloads, cases))
    assert result["metrics"]["adapter_failure_count"] == 1
    assert result["metrics"]["invalid_output_count"] == 1
    assert result["status"] == "QUALIFICATION_BLOCKED"


def test_required_documents_are_a_normalized_multiset_not_an_ordered_list():
    assert documents_match(["CCCD", "Đơn đăng ký"], [" đơn   đăng ký ", "cccd"])
    assert not documents_match(["CCCD", "CCCD"], ["CCCD"])


def test_offline_fixtures_never_construct_real_provider_client(monkeypatch, cases):
    def forbidden_extract(self, text):
        raise AssertionError("real provider must not be invoked")
    monkeypatch.setattr(GeminiQualificationAdapter, "extract", forbidden_extract)
    payloads = {case["id"]: payload_for(case) for case in cases}
    result = evaluate_cases(cases, offline_extractor(payloads, cases))
    assert result["metrics"]["adapter_success_count"] == 6


def test_reports_are_sanitized_and_machine_readable(tmp_path, cases):
    payloads = {case["id"]: payload_for(case) for case in cases}
    result = evaluate_cases(cases, offline_extractor(payloads, cases))
    json_path, markdown_path = write_reports(result, tmp_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["status"] == "QUALIFIED_FOR_EVALUATED_FIELDS_ONLY"
    assert "credentials" in markdown_path.read_text(encoding="utf-8")
