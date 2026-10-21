---
date: 2026-10-19
updated: 2026-10-19
tags: [project, bot, example]
status: active
summary: "Example Bot: the project note a bot writes its Log rows into. Copy its shape for a new bot."
sensitivity: public
---

# Example Bot

The project note for the example bot in `bots/_template/`. A real bot's note says why
the bot exists, its attention budget (minutes a week of your time), its kill rule, and
links to its spec and profile. Every run adds one row to the Log, in the same pull
request as its digest.

## Kill rule

Stop after six weekly runs with no "advance" verdict, and record the stop in a final
pull request.

## Log

| Date | Entry |
|------|-------|
| 2026-10-19 | [Digest](example-bot/digest-2026-10-19.md): 1 advance, 1 watch |
