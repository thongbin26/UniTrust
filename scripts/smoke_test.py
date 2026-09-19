"""Fast contract smoke checks against an already-running local demo."""

import httpx


class SmokeFailure(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise SmokeFailure(message)


def response_json(response):
    response.raise_for_status()
    return response.json()


def run_checks(client: httpx.Client) -> None:
    api = "http://127.0.0.1:8000"
    health = response_json(client.get(f"{api}/health"))
    require(isinstance(health, dict) and health.get("status") == "ok"
            and health.get("service") == "UniTrust" and health.get("database") == "ok", "Backend is not ready")
    print("[PASS] Backend health")

    frontend = client.get("http://127.0.0.1:8501/_stcore/health")
    frontend.raise_for_status()
    require(frontend.text.strip() == "ok", "Frontend is not ready")
    print("[PASS] Frontend health")

    notices = response_json(client.get(f"{api}/evidence/search-index"))
    index_fields = {"notice_id", "title", "source_id", "source_display_name", "searchable_text"}
    require(isinstance(notices, list) and len(notices) > 0, "Evidence index is empty or malformed")
    require(all(isinstance(item, dict) and index_fields <= item.keys() for item in notices), "Evidence index contract mismatch")
    print(f"[PASS] Evidence search-index ({len(notices)} notices)")

    profile = response_json(client.post(f"{api}/for-you", json={"major": "CNTT", "cohort": "K22"}))
    require(isinstance(profile, dict) and isinstance(profile.get("obligations"), list), "For You contract mismatch")
    obligations = profile["obligations"]
    require(bool(obligations), "For You returned no reviewed obligations")
    require(all(isinstance(item, dict) and isinstance(item.get("action_text"), str)
                and isinstance(item.get("applicability"), dict)
                and item["applicability"].get("status") in {"APPLIES", "DOES_NOT_APPLY", "UNKNOWN"}
                for item in obligations), "For You obligation contract mismatch")
    print(f"[PASS] For You ({len(obligations)} obligations)")

    verification = response_json(client.post(f"{api}/verify", json={
        "text": "Sinh viên khóa 2022 ngành CNTT ký tên theo danh sách lớp và nộp 01 ảnh thẻ 2x3 trước 16h00 ngày 26/06/2026.",
        "use_llm": False, "top_k": 5,
    }, timeout=60))
    require(isinstance(verification, dict) and isinstance(verification.get("results"), list)
            and bool(verification["results"]), "Verification returned no results")
    require(all(isinstance(item, dict)
                and item.get("verdict") in {"VERIFIED", "PARTIALLY_VERIFIED", "CONFLICT", "INSUFFICIENT_EVIDENCE"}
                and isinstance(item.get("field_results"), dict)
                for item in verification["results"]), "Verification contract mismatch")
    print("[PASS] Deterministic verification (LLM disabled)")


def main() -> int:
    try:
        with httpx.Client(timeout=10, trust_env=False) as client:
            run_checks(client)
    except (httpx.HTTPError, SmokeFailure, ValueError) as exc:
        print(f"[FAIL] Smoke test: {exc}")
        return 1
    print("Smoke test PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
