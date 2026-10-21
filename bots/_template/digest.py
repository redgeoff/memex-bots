"""Digest writer: memex frontmatter, short body, every claim linked."""

from .models import Candidate, Item


def render_digest(
    bot_name: str,
    run_date: str,
    candidates: list[Candidate],
    items: list[Item],
    problems: list[str] | None = None,
) -> str:
    """Render one digest as markdown that passes the note lint (scripts/lint_notes.py).

    Args:
        bot_name: Human name of the bot.
        run_date: YYYY-MM-DD.
        candidates: Scored candidates with verdicts.
        items: Valid evidence.
        problems: Run problems to list, if any.

    Returns:
        Markdown text with frontmatter.
    """
    counts = {
        v: sum(c["verdict"] == v for c in candidates)
        for v in ("advance", "watch", "drop")
    }
    lines = [
        "---",
        f"date: {run_date}",
        f"updated: {run_date}",
        "tags: [digest, bot]",
        "status: active",
        (
            f'summary: "{bot_name} digest for {run_date}: {counts["advance"]} '
            f'advance, {counts["watch"]} watch."'
        ),
        "sensitivity: private",
        "---",
        "",
        f"# {bot_name} digest {run_date}",
        "",
    ]
    for label, key in (("Advance", "advance"), ("Watch", "watch")):
        lines += [f"## {label}", ""]
        rows = [c for c in candidates if c["verdict"] == key]
        if not rows:
            lines += ["None this run.", ""]
        for c in rows:
            links = " ".join(
                f"[{n}]({i['url']})"
                for n, i in enumerate(
                    (i for i in items if i["candidate"] == c["id"]), start=1
                )
            )
            lines.append(f"- **{c['title']}** (score {c['score']}) {links}")
        lines.append("")
    dropped = counts["drop"]
    noun = "candidate" if dropped == 1 else "candidates"
    lines += ["## Dropped", "", f"{dropped} {noun}.", ""]
    if problems:
        lines += ["## Run problems", ""] + [f"- {p}" for p in problems] + [""]
    return "\n".join(lines)
