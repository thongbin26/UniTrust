import streamlit as st
from frontend.api_client import api_client
from frontend.demo_cases import DEMO_CASES

st.set_page_config(page_title="Verify", page_icon="🔍", layout="wide")

st.title("🔍 Verify Information")
st.markdown("Paste forwarded information below to verify it against official university evidence.")

st.info("UniTrust currently has human-reviewed structured coverage for a subset of the indexed DUT notices. Other official notices remain browseable, but structured verification may abstain when reviewed fields are not available.")

# OCR Placeholder
st.file_uploader("Upload Screenshot (OCR) - Coming in a later hardening step", disabled=True, help="OCR functionality is pending.")

text_input = st.text_area("Information to verify", height=150)
use_llm = st.checkbox("Use local semantic AI (may be slower)")
top_k = st.number_input("Top K evidence chunks", min_value=1, max_value=20, value=5)

# Example buttons (Explicitly marked Demo Examples)
st.write("**Demo Cases:**")
col1, col2, col3 = st.columns(3)
if col1.button(DEMO_CASES[0]["label"], help=DEMO_CASES[0]["purpose"]):
    text_input = DEMO_CASES[0]["claim_text"]
    st.rerun()
if col2.button(DEMO_CASES[1]["label"], help=DEMO_CASES[1]["purpose"]):
    text_input = DEMO_CASES[1]["claim_text"]
    st.rerun()
if col3.button(DEMO_CASES[2]["label"], help=DEMO_CASES[2]["purpose"]):
    text_input = DEMO_CASES[2]["claim_text"]
    st.rerun()

if st.button("Verify", type="primary"):
    if not text_input.strip():
        st.error("Please enter some text to verify.")
    else:
        with st.spinner("Verifying against official sources..."):
            try:
                result = api_client.verify_claim(text_input, use_llm=use_llm, top_k=top_k)
                st.success(f"Verification complete in {result.get('latency_ms', 0):.2f}ms")
                
                for claim_res in result.get('results', []):
                    st.divider()
                    st.markdown(f"**Claim:** `{claim_res['raw_claim_text']}`")
                    
                    verdict = claim_res['verdict']
                    temp = claim_res['temporal_status']
                    
                    # Trust State rendering
                    st.subheader("Trạng thái Xác minh (Trust State)")
                    if verdict == "VERIFIED":
                        st.success("✅ **Đã xác minh** - Thông tin này khớp với thông báo chính thức hiện hành.")
                    elif verdict == "PARTIALLY_VERIFIED":
                        st.warning("⚠️ **Xác minh một phần** - Một phần thông tin được xác minh, phần khác chưa rõ ràng.")
                    elif verdict == "CONFLICT":
                        st.error("❌ **Có mâu thuẫn** - Nội dung có điểm mâu thuẫn với thông báo chính thức.")
                    else: # INSUFFICIENT_EVIDENCE
                        reason = claim_res.get('abstention_reason')
                        reason_text = reason if reason and reason != "None" else "Lý do chưa xác định"
                        st.info(f"❔ **Chưa đủ bằng chứng** - Chưa đủ bằng chứng chính thống để xác minh chắc chắn thông tin này. ({reason_text})")
                        
                    # Temporal State rendering
                    st.subheader("Trạng thái Thời gian (Temporal State)")
                    if temp == "CURRENT":
                        st.success("🕒 **Phiên bản hiện hành**")
                    elif temp == "SUPERSEDED_OUTDATED":
                        st.error("🕒 **Đã bị thay thế / lỗi thời**")
                    else:
                        st.warning("🕒 **Chưa xác định phiên bản**")
                        
                    if claim_res.get('field_results'):
                        st.markdown("**So sánh chi tiết (Field Comparisons):**")
                        for k, v in claim_res['field_results'].items():
                            st.markdown(f"- **{k.title()}**: {v['state']} ({v['explanation']})")
                    
                    st.markdown("**Bằng chứng Chính thức (Official Evidence):**")
                    prov = claim_res.get('primary_provenance')
                    if prov:
                        with st.expander("Chi tiết kỹ thuật (Technical Details)"):
                            st.write(f"**Title:** {prov.get('title')}")
                            st.write(f"**Source URL:** {prov.get('canonical_url')}")
                            st.write(f"**Notice ID:** {prov.get('notice_id')} (Version {prov.get('version_id')})")
                            st.write(f"**Exact Official Text:**")
                            st.code(prov.get('exact_chunk_text'))
                    else:
                        st.info("Không có bằng chứng chính thức cụ thể cho yêu cầu này.")
            except Exception as e:
                st.error(f"Failed to verify: {e}")
