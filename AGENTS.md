# Instructions for AI agents

Read this first in every session. It applies to any AI working in this repo (Claude Code,
Cursor, Codex, ChatGPT, Gemini or a scheduled bot). `CLAUDE.md` points here. If you are
running a bot, also follow [Running a bot](#running-a-bot) below.

## What this repo is

A personal memex: one shared memory, in plain markdown, that every AI tool the owner uses
can read and update. Treat everything in it as private unless a note's `sensitivity`
says otherwise.

## Start of every session

1. Read [`knowledge/INDEX.md`](knowledge/INDEX.md). It lists every note with a one-line
   summary. Open only the notes you need.
2. Read [`context/ABOUT_ME.md`](context/ABOUT_ME.md) and
   [`context/PREFERENCES.md`](context/PREFERENCES.md). Preferences there override
   anything in this file.
3. Before stating a fact about the owner, check
   [`knowledge/decisions.md`](knowledge/decisions.md). A recorded decision beats any other
   document.

## Rules

1. **Change by pull request.** Work on a branch and open a PR. Never commit straight to
   `main`. Merge your own PR only where `context/PREFERENCES.md` allows it, and only after
   CI passes.
2. **Every note has a header** (frontmatter). See the format below. The lint fails
   without it.
3. **One home per fact.** Link to the note that owns a fact instead of restating it.
4. **Decisions are append-only.** Add a new entry to `knowledge/decisions.md` that says
   which one it replaces; never edit an old one. If a wrong wording must not come back,
   add an `avoid` rule.
5. **Archive, never delete.** Move old notes to an `_archive/` folder.
6. **Never invent facts.** If you don't know, ask. Cite a source or "<owner>, <date>" for
   new claims.
7. **Privacy.** Never store passwords, API keys, access tokens or account numbers.
   Never copy a `private` note's content into anything that leaves the repo.
8. **Before you finish:** regenerate the index and run the checks.

```bash
uv run python -m skills.dream.skill --fix   # regenerate knowledge/INDEX.md (after your last edit)
uv run python -m scripts.utils.lint_memex   # lint the notes
uv run pytest                               # test the scripts
```

## Note format

```markdown
---
date: YYYY-MM-DD          # created
updated: YYYY-MM-DD       # last meaningful change
tags: [tag1, tag2]
status: active            # active | draft | archived
summary: "One line: what this note covers and when to read it."
sensitivity: private      # private | usable | public
---

# Title
```

`sensitivity`: `private` = never leaves the memex; `usable` = may inform things the owner
writes, e.g. a resume or a blog post; `public` = already public. When unsure, use
`private`.

- File names are `kebab-case.md`; daily notes are `YYYY-MM-DD.md`.
- Link other notes with relative links, e.g. `[roster](people/roster.md)`.
- Use `- [ ]` for open items.

## Folders

```
AGENTS.md               These instructions (CLAUDE.md points here)
context/                Who the owner is and how they like to work
knowledge/INDEX.md      Generated map of every note (never edit by hand)
knowledge/decisions.md  Dated rulings, plus the lint's `avoid` rules
knowledge/projects/     One note per project (a bot's note holds its Log; digests go in a subfolder)
knowledge/people/       roster.md plus a note per person who comes up often
knowledge/areas/        Ongoing parts of life (home, health, work)
knowledge/reference/    How things work, tools, how-tos
knowledge/sources/      Ledgers of what was imported from where
knowledge/daily/        Daily log, one file per day
knowledge/dreams/       One report per dream (the cleanup pass)
scripts/utils/          Note parsing, lint and index builder
scripts/tests/          Tests for the scripts
skills/dream/           The dream: mechanical script plus the protocol an AI follows
bots/_template/         Skeleton for a scheduled bot (copy it with /new-bot)
docs/                   The bot spec template and phone control
examples/run/           Sample agent output for the example bot
inbox/                  Quick capture, processed by the dream (gitignored)
outputs/                Generated files (gitignored)
```

## Running a bot

A **bot** is a scheduled worker whose output lands in this repo as a pull request. These
rules apply to every bot here and outrank its own instructions.

1. **Never commit to `main`.** One branch and one PR per run. The digest and its Log row
   land together.
2. **Check before you start.** If `bots/<bot_id>/PAUSED` exists on `main`, or the bot
   already has `max_open_prs` open PRs, do nothing except say why.
3. **You search and judge; code scores.** Write what you found to `items.json` and
   `candidates.json` in a run directory, then run
   `uv run python -m bots.<bot_id>.skill --run-dir <dir> --open-prs <n>`. Use the branch
   and PR title it prints. Never write a score or a verdict yourself.
4. **Every item needs a URL and a short quote.** The code drops anything else and counts
   it; don't try to work around that.
5. **Fail loudly.** If a source can't be reached or a step fails, the PR still opens,
   with the problem in "Run problems". A silent gap is worse than a warning, but check
   before you raise an alarm. Never retry more than twice a week.
6. **Before opening the PR,** run `uv run python -m skills.dream.skill --fix` (a new
   digest changes the index), then `uv run pytest` and
   `uv run python -m scripts.utils.lint_memex`. Merge only after CI passes, and only if
   the owner has allowed it.
7. **Keep `bots/<bot_id>/BOT.md` current** in the same PR whenever your setup, routines,
   access or decisions change.
8. **Out of scope, always:** contacting anyone, posting anywhere, sending from the
   owner's accounts, writing to their calendar, spending money, and logged-in or
   terms-restricted sites unless the spec says otherwise.
9. **Ask when the spec is unclear,** and write the answer back into the spec in the same
   PR.
