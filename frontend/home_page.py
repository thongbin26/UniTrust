import httpx
import streamlit as st
from frontend.ui_style import apply_global_styles



apply_global_styles()

st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; margin-top: 2rem;">
    <div style="flex: 1; padding-right: 2rem;">
        <h1 class="hero-title" style="margin-top: 0; color: #1e3a8a;">UniTrust</h1>
        <p class="hero-tagline" style="font-size: 1.25rem; font-weight: 500; color: #3b82f6;">Kiểm chứng đúng nguồn, an tâm hành động.</p>
        <p class="hero-pitch" style="color: #4b5563; line-height: 1.6; margin-bottom: 2rem;">
            UniTrust giúp sinh viên tra cứu và xác minh thông tin dựa trên các thông báo,
            quy định chính thức của nhà trường. Không còn lo lắng về tin giả hay thông báo hết hạn.
        </p>
    </div>
    <div style="flex: 1; text-align: center;">
        <!-- Simple inline SVG for hero graphic -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="auto">
            <rect width="400" height="300" fill="#f8fafc" rx="16"/>
            <rect x="50" y="80" width="120" height="80" fill="#eff6ff" rx="8" stroke="#bfdbfe" stroke-width="2"/>
            <path d="M70 110 h80 M70 130 h50" stroke="#3b82f6" stroke-width="4" stroke-linecap="round"/>
            <circle cx="200" cy="120" r="30" fill="#ffffff" stroke="#2563eb" stroke-width="4"/>
            <path d="M190 120 l8 8 l15 -15" fill="none" stroke="#2563eb" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
            <rect x="230" y="140" width="120" height="80" fill="#ecfdf5" rx="8" stroke="#a7f3d0" stroke-width="2"/>
            <path d="M250 170 h80 M250 190 h50" stroke="#10b981" stroke-width="4" stroke-linecap="round"/>
            <path d="M130 180 Q165 220 200 170 T270 120" fill="none" stroke="#94a3b8" stroke-width="3" stroke-dasharray="6,6"/>
        </svg>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="stCard">
        <h3 style="color: #0f172a; display: flex; align-items: center; gap: 8px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            Xác minh
        </h3>
        <p style="color: #4b5563;">Kiểm tra chéo nội dung tin nhắn với bằng chứng chính thức.</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="stCard">
        <h3 style="color: #0f172a; display: flex; align-items: center; gap: 8px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            Tra cứu
        </h3>
        <p style="color: #4b5563;">Tìm kiếm hoặc duyệt danh sách các thông báo nhà trường.</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="stCard">
        <h3 style="color: #0f172a; display: flex; align-items: center; gap: 8px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            Dành cho bạn
        </h3>
        <p style="color: #4b5563;">Xem các nghĩa vụ và yêu cầu cá nhân hóa theo hồ sơ.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("Về UniTrust"):
    st.markdown("""
    **Dữ liệu hiện có**
    - 3 Nguồn thông báo chính thức
    - 30 Thông báo đã thu thập
    - 18 Nghĩa vụ đã cấu trúc

    **Chi tiết kỹ thuật**
    - Tỷ lệ truy xuất đúng ở kết quả đầu tiên: 94.83% (N=58 mẫu từ nguồn thực tế) - [Hybrid Hit@1]
    - Độ chính xác xác minh có kiểm soát: 78.00% (N=50 mẫu biến đổi nhân tạo)
    - Độ chính xác trên dữ liệu rà soát thủ công: 66.67% (N=18)
    """)
