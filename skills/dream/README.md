# Dream

**Dreaming** is the memex's maintenance cycle: an AI steps back from the day-to-day,
reflects on what is in the repo and consolidates it. It rebuilds the index, removes
duplicates, reconciles conflicts, flags what is stale and asks you the questions only
you can answer. It runs **when you ask** (`/dream` in Claude Code, or "let's dream" in
any AI that can read this repo), or on a schedule if you set one up. It lands as a
**pull request**, never a direct commit to `main`.

The idea is borrowed. Anthropic's
[dreaming for Claude Managed Agents](https://claude.com/blog/new-in-claude-managed-agents),
[OpenClaw's dreaming](https://docs.openclaw.ai/concepts/dreaming) and the
[hermes-dreaming](https://hermes-agent.nousresearch.com/docs/plugins/hermes-dreaming)
plugin for Hermes Agent all consolidate an agent's memory between sessions. This version
works on a git repo, so every change is a diff you can review.

Dreaming has two halves:

| Half | Who | What | Safe to automate? |
|------|-----|------|-------------------|
| **Mechanical** | `skills/dream/skill.py` and `scripts/utils/` | Lint, regenerate the index, gather facts about the repo | Yes; the lint also runs in CI |
| **Reflective** | An AI, following this protocol | Judgment: promote, reconcile, archive, ask | Only within the autonomy tiers below |

---

## When to dream

- After a big import or a long working session.
- Roughly weekly while the repo is growing.
- Before you rely on the memex for something important, so facts and wording are
  consistent.
- `/dream quick` runs only the mechanical half (about a minute) and is fine any time.

## Invocation

```bash
uv run python -m skills.dream.skill            # report only
uv run python -m skills.dream.skill --fix      # regenerate knowledge/INDEX.md too
uv run python -m skills.dream.skill --json     # structured output for an AI
```

## What the mechanical half checks

`lint_memex` (also run in CI) enforces: required frontmatter (`date`, `updated`, `tags`,
`status`, `summary`, `sensitivity`) and allowed values; relative links resolve; file
names are kebab-case; privacy patterns (credential assignments, keys, SSNs, long account
numbers); transient status text ("not yet read") outside ledger notes; contradictions of
recorded decisions (the `avoid` rules in `knowledge/decisions.md`); a fresh
`knowledge/INDEX.md`; and orphan notes.

The skill adds: the last dream report, notes changed since it, every open `- [ ]` item,
active notes untouched for 90 days, files waiting in `inbox/`, and people named in bold
in `knowledge/people/roster.md` who are mentioned often but have no note of their own.

---

## Autonomy tiers

What the AI may do on its own depends on the change.

| Tier | The AI may | Examples |
|------|-----------|----------|
| **A. Do it** | Apply mechanical, meaning-preserving fixes | Regenerate the index; fix broken links; normalize frontmatter and `updated` dates; add missing "Related" links; fix typos and formatting |
| **B. Propose in the PR** | Make the change on the branch, call it out in the report, and let you accept or revert | Replace a restated fact with a link to its canonical note; move or rename a note (use `move_note`, which rewrites links); archive a superseded note to `_archive/`; promote a durable fact from a daily note or the inbox; create a person note; add an `avoid` rule for a settled decision |
| **C. Ask first** | Write a question in the report and in chat; change nothing until answered | Anything that changes what a fact *means* or which version is right; editing `context/`; changing a recorded decision; lowering a note's `sensitivity`; deleting anything; resolving a conflict between what you said and a document; anything that touches the privacy rules |

**Never**: invent facts, merge two people or two events on a hunch, store credentials or
account numbers, turn an unverified claim into a verified one, or delete (archive
instead).

---

## The protocol

Work on a branch named `dream/YYYY-MM-DD`. Commit each phase separately so the PR reads
as a story.

### 0. Orient
Read `knowledge/INDEX.md`, `context/PREFERENCES.md`, `knowledge/decisions.md` and the
latest report in `knowledge/dreams/`. Note the date of the last dream; everything below
is "since then" unless a full pass is asked for.

### 1. Mechanical pass
Run `uv run python -m skills.dream.skill --fix --json`. Fix every lint **error** (Tier A
where mechanical; otherwise Tier C). Warnings are triaged in phase 5. Commit:
`Dream: regenerate index and fix lint`.

### 2. Sweep
Look at `inbox/` and daily notes newer than the last dream. For each durable item (a
fact, a decision, a person, a story, a lesson) decide where it lives:
- a canonical note (promote it, with a source and date), or
- `knowledge/decisions.md` (if it is a ruling about wording or process), or
- nowhere (ephemeral). Leave daily notes as the log; never rewrite them.

Move processed inbox files to `inbox/_processed/` (gitignored). Commit:
`Dream: promote durable items`.

### 3. Reconcile
For every note changed since the last dream:
- **One owner per fact.** Find facts and numbers stated in more than one note. Pick the
  canonical note and replace restatements with a link plus, at most, the one number
  needed in context.
- **Conflicts.** If two notes disagree, or a note disagrees with `decisions.md`, don't
  choose silently. Apply `decisions.md` if it settles the question (Tier B); otherwise
  list it as a question (Tier C).
- **Sources.** Check new claims cite their source document or "<you>, <date>".
  Unsourced claims get a question, not a guess.
- **Decisions to rules.** If a new decision has a wording that must not come back, add
  an `avoid` rule so the lint enforces it.

Commit: `Dream: reconcile duplicates and conflicts`.

### 4. Staleness
Go through the skill's open items, stale notes and ledgers:
- Open `- [ ]` items older than 30 days: ask whether to do, drop or keep.
- Status text in content notes ("unread", "pending", "not yet imported"): move it to a
  ledger in `knowledge/sources/`.
- Active notes not updated for 90 days: refresh, mark `status: archived` and move to
  `_archive/`, or confirm they are evergreen (then bump `updated`).
- Notes marked `draft` for more than 30 days.

Commit: `Dream: staleness and archive`.

### 5. Organize
- Resolve lint warnings (orphans, naming).
- **People**: for each candidate from the skill, create
  `knowledge/people/<first-last>.md` if there is enough to say (three or more distinct
  facts), linking back to the roster.
- **Tags**: reuse existing tags; propose merges for near-duplicates.
- **Structure**: if a folder has more than about 12 notes or a note exceeds about 4,000
  words, propose a split or a new subfolder (Tier C, with a one-line reason). Use
  `move_note` so links follow.
- **Summaries**: make sure each note's one-line `summary` still describes it. Re-run the
  index.

Commit: `Dream: organize`.

### 6. Report
Write `knowledge/dreams/YYYY-MM-DD.md` (template below). It is the audit trail and the
next dream's starting point. Commit: `Dream: report`.

### 7. Land
Run `uv run pytest` and the lint (both must pass). Push the branch and open a PR. The PR
description is the report's summary. Ask the Tier C questions in chat, numbered, most
important first. Leave the PR for you to merge, unless `context/PREFERENCES.md` says the
AI may merge a dream PR itself once CI passes and no Tier C question is open.

---

## Report template

```markdown
---
date: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [dream, meta]
status: active
summary: "Dream report: what changed, what is proposed, what needs an answer."
sensitivity: private
since: YYYY-MM-DD   # date of the previous dream, or "never"
---

# Dream YYYY-MM-DD

## Numbers
Notes, words, lint errors/warnings before → after, open items, stale notes.

## Done (Tier A)
- ...

## Proposed in this PR (Tier B)
- ... (each with the note it touches and why)

## Questions (Tier C)
1. ...

## Noticed but left alone
- ...
```

---

## Guardrails (why it is built this way)

- **Propose, don't impose.** Everything lands as a reviewable diff; you can revert any
  commit.
- **Raw sources stay linked.** Notes cite the source document, so summaries can't drift
  into summaries of summaries. A note that can't name its source is a finding.
- **Facts have owners.** Restating the same number in several notes is how a memex
  drifts. The index, the decisions log and the `avoid` rules make drift detectable.
- **Privacy first.** The privacy rules in `AGENTS.md` and `context/PREFERENCES.md`
  outrank tidiness. The lint enforces the patterns it can; the AI enforces the rest.
- **Cheap by default.** Only changed notes are re-read. A full pass is a deliberate
  choice.
- **Not a vector database.** For a personal memex (tens or a few hundred thousand
  words), an index and grep go a long way before embeddings are worth it.

## Files

| File | Purpose |
|------|---------|
| `skill.py` | Mechanical phase (`run()`, `render()`, CLI) |
| `tests/test_skill.py` | Tests |
| `../../scripts/utils/memex_notes.py` | Parsing, links, `move_note` |
| `../../scripts/utils/lint_memex.py` | Lint rules |
| `../../scripts/utils/build_index.py` | Generates `knowledge/INDEX.md` |
| `../../knowledge/decisions.md` | Decisions and the `avoid` rules |
| `../../knowledge/dreams/` | One report per dream |
| `../../.claude/commands/dream.md` | The `/dream` command for Claude Code |
