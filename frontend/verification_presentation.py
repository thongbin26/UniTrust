"""Small, deterministic presentation rules for verification results."""


APPLICABLE_EVIDENCE_VERDICTS = {
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "CONFLICT",
}


def has_verified_primary_information(response: dict) -> bool:
    """Identify the narrow partial-result pattern safe to explain positively.

    A message remains internally ``PARTIALLY_VERIFIED``.  This helper only
    distinguishes the presentation case where verified, current official
    evidence exists and every other segment was abstained because it contains
    no supported field to compare.  It never manufactures evidence or changes
    any verification verdict.
    """
    results = response.get("results", [])
    if response.get("message_verdict") != "PARTIALLY_VERIFIED" or not results:
        return False

    verified = [result for result in results if result.get("verdict") == "VERIFIED"]
    if not verified:
        return False
    if any(
        not should_render_official_evidence(result)
        or result.get("temporal_status") != "CURRENT"
        for result in verified
    ):
        return False

    remaining = [result for result in results if result.get("verdict") != "VERIFIED"]
    return bool(remaining) and all(
        result.get("verdict") == "INSUFFICIENT_EVIDENCE"
        and result.get("abstention_reason") == "UNSUPPORTED_CLAIM_FIELD"
        for result in remaining
    )


def should_render_official_evidence(result: dict) -> bool:
    """Return whether provenance is usable evidence rather than retrieval context."""
    if not result.get("primary_provenance"):
        return False
    if result.get("abstention_reason") == "NO_OFFICIAL_FIELD":
        return False
    return result.get("verdict") in APPLICABLE_EVIDENCE_VERDICTS
