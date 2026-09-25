"""Offline evaluation for the review-first AI generalization pack.

Only HUMAN_ACCEPTED records participate in metrics.  Candidate records stay in
the review worksheet and never become pseudo-gold.  The retrieval path loads
the published dense cache read-only and uses the verification-specific current
view, so historical versions cannot count as correct results.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PACK = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.retrieval.bm25 import BM25Retriever
from app.retrieval.chunking import build_corpus
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.verification.claim_extractor import DeterministicTextClaimExtractor

FIELDS = ("action", "deadline", "amount", "audience", "location")
FAILURE_LAYERS = (
    "EXTRACTION", "NORMALIZATION", "RETRIEVAL", "REVIEWED_EVIDENCE_SELECTION",
    "TEMPORAL", "APPLICABILITY", "OTHER",
)
ANALYSIS_ERROR_SUBTYPES = {
    "SEMANTIC_ROLE": {"AGV1-023", "AGV1-025", "AGV1-027", "AGV1-039", "AGV1-042"},
    "TEMPORAL_ROLE": {"AGV1-011", "AGV1-012", "AGV1-024", "AGV1-040", "AGV1-046", "AGV1-047", "AGV1-048"},
    "MULTI_OBLIGATION_SEGMENTATION": {"AGV1-028", "AGV1-034", "AGV1-041"},
    "FIELD_ROLE": {"AGV1-038", "AGV1-049"},
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def accepted_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if record["review_status"] == "HUMAN_ACCEPTED"]


def accepted_claim_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand accepted records only for per-obligation measurement.

    Human adjudication can retain one source record while explicitly marking
    multiple independent obligations.  Record counts and claim counts are
    intentionally kept separate in metrics and reports.
    """
    expanded: list[dict[str, Any]] = []
    for record in accepted_records(records):
        claims = record.get("gold_claims") or [record["gold_claim"]]
        for index, claim in enumerate(claims):
            item = dict(record)
            item["gold_claim"] = claim
            item["claim_index"] = index
            expanded.append(item)
    return expanded


def _normalize_location(value: str) -> str:
    return " ".join(value.casefold().split())


def gold_value(record: dict[str, Any], field: str) -> str | int | None:
    claim = record["gold_claim"]
    if field == "action":
        return claim["action"]["action_type"]
    if field == "deadline":
        deadline = claim.get("deadline")
        return deadline.get("normalized") if deadline else None
    if field == "amount":
        amount = claim.get("amount")
        return amount.get("value_vnd") if amount else None
    if field == "audience":
        audience = claim.get("audience")
        cohorts = audience.get("cohorts", []) if audience else []
        return cohorts[0] if len(cohorts) == 1 else None
    if field == "location":
        location = claim.get("location")
        return _normalize_location(location["text"]) if location else None
    raise KeyError(field)


def predicted_values(text: str, field: str) -> list[str | int]:
    values: list[str | int] = []
    for claim in DeterministicTextClaimExtractor().extract(text):
        value = getattr(claim, field)
        if value is None or value.normalized_value is None:
            continue
        normalized = value.normalized_value
        values.append(_normalize_location(normalized) if field == "location" else normalized)
    return values


def extraction_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for field in FIELDS:
        support = matched = predicted_count = 0
        for record in records:
            expected = gold_value(record, field)
            actual = predicted_values(record["source_text"], field)
            predicted_count += len(actual)
            if expected is None:
                continue
            support += 1
            matched += int(expected in actual)
        if support == 0:
            results[field] = {"status": "NOT_YET_MEASURED", "support_n": 0}
            continue
        precision = matched / predicted_count if predicted_count else None
        recall = matched / support
        results[field] = {
            "status": "MEASURED",
            "support_n": support,
            "matched_n": matched,
            "predicted_value_n": predicted_count,
            "field_presence_accuracy": recall,
            "precision": precision,
            "recall": recall,
            "f1": 0.0 if not precision or not recall else 2 * precision * recall / (precision + recall),
        }
    return results


def source_derived_query(record: dict[str, Any]) -> str:
    claim = record["gold_claim"]
    pieces = [claim["action"]["text"]]
    if claim.get("deadline"):
        pieces.append(claim["deadline"]["raw_text"])
    if claim.get("audience") and claim["audience"].get("raw_text"):
        pieces.append(claim["audience"]["raw_text"])
    return " ".join(pieces)


def build_read_only_current_retriever() -> HybridRetriever:
    """Load existing cache only; never rebuild or publish embeddings."""
    chunks = build_corpus()
    bm25 = BM25Retriever()
    bm25.index(chunks)
    dense = DenseRetriever(local_files_only=True)
    if not dense.load_cache(chunks):
        raise RuntimeError("Published dense cache cannot be loaded read-only; refusing to rebuild it.")
    hybrid = HybridRetriever([bm25, dense])
    hybrid.chunks = chunks
    return hybrid


def retrieval_metrics(records: list[dict[str, Any]], retriever: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    traces: list[dict[str, Any]] = []
    for record in records:
        expected = (record["source"]["notice_id"], record["source"]["version_id"])
        results = retriever.search_current(source_derived_query(record), top_k=5)
        # A broken implementation returning a historical chunk must be visible
        # as a violation and must never receive retrieval-credit by identity.
        identities = [
            (item.chunk.notice_id, item.chunk.version_id)
            for item in results
            if item.chunk.is_latest_version
        ]
        traces.append({
            "record_id": record["record_id"],
            "claim_index": record.get("claim_index", 0),
            "expected": {"notice_id": expected[0], "version_id": expected[1]},
            "query": source_derived_query(record),
            "retrieved": [
                {"notice_id": item.chunk.notice_id, "version_id": item.chunk.version_id,
                 "is_latest_version": item.chunk.is_latest_version}
                for item in results
            ],
            "rank": identities.index(expected) + 1 if expected in identities else None,
        })
    n = len(traces)
    ranks = [trace["rank"] for trace in traces]
    stale = sum(not item["is_latest_version"] for trace in traces for item in trace["retrieved"])
    return {
        "status": "MEASURED",
        "n": n,
        "recall_at_1": sum(rank == 1 for rank in ranks) / n if n else None,
        "recall_at_3": sum(rank is not None and rank <= 3 for rank in ranks) / n if n else None,
        "recall_at_5": sum(rank is not None and rank <= 5 for rank in ranks) / n if n else None,
        "mrr": sum(1 / rank for rank in ranks if rank is not None) / n if n else None,
        "current_version_correctness": sum(rank is not None for rank in ranks) / n if n else None,
        "stale_version_retrieval_violations": stale,
    }, traces


def evaluate_provider_output(gold_records: list[dict[str, Any]], predictions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Provider-neutral future comparison contract; no provider is invoked here."""
    return {
        "evaluation_population": "HUMAN_ACCEPTED_ONLY",
        "gold_record_count": len(gold_records),
        "prediction_record_count": len(predictions),
        "comparable_fields": list(FIELDS),
        "required_provenance": ["record_id", "provider_id", "model_id", "field_spans"],
        "runtime_authorization": "NOT_GRANTED_BY_THIS_PACK",
    }


def failure_taxonomy(records: list[dict[str, Any]], retrieval_traces: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter({name: 0 for name in FAILURE_LAYERS})
    trace_by_id = {(trace["record_id"], trace.get("claim_index", 0)): trace for trace in retrieval_traces}
    for record in records:
        trace = trace_by_id[(record["record_id"], record.get("claim_index", 0))]
        if trace["rank"] is None:
            counts["RETRIEVAL"] += 1
            continue
        if any(
            gold_value(record, field) is not None
            and gold_value(record, field) not in predicted_values(record["source_text"], field)
            for field in FIELDS
        ):
            counts["EXTRACTION"] += 1
    return dict(counts)


def analysis_extraction_error_breakdown(records: list[dict[str, Any]]) -> dict[str, int]:
    """Human-review analysis only; it has no runtime or verdict effect."""
    accepted_ids = {record["record_id"] for record in records}
    counts = {name: len(record_ids & accepted_ids) for name, record_ids in ANALYSIS_ERROR_SUBTYPES.items()}
    counts["MISSING_FIELD"] = 0
    counts["OTHER_EXTRACTION"] = 0
    return counts


def markdown_report(metrics: dict[str, Any]) -> str:
    retrieval = metrics["retrieval"]
    return (
        "# AI Generalization Evaluation Pack V1\n\n"
        f"- Candidate records: {metrics['dataset']['total_candidates']}\n"
        f"- Human-accepted records: {metrics['dataset']['human_accepted_record_count']}\n"
        f"- Human-accepted obligations: {metrics['dataset']['human_accepted_obligation_count']}\n"
        f"- Human review required: {metrics['dataset']['human_review_required']}\n\n"
        "## Measured\n\n"
        f"- Current-only Recall@1: {retrieval['recall_at_1']:.4f}\n"
        f"- Current-only Recall@3: {retrieval['recall_at_3']:.4f}\n"
        f"- Current-only Recall@5: {retrieval['recall_at_5']:.4f}\n"
        f"- MRR: {retrieval['mrr']:.4f}\n"
        f"- Stale-version violations: {retrieval['stale_version_retrieval_violations']}\n\n"
        "## Not Yet Measured\n\n"
        "Unreviewed candidates are excluded from all metrics. Gemini results require a qualified provider and separately persisted, grounded predictions.\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-dir", type=Path, default=PACK)
    parser.add_argument("--output-dir", type=Path, default=PACK / "reports")
    args = parser.parse_args(argv)
    records = load_jsonl(args.pack_dir / "dataset.jsonl")
    gold_records = accepted_records(records)
    gold = accepted_claim_records(records)
    if not gold:
        raise RuntimeError("No HUMAN_ACCEPTED records are available for evaluation.")
    if any(not record["source"]["current_version_at_pack_generation"] for record in gold):
        raise RuntimeError("Historical records cannot enter the current-only benchmark.")
    retriever = build_read_only_current_retriever()
    retrieval, traces = retrieval_metrics(gold, retriever)
    source_distribution = Counter(record["source"]["source_id"] for record in records)
    metrics = {
        "pack_version": "ai-generalization-v1",
        "dataset": {
            "total_candidates": len(records),
            "human_accepted_record_count": len(gold_records),
            "human_accepted_obligation_count": len(gold),
            "human_rejected_count": sum(record["review_status"] == "REJECTED" for record in records),
            "human_review_required": sum(record["review_status"] == "CANDIDATE_UNREVIEWED" for record in records),
            "source_distribution": dict(sorted(source_distribution.items())),
        },
        "extraction": extraction_metrics(gold),
        "retrieval": retrieval,
        "failure_taxonomy": failure_taxonomy(gold, traces),
        "analysis_extraction_error_breakdown": analysis_extraction_error_breakdown(gold),
        "future_gemini_contract": evaluate_provider_output(gold, {}),
        "provider_requests_executed": 0,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "retrieval_traces.jsonl").write_text(
        "".join(json.dumps(trace, ensure_ascii=False) + "\n" for trace in traces), encoding="utf-8"
    )
    (args.output_dir / "REPORT.md").write_text(markdown_report(metrics), encoding="utf-8")
    print(json.dumps({"status": "completed", "metrics": metrics}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
