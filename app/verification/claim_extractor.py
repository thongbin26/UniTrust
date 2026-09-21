import re
import unicodedata
from typing import Protocol
import uuid

from app.extraction.draft_canonicalizer import parse_deadline, parse_vnd
from app.models.obligation import ActionType
from app.verification.models import DecomposedUserClaim, TypedUserField


class ClaimExtractor(Protocol):
    def extract(self, text: str) -> list[DecomposedUserClaim]: ...


_BLANK_LINE_RE = re.compile(r"(?:\r?\n[ \t]*){2,}")
_SENTENCE_END_RE = re.compile(r"(?:\.\s+|[!?]+)")

_FULL_DATE_RE = re.compile(
    r"(?:(?:trước|đến)\s+(?:hết\s+)?ngày\s+|hạn\s+cuối\s*:?[ \t]*)?"
    r"(?P<date>\d{1,2}[./-]\d{1,2}[./-]\d{4})",
    re.IGNORECASE,
)
_MISSING_YEAR_DATE_RE = re.compile(
    r"(?:(?:trước|đến)\s+(?:hết\s+)?ngày\s+|hạn\s+cuối\s*:?[ \t]*)"
    r"(?P<date>\d{1,2}[./-]\d{1,2})(?![./-]\d)",
    re.IGNORECASE,
)
_MONEY_RE = re.compile(
    r"\b(?P<vnd>\d{1,3}(?:[.,\s]\d{3})+|\d+)\s*(?:đồng|vnđ|vnd|đ)\b"
    r"|\b(?P<thousand>\d+\s*k)\b",
    re.IGNORECASE,
)

_AUDIENCE_PATTERNS = (
    re.compile(r"\b(?:sinh\s+viên|sv)\s+k\s*(?P<year>\d{2})\b", re.IGNORECASE),
    re.compile(r"\b(?:sinh\s+viên|sv)\s+khóa\s*(?P<year>\d{2})\b", re.IGNORECASE),
    re.compile(
        r"\b(?:sinh\s+viên\s+)?khóa\s+tuyển\s+sinh\s+(?P<year>20\d{2})\b",
        re.IGNORECASE,
    ),
)

_LOCATION_RE = re.compile(
    r"(?:địa\s*điểm\s*:\s*|\btại\s+)"
    r"(?P<location>(?:Phòng|Khu|Ban|Trường|Văn\s+phòng|Hội\s+trường)"
    r"[^.;\r\n]{0,100})",
    re.IGNORECASE,
)

_DOCUMENT_TRIGGER_RE = re.compile(
    r"hồ\s+sơ\s+gồm|cần\s+nộp|bao\s+gồm", re.IGNORECASE
)
_DOCUMENT_RE = re.compile(
    r"đơn\s+đăng\s+k[ýí]|bản\s+sao\s+CCCD|bản\s+sao\s+CMND|"
    r"CCCD|CMND|bảng\s+điểm|chứng\s+chỉ",
    re.IGNORECASE,
)
_EXCEPTION_RE = re.compile(
    r"\b(?:trừ|ngoại\s+trừ|không\s+áp\s+dụng\s+cho)\s+[^.;\r\n]+",
    re.IGNORECASE,
)


def _trimmed_span(text: str, start: int, end: int) -> tuple[int, int] | None:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return (start, end) if start < end else None


def _block_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for boundary in _BLANK_LINE_RE.finditer(text):
        span = _trimmed_span(text, start, boundary.start())
        if span:
            spans.append(span)
        start = boundary.end()
    span = _trimmed_span(text, start, len(text))
    if span:
        spans.append(span)
    return spans


def _claim_spans(text: str) -> list[tuple[int, int]]:
    claims: list[tuple[int, int]] = []
    for block_start, block_end in _block_spans(text):
        block = text[block_start:block_end]
        # Consecutive lines commonly carry fields belonging to one forwarded
        # obligation. Blank lines remain the stronger deterministic boundary.
        if "\n" in block or "\r" in block:
            claims.append((block_start, block_end))
            continue
        local_start = 0
        for boundary in _SENTENCE_END_RE.finditer(block):
            span = _trimmed_span(text, block_start + local_start, block_start + boundary.start())
            if span:
                claims.append(span)
            local_start = boundary.end()
        span = _trimmed_span(text, block_start + local_start, block_end)
        if span:
            claims.append(span)
    return claims


def _field(
    source: str,
    start: int,
    end: int,
    normalized_value: str | int | None = None,
) -> TypedUserField:
    raw = source[start:end]
    return TypedUserField(
        text=raw,
        raw_text=raw,
        start_char=start,
        end_char=end,
        normalized_value=normalized_value,
    )


def _extract_action(source: str, start: int, end: int) -> TypedUserField | None:
    value = source[start:end]
    patterns = (
        # "đóng" is payment-specific only with an explicit payment object;
        # bare occurrences such as "đóng góp" are not student payment actions.
        (
            ActionType.PAY,
            re.compile(
                r"\b(?P<verb>đóng)\s+(?:học\s*phí|lệ\s*phí|phí|tiền|"
                r"BHYT|bảo\s+hiểm|khoản\s+phí)\b",
                re.IGNORECASE,
            ),
        ),
        (ActionType.PAY, re.compile(r"\b(?P<verb>thanh\s+toán)\b", re.IGNORECASE)),
        (
            ActionType.PAY,
            re.compile(r"\b(?P<verb>nộp)\s+(?:học\s*phí|lệ\s*phí|phí|tiền)\b", re.IGNORECASE),
        ),
        (ActionType.REGISTER, re.compile(r"\b(?P<verb>đăng\s+k[ýí])\b", re.IGNORECASE)),
        (ActionType.APPLY, re.compile(r"\b(?P<verb>ứng\s+tuyển)\b", re.IGNORECASE)),
        (ActionType.SUBMIT, re.compile(r"\b(?P<verb>nộp)\b", re.IGNORECASE)),
        (ActionType.ATTEND, re.compile(r"\b(?P<verb>tham\s+gia)\b", re.IGNORECASE)),
        (
            ActionType.COLLECT,
            re.compile(
                r"\b(?P<verb>nhận)\s+(?:kết\s+quả|thẻ(?:\s+sinh\s+viên)?|"
                r"giấy(?:\s+xác\s+nhận)?|chứng\s+nhận|học\s+bổng|biên\s+lai)\b",
                re.IGNORECASE,
            ),
        ),
        (ActionType.UPDATE, re.compile(r"\b(?P<verb>cập\s+nhật|tự\s+đánh\s+giá)\b", re.IGNORECASE)),
        (ActionType.CHECK, re.compile(r"\b(?P<verb>kiểm\s+tra|xem)\b", re.IGNORECASE)),
        (ActionType.OTHER, re.compile(r"\b(?P<verb>hoàn\s+thành|thực\s+hiện)\b", re.IGNORECASE)),
    )
    matches = []
    for action_type, pattern in patterns:
        match = pattern.search(value)
        if match:
            matches.append((match.start("verb"), match.end("verb"), action_type))
    if not matches:
        return None
    local_start, local_end, action_type = min(matches, key=lambda item: item[0])
    return _field(source, start + local_start, start + local_end, action_type.value)


def _extract_deadline(source: str, start: int, end: int) -> TypedUserField | None:
    value = source[start:end]
    match = _FULL_DATE_RE.search(value)
    if match:
        raw = match.group("date")
        normalized, _ = parse_deadline(raw)
        return _field(source, start + match.start("date"), start + match.end("date"), normalized)
    match = _MISSING_YEAR_DATE_RE.search(value)
    if match:
        # Preserve the grounded phrase but never invent the absent year.
        return _field(source, start + match.start("date"), start + match.end("date"), None)
    return None


def _extract_amount(source: str, start: int, end: int) -> TypedUserField | None:
    value = source[start:end]
    match = _MONEY_RE.search(value)
    if not match:
        return None
    group = "vnd" if match.group("vnd") is not None else "thousand"
    raw = match.group(0)
    return _field(
        source,
        start + match.start(group),
        start + match.end(group),
        parse_vnd(raw),
    )


def _extract_audience(source: str, start: int, end: int) -> TypedUserField | None:
    value = source[start:end]
    matches = []
    for pattern in _AUDIENCE_PATTERNS:
        match = pattern.search(value)
        if match:
            matches.append(match)
    if not matches:
        return None
    match = min(matches, key=lambda item: item.start())
    year = match.group("year")
    cohort = f"K{year[-2:]}"
    return _field(source, start + match.start(), start + match.end(), cohort)


def _extract_location(source: str, start: int, end: int) -> TypedUserField | None:
    match = _LOCATION_RE.search(source[start:end])
    if not match:
        return None
    return _field(
        source,
        start + match.start("location"),
        start + match.end("location"),
        " ".join(match.group("location").split()),
    )


def _extract_documents(source: str, start: int, end: int) -> list[TypedUserField]:
    value = source[start:end]
    if not _DOCUMENT_TRIGGER_RE.search(value):
        return []
    fields = []
    seen = set()
    for match in _DOCUMENT_RE.finditer(value):
        key = match.group(0).casefold()
        if key in seen:
            continue
        seen.add(key)
        fields.append(_field(source, start + match.start(), start + match.end()))
    return fields


def _extract_exceptions(source: str, start: int, end: int) -> list[TypedUserField]:
    return [
        _field(source, start + match.start(), start + match.end())
        for match in _EXCEPTION_RE.finditer(source[start:end])
    ]


class DeterministicTextClaimExtractor:
    def extract(self, text: str) -> list[DecomposedUserClaim]:
        if not text or not text.strip():
            return []

        claims = []
        for start, end in _claim_spans(text):
            raw_claim = text[start:end]
            claims.append(
                DecomposedUserClaim(
                    claim_id=str(uuid.uuid4()),
                    raw_claim_text=raw_claim,
                    start_char=start,
                    end_char=end,
                    normalized_text=" ".join(unicodedata.normalize("NFC", raw_claim).split()),
                    action=_extract_action(text, start, end),
                    deadline=_extract_deadline(text, start, end),
                    amount=_extract_amount(text, start, end),
                    audience=_extract_audience(text, start, end),
                    location=_extract_location(text, start, end),
                    required_documents=_extract_documents(text, start, end),
                    exceptions=_extract_exceptions(text, start, end),
                )
            )
        return claims
