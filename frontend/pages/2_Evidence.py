import streamlit as st
from frontend.api_client import api_client

st.set_page_config(page_title="Evidence", page_icon="📄", layout="wide")
st.title("📄 Official Evidence Browser")
st.markdown("Browse and trace the raw official notices indexed by UniTrust.")

try:
    notices = api_client.list_notices()
    
    if notices:
        options = {n['notice_id']: f"{n['title']} (ID: {n['notice_id']}) - {n['source_name']}" for n in notices}
        selected_id = st.selectbox("Select Notice", options=list(options.keys()), format_func=lambda x: options[x])
        
        if selected_id:
            notice_meta = next((n for n in notices if n['notice_id'] == selected_id), None)
            
            st.divider()
            
            notice = api_client.get_notice(selected_id)
            
            st.subheader(notice.get("title"))
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Source:** {notice.get('source_name')}")
                st.markdown(f"**URL:** [View Original]({notice.get('canonical_url')})")
            with col2:
                st.markdown(f"**Publication Date:** {notice.get('publication_date')}")
                st.markdown(f"**Current Version ID:** {notice.get('current_version_id')}")
                
            st.markdown(f"**Structured Semantic Coverage:** {notice_meta['structured_coverage']}")
            if not notice_meta['has_structured_obligations']:
                st.warning("This notice has not yet been processed for structured human-reviewed coverage. Verification over this document may abstain.")
                
            with st.expander("Raw Official Text", expanded=True):
                st.text(notice.get("raw_text"))
                
            st.divider()
            st.subheader("What Changed (Version History)")
            
            changes = api_client.get_notice_changes(selected_id)
            if not changes.get("has_history"):
                st.info("No historical version is currently stored for this notice.")
            else:
                st.success("Historical versions found.")
                st.json(changes.get("changes", []))
    else:
        st.info("No notices available in the database.")
        
except Exception as e:
    st.error(f"Error loading evidence: {e}")
