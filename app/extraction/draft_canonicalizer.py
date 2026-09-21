import re
from datetime import datetime
from zoneinfo import ZoneInfo

from app.extraction.draft import ExtractionDraft
from app.extraction.grounding import find_grounded_text
from app.extraction.types import ExtractionPayload
from app.models.obligation import (
    ActionValue,
    AudienceCondition,
    DeadlineValue,
    EvidenceBackedText,
    EvidenceField,
    EvidenceSpan,
    MoneyValue,
    StudentObligation,
    TemporalPrecision,
)

ACTION_ANCHORS = {
    "register": [
        r"đăng\s*k[ýí]",
    ],
    "apply": [
        r"ứng\s*tuyển",
        r"nộp\s+đơn",
        r"đăng\s*k[ýí]\s+tham\s+gia",
    ],
    "submit": [
        r"\bnộp\b",
        r"gửi\s+hồ\s+sơ",
    ],
    "pay": [
        r"đóng\s+học\s*phí",
        r"nộp\s+học\s*phí",
        r"thanh\s+toán",
    ],
    "attend": [
        r"tham\s+gia",
    ],
    "collect": [
        r"nhận",
    ],
    "update": [
        r"cập\s+nhật",
        r"tự\s+đánh\s+giá",
    ],
    "check": [
        r"kiểm\s+tra",
        r"\bxem\b",
    ],
    "other": [
        r"thực\s+hiện",
        r"hoàn\s+tất",
    ],
}

def segment_containing_match(
    raw_text: str,
    start: int,
    end: int,
) -> str:
    left = raw_text.rfind(
        "\n",
        0,
        start,
    )

    right = raw_text.find(
        "\n",
        end,
    )

    if left == -1:
        left = 0
    else:
        left += 1

    if right == -1:
        right = len(raw_text)

    segment = raw_text[
        left:right
    ].strip()

    if segment:
        return segment

    return raw_text[start:end]


def ground_action(
    action_text: str,
    action_type,
    raw_text: str,
) -> str | None:
    # First try normal grounding.
    grounded = ground(
        action_text,
        raw_text,
    )

    if grounded is not None:
        return grounded

    # Deterministic fallback based on action type.
    action_key = (
        action_type.value
        if hasattr(action_type, "value")
        else str(action_type)
    )

    patterns = ACTION_ANCHORS.get(
        action_key,
        [],
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            raw_text,
            re.IGNORECASE,
        )

        if match:
            return segment_containing_match(
                raw_text,
                match.start(),
                match.end(),
            )

    return None

FULL_DATE_RE = re.compile(
    r"(?P<day>\d{1,2})"
    r"\s*[./-]\s*"
    r"(?P<month>\d{1,2})"
    r"\s*[./-]\s*"
    r"(?P<year>\d{4})"
)

TIME_RE = re.compile(
    r"(?P<hour>\d{1,2})"
    r"\s*(?:h|:)\s*"
    r"(?P<minute>\d{0,2})",
    re.IGNORECASE,
)

MILLION_VND_RE = re.compile(
    r"(?P<number>\d+(?:[.,]\d+)?)"
    r"\s*triệu"
    r"(?:\s*(?:đồng|vnđ|vnd|đ))?",
    re.IGNORECASE,
)

VND_RE = re.compile(
    r"(?P<number>"
    r"\d{1,3}(?:[.,\s]\d{3})+"
    r"|\d+"
    r")"
    r"\s*(?:đồng|vnđ|vnd|đ)\b",
    re.IGNORECASE,
)

THOUSAND_VND_RE = re.compile(
    r"\b(?P<number>\d+)\s*k\b",
    re.IGNORECASE,
)


class EvidenceBuilder:
    def __init__(
        self,
        raw_text: str,
    ):
        self.raw_text = raw_text
        self.items: list[EvidenceSpan] = []
        self._cache: dict[
            tuple[str, str],
            str,
        ] = {}

    def add(
        self,
        field: EvidenceField,
        grounded_text: str,
    ) -> str:
        key = (
            field.value,
            grounded_text,
        )

        if key in self._cache:
            return self._cache[key]

        evidence_id = (
            f"e{len(self.items) + 1}"
        )

        start = self.raw_text.find(
            grounded_text
        )

        if start >= 0:
            end = (
                start
                + len(grounded_text)
            )
        else:
            start = None
            end = None

        evidence = EvidenceSpan(
            evidence_id=evidence_id,
            field=field,
            text=grounded_text,
            start_char=start,
            end_char=end,
        )

        self.items.append(
            evidence
        )

        self._cache[key] = (
            evidence_id
        )

        return evidence_id


def ground(
    value: str | None,
    raw_text: str,
) -> str | None:
    if not value:
        return None

    return find_grounded_text(
        value,
        raw_text,
    )


def parse_deadline(
    grounded_text: str,
) -> tuple[
    str | None,
    TemporalPrecision,
]:
    """
    Deterministically normalize a supported date phrase.

    If a phrase contains a date range, choose the LAST
    full date as the deadline/end date.

    If no safe full date is available, abstain from
    normalization instead of guessing.
    """

    matches = list(
        FULL_DATE_RE.finditer(
            grounded_text
        )
    )

    if not matches:
        return (
            None,
            TemporalPrecision.UNKNOWN,
        )

    chosen = matches[-1]

    try:
        day = int(
            chosen.group("day")
        )
        month = int(
            chosen.group("month")
        )
        year = int(
            chosen.group("year")
        )

        # Look around the chosen date for an explicit time.
        nearby_start = max(
            0,
            chosen.start() - 60,
        )

        nearby_end = min(
            len(grounded_text),
            chosen.end() + 40,
        )

        nearby = grounded_text[
            nearby_start:nearby_end
        ]

        time_matches = list(
            TIME_RE.finditer(
                nearby
            )
        )

        if time_matches:
            time_match = (
                time_matches[-1]
            )

            hour = int(
                time_match.group("hour")
            )

            minute_raw = (
                time_match.group(
                    "minute"
                )
            )

            minute = (
                int(minute_raw)
                if minute_raw
                else 0
            )

            value = datetime(
                year,
                month,
                day,
                hour,
                minute,
                tzinfo=ZoneInfo(
                    "Asia/Ho_Chi_Minh"
                ),
            )

            return (
                value.isoformat(),
                TemporalPrecision.DATETIME,
            )

        value = datetime(
            year,
            month,
            day,
        )

        return (
            value.date().isoformat(),
            TemporalPrecision.DATE,
        )

    except ValueError:
        return (
            None,
            TemporalPrecision.UNKNOWN,
        )


def parse_vnd(
    grounded_text: str,
) -> int | None:
    """
    Deterministic VND parser.

    Supports examples such as:
    - 450.000 đồng
    - 450000 VND
    - 34 triệu đồng
    - 1,5 triệu đồng
    """

    thousand_match = THOUSAND_VND_RE.search(grounded_text)

    if thousand_match:
        return int(thousand_match.group("number")) * 1_000

    million_match = (
        MILLION_VND_RE.search(
            grounded_text
        )
    )

    if million_match:
        number = (
            million_match.group(
                "number"
            )
            .replace(",", ".")
        )

        try:
            return int(
                float(number)
                * 1_000_000
            )
        except ValueError:
            return None

    match = VND_RE.search(
        grounded_text
    )

    if not match:
        return None

    digits = re.sub(
        r"[^\d]",
        "",
        match.group("number"),
    )

    if not digits:
        return None

    return int(digits)


def draft_to_payload(
    draft: ExtractionDraft,
    raw_text: str,
) -> ExtractionPayload:
    """
    Convert an LLM semantic draft into the Canonical
    extraction payload.

    Important:
    - LLM does NOT assign evidence IDs.
    - LLM does NOT control provenance.
    - Final evidence text always comes from raw_text.
    - Unsupported optional fields are dropped.
    - An obligation without grounded ACTION evidence
      is dropped entirely.
    """

    evidence = EvidenceBuilder(
        raw_text
    )

    obligations = []

    for draft_obligation in (
        draft.obligations
    ):
        # ---------------------------------------------
        # ACTION
        # Mandatory for an obligation.
        # ---------------------------------------------

        grounded_action = ground_action(
            action_text=(
                draft_obligation.action.text
            ),
            action_type=(
                draft_obligation.action.action_type
            ),
            raw_text=raw_text,
        )

        if grounded_action is None:
            continue

        action_evidence_id = (
            evidence.add(
                EvidenceField.ACTION,
                grounded_action,
            )
        )

        action = ActionValue(
            action_type=(
                draft_obligation
                .action
                .action_type
            ),
            text=grounded_action,
            evidence_span_ids=[
                action_evidence_id
            ],
        )

        # ---------------------------------------------
        # AUDIENCE
        # ---------------------------------------------

        audience = None

        if (
            draft_obligation.audience
            is not None
        ):
            grounded_audience = ground(
                draft_obligation
                .audience
                .raw_text,
                raw_text,
            )

            if grounded_audience:
                audience_evidence_id = (
                    evidence.add(
                        EvidenceField.AUDIENCE,
                        grounded_audience,
                    )
                )

                audience = (
                    AudienceCondition(
                        raw_text=(
                            grounded_audience
                        ),
                        applies_to_all_students=(
                            draft_obligation
                            .audience
                            .applies_to_all_students
                        ),
                        faculties=(
                            draft_obligation
                            .audience
                            .faculties
                        ),
                        majors=(
                            draft_obligation
                            .audience
                            .majors
                        ),
                        cohorts=(
                            draft_obligation
                            .audience
                            .cohorts
                        ),
                        programs=(
                            draft_obligation
                            .audience
                            .programs
                        ),
                        evidence_span_ids=[
                            audience_evidence_id
                        ],
                    )
                )

        # ---------------------------------------------
        # DEADLINE
        # ---------------------------------------------

        deadline = None

        if (
            draft_obligation.deadline
            is not None
        ):
            grounded_deadline = ground(
                draft_obligation
                .deadline
                .raw_text,
                raw_text,
            )

            if grounded_deadline:
                (
                    normalized,
                    precision,
                ) = parse_deadline(
                    grounded_deadline
                )

                deadline_evidence_id = (
                    evidence.add(
                        EvidenceField.DEADLINE,
                        grounded_deadline,
                    )
                )

                deadline = DeadlineValue(
                    raw_text=(
                        grounded_deadline
                    ),
                    normalized=normalized,
                    precision=precision,
                    timezone=(
                        "Asia/Ho_Chi_Minh"
                    ),
                    evidence_span_ids=[
                        deadline_evidence_id
                    ],
                )

        # ---------------------------------------------
        # MONEY
        # ---------------------------------------------

        amount = None

        if (
            draft_obligation.amount
            is not None
        ):
            grounded_amount = ground(
                draft_obligation
                .amount
                .raw_text,
                raw_text,
            )

            if grounded_amount:
                value_vnd = parse_vnd(
                    grounded_amount
                )

                if value_vnd is not None:
                    amount_evidence_id = (
                        evidence.add(
                            EvidenceField.AMOUNT,
                            grounded_amount,
                        )
                    )

                    amount = MoneyValue(
                        raw_text=(
                            grounded_amount
                        ),
                        value_vnd=value_vnd,
                        currency="VND",
                        evidence_span_ids=[
                            amount_evidence_id
                        ],
                    )

        # ---------------------------------------------
        # LOCATION
        # ---------------------------------------------

        location = None

        if (
            draft_obligation.location
            is not None
        ):
            grounded_location = ground(
                draft_obligation
                .location
                .text,
                raw_text,
            )

            if grounded_location:
                location_evidence_id = (
                    evidence.add(
                        EvidenceField.LOCATION,
                        grounded_location,
                    )
                )

                location = (
                    EvidenceBackedText(
                        text=grounded_location,
                        evidence_span_ids=[
                            location_evidence_id
                        ],
                    )
                )

        # ---------------------------------------------
        # REQUIRED DOCUMENTS
        # ---------------------------------------------

        required_documents = []

        for document in (
            draft_obligation
            .required_documents
        ):
            grounded_document = ground(
                document.text,
                raw_text,
            )

            if not grounded_document:
                continue

            document_evidence_id = (
                evidence.add(
                    EvidenceField.REQUIRED_DOCUMENT,
                    grounded_document,
                )
            )

            required_documents.append(
                EvidenceBackedText(
                    text=(
                        grounded_document
                    ),
                    evidence_span_ids=[
                        document_evidence_id
                    ],
                )
            )

        # ---------------------------------------------
        # EXCEPTIONS
        # ---------------------------------------------

        exceptions = []

        for exception in (
            draft_obligation.exceptions
        ):
            grounded_exception = ground(
                exception.text,
                raw_text,
            )

            if not grounded_exception:
                continue

            exception_evidence_id = (
                evidence.add(
                    EvidenceField.EXCEPTION,
                    grounded_exception,
                )
            )

            exceptions.append(
                EvidenceBackedText(
                    text=(
                        grounded_exception
                    ),
                    evidence_span_ids=[
                        exception_evidence_id
                    ],
                )
            )

        obligation = StudentObligation(
            obligation_id=(
                f"o{len(obligations) + 1}"
            ),
            audience=audience,
            action=action,
            deadline=deadline,
            amount=amount,
            location=location,
            required_documents=(
                required_documents
            ),
            exceptions=exceptions,
        )

        obligations.append(
            obligation
        )

    return ExtractionPayload(
        evidence_spans=(
            evidence.items
        ),
        obligations=obligations,
    )
