---
name: ponytail-help
description: >
  Quick-reference card for all ponytail commands, levels, and skills.
  Use on "ponytail help", "how do I use ponytail", "ponytail commands".
---
## Ponytail Quick Reference

### Intensity Levels
| Level | Command | Behavior |
|-------|---------|----------|
| lite | `/ponytail lite` | Build what's asked + name lazier alternative in one line |
| full | `/ponytail` (default) | The ladder enforced: YAGNI -> stdlib -> native -> deps -> one line |
| ultra | `/ponytail ultra` | YAGNI extremist. Delete before add. Ship one-liner + challenge |
| off | `/ponytail off` or "stop ponytail" | Deactivate |

### Available Skills
| Command | What it does |
|---------|-------------|
| `/ponytail-review` | Review current diff for over-engineering |
| `/ponytail-audit` | Audit entire repo for over-engineering |
| `/ponytail-debt` | Harvest `ponytail:` comments into ledger |
| `/ponytail-gain` | Show measured-impact scoreboard |
| `/ponytail-help` | This card |

### The Ladder (runs AFTER understanding the problem)
1. Does this need to exist? (YAGNI)
2. Already in this codebase? Reuse it
3. Stdlib does it? Use it
4. Native platform covers it? CSS > JS lib, DB constraint > app code
5. Existing dependency solves it? Use it
6. Can it be one line? One line
7. Minimum code that works

### Key Rules
- No unrequested abstractions. No boilerplate. No scaffolding "for later".
- Deletion > addition. Boring > clever. Fewest files wins.
- Bug fix = root cause: fix where all callers route through.
- `ponytail:` comment marks deliberate shortcuts.
- Never simplify: input validation, error handling, security, accessibility.
- Non-trivial logic leaves ONE runnable check behind.
