"""Small helpers that turn analyzer.py's raw data into UI-ready text/tables."""

import datetime

from src.analyzer import risk_score, missing_docs_report, missing_tests_report
from src.bob_client import narrate


def architecture_summary_text(summary: dict) -> str:
    lines = [
        f"**{summary['module_count']}** Python modules, "
        f"**{summary['total_loc']}** lines of code total.",
        f"**{summary['total_functions']}** functions, "
        f"**{summary['total_classes']}** classes found.",
        "",
        "**Most depended-on modules** (changing these has the widest blast radius):",
    ]
    for mod, info in summary["most_depended_on"]:
        if info.fan_in > 0:
            lines.append(f"- `{mod}` — imported by {info.fan_in} other module(s)")
    if len(lines) == 4:
        lines.append("- (no internal cross-module imports detected)")
    return "\n".join(lines)


def risk_table_rows(modules: dict) -> list:
    rows = []
    for mod, info in modules.items():
        rows.append({
            "Module": mod,
            "Risk score": risk_score(info),
            "Fan-in (depended on by)": info.fan_in,
            "Lines of code": info.loc,
            "Has tests": "Yes" if info.has_test_file else "No",
        })
    rows.sort(key=lambda r: r["Risk score"], reverse=True)
    return rows


def draft_docstring(kind: str, name: str, source_code: str = "") -> str:
    """
    Ask Bob (or the local fallback) to draft a docstring for a
    function/class that's missing one. Passing the real source code
    (when we have it) means Bob can answer directly from the prompt
    instead of spending time/tool-calls searching the filesystem.
    """
    if source_code:
        prompt = (
            f"Write a concise one-line Python docstring for this {kind} named '{name}'. "
            "You already have the full source code below — do not search any files or "
            "the workspace. Respond with ONLY the docstring text (including the triple "
            "quotes), nothing else — no explanation, no code fences."
        )
        context = source_code
    else:
        prompt = f"Write a concise one-line docstring for the {kind} named '{name}'."
        context = f"{kind}: {name}"
    return narrate(prompt, context=context)


def codebase_health_score(modules: dict) -> dict:
    """
    A single 0-100 'Codebase Health' score, built from three
    sub-scores that are each easy to explain to a judge or a
    new teammate:
      - Test coverage ratio  (how many modules have a matching test file)
      - Docstring coverage   (how many functions/classes are documented)
      - Risk concentration   (inverse of average risk score across modules)
    """
    if not modules:
        return {"score": 0, "test_pct": 0, "doc_pct": 0, "risk_pct": 0, "label": "No data"}

    total_modules = len(modules)
    tested = sum(1 for m in modules.values() if m.has_test_file)
    test_pct = round(100 * tested / total_modules)

    total_defs = sum(len(m.functions) + len(m.classes) for m in modules.values())
    documented = sum(
        sum(1 for _, has_doc, _, _ in m.functions if has_doc) +
        sum(1 for _, has_doc, _, _ in m.classes if has_doc)
        for m in modules.values()
    )
    doc_pct = round(100 * documented / total_defs) if total_defs else 100

    avg_risk = sum(risk_score(m) for m in modules.values()) / total_modules
    risk_pct = round(100 - avg_risk)

    score = round(0.4 * test_pct + 0.3 * doc_pct + 0.3 * risk_pct)

    if score >= 80:
        label = "Healthy"
    elif score >= 55:
        label = "Needs attention"
    else:
        label = "At risk"

    return {
        "score": score,
        "test_pct": test_pct,
        "doc_pct": doc_pct,
        "risk_pct": risk_pct,
        "label": label,
    }


def generate_onboarding_brief(modules: dict, summary: dict, repo_label: str) -> str:
    """
    Compiles everything the app knows into ONE shareable Markdown
    document — the thing a brand-new developer would actually want
    to read on day one, instead of clicking through three tabs.
    """
    health = codebase_health_score(modules)
    risky_rows = risk_table_rows(modules)[:5]
    docs_missing = missing_docs_report(modules)
    tests_missing = missing_tests_report(modules)

    lines = [
        f"# Day-1 Onboarding Brief — {repo_label}",
        f"_Generated {datetime.date.today().isoformat()} by Repo Onboarding & Risk Assistant_",
        "",
        f"## Codebase Health: {health['score']}/100 ({health['label']})",
        f"- Test coverage: {health['test_pct']}%",
        f"- Docstring coverage: {health['doc_pct']}%",
        f"- Risk concentration score: {health['risk_pct']}%",
        "",
        "## What this codebase looks like",
        architecture_summary_text(summary),
        "",
        "## Files to be careful with (highest risk first)",
        "New here? Don't touch these on day one without a second pair of eyes:",
    ]
    for row in risky_rows:
        lines.append(
            f"- `{row['Module']}` — risk {row['Risk score']}/100 "
            f"(depended on by {row['Fan-in (depended on by)']} module(s), "
            f"tests: {row['Has tests']})"
        )

    lines += [
        "",
        f"## Quick wins ({len(docs_missing)} missing docstrings, {len(tests_missing)} untested modules)",
        "Good first-week tasks — low risk, immediate value:",
    ]
    for mod, kind, name, lineno, end_lineno, file_path in docs_missing[:5]:
        lines.append(f"- Add a docstring to `{name}` ({kind}) in `{mod}`, line {lineno}")
    for mod in tests_missing[:5]:
        lines.append(f"- Write a first test for `{mod}`")

    lines += [
        "",
        "---",
        "_This brief was generated automatically. Once IBM Bob is connected, "
        "each section above will be replaced with a richer, narrated explanation._",
        "",
        "_Crafted by Hamna Munir — Repo Onboarding & Risk Assistant, built for the IBM Bob 2.0 Hackathon._",
    ]
    return "\n".join(lines)