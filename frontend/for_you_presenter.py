"""Presentation-only grouping for the Dành cho bạn feed."""


def is_visible_obligation(item: dict) -> bool:
    status = item.get("actionability_status")
    # Missing/new statuses stay visible: the feed must fail safe, never hide an
    # obligation unless the backend has established EXPIRED explicitly.
    return status != "EXPIRED"


def group_visible_obligations(items: list[dict]) -> dict[str, list[dict]]:
    groups = {
        "APPLIES": [],
        "UNKNOWN": [],
        "DOES_NOT_APPLY": [],
    }
    for item in items:
        if not is_visible_obligation(item):
            continue
        applicability = item.get("applicability", {}).get("status")
        if applicability in groups:
            groups[applicability].append(item)
    return groups
