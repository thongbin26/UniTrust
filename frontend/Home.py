import streamlit as st
import os
from frontend.profile_state import load_catalog, sync_profile_state
from frontend.ui_style import apply_global_styles

st.set_page_config(
    page_title="UniTrust",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()
st.sidebar.markdown(
    """
    <div class="ut-sidebar-brand">
        <div class="ut-sidebar-name">UniTrust</div>
        <div class="ut-sidebar-tagline">Kiểm chứng đúng nguồn,<br>an tâm hành động.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

base_dir = os.path.dirname(__file__)

# Navigation clears query parameters; keep the saved profile restorable on every page.
sync_profile_state(st.session_state, st.query_params, load_catalog())

pg = st.navigation([
    st.Page(os.path.join(base_dir, "home_page.py"), title="Trang chủ", icon=":material/home:"),
    st.Page(os.path.join(base_dir, "pages", "1_Verify.py"), title="Xác minh", icon=":material/verified_user:"),
    st.Page(os.path.join(base_dir, "pages", "2_Evidence.py"), title="Tra cứu thông báo", icon=":material/search:"),
    st.Page(os.path.join(base_dir, "pages", "3_For_You.py"), title="Dành cho bạn", icon=":material/person:")
])

pg.run()
