"""Tests for scripts/utils/lint_memex.py."""

from pathlib import Path

from scripts.tests.repo_factory import make_repo, note_text
from scripts.utils import build_index, lint_memex


def _rules(findings: list[lint_memex.Finding]) -> set[tuple[str, str]]:
    """Reduce findings to (path, rule) pairs for easy assertions."""
    return {(f.rel, f.rule) for f in findings}


def _clean_repo(tmp_path: Path, extra: dict[str, str] | None = None) -> Path:
    """Build a repo with a fresh index, linked from the index."""
    files = {"knowledge/a.md": note_text("Alpha")}
    files.update(extra or {})
    root = make_repo(tmp_path, files)
    build_index.write_index(root)
    return root


def test_clean_repo_has_no_findings(tmp_path: Path) -> None:
    """A well-formed repo with a fresh index passes."""
    assert lint_memex.lint(_clean_repo(tmp_path)) == []


def test_missing_frontmatter_and_keys(tmp_path: Path) -> None:
    """Missing frontmatter and missing keys are errors."""
    root = _clean_repo(
        tmp_path,
        {
            "knowledge/nofm.md": "# No frontmatter\n",
            "knowledge/nosum.md": note_text("No summary", summary=None),
        },
    )
    found = lint_memex.lint(root)
    assert ("knowledge/nofm.md", "frontmatter") in _rules(found)
    assert any("summary" in f.message for f in found if f.rel == "knowledge/nosum.md")


def test_bad_values_are_errors(tmp_path: Path) -> None:
    """Unknown status or sensitivity values are rejected."""
    root = _clean_repo(
        tmp_path,
        {
            "knowledge/bad.md": note_text(
                "Bad", status="weird", sensitivity="secret", date="not-a-date"
            ),
        },
    )
    messages = " ".join(
        f.message for f in lint_memex.lint(root) if f.rel == "knowledge/bad.md"
    )
    assert "status" in messages and "sensitivity" in messages and "ISO date" in messages


def test_broken_link_reports_file_line(tmp_path: Path) -> None:
    """Broken links are errors and the line number counts the frontmatter."""
    root = _clean_repo(
        tmp_path, {"knowledge/l.md": note_text("L", "see [x](missing.md)")}
    )
    build_index.write_index(root)
    link = [f for f in lint_memex.lint(root) if f.rule == "link"]
    assert (
        len(link) == 1 and link[0].line == 12
    )  # 8 frontmatter lines, blank, heading, blank, then the body line


def test_privacy_patterns(tmp_path: Path) -> None:
    """Credential assignments are flagged; code spans and phone numbers are not."""
    root = _clean_repo(
        tmp_path,
        {
            "knowledge/p.md": note_text(
                "P",
                "call 206-555-0142\n"
                "password: hunter2hunter2\n"
                "`password: hunter2hunter2`",
            ),
        },
    )
    privacy = [f for f in lint_memex.lint(root) if f.rule == "privacy"]
    assert len(privacy) == 1 and privacy[0].line == 13


def test_stale_status_warns_unless_ledger(tmp_path: Path) -> None:
    """Transient status text is a warning, except in ledger-tagged notes."""
    root = _clean_repo(
        tmp_path,
        {
            "knowledge/s.md": note_text("S", "This is not yet read."),
            "knowledge/ledger.md": note_text(
                "Ledger", "This is not yet read.", tags="[ledger]"
            ),
        },
    )
    flagged = {f.rel for f in lint_memex.lint(root) if f.rule == "stale-status"}
    assert flagged == {"knowledge/s.md"}


def test_decision_rules_flag_contradictions_with_allow_list(tmp_path: Path) -> None:
    """Notes contradicting a recorded decision fail unless allow-listed."""
    decisions = (
        "---\ndate: 2026-01-01\nupdated: 2026-01-01\ntags: [decisions]\n"
        'status: active\nsummary: "Decisions."\nsensitivity: private\navoid:\n'
        "  - pattern: 'team of 4'\n    reason: 'team was 5'\n"
        "    allow: ['knowledge/hist.md']\n---\n\n# Decisions\n"
    )
    root = _clean_repo(
        tmp_path,
        {
            "knowledge/decisions.md": decisions,
            "knowledge/hist.md": note_text("Hist", "older notes said team of 4"),
            "knowledge/wrong.md": note_text("Wrong", "managed a team of 4"),
        },
    )
    flagged = {f.rel for f in lint_memex.lint(root) if f.rule == "decision"}
    assert flagged == {"knowledge/wrong.md"}


def test_stale_index_detected(tmp_path: Path) -> None:
    """A new note without regenerating the index is an error."""
    root = _clean_repo(tmp_path)
    make_repo(root, {"knowledge/new.md": note_text("New")})
    assert ("knowledge/INDEX.md", "index") in _rules(lint_memex.lint(root))


def test_orphan_note_warns(tmp_path: Path) -> None:
    """The index links every note, so only notes missing from it are orphans."""
    root = _clean_repo(tmp_path)
    (root / "knowledge" / "INDEX.md").write_text(
        (root / "knowledge" / "INDEX.md")
        .read_text(encoding="utf-8")
        .replace("(a.md)", "(none.md)"),
        encoding="utf-8",
    )
    assert ("knowledge/a.md", "orphan") in _rules(lint_memex.lint(root))


def test_naming_warning(tmp_path: Path) -> None:
    """Non-kebab names warn; UPPER_CASE and date names are fine."""
    root = _clean_repo(
        tmp_path,
        {
            "knowledge/Bad_Name.md": note_text("Bad"),
            "context/ABOUT_ME.md": note_text("About"),
            "knowledge/daily/2026-01-01.md": note_text("Day"),
        },
    )
    build_index.write_index(root)
    named = {f.rel for f in lint_memex.lint(root) if f.rule == "naming"}
    assert named == {"knowledge/Bad_Name.md"}


def test_main_exit_codes(tmp_path: Path, capsys) -> None:
    """main returns 1 on errors and 0 when clean."""
    clean = _clean_repo(tmp_path / "ok")
    assert lint_memex.main(["--root", str(clean)]) == 0
    bad = make_repo(tmp_path / "bad", {"knowledge/x.md": "# nothing\n"})
    assert lint_memex.main(["--root", str(bad)]) == 1
    assert "error(s)" in capsys.readouterr().out
