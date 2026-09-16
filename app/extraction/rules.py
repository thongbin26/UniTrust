import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.extraction.base import Extractor
from app.extraction.common import (
    build_prediction,
)
from app.extraction.types import (
    ExtractionInput,
    ExtractionPayload,
    ExtractionRun,
)
from app.models.obligation import (
    ActionType,
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


DATE_RE = re.compile(
    r"(?P<day>\d{1,2})\s*/\s*"
    r"(?P<month>\d{1,2})\s*/\s*"
    r"(?P<year>\d{4})"
)

TIME_RE = re.compile(
    r"(?P<hour>\d{1,2})"
    r"\s*(?:h|:)\s*"
    r"(?P<minute>\d{2})",
    re.IGNORECASE,
)

MONEY_RE = re.compile(
    r"(?P<number>"
    r"\d{1,3}(?:[.\s]\d{3})+"
    r"|\d+"
    r")"
    r"\s*(?:đồng|VND|đ)"
    r"(?!\w)",
    re.IGNORECASE,
)


AUDIENCE_RE = re.compile(
    r"(?:(?:tất cả|các)\s+)?"
    r"(?:em\s+)?"
    r"sinh\s+viên"
    r"[^.;\n]{0,180}",
    re.IGNORECASE,
)


ACTION_PATTERNS = [
    (
        ActionType.PAY,
        re.compile(
            r"(?:nộp|đóng|thanh toán)"
            r"\s+(?:học\s*phí|lệ\s*phí|phí)",
            re.IGNORECASE,
        ),
    ),
    (
        ActionType.REGISTER,
        re.compile(
            r"đăng\s*k[ýí]",
            re.IGNORECASE,
        ),
    ),
    (
        ActionType.APPLY,
        re.compile(
            r"(?:ứng\s*tuyển|"
            r"đề\s+nghị\s+xét)",
            re.IGNORECASE,
        ),
    ),
    (
        ActionType.SUBMIT,
        re.compile(
            r"\bnộp\b",
            re.IGNORECASE,
        ),
    ),
    (
        ActionType.ATTEND,
        re.compile(
            r"tham\s+gia",
            re.IGNORECASE,
        ),
    ),
    (
        ActionType.UPDATE,
        re.compile(
            r"(?:tự\s+đánh\s+giá|"
            r"cập\s+nhật)",
            re.IGNORECASE,
        ),
    ),
    (
        ActionType.CHECK,
        re.compile(
            r"(?:xem|kiểm\s+tra)",
            re.IGNORECASE,
        ),
    ),
    (
        ActionType.OTHER,
        re.compile(
            r"(?:thực\s+hiện|"
            r"hoàn\s+tất)",
            re.IGNORECASE,
        ),
    ),
]


DOCUMENT_RE = re.compile(
    r"(?:"
    r"CMND|CCCD|"
    r"ảnh\s+thẻ[^.;\n]*|"
    r"bảng\s+điểm[^.;\n]*|"
    r"chứng\s+chỉ[^.;\n]*|"
    r"sơ\s+yếu\s+lý\s+lịch[^.;\n]*|"
    r"thư\s+tự\s+giới\s+thiệu[^.;\n]*|"
    r"bản\s+sao\s+hộ\s+chiếu|"
    r"phiếu\s+đăng\s+k[ýí][^.;\n]*|"
    r"đơn\s+xin[^.;\n]*"
    r")",
    re.IGNORECASE,
)


LOCATION_RE = re.compile(
    r"(?:Địa\s*điểm\s*:?\s*|"
    r"tại\s+)"
    r"(?P<location>"
    r"(?:Phòng|Khu|Ban|Trường)"
    r"[^.;\n]{2,120}"
    r")",
    re.IGNORECASE,
)


def normalize_spaces(
    value: str,
) -> str:
    return " ".join(
        value.split()
    )


def normalize_money(
    raw: str,
) -> int:

    digits = re.sub(
        r"[^\d]",
        "",
        raw,
    )

    return int(digits)


def normalize_date(
    match: re.Match,
    nearby_text: str,
) -> tuple[str, TemporalPrecision]:

    day = int(
        match.group("day")
    )

    month = int(
        match.group("month")
    )

    year = int(
        match.group("year")
    )

    before = nearby_text[
        max(
            0,
            match.start() - 40,
        ):
        match.start()
    ]

    time_matches = list(
        TIME_RE.finditer(before)
    )

    if time_matches:
        time_match = (
            time_matches[-1]
        )

        hour = int(
            time_match.group("hour")
        )

        minute = int(
            time_match.group("minute")
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


def line_containing(
    text: str,
    start: int,
    end: int,
) -> str:

    left = text.rfind(
        "\n",
        0,
        start,
    )

    right = text.find(
        "\n",
        end,
    )

    if left == -1:
        left = 0
    else:
        left += 1

    if right == -1:
        right = len(text)

    value = text[
        left:right
    ].strip()

    if not value:
        value = text[
            start:end
        ]

    return value


class EvidenceBuilder:

    def __init__(self):
        self.items: list[
            EvidenceSpan
        ] = []

        self.counter = 0

    def add(
        self,
        field: EvidenceField,
        text: str,
    ) -> str:

        self.counter += 1

        evidence_id = (
            f"e{self.counter}"
        )

        self.items.append(
            EvidenceSpan(
                evidence_id=evidence_id,
                field=field,
                text=text,
            )
        )

        return evidence_id


def detect_audience(
    text: str,
    evidence: EvidenceBuilder,
) -> AudienceCondition | None:

    match = AUDIENCE_RE.search(
        text
    )

    if not match:
        return None

    raw = match.group(0).strip()

    evidence_id = evidence.add(
        EvidenceField.AUDIENCE,
        raw,
    )

    cohorts = []

    for year in re.findall(
        r"kh[oó]a"
        r"(?:\s+tuyển\s+sinh)?"
        r"\s*(20\d{2})",
        raw,
        re.IGNORECASE,
    ):
        cohorts.append(
            f"K{year[-2:]}"
        )

    majors = []

    if re.search(
        r"\bCNTT\b|"
        r"Công\s+nghệ\s+Thông\s+tin",
        raw,
        re.IGNORECASE,
    ):
        majors.append("CNTT")

    programs = []

    if re.search(
        r"chính\s+quy",
        raw,
        re.IGNORECASE,
    ):
        programs.append(
            "chính quy"
        )

    if re.search(
        r"chương\s+trình\s+tiên\s+tiến",
        raw,
        re.IGNORECASE,
    ):
        programs.append(
            "Chương trình tiên tiến"
        )

    return AudienceCondition(
        raw_text=raw,
        applies_to_all_students=bool(
            re.search(
                r"tất\s+cả.*sinh\s+viên",
                raw,
                re.IGNORECASE,
            )
        ),
        faculties=[],
        majors=majors,
        cohorts=sorted(
            set(cohorts)
        ),
        programs=programs,
        evidence_span_ids=[
            evidence_id
        ],
    )


def find_deadline_after(
    text: str,
    action_end: int,
    evidence: EvidenceBuilder,
) -> DeadlineValue | None:

    window_end = min(
        len(text),
        action_end + 350,
    )

    window = text[
        action_end:window_end
    ]

    matches = list(
        DATE_RE.finditer(window)
    )

    if not matches:
        return None

    if (
        len(matches) > 1
        and re.search(
            r"\bđến\b",
            window,
            re.IGNORECASE,
        )
    ):
        chosen = matches[-1]
    else:
        chosen = matches[0]

    absolute_start = (
        action_end
        + chosen.start()
    )

    absolute_end = (
        action_end
        + chosen.end()
    )

    quote = line_containing(
        text,
        absolute_start,
        absolute_end,
    )

    normalized, precision = (
        normalize_date(
            chosen,
            window,
        )
    )

    evidence_id = evidence.add(
        EvidenceField.DEADLINE,
        quote,
    )

    return DeadlineValue(
        raw_text=quote,
        normalized=normalized,
        precision=precision,
        timezone=(
            "Asia/Ho_Chi_Minh"
        ),
        evidence_span_ids=[
            evidence_id
        ],
    )


def find_amount_after(
    text: str,
    action_end: int,
    evidence: EvidenceBuilder,
) -> MoneyValue | None:

    window = text[
        action_end:
        min(
            len(text),
            action_end + 200,
        )
    ]

    match = MONEY_RE.search(
        window
    )

    if not match:
        return None

    raw = match.group(0)

    evidence_id = evidence.add(
        EvidenceField.AMOUNT,
        raw,
    )

    return MoneyValue(
        raw_text=raw,
        value_vnd=(
            normalize_money(raw)
        ),
        currency="VND",
        evidence_span_ids=[
            evidence_id
        ],
    )


def find_location_after(
    text: str,
    action_end: int,
    evidence: EvidenceBuilder,
) -> EvidenceBackedText | None:

    window = text[
        action_end:
        min(
            len(text),
            action_end + 400,
        )
    ]

    match = LOCATION_RE.search(
        window
    )

    if not match:
        return None

    raw = match.group(
        "location"
    ).strip()

    evidence_id = evidence.add(
        EvidenceField.LOCATION,
        raw,
    )

    return EvidenceBackedText(
        text=normalize_spaces(
            raw
        ),
        evidence_span_ids=[
            evidence_id
        ],
    )


def detect_documents(
    text: str,
    evidence: EvidenceBuilder,
) -> list[EvidenceBackedText]:

    results = []
    seen = set()

    for match in DOCUMENT_RE.finditer(
        text
    ):
        raw = match.group(0).strip()

        normalized = (
            normalize_spaces(raw)
        )

        key = normalized.casefold()

        if key in seen:
            continue

        seen.add(key)

        evidence_id = evidence.add(
            EvidenceField.REQUIRED_DOCUMENT,
            raw,
        )

        results.append(
            EvidenceBackedText(
                text=normalized,
                evidence_span_ids=[
                    evidence_id
                ],
            )
        )

        if len(results) >= 8:
            break

    return results


class RuleExtractor(Extractor):

    @property
    def name(self) -> str:
        return "rules_v0.1"

    def extract(
        self,
        notice: ExtractionInput,
    ) -> ExtractionRun:

        started = (
            time.perf_counter()
        )

        try:
            evidence = EvidenceBuilder()

            audience = detect_audience(
                notice.raw_text,
                evidence,
            )

            documents = detect_documents(
                notice.raw_text,
                evidence,
            )

            action_matches = []

            for (
                action_type,
                pattern,
            ) in ACTION_PATTERNS:

                for match in pattern.finditer(
                    notice.raw_text
                ):
                    action_matches.append(
                        (
                            match.start(),
                            match.end(),
                            action_type,
                            match,
                        )
                    )

            action_matches.sort(
                key=lambda item: item[0]
            )

            obligations = []

            seen_spans = set()

            for (
                start,
                end,
                action_type,
                match,
            ) in action_matches:

                span_key = (
                    start,
                    end,
                )

                if span_key in seen_spans:
                    continue

                seen_spans.add(
                    span_key
                )

                raw_action = (
                    match.group(0)
                )

                action_evidence_id = (
                    evidence.add(
                        EvidenceField.ACTION,
                        raw_action,
                    )
                )

                deadline = (
                    find_deadline_after(
                        notice.raw_text,
                        end,
                        evidence,
                    )
                )

                amount = None

                if (
                    action_type
                    == ActionType.PAY
                ):
                    amount = (
                        find_amount_after(
                            notice.raw_text,
                            end,
                            evidence,
                        )
                    )

                location = (
                    find_location_after(
                        notice.raw_text,
                        end,
                        evidence,
                    )
                )

                attach_documents = []

                if action_type in {
                    ActionType.SUBMIT,
                    ActionType.APPLY,
                    ActionType.REGISTER,
                }:
                    attach_documents = (
                        documents
                    )

                obligations.append(
                    StudentObligation(
                        obligation_id=(
                            f"o"
                            f"{len(obligations)+1}"
                        ),

                        audience=audience,

                        action=ActionValue(
                            action_type=(
                                action_type
                            ),
                            text=(
                                normalize_spaces(
                                    raw_action
                                )
                            ),
                            evidence_span_ids=[
                                action_evidence_id
                            ],
                        ),

                        deadline=deadline,

                        amount=amount,

                        location=location,

                        required_documents=(
                            attach_documents
                        ),

                        exceptions=[],
                    )
                )

                if len(obligations) >= 6:
                    break

            payload = ExtractionPayload(
                evidence_spans=(
                    evidence.items
                ),
                obligations=obligations,
            )

            prediction = build_prediction(
                notice,
                payload,
                self.name,
            )

            error = None

        except Exception as exc:
            prediction = None
            error = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

        latency_ms = (
            time.perf_counter()
            - started
        ) * 1000

        return ExtractionRun(
            method=self.name,
            notice_id=notice.notice_id,
            provider=None,
            model=None,
            latency_ms=latency_ms,
            error=error,
            prediction=prediction,
        )