import streamlit as st
from pathlib import Path

from frontend.ui_style import apply_global_styles, page_marker


apply_global_styles()
page_marker("home")
asset_dir = Path(__file__).resolve().parent / "assets"

hero_copy, hero_visual = st.columns([1.06, 0.94], gap="large", vertical_alignment="center")
with hero_copy:
    st.markdown(
        """
        <div class="ut-hero">
            <div class="ut-eyebrow">Cổng thông tin dành cho sinh viên DUT</div>
            <h1 class="ut-hero-title">UniTrust</h1>
            <p class="ut-hero-slogan">Kiểm chứng đúng nguồn, an tâm hành động.</p>
            <p class="ut-page-description">
                Đối chiếu điều bạn nhận được với nguồn chính thức, tìm thông báo hiện hành
                và nhận biết những việc có thể liên quan đến hồ sơ của mình.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Xác minh thông tin", type="primary", icon=":material/verified_user:", width="content"):
        st.switch_page("pages/1_Verify.py")
    st.page_link("pages/2_Evidence.py", label="Tra cứu thông báo chính thức", icon=":material/search:", width="content")

with hero_visual:
    with st.container(border=True):
        st.image(str(asset_dir / "evidence-flow.svg"), width="stretch")

st.markdown('<div class="ut-section-title" style="margin-top:2.4rem;">Ba cách UniTrust hỗ trợ bạn</div>', unsafe_allow_html=True)
value_columns = st.columns(3, gap="medium")
values = [
    ("pages/1_Verify.py", ":material/verified_user:", "Kiểm chứng", "Dán văn bản, tải ảnh hoặc gửi đường link để đối chiếu với nguồn chính thức."),
    ("pages/2_Evidence.py", ":material/search:", "Tra cứu", "Tìm thông báo, đọc nguồn gốc và biết nội dung nào đang hiện hành."),
    ("pages/3_For_You.py", ":material/person:", "Dành cho bạn", "Xem những việc có thể liên quan đến hồ sơ sinh viên của bạn."),
]
for column, (path, icon, title, description) in zip(value_columns, values):
    with column:
        st.markdown(
            f'<div class="ut-action-tile"><p>{description}</p></div>',
            unsafe_allow_html=True,
        )
        st.page_link(path, label=f"{title}  →", icon=icon, width="stretch")

st.markdown(
    """
    <div class="ut-principle">
        <div class="ut-principle-mark">✓</div>
        <div><strong>Kết luận có căn cứ, giữ nguyên phần chưa chắc chắn.</strong><div class="ut-meta" style="margin-top:.22rem;">UniTrust cho biết khi nào thông tin đã được xác minh, có mâu thuẫn hoặc chưa đủ bằng chứng để kết luận.</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
