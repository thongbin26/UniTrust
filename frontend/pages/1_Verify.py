import logging
from html import escape

import streamlit as st

from frontend.api_client import api_client
from frontend.ui_style import apply_global_styles, page_header
from frontend.ui_translations import (
    get_abstention_reason_vi,
    get_explanation_vi,
    get_field_name_vi,
    get_field_state_vi,
    format_date_vi,
    get_temporal_state_vi,
    get_trust_state_vi,
)


apply_global_styles()
page_header(
    "Đối chiếu với nguồn chính thức",
    "Xác minh thông tin",
    "Dán nội dung bạn nhận được từ tin nhắn, bài đăng hoặc thông báo. UniTrust sẽ đối chiếu từng chi tiết có thể kiểm tra với dữ liệu chính thức hiện có.",
)


def _html_text(value) -> str:
    return escape(str(value or "")).replace("\n", "<br>")


def _status_class(verdict: str) -> str:
    return {
        "VERIFIED": "verified",
        "PARTIALLY_VERIFIED": "partial",
        "CONFLICT": "conflict",
        "INSUFFICIENT_EVIDENCE": "insufficient",
    }.get(verdict, "insufficient")


def render_verification_result(claim_result: dict) -> None:
    verdict = claim_result.get("verdict", "INSUFFICIENT_EVIDENCE")
    temporal_status = claim_result.get("temporal_status") or "UNKNOWN"
    status_class = _status_class(verdict)
    accent = {
        "verified": "success",
        "partial": "warning",
        "conflict": "conflict",
        "insufficient": "muted",
    }[status_class]
    trust_label = escape(get_trust_state_vi(verdict))
    temporal_label = escape(get_temporal_state_vi(temporal_status))
    explanation = escape(get_explanation_vi(verdict))
    claim_text = _html_text(claim_result.get("raw_claim_text"))

    st.markdown(
        f"""
        <div class="ut-card" style="border-top:4px solid var(--ut-{accent});">
            <div class="ut-badge ut-badge--{status_class}">{trust_label}</div>
            <h2 style="font-size:1.55rem;margin:.9rem 0 .55rem;">Kết luận</h2>
            <p style="color:#334155;font-size:1.02rem;margin:0 0 .9rem;">{explanation}</p>
            <div style="background:#f8fafc;border-radius:10px;color:#475569;padding:.85rem 1rem;">“{claim_text}”</div>
            <div class="ut-meta" style="margin-top:.85rem;"><strong>Trạng thái thông báo:</strong> {temporal_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if verdict == "INSUFFICIENT_EVIDENCE":
        reason = get_abstention_reason_vi(claim_result.get("abstention_reason"))
        st.info(f"Lý do: {reason}")

    field_results = claim_result.get("field_results") or {}
    if field_results:
        st.markdown('<div class="ut-section-title">Các nội dung được đối chiếu</div>', unsafe_allow_html=True)
        for field_name, field_value in field_results.items():
            state = field_value.get("state", "INSUFFICIENT_EVIDENCE")
            state_class = _status_class("VERIFIED" if state == "MATCH" else state)
            claimed = field_value.get("claimed_text")
            official = field_value.get("official_text")
            rows = []
            if claimed:
                rows.append(f'<div class="ut-meta"><strong>Bạn nhận được:</strong> {_html_text(claimed)}</div>')
            if official:
                rows.append(f'<div class="ut-meta"><strong>Nguồn chính thức:</strong> {_html_text(official)}</div>')
            st.markdown(
                f"""
                <div class="ut-card-flat" style="margin-bottom:.75rem;">
                    <div style="display:flex;gap:.75rem;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
                        <strong>{escape(get_field_name_vi(field_name))}</strong>
                        <span class="ut-badge ut-badge--{state_class}">{escape(get_field_state_vi(state))}</span>
                    </div>
                    <div style="display:grid;gap:.35rem;margin-top:.75rem;">{''.join(rows)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="ut-section-title">Nguồn chính thức</div>', unsafe_allow_html=True)
    provenance = claim_result.get("primary_provenance")
    if not provenance:
        st.markdown(
            '<div class="ut-empty"><strong>Chưa có nguồn cụ thể để hiển thị</strong>UniTrust chưa tìm thấy đoạn thông báo chính thức đủ liên quan cho nội dung này.</div>',
            unsafe_allow_html=True,
        )
        return

    source_title = _html_text(provenance.get("title") or "Thông báo chính thức")
    source_excerpt = escape(" ".join(str(provenance.get("exact_chunk_text") or "").split()))
    publication_date = provenance.get("publication_date")
    date_row = (
        f'<div class="ut-meta" style="margin-top:.35rem;"><strong>Ngày ban hành:</strong> {escape(format_date_vi(publication_date))}</div>'
        if publication_date else ""
    )
    source_card = (
        f'<div class="ut-card" style="box-shadow:none;border-color:#bdebdc;">'
        f'<h3 style="font-size:1.12rem;margin:0;">{source_title}</h3>{date_row}'
        f'<div style="background:#f8fafc;border-left:3px solid #94a3b8;border-radius:8px;color:#334155;line-height:1.65;margin-top:1rem;padding:1rem;">{source_excerpt}</div>'
        '</div>'
    )
    st.markdown(source_card, unsafe_allow_html=True)
    canonical_url = provenance.get("canonical_url")
    if canonical_url:
        st.link_button("Xem thông báo chính thức", canonical_url, icon=":material/open_in_new:")


st.markdown('<div class="ut-section-title" style="margin-top:.5rem;">Nội dung cần kiểm tra</div>', unsafe_allow_html=True)
text_input = st.text_area(
    "Nội dung cần xác minh",
    height=170,
    placeholder="Ví dụ: Sinh viên phải hoàn thành đánh giá rèn luyện trước ngày...",
    label_visibility="collapsed",
)
submitted = st.button("Xác minh thông tin", type="primary", icon=":material/verified_user:")

if submitted:
    if not text_input.strip():
        st.error("Vui lòng nhập nội dung cần xác minh.")
    else:
        with st.spinner("Đang đối chiếu với nguồn chính thức..."):
            try:
                response = api_client.verify_claim(text_input, use_llm=False, top_k=5)
                results = response.get("results", [])
                if results:
                    for item in results:
                        render_verification_result(item)
                else:
                    st.markdown(
                        '<div class="ut-empty"><strong>Chưa có kết quả</strong>Hãy thử diễn đạt rõ hơn nội dung hoặc bổ sung chi tiết cần kiểm tra.</div>',
                        unsafe_allow_html=True,
                    )
            except Exception:
                logging.getLogger(__name__).exception("Verification request or rendering failed")
                st.error("Không thể xác minh thông tin lúc này. Vui lòng thử lại.")
else:
    st.markdown(
        '<div class="ut-empty"><strong>Bắt đầu từ nội dung bạn đang phân vân</strong>Dán tin nhắn, bài đăng hoặc đoạn thông báo vào ô trên để kiểm tra.</div>',
        unsafe_allow_html=True,
    )
