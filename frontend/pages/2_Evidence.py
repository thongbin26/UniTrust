import logging
from html import escape

import streamlit as st
from streamlit_searchbox import st_searchbox

from frontend.api_client import api_client
from frontend.evidence_search import rank_notices
from frontend.ui_style import apply_global_styles, page_header, page_marker
from frontend.ui_translations import format_date_vi, get_notice_title_vi, get_source_name_vi


apply_global_styles()
page_marker("evidence")
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
    return f"[{notice['category']}] {get_notice_title_vi(notice['title'])} · {notice['source_display_name']}"


def render_browse_state(notices: list[dict]) -> None:
    """Show real index metadata without loading full notice details."""
    rows = []
    for notice in notices[:6]:
        rows.append(
            '<div class="ut-notice-item">'
            f'<div class="ut-section-kicker">{escape(notice["category"])}</div>'
            f'<strong style="display:block;line-height:1.45;">{escape(get_notice_title_vi(notice["title"]))}</strong>'
            f'<div class="ut-meta" style="margin-top:.25rem;">{escape(notice["source_display_name"])}</div>'
            '</div>'
        )
    st.markdown(
        '<div class="ut-section-title">Thông báo gần đây</div>'
        '<div class="ut-card-flat">'
        f'{"".join(rows)}'
        '</div>'
        '<div class="ut-helper" style="margin-top:.65rem;"><span class="ut-helper-mark" aria-hidden="true">i</span>'
        '<span>Mở ô tìm kiếm để duyệt toàn bộ danh sách hoặc gõ từ khóa để lọc ngay.</span></div>',
        unsafe_allow_html=True,
    )


try:
    notices = fetch_search_index()
    if not notices:
        st.markdown(
            '<div class="ut-empty"><strong>Chưa có thông báo để tra cứu</strong>Danh sách sẽ xuất hiện khi có dữ liệu chính thức.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="ut-section-title" style="margin-top:.35rem;">Tìm kiếm hoặc duyệt thông báo</div>', unsafe_allow_html=True)

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
            render_browse_state(notices)
        else:
            notice_meta = next((item for item in notices if item["notice_id"] == selected_id), None)
            if not notice_meta:
                st.warning("Không tìm thấy thông báo đã chọn. Vui lòng chọn lại.")
            else:
                with st.spinner("Đang tải nội dung thông báo..."):
                    notice = api_client.get_notice(selected_id)

                title = _html_text(get_notice_title_vi(notice.get("title")) or "Thông báo chính thức")
                source_name = escape(notice_meta["source_display_name"])
                category = escape(notice_meta["category"])
                publication_date = escape(format_date_vi(notice.get("publication_date")))
                raw_text = str(notice.get("raw_text") or "")
                st.markdown(
                    f"""
                    <div style="margin-top:1.5rem;">
                        <div class="ut-section-kicker">{category}</div>
                        <h2 style="font-size:1.65rem;line-height:1.35;margin:.3rem 0 .75rem;max-width:760px;">{title}</h2>
                        <div class="ut-meta"><strong>Nguồn:</strong> {source_name}</div>
                        <div class="ut-meta" style="margin-top:.25rem;"><strong>Ngày ban hành:</strong> {publication_date}</div>
                        <hr class="ut-divider" style="margin:1.2rem 0;">
                        <h3 style="font-size:1.08rem;margin:0 0 .7rem;">Nội dung thông báo</h3>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.container(border=True):
                    st.markdown(raw_text, unsafe_allow_html=False)
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
