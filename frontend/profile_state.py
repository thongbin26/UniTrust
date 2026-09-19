"""Profile labels, evidence values, and URL persistence (no applicability rules)."""

import json
import logging
from functools import lru_cache
from pathlib import Path


COHORT_LABELS = {
    f"K{year % 100}": f"Khóa tuyển sinh {year} (K{year % 100})"
    for year in range(2021, 2027)
}
COHORT_LABELS[None] = "Không xác định"

# Reviewed notice 13, obligation o2: audience.majors == ["CNTT"].
# This is a major-name alias, not a post-restructure faculty assignment.
MAJOR_VALUES = {"Công nghệ thông tin": "CNTT"}
PROFILE_QUERY_KEYS = {"profile", "faculty", "major", "cohort", "cohort_label", "program"}
PROFILE_WIDGET_KEYS = ("profile_faculty", "profile_major", "profile_cohort")


@lru_cache(maxsize=1)
def load_catalog():
    path = Path(__file__).resolve().parents[1] / "data/catalog/dut_catalog_2026.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logging.getLogger(__name__).exception("Cannot load profile catalog")
        return {"faculties": []}


def major_options(catalog, faculty_label):
    faculty = next((f for f in catalog["faculties"] if f["display_name"] == faculty_label), None)
    if not faculty or faculty["status"] == "UNVERIFIED":
        return []
    return [p["display_name"] for p in faculty["programs"]
            if p["faculty_assignment_status"] in ("VERIFIED", "PROVISIONAL")]


def make_profile(catalog, faculty_label, major_label, cohort):
    faculty = next((f for f in catalog["faculties"] if f["display_name"] == faculty_label), None)
    faculty_label = faculty["display_name"] if faculty else None
    if major_label not in major_options(catalog, faculty_label):
        major_label = None
    program = next((p for p in faculty["programs"] if p["display_name"] == major_label), None) if faculty else None
    return {
        "faculty_label": faculty_label,
        "major_label": major_label,
        # Reviewed audience.faculties has no canonical values in batch_001.
        # Do not invent an alias from a current faculty name to historical evidence.
        "faculty": None,
        "major": MAJOR_VALUES.get(major_label),
        "cohort": cohort if cohort in COHORT_LABELS else None,
        "program": None,
        "faculty_assignment_status": program["faculty_assignment_status"] if program else "UNKNOWN",
    }


def api_profile(profile):
    return {key: profile[key] for key in ("faculty", "major", "cohort", "program")}


def restore_profile(catalog, params):
    # The marker also permits a saved profile with all dimensions unknown.
    # Accept old label URLs, but never trust their program or canonical values.
    if params.get("profile") != "1" and not (params.get("faculty") or params.get("major")):
        return None
    return make_profile(catalog, params.get("faculty"), params.get("major"), params.get("cohort"))


def sync_profile_query(params, profile):
    desired = {}
    if profile is not None:
        desired = {"profile": "1"}
        for key, value in (("faculty", profile["faculty_label"]),
                           ("major", profile["major_label"]), ("cohort", profile["cohort"])):
            if value is not None:
                desired[key] = value
    for key in PROFILE_QUERY_KEYS:
        if key in params and key not in desired:
            del params[key]
    for key, value in desired.items():
        if params.get(key) != value:
            params[key] = value


def sync_profile_state(state, params, catalog):
    profile = state.get("student_profile")
    if profile is None:
        profile = restore_profile(catalog, params)
    else:
        # Migrate an existing session's old display-only state without assumptions.
        profile = make_profile(catalog, profile.get("faculty_label", profile.get("faculty")),
                               profile.get("major_label", profile.get("major")), profile.get("cohort"))
    state["student_profile"] = profile
    if "edit_mode" not in state:
        state["edit_mode"] = profile is None
    sync_profile_query(params, profile)


def save_profile(state, params, profile):
    state["student_profile"] = profile
    state["edit_mode"] = False
    sync_profile_query(params, profile)


def edit_profile(state):
    profile = state["student_profile"]
    state["profile_faculty"] = profile["faculty_label"]
    state["profile_major"] = profile["major_label"]
    state["profile_cohort"] = profile["cohort"]
    state["edit_mode"] = True


def clear_profile(state, params):
    state["student_profile"] = None
    state["edit_mode"] = True
    for key in PROFILE_WIDGET_KEYS:
        # Explicitly reset widget values so the Streamlit frontend cannot
        # restore the previous selection after the rerun.
        state[key] = None
    sync_profile_query(params, None)
