"""
IBM Bob adapter.

IMPORTANT: Bob is a CLI/IDE coding-agent tool (Bob Shell v2.x), NOT a
plain REST text-generation API. Non-interactive calls go through the
`bob run` subcommand, e.g.:

    bob run --accept-license --trust --mode ask "your prompt here"

Bob Shell v2.x reads the BOB_API_KEY environment variable
automatically — there is no --auth-method flag in v2.x (that was a
v1.x-only option).

If your API key is a "General" type key (scoped to the whole
subscription instance, not just one team), Bob also needs a team ID.
Set BOB_TEAM_ID in your .env in that case; "Inference" type keys don't
need it.

Setup (one-time, on this machine):
  1. Install Bob Shell:
       macOS/Linux: curl -fsSL https://bob.ibm.com/download/bobshell.sh | bash
       Windows:     powershell -ep Bypass 'irm -Uri "https://bob.ibm.com/download/bobshell.ps1" | iex'
     (Requires Node.js 22.15.0+.)
  2. Put your key in a local `.env` file (see .env.example):
       BOB_API_KEY=your-real-key-here
       BOB_TEAM_ID=your-team-id     # only if your key is type "General"

This module shells out to `bob run` for each request. If the `bob`
executable isn't installed, or the key isn't set, it falls back to a
local template so the app keeps working either way.
"""

import os
import shutil
import subprocess
from dotenv import load_dotenv

load_dotenv()  # reads .env in the project root, if present

BOB_API_KEY = os.environ.get("BOB_API_KEY")
BOB_TEAM_ID = os.environ.get("BOB_TEAM_ID")
BOB_AVAILABLE = bool(BOB_API_KEY)


def narrate(prompt: str, context: str) -> str:
    """
    Ask Bob Shell (or, until it's available, a local fallback) to turn
    raw analysis data into a short natural-language explanation.
    """
    if not BOB_AVAILABLE:
        return _local_fallback(prompt, context)

    # On Windows, npm-installed CLIs like `bob` are `.cmd` shims.
    # subprocess.run(["bob", ...]) with a bare name often can't find
    # those unless we resolve the real path first — shutil.which()
    # correctly checks PATHEXT (.CMD, .BAT, .EXE) so it works the same
    # on Windows, macOS, and Linux.
    bob_path = shutil.which("bob")
    if bob_path is None:
        return (
            "[Bob Shell not installed on this machine — install it with "
            "`curl -fsSL https://bob.ibm.com/download/bobshell.sh | bash` "
            "(or the PowerShell installer on Windows), then try again]\n\n"
            + _local_fallback(prompt, context)
        )

    full_prompt = f"{prompt}\n\nContext:\n{context}"
    env = {**os.environ, "BOB_API_KEY": BOB_API_KEY}

    command = [bob_path, "run", "--accept-license", "--trust", "--mode", "ask"]
    if BOB_TEAM_ID:
        command += ["--team-id", BOB_TEAM_ID]
    command.append(full_prompt)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return "[Bob Shell timed out]\n\n" + _local_fallback(prompt, context)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "team-id" in stderr.lower():
            stderr += " — set BOB_TEAM_ID in your .env if your key is a 'General' type key."
        return f"[Bob Shell error: {stderr[:300]}]\n\n" + _local_fallback(prompt, context)

    return _extract_final_answer(result.stdout) or _local_fallback(prompt, context)


def _extract_final_answer(raw_output: str) -> str:
    """
    Bob Shell's `pretty` output format is a full transcript — box-drawing
    separator lines, "User (n) <timestamp>", "Assistant (n) <timestamp>",
    tool-call logs, and a trailing "Task Summary" block. We only want the
    final assistant reply text, so this pulls out the last "Assistant"
    block (before any "Tool calls:" it made) and strips everything else.
    """
    import re

    # Blocks are separated by a run of box-drawing dash characters (─),
    # regardless of how many or what surrounds them.
    blocks = [b.strip() for b in re.split(r"─{3,}", raw_output) if b.strip()]

    last_assistant_text = None
    for block in blocks:
        lines = block.split("\n")
        if lines[0].strip().startswith("Assistant ("):
            body = "\n".join(lines[1:]).strip()
            # Drop a trailing "Tool calls:\n- toolname" section if present —
            # that belongs to an intermediate turn, not the final answer.
            body = re.split(r"\n\s*Tool calls:", body)[0].strip()
            if body:
                last_assistant_text = body

    if last_assistant_text:
        return last_assistant_text

    # Fallback: transcript shape didn't match (format changed, or this
    # really is already a plain reply) — just strip obvious log lines.
    clean_lines = [
        line for line in raw_output.splitlines()
        if line.strip("─ \t")
        and not line.strip().startswith((
            "User (", "Assistant (", "Tool (", "Tool calls:", "Tool:", "Args:",
            "Task Summary", "Total Cost:", "Total Duration:",
            "Assistant Messages:", "Tool Calls:", "Task ID:",
        ))
    ]
    return "\n".join(clean_lines).strip()


def _local_fallback(prompt: str, context: str) -> str:
    """A plain, honest fallback so the demo never breaks before Bob is wired up."""
    return (
        "[Local fallback — Bob not yet connected]\n"
        f"Prompt: {prompt}\n"
        f"Context preview: {context[:300]}..."
    )