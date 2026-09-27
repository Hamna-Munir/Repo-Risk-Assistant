"""
Repo Onboarding & Risk Assistant
Built for the IBM Bob 2.0 Hackathon (lablab.ai)
Developer: Hamna Munir

Point this at any GitHub repo (or local folder) and get:
  1. An architecture summary
  2. Risk flags for the riskiest files to touch
  3. Missing docstrings/tests, with drafts you can copy in
  4. A shareable Day-1 onboarding brief

Runs fully today on local static analysis (src/analyzer.py).
src/bob_client.py is the single place to plug in real IBM Bob access
once it's issued — nothing else needs to change.
"""

import streamlit as st

from src.analyzer import (
    scan_repo, missing_docs_report, missing_tests_report, build_summary, read_source_snippet,
)
from src.report import (
    architecture_summary_text, risk_table_rows, draft_docstring,
    codebase_health_score, generate_onboarding_brief,
)
from src.bob_client import BOB_AVAILABLE
from src.repo_source import resolve_repo_source
from src.theme import (
    inject_theme, render_header, render_hero, render_health_cards,
    render_status_pill, render_sidebar_mascot, render_footer,
)

st.set_page_config(page_title="Repo Onboarding & Risk Assistant", page_icon="🧭", layout="wide")
inject_theme()

render_header()
render_hero(
    'Understand any repo in <span class="hg-accent">minutes</span>, not days.',
    "Paste a GitHub link — I'll map the architecture, flag the risky files, "
    "and write a day-one onboarding brief for whoever joins next.",
)

with st.sidebar:
    render_sidebar_mascot(BOB_AVAILABLE)
    st.markdown("### Repo source")
    repo_path = st.text_input(
        "GitHub URL or a local folder path",
        value="",
        placeholder="https://github.com/user/repo  or  /path/to/repo",
        help="Paste a public GitHub repo URL (I'll clone it) or a folder already on this machine.",
    )
    scan_clicked = st.button("Scan repo", type="primary")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(render_status_pill(BOB_AVAILABLE), unsafe_allow_html=True)
    if not BOB_AVAILABLE:
        st.caption("Set BOB_API_KEY once access is issued, then wire it up in src/bob_client.py.")

if "modules" not in st.session_state:
    st.session_state.modules = None
if "repo_label" not in st.session_state:
    st.session_state.repo_label = ""

if scan_clicked:
    if not repo_path.strip():
        st.error("Paste a GitHub URL or a local folder path first.")
    else:
        with st.spinner("Getting the repo ready (cloning if it's a URL)..."):
            resolved_path, error = resolve_repo_source(repo_path)
        if error:
            st.error(error)
        else:
            with st.spinner("Scanning repo..."):
                st.session_state.modules = scan_repo(resolved_path)
            st.session_state.repo_label = repo_path.strip()
            st.success(f"Scanned {len(st.session_state.modules)} Python file(s).")

modules = st.session_state.modules
repo_label = st.session_state.repo_label

if modules:
    health = codebase_health_score(modules)
    render_health_cards(health)

# ---- Functional segmented navigation (native buttons — reliable across Streamlit versions) ----
SECTIONS = {
    "📐 Architecture Summary": "See how the repo is structured and which modules matter most.",
    "⚠️ Risk Flags": "Know which files are risky to touch before you change them.",
    "📝 Missing Docs & Tests": "Find the gaps — and draft fixes on the spot.",
    "🚀 Onboarding Brief": "A shareable, day-one document for whoever joins next.",
}

if "active_section" not in st.session_state:
    st.session_state.active_section = list(SECTIONS.keys())[0]

with st.container(key="hg_nav_row"):
    nav_cols = st.columns(len(SECTIONS))
    for col, section_name in zip(nav_cols, SECTIONS.keys()):
        with col:
            is_active = st.session_state.active_section == section_name
            if st.button(
                section_name,
                key=f"nav_{section_name}",
                type="primary" if is_active else "secondary",
                width="stretch",
            ):
                st.session_state.active_section = section_name
                st.rerun()

active = st.session_state.active_section
st.markdown(f'<div class="hg-panel"><div class="hg-panel-desc">{SECTIONS[active]}</div>', unsafe_allow_html=True)

if active == "📐 Architecture Summary":
    if not modules:
        st.info("Scan a repo from the sidebar to see its architecture summary.")
    else:
        summary = build_summary(modules)
        st.markdown(architecture_summary_text(summary))

elif active == "⚠️ Risk Flags":
    if not modules:
        st.info("Scan a repo from the sidebar to see risk flags.")
    else:
        rows = risk_table_rows(modules)
        st.caption("Higher score = riskier to change (widely depended-on, large, or untested).")
        st.dataframe(rows, width="stretch", hide_index=True)

        high_risk = [r for r in rows if r["Risk score"] >= 50]
        if high_risk:
            st.warning(f"{len(high_risk)} file(s) are high-risk — review before changing them.")
        else:
            st.success("No high-risk files detected.")

elif active == "📝 Missing Docs & Tests":
    if not modules:
        st.info("Scan a repo from the sidebar to see missing docs and tests.")
    else:
        missing_docs = missing_docs_report(modules)
        missing_tests = missing_tests_report(modules)

        st.subheader(f"Missing docstrings ({len(missing_docs)})")
        if not missing_docs:
            st.success("Everything has a docstring 🎉")
        else:
            for mod, kind, name, lineno, end_lineno, file_path in missing_docs[:15]:
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.write(f"`{mod}` — {kind} **{name}** (line {lineno})")
                with col2:
                    if st.button("Draft docstring", key=f"draft_{mod}_{name}_{lineno}"):
                        snippet = read_source_snippet(file_path, lineno, end_lineno)
                        with st.spinner("Asking Bob..." if BOB_AVAILABLE else "Generating..."):
                            st.code(draft_docstring(kind, name, snippet), language="text")
            if len(missing_docs) > 15:
                st.caption(f"...and {len(missing_docs) - 15} more.")

        st.subheader(f"Modules with no test file ({len(missing_tests)})")
        if not missing_tests:
            st.success("Every module has a matching test file 🎉")
        else:
            for mod in missing_tests[:15]:
                st.write(f"- `{mod}`")
            if len(missing_tests) > 15:
                st.caption(f"...and {len(missing_tests) - 15} more.")

elif active == "🚀 Onboarding Brief":
    if not modules:
        st.info("Scan a repo from the sidebar to generate its onboarding brief.")
    else:
        summary = build_summary(modules)
        brief_text = generate_onboarding_brief(modules, summary, repo_label or "this repo")
        st.markdown(brief_text)
        st.download_button(
            "⬇️ Download brief as Markdown",
            data=brief_text,
            file_name="onboarding_brief.md",
            mime="text/markdown",
        )

st.markdown("</div>", unsafe_allow_html=True)

render_footer()