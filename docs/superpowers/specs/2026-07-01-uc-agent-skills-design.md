# Ultimate Compression: Agent Skills & Full Feature Exposure

## Problem

Ultimate Compression (UC) currently uses only ~30% of the features available from its upstream tools (Caveman, Ponytail, RTK, Headroom). Users cannot access native commands like `ponytail-review`, `ponytail-audit`, `caveman-compress`, `caveman-commit`, etc. through their AI coding agents.

## Design

Expose full feature sets of all 4 upstream tools through the mechanisms each tool's authors chose:

| Tool | Mechanism | How it works |
|------|-----------|-------------|
| **Caveman** | Skills (.agents/skills/) | 7 SKILL.md files, agent invokes via `/caveman-review` etc. |
| **Ponytail** | Skills (.agents/skills/) | 6 SKILL.md files, agent invokes via `/ponytail-review` etc. |
| **RTK** | Shell shims (PATH interception) | Transparent — agent never knows. Already implemented. |
| **Headroom** | HTTP Proxy (Docker :8787) | Transparent — agent never knows. Already implemented. |

### Decision rationale

All 4 target platforms (Claude Code, OpenCode, Codex CLI, Antigravity CLI) support the **Agent Skills** standard (agentskills.io) with `.agents/skills/<name>/SKILL.md`. Skills work on all platforms simultaneously.

RTK does NOT use MCP in its original form — it uses CLI hooks and shims. Headroom's primary mechanism is an HTTP proxy, with MCP as a secondary channel for reversible compression (CCR retrieval). We keep both working as they already do.

## Inventory of Skills

### Caveman (7 skills)

| Skill | File | Type | Description |
|-------|------|------|-------------|
| `caveman` | AGENTS.md (always-on) | Behavior | Ultra-compressed communication, 6 intensity levels |
| `cavecrew` | `.agents/skills/cavecrew/SKILL.md` | Command | Subagent delegation guide (investigator/builder/reviewer) |
| `caveman-commit` | `.agents/skills/caveman-commit/SKILL.md` | Command | Conventional Commits with terse body |
| `caveman-compress` | `.agents/skills/caveman-compress/SKILL.md` | Command | Compress files via `uc compress` |
| `caveman-help` | `.agents/skills/caveman-help/SKILL.md` | Reference | Quick reference card |
| `caveman-review` | `.agents/skills/caveman-review/SKILL.md` | Command | Ultra-compact code review (🔴🟡🔵❓) |
| `caveman-stats` | `.agents/skills/caveman-stats/SKILL.md` | Command | Token savings statistics via `uc status` |

### Ponytail (6 skills)

| Skill | File | Type | Description |
|-------|------|------|-------------|
| `ponytail` | AGENTS.md (always-on) | Behavior | Lazy senior dev ladder, 3 intensity levels |
| `ponytail-audit` | `.agents/skills/ponytail-audit/SKILL.md` | Command | Whole-repo over-engineering audit |
| `ponytail-debt` | `.agents/skills/ponytail-debt/SKILL.md` | Command | Harvest `ponytail:` comments into ledger |
| `ponytail-gain` | `.agents/skills/ponytail-gain/SKILL.md` | Reference | Scoreboard (LOC, cost, speed) |
| `ponytail-help` | `.agents/skills/ponytail-help/SKILL.md` | Reference | Quick reference card |
| `ponytail-review` | `.agents/skills/ponytail-review/SKILL.md` | Command | Over-engineering review of current diff |

### What UC provides (runtime)

- `shims/` in PATH — RTK transparent compression (git, grep, ls, rg, find, tree)
- Headroom Docker proxy on :8787 — transparent context compression
- `uc` CLI — start, stop, status, config, rtk-filter
- Dashboard on :20129 — config, stats, metrics

## Architecture

```
uc init
├── .agents/AGENTS.md
│   ├── ## 🪨 Caveman Style (Constraint)
│   ├── ## 💈 Ponytail (Constraint)
│   └── ## 🛠️ UC Skills Available
│       └── Lista de skills + descrição + atalho RTK/Headroom
│
├── .agents/skills/
│   ├── cavecrew/SKILL.md
│   ├── caveman-commit/SKILL.md
│   ├── caveman-compress/SKILL.md
│   ├── caveman-help/SKILL.md
│   ├── caveman-review/SKILL.md
│   ├── caveman-stats/SKILL.md
│   ├── ponytail-audit/SKILL.md
│   ├── ponytail-debt/SKILL.md
│   ├── ponytail-gain/SKILL.md
│   ├── ponytail-help/SKILL.md
│   └── ponytail-review/SKILL.md
│
(Sem MCP — RTK via shims, Headroom via proxy, ambos transparentes)
```

## SKILL.md Format

All skills follow the Agent Skills standard. YAML frontmatter required:

```yaml
---
name: skill-name
description: What it does and when to invoke. 1-1024 chars.
---
```

Key restrictions (per agentskills.io):
- `name`: 1-64 chars, lowercase alphanumeric + single hyphens
- `description`: 1-1024 chars, specific enough for agent to auto-trigger
- Body: markdown instructions for the agent to follow when skill is active

## How skills execute

Skills are **instructions for the LLM agent** — they tell the agent HOW to perform the task. The agent uses its own tools (Read, Grep, Bash, Edit) to execute the skill's instructions.

For example, `ponytail-review` tells the agent to:
1. Read the current diff (`git diff`)
2. Apply Ponytail's review tags (delete:, stdlib:, native:, yagni:, shrink:)
3. Output in format `L<line>: <tag> <what>. <replacement>.`

The skill does NOT call `uc` for review — the agent performs the review itself following the skill's instructions (matching upstream Ponytail behavior).

`caveman-compress` tells the agent to run `uc rtk-filter <file>` to compress a file's content.

## uc CLI Changes

New subcommand: `uc init --skills` deploys only the skills directory. Existing `uc init` deploys everything (AGENTS.md + skills + shims + MCP).

New skills directory in the repo: `src/skills/` containing source SKILL.md files. `uc init` copies them to `.agents/skills/`.

## Files to create/modify

### New files (skill sources in repo, under `src/skills/`):
- `src/skills/caveman/SKILL.md` — source for AGENTS.md always-on rules (NOT deployed to .agents/skills/)
- `src/skills/cavecrew/SKILL.md` — deployed to .agents/skills/cavecrew/SKILL.md
- `src/skills/caveman-commit/SKILL.md` — deployed
- `src/skills/caveman-compress/SKILL.md` — deployed
- `src/skills/caveman-help/SKILL.md` — deployed
- `src/skills/caveman-review/SKILL.md` — deployed
- `src/skills/caveman-stats/SKILL.md` — deployed
- `src/skills/ponytail/SKILL.md` — source for AGENTS.md always-on rules (NOT deployed to .agents/skills/)
- `src/skills/ponytail-audit/SKILL.md` — deployed
- `src/skills/ponytail-debt/SKILL.md` — deployed
- `src/skills/ponytail-gain/SKILL.md` — deployed
- `src/skills/ponytail-help/SKILL.md` — deployed
- `src/skills/ponytail-review/SKILL.md` — deployed

Only 11 skills are deployed to `.agents/skills/`. `caveman` and `ponytail` source SKILL.md files serve as reference for AGENTS.md generation only.

### Modified files:
- `uc` (CLI entry point) — add `--skills` flag, update `init` to deploy skills
- `.agents/AGENTS.md` — add skills reference section

### No changes needed:
- `src/prompts.py` — already has Caveman/Ponytail level content
- `src/proxy.py` — already injects prompts
- `shims/` — already intercept commands
- `src/main.py` — Docker Headroom already works

## Platform Compatibility

| Platform | Skill Location | Invocation | Notes |
|----------|---------------|------------|-------|
| Claude Code | `.agents/skills/` | `/skill-name` | Also supports `.claude/skills/` |
| OpenCode | `.agents/skills/` | `skill()` tool | Also `.claude/skills/` or `.opencode/skills/` |
| Codex CLI | `.agents/skills/` | `$skill-name` | Reads from AGENTS.md too |
| Antigravity | `.agents/skills/` | `activate_skill` | Also `.gemini/skills/` |

`.agents/skills/` is the universal location recognized by all 4 platforms.
