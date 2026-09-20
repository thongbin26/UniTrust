import logging
from html import escape

import streamlit as st

from frontend.api_client import api_client
from frontend.profile_state import (
    COHORT_LABELS,
    api_profile,
    clear_profile,
    edit_profile,
    load_catalog,
    major_options,
    make_profile,
    save_profile,
    sync_profile_state,
)
from frontend.ui_style import apply_global_styles, page_header, page_marker
from frontend.ui_translations import get_field_name_vi, get_temporal_state_vi


apply_global_styles()
page_marker("for-you")
page_header(
    "Nghĩa vụ theo hồ sơ",
    "Dành cho bạn",
    "Lưu một hồ sơ ngắn để nhận biết thông báo nào có thể áp dụng, thông báo nào còn thiếu dữ liệu và thông báo nào không phù hợp với hồ sơ hiện tại.",
)

catalog = load_catalog()
sync_profile_state(st.session_state, st.query_params, catalog)


def _html_text(value) -> str:
    return escape(str(value or "")).replace("\n", "<br>")


def render_provisional_note() -> None:
    st.markdown(
        '<div class="ut-empty" style="background:var(--ut-warning-soft);border-color:#eadcb7;margin-bottom:1rem;"><strong>Đang tiếp tục đối chiếu</strong>Thông tin đơn vị quản lý đang chờ đối chiếu thêm với nguồn chính thức mới.</div>',
        unsafe_allow_html=True,
    )


def render_obligation(obligation: dict, status_class: str) -> None:
    temporal_label = get_temporal_state_vi(obligation.get("temporal_status") or "UNKNOWN")
    details = []
    if obligation.get("deadline"):
        details.append(
            f'<div class="ut-meta"><strong>{get_field_name_vi("deadline")}:</strong> {escape(str(obligation["deadline"]))}</div>'
        )
    if obligation.get("location"):
        details.append(
            f'<div class="ut-meta"><strong>{get_field_name_vi("location")}:</strong> {escape(str(obligation["location"]))}</div>'
        )
    if obligation.get("amount"):
        details.append(
            f'<div class="ut-meta"><strong>{get_field_name_vi("amount")}:</strong> {escape(str(obligation["amount"]))}</div>'
        )
    documents = obligation.get("required_documents") or []
    if documents:
        details.append(
            f'<div class="ut-meta"><strong>{get_field_name_vi("required_documents")}:</strong> {escape("; ".join(map(str, documents)))}</div>'
        )
    details_html = "".join(details)
    title = _html_text(obligation.get("title") or "Thông báo chính thức")
    raw_action = obligation.get("action_text")
    action = _html_text(raw_action) if raw_action and raw_action != "Unknown" else ""
    canonical_url = obligation.get("canonical_url")
    link_html = (
        f'<a href="{escape(str(canonical_url), quote=True)}" target="_blank" rel="noopener noreferrer" style="color:#1d4ed8;font-weight:650;text-decoration:none;">Xem thông báo chính thức →</a>'
        if canonical_url else ""
    )
    st.markdown(
        f"""
        <div class="ut-card-flat ut-obligation ut-obligation--{status_class}" style="border-left:3px solid var(--ut-{'official' if status_class == 'applies' else 'border-strong'});">
            {f'<h3 style="font-size:1.08rem;line-height:1.5;margin:0 0 .75rem;">{action}</h3>' if action else ''}
            <div style="display:grid;gap:.35rem;">{details_html}</div>
            <hr class="ut-divider">
            <div class="ut-meta"><strong>Nguồn:</strong> {title}</div>
            <div class="ut-meta" style="margin:.3rem 0 .7rem;"><strong>Trạng thái:</strong> {escape(temporal_label)}</div>
            {link_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_obligation_list(items: list[dict], status_class: str, initially_visible: int | None = None) -> None:
    visible = items if initially_visible is None else items[:initially_visible]
    remaining = [] if initially_visible is None else items[initially_visible:]
    for item in visible:
        render_obligation(item, status_class)
    if remaining:
        with st.expander(f"Xem thêm {len(remaining)} thông báo"):
            for item in remaining:
                render_obligation(item, status_class)


profile = st.session_state.student_profile
if profile and not st.session_state.edit_mode:
    faculty_label = escape(profile.get("faculty_label") or "Không xác định")
    major_label = escape(profile.get("major_label") or "Không xác định / Khác")
    cohort_label = escape(COHORT_LABELS.get(profile.get("cohort"), "Không xác định"))
    st.markdown(
        f"""
        <div class="ut-profile-summary">
            <div class="ut-section-kicker">Hồ sơ sinh viên</div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;">
                <div><div class="ut-meta">Khoa</div><strong>{faculty_label}</strong></div>
                <div><div class="ut-meta">Ngành / Chuyên ngành</div><strong>{major_label}</strong></div>
                <div><div class="ut-meta">Khóa tuyển sinh</div><strong>{cohort_label}</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if profile.get("faculty_assignment_status") == "PROVISIONAL":
        render_provisional_note()

    edit_column, clear_column, _ = st.columns([1, 1, 3])
    if edit_column.button("Chỉnh sửa", icon=":material/edit:"):
        edit_profile(st.session_state)
        st.rerun()
    if clear_column.button("Xóa hồ sơ", icon=":material/delete_outline:"):
        clear_profile(st.session_state, st.query_params)
        st.rerun()
else:
    st.markdown('<div class="ut-section-title" style="margin-top:.35rem;">Thiết lập hồ sơ của bạn</div>', unsafe_allow_html=True)
    form_column, _ = st.columns([0.86, 0.14])
    with form_column.container(border=True):
        st.markdown(
            '<div class="ut-helper" style="margin-top:0;"><span class="ut-helper-mark" aria-hidden="true">i</span><span>Chọn những thông tin bạn biết. Bạn có thể để “Không xác định” nếu chưa chắc chắn.</span></div>',
            unsafe_allow_html=True,
        )
        faculty_names = [None] + [faculty["display_name"] for faculty in catalog["faculties"]]
        if st.session_state.get("profile_faculty") not in faculty_names:
            st.session_state.profile_faculty = None

        faculty_column, major_column = st.columns(2, gap="medium")
        with faculty_column:
            selected_faculty = st.selectbox(
                "Khoa",
                options=faculty_names,
                key="profile_faculty",
                format_func=lambda value: value or "Không xác định",
                placeholder="Không xác định",
            )

        majors = [None] + major_options(catalog, selected_faculty)
        if st.session_state.get("profile_major") not in majors:
            st.session_state.profile_major = None
        with major_column:
            selected_major = st.selectbox(
                "Ngành / Chuyên ngành",
                options=majors,
                key="profile_major",
                format_func=lambda value: value or "Không xác định / Khác",
                placeholder="Không xác định / Khác",
            )

        selected_cohort = st.selectbox(
            "Khóa tuyển sinh",
            options=[None] + [cohort for cohort in COHORT_LABELS if cohort is not None],
            key="profile_cohort",
            format_func=lambda value: COHORT_LABELS[value],
            placeholder="Không xác định",
        )
        if selected_faculty and len(majors) == 1:
            st.caption("Danh mục ngành của khoa này đang được xác minh theo cơ cấu tổ chức mới.")

        draft_profile = make_profile(catalog, selected_faculty, selected_major, selected_cohort)
        if draft_profile["faculty_assignment_status"] == "PROVISIONAL":
            render_provisional_note()

        if st.button("Lưu hồ sơ và xem kết quả", type="primary", icon=":material/check:"):
            save_profile(st.session_state, st.query_params, draft_profile)
            st.rerun()

    if not profile:
        st.markdown(
            '<div class="ut-empty"><strong>Sau khi lưu hồ sơ</strong>UniTrust sẽ phân nhóm thông báo thành: có thể áp dụng cho bạn, chưa đủ thông tin để xác định và không áp dụng theo hồ sơ hiện tại.</div>',
            unsafe_allow_html=True,
        )

if st.session_state.student_profile and not st.session_state.edit_mode:
    with st.spinner("Đang tải các nghĩa vụ liên quan..."):
        try:
            response = api_client.for_you(api_profile(st.session_state.student_profile))
            obligations = response["obligations"]
            applies = [item for item in obligations if item["applicability"]["status"] == "APPLIES"]
            unknown = [item for item in obligations if item["applicability"]["status"] == "UNKNOWN"]
            not_applies = [item for item in obligations if item["applicability"]["status"] == "DOES_NOT_APPLY"]

            st.markdown(f'<div class="ut-section-title">Có thể áp dụng cho bạn <span class="ut-count">{len(applies)}</span></div>', unsafe_allow_html=True)
            if applies:
                render_obligation_list(applies, "applies")
            else:
                st.markdown(
                    '<div class="ut-empty"><strong>Chưa có nghĩa vụ áp dụng trực tiếp</strong>Không có thông báo nào khớp đầy đủ với hồ sơ hiện tại.</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(f'<div class="ut-section-title">Chưa đủ thông tin để xác định <span class="ut-count">{len(unknown)}</span></div>', unsafe_allow_html=True)
            if unknown:
                st.caption("Hồ sơ hiện chưa có đủ thông tin để xác định các thông báo dưới đây có áp dụng cho bạn hay không.")
                render_obligation_list(unknown, "unknown", initially_visible=4)
            else:
                st.caption("Không có thông báo nào đang chờ thêm thông tin hồ sơ.")

            with st.expander(f"Không áp dụng theo hồ sơ hiện tại ({len(not_applies)})"):
                if not_applies:
                    render_obligation_list(not_applies, "not-applies")
                else:
                    st.write("Không có thông báo nào trong nhóm này.")
        except Exception:
            logging.getLogger(__name__).exception("For You request or rendering failed")
            st.error("Không thể tải thông tin dành cho bạn lúc này. Vui lòng thử lại.")
