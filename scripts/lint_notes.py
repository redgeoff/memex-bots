"""Minimal note linter: every note under ``knowledge/`` needs valid frontmatter.

A memex is only useful if every note says what it is, when it changed and how
private it is. This is the smallest useful version of that check; a real memex
can add link checks, privacy patterns and rules from a decisions log.

Usage:
    uv run python -m scripts.lint_notes [ROOT]
"""

import sys
from pathlib import Path
from typing import Any

import yaml

REQUIRED = ("date", "updated", "tags", "status", "summary", "sensitivity")
STATUSES = ("active", "draft", "archived")
SENSITIVITIES = ("private", "usable", "public")


def read_note(path: Path) -> dict[str, Any]:
    """Return a note's frontmatter as a dict (empty if it has none).

    Args:
        path: Markdown file.

    Returns:
        The parsed frontmatter, or ``{}`` when the file has no frontmatter block.
    """
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    meta = yaml.safe_load(text[4:end]) or {}
    return meta if isinstance(meta, dict) else {}


def check_frontmatter(meta: dict[str, Any]) -> list[str]:
    """List the problems with one note's frontmatter.

    Args:
        meta: Parsed frontmatter.

    Returns:
        Human-readable problems; empty when the note is clean.
    """
    problems = [f"missing {key}" for key in REQUIRED if key not in meta]
    if "status" in meta and meta["status"] not in STATUSES:
        problems.append(f"status must be one of {', '.join(STATUSES)}")
    if "sensitivity" in meta and meta["sensitivity"] not in SENSITIVITIES:
        problems.append(f"sensitivity must be one of {', '.join(SENSITIVITIES)}")
    if "tags" in meta and not isinstance(meta["tags"], list):
        problems.append("tags must be a list")
    return problems


def lint(root: Path) -> list[str]:
    """Lint every markdown note under ``root/knowledge``.

    Args:
        root: Repo root.

    Returns:
        One line per problem, prefixed with the note's path.
    """
    findings = []
    for path in sorted((root / "knowledge").rglob("*.md")):
        for problem in check_frontmatter(read_note(path)):
            findings.append(f"{path.relative_to(root)}: {problem}")
    return findings


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point.

    Args:
        argv: Optional ``[ROOT]`` (default: the current directory).

    Returns:
        Process exit code: 0 when clean, 1 otherwise.
    """
    args = sys.argv[1:] if argv is None else argv
    findings = lint(Path(args[0]) if args else Path.cwd())
    print("\n".join(findings) or "0 problems")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
