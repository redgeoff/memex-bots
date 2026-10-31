"""Tests for the dream skill (mechanical phase)."""

from datetime import date
from pathlib import Path

from scripts.tests.repo_factory import make_repo, note_text
from scripts.utils import build_index
from skills.dream import skill

ROSTER = "**Ada Lovelace** is mentioned. **Grace Hopper** too."


def _repo(tmp_path: Path, extra: dict[str, str] | None = None) -> Path:
    """Create a small repo with one note and a roster."""
    files = {
        "knowledge/a.md": note_text(
            "A",
            "- [ ] first open item\n- [x] done item\n"
            "Ada Lovelace wrote this. Ada Lovelace again. Ada Lovelace thrice.",
        ),
        "knowledge/people/roster.md": note_text("Roster", ROSTER),
    }
    files.update(extra or {})
    root = make_repo(tmp_path, files)
    build_index.write_index(root)
    return root


def test_run_reports_open_items_and_people(tmp_path: Path) -> None:
    """Open items and often-mentioned people without notes are surfaced."""
    root = _repo(tmp_path)
    result = skill.run(repo_root=root, today=date(2026, 1, 2))
    assert result["status"] == "ok"
    out = result["output"]
    assert [i["text"] for i in out["open_items"]] == ["first open item"]
    assert out["people"] == [{"name": "Ada Lovelace", "mentions": 3}]
    assert out["lint"]["errors"] == 0
    assert out["last_dream"] is None and len(out["changed"]) == 2


def test_existing_person_note_removes_candidate(tmp_path: Path) -> None:
    """Once a person has a note they are no longer a candidate."""
    root = _repo(tmp_path, {"knowledge/people/ada-lovelace.md": note_text("Ada")})
    build_index.write_index(root)
    out = skill.run(repo_root=root, today=date(2026, 1, 2))["output"]
    assert out["people"] == []


def test_stale_and_inbox_and_last_dream(tmp_path: Path) -> None:
    """Stale active notes, inbox files and the latest dream report are found."""
    root = _repo(
        tmp_path,
        {
            "knowledge/old.md": note_text("Old", updated="2025-01-01"),
            "knowledge/dreams/2026-01-01.md": note_text("Dream"),
            "inbox/idea.txt": "an idea",
            "inbox/.gitkeep": "",
        },
    )
    build_index.write_index(root)
    out = skill.run(repo_root=root, today=date(2026, 6, 1), stale_days=90)["output"]
    assert out["last_dream"] == {
        "path": "knowledge/dreams/2026-01-01.md",
        "date": "2026-01-01",
    }
    assert out["inbox"] == ["idea.txt"]
    assert {s["rel"] for s in out["stale"]} == {
        "knowledge/a.md",
        "knowledge/old.md",
        "knowledge/people/roster.md",
    }
    assert (
        out["changed"] == ["knowledge/old.md"] or out["changed"] == []
    )  # no git history in tmp dirs


def test_fix_regenerates_index(tmp_path: Path) -> None:
    """--fix rebuilds a stale index; without it lint reports the drift."""
    root = _repo(tmp_path)
    make_repo(root, {"knowledge/new.md": note_text("New")})
    drift = skill.run(repo_root=root)["output"]
    assert drift["lint"]["errors"] == 1
    fixed = skill.run(repo_root=root, fix=True)["output"]
    assert fixed["index"]["regenerated"] is True and fixed["lint"]["errors"] == 0


def test_missing_knowledge_folder_is_an_error(tmp_path: Path) -> None:
    """A directory without knowledge/ returns an error result."""
    assert skill.run(repo_root=tmp_path)["status"] == "error"


def test_render_and_main(tmp_path: Path, capsys, monkeypatch) -> None:
    """The text report and exit code reflect lint results."""
    root = _repo(tmp_path)
    monkeypatch.setattr(skill, "_REPO_ROOT", root)
    text = skill.render(skill.run(repo_root=root)["output"])
    assert "Dream (mechanical phase)" in text and "open items: 1" in text
    assert skill.main([]) == 0
    assert "lint: 0 error(s)" in capsys.readouterr().out
