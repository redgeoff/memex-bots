"""Tests for scripts/utils/memex_notes.py."""

from pathlib import Path

import pytest

from scripts.tests.repo_factory import make_repo, note_text
from scripts.utils import memex_notes as mn


def test_split_frontmatter_parses_yaml_and_body() -> None:
    """Frontmatter is parsed and the body is returned separately."""
    meta, body, present = mn.split_frontmatter(
        "---\ntitle: x\ntags: [a, b]\n---\n\n# Hi\n"
    )
    assert present is True
    assert meta == {"title": "x", "tags": ["a", "b"]}
    assert body.strip() == "# Hi"


def test_split_frontmatter_without_block() -> None:
    """Text with no frontmatter reports it as absent."""
    meta, body, present = mn.split_frontmatter("# Just a heading\n")
    assert (meta, present) == ({}, False)
    assert body.startswith("# Just")


def test_split_frontmatter_invalid_yaml_does_not_raise() -> None:
    """Broken YAML yields empty metadata but still counts as present."""
    meta, _body, present = mn.split_frontmatter("---\nkey: [unclosed\n---\nbody\n")
    assert meta == {} and present is True


def test_find_links_ignores_external_anchors_and_code() -> None:
    """Only real relative links are returned, with line numbers."""
    text = (
        "[ok](a/b.md)\n"
        "[web](https://x.com/y.md)\n"
        "[mail](mailto:a@b.c)\n"
        "[anchor](#top)\n"
        "`[inline](nope.md)`\n"
        "```\n[fenced](nope2.md)\n```\n"
        "[with anchor](c.md#sec)\n"
    )
    assert mn.find_links(text) == [(1, "a/b.md", ""), (9, "c.md", "#sec")]


def test_note_title_words_and_offset(tmp_path: Path) -> None:
    """Title, word count and line offset come from the parsed note."""
    make_repo(tmp_path, {"knowledge/a.md": note_text("My Title", "one two three")})
    note = mn.read_note(tmp_path / "knowledge" / "a.md", tmp_path)
    assert note.title == "My Title"
    assert note.words >= 5
    assert note.offset == 8  # 6 frontmatter lines + delimiters + blank line


def test_load_notes_skips_archive_and_dreams(tmp_path: Path) -> None:
    """Archived notes and dream reports are not treated as live notes."""
    make_repo(
        tmp_path,
        {
            "knowledge/a.md": note_text("A"),
            "knowledge/_archive/old.md": note_text("Old"),
            "knowledge/dreams/2026-01-01.md": note_text("Dream"),
            "context/c.md": note_text("C"),
        },
    )
    rels = [n.rel for n in mn.load_notes(tmp_path)]
    assert rels == ["context/c.md", "knowledge/a.md"]
    assert len(mn.load_notes(tmp_path, include_skipped=True)) == 4


def test_move_note_rewrites_incoming_and_outgoing_links(tmp_path: Path) -> None:
    """Links to the moved note and from it are all rewritten."""
    make_repo(
        tmp_path,
        {
            "knowledge/ref/a.md": note_text("A", "[to b](b.md) and [to c](../c.md)"),
            "knowledge/ref/b.md": note_text("B", "[to a](a.md#part)"),
            "knowledge/c.md": note_text("C", "[to a](ref/a.md)"),
        },
    )
    changed = mn.move_note(
        tmp_path,
        tmp_path / "knowledge/ref/a.md",
        tmp_path / "knowledge/new/deep/a.md",
        use_git=False,
    )
    assert changed == 3
    moved = (tmp_path / "knowledge/new/deep/a.md").read_text(encoding="utf-8")
    assert "[to b](../../ref/b.md)" in moved and "[to c](../../c.md)" in moved
    assert "[to a](../new/deep/a.md#part)" in (
        tmp_path / "knowledge/ref/b.md"
    ).read_text(encoding="utf-8")
    assert "[to a](new/deep/a.md)" in (tmp_path / "knowledge/c.md").read_text(
        encoding="utf-8"
    )
    assert not (tmp_path / "knowledge/ref/a.md").exists()


def test_move_note_leaves_unaffected_links_alone(tmp_path: Path) -> None:
    """Links that still resolve are not touched, even if oddly written."""
    make_repo(
        tmp_path,
        {
            "knowledge/a.md": note_text("A"),
            "knowledge/b.md": note_text("B", "[to c](./c.md)"),
            "knowledge/c.md": note_text("C"),
        },
    )
    mn.move_note(
        tmp_path,
        tmp_path / "knowledge/a.md",
        tmp_path / "knowledge/z.md",
        use_git=False,
    )
    assert "[to c](./c.md)" in (tmp_path / "knowledge/b.md").read_text(encoding="utf-8")


def test_move_note_errors(tmp_path: Path) -> None:
    """Missing sources and existing destinations raise clear errors."""
    make_repo(
        tmp_path, {"knowledge/a.md": note_text("A"), "knowledge/b.md": note_text("B")}
    )
    with pytest.raises(FileNotFoundError):
        mn.move_note(
            tmp_path,
            tmp_path / "knowledge/none.md",
            tmp_path / "knowledge/x.md",
            use_git=False,
        )
    with pytest.raises(FileExistsError):
        mn.move_note(
            tmp_path,
            tmp_path / "knowledge/a.md",
            tmp_path / "knowledge/b.md",
            use_git=False,
        )
