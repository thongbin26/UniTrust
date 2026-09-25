"""Offline-first evaluator for the accepted Q001-Q006 provider experiment.

This module is evaluation tooling only.  It never changes UniTrust runtime
behavior and it never creates a provider client unless a caller explicitly
selects real-provider mode.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from app.verification.gemini_qualification import GeminiQualificationAdapter, validate_payload
from app.verification.models import DecomposedUserClaim


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset_draft.jsonl"
EXPECTED_IDS = ("Q001", "Q002", "Q003", "Q004", "Q005", "Q006")
# These are the fields the current Gemini adapter can receive from provider JSON.
SUPPORTED_FIELDS = ("audience", "action", "deadline", "amount", "required_documents")
NOT_APPLICABLE_FIELDS = ("object_hint", "location", "exceptions", "span_qualification")
SAFE_ERROR_CODES = {
    "INVALID_TOP_LEVEL_SCHEMA", "TRUST_VERDICT_OR_INVALID_CLAIM", "INVALID_ACTION",
    "INVALID_AMOUNT", "UNGROUNDED_FIELD", "UNGROUNDED_CLAIM", "INVENTED_YEAR",
    "MALFORMED_JSON", "REAL_PROVIDER_CONFIGURATION_REQUIRED", "GOOGLE_GENAI_SDK_NOT_INSTALLED",
}


def load_accepted_cases(path: Path = DATASET) -> list[dict[str, Any]]:
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if tuple(case.get("id") for case in cases) != EXPECTED_IDS:
        raise ValueError("EXPECTED_ACCEPTED_Q001_Q006_ONLY")
    if any(case.get("claim_count") != len(case.get("claims", [])) for case in cases):
        raise ValueError("INVALID_BENCHMARK_CLAIM_COUNT")
    return cases


def _normalized(field: Any) -> Any:
    return None if field is None else field.normalized_value


def _gold_value(claim: dict[str, Any], field: str) -> Any:
    if field == "action":
        return claim.get("action_normalized")
    if field == "deadline":
        return claim.get("deadline_normalized")
    if field == "amount":
        return claim.get("amount_value")
    return claim.get(field)


def _actual_value(claim: DecomposedUserClaim, field: str) -> Any:
    if field == "required_documents":
        return [item.text for item in claim.required_documents]
    value = getattr(claim, field)
    # The adapter normalizes action, deadline, and amount; audience remains an
    # exact grounded text field in the current provider schema.
    return value.text if field == "audience" and value is not None else _normalized(value)


def documents_match(expected: list[str], observed: list[str]) -> bool:
    """Compare document items as a normalized multiset, never discarding duplicates."""
    normalize = lambda value: re.sub(r"\s+", " ", value).strip().casefold()
    return Counter(normalize(item) for item in expected) == Counter(normalize(item) for item in observed)


def _empty_metrics() -> dict[str, Any]:
    return {
        "sample_count": 0,
        "expected_claim_count": 0,
        "returned_claim_count": 0,
        "missing_claims": 0,
        "unexpected_claims": 0,
        "adapter_success_count": 0,
        "adapter_failure_count": 0,
        "valid_structured_output_count": 0,
        "invalid_output_count": 0,
        "grounding_violation_count": 0,
        "invented_year_violation_count": 0,
        "invalid_action_violation_count": 0,
        "fields": {field: Counter(correct=0, incorrect=0, missing=0, hallucinated=0) for field in SUPPORTED_FIELDS},
        "not_applicable": list(NOT_APPLICABLE_FIELDS),
    }


def _error_kind(exc: Exception) -> str:
    message = str(exc)
    if message == "INVENTED_YEAR":
        return "invented_year"
    if "UNGROUNDED" in message:
        return "grounding"
    return "invalid_output"


def _safe_error_code(exc: Exception) -> str:
    """Avoid persisting arbitrary provider/transport exception text."""
    return str(exc) if str(exc) in SAFE_ERROR_CODES else "ADAPTER_ERROR"


def qualification_status(metrics: dict[str, Any]) -> str:
    """Apply the human-approved, pre-registered qualification policy."""
    blocking = (
        "adapter_failure_count", "invalid_output_count", "grounding_violation_count",
        "invented_year_violation_count", "invalid_action_violation_count",
    )
    if any(metrics[name] for name in blocking):
        return "QUALIFICATION_BLOCKED"
    structure_mismatch = metrics["missing_claims"] or metrics["unexpected_claims"]
    field_mismatch = any(
        values["incorrect"] or values["missing"] or values["hallucinated"]
        for values in metrics["fields"].values()
    )
    if structure_mismatch or field_mismatch:
        return "MEASURED_REQUIRES_HUMAN_REVIEW"
    return "QUALIFIED_FOR_EVALUATED_FIELDS_ONLY"


def evaluate_cases(
    cases: Iterable[dict[str, Any]],
    extract: Callable[[str], tuple[list[DecomposedUserClaim], float, str]],
    *,
    real_provider: bool = False,
) -> dict[str, Any]:
    """Evaluate one extraction invocation per benchmark input.

    ``extract`` is injected in offline tests.  It may raise an adapter/schema
    error; that failure is recorded for its sample and does not abort the run.
    """
    cases = list(cases)
    metrics = _empty_metrics()
    metrics["sample_count"] = len(cases)
    metrics["expected_claim_count"] = sum(case["claim_count"] for case in cases)
    request_counts = {
        "planned_provider_requests": len(cases) if real_provider else 0,
        "attempted_provider_requests": 0,
        "successful_provider_requests": 0,
        "failed_provider_requests": 0,
    }
    results: list[dict[str, Any]] = []

    for case in cases:
        sample = {"id": case["id"], "adapter_status": "SUCCESS", "mismatches": []}
        if real_provider:
            request_counts["attempted_provider_requests"] += 1
        try:
            claims, latency_ms, model = extract(case["input_text"])
        except Exception as exc:  # Expected provider/schema failures are benchmark evidence.
            kind = _error_kind(exc)
            sample.update({"adapter_status": "FAILURE", "error_class": type(exc).__name__, "error_code": _safe_error_code(exc)})
            metrics["adapter_failure_count"] += 1
            metrics[f"{kind}_violation_count" if kind != "invalid_output" else "invalid_output_count"] += 1
            if str(exc) == "INVALID_ACTION":
                metrics["invalid_action_violation_count"] += 1
            if real_provider:
                request_counts["failed_provider_requests"] += 1
            results.append(sample)
            continue

        sample.update({"model": model, "latency_ms": round(latency_ms, 3), "returned_claim_count": len(claims)})
        metrics["adapter_success_count"] += 1
        metrics["valid_structured_output_count"] += 1
        metrics["returned_claim_count"] += len(claims)
        if real_provider:
            request_counts["successful_provider_requests"] += 1

        expected_claims = case["claims"]
        metrics["missing_claims"] += max(0, len(expected_claims) - len(claims))
        metrics["unexpected_claims"] += max(0, len(claims) - len(expected_claims))
        for index, gold in enumerate(expected_claims):
            actual = claims[index] if index < len(claims) else None
            for field in SUPPORTED_FIELDS:
                expected = _gold_value(gold, field)
                observed = _actual_value(actual, field) if actual is not None else None
                bucket = metrics["fields"][field]
                if expected is None or expected == []:
                    if observed not in (None, []):
                        bucket["hallucinated"] += 1
                        sample["mismatches"].append({"field": field, "expected": expected, "provider": observed, "type": "HALLUCINATED"})
                elif observed is None or observed == []:
                    bucket["missing"] += 1
                    sample["mismatches"].append({"field": field, "expected": expected, "provider": observed, "type": "MISSING"})
                elif field == "required_documents" and documents_match(expected, observed):
                    bucket["correct"] += 1
                elif observed == expected:
                    bucket["correct"] += 1
                else:
                    bucket["incorrect"] += 1
                    sample["mismatches"].append({"field": field, "expected": expected, "provider": observed, "type": "INCORRECT"})
        results.append(sample)

    metrics["fields"] = {name: dict(values) for name, values in metrics["fields"].items()}
    return {
        "status": qualification_status(metrics),
        "mode": "REAL_PROVIDER" if real_provider else "OFFLINE",
        "benchmark_ids": [case["id"] for case in cases],
        "request_counts": request_counts,
        "metrics": metrics,
        "sample_results": results,
    }


def offline_extractor(payloads: dict[str, Any], cases: Iterable[dict[str, Any]]) -> Callable[[str], tuple[list[DecomposedUserClaim], float, str]]:
    """Build a network-free extractor from ``{sample_id: provider_payload}`` fixtures."""
    by_text = {case["input_text"]: case["id"] for case in cases}

    def extract(text: str) -> tuple[list[DecomposedUserClaim], float, str]:
        sample_id = by_text[text]
        payload = payloads[sample_id]
        if isinstance(payload, dict) and "__error__" in payload:
            raise RuntimeError(payload["__error__"])
        # Reuse the real adapter's schema and grounding contract without reading
        # provider configuration or constructing a client.
        return validate_payload(text, payload), 0.0, "OFFLINE_FIXTURE"

    return extract


def write_reports(result: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    """Write sanitized machine- and human-readable evaluation evidence."""
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {**result, "generated_at_utc": datetime.now(timezone.utc).isoformat()}
    json_path = output_dir / "provider_qualification_report.json"
    markdown_path = output_dir / "provider_qualification_report.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# V2.2A provider qualification measurement",
        "",
        f"- Status: `{result['status']}`",
        f"- Mode: `{result['mode']}`",
        f"- Samples: {', '.join(result['benchmark_ids'])}",
        f"- Planned real requests: {result['request_counts']['planned_provider_requests']}",
        f"- Attempted/successful/failed real requests: "
        f"{result['request_counts']['attempted_provider_requests']}/"
        f"{result['request_counts']['successful_provider_requests']}/"
        f"{result['request_counts']['failed_provider_requests']}",
        "- Qualification policy: **HUMAN_APPROVED — PRE-REGISTERED BEFORE REAL Q001-Q006 EVALUATION**",
        "- Provider credentials and environment values are intentionally omitted.",
        "",
        "## Per-sample mismatches",
    ]
    for sample in result["sample_results"]:
        lines.append(f"- `{sample['id']}` — {sample['adapter_status']}; mismatches: {len(sample['mismatches'])}")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, markdown_path
