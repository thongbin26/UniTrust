import streamlit as st
import unicodedata
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

try:
    notices = api_client.list_notices()
    
    if notices:
        # Pre-process notices with text and categories
        for n in notices:
            full_n = api_client.get_notice(n['notice_id'])
            n['raw_text'] = full_n.get('raw_text', '')
            n['category'] = get_category(n['title'], n['raw_text'])
            
        search_query = st.text_input("Tìm nhanh", placeholder="Tìm kiếm: điểm rèn luyện, học phí, tốt nghiệp, tiếng Anh...")
        
        filtered_notices = notices
        
        def unaccent(text):
            nfkd_form = unicodedata.normalize('NFKD', text)
            return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
            
        if search_query:
            q = unaccent(search_query.lower()).strip()
            
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
                s = unaccent(n['source_name'].lower())
                txt = unaccent(n['raw_text'].lower())
                
                score = 0
                match_reasons = []
                
                # 1. exact phrase in title -> highest weight
                if q in t:
                    score += 100
                    match_reasons.append("Tiêu đề chứa cụm từ chính xác")
                elif any(syn in t for syn in synonyms.get(q, [])):
                    score += 80
                    match_reasons.append("Tiêu đề chứa từ đồng nghĩa")
                
                # 2. all query tokens in title -> high weight
                t_tokens = set(t.split())
                if query_tokens and query_tokens.issubset(t_tokens):
                    score += 50
                    match_reasons.append("Tiêu đề chứa tất cả từ khóa")
                
                # 3. category match -> high weight
                if q in c:
                    score += 40
                    match_reasons.append("Khớp chuyên mục")
                
                # 4. partial title token match -> medium weight
                title_matches = len(query_tokens.intersection(t_tokens))
                if title_matches > 0:
                    score += (title_matches * 20)
                    if not any("Tiêu đề" in r for r in match_reasons):
                        match_reasons.append(f"Tiêu đề chứa một phần từ khóa")
                
                # 5. relevant tokens in raw_text -> lower weight
                txt_tokens = set(txt.split())
                txt_matches = len(query_tokens.intersection(txt_tokens))
                if q in txt or any(syn in txt for syn in synonyms.get(q, [])):
                    score += 30
                    match_reasons.append("Nội dung chứa cụm từ chính xác")
                elif txt_matches > 0:
                    score += (txt_matches * 5)
                    match_reasons.append("Nội dung chứa từ khóa")
                
                # 6. source-name match -> lowest weight
                if q in s:
                    score += 2
                    match_reasons.append("Khớp nguồn ban hành")
                
                if score >= 40:
                    n['search_score'] = score
                    n['match_reasons'] = list(dict.fromkeys(match_reasons)) # remove duplicates
                    scored_notices.append(n)
            
            scored_notices.sort(key=lambda x: x['search_score'], reverse=True)
            filtered_notices = scored_notices[:8] # Limit to top 8
        
        selected_id = None
        
        if search_query:
            if not filtered_notices:
                st.info("Không tìm thấy kết quả nào phù hợp.")
            else:
                st.markdown(f"**Kết quả tìm kiếm ({len(filtered_notices)}):**")
                
                options = {}
                for n in filtered_notices:
                    reason_str = ", ".join(n['match_reasons'][:2])
                    options[n['notice_id']] = f"[{n['category']}] {n['title']} (Điểm: {n['search_score']} - {reason_str})"
                    
                selected_id = st.selectbox("Chọn kết quả để xem chi tiết", options=list(options.keys()), format_func=lambda x: options[x], key="search_select")
        else:
            with st.expander("Duyệt toàn bộ thông báo", expanded=True):
                options = {n['notice_id']: f"[{n['category']}] {n['title']}" for n in notices}
                selected_id = st.selectbox("Chọn Thông báo", options=list(options.keys()), format_func=lambda x: options[x], key="manual_select")
        
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
                st.write(f"**Structured Semantic Coverage:** `{notice_meta['structured_coverage']}`")
                if changes.get("has_history"):
                    st.json(changes.get("changes", []))
                
    else:
        st.info("Chưa có thông báo nào trong cơ sở dữ liệu.")
        
except Exception as e:
    st.error(f"Lỗi khi tải bằng chứng: {e}")
