import streamlit as st
import os
from frontend.profile_state import load_catalog, sync_profile_state

st.set_page_config(
    page_title="UniTrust",
    page_icon="🎓",
    layout="wide",
)

base_dir = os.path.dirname(__file__)

# Navigation clears query parameters; keep the saved profile restorable on every page.
sync_profile_state(st.session_state, st.query_params, load_catalog())

pg = st.navigation([
    st.Page(os.path.join(base_dir, "home_page.py"), title="Trang chủ", icon="🏠"),
    st.Page(os.path.join(base_dir, "pages", "1_Verify.py"), title="Xác minh", icon="🛡️"),
    st.Page(os.path.join(base_dir, "pages", "2_Evidence.py"), title="Tra cứu thông báo", icon="📄"),
    st.Page(os.path.join(base_dir, "pages", "3_For_You.py"), title="Dành cho bạn", icon="👤")
])

pg.run()
