import logging
from html import escape
import streamlit as st
from frontend.api_client import api_client
from frontend.ui_translations import get_temporal_state_vi, get_field_name_vi
from frontend.profile_state import (
    COHORT_LABELS, api_profile, clear_profile, edit_profile, load_catalog,
    major_options, make_profile, save_profile, sync_profile_state,
)

st.markdown("""
<style>
    .stCard {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }
    .profile-card {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
    }
    .obs-card {
        background-color: #ffffff;
        border-left: 5px solid #3b82f6;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        border-top: 1px solid #e5e7eb;
        border-right: 1px solid #e5e7eb;
        border-bottom: 1px solid #e5e7eb;
    }
    .obs-apply { border-left-color: #10b981; }
    .obs-unknown { border-left-color: #f59e0b; }
    .obs-not-apply { border-left-color: #9ca3af; }
    
    .obs-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #111827;
        margin-top: 0;
        margin-bottom: 8px;
    }
    .obs-detail {
        font-size: 0.95rem;
        color: #4b5563;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

st.title("👤 Dành cho bạn")
st.markdown("Xem danh sách các nghĩa vụ và yêu cầu được cá nhân hóa dựa trên hồ sơ của bạn.")

catalog = load_catalog()
sync_profile_state(st.session_state, st.query_params, catalog)

if st.session_state.student_profile and not st.session_state.edit_mode:
    profile = st.session_state.student_profile
    st.markdown(f"""
    <div class="profile-card">
        <h3 style="margin-top:0; color:#166534;">Hồ sơ của bạn</h3>
        <div><b>Khoa:</b> {escape(profile['faculty_label'] or 'Không xác định')}</div>
        <div><b>Ngành / Chuyên ngành:</b> {escape(profile['major_label'] or 'Không xác định / Khác')}</div>
        <div><b>Khóa tuyển sinh:</b> {COHORT_LABELS[profile['cohort']]}</div>
    </div>
    """, unsafe_allow_html=True)
    if profile["faculty_assignment_status"] == "PROVISIONAL":
        st.caption("ℹ️ Thông tin khoa quản lý của ngành này còn tạm thời, chưa có xác nhận chính thức sau tái cơ cấu.")

    col1, col2 = st.columns([1, 1])
    if col1.button("Chỉnh sửa hồ sơ", use_container_width=True):
        edit_profile(st.session_state)
        st.rerun()
    if col2.button("Xóa hồ sơ đã lưu", use_container_width=True):
        clear_profile(st.session_state, st.query_params)
        st.rerun()
else:
    st.markdown("### Hồ sơ của bạn")
    faculty_names = [None] + [f["display_name"] for f in catalog["faculties"]]
    if st.session_state.get("profile_faculty") not in faculty_names:
        st.session_state.profile_faculty = None
    selected_faculty = st.selectbox(
        "Khoa", options=faculty_names, key="profile_faculty",
        format_func=lambda value: value or "Không xác định",
    )

    majors = [None] + major_options(catalog, selected_faculty)
    if st.session_state.get("profile_major") not in majors:
        st.session_state.profile_major = None
    selected_major = st.selectbox(
        "Ngành / Chuyên ngành", options=majors, key="profile_major",
        format_func=lambda value: value or "Không xác định / Khác",
    )
    if selected_faculty and len(majors) == 1:
        st.caption("Danh mục ngành của khoa này đang được xác minh theo cơ cấu tổ chức mới.")

    selected_cohort = st.selectbox(
        "Khóa tuyển sinh", options=[None] + [c for c in COHORT_LABELS if c is not None],
        key="profile_cohort", format_func=lambda value: COHORT_LABELS[value],
    )
    draft_profile = make_profile(catalog, selected_faculty, selected_major, selected_cohort)
    if draft_profile["faculty_assignment_status"] == "PROVISIONAL":
        st.caption("ℹ️ Thông tin khoa quản lý của ngành này còn tạm thời, chưa có xác nhận chính thức sau tái cơ cấu.")

    if st.button("Lưu hồ sơ & Xem kết quả", type="primary"):
        save_profile(st.session_state, st.query_params, draft_profile)
        st.rerun()

st.markdown("---")

if st.session_state.student_profile and not st.session_state.edit_mode:
    profile = st.session_state.student_profile
    with st.spinner("Đang tìm kiếm các nghĩa vụ áp dụng..."):
        try:
            response = api_client.for_you(api_profile(profile))
            obligations = response["obligations"]
            # Preserve backend order; deadline is display text, not a sortable date.
            applies = [o for o in obligations if o["applicability"]["status"] == "APPLIES"]
            unknown = [o for o in obligations if o["applicability"]["status"] == "UNKNOWN"]
            not_applies = [o for o in obligations if o["applicability"]["status"] == "DOES_NOT_APPLY"]

            def render_obs(obs, css_class):
                temp_vi = get_temporal_state_vi(obs["temporal_status"])
                html = f'<div class="obs-card {css_class}">'
                html += f'<h4 class="obs-title">{escape(obs["action_text"])}</h4>'
                if obs["deadline"]:
                    html += f'<div class="obs-detail">⏳ <b>{get_field_name_vi("deadline")}:</b> <span style="color:#b91c1c;">{escape(obs["deadline"])}</span></div>'
                if obs["location"]:
                    html += f'<div class="obs-detail">📍 <b>{get_field_name_vi("location")}:</b> {escape(obs["location"])}</div>'
                if obs["required_documents"]:
                    documents = "; ".join(obs["required_documents"])
                    html += f'<div class="obs-detail">📁 <b>{get_field_name_vi("required_documents")}:</b> {escape(documents)}</div>'
                html += '<hr style="margin: 12px 0; border-color: #e5e7eb;">'
                html += f'<div class="obs-detail" style="font-size:0.85rem;"><b>Thông báo:</b> {escape(obs["title"])} &nbsp;|&nbsp; <b>Phiên bản:</b> {escape(temp_vi)}</div>'
                if obs["canonical_url"]:
                    html += f'<a href="{escape(obs["canonical_url"])}" target="_blank">Xem thông báo gốc</a>'
                html += '</div>'
                st.markdown(html, unsafe_allow_html=True)

            st.markdown(f"### Có thể áp dụng cho bạn ({len(applies)})")
            if applies:
                for o in applies:
                    render_obs(o, "obs-apply")
            else:
                st.info("Hiện không có việc nào bắt buộc áp dụng trực tiếp cho bạn.")

            st.markdown(f"### Chưa đủ thông tin để xác định ({len(unknown)})")
            if unknown:
                for o in unknown:
                    render_obs(o, "obs-unknown")
            else:
                st.write("Không có việc nào cần kiểm tra thêm.")
                
            with st.expander(f"Không áp dụng theo hồ sơ hiện tại ({len(not_applies)})"):
                if not_applies:
                    for o in not_applies:
                        render_obs(o, "obs-not-apply")
                else:
                    st.write("Trống.")
                    
        except Exception:
            logging.getLogger(__name__).exception("For You request or rendering failed")
            st.error("Không thể tải thông tin dành cho bạn lúc này. Vui lòng thử lại.")
