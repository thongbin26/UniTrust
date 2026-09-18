import httpx
import streamlit as st


st.set_page_config(
    page_title="UniTrust V2",
    page_icon="🎓",
    layout="wide",
)


st.title("🎓 UniTrust AI")

st.markdown("### Đúng nguồn. Đúng phiên bản. Đúng người.")

st.info(
    "**UniTrust** giúp sinh viên kiểm chứng thông tin được chuyển tiếp bằng cách đối "
    "chiếu từng nghĩa vụ với bằng chứng chính thống của nhà trường và đúng phiên bản hiện hành."
)

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("🔍 Verify")
    st.write("Xác minh thông tin đối chiếu với bằng chứng chính thức.")
with col2:
    st.subheader("📄 Evidence")
    st.write("Truy xuất nguồn gốc và lịch sử các thông báo.")
with col3:
    st.subheader("👤 For You")
    st.write("Xem các nghĩa vụ dành riêng cho hồ sơ của bạn.")

st.markdown("---")

st.subheader("Nền tảng Dữ liệu (Real Product Data)")
st.markdown(
    """
    - **3** Nguồn thông báo chính thức (DUT sources)
    - **30** Thông báo đã thu thập (Crawled notices)
    - **10** Thông báo được con người đánh giá (Human-reviewed notices)
    - **18** Nghĩa vụ được bóc tách (Reviewed obligations)
    """
)
st.markdown("---")


st.subheader("System status")

backend_url = st.text_input(
    "Backend URL",
    value="http://127.0.0.1:8000",
)


if st.button("Check backend"):
    try:
        response = httpx.get(
            f"{backend_url}/health",
            timeout=3.0,
        )
        response.raise_for_status()

        data = response.json()

        if data.get("status") == "ok":
            st.success("UniTrust backend is running.")
        else:
            st.warning("Backend is reachable but reports degraded status.")

        st.json(data)

    except Exception as exc:
        st.error(
            "Cannot connect to the UniTrust backend. "
            "Make sure FastAPI is running."
        )

        st.code(str(exc))