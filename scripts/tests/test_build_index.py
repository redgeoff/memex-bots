"""Tests for scripts/utils/build_index.py."""

from pathlib import Path

from scripts.tests.repo_factory import make_repo, note_text
from scripts.utils import build_index


def test_index_lists_notes_by_section(tmp_path: Path) -> None:
    """Each note appears under its folder's section with its summary."""
    root = make_repo(
        tmp_path,
        {
            "knowledge/reference/facts.md": note_text(
                "Facts", summary='"Handy facts."', sensitivity="usable"
            ),
            "knowledge/projects/p.md": note_text("Project P"),
            "context/ABOUT_ME.md": note_text("About Me"),
        },
    )
    text = build_index.build_index(root)
    assert "## Reference" in text and "## Projects" in text and "## Context" in text
    assert "[Facts](reference/facts.md) | Handy facts. | usable" in text
    assert "[About Me](../context/ABOUT_ME.md)" in text


def test_index_is_deterministic_and_excludes_itself(tmp_path: Path) -> None:
    """Writing twice changes nothing the second time, and INDEX is not listed."""
    root = make_repo(tmp_path, {"knowledge/a.md": note_text("A")})
    assert build_index.write_index(root) is True
    assert build_index.write_index(root) is False
    assert (
        "INDEX.md)"
        not in (root / "knowledge" / "INDEX.md")
        .read_text(encoding="utf-8")
        .split("## ", 1)[1]
    )


def test_daily_notes_are_summarized_not_listed(tmp_path: Path) -> None:
    """Daily notes are collapsed to a count and the newest date."""
    root = make_repo(
        tmp_path,
        {
            "knowledge/daily/2026-01-01.md": note_text("Day 1"),
            "knowledge/daily/2026-01-05.md": note_text("Day 5"),
        },
    )
    text = build_index.build_index(root)
    assert "2 note(s)" in text and "newest: 2026-01-05" in text
    assert "[Day 1]" not in text


def test_unknown_folder_falls_back_to_nearest_section(tmp_path: Path) -> None:
    """A note in a nested, unlisted folder lands in its closest known section."""
    root = make_repo(tmp_path, {"knowledge/projects/zzz/deep.md": note_text("Deep")})
    assert "## Projects" in build_index.build_index(root)
