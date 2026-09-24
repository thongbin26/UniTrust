"""Build a read-only inventory from reviewed Batch 001 obligations."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANNOTATIONS = ROOT / "data" / "annotations" / "batch_001"
OUT = Path(__file__).parent

def action_value(value):
    return value.get("action_type") if value else None

def text_value(value):
    return value.get("text") if value else None

def main():
    records, actions, docs, dates, sources = [], Counter(), Counter(), Counter(), defaultdict(int)
    for path in sorted(ANNOTATIONS.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for obligation in data.get("obligations", []):
            audience = obligation.get("audience") or {}
            action = obligation.get("action") or {}
            deadline = obligation.get("deadline") or {}
            required = obligation.get("required_documents") or []
            source_id = data.get("source", {}).get("source_id")
            action_name = action_value(action)
            usable = "USABLE" if action_name else "NOT_SUITABLE"
            reason = "Reviewed actionable obligation." if action_name else "No reviewed action; not a standalone obligation."
            record = {
                "inventory_id": f"INV-{data.get('notice_id')}-{obligation.get('obligation_id')}",
                "annotation_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "annotation_record_id": obligation.get("obligation_id"), "notice_id": data.get("notice_id"),
                "version_id": data.get("version_id"), "title": data.get("title"),
                "official_source_url": data.get("url"),
                "reviewed_fields": {
                    "audience": audience.get("raw_text"), "action": action_name,
                    "object_hint": text_value(action), "deadline": deadline.get("raw_text"),
                    "amount": (obligation.get("amount") or {}).get("raw_text"),
                    "required_documents": [text_value(x) for x in required],
                    "location": text_value(obligation.get("location")),
                    "exceptions": [text_value(x) for x in obligation.get("exceptions") or []],
                },
                "supporting_text_reference": data.get("raw_text"), "usability": usable,
                "usability_reason": reason,
                "potential_benchmark_categories": [x for x, present in {
                    "ACTION_SCOPE": bool(action_name), "AUDIENCE_SCOPE": bool(audience.get("raw_text")),
                    "DATE_FULL": bool(deadline.get("normalized")), "AMOUNT": bool(obligation.get("amount")),
                    "DOCUMENT": bool(required), "LOCATION": bool(obligation.get("location")),
                }.items() if present],
                "authoring_notes": "Use only fields explicitly retained above.",
            }
            records.append(record); sources[source_id] += 1
            if action_name: actions[action_name] += 1
            if required:
                docs.update(record["reviewed_fields"]["required_documents"])
            if deadline.get("raw_text"):
                dates["full_date" if deadline.get("normalized") else "unresolved_or_other"] += 1
    fields = {name: sum(bool(r["reviewed_fields"].get(name)) for r in records) for name in ("audience","action","object_hint","deadline","amount","required_documents","location","exceptions")}
    summary = {"annotation_files_inspected": len(list(ANNOTATIONS.glob("*.json"))), "distinct_source_notices": len({r["notice_id"] for r in records}), "distinct_reviewed_obligations": len(records), "usable_obligations": sum(r["usability"] == "USABLE" for r in records), "ambiguous_obligations": 0, "not_suitable_obligations": sum(r["usability"] == "NOT_SUITABLE" for r in records), "field_support": fields, "action_distribution": dict(actions), "document_field_support": dict(docs), "deadline_structure_support": dict(dates), "source_diversity_summary": dict(sources), "potential_category_support": dict(Counter(t for r in records for t in r["potential_benchmark_categories"]))}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "source_obligation_inventory.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "source_inventory_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Reviewed source obligation inventory", "", "| ID | Notice | Action | Deadline | Why useful |", "|---|---:|---|---|---|"]
    for r in records:
        f = r["reviewed_fields"]; lines.append(f'| {r["inventory_id"]} | {r["notice_id"]} | {f["action"] or "—"} | {f["deadline"] or "—"} | {r["usability"]} |')
    (OUT / "SOURCE_INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
if __name__ == "__main__": main()
