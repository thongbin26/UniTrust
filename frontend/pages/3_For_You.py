import streamlit as st
from frontend.api_client import api_client

st.set_page_config(page_title="For You", page_icon="👤", layout="wide")
st.title("👤 Dành cho bạn (Nghĩa vụ)")
st.markdown("Nhập thông tin hồ sơ của bạn (không lưu trữ) để xem các nghĩa vụ liên quan từ trường.")

st.info("UniTrust currently has human-reviewed structured coverage for a subset of the indexed DUT notices. Obligations from other notices may not appear here.")

with st.form("profile_form"):
    col1, col2 = st.columns(2)
    with col1:
        faculty = st.text_input("Khoa (VD: CNTT)")
        major = st.text_input("Ngành (VD: Kỹ thuật phần mềm)")
    with col2:
        cohort = st.text_input("Khóa (VD: K22)")
        program = st.text_input("Chương trình (VD: CLC)")
        
    submitted = st.form_submit_button("Tìm nghĩa vụ liên quan")
    
if submitted:
    with st.spinner("Fetching obligations..."):
        try:
            resp = api_client.get_for_you(
                faculty=faculty if faculty.strip() else None,
                major=major if major.strip() else None,
                cohort=cohort if cohort.strip() else None,
                program=program if program.strip() else None
            )
            obligations = resp.get("obligations", [])
            
            if not obligations:
                st.info("Không tìm thấy nghĩa vụ nào trong dữ liệu đã xác minh.")
            else:
                st.subheader("Nghĩa vụ Sắp tới / Liên quan (APPLIES)")
                
                # Separate by Applicability
                applies = [o for o in obligations if o['applicability']['status'] == "APPLIES"]
                unknown = [o for o in obligations if o['applicability']['status'] == "UNKNOWN"]
                
                for obs in applies:
                    st.success(f"**{obs['action_text']}** (Hạn chót: {obs['deadline'] or 'Không có'})")
                    st.markdown(f"*Nguồn: {obs['title']}*")
                    st.markdown(f"Trạng thái: **{obs['temporal_status']}** | Áp dụng: **CÓ (APPLIES)**")
                    if obs.get('required_documents'):
                        st.markdown(f"Giấy tờ yêu cầu: {', '.join(obs['required_documents'])}")
                    st.divider()
                    
                if unknown:
                    st.subheader("Có thể liên quan — Chưa đủ thông tin đối tượng (UNKNOWN)")
                    for obs in unknown:
                        st.warning(f"**{obs['action_text']}** (Hạn chót: {obs['deadline'] or 'Không có'})")
                        st.markdown(f"*Nguồn: {obs['title']}*")
                        st.markdown(f"Trạng thái: **{obs['temporal_status']}** | Áp dụng: **CHƯA RÕ (UNKNOWN)** ({obs['applicability']['explanation']})")
                        st.divider()
                        
        except Exception as e:
            st.error(f"Error fetching obligations: {e}")
