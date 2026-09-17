import streamlit as st
from frontend.api_client import api_client

st.set_page_config(page_title="For You", page_icon="👤", layout="wide")
st.title("👤 For You (Obligations)")
st.markdown("Enter your stateless profile to see relevant official obligations.")

st.info("UniTrust currently has human-reviewed structured coverage for a subset of the indexed DUT notices. Obligations from other notices may not appear here.")

with st.form("profile_form"):
    col1, col2 = st.columns(2)
    with col1:
        faculty = st.text_input("Faculty (e.g., CNTT)")
        major = st.text_input("Major (e.g., Kỹ thuật phần mềm)")
    with col2:
        cohort = st.text_input("Cohort (e.g., K21)")
        program = st.text_input("Program (e.g., CLC)")
        
    submitted = st.form_submit_button("Find Relevant Obligations")
    
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
                st.info("No structured obligations found.")
            else:
                st.subheader("Upcoming / Relevant Obligations")
                
                # Separate by Applicability
                applies = [o for o in obligations if o['applicability']['status'] == "APPLIES"]
                unknown = [o for o in obligations if o['applicability']['status'] == "UNKNOWN"]
                
                for obs in applies:
                    st.success(f"**{obs['action_text']}** (Deadline: {obs['deadline'] or 'None'})")
                    st.markdown(f"*Source: {obs['title']}*")
                    st.markdown(f"Status: **{obs['temporal_status']}** | Applicability: **APPLIES**")
                    if obs.get('required_documents'):
                        st.markdown(f"Documents: {', '.join(obs['required_documents'])}")
                    st.divider()
                    
                if unknown:
                    st.subheader("May be relevant — insufficient audience information")
                    for obs in unknown:
                        st.warning(f"**{obs['action_text']}** (Deadline: {obs['deadline'] or 'None'})")
                        st.markdown(f"*Source: {obs['title']}*")
                        st.markdown(f"Status: **{obs['temporal_status']}** | Applicability: **UNKNOWN** ({obs['applicability']['explanation']})")
                        st.divider()
                        
        except Exception as e:
            st.error(f"Error fetching obligations: {e}")
