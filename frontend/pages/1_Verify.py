import streamlit as st
from frontend.api_client import api_client

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
col1, col2, col3 = st.columns(3)
if col1.button("Example 1: Verified (Real-Source Derived)"):
    text_input = "Sinh viên đóng học phí trước ngày 20/09/2026"
    st.rerun()
if col2.button("Example 2: Wrong Deadline (Synthetic Demo Example)"):
    # Real reviewed obligation has 2026-09-20 deadline
    text_input = "Sinh viên đóng học phí trước ngày 25/09/2026"
    st.rerun()
if col3.button("Example 3: Unsupported (Synthetic Demo Example)"):
    text_input = "Đại học yêu cầu sinh viên đi học mặc áo màu đỏ"
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
                    if verdict == "VERIFIED":
                        st.success(f"✅ {verdict} - Official evidence supports the material claim.")
                    elif verdict == "PARTIALLY_VERIFIED":
                        st.warning(f"⚠️ {verdict} - Some parts are supported, but other fields could not be verified.")
                    elif verdict == "CONFLICT":
                        st.error(f"❌ {verdict} - At least one material field conflicts with official evidence.")
                    else: # INSUFFICIENT_EVIDENCE
                        st.info(f"❔ {verdict} - UniTrust does not have enough official evidence to verify this claim. ({claim_res.get('abstention_reason')})")
                        
                    # Temporal State rendering
                    if temp == "CURRENT":
                        st.success(f"🕒 {temp} - Matches the current known official version.")
                    elif temp == "SUPERSEDED_OUTDATED":
                        st.error(f"🕒 OUTDATED - Evidence matches historical information that is no longer current.")
                    else:
                        st.warning(f"🕒 {temp} - Current validity could not be established.")
                        
                    if claim_res.get('field_results'):
                        st.markdown("**Field Comparisons:**")
                        for k, v in claim_res['field_results'].items():
                            st.markdown(f"- **{k.title()}**: {v['state']} ({v['explanation']})")
                    
                    if claim_res.get('primary_provenance'):
                        with st.expander("Official Evidence Provenance"):
                            prov = claim_res['primary_provenance']
                            st.write(f"**Title:** {prov.get('title')}")
                            st.write(f"**Source URL:** {prov.get('canonical_url')}")
                            st.write(f"**Notice ID:** {prov.get('notice_id')} (Version {prov.get('version_id')})")
                            st.write(f"**Exact Official Text:**")
                            st.code(prov.get('exact_chunk_text'))
            except Exception as e:
                st.error(f"Failed to verify: {e}")
