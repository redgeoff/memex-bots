---
date: 2026-11-02
updated: 2026-11-02
tags: [decisions, meta]
status: active
summary: "Log of your rulings on wording, numbers and process; also holds the lint rules that enforce them."
sensitivity: private
avoid:
  - pattern: '\b[Cc]olour'
    reason: 'Example rule: notes use American spelling, "color" not "colour" (D1). Replace with your own.'
    allow: ['knowledge/decisions.md']
---

# Decisions

A dated log of your rulings about wording, numbers and process, so every AI applies them
the same way and nobody asks twice. The `avoid` rules in the header are checked by the
lint: a note that contradicts a recorded decision fails unless it's on the rule's
`allow` list.

Add new entries at the bottom. Replace an old decision by adding a new one that says so,
never by editing the old one.

| # | Date | Decision | Applies to |
|---|------|----------|------------|
| D1 | 2026-11-02 | Example: notes use **American spelling**. Backed by an `avoid` rule. | All notes |
