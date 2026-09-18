import httpx
import streamlit as st
from frontend.ui_style import apply_global_styles



apply_global_styles()

st.markdown('<h1 class="hero-title" style="text-align: center; margin-top: 2rem;">🎓 UniTrust</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-tagline" style="text-align: center;">Kiểm chứng đúng nguồn, an tâm hành động.</p>', unsafe_allow_html=True)

st.markdown(
    '<p class="hero-pitch" style="text-align: center; margin: 0 auto 3rem auto;">UniTrust giúp sinh viên kiểm tra thông tin được chuyển tiếp bằng cách đối chiếu với các thông báo chính thức của nhà trường.</p>', 
    unsafe_allow_html=True
)

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="stCard">
        <h3>🛡️ Xác minh thông tin</h3>
        <p>Kiểm tra chéo nội dung tin nhắn với bằng chứng chính thức để xem có chính xác và còn hiệu lực không.</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="stCard">
        <h3>📄 Tra cứu thông báo</h3>
        <p>Tìm kiếm nhanh hoặc xem danh sách đầy đủ các thông báo chính thức từ nhà trường.</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="stCard">
        <h3>👤 Dành cho bạn</h3>
        <p>Lưu hồ sơ cá nhân để xem các nghĩa vụ và yêu cầu cụ thể áp dụng riêng cho bạn.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

st.markdown("### 📊 Dữ liệu hiện có")
st.markdown("""
<div class="stCard" style="background-color: #eff6ff; border-color: #bfdbfe;">
    <ul style="color: #1e3a8a; line-height: 1.8; margin-bottom: 0;">
        <li><b>3</b> Nguồn thông báo chính thức</li>
        <li><b>30</b> Thông báo đã thu thập</li>
        <li><b>10</b> Thông báo đã rà soát</li>
        <li><b>18</b> Nghĩa vụ đã cấu trúc</li>
    </ul>
</div>
""", unsafe_allow_html=True)

with st.expander("Kết quả đánh giá hệ thống (Chi tiết kỹ thuật)"):
    st.markdown("""
    <ul style="color: #4b5563; line-height: 1.8;">
        <li><b>Tỷ lệ truy xuất đúng ở kết quả đầu tiên:</b> 94.83% (N=58 mẫu từ nguồn thực tế) - [Hybrid Hit@1]</li>
        <li><b>Độ chính xác xác minh có kiểm soát:</b> 78.00% (N=50 mẫu biến đổi nhân tạo)</li>
        <li><b>Độ chính xác trên dữ liệu rà soát thủ công:</b> 66.67% (N=18)</li>
    </ul>
    """, unsafe_allow_html=True)

st.markdown("---")

st.subheader("Trạng thái kết nối")

backend_url = st.text_input(
    "Địa chỉ máy chủ (Backend URL)",
    value="http://127.0.0.1:8000",
)

if st.button("Kiểm tra kết nối"):
    try:
        response = httpx.get(
            f"{backend_url}/health",
            timeout=3.0,
        )
        response.raise_for_status()

        data = response.json()

        if data.get("status") == "ok":
            st.success("Hệ thống UniTrust đang hoạt động ổn định.")
        else:
            st.warning("Hệ thống có phản hồi nhưng báo cáo tình trạng chưa tối ưu.")

    except Exception as exc:
        st.error(
            "Không thể kết nối đến máy chủ UniTrust. Vui lòng đảm bảo hệ thống đã được khởi động."
        )
