import streamlit as st
import unicodedata
from streamlit_searchbox import st_searchbox
from frontend.api_client import api_client

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
        "dut_daotao": "Phòng Đào tạo",
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

            def unaccent(text):
                nfkd_form = unicodedata.normalize('NFKD', text)
                return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

            q = unaccent(searchterm.lower()).strip()
            synonyms = {
                "diem ren luyen": ["ren luyen", "danh gia ren luyen", "ket qua ren luyen"],
                "tot nghiep": ["tot nghiep", "xet tot nghiep", "do an tot nghiep"]
            }

            query_tokens = set(q.split())
            if q in synonyms:
                for syn in synonyms[q]:
                    query_tokens.update(syn.split())

            scored_notices = []
            for n in notices:
                t = unaccent(n['title'].lower())
                c = unaccent(n['category'].lower())
                s = unaccent(n['source_display_name'].lower())
                txt = unaccent(n['searchable_text'].lower() if n.get('searchable_text') else "")

                score = 0
                match_reasons = []

                if q in t:
                    score += 100
                    match_reasons.append("Tiêu đề chứa cụm từ chính xác")
                elif any(syn in t for syn in synonyms.get(q, [])):
                    score += 80
                    match_reasons.append("Tiêu đề chứa từ đồng nghĩa")

                t_tokens = set(t.split())
                if query_tokens and query_tokens.issubset(t_tokens):
                    score += 50
                    match_reasons.append("Tiêu đề chứa tất cả từ khóa")

                if q in c:
                    score += 40
                    match_reasons.append("Khớp chuyên mục")

                title_matches = len(query_tokens.intersection(t_tokens))
                if title_matches > 0:
                    score += (title_matches * 20)
                    if not any("Tiêu đề" in r for r in match_reasons):
                        match_reasons.append(f"Tiêu đề chứa một phần từ khóa")

                txt_tokens = set(txt.split())
                txt_matches = len(query_tokens.intersection(txt_tokens))
                if txt and (q in txt or any(syn in txt for syn in synonyms.get(q, []))):
                    score += 30
                    match_reasons.append("Nội dung chứa cụm từ chính xác")
                elif txt_matches > 0:
                    score += (txt_matches * 5)
                    match_reasons.append("Nội dung chứa từ khóa")

                if score >= 40:
                    nc = n.copy()
                    nc['search_score'] = score
                    nc['match_reasons'] = list(dict.fromkeys(match_reasons))
                    scored_notices.append(nc)

            scored_notices.sort(key=lambda x: x['search_score'], reverse=True)
            results = []
            for n in scored_notices[:10]:
                reason_str = ", ".join(n['match_reasons'][:2])
                label = f"[{n['category']}] {n['title']} (Điểm: {n['search_score']} - {reason_str})"
                results.append((label, n['notice_id']))
            return results

        selected_id = st_searchbox(
            search_notices,
            key="evidence_searchbox",
            placeholder="Gõ từ khóa (vd: rèn luyện, học phí...) hoặc duyệt danh sách bên dưới"
        )

        if selected_id:
            notice_meta = next((n for n in notices if n['notice_id'] == selected_id), None)
            notice = api_client.get_notice(selected_id)

            st.markdown(f"""
            <div class="stCard">
                <div class="category-badge">{notice_meta['category']}</div>
                <h2 class="doc-title">{notice.get("title")}</h2>
                <div class="doc-meta"><b>Nguồn chính thức:</b> {notice.get("source_name")}</div>
                <div class="doc-meta"><b>Ngày ban hành:</b> {notice.get("publication_date")}</div>
                <div class="doc-meta"><b>Đường dẫn gốc:</b> <a href="{notice.get("canonical_url")}" target="_blank">Xem tại đây</a></div>
                <hr style="margin: 20px 0; border-color: #e5e7eb;">
                <h4 style="margin-top:0; color:#111827;">Nội dung thông báo</h4>
                <div class="doc-body">{notice.get("raw_text")}</div>
            </div>
            """, unsafe_allow_html=True)

            if notice_meta['has_structured_obligations']:
                st.info("✅ Thông báo này đã được UniTrust rà soát và cấu trúc. Có chứa các nghĩa vụ được hệ thống nhận diện.")
            else:
                st.warning("⚠️ Thông báo này chưa được hệ thống rà soát cấu trúc nghĩa vụ.")


            st.subheader("Lịch sử cập nhật")
            changes = api_client.get_notice_changes(selected_id)
            if not changes.get("has_history"):
                st.write("Hiện chưa lưu phiên bản lịch sử nào cho thông báo này.")
            else:
                st.success("Đã tìm thấy các phiên bản lịch sử.")

            with st.expander("Chi tiết kỹ thuật (Dành cho nhà phát triển)"):
                st.write(f"**Notice ID:** `{notice.get('notice_id')}`")
                st.write(f"**Current Version ID:** `{notice.get('current_version_id')}`")
                if changes.get("has_history"):
                    st.json(changes.get("changes", []))

    else:
        st.info("Chưa có thông báo nào trong cơ sở dữ liệu.")

except Exception as e:
    st.error(f"Lỗi khi tải bằng chứng: {e}")
