"""Run exactly one sanitized, local-user-authorized Gemini qualification smoke."""
import json
import re
import sys
import traceback
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from app.verification.gemini_qualification import (
    GeminiQualificationAdapter, PROMPT_VERSION, ProviderConfigurationError,
    ProviderGroundingError, ProviderSchemaError, SCHEMA_VERSION, prompt_hash,
    runtime_config,
)

TEXT = "K26 cần nộp CCCD trước ngày 18/09/2026."
ROOT = Path(r"C:\Users\DELL\unitrust-gemini-smoke")
SAFE_ERROR_CODES = {
    "REAL_PROVIDER_CONFIGURATION_REQUIRED", "GOOGLE_GENAI_SDK_NOT_INSTALLED",
    "INVALID_TOP_LEVEL_SCHEMA", "TRUST_VERDICT_OR_INVALID_CLAIM", "INVALID_ACTION",
    "INVALID_AMOUNT", "UNGROUNDED_FIELD", "UNGROUNDED_CLAIM", "INVENTED_YEAR",
    "MALFORMED_JSON",
}


def safe_error_code(exc: Exception) -> str:
    """Persist a stable diagnostic without serializing provider exception text."""
    return str(exc) if str(exc) in SAFE_ERROR_CODES else "PROVIDER_REQUEST_FAILED"


def _safe_origin_module(filename: str) -> str:
    """Classify a traceback filename without retaining its path."""
    normalized = filename.replace("\\", "/").lower()
    if "/google/genai/" in normalized:
        return "google.genai"
    if "/app/" in normalized or "/scripts/" in normalized or "/tests/" in normalized:
        return "unitrust"
    if "/lib/" in normalized or "/python" in normalized:
        return "python_stdlib"
    return "unknown"


def safe_exception_origin(exc: Exception) -> dict[str, object]:
    """Return the final traceback frame using path- and message-free metadata."""
    if exc.__traceback__ is None:
        return {}
    frame = traceback.extract_tb(exc.__traceback__)[-1]
    function = frame.name if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", frame.name) else "unknown"
    basename = Path(frame.filename).name
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", basename):
        basename = "unknown"
    return {
        "safe_origin_module": _safe_origin_module(frame.filename),
        "safe_origin_function": function,
        "safe_origin_file_basename": basename,
        "safe_origin_line": frame.lineno,
    }


def safe_failure_details(exc: Exception) -> dict[str, object]:
    """Return only allowlisted structural diagnostics; never exception messages."""
    details: dict[str, object] = {
        "error_class": type(exc).__name__,
        "error_code": safe_error_code(exc),
        "failure_stage": "unknown_sdk_or_local",
    }
    if isinstance(exc, ProviderConfigurationError):
        details["failure_stage"] = "configuration"
    elif isinstance(exc, ProviderSchemaError):
        details["failure_stage"] = "local_response_validation"
    elif isinstance(exc, ProviderGroundingError):
        details["failure_stage"] = "local_grounding_validation"
    else:
        try:
            from google.genai import errors as genai_errors
            if isinstance(exc, genai_errors.APIError):
                details["failure_stage"] = "provider_response"
                details["sdk_error_category"] = type(exc).__name__.upper()
                if isinstance(exc.code, int) and 100 <= exc.code <= 599:
                    details["http_status_code"] = exc.code
                if isinstance(exc.status, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", exc.status):
                    details["api_status"] = exc.status
        except ImportError:
            pass
    if isinstance(exc, TypeError):
        details["failure_stage"] = "local_type_error"
        details.update(safe_exception_origin(exc))
    return details

def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    attempted_provider_invocations = 0
    try:
        # Establish configuration before counting an external invocation.
        runtime_config()
        attempted_provider_invocations = 1
        claims, latency_ms, model = GeminiQualificationAdapter().extract(TEXT)
        result = {"status": "REAL_PROVIDER_SMOKE_PASSED", "provider": "Gemini", "model": model,
                  "prompt_version": PROMPT_VERSION, "prompt_hash": prompt_hash(), "schema_version": SCHEMA_VERSION,
                  "latency_ms": latency_ms, "request_count": 1, "schema_validation": "PASS", "grounding_validation": "PASS",
                  "claims": [claim.model_dump() for claim in claims]}
        code = 0
    except Exception as exc:
        result = {
            "status": safe_error_code(exc),
            "request_count": attempted_provider_invocations,
            **safe_failure_details(exc),
        }
        code = 1
    (ROOT / "smoke_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(result["status"])
    return code

if __name__ == "__main__":
    raise SystemExit(main())
