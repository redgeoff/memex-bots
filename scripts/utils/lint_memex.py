"""Lint the memex: frontmatter, links, privacy patterns and consistency rules.

Usage:
    uv run python -m scripts.utils.lint_memex            # report, exit 1 on errors
    uv run python -m scripts.utils.lint_memex --strict   # warnings fail too

The rules are deliberately mechanical so they can run in CI. Judgement calls
(is this fact still true? which note owns it?) belong to the dreaming skill.
"""

import argparse
import fnmatch
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from scripts.utils import build_index
from scripts.utils.memex_notes import (
    Note,
    find_links,
    load_notes,
    resolve_link,
    split_frontmatter,
    strip_code,
)

REQUIRED_KEYS = ("date", "updated", "tags", "status", "summary", "sensitivity")
STATUSES = {"active", "draft", "archived"}
SENSITIVITIES = {"private", "usable", "public"}
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
UPPER_RE = re.compile(r"^[A-Z0-9]+(_[A-Z0-9]+)*$")
DATE_NAMED_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: Patterns that must never appear in any note (see AGENTS.md).
#: Phone numbers and other contact details are allowed on purpose; add a pattern
#: here if you want them blocked.
PRIVACY_PATTERNS: dict[str, str] = {
    "SSN": r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)",
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "AWS access key": r"AKIA[0-9A-Z]{16}",
    "credential assignment": (
        r"(?i)\b(password|passwd|api[_-]?key|secret)\s*[:=]\s*\S{6,}"
    ),
    "long account number": r"(?i)account\s*(number|no\.?|#)\s*[:=]?\s*\d{6,}",
}

#: Phrases that mean transient status leaked into a content note.
STALE_STATUS_RE = re.compile(
    r"(?i)\b(not yet (read|imported)|still unread|google docs? .{0,40}pending|"
    r"\(pending\)|todo: fill)\b"
)

#: Notes tagged with one of these may talk about import status.
STATUS_TAGS = {"ledger", "meta", "setup"}


@dataclass(frozen=True)
class Finding:
    """One lint finding.

    Attributes:
        severity: "error" or "warning".
        rel: Path of the file, relative to the repository root.
        line: 1-based line number, or 0 when not applicable.
        rule: Short rule identifier.
        message: Human-readable explanation.
    """

    severity: str
    rel: str
    line: int
    rule: str
    message: str

    def format(self) -> str:
        """Return a one-line, grep-friendly rendering."""
        loc = f"{self.rel}:{self.line}" if self.line else self.rel
        return f"{self.severity.upper():7} {loc}: [{self.rule}] {self.message}"


def _as_date(value: object) -> date | None:
    """Coerce a frontmatter date value to a date, or None."""
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


def check_frontmatter(note: Note) -> list[Finding]:
    """Check required keys and allowed values in a note's frontmatter."""
    out: list[Finding] = []
    if not note.has_frontmatter:
        return [
            Finding("error", note.rel, 1, "frontmatter", "missing frontmatter block")
        ]
    for key in REQUIRED_KEYS:
        if note.meta.get(key) in (None, "", []):
            out.append(Finding("error", note.rel, 1, "frontmatter", f"missing '{key}'"))
    status = note.meta.get("status")
    if status and status not in STATUSES:
        out.append(
            Finding(
                "error",
                note.rel,
                1,
                "frontmatter",
                f"status '{status}' not in {sorted(STATUSES)}",
            )
        )
    sens = note.meta.get("sensitivity")
    if sens and sens not in SENSITIVITIES:
        out.append(
            Finding(
                "error",
                note.rel,
                1,
                "frontmatter",
                f"sensitivity '{sens}' not in {sorted(SENSITIVITIES)}",
            )
        )
    for key in ("date", "updated"):
        if note.meta.get(key) and _as_date(note.meta[key]) is None:
            out.append(
                Finding(
                    "error", note.rel, 1, "frontmatter", f"'{key}' is not an ISO date"
                )
            )
    created, updated = (
        _as_date(note.meta.get("date")),
        _as_date(note.meta.get("updated")),
    )
    if created and updated and updated < created:
        out.append(
            Finding("warning", note.rel, 1, "frontmatter", "'updated' is before 'date'")
        )
    summary = str(note.meta.get("summary") or "")
    if summary and len(summary) > 220:
        out.append(
            Finding(
                "warning",
                note.rel,
                1,
                "frontmatter",
                "summary is over 220 characters; keep it to one line",
            )
        )
    if note.meta.get("tags") and not isinstance(note.meta["tags"], list):
        out.append(
            Finding("error", note.rel, 1, "frontmatter", "'tags' must be a list")
        )
    return out


def check_filename(note: Note) -> list[Finding]:
    """Check the file name follows the naming conventions."""
    stem = note.path.stem
    if stem in {"INDEX", "README", "CLAUDE"} or DATE_NAMED_RE.match(stem):
        return []
    if not (KEBAB_RE.match(stem) or UPPER_RE.match(stem)):
        return [
            Finding("warning", note.rel, 0, "naming", "file name is not kebab-case")
        ]
    return []


def check_links(note: Note, repo_root: Path) -> list[Finding]:
    """Check every relative link resolves to an existing file."""
    out = []
    for lineno, target, _anchor in find_links(note.body):
        if not resolve_link(note.path, target).exists():
            out.append(
                Finding(
                    "error",
                    note.rel,
                    lineno + note.offset,
                    "link",
                    f"broken link: {target}",
                )
            )
    return out


def check_privacy(note: Note) -> list[Finding]:
    """Check for patterns that the privacy rules forbid in notes."""
    out = []
    for lineno, line in enumerate(strip_code(note.body).splitlines(), start=1):
        for name, pattern in PRIVACY_PATTERNS.items():
            if re.search(pattern, line):
                out.append(
                    Finding(
                        "error",
                        note.rel,
                        lineno + note.offset,
                        "privacy",
                        f"looks like a {name}",
                    )
                )
    return out


def check_stale_status(note: Note) -> list[Finding]:
    """Flag transient import/status phrases in notes that are not ledgers."""
    if STATUS_TAGS & set(note.meta.get("tags") or []):
        return []
    out = []
    for lineno, line in enumerate(note.body.splitlines(), start=1):
        if STALE_STATUS_RE.search(line):
            out.append(
                Finding(
                    "warning",
                    note.rel,
                    lineno + note.offset,
                    "stale-status",
                    "transient status text; move it to the sources ledger",
                )
            )
    return out


def load_avoid_rules(repo_root: Path) -> list[dict]:
    """Load consistency rules from the ``avoid`` list in knowledge/decisions.md.

    Each rule is a mapping with ``pattern`` (regex), ``reason`` and an optional
    ``allow`` list of path globs where the pattern is acceptable.

    Args:
        repo_root: Repository root.

    Returns:
        List of rule dicts (empty if the file or key is missing).
    """
    path = repo_root / "knowledge" / "decisions.md"
    if not path.exists():
        return []
    meta, _body, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    rules = meta.get("avoid") or []
    return [r for r in rules if isinstance(r, dict) and r.get("pattern")]


def check_avoid_rules(note: Note, rules: list[dict]) -> list[Finding]:
    """Apply decision-derived 'avoid' patterns to one note."""
    out = []
    for rule in rules:
        if any(fnmatch.fnmatch(note.rel, g) for g in rule.get("allow", [])):
            continue
        regex = re.compile(rule["pattern"])
        for lineno, line in enumerate(note.body.splitlines(), start=1):
            if regex.search(line):
                out.append(
                    Finding(
                        "error",
                        note.rel,
                        lineno + note.offset,
                        "decision",
                        "contradicts a recorded decision: "
                        f"{rule.get('reason', rule['pattern'])}",
                    )
                )
    return out


def check_index_fresh(repo_root: Path, notes: list[Note]) -> list[Finding]:
    """Check knowledge/INDEX.md matches what the generator would produce."""
    index = repo_root / "knowledge" / "INDEX.md"
    expected = build_index.build_index(repo_root, notes)
    if not index.exists():
        return [
            Finding(
                "error",
                "knowledge/INDEX.md",
                0,
                "index",
                "INDEX.md is missing; run the dream skill",
            )
        ]
    if index.read_text(encoding="utf-8") != expected:
        return [
            Finding(
                "error",
                "knowledge/INDEX.md",
                0,
                "index",
                "INDEX.md is out of date; "
                "run `uv run python -m skills.dream.skill --fix`",
            )
        ]
    return []


def check_orphans(repo_root: Path, notes: list[Note]) -> list[Finding]:
    """Flag notes that no other note (or the index) links to."""
    linked: set[Path] = set()
    for note in notes:
        for _ln, target, _a in find_links(note.body):
            linked.add(resolve_link(note.path, target).resolve())
    index = repo_root / "knowledge" / "INDEX.md"
    if index.exists():
        for _ln, target, _a in find_links(index.read_text(encoding="utf-8")):
            linked.add(resolve_link(index, target).resolve())
    out = []
    for note in notes:
        if note.path.resolve() in linked or note.path.stem in {"INDEX", "CLAUDE"}:
            continue
        if DATE_NAMED_RE.match(note.path.stem):
            continue
        out.append(
            Finding("warning", note.rel, 0, "orphan", "no note links to this one")
        )
    return out


def lint(repo_root: Path) -> list[Finding]:
    """Run every lint rule over the repository.

    Args:
        repo_root: Repository root.

    Returns:
        All findings, sorted by file and line.
    """
    notes = load_notes(repo_root)
    rules = load_avoid_rules(repo_root)
    findings: list[Finding] = []
    for note in notes:
        if note.path.stem == "INDEX":
            continue
        findings += check_frontmatter(note)
        findings += check_filename(note)
        findings += check_links(note, repo_root)
        findings += check_privacy(note)
        findings += check_stale_status(note)
        findings += check_avoid_rules(note, rules)
    findings += check_index_fresh(repo_root, notes)
    findings += check_orphans(repo_root, [n for n in notes if n.path.stem != "INDEX"])
    return sorted(findings, key=lambda f: (f.rel, f.line, f.rule))


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point.

    Args:
        argv: Optional argument list (defaults to sys.argv).

    Returns:
        Process exit code: 1 if any error (or any warning with --strict).
    """
    parser = argparse.ArgumentParser(description="Lint the memex.")
    parser.add_argument("--strict", action="store_true", help="warnings fail too")
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    args = parser.parse_args(argv)
    findings = lint(args.root)
    for f in findings:
        print(f.format())
    errors = sum(f.severity == "error" for f in findings)
    warnings = len(findings) - errors
    print(f"\n{errors} error(s), {warnings} warning(s)")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
