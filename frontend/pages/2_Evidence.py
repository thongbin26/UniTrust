import logging
from html import escape

import streamlit as st
from streamlit_searchbox import st_searchbox

from frontend.api_client import api_client
from frontend.evidence_search import rank_notices
from frontend.ui_style import apply_global_styles, page_header
from frontend.ui_translations import format_date_vi, get_source_name_vi


apply_global_styles()
page_header(
    "Kho thông báo chính thức",
    "Tra cứu thông báo",
    "Gõ từ khóa để tìm nhanh hoặc mở danh sách để duyệt. Kết quả được xếp hạng ổn định theo mức độ liên quan.",
)


def _html_text(value) -> str:
    return escape(str(value or "")).replace("\n", "<br>")


def get_category(title: str, text: str) -> str:
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
    if "rèn luyện" in text_lower:
        return "Rèn luyện & công tác sinh viên"
    return "Thông báo khác"


@st.cache_data(ttl=300)
def fetch_search_index() -> list[dict]:
    index = api_client.get_search_index()
    prepared = []
    for notice in index:
        item = dict(notice)
        item["category"] = item.get("category") or get_category(
            item.get("title", ""), item.get("searchable_text", "")
        )
        item["source_display_name"] = get_source_name_vi(
            item.get("source_id", ""), item.get("source_display_name", "")
        )
        prepared.append(item)
    return prepared


def suggestion_label(notice: dict) -> str:
    return f"[{notice['category']}] {notice['title']} · {notice['source_display_name']}"


try:
    notices = fetch_search_index()
    if not notices:
        st.markdown(
            '<div class="ut-empty"><strong>Chưa có thông báo để tra cứu</strong>Danh sách sẽ xuất hiện khi có dữ liệu chính thức.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="ut-section-title" style="margin-top:.5rem;">Tìm kiếm hoặc duyệt danh sách</div>', unsafe_allow_html=True)

        def search_notices(searchterm: str):
            ranked = notices if not searchterm else rank_notices(notices, searchterm)
            return [(suggestion_label(notice), notice["notice_id"]) for notice in ranked]

        selected_id = st_searchbox(
            search_notices,
            default_options=search_notices(""),
            key="evidence_searchbox",
            placeholder="Gõ: điểm rèn luyện, tốt nghiệp, học phí...",
        )

        if not selected_id:
            st.markdown(
                '<div class="ut-empty"><strong>Chọn một thông báo để xem nội dung</strong>Bạn có thể mở danh sách để duyệt hoặc gõ từ khóa; không cần nhấn Enter.</div>',
                unsafe_allow_html=True,
            )
        else:
            notice_meta = next((item for item in notices if item["notice_id"] == selected_id), None)
            if not notice_meta:
                st.warning("Không tìm thấy thông báo đã chọn. Vui lòng chọn lại.")
            else:
                with st.spinner("Đang tải nội dung thông báo..."):
                    notice = api_client.get_notice(selected_id)

                title = _html_text(notice.get("title") or "Thông báo chính thức")
                source_name = escape(notice_meta["source_display_name"])
                category = escape(notice_meta["category"])
                publication_date = escape(format_date_vi(notice.get("publication_date")))
                raw_text = _html_text(notice.get("raw_text"))
                st.markdown(
                    f"""
                    <div class="ut-card" style="margin-top:1.25rem;">
                        <span class="ut-badge ut-badge--insufficient">{category}</span>
                        <h2 style="font-size:1.55rem;line-height:1.35;margin:.9rem 0 .8rem;">{title}</h2>
                        <div class="ut-meta"><strong>Nguồn:</strong> {source_name}</div>
                        <div class="ut-meta" style="margin-top:.3rem;"><strong>Ngày ban hành:</strong> {publication_date}</div>
                        <hr class="ut-divider">
                        <h3 style="font-size:1.05rem;margin:0 0 .75rem;">Nội dung thông báo</h3>
                        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;color:#334155;line-height:1.68;max-height:420px;overflow-y:auto;padding:1rem;white-space:pre-wrap;">{raw_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                canonical_url = notice.get("canonical_url")
                if canonical_url:
                    st.link_button("Xem thông báo chính thức", canonical_url, icon=":material/open_in_new:")

                changes = api_client.get_notice_changes(selected_id)
                if changes.get("has_history"):
                    st.caption("Thông báo này có phiên bản cập nhật đã được lưu trong hệ thống.")
                else:
                    st.caption("Hiện chưa có phiên bản lịch sử được lưu cho thông báo này.")
except Exception:
    logging.getLogger(__name__).exception("Evidence browser failed")
    st.error("Không thể tải thông báo lúc này. Vui lòng thử lại.")
