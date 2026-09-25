"""Build the offline, review-first AI generalization pack from local data.

This tool never fetches sources, calls providers, or writes production data.
It reuses only existing REVIEWED/GOLD annotations as accepted labels; every
other current notice is emitted as an explicitly unreviewed review candidate.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ANNOTATIONS = ROOT / "data" / "annotations" / "batch_001"
DEFAULT_OUTPUT = Path(__file__).resolve().parent

import sys
sys.path.insert(0, str(ROOT))

from app.models.obligation import AnnotationStatus
from app.verification.claim_extractor import DeterministicTextClaimExtractor


def _jsonl_write(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def load_current_notices(database: Path) -> list[dict[str, Any]]:
    """Read the current notice version for each canonical identity."""
    connection = sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT n.notice_id, nv.version_id, n.source_id, n.title,
                   n.canonical_url, nv.raw_text, nv.content_hash
            FROM notices AS n
            JOIN notice_versions AS nv
              ON nv.notice_id = n.notice_id
             AND nv.content_hash = n.current_content_hash
            ORDER BY n.notice_id
            """
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def load_reviewed_annotations(directory: Path = ANNOTATIONS) -> dict[tuple[int, int], dict[str, Any]]:
    annotations: dict[tuple[int, int], dict[str, Any]] = {}
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("annotation_status") not in {
            AnnotationStatus.REVIEWED.value,
            AnnotationStatus.GOLD.value,
        }:
            continue
        annotations[(payload["notice_id"], payload["version_id"])] = payload
    return annotations


def _field_payload(annotation: dict[str, Any], obligation: dict[str, Any]) -> dict[str, Any]:
    """Copy reviewed fields and their evidence references without re-labeling."""
    spans = {span["evidence_id"]: span for span in annotation.get("evidence_spans", [])}

    def evidence(ids: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "evidence_id": item["evidence_id"],
                "field": item["field"],
                "text": item["text"],
                "start_char": item.get("start_char"),
                "end_char": item.get("end_char"),
            }
            for evidence_id in ids
            if (item := spans.get(evidence_id)) is not None
        ]

    audience = obligation.get("audience")
    action = obligation["action"]
    deadline = obligation.get("deadline")
    amount = obligation.get("amount")
    location = obligation.get("location")
    documents = obligation.get("required_documents", [])
    exceptions = obligation.get("exceptions", [])
    return {
        "claim_span": None,
        "claim_span_status": "NOT_ANNOTATED_IN_REVIEWED_SOURCE",
        "audience": audience,
        "action": action,
        "deadline": deadline,
        "amount": amount,
        "location": location,
        "required_documents": documents,
        "exceptions": exceptions,
        "evidence_spans": {
            "audience": evidence(audience.get("evidence_span_ids", [])) if audience else [],
            "action": evidence(action.get("evidence_span_ids", [])),
            "deadline": evidence(deadline.get("evidence_span_ids", [])) if deadline else [],
            "amount": evidence(amount.get("evidence_span_ids", [])) if amount else [],
            "location": evidence(location.get("evidence_span_ids", [])) if location else [],
            "required_documents": [
                {"text": document["text"], "evidence": evidence(document.get("evidence_span_ids", []))}
                for document in documents
            ],
            "exceptions": [
                {"text": exception["text"], "evidence": evidence(exception.get("evidence_span_ids", []))}
                for exception in exceptions
            ],
        },
    }


def _prediction_payload(text: str) -> list[dict[str, Any]]:
    """Serialize deterministic proposals without random runtime claim IDs."""
    predictions = DeterministicTextClaimExtractor().extract(text)
    fields = ("audience", "action", "deadline", "amount", "location", "object_hint")
    output = []
    for index, claim in enumerate(predictions):
        serialized = {
            "claim_index": index,
            "claim_text": claim.raw_claim_text,
            "start_char": claim.start_char,
            "end_char": claim.end_char,
            "fields": {},
            "required_documents": [],
            "exceptions": [],
        }
        for name in fields:
            value = getattr(claim, name, None)
            serialized["fields"][name] = None if value is None else {
                "text": value.text,
                "start_char": value.start_char,
                "end_char": value.end_char,
                "normalized_value": value.normalized_value,
            }
        for name in ("required_documents", "exceptions"):
            serialized[name] = [
                {
                    "text": value.text,
                    "start_char": value.start_char,
                    "end_char": value.end_char,
                    "normalized_value": value.normalized_value,
                }
                for value in getattr(claim, name)
            ]
        output.append(serialized)
    return output


def build_records(database: Path) -> list[dict[str, Any]]:
    reviewed = load_reviewed_annotations()
    records: list[dict[str, Any]] = []
    sequence = 1
    for notice in load_current_notices(database):
        identity = (notice["notice_id"], notice["version_id"])
        annotation = reviewed.get(identity)
        source = {
            "notice_id": notice["notice_id"],
            "version_id": notice["version_id"],
            "source_id": notice["source_id"],
            "title": notice["title"],
            "canonical_url": notice["canonical_url"],
            "content_hash": notice["content_hash"],
            "current_version_at_pack_generation": True,
        }
        if annotation:
            for obligation in annotation.get("obligations", []):
                records.append({
                    "record_id": f"AGV1-{sequence:03d}",
                    "review_status": "HUMAN_ACCEPTED",
                    "gold_provenance": "REUSED_REVIEWED_ANNOTATION",
                    "source": source,
                    "source_text": notice["raw_text"],
                    "obligation_id": obligation["obligation_id"],
                    "gold_claim": _field_payload(annotation, obligation),
                    "proposed_claims": _prediction_payload(notice["raw_text"]),
                    "review_action": "ACCEPTED_EXISTING_REVIEW",
                })
                sequence += 1
        else:
            records.append({
                "record_id": f"AGV1-{sequence:03d}",
                "review_status": "CANDIDATE_UNREVIEWED",
                "gold_provenance": "NONE",
                "source": source,
                "source_text": notice["raw_text"],
                "obligation_id": None,
                "gold_claim": None,
                "proposed_claims": _prediction_payload(notice["raw_text"]),
                "review_action": "ACCEPT / EDIT / REJECT",
                "notes_for_reviewer": "No reviewed obligation exists for this current notice version.",
            })
            sequence += 1
    return records


def write_pack(records: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _jsonl_write(output_dir / "dataset.jsonl", records)
    _jsonl_write(
        output_dir / "accepted_gold.jsonl",
        [record for record in records if record["review_status"] == "HUMAN_ACCEPTED"],
    )
    _jsonl_write(
        output_dir / "review_worksheet.jsonl",
        [record for record in records if record["review_status"] == "CANDIDATE_UNREVIEWED"],
    )
    source_counts: dict[str, int] = {}
    for record in records:
        source_id = record["source"]["source_id"]
        source_counts[source_id] = source_counts.get(source_id, 0) + 1
    manifest = {
        "pack_version": "ai-generalization-v1",
        "selection_policy": "all current notice versions; one record per reviewed obligation or one unreviewed notice candidate",
        "record_count": len(records),
        "human_accepted_count": sum(record["review_status"] == "HUMAN_ACCEPTED" for record in records),
        "human_review_required_count": sum(record["review_status"] == "CANDIDATE_UNREVIEWED" for record in records),
        "source_distribution": dict(sorted(source_counts.items())),
        "provider_required": False,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "unitrust.db")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    write_pack(build_records(args.database), args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
