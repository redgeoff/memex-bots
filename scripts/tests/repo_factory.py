"""Helpers for building throwaway memex repositories in tests."""

from pathlib import Path

DEFAULT_META = {
    "date": "2026-01-01",
    "updated": "2026-01-01",
    "tags": "[test]",
    "status": "active",
    "summary": '"A test note."',
    "sensitivity": "private",
}


def note_text(title: str, body: str = "", **overrides: str) -> str:
    """Build a note with complete frontmatter.

    Args:
        title: Text of the level-1 heading.
        body: Markdown to put after the heading.
        **overrides: Frontmatter values to override; a value of None removes the key.

    Returns:
        The note's full text.
    """
    meta = {**DEFAULT_META, **overrides}
    lines = [f"{k}: {v}" for k, v in meta.items() if v is not None]
    return "---\n" + "\n".join(lines) + f"\n---\n\n# {title}\n\n{body}\n"


def make_repo(root: Path, files: dict[str, str]) -> Path:
    """Write files into a directory to act as a memex repository.

    Args:
        root: Directory to populate (usually pytest's tmp_path).
        files: Mapping of relative path to file contents.

    Returns:
        The repository root.
    """
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (root / "knowledge").mkdir(exist_ok=True)
    return root
