import streamlit as st
from frontend.api_client import api_client
from frontend.ui_translations import (
    get_trust_state_vi,
    get_temporal_state_vi,
    get_abstention_reason_vi,
    get_explanation_vi,
    get_field_name_vi
)

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
    .result-card {
        background-color: #f8fafc;
        border-left: 6px solid #3b82f6;
    }
    .result-verified { border-left-color: #10b981; }
    .result-conflict { border-left-color: #ef4444; }
    .result-partial { border-left-color: #f59e0b; }
    .result-insufficient { border-left-color: #6b7280; }
    
    .field-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .field-header {
        font-weight: 600;
        color: #374151;
        margin-bottom: 4px;
    }
    .evidence-card {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 16px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Xác minh thông tin")
st.markdown("Dán hoặc nhập thông tin được chuyển tiếp vào bên dưới để xác minh chéo với các bằng chứng chính thức từ nhà trường.")

with st.expander("ℹ️ Giới hạn dữ liệu hiện tại"):
    st.info("Hệ thống UniTrust hiện đang tập trung xử lý dữ liệu cấu trúc đã được rà soát cho một số thông báo chọn lọc của ĐHBK. Việc xác minh các thông tin nằm ngoài phạm vi này có thể trả về kết quả 'Chưa đủ bằng chứng'.")

text_input = st.text_area("Nội dung cần xác minh", height=150, placeholder="Nhập hoặc dán nội dung thông báo tại đây...")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Xác minh thông tin", type="primary", use_container_width=True):
    if not text_input.strip():
        st.error("Vui lòng nhập nội dung cần xác minh.")
    else:
        with st.spinner("Đang xác minh dữ liệu với hệ thống chính thức..."):
            try:
                # hardcode top_k=5, use_llm=False to simplify UI and focus on claim
                result = api_client.verify_claim(text_input, use_llm=False, top_k=5)
                
                for claim_res in result.get('results', []):
                    verdict = claim_res['verdict']
                    temp = claim_res['temporal_status']
                    
                    trust_vi = get_trust_state_vi(verdict)
                    temp_vi = get_temporal_state_vi(temp)
                    explanation = get_explanation_vi(verdict)
                    
                    card_class = "result-card "
                    icon = "✅"
                    if verdict == "VERIFIED":
                        card_class += "result-verified"
                    elif verdict == "CONFLICT":
                        card_class += "result-conflict"
                        icon = "❌"
                    elif verdict == "PARTIALLY_VERIFIED":
                        card_class += "result-partial"
                        icon = "⚠️"
                    else:
                        card_class += "result-insufficient"
                        icon = "❔"
                    
                    st.markdown(f"""
                    <div class="stCard {card_class}">
                        <h2 style="margin-top:0;">KẾT QUẢ XÁC MINH</h2>
                        <div style="margin-bottom: 16px;">
                            <div style="font-size: 1.1rem; margin-bottom: 8px;"><b>Trạng thái:</b> {icon} {trust_vi}</div>
                            <div style="font-size: 1.1rem;"><b>Tình trạng phiên bản:</b> 🕒 {temp_vi}</div>
                        </div>
                        <hr style="margin: 16px 0; border-color: #e5e7eb;">
                        <h4 style="margin-top:0;">Vì sao UniTrust kết luận như vậy?</h4>
                        <p>{explanation}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if verdict == "INSUFFICIENT_EVIDENCE":
                        reason = claim_res.get('abstention_reason')
                        reason_vi = get_abstention_reason_vi(reason)
                        st.info(f"**Lý do:** {reason_vi}")

                    if claim_res.get('field_results'):
                        st.markdown("### So sánh chi tiết")
                        for k, v in claim_res['field_results'].items():
                            f_state_vi = get_trust_state_vi(v['state'])
                            f_name_vi = get_field_name_vi(k)
                            st.markdown(f"""
                            <div class="field-card">
                                <div class="field-header">Trường dữ liệu: {f_name_vi}</div>
                                <div style="color: #4b5563;"><b>Kết quả:</b> {f_state_vi}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown("### Nguồn bằng chứng chính thức")
                    prov = claim_res.get('primary_provenance')
                    if prov:
                        st.markdown(f"""
                        <div class="evidence-card">
                            <h4 style="margin-top: 0; color: #166534;">{prov.get('title')}</h4>
                            <p style="margin-bottom: 8px;"><b>URL:</b> <a href="{prov.get('canonical_url')}">{prov.get('canonical_url')}</a></p>
                            <div style="background: #ffffff; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 0.9rem; color: #374151; border: 1px solid #d1fae5;">
                                {prov.get('exact_chunk_text')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("Không tìm thấy bằng chứng cụ thể liên quan trong hệ thống.")
                    
                    with st.expander("Chi tiết kỹ thuật (Dành cho nhà phát triển)"):
                        st.write(f"**Domain Verdict:** `{verdict}`")
                        st.write(f"**Temporal Status:** `{temp}`")
                        st.write(f"**Abstention Reason:** `{claim_res.get('abstention_reason')}`")
                        if prov:
                            st.write(f"**Notice ID:** `{prov.get('notice_id')}` | **Version ID:** `{prov.get('version_id')}`")
                            
            except Exception as e:
                st.error("Rất tiếc, đã có lỗi xảy ra trong quá trình xác minh. Vui lòng thử lại sau.")
