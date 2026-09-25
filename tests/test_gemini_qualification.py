import json

import httpx
import pytest

from app.verification.gemini_qualification import (
    GeminiQualificationAdapter, ProviderConfigurationError, ProviderGroundingError,
    ProviderSchemaError, generation_config, validate_payload,
)
from scripts.run_gemini_qualification_smoke import (
    safe_error_code,
    safe_exception_origin,
    safe_failure_details,
)


TEXT = "K26 cần nộp CCCD trước ngày 18/09/2026."


def test_missing_configuration_is_offline_safe(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ProviderConfigurationError):
        GeminiQualificationAdapter().extract(TEXT)


def test_grounded_cccd_is_accepted(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    monkeypatch.setenv("UNITRUST_GEMINI_MODEL", "test-model")
    monkeypatch.setenv("UNITRUST_ALLOW_REAL_PROVIDER_EVAL", "1")
    payload = {"claims": [{"claim_text": TEXT, "audience": "K26", "action": "nộp", "action_normalized": "submit", "deadline_raw": "18/09/2026", "deadline_normalized": "2026-09-18", "required_documents": ["CCCD"]}]}
    claims, _, _ = GeminiQualificationAdapter(transport=lambda *_: json.dumps(payload)).extract(TEXT)
    assert claims[0].required_documents[0].text == "CCCD"


@pytest.mark.parametrize("payload,error", [
    ({"claims": [{"claim_text": TEXT, "verdict": "VERIFIED"}]}, ProviderSchemaError),
    ({"claims": [{"claim_text": TEXT, "action": "nộp", "action_normalized": "unknown"}]}, ProviderSchemaError),
    ({"claims": [{"claim_text": TEXT, "required_documents": ["CMND"]}]}, ProviderGroundingError),
    ({"claims": [{"claim_text": TEXT, "deadline_raw": "18/09", "deadline_normalized": "2026-09-18"}]}, ProviderGroundingError),
])
def test_unsafe_provider_fields_are_rejected(payload, error):
    with pytest.raises(error):
        validate_payload(TEXT, payload)


def test_smoke_artifact_does_not_persist_arbitrary_provider_exception_text():
    assert safe_error_code(RuntimeError("secret-like transport detail")) == "PROVIDER_REQUEST_FAILED"
    assert safe_error_code(ProviderConfigurationError("REAL_PROVIDER_CONFIGURATION_REQUIRED")) == "REAL_PROVIDER_CONFIGURATION_REQUIRED"


def test_smoke_diagnostics_keep_safe_sdk_http_metadata_without_message():
    from google.genai import errors
    error = errors.ClientError(403, {"error": {"status": "PERMISSION_DENIED", "message": "secret diagnostic"}}, None)
    details = safe_failure_details(error)
    assert details == {
        "error_class": "ClientError",
        "error_code": "PROVIDER_REQUEST_FAILED",
        "failure_stage": "provider_response",
        "sdk_error_category": "CLIENTERROR",
        "http_status_code": 403,
        "api_status": "PERMISSION_DENIED",
    }
    assert "secret diagnostic" not in repr(details)


def test_unknown_smoke_error_uses_a_generic_safe_category():
    details = safe_failure_details(RuntimeError("credential-looking detail"))
    assert details == {
        "error_class": "RuntimeError",
        "error_code": "PROVIDER_REQUEST_FAILED",
        "failure_stage": "unknown_sdk_or_local",
    }


def test_typeerror_origin_metadata_is_sanitized_without_its_message():
    def local_failure():
        raise TypeError("api-key-like detail must not persist")

    with pytest.raises(TypeError) as caught:
        local_failure()
    details = safe_failure_details(caught.value)
    assert details["failure_stage"] == "local_type_error"
    assert details["safe_origin_module"] == "unitrust"
    assert details["safe_origin_function"] == "local_failure"
    assert details["safe_origin_file_basename"] == "test_gemini_qualification.py"
    assert isinstance(details["safe_origin_line"], int)
    assert "api-key-like detail" not in repr(details)
    assert safe_exception_origin(caught.value) == {
        key: details[key]
        for key in (
            "safe_origin_module", "safe_origin_function",
            "safe_origin_file_basename", "safe_origin_line",
        )
    }


def test_real_sdk_path_reaches_mocked_request_boundary_without_network(monkeypatch, caplog):
    """Exercise SDK serialization while making any HTTP call impossible."""
    from google.genai import _api_client, models

    class RequestBoundaryReached(Exception):
        pass

    calls = []

    def blocked_request(self, http_method, path, request_dict, http_options=None):
        calls.append((http_method, path, request_dict, http_options))
        raise RequestBoundaryReached()

    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    monkeypatch.setenv("UNITRUST_GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setenv("UNITRUST_ALLOW_REAL_PROVIDER_EVAL", "1")
    monkeypatch.setattr(_api_client.BaseApiClient, "request", blocked_request)
    monkeypatch.setattr(models.Models, "_logged_afc_warning", False)

    with pytest.raises(RequestBoundaryReached):
        GeminiQualificationAdapter().extract(TEXT)

    assert len(calls) == 1
    assert calls[0][0] == "post"
    assert "gemini-3.5-flash-lite" in calls[0][1]
    assert any("Direct use of automatic function calling" in record.message for record in caplog.records)


def test_gemini_38_generation_config_keeps_json_mime_without_sampling_overrides():
    from google.genai import types
    config = generation_config(types)
    assert config.response_mime_type == "application/json"
    assert config.temperature is None
    assert config.top_p is None
    assert config.top_k is None
    assert config.candidate_count is None
    assert config.tools is None
    assert config.response_schema is None
    assert config.automatic_function_calling is None


def test_afc_explicit_disable_is_only_an_offline_sdk_control_fixture():
    from google.genai import _extra_utils, types

    current = generation_config(types)
    diagnostic_only_disabled = types.GenerateContentConfig(
        response_mime_type="application/json",
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    assert _extra_utils.should_disable_afc(current) is False
    assert _extra_utils.should_disable_afc(diagnostic_only_disabled) is True


def _provider_json_response() -> str:
    return json.dumps({
        "candidates": [{
            "content": {"parts": [{"text": json.dumps({"claims": []})}]},
        }],
    })


@pytest.mark.parametrize(
    ("status_code", "response_body", "expected_error"),
    [
        (200, _provider_json_response(), None),
        (503, json.dumps({"error": {"status": "UNAVAILABLE"}}), Exception),
    ],
)
def test_default_sdk_retry_policy_makes_one_mocked_transport_attempt(
    monkeypatch, status_code, response_body, expected_error,
):
    """The adapter's default client must not retry a 503 behind its back."""
    from google.genai import _api_client

    transport_calls = []

    def fake_send(self, request, stream=False):
        transport_calls.append(request)
        return httpx.Response(status_code, text=response_body, request=request)

    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    monkeypatch.setenv("UNITRUST_GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setenv("UNITRUST_ALLOW_REAL_PROVIDER_EVAL", "1")
    monkeypatch.setattr(_api_client.SyncHttpxClient, "send", fake_send)

    adapter = GeminiQualificationAdapter()
    if expected_error is None:
        claims, _, model = adapter.extract(TEXT)
        assert claims == []
        assert model == "gemini-3.5-flash-lite"
    else:
        with pytest.raises(expected_error):
            adapter.extract(TEXT)

    assert len(transport_calls) == 1


def test_default_client_has_no_sdk_retry_options():
    from google import genai
    from google.genai import _api_client

    client = genai.Client(api_key="test-only-key")
    assert client._api_client._http_options.retry_options is None
    retry = _api_client.retry_args(None)
    assert retry["stop"].max_attempt_number == 1
