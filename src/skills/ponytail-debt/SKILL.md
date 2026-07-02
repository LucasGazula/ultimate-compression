---
name: ponytail-debt
description: >
  Harvest `ponytail:` shortcut comments from the codebase into a tracked debt
  ledger. Use on "track my ponytail debt", "harvest shortcuts", "list ponytail
  comments", "show debt".
---
Find all `ponytail:` comments in the codebase. Build a debt ledger with ceiling and upgrade path.

## What to find
Grep for `ponytail:` in all source files (exclude .git, node_modules, .venv, vendor). Example comments:
```python
# ponytail: global lock, per-account locks if throughput matters
```
```typescript
// ponytail: flat list, tree if >50 items
```

## Ledger format
```
| File | Line | Ceiling | Upgrade Path |
|------|------|---------|-------------|
| src/auth.py | 42 | global lock | per-account locks if throughput matters |
| src/search.ts | 17 | flat list | tree if >50 items |
```

## Tags
- Mark entries missing a trigger condition as `no-trigger`
- Mark entries that HAVE triggered with the date

## Output
Markdown table. If no `ponytail:` comments found, say "No debt markers found — clean codebase."

## Boundaries
Read-only. Does not modify files.
