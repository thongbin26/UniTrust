from app.extraction.canonicalizer import (
    dates_in_raw_text,
)


def test_dates_in_raw_text():

    raw = (
        "Sinh viên đăng ký từ ngày "
        "26/05/2026 đến ngày 31/05/2026. "
        "Nộp hồ sơ ngày 02/06/2026."
    )

    values = dates_in_raw_text(
        raw
    )

    assert values == {
        "2026-05-26",
        "2026-05-31",
        "2026-06-02",
    }

    assert (
        "2026-09-20"
        not in values
    )