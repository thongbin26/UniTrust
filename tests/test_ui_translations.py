import os
import json
import pytest
from frontend.ui_translations import (
    get_trust_state_vi,
    get_temporal_state_vi,
    get_applicability_vi,
    get_abstention_reason_vi,
    get_explanation_vi,
    get_field_state_vi,
    get_notice_title_vi,
    get_source_name_vi,
    get_url_fetch_error_vi,
    get_url_fetch_warning_vi,
    format_date_vi,
)
from frontend.demo_cases import DEMO_CASES

def test_trust_state_vi():
    assert get_trust_state_vi("VERIFIED") == "Đã xác minh"
    assert get_trust_state_vi("CONFLICT") == "Có thông tin mâu thuẫn"
    assert get_trust_state_vi("PARTIALLY_VERIFIED") == "Xác minh một phần"
    assert get_trust_state_vi("INSUFFICIENT_EVIDENCE") == "Chưa đủ bằng chứng"
    assert get_trust_state_vi("UNKNOWN_VERDICT") == "UNKNOWN_VERDICT"

def test_temporal_state_vi():
    assert get_temporal_state_vi("CURRENT") == "Phiên bản hiện hành"
    assert get_temporal_state_vi("SUPERSEDED_OUTDATED") == "Đã có phiên bản mới hơn"
    assert get_temporal_state_vi("UNKNOWN") == "Chưa xác định phiên bản"

def test_applicability_vi():
    assert get_applicability_vi("APPLIES") == "Có thể áp dụng cho bạn"
    assert get_applicability_vi("DOES_NOT_APPLY") == "Không áp dụng theo hồ sơ hiện tại"
    assert get_applicability_vi("UNKNOWN") == "Chưa đủ thông tin để xác định"

def test_abstention_reasons_vi():
    assert get_abstention_reason_vi("NO_OFFICIAL_FIELD") == (
        "Chưa tìm thấy bằng chứng chính thức đủ phù hợp để đối chiếu với nội dung này."
    )
    assert get_abstention_reason_vi(None) == "Không có"

@pytest.mark.parametrize("code", [
    "INVALID_URL", "UNSAFE_URL", "FETCH_TIMEOUT", "FETCH_FAILED", "TOO_LARGE",
    "UNSUPPORTED_CONTENT_TYPE", "EMPTY_CONTENT", "TOO_MANY_REDIRECTS",
])
def test_url_fetch_errors_are_safe_and_vietnamese(code):
    message = get_url_fetch_error_vi(code)
    assert message
    assert code not in message


def test_url_fetch_messages_have_expected_fallback_and_warning():
    assert get_url_fetch_error_vi("UNSAFE_URL") == "Đường link này không thể được truy cập vì lý do an toàn."
    assert get_url_fetch_error_vi("UNKNOWN") == "Không thể đọc nội dung từ đường link này."
    assert "CONTENT_TRUNCATED" not in get_url_fetch_warning_vi("CONTENT_TRUNCATED")

def test_explanation_vi():
    assert "khớp với bằng chứng" in get_explanation_vi("VERIFIED")

def test_field_state_and_source_names_vi():
    assert get_field_state_vi("MATCH") == "Khớp với nguồn chính thức"
    assert get_field_state_vi("CONFLICT") == "Có mâu thuẫn"
    assert get_field_state_vi("UNKNOWN_VALUE") == "Chưa xác định"
    assert get_source_name_vi("dut_academic", "DUT Academic and Examination Notices") == "Thông báo đào tạo và khảo thí DUT"
    assert get_source_name_vi("unknown", "Nguồn đã xác nhận") == "Nguồn đã xác nhận"
    assert format_date_vi("2026-09-14T15:58:00+07:00") == "14/09/2026"
    assert format_date_vi(None) == "Chưa xác định"
    assert format_date_vi("Học kỳ I") == "Học kỳ I"

def test_notice_title_hides_flattened_source_badges_only_at_suffix():
    assert get_notice_title_vi("Thông báo tuyển sinh Hot") == "Thông báo tuyển sinh"
    assert get_notice_title_vi("Thông báo mới New") == "Thông báo mới"
    assert get_notice_title_vi("Hot topic trong học thuật") == "Hot topic trong học thuật"
    assert get_notice_title_vi("New Zealand scholarship") == "New Zealand scholarship"

def test_demo_cases_schema_unchanged():
    assert isinstance(DEMO_CASES, list)
    assert len(DEMO_CASES) >= 3
    # Check that case B is labeled synthetic
    assert "SYNTHETIC DEMO MUTATION" in DEMO_CASES[1]["label"]

def test_dut_catalog_schema():
    catalog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "catalog", "dut_catalog_2026.json")
    assert os.path.exists(catalog_path)
    
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
        
    assert "catalog_year" in catalog
    assert catalog["catalog_year"] == 2026
    
    faculties = catalog["faculties"]
    assert len(faculties) >= 9
    
    cntt = next(f for f in faculties if f["display_name"] == "Khoa Công nghệ Thông tin")
    programs = [p["display_name"] for p in cntt["programs"]]
    assert "Công nghệ thông tin" in programs

def test_cohort_mapping_logic():
    # Extracted logic from For You page
    cohorts_mapping = {
        "Khóa tuyển sinh 2021 (K21)": "K21",
        "Khóa tuyển sinh 2022 (K22)": "K22",
        "Khóa tuyển sinh 2023 (K23)": "K23",
        "Khóa tuyển sinh 2024 (K24)": "K24",
        "Khóa tuyển sinh 2025 (K25)": "K25",
        "Khóa tuyển sinh 2026 (K26)": "K26",
        "Không xác định / Khác": ""
    }
    assert cohorts_mapping["Khóa tuyển sinh 2022 (K22)"] == "K22"
    assert cohorts_mapping["Khóa tuyển sinh 2026 (K26)"] == "K26"
    assert cohorts_mapping["Không xác định / Khác"] == ""

def test_dependent_dropdown_helper_logic():
    catalog = {
        "faculties": [
            {"display_name": "Khoa A", "programs": [{"display_name": "M1"}, {"display_name": "M2"}]},
            {"display_name": "Khoa B", "programs": [{"display_name": "M3"}]}
        ]
    }
    
    def get_majors_for_faculty(fac_name):
        for f in catalog["faculties"]:
            if f["display_name"] == fac_name:
                return [p["display_name"] for p in f.get("programs", [])]
        return []

    assert get_majors_for_faculty("Khoa A") == ["M1", "M2"]
    assert get_majors_for_faculty("Khoa B") == ["M3"]
    assert get_majors_for_faculty("Khoa C") == []
