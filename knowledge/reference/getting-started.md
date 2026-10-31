---
date: 2026-01-01
updated: 2026-01-01
tags: [reference, setup]
status: active
summary: "How to start using this memex: first steps, importing documents and the first dream."
sensitivity: public
---

# Getting started

1. Fill in [About Me](../../context/ABOUT_ME.md) and
   [Preferences](../../context/PREFERENCES.md). Short is fine.
2. Point an AI at this repo and ask it to add something, e.g. "add a note about my
   garden project". It should read [AGENTS.md](../../AGENTS.md), make a branch, add the
   note with a header, regenerate the index and open a pull request.
3. When you correct the same fact twice, record it in the
   [decisions log](../decisions.md).
4. To bring in old documents, export them to a folder, decide first what stays out, and
   have an AI summarize them into notes. Keep a ledger of what was read and skipped in
   [sources](../sources/import-ledger.md).
5. Once there are a few dozen notes, run a dream (`/dream` in Claude Code, or ask any
   AI to follow [the protocol](../../skills/dream/README.md)).

Don't try to design it all up front. The structure will change as you use it.
