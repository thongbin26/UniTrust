"""Offline-first runner for Q001-Q006 Gemini qualification measurement."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from app.verification.gemini_qualification import GeminiQualificationAdapter
from evaluation.v22a_ai_qualification.provider_qualification import (
    ROOT, evaluate_cases, load_accepted_cases, offline_extractor, write_reports,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure Q001-Q006 provider extraction; never qualifies a provider.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--offline-fixtures", type=Path, help="JSON object keyed by Q001-Q006; never contacts a provider.")
    mode.add_argument("--real-provider", action="store_true", help="Requires UNITRUST_ALLOW_REAL_PROVIDER_EVAL=1 and configured Gemini credentials.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    cases = load_accepted_cases()
    if args.real_provider:
        result = evaluate_cases(cases, GeminiQualificationAdapter().extract, real_provider=True)
    else:
        payloads = json.loads(args.offline_fixtures.read_text(encoding="utf-8"))
        result = evaluate_cases(cases, offline_extractor(payloads, cases), real_provider=False)
    json_path, markdown_path = write_reports(result, args.output_dir)
    print(result["status"])
    print(json_path)
    print(markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
