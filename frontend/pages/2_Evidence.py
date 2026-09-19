import streamlit as st
import logging
from html import escape
from streamlit_searchbox import st_searchbox
from frontend.api_client import api_client
from frontend.evidence_search import rank_notices

st.markdown("""
<style>
    .stCard {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }
    .doc-meta {
        font-size: 0.95rem;
        color: #4b5563;
        margin-bottom: 8px;
    }
    .doc-title {
        color: #111827;
        font-weight: 700;
        font-size: 1.5rem;
        margin-top: 0;
        margin-bottom: 16px;
    }
    .doc-body {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        font-family: monospace;
        font-size: 0.9rem;
        white-space: pre-wrap;
        color: #374151;
        max-height: 400px;
        overflow-y: auto;
    }
    .category-badge {
        display: inline-block;
        padding: 2px 8px;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 4px;
        background-color: #e0f2fe;
        color: #0369a1;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📄 Tra cứu thông báo")
st.markdown("Tìm nhanh hoặc duyệt toàn bộ các thông báo chính thức từ nhà trường.")

def get_category(title, text):
    title_lower = title.lower()
    text_lower = text.lower()

    if any(k in title_lower for k in ["học vụ", "đăng ký học", "thời khóa biểu", "lịch học", "nghỉ học"]):
        return "Học vụ"
    if any(k in title_lower for k in ["thi cử", "điểm", "lịch thi", "phúc khảo"]):
        return "Thi cử & điểm"
    if any(k in title_lower for k in ["tốt nghiệp", "chuẩn đầu ra", "xét công nhận"]):
        return "Tốt nghiệp"
    if any(k in title_lower for k in ["học phí", "bảo hiểm", "nộp tiền", "miễn giảm"]):
        return "Học phí & hỗ trợ"
    if any(k in title_lower for k in ["rèn luyện", "công tác sinh viên", "ngoại khóa", "sinh hoạt lớp", "ảnh thẻ", "khám sức khỏe"]):
        return "Rèn luyện & công tác sinh viên"
    if any(k in title_lower for k in ["tiếng anh", "ngoại ngữ", "toeic", "aptis"]):
        return "Ngoại ngữ"
    if any(k in title_lower for k in ["học bổng", "tuyển dụng", "cơ hội", "cuộc thi"]):
        return "Học bổng & cơ hội"
    if any(k in title_lower for k in ["khảo sát", "biểu mẫu", "đánh giá"]):
        return "Khảo sát & biểu mẫu"
    return "Thông báo khác"

@st.cache_data(ttl=300)
def fetch_search_index():
    source_map = {
        "dut_academic": "Phòng Đào tạo",
        "dut_ctsv": "Phòng Công tác sinh viên",
        "dut_it_faculty": "Khoa Công nghệ thông tin"
    }
    # Fix category during fetch to ensure we have it for display
    idx = api_client.get_search_index()
    for n in idx:
        if 'category' not in n or not n['category']:
            n['category'] = get_category(n.get('title', ''), n.get('searchable_text', ''))
        # Map source display name
        s_id = n.get('source_id')
        if s_id in source_map:
            n['source_display_name'] = source_map[s_id]
        elif 'Academic' in str(n.get('source_display_name')):
            n['source_display_name'] = "Phòng Đào tạo"
    return idx

try:
    notices = fetch_search_index()

    if notices:
        st.markdown("### Tìm kiếm và duyệt thông báo")

        def search_notices(searchterm: str):
            if not notices:
                return []

            if not searchterm:
                return [(f"[{n['category']}] {n['title']} - Nguồn: {n['source_display_name']}", n['notice_id']) for n in notices]

            results = []
            for n in rank_notices(notices, searchterm):
                reason_str = ", ".join(n['match_reasons'][:2])
                label = f"[{n['category']}] {n['title']} (Điểm: {n['search_score']} - {reason_str})"
                results.append((label, n['notice_id']))
            return results

        selected_id = st_searchbox(
            search_notices,
            default_options=search_notices(""),
            key="evidence_searchbox",
            placeholder="Gõ từ khóa (vd: rèn luyện, học phí...) hoặc duyệt danh sách bên dưới"
        )

        if selected_id:
            notice_meta = next((n for n in notices if n['notice_id'] == selected_id), None)
            notice = api_client.get_notice(selected_id)

            st.markdown(f"""
            <div class="stCard">
                <div class="category-badge">{notice_meta['category']}</div>
                <h2 class="doc-title">{escape(notice["title"])}</h2>
                <div class="doc-meta"><b>Nguồn chính thức:</b> {escape(notice_meta["source_display_name"])}</div>
                <div class="doc-meta"><b>Ngày ban hành:</b> {escape(notice["publication_date"] or "Chưa rõ")}</div>
                <div class="doc-meta"><b>Đường dẫn gốc:</b> <a href="{escape(notice["canonical_url"])}" target="_blank">Xem tại đây</a></div>
                <hr style="margin: 20px 0; border-color: #e5e7eb;">
                <h4 style="margin-top:0; color:#111827;">Nội dung thông báo</h4>
                <div class="doc-body">{escape(notice["raw_text"] or "")}</div>
            </div>
            """, unsafe_allow_html=True)

            st.subheader("Lịch sử cập nhật")
            changes = api_client.get_notice_changes(selected_id)
            if not changes.get("has_history"):
                st.write("Hiện chưa lưu phiên bản lịch sử nào cho thông báo này.")
            else:
                st.success("Đã tìm thấy các phiên bản lịch sử.")

    else:
        st.info("Chưa có thông báo nào trong cơ sở dữ liệu.")

except Exception:
    logging.getLogger(__name__).exception("Evidence browser failed")
    st.error("Không thể tải thông báo lúc này. Vui lòng thử lại.")
