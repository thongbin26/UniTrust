import logging
from html import escape

import streamlit as st

from frontend.api_client import URLVerificationRequestError, api_client
from frontend.demo_cases import DEMO_CASES, get_demo_case, selected_demo_text
from frontend.ui_style import apply_global_styles, page_header, page_marker
from frontend.verification_presentation import should_render_official_evidence
from frontend.ui_translations import (
    get_abstention_reason_vi,
    get_action_value_vi,
    get_explanation_vi,
    get_field_name_vi,
    get_field_state_vi,
    format_date_vi,
    get_temporal_state_vi,
    get_trust_state_vi,
    get_url_fetch_error_vi,
    get_url_fetch_warning_vi,
)


apply_global_styles()
page_marker("verify")
page_header(
    "Đối chiếu với nguồn chính thức",
    "Xác minh thông tin",
    "Dán nội dung bạn nhận được từ tin nhắn, bài đăng hoặc thông báo. UniTrust sẽ đối chiếu từng chi tiết có thể kiểm tra với dữ liệu chính thức hiện có.",
)


def _html_text(value) -> str:
    return escape(str(value or "")).replace("\n", "<br>")


def _recognized_field_text(name: str, value: object) -> str:
    values = value if isinstance(value, list) else [value]
    rendered = []
    for item in values:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or ""
        if name == "action":
            text = get_action_value_vi(item.get("normalized_value")) or text
        rendered.append(_html_text(text))
    return ", ".join(rendered)


def _status_class(verdict: str) -> str:
    return {
        "VERIFIED": "verified",
        "PARTIALLY_VERIFIED": "partial",
        "CONFLICT": "conflict",
        "INSUFFICIENT_EVIDENCE": "insufficient",
    }.get(verdict, "insufficient")


def _status_icon(status_class: str) -> str:
    return {
        "verified": "✓",
        "partial": "◐",
        "conflict": "!",
        "insufficient": "?",
    }.get(status_class, "?")


def render_temporal_note(temporal_label: str) -> None:
    st.markdown('<div class="ut-section-title">Điều cần lưu ý</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="ut-empty"><strong>Trạng thái của thông báo</strong>{temporal_label}. UniTrust hiển thị trạng thái này để bạn biết nguồn có còn hiện hành trước khi hành động.</div>',
        unsafe_allow_html=True,
    )


def render_message_results(response: dict) -> None:
    """Render one message-level summary before independently verified claims."""
    results = response.get("results", [])
    if len(results) > 1:
        verdict = response.get("message_verdict", "INSUFFICIENT_EVIDENCE")
        counts = {
            state: sum(item.get("verdict") == state for item in results)
            for state in ("VERIFIED", "PARTIALLY_VERIFIED", "CONFLICT", "INSUFFICIENT_EVIDENCE")
        }
        summary_parts = []
        if counts["VERIFIED"]:
            summary_parts.append(f'{counts["VERIFIED"]} nội dung đã được xác minh')
        if counts["PARTIALLY_VERIFIED"]:
            summary_parts.append(f'{counts["PARTIALLY_VERIFIED"]} nội dung xác minh được một phần')
        if counts["CONFLICT"]:
            summary_parts.append(f'{counts["CONFLICT"]} nội dung có mâu thuẫn')
        if counts["INSUFFICIENT_EVIDENCE"]:
            summary_parts.append(f'{counts["INSUFFICIENT_EVIDENCE"]} nội dung chưa đủ bằng chứng')
        st.markdown('<div class="ut-section-title">Kết luận toàn bộ</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="ut-card-flat"><strong>{escape(get_trust_state_vi(verdict))}</strong><br>'
            f'UniTrust nhận diện {len(results)} nội dung cần kiểm chứng: '
            f'{"; ".join(summary_parts)}.</div>',
            unsafe_allow_html=True,
        )
    for index, item in enumerate(results, start=1):
        render_verification_result(item, index if len(results) > 1 else None, len(results) if len(results) > 1 else None)


def render_verification_result(claim_result: dict, position: int | None = None, total: int | None = None) -> None:
    verdict = claim_result.get("verdict", "INSUFFICIENT_EVIDENCE")
    temporal_status = claim_result.get("temporal_status") or "UNKNOWN"
    status_class = _status_class(verdict)
    trust_label = escape(get_trust_state_vi(verdict))
    temporal_label = escape(get_temporal_state_vi(temporal_status))
    explanation = escape(get_explanation_vi(verdict))
    claim_text = _html_text(claim_result.get("raw_claim_text"))
    compact = position is not None and total is not None
    heading = "Kết luận" if not compact else f"Nội dung {position}/{total}"

    st.markdown(
        f"""
        <div class="ut-section-title">{heading}</div>
        <div class="ut-status-panel ut-status-panel--{status_class}">
            <div class="ut-badge ut-badge--{status_class}"><span class="ut-status-icon" aria-hidden="true">{_status_icon(status_class)}</span>{trust_label}</div>
            <p style="color:var(--ut-ink-soft);font-size:1.02rem;margin:.8rem 0 .9rem;">{explanation}</p>
            <div style="background:var(--ut-surface-subtle);border-radius:8px;color:var(--ut-ink-soft);padding:.8rem .9rem;"><div class="ut-meta" style="font-weight:700;margin:0 0 .35rem;">Nội dung đang được đối chiếu</div>“{claim_text}”</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if verdict == "INSUFFICIENT_EVIDENCE":
        reason = get_abstention_reason_vi(claim_result.get("abstention_reason"))
        st.markdown(
            f'<div class="ut-empty"><strong>Vì sao chưa thể kết luận?</strong>{escape(reason)}</div>',
            unsafe_allow_html=True,
        )

    field_results = claim_result.get("field_results") or {}
    understood = claim_result.get("understood_fields") or {}
    if understood:
        st.markdown('<div class="ut-section-title">Nội dung được nhận diện</div>', unsafe_allow_html=True)
        labels = [
            f'<strong>{escape(get_field_name_vi(name))}:</strong> {_recognized_field_text(name, value)}'
            for name, value in understood.items()
        ]
        st.markdown(f'<div class="ut-card-flat">{"<br>".join(labels)}</div>', unsafe_allow_html=True)

    def render_comparisons() -> None:
        if not field_results:
            return
        st.markdown('<div class="ut-section-title">Điều đã đối chiếu</div>', unsafe_allow_html=True)
        comparison_rows = []
        for field_name, field_value in field_results.items():
            state = field_value.get("state", "INSUFFICIENT_EVIDENCE")
            state_class = _status_class("VERIFIED" if state == "MATCH" else state)
            claimed = field_value.get("claimed_text")
            official = field_value.get("official_text")
            if field_name == "action":
                claimed = get_action_value_vi(claimed)
                official = get_action_value_vi(official)
            claimed_html = _html_text(claimed) if claimed else "—"
            official_html = _html_text(official) if official else "—"
            comparison_rows.append(
                f'<div class="ut-comparison-row">'
                f'<div class="ut-comparison-heading"><strong>{escape(get_field_name_vi(field_name))}</strong>'
                f'<span class="ut-badge ut-badge--{state_class}"><span class="ut-status-icon" aria-hidden="true">{_status_icon(state_class)}</span>{escape(get_field_state_vi(state))}</span></div>'
                f'<div class="ut-comparison"><div></div><div class="ut-comparison-label">Bạn nhận được</div><div class="ut-comparison-label">Nguồn chính thức</div>'
                f'<div></div><div>{claimed_html}</div><div>{official_html}</div></div></div>'
            )
        st.markdown(f'<div class="ut-card-flat">{"".join(comparison_rows)}</div>', unsafe_allow_html=True)

    def render_evidence() -> None:
        provenance = claim_result.get("primary_provenance")
        if not should_render_official_evidence(claim_result):
            if verdict != "INSUFFICIENT_EVIDENCE":
                st.markdown(
                    '<div class="ut-empty"><strong>Bằng chứng chính thức phù hợp</strong>Chưa tìm thấy bằng chứng chính thức đủ phù hợp để đối chiếu với nội dung này.</div>',
                    unsafe_allow_html=True,
                )
            render_temporal_note(temporal_label)
            return
        st.markdown('<div class="ut-section-title">Nguồn chính thức</div>', unsafe_allow_html=True)
        if not provenance:
            st.markdown(
                '<div class="ut-empty"><strong>Chưa có nguồn cụ thể để hiển thị</strong>UniTrust chưa tìm thấy đoạn thông báo chính thức đủ liên quan cho nội dung này.</div>',
                unsafe_allow_html=True,
            )
            render_temporal_note(temporal_label)
            return
        source_title = _html_text(provenance.get("title") or "Thông báo chính thức")
        source_excerpt = escape(" ".join(str(provenance.get("exact_chunk_text") or "").split()))
        publication_date = provenance.get("publication_date")
        date_row = (
            f'<div class="ut-meta" style="margin-top:.35rem;"><strong>Ngày ban hành:</strong> {escape(format_date_vi(publication_date))}</div>'
            if publication_date else ""
        )
        st.markdown(
            f'<div class="ut-card-flat" style="border-color:#cfe5df;"><h3 style="font-size:1.12rem;margin:0;">{source_title}</h3>{date_row}<div class="ut-citation">{source_excerpt}</div></div>',
            unsafe_allow_html=True,
        )
        canonical_url = provenance.get("canonical_url")
        if canonical_url:
            st.link_button("Xem thông báo chính thức", canonical_url, icon=":material/open_in_new:")
        render_temporal_note(temporal_label)

    if compact:
        with st.expander("Xem đối chiếu chi tiết", expanded=False):
            render_comparisons()
            render_evidence()
        return

    render_comparisons()
    render_evidence()


input_mode = st.radio(
    "Bạn nhận được thông tin từ đâu?",
    ("Văn bản", "Ảnh chụp", "Đường link"),
    horizontal=True,
)
submitted = submitted_image = submitted_url = False
text_input = ""
uploaded_image = None
url_input = ""


def _apply_demo_case_to_text_input() -> None:
    """Seed the ordinary text input; verification still requires its normal button."""
    selected_case_id = st.session_state.get("verify_demo_case")
    if selected_case_id:
        st.session_state["verify_text_input"] = selected_demo_text(selected_case_id)

with st.container(border=True):
    if input_mode == "Văn bản":
        st.markdown('<div class="ut-section-title" style="margin:.1rem 0 .65rem;">Dán nội dung bạn nhận được</div>', unsafe_allow_html=True)
        demo_options = [""] + [case["case_id"] for case in DEMO_CASES]
        selected_case_id = st.selectbox(
            "Tình huống mẫu phục vụ trình diễn",
            options=demo_options,
            format_func=lambda case_id: (
                "Chọn tình huống mẫu" if not case_id
                else get_demo_case(case_id)["ui_label"]
            ),
            key="verify_demo_case",
            on_change=_apply_demo_case_to_text_input,
        )
        selected_case = get_demo_case(selected_case_id)
        if selected_case:
            st.caption("Tình huống mẫu phục vụ trình diễn")
            if selected_case["is_synthetic"]:
                st.caption(
                    "Dữ liệu tình huống được tạo có kiểm soát để kiểm thử khả năng "
                    "phát hiện mâu thuẫn hoặc báo chưa đủ bằng chứng."
                )
        text_input = st.text_area(
            "Nội dung cần xác minh",
            height=138,
            placeholder="Dán tin nhắn, bài đăng hoặc đoạn thông báo bạn muốn kiểm tra...",
            label_visibility="collapsed",
            key="verify_text_input",
        )
        st.markdown(
            '<div class="ut-helper"><span class="ut-helper-mark" aria-hidden="true">i</span><span>UniTrust đối chiếu những chi tiết có thể kiểm tra và nói rõ khi chưa đủ bằng chứng.</span></div>',
            unsafe_allow_html=True,
        )
        submitted = st.button("Kiểm chứng nội dung", type="primary", icon=":material/verified_user:")
    elif input_mode == "Ảnh chụp":
        st.markdown('<div class="ut-section-title" style="margin:.1rem 0 .65rem;">Tải ảnh chụp thông tin</div>', unsafe_allow_html=True)
        uploaded_image = st.file_uploader(
            "Ảnh chụp thông tin cần kiểm tra",
            type=["png", "jpg", "jpeg", "webp"],
            help="Hỗ trợ PNG, JPEG và WEBP. Ảnh không được lưu lại.",
        )
        if uploaded_image is not None:
            st.image(uploaded_image.getvalue(), caption="Ảnh bạn đã chọn", width="stretch")
        submitted_image = st.button("Kiểm chứng ảnh", type="primary", icon=":material/image_search:")
    else:
        st.markdown('<div class="ut-section-title" style="margin:.1rem 0 .65rem;">Dán đường link cần kiểm chứng</div>', unsafe_allow_html=True)
        url_input = st.text_input(
            "Đường link cần kiểm chứng",
            placeholder="https://...",
            label_visibility="collapsed",
        )
        st.markdown(
            '<div class="ut-helper"><span class="ut-helper-mark" aria-hidden="true">i</span><span>UniTrust đọc nội dung từ đường link bạn gửi rồi đối chiếu với nguồn chính thức hiện có.</span></div>',
            unsafe_allow_html=True,
        )
        submitted_url = st.button("Kiểm chứng đường link", type="primary", icon=":material/link:")

if submitted:
    if not text_input.strip():
        st.error("Vui lòng nhập nội dung cần xác minh.")
    else:
        with st.spinner("Đang đối chiếu với nguồn chính thức..."):
            try:
                response = api_client.verify_claim(text_input, use_llm=False, top_k=5)
                results = response.get("results", [])
                if results:
                    render_message_results(response)
                else:
                    st.markdown(
                        '<div class="ut-empty"><strong>Chưa có kết quả</strong>Hãy thử diễn đạt rõ hơn nội dung hoặc bổ sung chi tiết cần kiểm tra.</div>',
                        unsafe_allow_html=True,
                    )
            except Exception:
                logging.getLogger(__name__).exception("Verification request or rendering failed")
                st.error("Không thể xác minh thông tin lúc này. Vui lòng thử lại.")
elif submitted_image:
    if uploaded_image is None:
        st.error("Vui lòng chọn ảnh cần kiểm chứng.")
    else:
        with st.spinner("Đang nhận dạng chữ và đối chiếu với nguồn chính thức..."):
            try:
                response = api_client.verify_image(
                    uploaded_image.getvalue(),
                    uploaded_image.name,
                    uploaded_image.type,
                    use_llm=False,
                    top_k=5,
                )
                ocr = response.get("ocr", {})
                st.markdown('<div class="ut-section-title">Nội dung hệ thống đọc được</div>', unsafe_allow_html=True)
                st.text_area(
                    "Nội dung nhận dạng từ ảnh",
                    value=ocr.get("text", ""),
                    height=160,
                    disabled=True,
                )
                st.markdown(
                    '<div class="ut-helper"><span class="ut-helper-mark" aria-hidden="true">i</span><span>Nội dung được nhận dạng tự động từ ảnh. Nếu ảnh mờ hoặc ký tự khó đọc, kết quả nhận dạng có thể chưa chính xác.</span></div>',
                    unsafe_allow_html=True,
                )
                render_message_results(response)
            except Exception:
                logging.getLogger(__name__).exception("Image verification request or rendering failed")
                st.error("Không thể nhận dạng hoặc xác minh ảnh lúc này. Vui lòng thử lại.")
elif submitted_url:
    url = url_input.strip()
    if not url:
        st.warning("Vui lòng nhập đường link cần kiểm chứng.")
    else:
        with st.spinner("Đang đọc nội dung và đối chiếu với nguồn chính thức..."):
            try:
                response = api_client.verify_url(url, top_k=5, use_llm=False)
                st.markdown('<div class="ut-section-title">Nội dung hệ thống đọc được từ đường link</div>', unsafe_allow_html=True)
                title = response.get("page_title")
                if title:
                    st.markdown(f'<div class="ut-meta"><strong>Tiêu đề trang:</strong> {_html_text(title)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ut-meta"><strong>Đường link đã gửi:</strong> {_html_text(response.get("requested_url"))}</div>', unsafe_allow_html=True)
                if response.get("final_url") and response.get("final_url") != response.get("requested_url"):
                    st.markdown(f'<div class="ut-meta"><strong>Đường link sau chuyển hướng:</strong> {_html_text(response.get("final_url"))}</div>', unsafe_allow_html=True)
                st.text_area(
                    "Nội dung đọc từ đường link",
                    value=response.get("extracted_text", ""),
                    height=180,
                    disabled=True,
                )
                st.markdown(
                    '<div class="ut-helper"><span class="ut-helper-mark" aria-hidden="true">i</span><span>Nội dung này được lấy từ đường link bạn cung cấp và chưa được xem là bằng chứng chính thức. UniTrust đối chiếu nội dung này với các nguồn chính thống trong hệ thống.</span></div>',
                    unsafe_allow_html=True,
                )
                for warning in response.get("warnings", []):
                    st.info(get_url_fetch_warning_vi(warning))
                render_message_results(response)
            except URLVerificationRequestError as exc:
                st.error(get_url_fetch_error_vi(exc.code))
            except Exception:
                logging.getLogger(__name__).exception("URL verification request or rendering failed")
                st.error("Không thể đọc nội dung từ đường link này.")
else:
    st.markdown(
        '<div class="ut-empty"><strong>Bạn sẽ nhận được kết quả gì?</strong>UniTrust nêu kết luận, chỉ ra từng chi tiết đã đối chiếu, dẫn nguồn chính thức và giữ rõ những phần chưa chắc chắn.</div>',
        unsafe_allow_html=True,
    )
