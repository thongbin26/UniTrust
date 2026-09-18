import json
import os
import streamlit as st
from frontend.api_client import api_client
from frontend.ui_translations import get_applicability_vi, get_temporal_state_vi, get_field_name_vi

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

@st.cache_data
def load_catalog():
    catalog_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "catalog", "dut_catalog_2026.json")
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"faculties": []}

catalog = load_catalog()

# Initialize session state for profile
if "student_profile" not in st.session_state:
    st.session_state.student_profile = None

# Restore from query_params if session_state is empty
if st.session_state.student_profile is None:
    q_faculty = st.query_params.get("faculty")
    q_major = st.query_params.get("major")
    q_cohort_label = st.query_params.get("cohort_label")
    q_cohort = st.query_params.get("cohort")
    q_program = st.query_params.get("program")
    
    if q_faculty and q_major and q_cohort_label and q_cohort:
        st.session_state.student_profile = {
            "faculty": q_faculty,
            "major": q_major,
            "cohort_label": q_cohort_label,
            "cohort": q_cohort,
            "program": q_program if q_program else "Đại trà"
        }
        st.session_state.edit_mode = False

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = True if st.session_state.student_profile is None else False

if st.session_state.student_profile and not st.session_state.edit_mode:
    profile = st.session_state.student_profile
    st.markdown(f"""
    <div class="profile-card">
        <h3 style="margin-top:0; color:#166534;">Hồ sơ của bạn</h3>
        <div><b>Khoa:</b> {profile.get('faculty')}</div>
        <div><b>Ngành / Chuyên ngành:</b> {profile.get('major')}</div>
        <div><b>Khóa tuyển sinh:</b> {profile.get('cohort_label')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    if col1.button("Chỉnh sửa hồ sơ", use_container_width=True):
        st.session_state.edit_mode = True
        st.rerun()
    if col2.button("Xóa hồ sơ đã lưu", use_container_width=True):
        st.session_state.student_profile = None
        st.session_state.edit_mode = True
        st.query_params.clear()
        st.rerun()
else:
    st.markdown("### Hồ sơ của bạn")
    
    faculty_names = [f["display_name"] for f in catalog.get("faculties", [])]
    
    # Pre-fill if editing
    prev_faculty = st.session_state.student_profile.get("faculty") if st.session_state.student_profile else None
    prev_major = st.session_state.student_profile.get("major") if st.session_state.student_profile else None
    
    faculty_idx = faculty_names.index(prev_faculty) if prev_faculty in faculty_names else 0
    
    selected_faculty = st.selectbox("Khoa", options=faculty_names, index=faculty_idx)
    
    faculty_obj = next((f for f in catalog.get("faculties", []) if f["display_name"] == selected_faculty), None)
    
    if faculty_obj and faculty_obj.get("status") == "UNVERIFIED":
        st.warning("⚠️ Danh mục ngành của khoa này đang được UniTrust cập nhật theo cơ cấu tổ chức mới.")
        major_options = ["Không xác định / Khác"]
    elif faculty_obj:
        major_options = [p["display_name"] for p in faculty_obj.get("programs", []) if p.get("faculty_assignment_status") in ("VERIFIED", "PROVISIONAL")]
        if not major_options:
            major_options = ["Không xác định / Khác"]
        else:
            major_options.append("Không xác định / Khác")
    else:
        major_options = ["Không xác định / Khác"]
    
    major_idx = major_options.index(prev_major) if prev_major in major_options else 0
    selected_major = st.selectbox("Ngành / Chuyên ngành", options=major_options, index=major_idx)

    # Check if selected major is PROVISIONAL
    if faculty_obj:
        for p in faculty_obj.get("programs", []):
            if p["display_name"] == selected_major and p.get("faculty_assignment_status") == "PROVISIONAL":
                st.caption("ℹ️ Thông tin khoa quản lý đang được UniTrust cập nhật theo cơ cấu tổ chức mới.")
                break
    
    cohort_options = [
        "Khóa tuyển sinh 2021 (K21)",
        "Khóa tuyển sinh 2022 (K22)",
        "Khóa tuyển sinh 2023 (K23)",
        "Khóa tuyển sinh 2024 (K24)",
        "Khóa tuyển sinh 2025 (K25)",
        "Khóa tuyển sinh 2026 (K26)",
        "Không xác định"
    ]
    selected_cohort_label = st.selectbox("Khóa tuyển sinh", options=cohort_options)
    
    cohort_map = {
        "Khóa tuyển sinh 2021 (K21)": "K21",
        "Khóa tuyển sinh 2022 (K22)": "K22",
        "Khóa tuyển sinh 2023 (K23)": "K23",
        "Khóa tuyển sinh 2024 (K24)": "K24",
        "Khóa tuyển sinh 2025 (K25)": "K25",
        "Khóa tuyển sinh 2026 (K26)": "K26",
        "Không xác định": None
    }
    selected_cohort = cohort_map[selected_cohort_label]
    
    selected_cohort = cohort_map[selected_cohort_label]
    
    if st.button("Lưu hồ sơ & Xem kết quả", type="primary"):
        st.session_state.student_profile = {
            "faculty": selected_faculty,
            "major": selected_major,
            "cohort_label": selected_cohort_label,
            "cohort": selected_cohort,
            "program": "Đại trà" # Placeholder removed from UI but kept in state safely
        }
        st.session_state.edit_mode = False
        st.query_params["faculty"] = selected_faculty
        st.query_params["major"] = selected_major
        st.query_params["cohort_label"] = selected_cohort_label
        if selected_cohort:
            st.query_params["cohort"] = selected_cohort
        st.rerun()

st.markdown("---")

if st.session_state.student_profile and not st.session_state.edit_mode:
    profile = st.session_state.student_profile
    api_profile = {
        "faculty": profile["faculty"],
        "major": profile["major"],
        "cohort": profile["cohort"]
    }
    
    with st.spinner("Đang tìm kiếm các nghĩa vụ áp dụng..."):
        try:
            results = api_client.for_you(api_profile)
            
            # Sort obligations: upcoming deadlines first, then no deadline
            def sort_key(obs):
                dl = obs['obligation'].get('deadline')
                if dl:
                    return (0, dl)
                return (1, "")
                
            sorted_obs = sorted(results, key=sort_key)
            
            applies = [o for o in sorted_obs if o['applicability_status'] == 'APPLIES']
            unknown = [o for o in sorted_obs if o['applicability_status'] == 'UNKNOWN']
            not_applies = [o for o in sorted_obs if o['applicability_status'] == 'DOES_NOT_APPLY']
            
            def render_obs(o, css_class):
                obs = o['obligation']
                temp_vi = get_temporal_state_vi(o['temporal_status'])
                
                html = f'<div class="obs-card {css_class}">'
                html += f'<h4 class="obs-title">{obs.get("action", "Không rõ hành động")}</h4>'
                
                if obs.get("deadline"):
                    html += f'<div class="obs-detail">⏳ <b>{get_field_name_vi("deadline")}:</b> <span style="color:#b91c1c;">{obs["deadline"]}</span></div>'
                if obs.get("audience"):
                    html += f'<div class="obs-detail">👥 <b>{get_field_name_vi("audience")}:</b> {obs["audience"]}</div>'
                if obs.get("location"):
                    html += f'<div class="obs-detail">📍 <b>{get_field_name_vi("location")}:</b> {obs["location"]}</div>'
                if obs.get("required_documents"):
                    html += f'<div class="obs-detail">📁 <b>{get_field_name_vi("required_documents")}:</b> {obs["required_documents"]}</div>'
                
                source = obs.get("source") or "Chưa rõ"
                html += f'<hr style="margin: 12px 0; border-color: #e5e7eb;">'
                html += f'<div class="obs-detail" style="font-size:0.85rem;"><b>Nguồn:</b> {source} &nbsp;|&nbsp; <b>Phiên bản:</b> {temp_vi}</div>'
                html += '</div>'
                st.markdown(html, unsafe_allow_html=True)
                
                with st.expander("Chi tiết kỹ thuật (Dành cho nhà phát triển)"):
                    st.write(f"**Applicability Reason:** {o.get('applicability_reason')}")
                    st.json(obs)

            st.markdown(f"### Việc áp dụng cho bạn ({len(applies)})")
            if applies:
                for o in applies:
                    render_obs(o, "obs-apply")
            else:
                st.info("Hiện không có việc nào bắt buộc áp dụng trực tiếp cho bạn.")

            st.markdown(f"### Cần kiểm tra thêm ({len(unknown)})")
            if unknown:
                for o in unknown:
                    render_obs(o, "obs-unknown")
            else:
                st.write("Không có việc nào cần kiểm tra thêm.")
                
            with st.expander(f"Không áp dụng ({len(not_applies)})"):
                if not_applies:
                    for o in not_applies:
                        render_obs(o, "obs-not-apply")
                else:
                    st.write("Trống.")
                    
        except Exception as e:
            st.error("Không thể tải thông tin dành cho bạn lúc này. Vui lòng thử lại.")