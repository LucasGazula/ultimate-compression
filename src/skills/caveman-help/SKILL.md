---
name: caveman-help
description: >
  Quick-reference card for all caveman modes, skills, and commands. One-shot
  display. Trigger: /caveman-help, "caveman help", "what caveman commands",
  "how do I use caveman".
---
## Caveman Quick Reference

### Modes (intensity levels)
| Level | Command | Effect | Savings |
|-------|---------|--------|---------|
| lite | `/caveman lite` | Drop filler/hedging. Keep articles + full sentences. | Moderate |
| full | `/caveman` (default) | Drop articles, fragments OK, short synonyms. | ~65% |
| ultra | `/caveman ultra` | Abbreviate prose words, arrows for causality. | Highest |
| off | `/caveman off` or "stop caveman" | Deactivate | N/A |

### Available Skills
| Command | What it does |
|---------|-------------|
| `/caveman-commit` | Generate terse Conventional Commits message |
| `/caveman-review` | One-line PR review comments (bug/risk/nit) |
| `/caveman-compress <file>` | Compress a prose/memory file |
| `/caveman-stats` | Show session token usage + savings |
| `/caveman-help` | This card |
| `/cavecrew` | Delegate to compressed-output subagents |

### Key Rules
- Active every response. No revert after many turns.
- Drop: articles, filler, pleasantries, hedging.
- Keep exact: code blocks, paths, commands, errors, URLs.
- Auto-clarity: security warnings, irreversible actions -> write normal, resume after.
