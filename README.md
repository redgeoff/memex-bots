# memex-template

A template for a **memex**: one shared memory, in plain markdown, that every AI you use
can read and update, plus **bots** you can leave running that deliver into it by pull
request.

The name comes from Vannevar Bush's 1945 essay "As We May Think", where a memex is a
personal store of "books, records, and communications" that can be consulted "with
exceeding speed and flexibility". Here it's a git repo of markdown notes. Any AI that can
read files (Claude Code, Cursor, Codex, ChatGPT, Gemini or a bot you schedule) gets the
same context, and git keeps a record of every change, so you can see what an AI did and
undo it.

The stories behind it:
- [I built an AI bot to read our kids' school email. Here's what I'd tell you before you
  build one.](https://redgeoff.com/posts/school-email-bot/) (the bots)

This repo was called memex-bots until the memory half moved in; old links redirect here.

## Try it

You need [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/redgeoff/memex-template.git my-memex
cd my-memex
uv sync --all-extras
uv run pytest                               # test the scripts
uv run python -m scripts.utils.lint_memex   # lint the notes
uv run python -m skills.dream.skill         # the dream's mechanical report
uv run python -m bots._template.skill --run-dir examples/run --date 2026-10-19
```

The last command plays a bot agent's part with the JSON in `examples/run/`. It writes
[a digest](knowledge/projects/example-bot/digest-2026-10-19.md) and adds a row to the
Log in [the project note](knowledge/projects/example-bot.md). One item has no URL, so
the digest lists it under "Run problems" instead of quietly using it.

Or use **Use this template** on GitHub. Keep your copy **private**: it will hold your
notes.

## Part 1: the memory

### The rules

1. **A header on every note:** created and updated dates, tags, status, a one-line
   summary and a sensitivity level (`private`, `usable` or `public`).
2. **A generated index.** A script builds `knowledge/INDEX.md` from the headers, one
   line per note. An AI reads it first and opens only the notes it needs.
3. **A decisions log.** Each ruling you make about a fact or a wording gets a dated
   entry. Old entries are never edited; a new one says which it replaces.
4. **Decisions the checker enforces.** An `avoid` rule in the log makes the lint fail
   if a corrected fact creeps back in.
5. **A linter on every change:** headers, broken links, file names, anything that looks
   like a password or an access key, and a current index. It runs in CI.
6. **Changes by pull request**, so you see what an AI did before it sticks. Pull
   requests are also handy for feedback: comment on specific lines of a note and have
   the AI answer and push a new version.
7. **Archive, never delete.**
8. **A dream:** a regular cleanup pass where an AI promotes what's durable from the
   daily log, keeps one home for each fact, flags stale notes and asks you what only you
   can answer. See [skills/dream/README.md](skills/dream/README.md).

[AGENTS.md](AGENTS.md) holds the instructions every AI reads first. `CLAUDE.md` points to
it.

### Start your own

1. Fill in [context/ABOUT_ME.md](context/ABOUT_ME.md) and
   [context/PREFERENCES.md](context/PREFERENCES.md). A few lines each is enough.
2. Point an AI at the repo and ask it to add something. It should make a branch, add a
   note with a header, regenerate the index and open a pull request.
3. Record a decision the second time you correct the same fact.
4. Run a dream once you have a few dozen notes (`/dream` in Claude Code).

Don't design it all up front. Everyone's preferences differ, and the structure will
change as you use it. Over time it should hold your context and preferences, written
down. [Getting started](knowledge/reference/getting-started.md) has more, including
importing old documents. Delete the example bot's notes once you don't need them.

## Part 2: the bots (optional)

A bot is a scheduled worker. An AI agent wakes it up, does the searching and the
judgment with its own tools, and hands plain JSON to a small Python pipeline. The
pipeline checks every claim for a source, scores it with ordinary code, writes a short
digest into the memex, and the agent delivers that digest as a pull request. Nothing a
bot does reaches `main` without passing CI, and nothing it scores depends on what the
model felt like that day. If you only want the memory, delete `bots/`, `docs/` and
`examples/`.

### The rules

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

### Make your own bot

1. In Claude Code, run `/new-bot <name and one-line purpose>`. Or follow
   [`bots/_template/README.md`](bots/_template/README.md) by hand: fill in
   [`docs/bot-spec-template.md`](docs/bot-spec-template.md), copy `bots/_template/`,
   replace every `TODO(bot)`.
2. Protect `main` with a ruleset that requires a pull request and passing CI, and give
   the bot a fine-grained token that can't bypass it (see
   [Security](bots/_template/README.md#security-and-credentials)).
3. Schedule the agent. Its routine prompt can be short: point it at `AGENTS.md` and the
   bot's spec, and tell it when to run.

### Running the bots

The bots are plain folders, so any agent that can run on a schedule, read and write
files, run a command and open a pull request can run them. I run mine with Grok Bot,
which comes with my Cursor subscription and has a headless browser. To control a bot
from your phone, see [docs/phone-control.md](docs/phone-control.md).

## Layout

```
AGENTS.md               Instructions for every AI and every bot (CLAUDE.md points here)
context/                Who you are, your preferences and goals
knowledge/INDEX.md      Generated map of every note (never edit by hand)
knowledge/decisions.md  Dated rulings, plus the lint's `avoid` rules
knowledge/projects/     One note per project; the example bot's note and digest
knowledge/people/       A roster, plus a note for anyone who comes up often
knowledge/areas/        Ongoing parts of life (home, health, work)
knowledge/reference/    How things work, tools, how-tos
knowledge/sources/      Ledgers of what was imported from where
knowledge/daily/        Daily log, one file per day
knowledge/dreams/       One report per dream
scripts/utils/          Note parsing, the lint and the index builder
skills/dream/           The dream: a mechanical script plus the protocol an AI follows
bots/_template/         Bot skeleton: config, models, scoring, digest, delivery, tests
docs/                   The bot spec template and phone control
examples/run/           Sample agent output for the try-it run
.claude/commands/       /dream and /new-bot for Claude Code
.github/workflows/      Tests and lint on every push and pull request
```

## Related

Dreaming elsewhere:
[Anthropic's dreaming for Claude Managed Agents](https://claude.com/blog/new-in-claude-managed-agents),
[OpenClaw](https://docs.openclaw.ai/concepts/dreaming) and
[hermes-dreaming](https://hermes-agent.nousresearch.com/docs/plugins/hermes-dreaming).

## License

MIT. See [LICENSE](LICENSE).
