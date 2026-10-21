"""Delivery helpers: PR-only landing, pause switch, open-PR cap.

Python does the deterministic parts. The agent opens the PR with its GitHub
connector, waits for CI, merges it if you allow that, and summarizes the digest
in chat.
"""

import re
from pathlib import Path


def label(run_date: str, interim: bool = False) -> str:
    """Return the file and branch label: DATE or DATE-interim."""
    return f"{run_date}-interim" if interim else run_date


def branch_name(prefix: str, run_date: str, interim: bool = False) -> str:
    """Return the delivery branch, e.g. ``example-bot/2026-10-19``."""
    return f"{prefix}{label(run_date, interim)}"


def pr_title(bot_name: str, run_date: str, counts: dict[str, int]) -> str:
    """Return the PR title for a digest."""
    return (
        f"{bot_name} digest {run_date} "
        f"({counts.get('advance', 0)} advance, {counts.get('watch', 0)} watch)"
    )


def skip_reason(
    repo: Path, bot_id: str, open_prs: int, max_open_prs: int
) -> str | None:
    """Return why this run must be skipped, or None.

    Args:
        repo: Repo checkout at origin/main.
        bot_id: The bot's directory name under ``bots/``.
        open_prs: Open PRs from this bot (counted by the agent).
        max_open_prs: Cap on stacked open PRs.
    """
    if (repo / "bots" / bot_id / "PAUSED").exists():
        return "PAUSED file present on main"
    if open_prs >= max_open_prs:
        return f"{open_prs} PRs already open (cap {max_open_prs})"
    return None


def add_log_row(
    note_text: str, run_date: str, digest_rel: str, counts: dict[str, int]
) -> str:
    """Append a Log row linking the digest and bump ``updated``.

    This also keeps the digest from being an orphan note.

    Args:
        note_text: Project note markdown (must have a Log table).
        run_date: YYYY-MM-DD.
        digest_rel: Link target relative to the project note.
        counts: Verdict counts.

    Returns:
        The updated markdown.
    """
    row = (
        f"| {run_date} | [Digest]({digest_rel}): {counts.get('advance', 0)} "
        f"advance, {counts.get('watch', 0)} watch |"
    )
    lines = [
        ln
        for ln in note_text.rstrip("\n").split("\n")
        if not (ln.startswith(f"| {run_date} |") and digest_rel in ln)
    ]
    text = "\n".join(lines) + "\n" + row + "\n"
    return re.sub(
        r"^updated: .*$", f"updated: {run_date}", text, count=1, flags=re.MULTILINE
    )
