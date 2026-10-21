# Instructions for agents running bots in this repo

You are running a **bot**: a scheduled worker whose output lands in this repo as a pull
request. These rules apply to every bot here and outrank its own instructions.

1. **Never commit to `main`.** One branch and one PR per run. The digest and its Log row
   land together.
2. **Check before you start.** If `bots/<bot_id>/PAUSED` exists on `main`, or the bot
   already has `max_open_prs` open PRs, do nothing except say why.
3. **You search and judge; code scores.** Write what you found to `items.json` and
   `candidates.json` in a run directory, then run
   `uv run python -m bots.<bot_id>.skill --run-dir <dir>`. Never write a score or a
   verdict yourself.
4. **Every item needs a URL and a short quote.** The code drops anything else and counts
   it; don't try to work around that.
5. **Fail loudly.** If a source can't be reached or a step fails, the PR still opens,
   with the problem in "Run problems". A silent gap is worse than a warning, but check
   before you raise an alarm. Never retry more than twice a week.
6. **Run `uv run pytest` and `uv run python -m scripts.lint_notes` before opening the
   PR.** Merge only after CI passes, and only if the owner has allowed it.
7. **Keep `bots/<bot_id>/BOT.md` current** in the same PR whenever your setup, routines,
   access or decisions change.
8. **Out of scope, always:** contacting anyone, posting anywhere, sending from the
   owner's accounts, writing to their calendar, spending money, and logged-in or
   terms-restricted sites unless the spec says otherwise.
9. **Ask when the spec is unclear,** and write the answer back into the spec in the same
   PR.
