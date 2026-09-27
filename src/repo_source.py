"""Small helper for turning a GitHub URL into a local folder via `git clone`."""

import os
import shutil
import subprocess
import tempfile


def is_github_url(text: str) -> bool:
    return text.strip().startswith(("http://", "https://")) and "github.com" in text


def resolve_repo_source(path_or_url: str):
    """
    Returns (local_folder_path, error_message).
    - If given a local path, returns it as-is (after validating it exists).
    - If given a GitHub URL, clones it (shallow) into a temp folder and
      returns that folder's path.
    """
    path_or_url = path_or_url.strip()

    if is_github_url(path_or_url):
        dest = tempfile.mkdtemp(prefix="repo_scan_")
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", path_or_url, dest],
                capture_output=True,
                text=True,
                timeout=120,
            )
        except FileNotFoundError:
            return None, ("git is not installed on this machine, so I can't clone GitHub "
                          "URLs here. Paste a local folder path instead.")
        except subprocess.TimeoutExpired:
            shutil.rmtree(dest, ignore_errors=True)
            return None, "Cloning took too long (repo too large, or a network/access issue)."

        if result.returncode != 0:
            shutil.rmtree(dest, ignore_errors=True)
            stderr = result.stderr.strip()
            if "not found" in stderr.lower():
                return None, ("That repo wasn't found — check the URL, or it may be private "
                              "(private repos need auth, not supported in this demo yet).")
            return None, f"git clone failed: {stderr[:300]}"

        return dest, None

    if not os.path.isdir(path_or_url):
        return None, f"'{path_or_url}' is not a valid local folder, and it doesn't look like a GitHub URL either."

    return path_or_url, None