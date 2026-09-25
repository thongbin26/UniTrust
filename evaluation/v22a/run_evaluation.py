"""Offline V2.2A structured-claim evaluation with split discipline."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.verification.claim_extractor import DeterministicTextClaimExtractor

ROOT = Path(__file__).parent
FIELDS = ("action", "deadline", "amount", "audience", "location", "object_hint")


def _value(claim, field):
    value = getattr(claim, field, None)
    return None if value is None else value.normalized_value


def _score_field(gold_claims, predicted_claims, field):
    counts = Counter()
    span_exact = 0
    support = 0
    for index, gold_claim in enumerate(gold_claims):
        expected = gold_claim["fields"].get(field)
        actual = _value(predicted_claims[index], field) if index < len(predicted_claims) else None
        if expected is not None:
            support += 1
            if actual == expected:
                counts["tp"] += 1
                value = getattr(predicted_claims[index], field)
                span_exact += int(value is not None and value.text in gold_claim["text"])
            else:
                counts["fn"] += 1
        elif actual is not None:
            counts["fp"] += 1
    precision = counts["tp"] / (counts["tp"] + counts["fp"]) if counts["tp"] + counts["fp"] else None
    recall = counts["tp"] / (counts["tp"] + counts["fn"]) if counts["tp"] + counts["fn"] else None
    f1 = (2 * precision * recall / (precision + recall)) if precision and recall else 0.0
    return {
        "support_n": support,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact_normalized_value_accuracy": counts["tp"] / support if support else None,
        "span_exact_accuracy": span_exact / support if support else None,
    }


def evaluate(cases):
    extractor = DeterministicTextClaimExtractor()
    predictions = [extractor.extract(case["text"]) for case in cases]
    correct_count = sum(len(predicted) == case["claim_count"] for predicted, case in zip(predictions, cases))
    boundary_correct = sum(
        len(predicted) == len(case["claims"])
        and all(claim.raw_claim_text == gold["text"] for claim, gold in zip(predicted, case["claims"]))
        for predicted, case in zip(predictions, cases)
    )
    gold_claims = [gold for case in cases for gold in case["claims"]]
    predicted_claims = [claim for predicted in predictions for claim in predicted]
    expected_claims = sum(case["claim_count"] for case in cases)
    observed_claims = sum(len(predicted) for predicted in predictions)
    return {
        "n": len(cases),
        "mode": "DETERMINISTIC",
        "provider": "NOT_EVALUATED",
        "claim_count_accuracy": correct_count / len(cases),
        "claim_boundary_accuracy": boundary_correct / len(cases),
        "missed_claims": max(0, expected_claims - observed_claims),
        "hallucinated_claims": max(0, observed_claims - expected_claims),
        "field_metrics": {
            field: _score_field(gold_claims, predicted_claims, field)
            for field in FIELDS
        },
        "invalid_output_rate": 0.0,
        "fallback_rate": 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "held_out"), required=True)
    args = parser.parse_args()
    cases = [
        json.loads(line)
        for line in (ROOT / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        if json.loads(line)["split"] == args.split
    ]
    print(json.dumps({"split": args.split, **evaluate(cases)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
