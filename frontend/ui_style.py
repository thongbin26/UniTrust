"""Shared presentation primitives for the UniTrust student portal."""

from html import escape

import streamlit as st


def apply_global_styles() -> None:
    """Apply the Calm Academic Trust Portal design system."""
    st.markdown(
        """
        <style>
            :root {
                --ut-canvas: #f7f7f4;
                --ut-surface: #ffffff;
                --ut-surface-subtle: #f2f3f1;
                --ut-ink: #111c2c;
                --ut-ink-soft: #2f3d4f;
                --ut-muted: #556273;
                --ut-border: #d9dedf;
                --ut-border-strong: #c3cbce;
                --ut-primary: #1f5ed8;
                --ut-primary-hover: #194fb9;
                --ut-primary-soft: #edf3fb;
                --ut-official: #18766c;
                --ut-official-soft: #eaf6f2;
                --ut-warning: #936514;
                --ut-warning-soft: #fbf5e5;
                --ut-conflict: #a7473d;
                --ut-conflict-soft: #faefed;
                --ut-neutral-soft: #eef1f2;
                --ut-radius-sm: 8px;
                --ut-radius: 12px;
                --ut-radius-lg: 16px;
                --ut-shadow: 0 10px 26px rgba(17, 28, 44, 0.045);
            }

            html, body, [data-testid="stAppViewContainer"] {
                background: var(--ut-canvas);
                color: var(--ut-ink);
                font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                    "Segoe UI", sans-serif;
            }
            [data-testid="stMainBlockContainer"] {
                max-width: 1180px;
                padding-top: 2.4rem;
                padding-bottom: 4.5rem;
            }
            [data-testid="stMainBlockContainer"]:has(.ut-page--verify) { max-width: 880px; }
            [data-testid="stMainBlockContainer"]:has(.ut-page--evidence) { max-width: 960px; }
            [data-testid="stMainBlockContainer"]:has(.ut-page--for-you) { max-width: 1080px; }

            h1, h2, h3, h4, h5, h6 {
                color: var(--ut-ink);
                letter-spacing: -0.026em;
            }
            p { line-height: 1.65; }
            a { text-underline-offset: 0.16em; }

            .ut-page-marker { height: 0; margin: 0; overflow: hidden; }
            .ut-page-header { margin: 0 0 1.45rem; max-width: 760px; }
            .ut-eyebrow {
                color: var(--ut-primary-hover);
                font-size: 0.75rem;
                font-weight: 760;
                letter-spacing: 0.09em;
                margin-bottom: 0.6rem;
                text-transform: uppercase;
            }
            .ut-page-title {
                color: var(--ut-ink);
                font-size: clamp(2.45rem, 4.2vw, 2.85rem);
                font-weight: 780;
                line-height: 1.08;
                margin: 0 0 0.7rem;
            }
            .ut-page-description {
                color: var(--ut-muted);
                font-size: 1.025rem;
                line-height: 1.65;
                margin: 0;
                max-width: 720px;
            }
            .ut-section-title {
                align-items: center;
                color: var(--ut-ink);
                display: flex;
                font-size: 1.18rem;
                font-weight: 730;
                gap: 0.55rem;
                letter-spacing: -0.016em;
                margin: 1.75rem 0 0.75rem;
            }
            .ut-section-kicker {
                color: var(--ut-muted);
                font-size: 0.88rem;
                font-weight: 650;
                letter-spacing: 0.015em;
                margin-bottom: 0.3rem;
            }

            .ut-task-panel {
                background: var(--ut-surface);
                border: 1px solid var(--ut-border);
                border-radius: var(--ut-radius-lg);
                box-shadow: var(--ut-shadow);
                padding: 1.25rem 1.35rem 0.35rem;
            }
            .ut-status-panel {
                background: var(--ut-surface);
                border: 1px solid var(--ut-border);
                border-left: 4px solid var(--ut-border-strong);
                border-radius: var(--ut-radius);
                padding: 1.2rem 1.25rem;
            }
            .ut-status-panel--verified { border-left-color: var(--ut-official); }
            .ut-status-panel--partial, .ut-status-panel--insufficient { border-left-color: var(--ut-warning); }
            .ut-status-panel--conflict { border-left-color: var(--ut-conflict); }
            .ut-profile-summary {
                background: var(--ut-surface);
                border: 1px solid var(--ut-border);
                border-radius: var(--ut-radius);
                padding: 1.1rem 1.2rem;
            }
            .ut-notice-item {
                border-bottom: 1px solid var(--ut-border);
                padding: 0.9rem 0;
            }
            .ut-notice-item:last-child { border-bottom: 0; padding-bottom: 0.2rem; }

            .ut-card {
                background: var(--ut-surface);
                border: 1px solid var(--ut-border);
                border-radius: var(--ut-radius-lg);
                margin-bottom: 1rem;
                padding: 1.35rem;
            }
            .ut-card-flat {
                background: var(--ut-surface);
                border: 1px solid var(--ut-border);
                border-radius: var(--ut-radius);
                padding: 1.05rem 1.1rem;
            }
            .ut-empty {
                background: var(--ut-surface-subtle);
                border: 1px solid var(--ut-border);
                border-radius: var(--ut-radius);
                color: var(--ut-muted);
                margin: 1rem 0;
                padding: 1.05rem 1.15rem;
            }
            .ut-empty strong {
                color: var(--ut-ink);
                display: block;
                margin-bottom: 0.2rem;
            }
            .ut-helper {
                align-items: flex-start;
                color: var(--ut-muted);
                display: flex;
                font-size: 0.9rem;
                gap: 0.55rem;
                line-height: 1.55;
                margin: 0.25rem 0 0.9rem;
            }
            .ut-helper-mark {
                color: var(--ut-official);
                font-size: 1rem;
                font-weight: 800;
                line-height: 1.35;
            }

            .ut-badge {
                align-items: center;
                border: 1px solid transparent;
                border-radius: 999px;
                display: inline-flex;
                font-size: 0.78rem;
                font-weight: 720;
                gap: 0.35rem;
                line-height: 1;
                padding: 0.4rem 0.65rem;
            }
            .ut-status-icon { font-size: 0.84rem; font-weight: 850; line-height: 1; }
            .ut-badge--verified, .ut-badge--applies {
                background: var(--ut-official-soft);
                border-color: #cce6df;
                color: var(--ut-official);
            }
            .ut-badge--partial {
                background: #f3f0e8;
                border-color: #e1d8be;
                color: #775d1f;
            }
            .ut-badge--unknown, .ut-badge--insufficient {
                background: var(--ut-warning-soft);
                border-color: #eadcb7;
                color: var(--ut-warning);
            }
            .ut-badge--conflict {
                background: var(--ut-conflict-soft);
                border-color: #eccbc7;
                color: var(--ut-conflict);
            }
            .ut-badge--not-applies {
                background: var(--ut-neutral-soft);
                border-color: var(--ut-border);
                color: #52606d;
            }
            .ut-count {
                align-items: center;
                background: var(--ut-neutral-soft);
                border-radius: 999px;
                color: var(--ut-ink-soft);
                display: inline-flex;
                font-size: 0.76rem;
                font-weight: 720;
                justify-content: center;
                min-width: 1.55rem;
                padding: 0.2rem 0.48rem;
            }

            .ut-meta { color: var(--ut-muted); font-size: 0.9rem; line-height: 1.55; }
            .ut-meta strong { color: var(--ut-ink-soft); }
            .ut-divider { border: 0; border-top: 1px solid var(--ut-border); margin: 1rem 0; }
            .ut-citation {
                background: var(--ut-surface-subtle);
                border-left: 3px solid var(--ut-official);
                color: var(--ut-ink-soft);
                line-height: 1.68;
                margin-top: 1rem;
                padding: 0.95rem 1rem;
            }
            .ut-comparison {
                display: grid;
                gap: 0;
                grid-template-columns: minmax(115px, 0.75fr) minmax(0, 1.25fr) minmax(0, 1.25fr);
                margin-top: 0.8rem;
            }
            .ut-comparison > div {
                border-top: 1px solid var(--ut-border);
                color: var(--ut-ink-soft);
                min-width: 0;
                padding: 0.75rem 0.7rem;
            }
            .ut-comparison-label { color: var(--ut-muted) !important; font-size: 0.82rem; font-weight: 680; }
            .ut-comparison-row { border-bottom: 1px solid var(--ut-border); padding: 0.15rem 0 0.7rem; }
            .ut-comparison-row:last-child { border-bottom: 0; padding-bottom: 0; }
            .ut-comparison-heading {
                align-items: center;
                display: flex;
                flex-wrap: wrap;
                gap: 0.65rem;
                justify-content: space-between;
                padding-top: 0.7rem;
            }

            div.stButton > button, div.stLinkButton > a {
                border-radius: var(--ut-radius-sm);
                font-weight: 690;
                min-height: 2.75rem;
                transition: border-color 120ms ease, background-color 120ms ease, color 120ms ease;
            }
            div.stButton > button[kind="primary"], div.stLinkButton > a[kind="primary"] {
                background: var(--ut-primary);
                border-color: var(--ut-primary);
                color: #ffffff;
            }
            div.stButton > button[kind="primary"]:hover, div.stLinkButton > a[kind="primary"]:hover {
                background: var(--ut-primary-hover);
                border-color: var(--ut-primary-hover);
            }
            div.stButton > button:focus-visible, div.stLinkButton > a:focus-visible,
            [data-testid="stPageLink"] a:focus-visible {
                box-shadow: 0 0 0 3px rgba(31, 94, 216, 0.2);
                outline: 2px solid var(--ut-primary);
                outline-offset: 2px;
            }
            [data-testid="stPageLink"] a {
                border: 1px solid transparent;
                border-radius: var(--ut-radius-sm);
                color: var(--ut-ink-soft);
                font-weight: 670;
                min-height: 2.7rem;
                padding: 0.58rem 0.75rem;
            }
            [data-testid="stPageLink"] a:hover {
                background: var(--ut-surface-subtle);
                border-color: var(--ut-border);
                color: var(--ut-primary-hover);
            }

            [data-testid="stTextArea"] textarea,
            [data-baseweb="select"] > div,
            [data-testid="stTextInput"] input {
                background: var(--ut-surface);
                border-color: var(--ut-border-strong);
                border-radius: var(--ut-radius-sm);
                color: var(--ut-ink);
            }
            [data-testid="stTextArea"] textarea { line-height: 1.6; padding: 0.9rem 1rem; }
            [data-testid="stTextArea"] textarea:focus,
            [data-baseweb="select"] > div:focus-within,
            [data-testid="stTextInput"] input:focus {
                border-color: var(--ut-primary);
                box-shadow: 0 0 0 3px rgba(31, 94, 216, 0.13);
            }
            [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {
                border-color: var(--ut-border);
                border-radius: var(--ut-radius-lg);
            }
            [data-testid="stExpander"] {
                background: var(--ut-surface);
                border-color: var(--ut-border);
                border-radius: var(--ut-radius);
            }
            [data-testid="stAlert"] { border-radius: var(--ut-radius); }
            [data-testid="stCustomComponentV1"] iframe { border-radius: var(--ut-radius-sm); }

            [data-testid="stSidebar"] {
                background: #fbfbf9;
                border-right: 1px solid var(--ut-border);
            }
            [data-testid="stSidebarContent"] { padding-top: 1.1rem; }
            [data-testid="stSidebar"] [data-testid="stPageLink"] { margin: 0.12rem 0; }
            [data-testid="stSidebar"] [data-testid="stPageLink"] a {
                border-radius: var(--ut-radius-sm);
                min-height: 2.55rem;
                position: relative;
            }
            [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {
                background: var(--ut-primary-soft);
                color: var(--ut-ink);
                font-weight: 720;
            }
            [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"]::before {
                background: var(--ut-primary);
                border-radius: 0 3px 3px 0;
                content: "";
                height: 1.45rem;
                left: -0.55rem;
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                width: 3px;
            }
            .ut-sidebar-brand { padding: 0 0.35rem 0.7rem; }
            .ut-sidebar-lockup { align-items: center; display: flex; gap: 0.7rem; }
            .ut-sidebar-mark {
                align-items: center;
                background: var(--ut-ink);
                border-radius: 9px;
                color: #ffffff;
                display: inline-flex;
                font-size: 0.84rem;
                font-weight: 800;
                height: 2.1rem;
                justify-content: center;
                letter-spacing: -0.04em;
                width: 2.1rem;
            }
            .ut-sidebar-name { color: var(--ut-ink); font-size: 1.12rem; font-weight: 790; letter-spacing: -0.035em; }
            .ut-sidebar-tagline { color: var(--ut-muted); font-size: 0.76rem; line-height: 1.45; margin-top: 0.08rem; }

            .ut-hero { padding: 0.5rem 0 0.2rem; }
            .ut-hero-title {
                color: var(--ut-ink);
                font-size: clamp(3.1rem, 6vw, 4.65rem);
                font-weight: 800;
                letter-spacing: -0.055em;
                line-height: 0.98;
                margin: 0 0 1.05rem;
            }
            .ut-hero-slogan {
                color: var(--ut-primary-hover);
                font-size: clamp(1.12rem, 2vw, 1.28rem);
                font-weight: 730;
                margin: 0 0 0.85rem;
            }
            .ut-hero-visual {
                background: var(--ut-surface);
                border: 1px solid var(--ut-border);
                border-radius: 20px;
                box-shadow: var(--ut-shadow);
                padding: 0.75rem;
            }
            .ut-action-tile {
                background: transparent;
                border-top: 1px solid var(--ut-border-strong);
                min-height: 70px;
                padding: 0.75rem 0.2rem 0.1rem;
            }
            .ut-action-icon {
                color: var(--ut-primary-hover);
                font-size: 1.05rem;
                font-weight: 760;
                margin-bottom: 0.75rem;
            }
            .ut-action-tile h3 { font-size: 1.08rem; margin: 0 0 0.35rem; }
            .ut-action-tile p { color: var(--ut-muted); font-size: 0.92rem; margin: 0; }
            .ut-obligation { margin-bottom: 0.65rem; }
            .ut-obligation--unknown { padding: 0.82rem 1rem; }
            .ut-obligation--unknown h3 { margin-bottom: 0.55rem !important; }
            .ut-obligation--unknown .ut-divider { margin: 0.68rem 0; }
            .ut-principle {
                align-items: flex-start;
                background: var(--ut-official-soft);
                border: 1px solid #cfe5df;
                border-radius: var(--ut-radius);
                display: flex;
                gap: 0.8rem;
                margin-top: 1.75rem;
                padding: 1rem 1.1rem;
            }
            .ut-principle-mark { color: var(--ut-official); font-size: 1.1rem; font-weight: 800; line-height: 1.25; }

            @media (max-width: 900px) {
                [data-testid="stMainBlockContainer"] { padding-left: 1.4rem; padding-right: 1.4rem; }
                .ut-comparison { grid-template-columns: 1fr; }
                .ut-comparison > div { padding-left: 0; padding-right: 0; }
                .ut-comparison-label { border-bottom: 0; padding-bottom: 0.15rem !important; }
            }
            @media (max-width: 760px) {
                [data-testid="stMainBlockContainer"] { padding-top: 1.35rem; }
                .ut-page-title { font-size: 2.15rem; }
                .ut-hero-title { font-size: 3rem; }
                .ut-task-panel, .ut-card { padding: 1.05rem; }
            }
            @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_marker(page: str) -> None:
    """Mark a page so its task-specific content width can be applied."""
    safe_page = "".join(character for character in page if character.isalnum() or character == "-")
    st.markdown(f'<div class="ut-page-marker ut-page--{safe_page}"></div>', unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, description: str) -> None:
    """Render a page heading from trusted copy using the shared hierarchy."""
    st.markdown(
        f"""
        <div class="ut-page-header">
            <div class="ut-eyebrow">{escape(eyebrow)}</div>
            <h1 class="ut-page-title">{escape(title)}</h1>
            <p class="ut-page-description">{escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
