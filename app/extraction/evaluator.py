import re
import statistics

from app.extraction.types import (
    ExtractionRun,
)
from app.models.obligation import (
    CanonicalNoticeAnnotation,
)


def norm_text(
    value: str,
) -> str:

    value = value.casefold()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    value = re.sub(
        r"[.,;:()]+",
        "",
        value,
    )

    return value.strip()


def audience_atoms(
    annotation:
        CanonicalNoticeAnnotation,
) -> set[str]:

    result = set()

    for obligation in (
        annotation.obligations
    ):
        audience = (
            obligation.audience
        )

        if audience is None:
            continue

        if (
            audience
            .applies_to_all_students
        ):
            result.add(
                "all_students"
            )

        for value in audience.faculties:
            result.add(
                "faculty:"
                + norm_text(value)
            )

        for value in audience.majors:
            result.add(
                "major:"
                + norm_text(value)
            )

        for value in audience.cohorts:
            result.add(
                "cohort:"
                + norm_text(value)
            )

        for value in audience.programs:
            result.add(
                "program:"
                + norm_text(value)
            )

        if (
            not audience.faculties
            and not audience.majors
            and not audience.cohorts
            and not audience.programs
            and not audience
            .applies_to_all_students
            and audience.raw_text
        ):
            result.add(
                "raw:"
                + norm_text(
                    audience.raw_text
                )
            )

    return result


def action_atoms(
    annotation:
        CanonicalNoticeAnnotation,
) -> set[str]:

    return {
        obligation
        .action
        .action_type
        .value

        for obligation
        in annotation.obligations
    }


def location_atoms(
    annotation:
        CanonicalNoticeAnnotation,
) -> set[str]:

    return {
        norm_text(
            obligation.location.text
        )

        for obligation
        in annotation.obligations

        if obligation.location
    }


def document_atoms(
    annotation:
        CanonicalNoticeAnnotation,
) -> set[str]:

    return {
        norm_text(
            document.text
        )

        for obligation
        in annotation.obligations

        for document
        in obligation.required_documents
    }


def deadline_atoms(
    annotation:
        CanonicalNoticeAnnotation,
) -> set[str]:

    return {
        obligation
        .deadline
        .normalized

        for obligation
        in annotation.obligations

        if (
            obligation.deadline
            and obligation
            .deadline
            .normalized
        )
    }


def money_atoms(
    annotation:
        CanonicalNoticeAnnotation,
) -> set[int]:

    return {
        obligation
        .amount
        .value_vnd

        for obligation
        in annotation.obligations

        if obligation.amount
    }


def evidence_atoms(
    annotation:
        CanonicalNoticeAnnotation,
) -> set[str]:

    return {
        norm_text(
            evidence.text
        )

        for evidence
        in annotation.evidence_spans
    }


def count_sets(
    predicted: set,
    gold: set,
) -> tuple[int, int, int]:

    tp = len(
        predicted & gold
    )

    fp = len(
        predicted - gold
    )

    fn = len(
        gold - predicted
    )

    return tp, fp, fn


def prf(
    tp: int,
    fp: int,
    fn: int,
) -> dict:

    precision = (
        tp / (tp + fp)
        if tp + fp
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn
        else 0.0
    )

    f1 = (
        2
        * precision
        * recall
        / (
            precision
            + recall
        )
        if precision + recall
        else 0.0
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


FIELD_FUNCTIONS = {
    "audience": audience_atoms,
    "action": action_atoms,
    "location": location_atoms,
    "required_documents": (
        document_atoms
    ),
    "evidence": evidence_atoms,
}


def evaluate_runs(
    runs: list[ExtractionRun],
    gold_by_id: dict[
        int,
        CanonicalNoticeAnnotation,
    ],
    exclude_ids: set[int] | None = None,
) -> dict:

    exclude_ids = (
        exclude_ids or set()
    )

    valid_runs = [
        run
        for run in runs
        if (
            run.notice_id
            not in exclude_ids
        )
    ]

    metrics = {
        "eval_n": len(
            valid_runs
        ),
        "errors": sum(
            1
            for run in valid_runs
            if run.error
        ),
    }

    for (
        field_name,
        getter,
    ) in FIELD_FUNCTIONS.items():

        total_tp = 0
        total_fp = 0
        total_fn = 0

        for run in valid_runs:

            gold = gold_by_id[
                run.notice_id
            ]

            predicted = (
                getter(
                    run.prediction
                )
                if run.prediction
                else set()
            )

            expected = getter(
                gold
            )

            tp, fp, fn = (
                count_sets(
                    predicted,
                    expected,
                )
            )

            total_tp += tp
            total_fp += fp
            total_fn += fn

        metrics[field_name] = (
            prf(
                total_tp,
                total_fp,
                total_fn,
            )
        )

    deadline_correct = 0
    deadline_total = 0

    deadline_present_correct = 0
    deadline_present_total = 0

    money_correct = 0
    money_total = 0

    money_present_correct = 0
    money_present_total = 0

    for run in valid_runs:

        gold = gold_by_id[
            run.notice_id
        ]

        predicted_deadlines = (
            deadline_atoms(
                run.prediction
            )
            if run.prediction
            else set()
        )

        gold_deadlines = (
            deadline_atoms(
                gold
            )
        )

        deadline_total += 1

        if (
            predicted_deadlines
            == gold_deadlines
        ):
            deadline_correct += 1

        if gold_deadlines:
            deadline_present_total += 1

            if (
                predicted_deadlines
                == gold_deadlines
            ):
                deadline_present_correct += 1

        predicted_money = (
            money_atoms(
                run.prediction
            )
            if run.prediction
            else set()
        )

        gold_money = (
            money_atoms(
                gold
            )
        )

        money_total += 1

        if (
            predicted_money
            == gold_money
        ):
            money_correct += 1

        if gold_money:
            money_present_total += 1

            if (
                predicted_money
                == gold_money
            ):
                money_present_correct += 1

    metrics[
        "deadline_exact_match"
    ] = (
        deadline_correct
        / deadline_total
        if deadline_total
        else 0.0
    )

    metrics[
        "deadline_present_exact_match"
    ] = (
        deadline_present_correct
        / deadline_present_total
        if deadline_present_total
        else 0.0
    )

    metrics[
        "money_exact_match"
    ] = (
        money_correct
        / money_total
        if money_total
        else 0.0
    )

    metrics[
        "money_present_exact_match"
    ] = (
        money_present_correct
        / money_present_total
        if money_present_total
        else 0.0
    )

    latencies = [
        run.latency_ms
        for run in valid_runs
    ]

    metrics["latency_ms"] = {
        "mean": (
            statistics.mean(
                latencies
            )
            if latencies
            else 0.0
        ),
        "median": (
            statistics.median(
                latencies
            )
            if latencies
            else 0.0
        ),
    }

    return metrics