import json
from collections import Counter
from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

from frontend.profile_state import load_catalog, major_options, make_profile, restore_profile


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data/catalog/dut_catalog_2026.json"
OFFICIAL_SOURCE_TYPES = {
    "OFFICIAL_ANNOUNCEMENT",
    "OFFICIAL_CURRENT_DIRECTORY",
    "OFFICIAL_ADMISSIONS_CATALOG",
    "OFFICIAL_HISTORICAL_ADMISSIONS_TABLE",
    "OFFICIAL_PRE_RESTRUCTURE_ADMISSIONS_NOTICE",
    "OFFICIAL_CURRENT_FACULTY_PAGE",
}


def catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def programs(data):
    return [program for faculty in data["faculties"] for program in faculty["programs"]] + data["unassigned_programs"]


def test_current_faculty_structure_is_nine_unique_named_faculties():
    data = catalog()
    ids = [faculty["faculty_id"] for faculty in data["faculties"]]
    assert len(ids) == len(set(ids)) == 9
    assert all(faculty["display_name"].strip() for faculty in data["faculties"])
    assert all(faculty["status"] == "VERIFIED" for faculty in data["faculties"])


def test_catalog_reconciles_all_49_programs_and_declared_status_counts():
    data = catalog()
    audited = programs(data)
    assert len(audited) == data["institution_program_count"] == 49
    declared = {status: data["audit_summary"][status] for status in ("VERIFIED", "PROVISIONAL", "UNVERIFIED")}
    assert Counter(p["faculty_assignment_status"] for p in audited) == declared


def test_official_codes_are_unique_when_present():
    codes = [p["official_code"] for p in programs(catalog()) if p["official_code"]]
    assert len(codes) == len(set(codes))


def test_verified_mapping_has_direct_current_official_source():
    data = catalog()
    registry = data["source_registry"]
    verified = [p for p in programs(data) if p["faculty_assignment_status"] == "VERIFIED"]
    assert verified
    for program in verified:
        evidence = [registry[source_id] for source_id in program["sources"]]
        assert any(source["source_type"] == "OFFICIAL_CURRENT_FACULTY_PAGE" for source in evidence)


def test_provisional_and_unverified_are_not_masquerading_as_verified():
    data = catalog()
    assert all(p["faculty_assignment_status"] != "VERIFIED" for p in programs(data) if p in data["unassigned_programs"])
    assert all(p["faculty_assignment_status"] in {"PROVISIONAL", "UNVERIFIED"} for p in programs(data) if p["faculty_assignment_status"] != "VERIFIED")


def test_unverified_programs_are_unassigned_and_hidden_from_faculty_options():
    data = catalog()
    visible = {name for faculty in data["faculties"] for name in major_options(data, faculty["display_name"])}
    for program in data["unassigned_programs"]:
        assert program["faculty_assignment_status"] == "UNVERIFIED"
        assert program["faculty_id"] is None
        assert program["display_name"] not in visible


def test_effective_dates_parse_when_present():
    data = catalog()
    values = [data["organization_effective_date"]]
    values += [faculty.get("effective_from") for faculty in data["faculties"]]
    values += [program.get("effective_from") for program in programs(data)]
    for value in filter(None, values):
        date.fromisoformat(value)


def test_source_records_keep_publication_effective_and_retrieval_dates_distinct():
    for source in catalog()["source_registry"].values():
        assert {"published_date", "effective_date", "retrieved_date"} <= source.keys()
        assert source["retrieved_date"]
        for field in ("published_date", "effective_date", "retrieved_date"):
            if source[field]:
                date.fromisoformat(source[field])


def test_all_source_references_exist_and_verified_faculty_sources_are_official():
    data = catalog()
    registry = data["source_registry"]
    for faculty in data["faculties"]:
        assert all(source_id in registry for source_id in faculty["sources"])
        assert any(registry[source_id]["source_type"] in OFFICIAL_SOURCE_TYPES for source_id in faculty["sources"])
        for program in faculty["programs"]:
            assert all(source_id in registry for source_id in program["sources"])
    assert all(all(source_id in registry for source_id in p["sources"]) for p in data["unassigned_programs"])


def test_dsai_stays_provisional_without_direct_official_current_evidence():
    data = catalog()
    dsai = next(p for p in programs(data) if p["official_code"] == "7480201B")
    assert dsai["faculty_assignment_status"] == "PROVISIONAL"
    assert dsai["faculty_id"] == "khoa_dien_tu_tri_tue_nhan_tao"
    assert "project_owner_dsai" in dsai["sources"]
    assert data["source_registry"]["project_owner_dsai"]["url"] is None


def test_migration_history_preserves_old_source_and_does_not_promote_owner_report():
    migration = catalog()["migration_audit"][0]
    assert migration["old_source_date"] < migration["new_source_date"]
    assert migration["status"] == "PROVISIONAL"
    assert migration["old_source"] != migration["new_source"]


def test_saved_profile_alias_migrates_without_crashing():
    data = load_catalog()
    restored = restore_profile(data, {"profile": "1", "faculty": "Khoa Điện tử và Trí tuệ nhân tạo", "major": "Khoa học dữ liệu và Trí tuệ nhân tạo", "cohort": "K26"})
    assert restored["major_label"] == "Công nghệ thông tin, chuyên ngành Khoa học dữ liệu và Trí tuệ nhân tạo"
    assert restored["faculty_assignment_status"] == "PROVISIONAL"


def test_profile_page_never_displays_raw_assignment_status_enums():
    page = AppTest.from_file(ROOT / "frontend/pages/3_For_You.py").run(timeout=20)
    rendered = " ".join(markdown.value for markdown in page.markdown)
    assert "PROVISIONAL" not in rendered
    assert "UNVERIFIED" not in rendered


def test_unknown_program_cannot_be_silently_assigned_by_profile_builder():
    data = load_catalog()
    unverified = catalog()["unassigned_programs"][0]["display_name"]
    profile = make_profile(data, "Khoa Công nghệ Thông tin", unverified, "K26")
    assert profile["major_label"] is None
    assert profile["faculty_assignment_status"] == "UNKNOWN"
