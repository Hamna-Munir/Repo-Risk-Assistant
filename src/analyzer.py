"""
Core repo analysis engine.

This works TODAY using pure Python `ast` parsing — no external AI needed.
Once IBM Bob access is available, `bob_client.py` wraps this raw data into
a natural-language narrative (architecture summary, risk explanations,
auto-drafted docstrings/tests). Until then, the app runs fully on this
module so you always have a working demo.
"""

import ast
import os
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class ModuleInfo:
    path: str
    imports: list = field(default_factory=list)          # modules this file imports
    functions: list = field(default_factory=list)         # (name, has_docstring, lineno, end_lineno)
    classes: list = field(default_factory=list)            # (name, has_docstring, lineno, end_lineno)
    has_test_file: bool = False
    fan_in: int = 0                                         # how many other modules import this one
    loc: int = 0


def _module_name_from_path(root: str, path: str) -> str:
    rel = os.path.relpath(path, root)
    rel = rel[:-3] if rel.endswith(".py") else rel
    return rel.replace(os.sep, ".")


def _find_test_file_for(module_path: str, all_files: list) -> bool:
    base = os.path.splitext(os.path.basename(module_path))[0]
    candidates = {f"test_{base}.py", f"{base}_test.py"}
    for f in all_files:
        if os.path.basename(f) in candidates:
            return True
    return False


def scan_repo(root_dir: str) -> dict:
    """
    Walks a local repo directory, parses every .py file with `ast`,
    and returns a dict of ModuleInfo keyed by module name.
    """
    root_dir = os.path.abspath(root_dir)
    py_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # skip hidden directories (.git, .venv, etc.) without skipping the root itself
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("__pycache__", "node_modules")]
        for fname in filenames:
            if fname.endswith(".py"):
                py_files.append(os.path.join(dirpath, fname))

    modules: dict[str, ModuleInfo] = {}

    for path in py_files:
        mod_name = _module_name_from_path(root_dir, path)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
            tree = ast.parse(source, filename=path)
        except (SyntaxError, UnicodeDecodeError):
            continue

        info = ModuleInfo(path=path)
        info.loc = source.count("\n") + 1
        info.has_test_file = _find_test_file_for(path, py_files)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    info.imports.append(alias.name)          # e.g. "src.analyzer"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    info.imports.append(node.module)           # e.g. "src.analyzer"
            elif isinstance(node, ast.FunctionDef):
                has_doc = ast.get_docstring(node) is not None
                info.functions.append((node.name, has_doc, node.lineno, getattr(node, "end_lineno", node.lineno)))
            elif isinstance(node, ast.ClassDef):
                has_doc = ast.get_docstring(node) is not None
                info.classes.append((node.name, has_doc, node.lineno, getattr(node, "end_lineno", node.lineno)))

        modules[mod_name] = info

    # compute fan-in: how many other local modules import each module.
    # Matches on full dotted name first (e.g. "src.analyzer"), then falls
    # back to the last segment (e.g. "analyzer") for bare `from x import y` style.
    local_names = set(modules.keys())
    short_to_full: dict[str, str] = {}
    for name in local_names:
        short_to_full.setdefault(name.split(".")[-1], name)

    for info in modules.values():
        seen_targets = set()
        for imp in info.imports:
            target = imp if imp in local_names else short_to_full.get(imp.split(".")[-1])
            if target and target in modules and target not in seen_targets:
                modules[target].fan_in += 1
                seen_targets.add(target)

    return modules


def risk_score(info: ModuleInfo) -> int:
    """
    Simple, explainable risk heuristic (0-100):
    - high fan-in (many things depend on it) = risky to change
    - large file size = harder to reason about
    - no test file = no safety net
    """
    score = 0
    score += min(info.fan_in * 15, 60)         # up to 60 pts for being widely depended-on
    score += min(info.loc // 50, 20)            # up to 20 pts for size
    score += 20 if not info.has_test_file else 0
    return min(score, 100)


def missing_docs_report(modules: dict) -> list:
    """Returns a flat list of (module, kind, name, lineno, end_lineno, file_path) missing a docstring."""
    missing = []
    for mod_name, info in modules.items():
        for name, has_doc, lineno, end_lineno in info.functions:
            if not has_doc:
                missing.append((mod_name, "function", name, lineno, end_lineno, info.path))
        for name, has_doc, lineno, end_lineno in info.classes:
            if not has_doc:
                missing.append((mod_name, "class", name, lineno, end_lineno, info.path))
    return missing


def read_source_snippet(file_path: str, start_line: int, end_line: int, max_lines: int = 25) -> str:
    """Reads the exact source lines for a function/class, for passing as real context to Bob."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        end_line = min(end_line, start_line + max_lines - 1)
        snippet = "".join(lines[start_line - 1:end_line])
        return snippet.rstrip()
    except (OSError, IndexError):
        return ""


def missing_tests_report(modules: dict) -> list:
    """Modules with no matching test_*.py / *_test.py file."""
    return [mod for mod, info in modules.items() if not info.has_test_file]


def build_summary(modules: dict) -> dict:
    total_loc = sum(m.loc for m in modules.values())
    total_functions = sum(len(m.functions) for m in modules.values())
    total_classes = sum(len(m.classes) for m in modules.values())
    ranked_by_fanin = sorted(modules.items(), key=lambda kv: kv[1].fan_in, reverse=True)
    return {
        "module_count": len(modules),
        "total_loc": total_loc,
        "total_functions": total_functions,
        "total_classes": total_classes,
        "most_depended_on": ranked_by_fanin[:5],
    }