import httpx
import streamlit as st


st.set_page_config(
    page_title="UniTrust V2",
    page_icon="🎓",
    layout="wide",
)


st.title("🎓 UniTrust V2")

st.caption(
    "Temporal Evidence & Obligation Intelligence for University Notices"
)

st.info(
    "Welcome to UniTrust V2 Competition Demo. "
    "Select a page from the sidebar to begin verification, browse evidence, or check personalized obligations."
)


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