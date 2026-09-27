"""
Visual theme for Repo Onboarding & Risk Assistant.

Design concept: a premium, focused dev-tool workspace — white cards on
a soft neutral background, one confident blue accent, a gradient icon
mark, and a tagline hero (not a personal greeting, since this is a
hackathon product, not a personal assistant). IBM Plex Mono carries
code identifiers and the accent word in the tagline; IBM Plex Sans
carries everything else.

Palette:
  bg          #F5F6FA  soft neutral background
  surface     #FFFFFF  cards / sidebar / panel
  border      #E6E8EE
  text        #14161C
  text-muted  #6B7280
  blue        #2F6FED  primary accent
  blue-2      #22C9C0  gradient partner (icon mark, accent word)
  teal        #1FA97E  status: healthy
  amber       #D8A22B  status: needs attention
  red         #E5484D  status: at risk

Credit: this app was built by Hamna Munir. render_header() renders a
single credit pill in the top-right corner — that is the one place
the name appears in the UI, matching the reference product style.
"""

import streamlit as st

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
    --bg: #F5F6FA;
    --surface: #FFFFFF;
    --border: #E6E8EE;
    --text: #14161C;
    --text-muted: #6B7280;
    --blue: #2F6FED;
    --blue-hover: #2559C7;
    --blue-2: #22C9C0;
    --teal: #1FA97E;
    --amber: #D8A22B;
    --red: #E5484D;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    color: var(--text);
}
[data-testid="stAppViewContainer"] { background-color: var(--bg); }
[data-testid="stHeader"] { background-color: transparent; }

h1, h2, h3 {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 600 !important;
    color: var(--text) !important;
}

/* ---- Top header row: wordmark only (credit lives in the footer, one place) ---- */
.hg-topbar {
    margin-bottom: 1.6rem;
}
.hg-wordmark {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    font-weight: 700;
    font-size: 1.85rem;
    color: var(--text);
    letter-spacing: -0.015em;
}
.hg-wordmark-icon {
    width: 52px; height: 52px;
    border-radius: 13px;
    background: linear-gradient(135deg, var(--blue), var(--blue-2));
    display: flex; align-items: center; justify-content: center;
    font-size: 1.7rem;
    box-shadow: 0 2px 8px rgba(47,111,237,0.3);
}

/* ---- Hero ---- */
.hg-hero {
    margin-bottom: 1.8rem;
}
.hg-hero-title {
    font-size: 2.15rem;
    font-weight: 700;
    line-height: 1.25;
    color: var(--text);
    margin-bottom: 0.6rem;
}
.hg-hero-title .hg-accent {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    background: linear-gradient(135deg, var(--blue), var(--blue-2));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.hg-hero-subtitle {
    color: var(--text-muted);
    font-size: 1.02rem;
    max-width: 640px;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background-color: var(--surface);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.95rem;
}
[data-testid="stSidebar"] label { color: var(--text-muted) !important; font-size: 0.85rem; }

.stTextInput > div > div input {
    border-radius: 8px;
    border: 1px solid var(--border);
    background-color: var(--bg);
}

.stButton > button[kind="primary"] {
    background-color: var(--blue);
    color: #FFFFFF;
    border: none;
    font-weight: 500;
    border-radius: 8px;
}
.stButton > button[kind="primary"]:hover { background-color: var(--blue-hover); color: #FFFFFF; }
.stButton > button:not([kind="primary"]) {
    border-radius: 8px;
    border: 1px solid var(--border);
    color: var(--text);
}

.hg-pill { display: inline-block; padding: 0.3rem 0.7rem; border-radius: 999px; font-size: 0.8rem; font-weight: 500; }
.hg-pill-on { background-color: #E4F6EE; color: var(--teal); }
.hg-pill-off { background-color: #FBEFDC; color: var(--amber); }

code, .hg-mono {
    font-family: 'IBM Plex Mono', monospace !important;
    background-color: #EEF0F5;
    padding: 0.05rem 0.35rem;
    border-radius: 4px;
    color: var(--text);
}

/* ---- Health stat cards ---- */
.hg-card-row { display: flex; gap: 0.9rem; flex-wrap: wrap; margin: 0.4rem 0 1.6rem 0; }
.hg-card {
    flex: 1 1 180px;
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.95rem 1.15rem;
    box-shadow: 0 1px 3px rgba(16,24,40,0.05);
    position: relative;
    overflow: hidden;
}
.hg-card::before {
    content: "";
    position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    background-color: var(--accent, var(--blue));
}
.hg-card-label { color: var(--text-muted); font-size: 0.82rem; margin-bottom: 0.25rem; }
.hg-card-value { font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 1.6rem; color: var(--text); line-height: 1.1; }
.hg-card-sub { color: var(--text-muted); font-size: 0.78rem; margin-top: 0.15rem; }

/* ---- Functional segmented navigation (native st.button per section) ---- */
.st-key-hg_nav_row [data-testid="column"] { display: flex; }
.st-key-hg_nav_row .stButton { width: 100%; }
.st-key-hg_nav_row .stButton > button {
    width: 100%;
    height: 3.1rem;
    border-radius: 10px;
    font-weight: 500;
    font-size: 0.92rem;
    white-space: nowrap;
}
.st-key-hg_nav_row .stButton > button[kind="secondary"] {
    background-color: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
}
.st-key-hg_nav_row .stButton > button[kind="secondary"]:hover {
    background-color: #F3F5FA;
    border-color: #C9DBFF;
}

/* Panel that wraps the active section's content */
.hg-panel {
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.5rem 1.6rem;
    margin-top: 0.9rem;
}
.hg-panel-desc { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem; }

[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }

.hg-footer {
    margin-top: 2.5rem;
    padding-top: 1.2rem;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: center;
}
.hg-footer-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 0.45rem 0.95rem;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-muted);
    box-shadow: 0 1px 2px rgba(16,24,40,0.05);
}
.hg-footer-pill strong { color: var(--text); font-weight: 600; }
</style>
"""


def inject_theme() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_sidebar_mascot(connected: bool) -> None:
    """A small original robot mascot for the sidebar — reflects Bob's connection state."""
    face_color = "#2F6FED" if connected else "#B9BEC9"
    glow = "0 0 0 4px rgba(47,111,237,0.12)" if connected else "none"
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin: 0.4rem 0 1rem 0;">
            <svg width="72" height="72" viewBox="0 0 72 72" style="filter: drop-shadow({glow});">
                <rect x="14" y="24" width="44" height="36" rx="12" fill="#F5F6FA" stroke="{face_color}" stroke-width="2.5"/>
                <rect x="30" y="10" width="12" height="14" rx="4" fill="{face_color}"/>
                <circle cx="36" cy="8" r="3" fill="{face_color}"/>
                <circle cx="26" cy="40" r="4" fill="#14161C"/>
                <circle cx="46" cy="40" r="4" fill="#14161C"/>
                <path d="M27 50 Q36 57 45 50" stroke="#14161C" stroke-width="2.5" fill="none" stroke-linecap="round"/>
                <rect x="4" y="34" width="8" height="14" rx="4" fill="{face_color}"/>
                <rect x="60" y="34" width="8" height="14" rx="4" fill="{face_color}"/>
            </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Top row: just the product wordmark. Credit lives only in the footer."""
    st.markdown(
        """
        <div class="hg-topbar">
            <div class="hg-wordmark">
                <span class="hg-wordmark-icon">🧭</span>
                Repo Onboarding &amp; Risk Assistant
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title_html: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hg-hero">
            <div class="hg-hero-title">{title_html}</div>
            <div class="hg-hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


_STATUS_COLOR = {"Healthy": "var(--teal)", "Needs attention": "var(--amber)", "At risk": "var(--red)"}


def render_health_cards(health: dict) -> None:
    accent = _STATUS_COLOR.get(health["label"], "var(--blue)")
    cards = [
        (f"{health['score']}/100", "Codebase health", health["label"], accent),
        (f"{health['test_pct']}%", "Test coverage", None, "var(--blue)"),
        (f"{health['doc_pct']}%", "Docstring coverage", None, "var(--blue)"),
        (f"{health['risk_pct']}%", "Risk concentration", None, "var(--blue)"),
    ]
    html = ['<div class="hg-card-row">']
    for value, label, sub, accent_color in cards:
        sub_html = f'<div class="hg-card-sub">{sub}</div>' if sub else ""
        html.append(
            f'<div class="hg-card" style="--accent:{accent_color}">'
            f'<div class="hg-card-label">{label}</div>'
            f'<div class="hg-card-value">{value}</div>'
            f"{sub_html}"
            f"</div>"
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_status_pill(connected: bool) -> str:
    if connected:
        return '<span class="hg-pill hg-pill-on">IBM Bob connected</span>'
    return '<span class="hg-pill hg-pill-off">Bob not connected — local analysis only</span>'


def render_footer() -> None:
    st.markdown(
        """
        <div class="hg-footer">
            <div class="hg-footer-pill">🔗 Built by <strong>Hamna Munir</strong> — IBM Bob 2.0 Hackathon</div>
        </div>
        """,
        unsafe_allow_html=True,
    )