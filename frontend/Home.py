import streamlit as st
import os
from pathlib import Path

from frontend.profile_state import load_catalog, sync_profile_state
from frontend.ui_style import apply_global_styles

st.set_page_config(
    page_title="UniTrust",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()
asset_dir = Path(__file__).resolve().parent / "assets"
with st.sidebar.container():
    mark_column, name_column = st.columns([0.2, 0.8], gap="small", vertical_alignment="center")
    with mark_column:
        st.image(str(asset_dir / "unitrust-mark.svg"), width=38)
    with name_column:
        st.markdown(
            """
            <div class="ut-sidebar-brand">
                <div class="ut-sidebar-name">UniTrust</div>
                <div class="ut-sidebar-tagline">Thông tin đáng tin cậy cho sinh viên DUT</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

base_dir = os.path.dirname(__file__)

pages = [
    st.Page(os.path.join(base_dir, "home_page.py"), title="Trang chủ", icon=":material/home:"),
    st.Page(os.path.join(base_dir, "pages", "1_Verify.py"), title="Xác minh", icon=":material/verified_user:"),
    st.Page(os.path.join(base_dir, "pages", "2_Evidence.py"), title="Tra cứu thông báo", icon=":material/search:"),
    st.Page(os.path.join(base_dir, "pages", "3_For_You.py"), title="Dành cho bạn", icon=":material/person:"),
]

with st.sidebar.container():
    st.page_link(pages[0], label="Trang chủ", icon=":material/home:", use_container_width=True)
    st.page_link(pages[1], label="Xác minh", icon=":material/verified_user:", use_container_width=True)
    st.page_link(pages[2], label="Tra cứu thông báo", icon=":material/search:", use_container_width=True)
    st.page_link(pages[3], label="Dành cho bạn", icon=":material/person:", use_container_width=True)

# Navigation clears query parameters; keep the saved profile restorable on every page.
sync_profile_state(st.session_state, st.query_params, load_catalog())

pg = st.navigation(pages, position="hidden")

pg.run()
