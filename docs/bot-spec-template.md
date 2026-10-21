# <Bot name> — build spec

**Status: draft.** Copy this file to `bots/<bot_id>/README.md` and fill in every section. If something is ambiguous, the builder (you or an agent) **asks the owner** rather than guessing, and records the answer here in the same PR. Skeleton and checklist: [`bots/_template/`](../bots/_template/README.md); security rules are in its README.

Project context and the kill rule live in `knowledge/projects/<bot-id>.md`. The bot's canonical profile (identity, hosting, routines and prompts, access, decisions, history) is `bots/<bot_id>/BOT.md`; **the bot keeps it current by PR whenever any of those change.**

## 0. Architecture

Hybrid (see `bots/_template/README.md`): the agent routine searches and judges with its own tools and writes JSON into a run directory; Python validates, scores and writes the digest. State the run-directory files this bot uses and their schemas.

## 1. What it is, in one paragraph

What it watches, what it produces, how often, and what it explicitly does not do.

## 2. Why it exists

The decision or goal it serves, and the past lesson that shapes its design. Link the note that holds the criteria.

## 3. Hard constraints

Numbered, each testable. A violation is a bug. Include the attention budget (minutes a week of the owner's time) and the cost ceiling (default: no paid APIs).

## 4. Targets

What it watches: groups, topics, accounts or feeds. Configurable in `config.yaml`, not hard-coded.

## 5. Sources

For each source: how it is reached (agent tool, public API with no key), what counts as evidence, rate and terms limits. No logged-in or terms-restricted sites.

## 6. Pipeline

Collect → validate → cluster or dedupe → score → verdict → digest → deliver. Say which steps are agent judgement and which are code.

## 7. Data model

The `Item` and `Candidate` fields. Every item has a URL and a short quote. Candidate ids are stable across weeks so diffs work.

## 8. Scoring rubric

Questions or signals, weights, thresholds, and the verdict rules (advance, watch, drop). Verdicts must be computable from stored fields.

## 9. Digest format

Sections, word limit (default about 600), what the owner must be able to decide from it. Lands at `knowledge/projects/<bot-id>/digest-YYYY-MM-DD.md` with full frontmatter and a Log row.

## 10. Delivery and hosting

- Branch `<prefix>/YYYY-MM-DD`, one PR per run, never on `main`; merge when CI passes, then summarize in chat.
- Where the bot is scheduled and hosted, where secrets live, how to rotate keys.
- Pause: `bots/<bot_id>/PAUSED` on `main`. Cap: `max_open_prs`.
- Failure handling: partial digest with a "Run problems" section; at most two retries a week.

## 10a. Security

Name the bot's token (fine-grained, your memex repo only, Contents and Pull requests read/write), its expiry date, where it is stored, and how it is rotated. Confirm `main` has a ruleset requiring a PR and passing CI that the token cannot bypass. List the paths the bot may write. Follow [Security and credentials](../bots/_template/README.md#security-and-credentials).

## 11. Kill rule

When the bot stops running and what it records when it does (one final PR with the verdict).

## 12. Out of scope

Contacting anyone, posting anywhere, drafting outreach, building products, anything outside the criteria above.

## 13. Milestones

1. Skeleton: config, models, scoring, digest, `--dry-run`, tests (no network)
2. First source plus agent extraction, one end-to-end run
3. Remaining sources and clustering
4. State and week-over-week diff
5. Scheduling and PR delivery, first real digest

## 14. Acceptance criteria

- [ ] Every claim in the digest links to a source; spot-check 10 random links
- [ ] Verdicts reproducible from stored fields
- [ ] Digest under the word limit and passes the note lint
- [ ] No secrets or personal contact data in outputs or the repo
- [ ] Tests pass offline
- [ ] Runs on schedule without the owner, one PR per run, CI green
- [ ] README documents hosting, pause and key rotation

## 15. Open questions for the owner

Numbered, most important first. Answers get written back here.
