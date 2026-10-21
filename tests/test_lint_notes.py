"""Tests for scripts/lint_notes.py."""

from pathlib import Path

from scripts.lint_notes import check_frontmatter, lint, main, read_note

GOOD = (
    "---\ndate: 2026-10-01\nupdated: 2026-10-01\ntags: [project]\nstatus: active\n"
    'summary: "A note."\nsensitivity: private\n---\n\n# Note\n'
)


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_good_note_is_clean(tmp_path: Path) -> None:
    assert check_frontmatter(read_note(_write(tmp_path, "n.md", GOOD))) == []


def test_missing_frontmatter_reports_every_field(tmp_path: Path) -> None:
    problems = check_frontmatter(read_note(_write(tmp_path, "n.md", "# No meta\n")))
    assert len(problems) == 6


def test_bad_values_are_reported() -> None:
    meta = {
        "date": 1,
        "updated": 1,
        "tags": "x",
        "status": "done",
        "summary": "s",
        "sensitivity": "secret",
    }
    assert len(check_frontmatter(meta)) == 3


def test_lint_walks_knowledge_and_main_exit_codes(tmp_path: Path) -> None:
    _write(tmp_path, "knowledge/a.md", GOOD)
    assert lint(tmp_path) == [] and main([str(tmp_path)]) == 0
    _write(tmp_path, "knowledge/sub/b.md", "# bad\n")
    assert lint(tmp_path)[0].startswith("knowledge/sub/b.md: missing date")
    assert main([str(tmp_path)]) == 1


def test_repo_notes_are_clean() -> None:
    assert lint(Path(__file__).resolve().parents[1]) == []
