import os
import json
from frontend.ui_translations import (
    get_trust_state_vi,
    get_temporal_state_vi,
    get_applicability_vi,
    get_abstention_reason_vi,
    get_explanation_vi
)
from frontend.demo_cases import DEMO_CASES

def test_trust_state_vi():
    assert get_trust_state_vi("VERIFIED") == "Đã xác minh"
    assert get_trust_state_vi("CONFLICT") == "Có mâu thuẫn"
    assert get_trust_state_vi("PARTIALLY_VERIFIED") == "Xác minh một phần"
    assert get_trust_state_vi("INSUFFICIENT_EVIDENCE") == "Chưa đủ bằng chứng"
    assert get_trust_state_vi("UNKNOWN_VERDICT") == "UNKNOWN_VERDICT"

def test_temporal_state_vi():
    assert get_temporal_state_vi("CURRENT") == "Phiên bản hiện hành"
    assert get_temporal_state_vi("SUPERSEDED_OUTDATED") == "Đã bị thay thế / lỗi thời"
    assert get_temporal_state_vi("UNKNOWN") == "Chưa xác định phiên bản"

def test_applicability_vi():
    assert get_applicability_vi("APPLIES") == "Áp dụng cho bạn"
    assert get_applicability_vi("DOES_NOT_APPLY") == "Không áp dụng"
    assert get_applicability_vi("UNKNOWN") == "Chưa đủ thông tin để xác định"

def test_abstention_reasons_vi():
    assert get_abstention_reason_vi("NO_OFFICIAL_FIELD") == "Chưa có bằng chứng chính thức cho loại thông tin này."
    assert get_abstention_reason_vi(None) == "Không có"

def test_explanation_vi():
    assert "khớp với bằng chứng" in get_explanation_vi("VERIFIED")

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
