"""Apply the approved, source-grounded AI Generalization V1 adjudication.

This is an evaluation-data maintenance tool.  It never reads or writes the
production database, calls a provider, or changes the product runtime.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACK = Path(__file__).resolve().parent

REJECTED = {
    "AGV1-004", "AGV1-006", "AGV1-007", "AGV1-008", "AGV1-009", "AGV1-010",
    "AGV1-017", "AGV1-018", "AGV1-026", "AGV1-031", "AGV1-035", "AGV1-043",
    "AGV1-044", "AGV1-045",
}
EDITED = {
    "AGV1-011", "AGV1-012", "AGV1-023", "AGV1-024", "AGV1-025", "AGV1-027",
    "AGV1-028", "AGV1-034", "AGV1-038", "AGV1-039", "AGV1-040", "AGV1-041",
    "AGV1-042", "AGV1-046", "AGV1-047", "AGV1-048", "AGV1-049",
}


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def exact(text: str, value: str, *, after: int = 0) -> dict[str, Any]:
    """Return an offset-verified exact source span, never an inferred span."""
    start = text.find(value, after)
    if start < 0:
        raise ValueError(f"Approved source span not found: {value!r}")
    end = start + len(value)
    assert text[start:end] == value
    return {"text": value, "start_char": start, "end_char": end}


def _field(text: str, value: str, normalized: Any = None, *, after: int = 0) -> dict[str, Any]:
    span = exact(text, value, after=after)
    span["normalized_value"] = normalized
    return span


def claim(text: str, *, action: tuple[str, str], audience: str | None = None,
          deadline: tuple[str, str] | None = None, location: str | None = None,
          documents: list[str] | None = None, object_hint: str | None = None,
          non_comparable_fields: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    action_span = _field(text, action[0], action[1])
    audience_span = _field(text, audience) if audience else None
    deadline_span = _field(text, deadline[0], deadline[1]) if deadline else None
    location_span = _field(text, location) if location else None
    document_spans = [_field(text, item) for item in (documents or [])]
    object_span = _field(text, object_hint) if object_hint else None
    evidence = {
        "action": [action_span], "audience": [audience_span] if audience_span else [],
        "deadline": [deadline_span] if deadline_span else [], "location": [location_span] if location_span else [],
        "required_documents": document_spans, "amount": [], "exceptions": [],
    }
    return {
        "claim_span": {k: action_span[k] for k in ("text", "start_char", "end_char")},
        "claim_span_status": "HUMAN_ADJUDICATED_EXACT_SOURCE_SPAN",
        "audience": None if audience_span is None else {"raw_text": audience, "cohorts": [], "faculties": [], "majors": [], "programs": [], "applies_to_all_students": False},
        "action": {"text": action[0], "action_type": action[1]},
        "object_hint": None if object_span is None else {"text": object_hint},
        "deadline": None if deadline_span is None else {"raw_text": deadline[0], "normalized": deadline[1], "precision": "date", "timezone": "Asia/Ho_Chi_Minh"},
        "amount": None, "location": None if location_span is None else {"text": location},
        "required_documents": [{"text": item["text"]} for item in document_spans],
        "exceptions": [], "evidence_spans": evidence,
        "non_comparable_fields": non_comparable_fields or [],
    }


def _claims(record: dict[str, Any]) -> list[dict[str, Any]]:
    t, rid = record["source_text"], record["record_id"]
    # Each value is deliberately a source substring.  `claim()` fails closed
    # if the adjudicated wording is not present in this immutable source text.
    if rid == "AGV1-011": return [claim(t, audience="Hà Thị Minh Phương", action=("bảo vệ luận án tiến sĩ", "other"), location="Trường Đại học Bách khoa, Đại học Đà Nẵng - Số 54 Nguyễn Lương Bằng, Phường Liên Chiểu, TP. Đà Nẵng.")]
    if rid == "AGV1-012": return [claim(t, audience="279 sinh viên Khoa Công nghệ Thông tin", action=("bảo vệ Đồ án Tốt nghiệp", "other"), location="Các phòng A133 -A146")]
    if rid == "AGV1-023": return [claim(t, audience="Sinh viên năm cuối/mới tốt nghiệp ngành CNTT, Khoa học máy tính, Kỹ thuật phần mềm,...", action=("ứng tuyển", "register"))]
    if rid == "AGV1-024": return [claim(t, audience="Học sinh THPT yêu thích công nghệ, đam mê lập trình và muốn tìm hiểu về ngành CNTT tại Bách khoa Đà Nẵng", action=("đăng ký", "register"), deadline=("10/5/2026", "2026-05-10"))]
    if rid == "AGV1-025": return [claim(t, audience="sinh viên", action=("đăng ký ứng tuyển", "register"))]
    if rid == "AGV1-027": return [claim(t, audience="sinh viên các khóa 2019, khóa 2020, khóa 2021 và khóa 2022 đã tốt nghiệp", action=("liên hệ nhận hồ sơ", "collect"), deadline=("29/8/2026", "2026-08-29"), location="Trung tâm Công nghệ thông tin và Học liệu số – Trường Đại học Bách khoa.\n(Số 54 Nguyễn Lương Bằng, P. Liên Chiểu, TP. Đà Nẵng)")]
    if rid == "AGV1-028": return [claim(t, action=("Học online", "other")), claim(t, action=("Học tập trung", "other"), location="Hội trường F")]
    if rid == "AGV1-034":
        audience = "mỗi sinh viên Trường Đại học Bách khoa"
        actions = [
            "Chấp hành nghiêm Luật Trật tự, an toàn giao thông đường bộ và các quy định của pháp luật khi tham gia giao thông.",
            "Đội mũ bảo hiểm đạt chuẩn và cài quai đúng quy cách khi điều khiển hoặc ngồi trên xe mô tô, xe gắn máy, xe máy điện.",
            "Không điều khiển phương tiện khi đã sử dụng rượu, bia hoặc các chất kích thích; tuyệt đối không phóng nhanh, vượt ẩu, lạng lách, đánh võng.",
            "Tuân thủ tín hiệu đèn giao thông, biển báo, vạch kẻ đường; đi đúng làn đường, phần đường quy định.",
            "Không sử dụng điện thoại di động hoặc các thiết bị gây mất tập trung khi đang điều khiển phương tiện.",
            "Chủ động nhắc nhở bạn bè, người thân cùng thực hiện văn hóa giao thông; tích cực tham gia các hoạt động tuyên truyền về an toàn giao thông do Nhà trường và các tổ chức phát động.",
        ]
        return [claim(t, audience=audience, action=(item, "other")) for item in actions]
    if rid == "AGV1-038": return [claim(t, action=("nộp lưu chiểu Đồ án tốt nghiệp", "submit"))]
    if rid == "AGV1-039": return [claim(t, audience="Các em trong mục ghi chú có ghi \"\n(Yêu cầu đến phòng S05.06 cung cấp thông tin (Phòng ĐTBĐCL\n)\"", action=("cung cấp thông tin phục vụ cho công tác hậu kiểm", "update"), deadline=("22/09/2026", "2026-09-22"), location="S05.06")]
    if rid == "AGV1-040": return [claim(t, audience="Ngô Tấn Thống", action=("bảo vệ luận án tiến sĩ", "other"), location="Trường Đại học Bách khoa, Đại học Đà Nẵng - Số 54 Nguyễn Lương Bằng, Phường Liên Chiểu, TP. Đà Nẵng.")]
    if rid == "AGV1-041": return [
        claim(t, audience="sinh viên khóa 2022 (hệ kỹ sư), 2023, 2024 và 2025 có đăng ký học phần trong học kỳ II năm học 2025-2026", action=("tự ĐGRL", "other"), deadline=("22/9/2026", "2026-09-22")),
        claim(t, audience="Lớp trưởng và Chủ nhiệm lớp", action=("hoàn thành việc xác nhận điểm cho lớp", "other"), deadline=("30/9/2026", "2026-09-30")),
        claim(t, audience="Tất cả các lớp các khóa 2022 (hệ kỹ sư), 2023, 2024 và 2025", action=("nộp hồ sơ ĐGRL HK2/2025-2026 về Khoa", "submit"), deadline=("05/10/2026", "2026-10-05")),
    ]
    if rid == "AGV1-042": return [claim(t, audience="Sinh viên có nhu cầu cấp Giấy xác nhận để thực hiện thủ tục vay vốn tại Ngân hàng Chính sách Xã hội theo Quyết định số 29/2025/QĐ-TTg", action=("đăng ký trực tuyến", "register"), object_hint="Giấy xác nhận")]
    if rid == "AGV1-046": return [claim(t, audience="Mai Thị Thùy Dương", action=("bảo vệ luận án tiến sĩ", "other"), location="Trường Đại học Bách khoa, Đại học Đà Nẵng - Số 54 Nguyễn Lương Bằng, Phường Liên Chiểu, TP. Đà Nẵng.")]
    if rid == "AGV1-047": return [claim(t, audience="Ứng viên tốt nghiệp đại học một trong các chuyên ngành: Kỹ thuật Nhiệt, Nhiệt lạnh, Điện lạnh, Hệ thống kỹ thuật công trình, Cơ khí chế tạo máy, Chế tạo thiết bị, Kỹ thuật Cơ khí.", action=("nộp hồ sơ trực tiếp", "submit"), deadline=("01/10/2026", "2026-10-01"), documents=["Bảng thông tin ứng viên", "đơn xin việc", "sơ yếu lý lịch có chứng nhận", "giấy khám sức khỏe", "bản sao Căn cước", "bằng tốt nghiệp đại học", "bảng điểm", "chứng chỉ ngoại ngữ", "tin học", "02 ảnh thẻ 3×4"])]
    if rid == "AGV1-048":
        audience = "Tân sinh viên Khóa 2026 có thành tích đầu vào xuất sắc;\n03 suất\ndành cho sinh viên năm 3, năm 4"
        value = exact(t, "40.000 Yên/suất")
        return [claim(t, audience=audience, action=("đăng ký và kê khai hồ sơ trực tuyến", "register"), deadline=("15/9/2026", "2026-09-15"), non_comparable_fields=[{"field": "amount", "raw_span": value, "reason": "CURRENCY_UNIT_NOT_SUPPORTED_BY_VND_SCHEMA"}])]
    if rid == "AGV1-049": return [claim(t, audience="Sinh viên\nngành Kỹ thuật Nhiệt\nnăm ba hoặc năm cuối\n, đang theo học\nchính quy\ntại trường.", action=("chuẩn bị đầy đủ hồ sơ và gửi về Công ty", "submit"), deadline=("19/09/2026", "2026-09-19"), documents=["Đơn xin cấp học bổng\ncó dán ảnh, theo mẫu.", "Thư giới thiệu của Khoa/Trường Đại học", "Bảng điểm", "Bản sao các văn bằng, giấy khen, giấy chứng nhận giải thưởng", "01 bản sao CMND/CCCD/Hộ chiếu", "giấy tờ chứng minh thu nhập trung bình của các thành viên trong độ tuổi lao động dưới 1.300.000 đồng/tháng"])]
    raise KeyError(rid)


def apply(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for record in records:
        rid = record["record_id"]
        if rid in REJECTED:
            record.update(review_status="REJECTED", review_action="HUMAN_REJECTED", gold_provenance="NONE", gold_claim=None, gold_claims=[], human_review_decision={"decision": "REJECT", "reviewer": "human_adjudication_v1", "reason": "NO_ACTIONABLE_OBLIGATION"})
        elif rid in EDITED:
            claims = _claims(record)
            record.update(review_status="HUMAN_ACCEPTED", review_action="HUMAN_EDITED_ACCEPTED", gold_provenance="HUMAN_ADJUDICATION_V1", gold_claim=claims[0], gold_claims=claims, obligation_id="human-adjudicated", human_review_decision={"decision": "EDIT", "reviewer": "human_adjudication_v1"})
    return records


def main() -> int:
    records = apply(_rows(PACK / "dataset.jsonl"))
    assert len(records) == 49
    assert sum(item["review_status"] == "HUMAN_ACCEPTED" for item in records) == 35
    assert {item["record_id"] for item in records if item["review_status"] == "REJECTED"} == REJECTED
    _write(PACK / "dataset.jsonl", records)
    _write(PACK / "accepted_gold.jsonl", [r for r in records if r["review_status"] == "HUMAN_ACCEPTED"])
    _write(PACK / "review_worksheet.jsonl", [r for r in records if r["record_id"] in EDITED | REJECTED])
    manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
    manifest.update(human_accepted_count=35, human_review_required_count=0, human_rejected_count=14,
                    human_accepted_obligation_count=sum(len(r.get("gold_claims", [r.get("gold_claim")])) for r in records if r["review_status"] == "HUMAN_ACCEPTED"))
    (PACK / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
