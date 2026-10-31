"""Shared helpers for reading, linking and moving memex notes.

Every other memex tool (lint, index, dreaming) builds on this module so that
frontmatter parsing and relative-link handling live in exactly one place.
"""

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

#: Folders whose markdown files are treated as notes.
NOTE_ROOTS = ("knowledge", "context")

#: Folders that are never indexed or linted as notes.
SKIP_DIRS = {"_archive", "dreams", ".git", ".venv", "node_modules"}

#: Matches inline markdown links: [text](target) and [text](target#anchor).
LINK_RE = re.compile(
    r"\[(?P<text>[^\]]*)\]\((?P<target>[^)\s]+?)(?P<anchor>#[^)\s]*)?\)"
)

_FRONTMATTER_RE = re.compile(r"\A---\n(?P<meta>.*?)\n---\n?(?P<body>.*)\Z", re.S)


@dataclass
class Note:
    """A parsed markdown note.

    Attributes:
        path: Absolute path to the file.
        rel: Path relative to the repository root, with forward slashes.
        meta: Parsed YAML frontmatter (empty if none).
        body: Markdown after the frontmatter.
        has_frontmatter: Whether a frontmatter block was found.
        offset: Number of file lines before the body (add to body line numbers).
    """

    path: Path
    rel: str
    meta: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    has_frontmatter: bool = False
    offset: int = 0

    @property
    def title(self) -> str:
        """Return the first level-1 heading, or the file stem."""
        for line in self.body.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return self.path.stem

    @property
    def words(self) -> int:
        """Return the approximate word count of the body."""
        return len(self.body.split())


def split_frontmatter(text: str) -> tuple[dict[str, Any], str, bool]:
    """Split a markdown document into frontmatter and body.

    Args:
        text: Full file contents.

    Returns:
        A tuple of (metadata dict, body text, whether frontmatter was present).
        Invalid YAML yields an empty dict but still reports frontmatter present.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text, False
    try:
        meta = yaml.safe_load(match.group("meta")) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, match.group("body"), True


def read_note(path: Path, repo_root: Path) -> Note:
    """Read and parse one note.

    Args:
        path: Path to the markdown file.
        repo_root: Repository root, used to compute the relative path.

    Returns:
        The parsed Note.
    """
    text = path.read_text(encoding="utf-8")
    meta, body, has_fm = split_frontmatter(text)
    rel = path.resolve().relative_to(repo_root.resolve()).as_posix()
    offset = text[: len(text) - len(body)].count("\n")
    return Note(
        path=path, rel=rel, meta=meta, body=body, has_frontmatter=has_fm, offset=offset
    )


def iter_note_paths(repo_root: Path, include_skipped: bool = False) -> list[Path]:
    """List note files under the note roots, sorted by path.

    Args:
        repo_root: Repository root.
        include_skipped: If True, also include files under skipped folders such
            as ``_archive`` and ``dreams``.

    Returns:
        Sorted list of markdown file paths.
    """
    paths: list[Path] = []
    for root_name in NOTE_ROOTS:
        root = repo_root / root_name
        if not root.exists():
            continue
        for path in root.rglob("*.md"):
            parts = set(path.relative_to(repo_root).parts)
            if not include_skipped and parts & SKIP_DIRS:
                continue
            paths.append(path)
    return sorted(paths)


def load_notes(repo_root: Path, include_skipped: bool = False) -> list[Note]:
    """Read every note under the note roots.

    Args:
        repo_root: Repository root.
        include_skipped: Include archived and dream-report notes.

    Returns:
        List of parsed notes.
    """
    return [
        read_note(p, repo_root) for p in iter_note_paths(repo_root, include_skipped)
    ]


def strip_code(text: str) -> str:
    """Blank out fenced code blocks and inline code, preserving line numbers.

    Args:
        text: Markdown text.

    Returns:
        Text of the same line structure with code replaced by spaces.
    """
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        out.append(
            ""
            if in_fence
            else re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), line)
        )
    return "\n".join(out)


def find_links(text: str) -> list[tuple[int, str, str]]:
    """Find relative markdown links in text.

    External links (http, https, mailto) and pure anchors are ignored.

    Args:
        text: Markdown text.

    Returns:
        List of (line number, target path, anchor including '#' or '').
    """
    found = []
    for lineno, line in enumerate(strip_code(text).splitlines(), start=1):
        for m in LINK_RE.finditer(line):
            target = m.group("target")
            if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            found.append((lineno, target, m.group("anchor") or ""))
    return found


def resolve_link(from_path: Path, target: str) -> Path:
    """Resolve a relative link target against the file that contains it.

    Args:
        from_path: Path of the file containing the link.
        target: The link target as written.

    Returns:
        Normalized absolute path the link points to.
    """
    return Path(os.path.normpath(from_path.parent / target))


def _relative(from_dir: Path, to_path: Path) -> str:
    """Return a posix relative path from a directory to a file."""
    return Path(os.path.relpath(to_path, from_dir)).as_posix()


def move_note(repo_root: Path, src: Path, dst: Path, use_git: bool = True) -> int:
    """Move a note and rewrite every relative link that is affected.

    Links in other markdown files that pointed at ``src`` are updated, and the
    moved file's own relative links are recomputed so they still resolve.

    Args:
        repo_root: Repository root.
        src: Current path of the note.
        dst: New path of the note.
        use_git: Use ``git mv`` so history follows the file.

    Returns:
        Number of files whose contents were rewritten (including the moved file).

    Raises:
        FileNotFoundError: If ``src`` does not exist.
        FileExistsError: If ``dst`` already exists.
    """
    src, dst = src.resolve(), dst.resolve()
    if not src.exists():
        raise FileNotFoundError(src)
    if dst.exists():
        raise FileExistsError(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Snapshot where every markdown file's links point before anything moves.
    md_files = [
        p.resolve()
        for p in repo_root.rglob("*.md")
        if not (set(p.relative_to(repo_root).parts) & {".git", ".venv"})
    ]

    if use_git:
        subprocess.run(["git", "mv", str(src), str(dst)], cwd=repo_root, check=True)
    else:
        src.rename(dst)

    rewritten = 0
    for original in md_files:
        current = dst if original == src else original
        text = current.read_text(encoding="utf-8")

        def fix(
            m: re.Match[str], original: Path = original, current: Path = current
        ) -> str:
            target = m.group("target")
            if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                return m.group(0)
            old_target = resolve_link(original, target)
            new_target = dst if old_target == src else old_target
            if new_target == old_target and current == original:
                return m.group(0)
            new_rel = _relative(current.parent, new_target)
            if new_rel == target:
                return m.group(0)
            return f"[{m.group('text')}]({new_rel}{m.group('anchor') or ''})"

        new_text = LINK_RE.sub(fix, text)
        if new_text != text:
            current.write_text(new_text, encoding="utf-8")
            rewritten += 1
    return rewritten
