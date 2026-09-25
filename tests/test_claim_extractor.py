import pytest

from app.verification.claim_extractor import DeterministicTextClaimExtractor


def extract_one(text: str):
    claims = DeterministicTextClaimExtractor().extract(text)
    assert len(claims) == 1
    return claims[0]


def populated_fields(claim):
    values = [claim.action, claim.deadline, claim.amount, claim.audience, claim.location]
    values.extend(claim.required_documents)
    values.extend(claim.exceptions)
    return [value for value in values if value is not None]


def assert_grounded(source: str, claim) -> None:
    assert source[claim.start_char:claim.end_char] == claim.raw_claim_text
    for field in populated_fields(claim):
        assert 0 <= field.start_char < field.end_char <= len(source)
        assert source[field.start_char:field.end_char] == field.text == field.raw_text
        assert field.extraction_method == "deterministic"


def test_full_date_audience_action_are_normalized_and_grounded():
    text = "Sinh viên K26 nộp hồ sơ trước ngày 30/09/2026."
    claim = extract_one(text)
    assert claim.action.text == "nộp"
    assert claim.action.normalized_value == "submit"
    assert claim.audience.normalized_value == "K26"
    assert claim.deadline.normalized_value == "2026-09-30"
    assert_grounded(text, claim)


@pytest.mark.parametrize("separator", ["/", "-", "."])
def test_full_numeric_date_separators(separator):
    text = f"Nộp hồ sơ trước ngày 30{separator}09{separator}2026."
    claim = extract_one(text)
    assert claim.deadline.normalized_value == "2026-09-30"
    assert_grounded(text, claim)


def test_den_het_ngay_selects_deadline():
    text = "Thời gian đăng ký đến hết ngày 30/09/2026."
    claim = extract_one(text)
    assert claim.action.normalized_value == "register"
    assert claim.deadline.normalized_value == "2026-09-30"
    assert_grounded(text, claim)


def test_missing_year_is_grounded_but_not_invented():
    text = "Nộp hồ sơ trước ngày 30/9."
    claim = extract_one(text)
    assert claim.deadline.text == "30/9"
    assert claim.deadline.normalized_value is None
    assert_grounded(text, claim)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("450.000 đồng", 450000),
        ("450,000 đồng", 450000),
        ("450000 đồng", 450000),
        ("450.000 VNĐ", 450000),
        ("450.000 VND", 450000),
        ("450k", 450000),
        ("650k", 650000),
    ],
)
def test_vnd_amounts_are_safe_and_grounded(raw, expected):
    text = f"Lệ phí là {raw}."
    claim = extract_one(text)
    expected_raw = raw if raw.casefold().endswith("k") else raw.split()[0]
    assert claim.amount.text == expected_raw
    assert claim.amount.normalized_value == expected
    assert claim.amount.normalized_value != 450 if raw == "450k" else True
    assert_grounded(text, claim)


def test_admission_cohort_is_deterministic_without_faculty_or_program():
    text = "Sinh viên khóa tuyển sinh 2026 cần hoàn thành khảo sát."
    claim = extract_one(text)
    assert claim.audience.normalized_value == "K26"
    assert claim.action.normalized_value == "other"
    assert "khoa" not in claim.audience.text.casefold()
    assert_grounded(text, claim)


def test_related_multiline_fields_remain_one_claim():
    text = (
        "Sinh viên K26 cần nộp hồ sơ\n"
        "trước ngày 30/09/2026\n"
        "tại Phòng Công tác Sinh viên."
    )
    claim = extract_one(text)
    assert claim.action is not None
    assert claim.audience.normalized_value == "K26"
    assert claim.deadline.normalized_value == "2026-09-30"
    assert claim.location.text == "Phòng Công tác Sinh viên"
    assert_grounded(text, claim)


def test_blank_line_separates_independent_obligations():
    text = (
        "Sinh viên K26 đăng ký học bổng trước ngày 30/09/2026.\n\n"
        "Sinh viên K25 nộp minh chứng trước ngày 15/10/2026."
    )
    claims = DeterministicTextClaimExtractor().extract(text)
    assert len(claims) == 2
    assert [claim.audience.normalized_value for claim in claims] == ["K26", "K25"]
    assert [claim.deadline.normalized_value for claim in claims] == ["2026-09-30", "2026-10-15"]
    for claim in claims:
        assert_grounded(text, claim)


def test_required_documents_are_only_extracted_with_explicit_trigger():
    text = "Hồ sơ gồm:\n- Đơn đăng ký\n- Bản sao CCCD"
    claim = extract_one(text)
    assert [item.text for item in claim.required_documents] == ["Đơn đăng ký", "Bản sao CCCD"]
    assert_grounded(text, claim)


def test_location_is_exactly_grounded():
    text = "Nộp hồ sơ tại Phòng Công tác Sinh viên."
    claim = extract_one(text)
    assert claim.location.text == "Phòng Công tác Sinh viên"
    assert_grounded(text, claim)


def test_simple_exception_is_exactly_grounded():
    text = "Sinh viên đăng ký, ngoại trừ sinh viên đã tốt nghiệp."
    claim = extract_one(text)
    assert [item.text for item in claim.exceptions] == ["ngoại trừ sinh viên đã tốt nghiệp"]
    assert_grounded(text, claim)


def test_unrelated_text_does_not_invent_fields():
    text = "Nhà trường vừa đăng một thông báo mới."
    claim = extract_one(text)
    assert populated_fields(claim) == []
    assert claim.normalized_text == text


def test_collect_action_remains_available_for_legitimate_receive_phrase():
    text = "Sinh viên nhận kết quả tại Phòng Công tác Sinh viên."
    claim = extract_one(text)
    assert claim.action.text == "nhận"
    assert claim.action.normalized_value == "collect"
    assert_grounded(text, claim)


def test_dong_gop_is_not_misclassified_as_payment():
    text = "Sinh viên tham gia đóng góp ý kiến cho chương trình."
    claim = extract_one(text)
    assert claim.action is not None
    assert claim.action.normalized_value == "attend"
    assert_grounded(text, claim)


def test_dong_hoc_phi_remains_payment_with_exact_grounding():
    text = "Sinh viên cần đóng học phí trước ngày 30/09/2026."
    claim = extract_one(text)
    assert claim.action.text == "đóng"
    assert claim.action.normalized_value == "pay"
    assert_grounded(text, claim)


@pytest.mark.parametrize(
    "text",
    [
        "Đây là nhận định của người viết.",
        "Nội dung chưa thuộc mẫu nhận diện hiện tại.",
        "Đây là nội dung để nhận biết vấn đề.",
        "Bài viết nói về nhận thức cộng đồng.",
    ],
)
def test_lexical_nhan_compounds_are_not_misclassified_as_collect(text):
    claim = extract_one(text)
    assert claim.action is None or claim.action.normalized_value != "collect"
    assert_grounded(text, claim)


def test_raw_claim_remains_available_when_no_fields_are_found():
    text = "Nội dung chưa thuộc mẫu nhận diện hiện tại."
    claim = extract_one(text)
    assert claim.raw_claim_text == text
    assert populated_fields(claim) == []
