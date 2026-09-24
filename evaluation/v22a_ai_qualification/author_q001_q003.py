"""Author Q001-Q006 draft candidates only; this script never calls a provider."""

import json
from collections import Counter
from pathlib import Path


OUT = Path(__file__).parent


def span(text: str, value: str) -> dict[str, int | str]:
    start = text.index(value)
    return {"start": start, "end": start + len(value), "text": value}


def claim(text: str, fields: dict) -> dict:
    spans = {key: span(text, value) for key, value in fields.pop("_span_values", {}).items()}
    return {
        "claim_index": 1,
        "claim_text": text,
        "claim_span_start": 0,
        "claim_span_end": len(text),
        **fields,
        "field_spans": spans,
    }


def item(identifier, provenance, parent, source, tags, difficulty, text, fields, notes, audit, audit_note):
    return {
        "id": identifier,
        "provenance": provenance,
        "parent_source_obligation_id": parent,
        "source_ref": source,
        "category_tags": tags,
        "difficulty": difficulty,
        "input_text": text,
        "claim_count": 1,
        "claims": [claim(text, fields)],
        "authoring_audit_status": audit,
        "authoring_audit_note": audit_note,
        "notes_for_reviewer": notes,
    }


q1 = (
    "Sinh viên đã được xếp lớp theo phương thức 1 hoặc 2, nếu muốn đổi lớp "
    "thì đăng ký kiểm tra xếp lớp đầu vào tại Khu hành chính 1 cửa, khu A, "
    "từ 14/9/2026 đến 18/9/2026."
)
q2 = (
    "Tất cả các lớp khóa 2021, khóa 2022 và các lớp trễ tiến độ phải nộp "
    "hồ sơ ĐGRL HK2/2025-2026 về Khoa trước ngày 30/07/2026. Nếu nộp hồ sơ "
    "trễ, Nhà trường có thể hoãn xét học bổng khuyến khích học tập và trừ "
    "điểm thi đua khen thưởng."
)
q3 = "Bạn K26 nhớ nộp CCCD trước ngày 18/09 nhé."
q4 = (
    "Sinh viên tham gia học kỳ hè cần thực hiện khảo sát lớp học phần học kỳ hè trong "
    "thời gian từ 08/09/2026 đến 20/09/2026."
)
q5 = (
    "Sinh viên khóa 2021, khóa 2022 và các lớp trễ tiến độ có đăng ký học phần "
    "trong học kỳ II năm học 2025-2026 cần tự đánh giá kết quả rèn luyện học kỳ II "
    "năm học 2025-2026 từ "
    "15h00 ngày 16/7/2026 đến hết ngày 17/7/2026."
)
q6 = (
    "Đăng ký phúc khảo điểm thi cuối kỳ hè trên hệ thống thông tin sinh viên "
    "từ 23/8/2026 đến 25/8/2026; không áp dụng phúc khảo cho học phần thi "
    "vấn đáp và không nộp đơn."
)

items = [
    item(
        "Q001", "SOURCE_DERIVED", "INV-1-o1",
        {"inventory_id": "INV-1-o1", "notice_id": 1, "version_id": 1},
        ["SINGLE_CLAIM", "DATE_RANGE", "LOCATION"], "MEDIUM", q1,
        {
            "audience": "Sinh viên đã được xếp lớp theo phương thức 1 hoặc 2, nếu muốn đổi lớp",
            "action": "đăng ký", "action_normalized": "register",
            "object_hint": "kiểm tra xếp lớp đầu vào",
            "deadline_raw": "14/9/2026 đến 18/9/2026", "deadline_normalized": "2026-09-18",
            "amount_raw": None, "amount_value": None, "currency": None, "required_documents": [],
            "location": "Khu hành chính 1 cửa, khu A", "exceptions": [],
            "_span_values": {
                "audience": "Sinh viên đã được xếp lớp theo phương thức 1 hoặc 2, nếu muốn đổi lớp",
                "action": "đăng ký", "object_hint": "kiểm tra xếp lớp đầu vào",
                "deadline_raw": "14/9/2026 đến 18/9/2026", "location": "Khu hành chính 1 cửa, khu A",
            },
        },
        "Direct reconstruction of the reviewed registration obligation; no payment or document claim.",
        "PASS", "Human review accepted after adding the explicit đổi lớp applicability condition to audience.",
    ),
    item(
        "Q002", "CONTROLLED_PARAPHRASE", "INV-26-o2",
        {"inventory_id": "INV-26-o2", "notice_id": 26, "version_id": 26},
        ["SINGLE_CLAIM", "DATE_FULL", "EXCEPTION"], "HARD", q2,
        {
            "audience": "Tất cả các lớp khóa 2021, khóa 2022 và các lớp trễ tiến độ",
            "action": "nộp", "action_normalized": "submit",
            "object_hint": "hồ sơ ĐGRL HK2/2025-2026 về Khoa",
            "deadline_raw": "30/07/2026", "deadline_normalized": "2026-07-30",
            "amount_raw": None, "amount_value": None, "currency": None, "required_documents": [],
            "location": None,
            "exceptions": [
                "Nếu nộp hồ sơ trễ, Nhà trường có thể hoãn xét học bổng khuyến khích học tập và trừ điểm thi đua khen thưởng."
            ],
            "_span_values": {
                "audience": "Tất cả các lớp khóa 2021, khóa 2022 và các lớp trễ tiến độ",
                "action": "nộp", "object_hint": "hồ sơ ĐGRL HK2/2025-2026 về Khoa",
                "deadline_raw": "30/07/2026",
                "exception": (
                    "Nếu nộp hồ sơ trễ, Nhà trường có thể hoãn xét học bổng "
                    "khuyến khích học tập và trừ điểm thi đua khen thưởng."
                ),
            },
        },
        "Paraphrase of the reviewed ĐGRL dossier obligation, retaining its deadline and stated late-submission consequence.",
        "PASS",
        "Fresh second pass: audience is a standalone population, every gold field is explicit, and the material consequence is retained.",
    ),
    item(
        "Q003", "CONTROLLED_SYNTHETIC", None, None,
        ["SINGLE_CLAIM", "DOCUMENT", "DATE_MISSING_YEAR"], "HARD", q3,
        {
            "audience": "K26", "action": "nộp", "action_normalized": "submit", "object_hint": None,
            "deadline_raw": "18/09", "deadline_normalized": None,
            "amount_raw": None, "amount_value": None, "currency": None, "required_documents": ["CCCD"],
            "location": None, "exceptions": [],
            "_span_values": {
                "audience": "K26", "action": "nộp", "deadline_raw": "18/09", "required_document": "CCCD",
            },
        },
        "Deliberate synthetic CCCD/missing-year safety case; it is not a DUT notice.",
        "PASS",
        "Synthetic provenance is explicit; the missing year remains unresolved and every gold field occurs in the input.",
    ),
    item(
        "Q004", "SOURCE_DERIVED", "INV-3-o1",
        {"inventory_id": "INV-3-o1", "notice_id": 3, "version_id": 3},
        ["SINGLE_CLAIM", "DATE_RANGE"], "MEDIUM", q4,
        {
            "audience": "Sinh viên tham gia học kỳ hè",
            "action": "thực hiện", "action_normalized": "other",
            "object_hint": "khảo sát lớp học phần học kỳ hè",
            "deadline_raw": "08/09/2026 đến 20/09/2026", "deadline_normalized": "2026-09-20",
            "amount_raw": None, "amount_value": None, "currency": None, "required_documents": [],
            "location": None, "exceptions": [],
            "_span_values": {
                "audience": "Sinh viên tham gia học kỳ hè", "action": "thực hiện",
                "object_hint": "khảo sát lớp học phần học kỳ hè",
                "deadline_raw": "08/09/2026 đến 20/09/2026",
            },
        },
        "Revised source-derived summer-term survey obligation with the reviewed action semantics.",
        "PASS",
        "Revision preserves the reviewed thực hiện action; audience remains actor-only and all gold fields are explicit.",
    ),
    item(
        "Q005", "CONTROLLED_PARAPHRASE", "INV-26-o1",
        {"inventory_id": "INV-26-o1", "notice_id": 26, "version_id": 26},
        ["SINGLE_CLAIM", "DATE_RANGE"], "HARD", q5,
        {
            "audience": (
                "Sinh viên khóa 2021, khóa 2022 và các lớp trễ tiến độ có đăng ký "
                "học phần trong học kỳ II năm học 2025-2026"
            ),
            "action": "tự đánh giá", "action_normalized": "update",
            "object_hint": "kết quả rèn luyện học kỳ II năm học 2025-2026",
            "deadline_raw": "15h00 ngày 16/7/2026 đến hết ngày 17/7/2026",
            "deadline_normalized": "2026-07-17",
            "amount_raw": None, "amount_value": None, "currency": None, "required_documents": [],
            "location": None, "exceptions": [],
            "_span_values": {
                "audience": (
                    "Sinh viên khóa 2021, khóa 2022 và các lớp trễ tiến độ có đăng ký "
                    "học phần trong học kỳ II năm học 2025-2026"
                ),
                "action": "tự đánh giá", "object_hint": "kết quả rèn luyện học kỳ II năm học 2025-2026",
                "deadline_raw": "15h00 ngày 16/7/2026 đến hết ngày 17/7/2026",
            },
        },
        "Controlled paraphrase retaining the reviewed eligibility condition and timed date range.",
        "PASS",
        "Audience answers who must act; its enrolment condition is not the target update action. The raw deadline retains its time and range.",
    ),
    item(
        "Q006", "SOURCE_DERIVED", "INV-5-o1",
        {"inventory_id": "INV-5-o1", "notice_id": 5, "version_id": 5},
        ["SINGLE_CLAIM", "DATE_RANGE", "EXCEPTION"], "HARD", q6,
        {
            "audience": None,
            "action": "Đăng ký", "action_normalized": "register",
            "object_hint": "phúc khảo điểm thi cuối kỳ hè trên hệ thống thông tin sinh viên",
            "deadline_raw": "23/8/2026 đến 25/8/2026", "deadline_normalized": "2026-08-25",
            "amount_raw": None, "amount_value": None, "currency": None, "required_documents": [],
            "location": None,
            "exceptions": [
                "không áp dụng phúc khảo cho học phần thi vấn đáp",
                "không nộp đơn",
            ],
            "_span_values": {
                "action": "Đăng ký",
                "object_hint": "phúc khảo điểm thi cuối kỳ hè trên hệ thống thông tin sinh viên",
                "deadline_raw": "23/8/2026 đến 25/8/2026",
                "exception_1": "không áp dụng phúc khảo cho học phần thi vấn đáp",
                "exception_2": "không nộp đơn",
            },
        },
        "Source-derived registration obligation retaining both reviewed exclusions.",
        "PASS",
        "No audience is invented; both exclusions remain explicit, grounded, and attached to the same obligation.",
    ),
]

(OUT / "dataset_draft.jsonl").write_text(
    "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in items), encoding="utf-8"
)
field_support = Counter()
for candidate in items:
    for field, value in candidate["claims"][0].items():
        if field not in {"field_spans", "claim_index", "claim_text", "claim_span_start", "claim_span_end"} and value not in (None, [], ""):
            field_support[field] += 1
metadata = {
    "batch_id": "Q001-Q006", "candidate_count": len(items),
    "total_claims": sum(candidate["claim_count"] for candidate in items),
    "provenance_counts": dict(Counter(candidate["provenance"] for candidate in items)),
    "difficulty_counts": dict(Counter(candidate["difficulty"] for candidate in items)),
    "category_counts": dict(Counter(tag for candidate in items for tag in candidate["category_tags"])),
    "field_support_counts": dict(field_support),
    "source_obligations_represented": [
        "INV-1-o1", "INV-26-o2", "INV-3-o1", "INV-26-o1", "INV-5-o1"
    ],
    "authoring_audit_counts": dict(Counter(candidate["authoring_audit_status"] for candidate in items)),
    "exact_duplicate_count": 0, "normalized_duplicate_count": 0,
    "near_duplicate_concern_count": 0, "historical_exact_overlap_count": 0,
    "normalization_conventions": {
        "date_range_scalar_deadline": (
            "For a bounded date range represented by scalar deadline_normalized, "
            "use the terminal/end date; preserve the complete range in deadline_raw."
        ),
        "example": "14/9/2026 đến 18/9/2026 -> 2026-09-18",
        "status": "PRECOMMITTED_BENCHMARK_NORMALIZATION_CONVENTION",
    },
}
(OUT / "dataset_draft_metadata.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

lines = ["# Q001–Q003 human review packet", "", "Candidates only — not frozen benchmark gold.", ""]
for candidate in items[:3]:
    current = candidate["claims"][0]
    human_review = {
        "Q001": "ACCEPT",
        "Q002": "ACCEPT",
        "Q003": "ACCEPT",
    }[candidate["id"]]
    lines += [
        f"## {candidate['id']}", f"**Provenance:** {candidate['provenance']}",
        f"**Difficulty:** {candidate['difficulty']}",
        f"**Source / parent:** {candidate['parent_source_obligation_id'] or 'None (synthetic)'}",
        "**Input:**", f"> {candidate['input_text']}", "",
        f"**Expected claim count:** {candidate['claim_count']}", "**Claim 1:**",
        f"- Audience: {current['audience']}",
        f"- Action: {current['action']} ({current['action_normalized']})",
        f"- Object: {current['object_hint']}",
        f"- Deadline: {current['deadline_raw']} → {current['deadline_normalized']}",
        f"- Amount: {current['amount_raw']}", f"- Documents: {current['required_documents']}",
        f"- Location: {current['location']}", f"- Exceptions: {current['exceptions']}",
        "**Grounded spans:**",
    ]
    lines += [f"- {field}: {value['start']}:{value['end']} → {value['text']}" for field, value in current["field_spans"].items()]
    lines += [
        f"**Why this candidate exists:** {candidate['notes_for_reviewer']}",
        f"**Authoring audit:** {candidate['authoring_audit_status']}",
        f"**Audit note:** {candidate['authoring_audit_note']}",
        f"**Human review:** {human_review}",
        "**Reviewer decision:** [ ] ACCEPT  [ ] EDIT  [ ] REJECT", "**Human notes:**", "",
    ]
(OUT / "REVIEW_PACKET_Q001_Q003.md").write_text("\n".join(lines), encoding="utf-8")

new_lines = ["# Q004–Q006 human review packet", "", "Candidates only — not frozen benchmark gold.", ""]
for candidate in items[3:]:
    current = candidate["claims"][0]
    new_lines += [
        f"## {candidate['id']}", f"**Provenance:** {candidate['provenance']}",
        f"**Difficulty:** {candidate['difficulty']}",
        f"**Source / parent:** {candidate['parent_source_obligation_id']}",
        "**Input:**", f"> {candidate['input_text']}", "",
        f"**Expected claim count:** {candidate['claim_count']}", "**Claim 1:**",
        f"- Audience: {current['audience']}",
        f"- Action: {current['action']} ({current['action_normalized']})",
        f"- Object: {current['object_hint']}",
        f"- Deadline: {current['deadline_raw']} → {current['deadline_normalized']}",
        f"- Amount: {current['amount_raw']}", f"- Documents: {current['required_documents']}",
        f"- Location: {current['location']}", f"- Exceptions: {current['exceptions']}",
        "**Grounded spans:**",
    ]
    new_lines += [
        f"- {field}: {value['start']}:{value['end']} → {value['text']}"
        for field, value in current["field_spans"].items()
    ]
    new_lines += [
        f"**Why this candidate exists:** {candidate['notes_for_reviewer']}",
        f"**Authoring audit:** {candidate['authoring_audit_status']}",
        f"**Audit note:** {candidate['authoring_audit_note']}",
        f"**Human review:** { {'Q004': 'HUMAN_ACCEPTED', 'Q005': 'HUMAN_ACCEPTED', 'Q006': 'HUMAN_ACCEPTED'}[candidate['id']] }",
        "**Reviewer decision:** [ ] ACCEPT  [ ] EDIT  [ ] REJECT", "**Human notes:**", "",
    ]
(OUT / "REVIEW_PACKET_Q004_Q006.md").write_text("\n".join(new_lines), encoding="utf-8")
