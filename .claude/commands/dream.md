---
description: Run the memex dream cycle (reflect, index, clean). Use "quick" for the mechanical pass only.
argument-hint: "[quick]"
---

Run the memex **dream** cycle. The full protocol, autonomy tiers and report template are in `skills/dream/README.md`; read it first and follow it exactly.

Argument: `$ARGUMENTS`

- If the argument is `quick`: run `uv run python -m skills.dream.skill --fix`, fix any lint errors that are mechanical, show me the report, and stop. No branch or PR unless fixes were needed.
- Otherwise run the full protocol (phases 0 to 7) on a branch named `dream/<today's date>`:
  1. Orient: read `knowledge/INDEX.md`, `context/PREFERENCES.md`, `knowledge/decisions.md` and the latest report in `knowledge/dreams/`.
  2. Mechanical pass, sweep, reconcile, staleness, organize, report, land.
  3. Open a PR, ask me the Tier C questions in chat (numbered, most important first), and merge it only if `context/PREFERENCES.md` allows that and no Tier C question is open; otherwise leave it open.

Rules that outrank tidiness: never invent facts; never store credentials or account numbers; ask before changing the meaning of a fact, a recorded decision, anything in `context/`, or a note's sensitivity; archive instead of deleting.
