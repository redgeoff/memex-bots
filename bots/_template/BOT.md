# <bot name> — bot profile (canonical)

**This is the one canonical reference for this bot.** It's written so that another bot can
read it and know who this bot is, where it runs, what it may touch, how its routines
work, and which decisions bind it. The build spec is [README.md](./README.md); project
context is in `knowledge/projects/<bot-id>.md`.

> **Keep this file current.** The bot itself updates this profile **by PR** whenever its
> setup, routines (schedule or prompt), access or secrets, or decisions change. Do it in
> the same PR as the change when possible, and bump "Last updated". Never put secret
> values here, only their names, scopes, where they are stored, and rotation dates.

_Last updated: YYYY-MM-DD._

## Identity and role
Name (and any rename, with its date), who it acts for, what it does and doesn't do.

## Hosting
Where it runs (platform, machine), and a table of box paths (clones, run dirs, state, backups).

## Architecture
What the agent does with its own tools; what deterministic code does (module, CLI); cost.

## Routines
For each routine: its name, schedule with timezone (`CRON_TZ`), and the **full prompt
verbatim**. Also cover on-demand modes.
Slack channel / routine: private channel and the Slack-trigger prompt, if this bot is
controlled from the phone ([phone control](../../docs/phone-control.md)).

## Access and secrets
Each token or connector: scope, where it is stored, expiry and rotation. Note which
connected services are unused.
Slack channel / routine: the Slack connector and any account connection it needs, if used
([phone control](../../docs/phone-control.md)).

## Rules and permissions
How changes land (PR, CI, merge), data rules, citation rules, and the never-do list.

## Binding decisions
A table of the decisions that bind this bot, one line each, with where each is recorded.

## History (PRs)
One line per PR.

## Open items
What is unfinished or waiting on the owner.
