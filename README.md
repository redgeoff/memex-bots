# memex-bots

A template for AI bots you can leave running: **every change lands by pull request.**

A bot here is a scheduled worker. An AI agent wakes it up, does the searching and the
judgment with its own tools, and hands plain JSON to a small Python pipeline. The
pipeline checks every claim for a source, scores it with ordinary code, writes a short
digest, and the agent delivers that digest to your repo as a pull request. Nothing a bot
does reaches `main` without passing CI, and nothing it scores depends on what the model
felt like that day.

It is called memex-bots because the bots deliver into a *memex*, Vannevar Bush's 1945
name for a personal store of "books, records, and communications" that can be consulted
"with exceeding speed and flexibility". Here the memex is a git repo of markdown notes;
`knowledge/` is a tiny example of one.

## The rules

1. **Hybrid split.** The agent finds and judges. Deterministic code validates, scores,
   decides and writes, offline and tested.
2. **Citation rule.** Every item needs a URL and a short quote, or it is dropped and
   counted.
3. **PR only.** One branch and one PR per run; the digest and a Log row land together.
4. **Pause and cap.** A `PAUSED` file stops a bot; a cap on open PRs stops a runaway.
5. **Fail loudly.** A failed run still opens a PR that says what went wrong.
6. **Spec first.** Every bot starts as a spec with a kill rule, an attention budget, an
   out-of-scope list and open questions.
7. **A profile the bot keeps current.** `BOT.md` records where the bot runs, its
   routines verbatim, its access and its decisions, so it can be rebuilt from scratch.

## Try it

```bash
git clone https://github.com/redgeoff/memex-bots.git
cd memex-bots
uv sync --all-extras
uv run pytest
uv run python -m bots._template.skill --run-dir examples/run --date 2026-10-19
```

The last command plays the agent's part with the JSON in `examples/run/`. It writes
[a digest](knowledge/projects/example-bot/digest-2026-10-19.md) and adds a row to the
Log in [the project note](knowledge/projects/example-bot.md). One item has no URL, so
the digest lists it under "Run problems" instead of quietly using it.

## Make your own bot

1. Copy this repo, or copy `bots/`, `docs/`, `scripts/` and `AGENTS.md` into your own
   notes repo.
2. In Claude Code, run `/new-bot <name and one-line purpose>`. Or follow
   [`bots/_template/README.md`](bots/_template/README.md) by hand: fill in
   [`docs/bot-spec-template.md`](docs/bot-spec-template.md), copy `bots/_template/`,
   replace every `TODO(bot)`.
3. Protect `main` with a ruleset that requires a pull request and passing CI, and give
   the bot a fine-grained token that can't bypass it (see
   [Security](bots/_template/README.md#security-and-credentials)).
4. Schedule the agent. Its routine prompt can be short: point it at `AGENTS.md` and the
   bot's spec, and tell it when to run.

## Running the bots

The bots are plain folders, so any agent that can run on a schedule, read and write
files, run a command and open a pull request can run them. I run mine with Grok Bot,
which comes with my Cursor subscription and has a headless browser. To control a bot
from your phone, see [docs/phone-control.md](docs/phone-control.md).

## Layout

```
AGENTS.md                  Rules every bot follows (read by the agent on each run)
bots/_template/            The skeleton: config, models, scoring, digest, delivery, tests
bots/_template/BOT.md      Profile template the bot keeps current
docs/bot-spec-template.md  The spec every bot starts from
docs/phone-control.md      Slack as a remote control
examples/run/              Sample agent output for the try-it run
knowledge/                 A tiny memex the example bot delivers into
scripts/lint_notes.py      Frontmatter lint for every note (runs in CI)
.claude/commands/new-bot.md  /new-bot for Claude Code
```

## License

MIT
