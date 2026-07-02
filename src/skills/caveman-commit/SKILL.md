---
name: caveman-commit
description: >
  Generates ultra-compressed Conventional Commits messages. Subject <=50 chars,
  body only when "why" isn't obvious. Use on "write a commit", "commit message",
  "/commit", or when staging changes.
---
Write commit messages terse and exact. Conventional Commits format. No fluff. Why over what.

## Rules
**Subject:** `<type>(<scope>): <imperative summary>` — scope optional. Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `build`, `ci`, `style`, `revert`. Imperative mood ("add" not "added"). <=50 chars, hard cap 72. No trailing period.
**Body:** Skip when subject is self-explanatory. Add only for non-obvious *why*, breaking changes, migration notes, linked issues. Wrap at 72. Bullets `-`. Reference issues at end: `Closes #42`.
**NEVER:** "This commit does X", "I", "we", "now" — the diff says what. No AI attribution unless project requires an `Assisted-by` trailer.

## Examples
Diff: new endpoint for user profile with body explaining the why
```
feat(api): add GET /users/:id/profile

Mobile client needs profile data without the full user payload
to reduce LTE bandwidth on cold-launch screens.

Closes #128
```

Diff: breaking API change
```
feat(api)!: rename /v1/orders to /v1/checkout

BREAKING CHANGE: clients on /v1/orders must migrate to /v1/checkout
before 2026-06-01. Old route returns 410 after that date.
```

## Auto-Clarity
Always include body for: breaking changes, security fixes, data migrations, reverts.

## Boundaries
Output the message as a code block ready to paste. Does not run `git commit`, does not stage files.
