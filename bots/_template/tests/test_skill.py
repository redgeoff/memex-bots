"""Tests for the bot template. No network access (README: tests must be offline)."""

import json
from pathlib import Path

import pytest

from scripts.lint_notes import check_frontmatter, read_note

from .. import skill
from ..delivery import add_log_row, branch_name, pr_title, skip_reason
from ..scoring import valid_items, verdict

NOTE = (
    "---\ndate: 2026-10-01\nupdated: 2026-10-01\ntags: [project]\nstatus: active\n"
    'summary: "Example bot project note."\nsensitivity: private\n---\n\n'
    "# Example Bot\n\n## Log\n\n| Date | Entry |\n|------|-------|\n"
)


def _item(
    n: int,
    url: str = "https://example.com/{n}",
    quote: str = "a quote",
    source: str = "web",
    cand: str = "c1",
) -> dict:
    return {
        "id": f"e{n}",
        "url": url.format(n=n),
        "quote": quote,
        "source": source,
        "candidate": cand,
    }


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Fake repo root with the project note present."""
    note = tmp_path / "knowledge/projects/example-bot.md"
    note.parent.mkdir(parents=True)
    note.write_text(NOTE, encoding="utf-8")
    return tmp_path


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    """Agent-written run directory: one strong candidate, one weak one."""
    d = tmp_path / "run"
    d.mkdir()
    items = [
        _item(1, source="hn"),
        _item(2, source="web"),
        _item(3, source="gh"),
        _item(4, source="x"),
        _item(5, cand="c2", source="web"),
        _item(6, url="", cand="c2"),
        _item(7, quote="word " * 40, cand="c2"),
    ]
    (d / "items.json").write_text(json.dumps({"items": items}))
    (d / "candidates.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {"id": "c1", "title": "Strong one"},
                    {"id": "c2", "title": "Weak one"},
                ]
            }
        )
    )
    return d


def test_citation_rule_drops_bad_items() -> None:
    items = [_item(1), _item(2, url=""), _item(3, quote="w " * 30)]
    kept, dropped = valid_items(items, max_quote_words=25)
    assert [i["id"] for i in kept] == ["e1"] and dropped == 2


@pytest.mark.parametrize("score,expected", [(4, "advance"), (2, "watch"), (1, "drop")])
def test_verdict_thresholds(score: int, expected: str) -> None:
    assert verdict(score, advance=4, watch=2) == expected


def test_run_writes_digest_and_log(repo: Path, run_dir: Path) -> None:
    result = skill.run(str(run_dir), "2026-10-19", repo=str(repo))
    assert result["status"] == "ok"
    assert result["output"]["counts"] == {"advance": 1, "watch": 0, "drop": 1}
    assert result["output"]["dropped"] == 2
    digest = repo / "knowledge/projects/example-bot/digest-2026-10-19.md"
    assert "Strong one" in digest.read_text()
    note = (repo / "knowledge/projects/example-bot.md").read_text()
    assert "example-bot/digest-2026-10-19.md" in note
    assert "updated: 2026-10-19" in note


def test_digest_passes_lint_frontmatter(repo: Path, run_dir: Path) -> None:
    skill.run(str(run_dir), "2026-10-19", repo=str(repo))
    path = repo / "knowledge/projects/example-bot/digest-2026-10-19.md"
    assert check_frontmatter(read_note(path)) == []


def test_paused_file_and_pr_cap_skip_the_run(repo: Path, run_dir: Path) -> None:
    assert skill.run(str(run_dir), repo=str(repo), open_prs=3)["output"]["skipped"]
    paused = repo / "bots/example_bot/PAUSED"
    paused.parent.mkdir(parents=True)
    paused.write_text("")
    assert "PAUSED" in skill.run(str(run_dir), repo=str(repo))["output"]["skipped"]
    assert skip_reason(repo, "example_bot", 0, 3) == "PAUSED file present on main"


def test_bad_run_dir_is_an_error(repo: Path, tmp_path: Path) -> None:
    assert skill.run(str(tmp_path / "missing"), repo=str(repo))["status"] == "error"


def test_dry_run_writes_nothing(repo: Path) -> None:
    assert skill.run(dry_run=True, repo=str(repo))["status"] == "ok"
    assert not (repo / "knowledge/projects/example-bot").exists()


def test_branch_and_title_and_log_row_idempotent() -> None:
    assert branch_name("example-bot/", "2026-10-19") == "example-bot/2026-10-19"
    assert branch_name("b/", "2026-10-19", interim=True) == "b/2026-10-19-interim"
    counts = {"advance": 1, "watch": 2}
    assert pr_title("Example Bot", "2026-10-19", counts).endswith(
        "(1 advance, 2 watch)"
    )
    once = add_log_row(NOTE, "2026-10-19", "x/digest-2026-10-19.md", counts)
    twice = add_log_row(once, "2026-10-19", "x/digest-2026-10-19.md", counts)
    assert once == twice
