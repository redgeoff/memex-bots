"""Bot template (hybrid architecture).

The agent routine searches and judges with its own tools and writes
``items.json`` and ``candidates.json`` into a run directory. This module
validates, scores, writes the digest and updates the project-note Log.
No network calls. Imports are relative, so copying the folder to
``bots/<bot_id>/`` works with no edits beyond ``config.yaml``.

Usage:
    uv run python -m bots.<bot_id>.skill --dry-run
    uv run python -m bots.<bot_id>.skill --run-dir DIR [--date D] [--open-prs N]
    uv run python -m bots._template.skill --run-dir examples/run --date 2026-10-19

Run directory:
    items.json       {"items": [Item...]}
    candidates.json  {"candidates": [{"id", "title"}...]}
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from bots._base import SkillResult, error, ok

from .delivery import add_log_row, branch_name, label, pr_title, skip_reason
from .digest import render_digest
from .llm import FileLLM
from .models import Candidate
from .scoring import score_candidate, valid_items, verdict

CONFIG_PATH = Path(__file__).with_name("config.yaml")
REPO_ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load the bot configuration.

    Args:
        path: Path to ``config.yaml``.

    Returns:
        The parsed configuration.
    """
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def run(
    run_dir: str | None = None,
    run_date: str | None = None,
    open_prs: int = 0,
    repo: str | None = None,
    dry_run: bool = False,
    config_path: str | None = None,
) -> SkillResult:
    """Process one run directory into a digest.

    Args:
        run_dir: Directory with the agent's JSON outputs.
        run_date: YYYY-MM-DD (default today).
        open_prs: Open PRs from this bot, counted by the agent.
        repo: Repo checkout to write into (default this repo).
        dry_run: Validate config and print the plan; write nothing.
        config_path: Alternate config file (used by tests).

    Returns:
        SkillResult whose output holds the digest path, counts, branch and PR
        title, or the reason the run was skipped.
    """
    cfg = load_config(Path(config_path) if config_path else CONFIG_PATH)
    bot, rc, dc = cfg["bot"], cfg["run"], cfg["delivery"]
    root = Path(repo) if repo else REPO_ROOT
    day = run_date or date.today().isoformat()

    reason = skip_reason(root, bot["id"], open_prs, dc["max_open_prs"])
    if reason:
        return ok({"skipped": reason})
    if dry_run:
        return ok(
            {
                "plan": f"{bot['name']} would read {run_dir or '<run-dir>'} "
                f"and write a digest for {day}"
            }
        )
    if not run_dir:
        return error("run_dir is required unless --dry-run")

    llm = FileLLM(Path(run_dir))
    try:
        raw_items = llm.complete_json("items")["items"]
        raw_cands = llm.complete_json("candidates")["candidates"]
    except (FileNotFoundError, KeyError, ValueError) as exc:
        return error(f"bad run directory: {exc}")

    items, dropped = valid_items(raw_items, rc["max_quote_words"])
    candidates: list[Candidate] = []
    for c in raw_cands:
        cand = Candidate(id=c["id"], title=c["title"])
        cand["score"] = score_candidate(cand, items)
        cand["verdict"] = verdict(
            cand["score"], rc["min_score_advance"], rc["min_score_watch"]
        )
        candidates.append(cand)

    problems = []
    if dropped:
        noun = "item" if dropped == 1 else "items"
        problems.append(f"{dropped} {noun} dropped (no URL or quote too long)")
    text = render_digest(bot["name"], day, candidates, items, problems)
    words = len(text.split("\n---\n", 1)[-1].split())
    if words > rc["max_digest_words"]:
        problems.append(f"digest is {words} words (limit {rc['max_digest_words']})")
        text = render_digest(bot["name"], day, candidates, items, problems)

    digest_dir = root / bot["digest_dir"]
    digest_dir.mkdir(parents=True, exist_ok=True)
    digest_path = digest_dir / f"digest-{label(day)}.md"
    digest_path.write_text(text, encoding="utf-8")

    counts = {
        v: sum(c["verdict"] == v for c in candidates)
        for v in ("advance", "watch", "drop")
    }
    note = root / bot["project_note"]
    if note.exists():
        rel = f"{Path(bot['digest_dir']).name}/{digest_path.name}"
        note.write_text(
            add_log_row(note.read_text(encoding="utf-8"), day, rel, counts),
            encoding="utf-8",
        )
    return ok(
        {
            "digest": str(digest_path.relative_to(root)),
            "counts": counts,
            "dropped": dropped,
            "branch": branch_name(dc["branch_prefix"], day),
            "pr_title": pr_title(bot["name"], day, counts),
        }
    )


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point.

    Args:
        argv: Arguments (default ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir")
    p.add_argument("--date")
    p.add_argument("--open-prs", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    result = run(a.run_dir, a.date, a.open_prs, dry_run=a.dry_run)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
