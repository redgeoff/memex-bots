---
description: Scaffold a new scheduled bot (a worker that delivers digests by PR) from the template.
argument-hint: "<bot name and one-line purpose>"
---

Create a new **bot** from the template. Argument: `$ARGUMENTS`

1. Read `AGENTS.md`, `bots/_template/README.md` and `docs/bot-spec-template.md`.
2. If the purpose, sources or success criteria are unclear, ask me up to three numbered
   questions first. Otherwise state the reading you took and continue.
3. On a branch named `bot/<bot_id>`:
   - Fill in `docs/bot-spec-template.md` as `bots/<bot_id>/README.md`.
   - Copy `bots/_template/` to `bots/<bot_id>/` and edit `config.yaml` (id, name, paths,
     thresholds, branch prefix). Adapt the template's tests to the new rubric rather
     than copying their expectations blindly.
   - Create `knowledge/projects/<bot-id>.md` with frontmatter and a `## Log` table.
   - Copy `bots/_template/BOT.md` to `bots/<bot_id>/BOT.md` and fill it in.
4. Build only milestone 1 (skeleton, tests, `--dry-run`) unless I ask for more. No
   network in tests.
5. Run `uv run pytest` and `uv run python -m scripts.lint_notes`; fix anything that
   fails.
6. Open a PR. Merge it yourself once CI passes only if I have said you may; otherwise
   list any open questions in chat, numbered, most important first.

Rules that outrank speed: follow the Security section of `bots/_template/README.md`
(one fine-grained token per bot, an expiry date, `main` protected by a ruleset); no paid
APIs and no secrets in the repo; no contacting anyone or posting anywhere; every digest
claim links to a source; never commit to `main`.
