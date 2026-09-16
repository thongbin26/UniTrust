from app.extraction.grounding import (
    find_grounded_text,
)


def test_exact_evidence():
    raw = (
        "Sinh viên đăng ký trực tuyến "
        "từ ngày 26/05/2026 đến hết "
        "ngày 31/05/2026."
    )

    result = find_grounded_text(
        raw,
        raw,
    )

    assert result == raw


def test_ground_whitespace_difference():
    raw = (
        "Sinh viên tham gia học kỳ hè\n"
        "sử dụng tài khoản cá nhân."
    )

    result = find_grounded_text(
        "Sinh viên tham gia học kỳ hè "
        "sử dụng tài khoản cá nhân.",
        raw,
    )

    assert result is not None
    assert result in raw


def test_reject_unrelated_evidence():
    raw = (
        "Sinh viên đăng ký trước "
        "ngày 20/09/2026."
    )

    result = find_grounded_text(
        "Sinh viên phải nộp học phí "
        "5 triệu đồng.",
        raw,
    )

    assert result is None