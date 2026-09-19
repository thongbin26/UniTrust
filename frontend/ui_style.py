import streamlit as st


def apply_global_styles() -> None:
    """Apply the small, shared UniTrust presentation system."""
    st.markdown(
        """
        <style>
            :root {
                --ut-primary: #2563eb;
                --ut-primary-dark: #1d4ed8;
                --ut-primary-soft: #eff6ff;
                --ut-ink: #0f172a;
                --ut-muted: #526176;
                --ut-border: #dce4ee;
                --ut-surface: #ffffff;
                --ut-canvas: #f7f9fc;
                --ut-success: #0f766e;
                --ut-success-soft: #ecfdf5;
                --ut-warning: #a16207;
                --ut-warning-soft: #fffbeb;
                --ut-conflict: #b42318;
                --ut-conflict-soft: #fff1f2;
                --ut-neutral-soft: #f1f5f9;
                --ut-radius: 16px;
                --ut-shadow: 0 12px 30px rgba(15, 23, 42, 0.055);
            }

            html, body, [data-testid="stAppViewContainer"] {
                font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
                color: var(--ut-ink);
                background: var(--ut-canvas);
            }
            [data-testid="stMainBlockContainer"] {
                max-width: 1180px;
                padding-top: 2.25rem;
                padding-bottom: 4rem;
            }
            h1, h2, h3, h4, h5, h6 { color: var(--ut-ink); letter-spacing: -0.025em; }
            p { line-height: 1.65; }

            .ut-page-header { margin: 0 0 1.75rem; max-width: 760px; }
            .ut-eyebrow {
                color: var(--ut-primary-dark);
                font-size: 0.78rem;
                font-weight: 750;
                letter-spacing: 0.095em;
                margin-bottom: 0.6rem;
                text-transform: uppercase;
            }
            .ut-page-title {
                color: var(--ut-ink);
                font-size: clamp(2rem, 4vw, 3rem);
                font-weight: 780;
                line-height: 1.08;
                margin: 0 0 0.75rem;
            }
            .ut-page-description {
                color: var(--ut-muted);
                font-size: 1.04rem;
                line-height: 1.7;
                margin: 0;
                max-width: 720px;
            }
            .ut-section-title {
                color: var(--ut-ink);
                font-size: 1.25rem;
                font-weight: 720;
                margin: 2rem 0 0.85rem;
            }

            .ut-card, .stCard {
                background: var(--ut-surface);
                border: 1px solid var(--ut-border);
                border-radius: var(--ut-radius);
                box-shadow: var(--ut-shadow);
                margin-bottom: 1rem;
                padding: 1.4rem;
            }
            .ut-card-flat {
                background: var(--ut-surface);
                border: 1px solid var(--ut-border);
                border-radius: 14px;
                padding: 1.15rem;
            }
            .ut-empty {
                background: var(--ut-surface);
                border: 1px dashed #cbd5e1;
                border-radius: var(--ut-radius);
                color: var(--ut-muted);
                margin: 1.1rem 0;
                padding: 1.25rem 1.4rem;
            }
            .ut-empty strong { color: var(--ut-ink); display: block; margin-bottom: 0.2rem; }

            .ut-badge {
                align-items: center;
                border-radius: 999px;
                display: inline-flex;
                font-size: 0.78rem;
                font-weight: 720;
                line-height: 1;
                padding: 0.42rem 0.68rem;
            }
            .ut-badge--verified, .ut-badge--applies { background: var(--ut-success-soft); color: var(--ut-success); }
            .ut-badge--partial, .ut-badge--unknown { background: var(--ut-warning-soft); color: var(--ut-warning); }
            .ut-badge--conflict { background: var(--ut-conflict-soft); color: var(--ut-conflict); }
            .ut-badge--insufficient, .ut-badge--not-applies { background: var(--ut-neutral-soft); color: #475569; }

            .ut-meta { color: var(--ut-muted); font-size: 0.9rem; }
            .ut-meta strong { color: #334155; }
            .ut-divider { border: 0; border-top: 1px solid var(--ut-border); margin: 1rem 0; }

            div.stButton > button, div.stLinkButton > a {
                border-radius: 10px;
                font-weight: 680;
                min-height: 2.7rem;
                transition: border-color 120ms ease, background 120ms ease, transform 120ms ease;
            }
            div.stButton > button[kind="primary"], div.stLinkButton > a[kind="primary"] {
                background: var(--ut-primary);
                border-color: var(--ut-primary);
                color: white;
            }
            div.stButton > button[kind="primary"]:hover, div.stLinkButton > a[kind="primary"]:hover {
                background: var(--ut-primary-dark);
                border-color: var(--ut-primary-dark);
            }
            [data-testid="stPageLink"] a {
                border: 1px solid var(--ut-border);
                border-radius: 10px;
                font-weight: 680;
                min-height: 2.8rem;
                padding: 0.65rem 1rem;
            }
            [data-testid="stPageLink"] a:hover { border-color: #93b4f7; color: var(--ut-primary-dark); }

            [data-testid="stTextArea"] textarea, [data-baseweb="select"] > div {
                background: white;
                border-color: #cbd5e1;
                border-radius: 10px;
            }
            [data-testid="stTextArea"] textarea:focus { border-color: var(--ut-primary); }
            [data-testid="stExpander"] {
                background: var(--ut-surface);
                border-color: var(--ut-border);
                border-radius: 12px;
            }
            [data-testid="stAlert"] { border-radius: 12px; }

            [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--ut-border); }
            .ut-sidebar-brand { padding: 0.25rem 0.35rem 1.15rem; }
            .ut-sidebar-name { color: var(--ut-ink); font-size: 1.18rem; font-weight: 780; letter-spacing: -0.03em; }
            .ut-sidebar-tagline { color: var(--ut-muted); font-size: 0.76rem; line-height: 1.45; margin-top: 0.2rem; }

            @media (max-width: 760px) {
                [data-testid="stMainBlockContainer"] { padding-top: 1.25rem; }
                .ut-page-title { font-size: 2rem; }
                .ut-card, .stCard { padding: 1.1rem; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(eyebrow: str, title: str, description: str) -> None:
    """Render a page heading from trusted, static copy."""
    st.markdown(
        f"""
        <div class="ut-page-header">
            <div class="ut-eyebrow">{eyebrow}</div>
            <h1 class="ut-page-title">{title}</h1>
            <p class="ut-page-description">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
