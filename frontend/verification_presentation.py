"""Small, deterministic presentation rules for verification results."""


APPLICABLE_EVIDENCE_VERDICTS = {
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "CONFLICT",
}


def should_render_official_evidence(result: dict) -> bool:
    """Return whether provenance is usable evidence rather than retrieval context."""
    if not result.get("primary_provenance"):
        return False
    if result.get("abstention_reason") == "NO_OFFICIAL_FIELD":
        return False
    return result.get("verdict") in APPLICABLE_EVIDENCE_VERDICTS
