import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from frontend.profile_state import (
    COHORT_LABELS, PROFILE_WIDGET_KEYS, api_profile, clear_profile, edit_profile,
    load_catalog, make_profile, restore_profile, save_profile, sync_profile_state,
)
from tests.phase1_fixtures import phase1_client, frontend_http


FACULTY = "Khoa Công nghệ Thông tin"
MAJOR = "Công nghệ thông tin"


def profile(cohort="K22"):
    return make_profile(load_catalog(), FACULTY, MAJOR, cohort)


def test_canonical_alias_is_grounded_in_reviewed_vocabulary():
    root = Path(__file__).resolve().parents[1]
    reviewed = json.loads((root / "data/annotations/batch_001/09_notice_13.json").read_text(encoding="utf-8"))
    audience = next(o["audience"] for o in reviewed["obligations"] if o["obligation_id"] == "o2")
    saved = profile()
    assert saved["major_label"] == MAJOR
    assert api_profile(saved)["major"] == "CNTT"
    assert api_profile(saved)["major"] in audience["majors"]
    assert api_profile(saved)["cohort"] in audience["cohorts"]
    assert api_profile(saved)["program"] is None


def test_unestablished_canonical_values_are_not_guessed():
    saved = make_profile(load_catalog(), FACULTY, "Kỹ thuật phần mềm", "K22")
    assert saved["major_label"] == "Kỹ thuật phần mềm"
    assert api_profile(saved)["major"] is None
    assert api_profile(saved)["faculty"] is None


def test_provisional_relationship_survives_save_restore():
    saved = make_profile(load_catalog(), "Khoa Điện tử và Trí tuệ nhân tạo",
                         "Khoa học dữ liệu và Trí tuệ nhân tạo", "K26")
    state, params = {}, {}
    save_profile(state, params, saved)
    restored = restore_profile(load_catalog(), params)
    assert restored == saved
    assert restored["faculty_assignment_status"] == "PROVISIONAL"
    assert restored["major"] is None and restored["faculty"] is None


@pytest.mark.parametrize("cohort", ["K22", None])
def test_save_restore_and_refresh(cohort):
    state, params = {}, {"unrelated": ["keep", "both"]}
    save_profile(state, params, profile(cohort))
    assert state["edit_mode"] is False
    assert restore_profile(load_catalog(), params) == profile(cohort)
    refreshed_state = {}
    sync_profile_state(refreshed_state, params, load_catalog())
    assert refreshed_state["student_profile"] == profile(cohort)
    assert refreshed_state["edit_mode"] is False
    assert params["unrelated"] == ["keep", "both"]


def test_unknown_cohort_removes_stale_query_parameters():
    state, params = {}, {"cohort": "K22", "cohort_label": COHORT_LABELS["K22"], "program": "Đại trà"}
    save_profile(state, params, profile(None))
    assert "cohort" not in params and "cohort_label" not in params and "program" not in params
    restored = restore_profile(load_catalog(), params)
    assert restored["faculty_label"] == FACULTY and restored["major_label"] == MAJOR
    assert restored["cohort"] is None and restored["program"] is None


def test_unknown_major_removes_stale_query_parameter():
    state, params = {}, {"faculty": FACULTY, "major": MAJOR, "cohort": "K22"}
    save_profile(state, params, make_profile(load_catalog(), FACULTY, None, "K22"))
    assert "major" not in params
    assert restore_profile(load_catalog(), params)["major"] is None


def test_navigation_repopulates_profile_query_then_refresh_restores():
    state = {"student_profile": profile(), "edit_mode": False}
    # Streamlit navigation clears the URL. Home.py runs this helper on every page.
    params = {}
    sync_profile_state(state, params, load_catalog())
    refreshed = {}
    sync_profile_state(refreshed, params, load_catalog())
    assert refreshed["student_profile"] == profile()


def test_edit_restores_labels_and_canonical_cohort():
    state = {"student_profile": profile(), "edit_mode": False}
    edit_profile(state)
    assert state["profile_faculty"] == FACULTY
    assert state["profile_major"] == MAJOR
    assert state["profile_cohort"] == "K22"
    assert state["student_profile"]["major"] == "CNTT"
    assert state["edit_mode"] is True


def test_clear_only_removes_profile_state_and_query_parameters():
    state, params = {"other_state": 42}, {"other_param": ["a", "b"]}
    save_profile(state, params, profile())
    edit_profile(state)
    clear_profile(state, params)
    assert state["student_profile"] is None
    assert state["edit_mode"] is True
    assert all(state[key] is None for key in PROFILE_WIDGET_KEYS)
    assert state["other_state"] == 42 and params == {"other_param": ["a", "b"]}
    assert restore_profile(load_catalog(), params) is None


def test_legacy_query_restores_without_cohort_or_program_assumptions():
    params = {"faculty": FACULTY, "major": MAJOR, "program": "Đại trà"}
    state = {}
    sync_profile_state(state, params, load_catalog())
    assert state["student_profile"] == profile(None)
    assert "program" not in params


def test_unknown_or_incompatible_query_values_are_not_sent_as_canonical():
    saved = restore_profile(load_catalog(), {"profile": "1", "faculty": FACULTY,
                                           "major": "Unrecognized", "cohort": "K999"})
    assert saved["major_label"] is None and saved["cohort"] is None
    assert api_profile(saved) == {"faculty": None, "major": None, "cohort": None, "program": None}


def test_page_save_edit_unknown_cohort_refresh_clear(frontend_http):
    page = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/pages/3_For_You.py").run(timeout=20)
    page.selectbox(key="profile_faculty").select(FACULTY).run()
    page.selectbox(key="profile_major").select(MAJOR).run()
    page.selectbox(key="profile_cohort").select("K22").run()
    page.button[0].click().run()
    assert not page.exception and not page.error
    assert frontend_http[-1][2] == api_profile(profile())

    page.button[0].click().run()
    assert page.selectbox(key="profile_faculty").value == FACULTY
    assert page.selectbox(key="profile_major").value == MAJOR
    assert page.selectbox(key="profile_cohort").value == "K22"
    page.selectbox(key="profile_cohort").select(None).run()
    page.button[0].click().run()
    assert "cohort" not in page.query_params
    assert frontend_http[-1][2]["cohort"] is None

    refreshed = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/pages/3_For_You.py")
    refreshed.query_params.update(page.query_params)
    refreshed.run()
    assert not refreshed.exception and not refreshed.error
    assert refreshed.session_state["student_profile"] == profile(None)
    refreshed.button[1].click().run()
    assert refreshed.session_state["student_profile"] is None
    assert refreshed.query_params == {}
    assert all(widget.value is None for widget in refreshed.selectbox)
