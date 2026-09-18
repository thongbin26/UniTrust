import streamlit as st
import os

st.set_page_config(
    page_title="UniTrust",
    page_icon="🎓",
    layout="wide",
)

base_dir = os.path.dirname(__file__)

pg = st.navigation([
    st.Page(os.path.join(base_dir, "home_page.py"), title="Trang chủ", icon="🏠"),
    st.Page(os.path.join(base_dir, "pages", "1_Verify.py"), title="Xác minh", icon="🛡️"),
    st.Page(os.path.join(base_dir, "pages", "2_Evidence.py"), title="Tra cứu thông báo", icon="📄"),
    st.Page(os.path.join(base_dir, "pages", "3_For_You.py"), title="Dành cho bạn", icon="👤")
])

pg.run()