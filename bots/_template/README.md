# Bot template

A working skeleton for a **bot**: a scheduled worker that researches something with an
AI agent's own tools and delivers a short digest to your repo by pull request.

## Start here

1. Run `/new-bot <name>` in Claude Code (see `.claude/commands/new-bot.md`), or follow
   the steps below by hand.
2. Fill in [`docs/bot-spec-template.md`](../../docs/bot-spec-template.md) first and
   answer its open questions. The spec is the brief; code comes second.
3. Copy this folder to `bots/<bot_id>/` (snake_case) and edit `config.yaml`. Imports are
   relative, so nothing else needs renaming.
4. Replace every `TODO(bot)`: the `Item` and `Candidate` models, the rubric in
   `scoring.py`, the digest sections.
5. Copy [`BOT.md`](./BOT.md) to `bots/<bot_id>/BOT.md` and fill it in. It is the bot's
   canonical profile, and **the bot must keep it current by PR whenever its setup,
   routines, access or decisions change.**
6. Create the project note `knowledge/projects/<bot-id>.md` with a `## Log` table (copy
   [example-bot.md](../../knowledge/projects/example-bot.md)).
7. Run the checks below and land it by PR.

## Architecture (hybrid)

```
agent routine (its own search/fetch tools + judgment)
        │ writes JSON
        ▼
<run_dir>/items.json, candidates.json
        │ read by FileLLM (no network in code)
        ▼
skill.py: validate (citation rule) → score (pure code) → verdict → digest → Log row
        │
        ▼
agent: branch, commit, open PR, wait for CI, merge if allowed, summarize in chat
```

Rules that make bots safe to leave alone:

- **Code is deterministic.** Scores and verdicts come from stored fields, never from the
  model, so they are reproducible.
- **Citation rule.** Every item needs a URL and a short quote; anything else is dropped
  and counted.
- **PR only.** Never commit to `main`. The digest and one Log row land together, so the
  digest is never an orphan note.
- **Pause and cap.** A file `bots/<bot_id>/PAUSED` on `main` skips runs; at
  `max_open_prs` unmerged PRs the run opens nothing.
- **Fail loudly.** A failed run still opens a PR with a "Run problems" section; never
  retry more than twice a week.
- **Attention budget.** State in the spec how many minutes a week the digest may cost
  you.

## Security and credentials

A bot works unattended, so its credentials are its blast radius.

- **One token per bot:** a fine-grained GitHub token limited to your memex repo, with
  only *Contents: read/write* and *Pull requests: read/write*. Never a classic token,
  never an account-wide one, never shared between bots.
- **Set an expiry** (90 days or less) and record the date and the rotation steps in the
  bot's README. An expired token should fail loudly in the run's "Run problems" section.
- **Keep the token out of Python and the repo.** The agent's GitHub connector opens (and,
  if you allow it, merges) the PR; code only does local git. Secrets come from the host's secret store;
  list their names, never their values.
- **A token that can write contents can push to `main`.** "Never push to `main`" must be
  enforced, not just promised: keep a branch ruleset on `main` that requires a pull
  request and passing CI (Settings → Rules), and don't let the bot's token bypass it.
- **Limit the paths a bot writes** to its digest directory, its project note and its own
  state, and say so in the spec.
- **Least outside access:** public APIs with no key where possible; no logged-in sites;
  no paid APIs without your approval.
- **If a token leaks or a run misbehaves:** add `bots/<bot_id>/PAUSED` by PR, revoke the
  token, then rotate.

## Files

| File | Job |
|------|-----|
| `config.yaml` | Bot id, paths, thresholds, delivery settings |
| `models.py` | `Item`, `Candidate` types |
| `llm.py` | `FileLLM`: serves the agent's JSON files |
| `scoring.py` | Citation rule, score, verdict |
| `digest.py` | Digest markdown with lint-clean frontmatter |
| `delivery.py` | Branch and PR names, PAUSED and PR-cap check, Log row |
| `skill.py` | `run()` and CLI (`--dry-run`, `--run-dir`, `--date`, `--open-prs`) |
| `tests/test_skill.py` | Offline tests to copy and extend |

## Definition of done

- [ ] Spec filled in and its open questions answered (recorded in the spec)
- [ ] Tests cover the verdict branches, citation rule, PAUSED and PR cap, digest lint and
      Log row, with **no network**
- [ ] `uv run pytest` and `uv run python -m scripts.lint_notes` pass
- [ ] The bot's README says how it is scheduled, where secrets live, and how to pause it
- [ ] `bots/<bot_id>/BOT.md` filled in and kept current by PR
- [ ] Security section followed; token expiry date recorded
- [ ] Out-of-scope list written (no contacting anyone, no posting, no logged-in sites)
