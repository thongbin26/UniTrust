import argparse
import json
from pathlib import Path

from app.extraction.evaluator import evaluate_runs
from app.extraction.llm import LLMExtractor
from app.extraction.providers.factory import get_json_provider
from app.extraction.rules import RuleExtractor
from app.extraction.types import ExtractionInput
from app.models.obligation import CanonicalNoticeAnnotation


ANNOTATION_DIR = Path(
    "data/annotations/batch_001"
)

OUTPUT_DIR = Path(
    "data/benchmark/step6"
)

# These notices are used as demonstrations for few-shot.
# They must NOT be counted in the official few-shot evaluation.
FEW_SHOT_IDS = {
    3,
    24,
}


def load_gold() -> list[CanonicalNoticeAnnotation]:
    annotations = []

    for path in sorted(
        ANNOTATION_DIR.glob("*.json")
    ):
        annotation = (
            CanonicalNoticeAnnotation.model_validate_json(
                path.read_text(
                    encoding="utf-8"
                )
            )
        )

        annotations.append(
            annotation
        )

    return annotations


def save_runs(
    method: str,
    runs,
) -> None:
    directory = (
        OUTPUT_DIR
        / method
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    for run in runs:
        path = (
            directory
            / f"notice_{run.notice_id}.json"
        )

        path.write_text(
            run.model_dump_json(
                indent=2
            ),
            encoding="utf-8",
        )


def print_metrics(
    name: str,
    metrics: dict,
) -> None:
    print()
    print(name)
    print("-" * 90)

    print(
        f"eval_n={metrics['eval_n']} "
        f"errors={metrics['errors']} "
        f"mean_latency="
        f"{metrics['latency_ms']['mean']:.1f}ms"
    )

    if (
        metrics["eval_n"] > 0
        and metrics["errors"]
        == metrics["eval_n"]
    ):
        print(
            "WARNING: ALL extraction runs failed. "
            "Do not treat these metrics as a valid "
            "model benchmark."
        )

    elif metrics["errors"] > 0:
        print(
            f"WARNING: {metrics['errors']} extraction "
            "run(s) failed. Treat these metrics as "
            "debug results, not the final benchmark."
        )

    for field in [
        "audience",
        "action",
        "location",
        "required_documents",
        "evidence",
    ]:
        value = metrics[field]

        print(
            f"{field:<20} "
            f"P={value['precision']:.3f} "
            f"R={value['recall']:.3f} "
            f"F1={value['f1']:.3f}"
        )

    print(
        "deadline EM(all)      = "
        f"{metrics['deadline_exact_match']:.3f}"
    )

    print(
        "deadline EM(present)  = "
        f"{metrics['deadline_present_exact_match']:.3f}"
    )

    print(
        "money EM(all)         = "
        f"{metrics['money_exact_match']:.3f}"
    )

    print(
        "money EM(present)     = "
        f"{metrics['money_present_exact_match']:.3f}"
    )


def run_method(
    extractor,
    gold,
    few_shot_examples=None,
):
    runs = []

    for annotation in gold:
        notice = (
            ExtractionInput.from_annotation(
                annotation
            )
        )

        # When the target itself is one of the
        # few-shot examples, do not leak its own
        # ground truth into its prompt.
        if (
            few_shot_examples is not None
            and isinstance(
                extractor,
                LLMExtractor,
            )
        ):
            extractor.examples = [
                example
                for example
                in few_shot_examples
                if (
                    example.notice_id
                    != annotation.notice_id
                )
            ]

        print(
            f"[{extractor.name}] "
            f"notice={notice.notice_id}...",
            end=" ",
            flush=True,
        )

        run = extractor.extract(
            notice
        )

        if run.error:
            print(
                f"ERROR: {run.error}"
            )
        else:
            print(
                f"OK "
                f"{run.latency_ms:.0f}ms"
            )

        runs.append(
            run
        )

    return runs


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--methods",
        nargs="+",
        choices=[
            "rules",
            "zero_shot",
            "few_shot",
            "all",
        ],
        default=["all"],
    )

    parser.add_argument(
        "--notice-ids",
        nargs="*",
        type=int,
        default=None,
        help=(
            "Run only selected notice IDs. "
            "Useful for debugging."
        ),
    )

    args = parser.parse_args()

    requested = set(
        args.methods
    )

    if "all" in requested:
        requested = {
            "rules",
            "zero_shot",
            "few_shot",
        }

    # --------------------------------------------------
    # Load all 10 reviewed annotations.
    # --------------------------------------------------

    all_gold = load_gold()

    if len(all_gold) != 10:
        raise RuntimeError(
            "Expected 10 reviewed annotations, "
            f"found {len(all_gold)}."
        )

    gold_by_id = {
        item.notice_id: item
        for item in all_gold
    }

    # --------------------------------------------------
    # Optional debug subset.
    # --------------------------------------------------

    gold = all_gold

    if args.notice_ids:
        wanted = set(
            args.notice_ids
        )

        gold = [
            item
            for item in all_gold
            if item.notice_id in wanted
        ]

        found = {
            item.notice_id
            for item in gold
        }

        missing = (
            wanted - found
        )

        if missing:
            raise RuntimeError(
                "Notice IDs not found: "
                f"{sorted(missing)}"
            )

        print(
            "Debug notice subset: "
            f"{sorted(found)}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_results = {}

    # ==================================================
    # RULE BASELINE
    # ==================================================

    if "rules" in requested:
        extractor = RuleExtractor()

        runs = run_method(
            extractor,
            gold,
        )

        save_runs(
            extractor.name,
            runs,
        )

        metrics = evaluate_runs(
            runs,
            gold_by_id,
        )

        all_results[
            extractor.name
        ] = metrics

        print_metrics(
            extractor.name,
            metrics,
        )

    # ==================================================
    # LLM PROVIDER
    # ==================================================

    provider = None

    if (
        "zero_shot" in requested
        or "few_shot" in requested
    ):
        provider = (
            get_json_provider()
        )

    # ==================================================
    # ZERO-SHOT
    # ==================================================

    if "zero_shot" in requested:
        if provider is None:
            raise RuntimeError(
                "LLM provider was not initialized."
            )

        extractor = LLMExtractor(
            provider=provider,
            mode="zero_shot",
        )

        runs = run_method(
            extractor,
            gold,
        )

        save_runs(
            extractor.name,
            runs,
        )

        metrics = evaluate_runs(
            runs,
            gold_by_id,
        )

        all_results[
            extractor.name
        ] = metrics

        print_metrics(
            extractor.name,
            metrics,
        )

        # Same held-out set used later by few-shot,
        # enabling fair zero-shot vs few-shot comparison.
        heldout = evaluate_runs(
            runs,
            gold_by_id,
            exclude_ids=FEW_SHOT_IDS,
        )

        all_results[
            extractor.name
            + "_common_heldout"
        ] = heldout

    # ==================================================
    # FEW-SHOT
    # ==================================================

    if "few_shot" in requested:
        if provider is None:
            raise RuntimeError(
                "LLM provider was not initialized."
            )

        # IMPORTANT:
        # examples must come from ALL annotations,
        # not from the debug subset.
        examples = [
            item
            for item in all_gold
            if item.notice_id
            in FEW_SHOT_IDS
        ]

        if len(examples) != 2:
            raise RuntimeError(
                "Few-shot examples "
                "3 and 24 were not found."
            )

        extractor = LLMExtractor(
            provider=provider,
            mode="few_shot",
            examples=examples,
        )

        runs = run_method(
            extractor,
            gold,
            few_shot_examples=examples,
        )

        save_runs(
            extractor.name,
            runs,
        )

        # Research-correct:
        # do NOT grade the demonstration notices.
        metrics = evaluate_runs(
            runs,
            gold_by_id,
            exclude_ids=FEW_SHOT_IDS,
        )

        all_results[
            extractor.name
        ] = metrics

        print_metrics(
            extractor.name
            + " [HELD-OUT ONLY]",
            metrics,
        )

    # ==================================================
    # SAVE METRICS
    # ==================================================

    if args.notice_ids:
        notice_suffix = "_".join(
            str(notice_id)
            for notice_id
            in sorted(
                args.notice_ids
            )
        )

        metrics_path = (
            OUTPUT_DIR
            / (
                "metrics_debug_"
                f"{notice_suffix}.json"
            )
        )

    else:
        metrics_path = (
            OUTPUT_DIR
            / "metrics.json"
        )

    metrics_path.write_text(
        json.dumps(
            all_results,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 90)
    print(
        "Metrics saved to: "
        f"{metrics_path}"
    )


if __name__ == "__main__":
    main()