import streamlit as st

from frontend.ui_style import apply_global_styles


apply_global_styles()

hero_copy, hero_visual = st.columns([1.12, 0.88], gap="large", vertical_alignment="center")
with hero_copy:
    st.markdown(
        """
        <div class="ut-eyebrow">Thông tin đáng tin cậy cho sinh viên DUT</div>
        <h1 class="ut-page-title" style="font-size:clamp(2.8rem,6vw,4.8rem);margin-bottom:.7rem;">UniTrust</h1>
        <p style="color:#2563eb;font-size:1.28rem;font-weight:720;margin:0 0 1rem;">
            Kiểm chứng đúng nguồn, an tâm hành động.
        </p>
        <p class="ut-page-description" style="font-size:1.08rem;max-width:650px;">
            Đối chiếu thông tin bạn nhận được với thông báo chính thức, tìm nội dung hiện hành
            và nhận biết những việc có thể liên quan đến hồ sơ của mình.
        </p>
        """,
        unsafe_allow_html=True,
    )
    verify_cta, evidence_cta = st.columns(2)
    with verify_cta:
        if st.button("Xác minh thông tin", type="primary", icon=":material/verified_user:", use_container_width=True):
            st.switch_page("pages/1_Verify.py")
    with evidence_cta:
        st.page_link("pages/2_Evidence.py", label="Tra cứu thông báo", icon=":material/search:", use_container_width=True)

with hero_visual:
    st.markdown(
        """
        <div class="ut-card" style="padding:1rem;background:linear-gradient(145deg,#ffffff,#f2f7ff);">
            <svg aria-label="Luồng kiểm chứng thông tin" viewBox="0 0 520 330" width="100%" role="img">
                <defs><linearGradient id="shield" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#3b82f6"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient></defs>
                <rect x="24" y="58" width="148" height="98" rx="18" fill="#fff" stroke="#dbe4f0"/>
                <circle cx="51" cy="87" r="10" fill="#dbeafe"/><rect x="70" y="79" width="73" height="9" rx="4" fill="#94a3b8"/>
                <rect x="45" y="108" width="100" height="8" rx="4" fill="#cbd5e1"/><rect x="45" y="128" width="72" height="8" rx="4" fill="#dbe4f0"/>
                <path d="M175 108 C210 108 218 150 237 150" fill="none" stroke="#9ab5df" stroke-width="3" stroke-dasharray="7 7"/>
                <path d="M260 74 L325 99 V150 C325 203 288 232 260 245 C232 232 195 203 195 150 V99 Z" fill="url(#shield)"/>
                <path d="M231 155 L251 175 L292 130" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M326 169 C357 169 363 210 383 210" fill="none" stroke="#9ab5df" stroke-width="3" stroke-dasharray="7 7"/>
                <rect x="354" y="177" width="142" height="102" rx="18" fill="#fff" stroke="#bdebdc"/>
                <rect x="378" y="201" width="95" height="10" rx="5" fill="#5bbba4"/><rect x="378" y="226" width="82" height="8" rx="4" fill="#b7dacf"/><rect x="378" y="246" width="60" height="8" rx="4" fill="#d4ebe4"/>
                <text x="98" y="190" fill="#64748b" font-size="14" text-anchor="middle">Thông tin nhận được</text>
                <text x="260" y="283" fill="#1d4ed8" font-size="15" font-weight="700" text-anchor="middle">UniTrust đối chiếu</text>
                <text x="425" y="309" fill="#0f766e" font-size="14" text-anchor="middle">Nguồn chính thức</text>
            </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="ut-section-title">Ba cách UniTrust hỗ trợ bạn</div>', unsafe_allow_html=True)
value_columns = st.columns(3, gap="medium")
values = [
    ("01", "Xác minh", "Đối chiếu nội dung tin nhắn hoặc bài đăng với bằng chứng chính thức."),
    ("02", "Tra cứu", "Tìm nhanh thông báo cần thiết và đọc nội dung từ đúng nguồn."),
    ("03", "Dành cho bạn", "Nhận biết nghĩa vụ có thể áp dụng dựa trên hồ sơ đã khai báo."),
]
for column, (number, title, description) in zip(value_columns, values):
    with column:
        st.markdown(
            f'<div class="ut-card-flat" style="min-height:170px;"><div class="ut-eyebrow" style="margin-bottom:1rem;">{number}</div><h3 style="font-size:1.2rem;margin:0 0 .55rem;">{title}</h3><p style="color:#526176;margin:0;">{description}</p></div>',
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <div class="ut-card" style="margin-top:2rem;display:flex;gap:1rem;align-items:flex-start;box-shadow:none;background:#eff6ff;border-color:#cfe0ff;">
        <div style="color:#1d4ed8;font-size:1.35rem;font-weight:800;line-height:1;">✓</div>
        <div><strong style="color:#0f172a;">Kết luận có căn cứ, giữ nguyên phần chưa chắc chắn.</strong><div style="color:#526176;margin-top:.25rem;">UniTrust cho biết khi nào thông tin đã được xác minh, có mâu thuẫn hoặc chưa đủ bằng chứng để kết luận.</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
