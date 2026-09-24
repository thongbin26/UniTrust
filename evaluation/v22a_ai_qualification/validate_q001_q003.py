"""Static, provider-free validation for the Q001-Q006 draft batch."""

import json
import re
import sys
from datetime import date
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.models.obligation import ActionType


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset_draft.jsonl"
ALLOWED_PROVENANCE = {"SOURCE_DERIVED", "CONTROLLED_PARAPHRASE", "CONTROLLED_SYNTHETIC"}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def validate_span(text: str, span: dict, label: str, errors: list[str]) -> None:
    if text[span["start"] : span["end"]] != span["text"]:
        errors.append(f"{label}: expected exact source span")


def historical_input_texts() -> set[str]:
    """Read only historical JSONL evaluation inputs; never mutate frozen artifacts."""
    texts: set[str] = set()
    evaluation_root = REPOSITORY_ROOT / "evaluation"
    for path in evaluation_root.rglob("*.jsonl"):
        if path == DATASET or "v22a_ai_qualification" in path.parts:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload.get("input_text"), str):
                texts.add(normalize(payload["input_text"]))
    return texts


def main() -> int:
    candidates = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line]
    errors: list[str] = []
    ids = [candidate["id"] for candidate in candidates]
    if len(ids) != len(set(ids)):
        errors.append("duplicate candidate id")

    inventory = {
        record["inventory_id"]: record
        for record in json.loads((ROOT / "source_obligation_inventory.json").read_text(encoding="utf-8"))
    }
    allowed_actions = {action.value for action in ActionType}
    for candidate in candidates:
        label = candidate["id"]
        text = candidate["input_text"]
        if candidate["provenance"] not in ALLOWED_PROVENANCE:
            errors.append(f"{label}: invalid provenance")
        parent = candidate["parent_source_obligation_id"]
        source = candidate["source_ref"]
        if candidate["provenance"] == "CONTROLLED_SYNTHETIC":
            if parent is not None or source is not None:
                errors.append(f"{label}: synthetic candidate must have no source")
        elif parent not in inventory or not source or source.get("inventory_id") != parent:
            errors.append(f"{label}: source provenance does not match inventory")
        if candidate["claim_count"] != len(candidate["claims"]):
            errors.append(f"{label}: claim_count mismatch")
        for expected_index, claim in enumerate(candidate["claims"], start=1):
            if claim["claim_index"] != expected_index:
                errors.append(f"{label}: claim indices are not ordered")
            if text[claim["claim_span_start"] : claim["claim_span_end"]] != claim["claim_text"]:
                errors.append(f"{label}: claim span is not exact")
            for field, field_span in claim["field_spans"].items():
                validate_span(text, field_span, f"{label}.{field}", errors)
            if claim.get("action_normalized") not in allowed_actions:
                errors.append(f"{label}: invalid action enum")
            if any(value is not None for value in (claim["amount_raw"], claim["amount_value"], claim["currency"])):
                errors.append(f"{label}: amount is outside approved Q001-Q006 scope")
            if not isinstance(claim["required_documents"], list):
                errors.append(f"{label}: required_documents must be a list")
            raw_date = claim.get("deadline_raw")
            normalized_date = claim.get("deadline_normalized")
            if raw_date == "18/09" and normalized_date is not None:
                errors.append(f"{label}: invented year for missing-year date")
            if normalized_date:
                try:
                    date.fromisoformat(normalized_date)
                except ValueError:
                    errors.append(f"{label}: invalid normalized deadline")
            if label == "Q001":
                expected_audience = (
                    "Sinh viên đã được xếp lớp theo phương thức 1 hoặc 2, nếu muốn đổi lớp"
                )
                audience_span = claim["field_spans"]["audience"]
                if (
                    claim["audience"] != expected_audience
                    or audience_span["start"] != 0
                    or audience_span["end"] != 69
                    or text[0:69] != expected_audience
                ):
                    errors.append(f"{label}: approved audience applicability span mismatch")

    exact_duplicates = len(candidates) - len({candidate["input_text"] for candidate in candidates})
    normalized_duplicates = len(candidates) - len({normalize(candidate["input_text"]) for candidate in candidates})
    historical_matches = [
        candidate["id"]
        for candidate in candidates
        if normalize(candidate["input_text"]) in historical_input_texts()
    ]
    if exact_duplicates or normalized_duplicates:
        errors.append("candidate duplicate detected")
    print(f"candidates={len(candidates)}")
    print(f"claim_span_errors={sum('claim span' in error for error in errors)}")
    print(f"field_span_errors={sum('exact source span' in error for error in errors)}")
    print(f"exact_duplicates={exact_duplicates}")
    print(f"normalized_duplicates={normalized_duplicates}")
    print(f"historical_exact_overlap_count={len(historical_matches)}")
    print(f"invented_year_violations={sum('invented year' in error for error in errors)}")
    print(f"unsupported_field_violations={sum('outside approved' in error for error in errors)}")
    print(f"invalid_actions={sum('invalid action' in error for error in errors)}")
    if historical_matches:
        print(f"historical_exact_overlaps={','.join(historical_matches)}")
    if errors:
        print("static_validation=FAIL")
        print("\n".join(errors))
        return 1
    print("static_validation=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
