"""Skill: dream

The mechanical half of the memex "dreaming" cycle: lint the notes, rebuild the
index and gather everything a reflective pass needs (what changed since the
last dream, open items, stale notes, orphans, inbox items, people who deserve a
note). It never rewrites note content; Claude does the reflective half by
following skills/dream/README.md.

Usage:
    uv run python -m skills.dream.skill            # report only
    uv run python -m skills.dream.skill --fix      # also regenerate INDEX.md
    uv run python -m skills.dream.skill --json     # machine-readable

Returns a SkillResult (see skills/_base.py for the contract).
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.utils import build_index, lint_memex  # noqa: E402
from scripts.utils.memex_notes import Note, load_notes  # noqa: E402
from skills._base import SkillResult, error, ok  # noqa: E402

OPEN_ITEM_RE = re.compile(r"^\s*[-*] \[ \] (?P<text>.+)$")
BOLD_NAME_RE = re.compile(r"\*\*(?P<name>[A-Z][a-z]+(?: [A-Z][A-Za-z.\-']+)+)\*\*")


def _as_date(value: Any) -> date | None:
    """Coerce a frontmatter value to a date, or None."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def latest_dream(repo_root: Path) -> dict[str, str] | None:
    """Find the most recent dream report.

    Args:
        repo_root: Repository root.

    Returns:
        Dict with the report's ``path`` and ``date``, or None if there is none.
    """
    reports = sorted((repo_root / "knowledge" / "dreams").glob("????-??-??*.md"))
    if not reports:
        return None
    last = reports[-1]
    return {"path": last.relative_to(repo_root).as_posix(), "date": last.stem[:10]}


def changed_notes(repo_root: Path, since: str | None, notes: list[Note]) -> list[str]:
    """List notes changed since a date, using git history when available.

    Args:
        repo_root: Repository root.
        since: ISO date of the last dream, or None for "everything".
        notes: All parsed notes.

    Returns:
        Sorted relative paths of changed notes.
    """
    note_paths = {n.rel for n in notes}
    if since is None:
        return sorted(note_paths)
    try:
        out = subprocess.run(
            ["git", "log", f"--since={since} 23:59", "--name-only", "--pretty=format:"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return sorted(
            {line.strip() for line in out.splitlines() if line.strip() in note_paths}
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        cutoff = date.fromisoformat(since)
        return sorted(
            n.rel
            for n in notes
            if (_as_date(n.meta.get("updated")) or date.min) > cutoff
        )


def open_items(notes: list[Note]) -> list[dict[str, Any]]:
    """Collect unchecked ``- [ ]`` items across notes."""
    items = []
    for note in notes:
        for lineno, line in enumerate(note.body.splitlines(), start=1):
            m = OPEN_ITEM_RE.match(line)
            if m:
                items.append(
                    {
                        "rel": note.rel,
                        "line": lineno + note.offset,
                        "text": m.group("text")[:160],
                    }
                )
    return items


def stale_notes(
    notes: list[Note], today: date, stale_days: int
) -> list[dict[str, Any]]:
    """List active notes not updated within ``stale_days`` days."""
    cutoff = today - timedelta(days=stale_days)
    out = []
    for note in notes:
        updated = _as_date(note.meta.get("updated"))
        if note.meta.get("status") == "active" and updated and updated < cutoff:
            out.append({"rel": note.rel, "updated": updated.isoformat()})
    return out


def inbox_items(repo_root: Path) -> list[str]:
    """List files waiting in inbox/ (excluding .gitkeep)."""
    inbox = repo_root / "inbox"
    if not inbox.exists():
        return []
    return sorted(
        p.name for p in inbox.iterdir() if p.is_file() and p.name != ".gitkeep"
    )


def people_candidates(
    repo_root: Path, notes: list[Note], min_mentions: int = 3
) -> list[dict[str, Any]]:
    """Find people named in bold in the roster who are mentioned often elsewhere.

    A person who appears in at least ``min_mentions`` notes' text (counting
    every mention) but has no note of their own is a candidate for a note in
    knowledge/people/.

    Args:
        repo_root: Repository root.
        notes: All parsed notes.
        min_mentions: Mention threshold.

    Returns:
        List of dicts with ``name`` and ``mentions``, most-mentioned first.
    """
    roster = repo_root / "knowledge" / "people" / "roster.md"
    if not roster.exists():
        return []
    names = sorted(
        {
            m.group("name")
            for m in BOLD_NAME_RE.finditer(roster.read_text(encoding="utf-8"))
        }
    )
    existing = {p.stem for p in (repo_root / "knowledge" / "people").glob("*.md")}
    corpus = "\n".join(n.body for n in notes if n.path.resolve() != roster.resolve())
    out = []
    for name in names:
        slug = name.lower().replace(" ", "-")
        count = corpus.count(name)
        if count >= min_mentions and slug not in existing:
            out.append({"name": name, "mentions": count})
    return sorted(out, key=lambda d: -d["mentions"])


def run(
    repo_root: Path | None = None,
    fix: bool = False,
    today: date | None = None,
    stale_days: int = 90,
) -> SkillResult:
    """Run the mechanical dreaming phase.

    Args:
        repo_root: Repository root (defaults to this repo).
        fix: If True, regenerate knowledge/INDEX.md before linting.
        today: Override today's date (for tests).
        stale_days: Days without an update before an active note is stale.

    Returns:
        SkillResult whose output holds ``lint``, ``index``, ``last_dream``,
        ``changed``, ``open_items``, ``stale``, ``inbox`` and ``people``.
    """
    root = (repo_root or _REPO_ROOT).resolve()
    if not (root / "knowledge").exists():
        return error(f"no knowledge/ folder under {root}")
    today = today or date.today()
    index_changed = build_index.write_index(root) if fix else None
    notes = [n for n in load_notes(root) if n.path.name != "INDEX.md"]
    findings = lint_memex.lint(root)
    last = latest_dream(root)
    output = {
        "today": today.isoformat(),
        "last_dream": last,
        "index": {"regenerated": index_changed},
        "lint": {
            "errors": sum(f.severity == "error" for f in findings),
            "warnings": sum(f.severity == "warning" for f in findings),
            "findings": [f.format() for f in findings],
        },
        "changed": changed_notes(root, last["date"] if last else None, notes),
        "open_items": open_items(notes),
        "stale": stale_notes(notes, today, stale_days),
        "inbox": inbox_items(root),
        "people": people_candidates(root, notes),
        "stats": {"notes": len(notes), "words": sum(n.words for n in notes)},
    }
    return ok(output)


def render(output: dict[str, Any]) -> str:
    """Render the skill output as a short human-readable report."""
    lint = output["lint"]
    last = output["last_dream"]
    lines = [
        f"Dream (mechanical phase), {output['today']}",
        f"  notes: {output['stats']['notes']}, words: {output['stats']['words']:,}",
        f"  last dream: {last['date'] if last else 'never'}",
        f"  lint: {lint['errors']} error(s), {lint['warnings']} warning(s)",
    ]
    lines += [f"    {f}" for f in lint["findings"][:30]]
    lines.append(f"  changed since last dream: {len(output['changed'])} note(s)")
    lines.append(f"  open items: {len(output['open_items'])}")
    lines.append(f"  stale active notes: {len(output['stale'])}")
    lines.append(f"  inbox items: {len(output['inbox'])}")
    if output["people"]:
        lines.append(
            "  people mentioned often without a note: "
            + ", ".join(f"{p['name']} ({p['mentions']})" for p in output["people"][:10])
        )
    if output["index"]["regenerated"] is not None:
        lines.append(f"  INDEX.md regenerated: {output['index']['regenerated']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point; returns 1 if lint errors remain."""
    parser = argparse.ArgumentParser(
        description="Mechanical phase of the memex dream cycle."
    )
    parser.add_argument(
        "--fix", action="store_true", help="regenerate knowledge/INDEX.md"
    )
    parser.add_argument(
        "--json", action="store_true", help="print JSON instead of text"
    )
    args = parser.parse_args(argv)
    result = run(fix=args.fix)
    if result["status"] != "ok":
        print(result["error"], file=sys.stderr)
        return 2
    print(
        json.dumps(result["output"], indent=2)
        if args.json
        else render(result["output"])
    )
    return 1 if result["output"]["lint"]["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
