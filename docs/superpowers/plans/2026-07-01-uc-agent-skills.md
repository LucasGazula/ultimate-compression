# UC Agent Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy 11 Agent Skills (`.agents/skills/`) exposing full Caveman/Ponytail feature sets, update AGENTS.md to reference them, and add `uc init --skills` flag.

**Architecture:** Skills follow agentskills.io standard with YAML frontmatter. Source SKILL.md files live in `src/skills/`. `uc init` copies 11 deployable skills to `.agents/skills/` and updates AGENTS.md with skills reference section.

**Tech Stack:** Python 3 (CLI), Markdown/YAML (SKILL.md)

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/skills/caveman/SKILL.md` | Create | Reference source for AGENTS.md always-on rules |
| `src/skills/cavecrew/SKILL.md` | Create | Deployable skill |
| `src/skills/caveman-commit/SKILL.md` | Create | Deployable skill |
| `src/skills/caveman-compress/SKILL.md` | Create | Deployable skill |
| `src/skills/caveman-help/SKILL.md` | Create | Deployable skill |
| `src/skills/caveman-review/SKILL.md` | Create | Deployable skill |
| `src/skills/caveman-stats/SKILL.md` | Create | Deployable skill |
| `src/skills/ponytail/SKILL.md` | Create | Reference source for AGENTS.md always-on rules |
| `src/skills/ponytail-audit/SKILL.md` | Create | Deployable skill |
| `src/skills/ponytail-debt/SKILL.md` | Create | Deployable skill |
| `src/skills/ponytail-gain/SKILL.md` | Create | Deployable skill |
| `src/skills/ponytail-help/SKILL.md` | Create | Deployable skill |
| `src/skills/ponytail-review/SKILL.md` | Create | Deployable skill |
| `uc` | Modify | Add `init --skills`, update `init_project()` to deploy skills + update AGENTS.md |

---

### Task 1: Create `src/skills/` directory and 6 Caveman SKILL.md files

**Files:**
- Create: `src/skills/cavecrew/SKILL.md`
- Create: `src/skills/caveman-commit/SKILL.md`
- Create: `src/skills/caveman-compress/SKILL.md`
- Create: `src/skills/caveman-help/SKILL.md`
- Create: `src/skills/caveman-review/SKILL.md`
- Create: `src/skills/caveman-stats/SKILL.md`

- [ ] **Create directory and cavecrew skill**

```bash
mkdir -p src/skills/cavecrew src/skills/caveman-commit src/skills/caveman-compress src/skills/caveman-help src/skills/caveman-review src/skills/caveman-stats src/skills/ponytail-audit src/skills/ponytail-debt src/skills/ponytail-gain src/skills/ponytail-help src/skills/ponytail-review src/skills/caveman src/skills/ponytail
```

```markdown
# src/skills/cavecrew/SKILL.md
---
name: cavecrew
description: >
  Decision guide for delegating to subagents for code investigation and surgical
  edits. Use when the task involves finding code, making narrow edits (1-2 files),
  or reviewing diffs — especially in long sessions where context is precious.
---
## Cavecrew = 3 compressed-output subagents

Spawn these instead of vanilla `Explore` or edit agents when main context is tight.

### investigator
**Use:** "Where is X defined / what calls Y / list uses of Z"
**Output:**
```
<path:line> -- `symbol` -- short note (≤6 words)
totals: <counts>.
```
**Avoid:** When you want architecture opinions or design suggestions (use `Explore`).

### builder
**Use:** Surgical edit, ≤2 files, scope obvious. Provide exact path:line.
**Output:**
```
<path:line-range> -- <change ≤10 words>.
verified: <re-read OK | mismatch @ path:line>.
```
**Terminal refusals:** `too-big.` / `needs-confirm.` / `ambiguous.` / `regressed.`
**Avoid:** 3+ file changes, new features, cross-cutting refactors (do on main thread).

### reviewer
**Use:** Review diff, branch, or file for correctness/security.
**Output:**
```
path:line: <emoji> <severity>: <problem>. <fix>.
totals: N🔴 N🟡 N🔵 N❓
```
**Severities:** 🔴 bug, 🟡 risk, 🔵 nit, ❓ question
**Avoid:** Deep architecture feedback or prose (use vanilla `Code Reviewer`).

### Chaining patterns
- **Locate → fix → verify:** investigator returns sites → builder patches 1-2 → reviewer audits diff
- **Parallel scout:** 2-3 investigator calls in one message (different angles), aggregate results
- **Single-shot edit:** Skip investigator, hand exact path:line to builder directly

### When NOT to use
- **cavecrew-builder** without knowing the file first — spawn investigator
- **cavecrew-reviewer** for "general feedback" — it returns findings only, no opinions
- Expecting prose — output is structured, paraphrase if a human reads it
```

- [ ] **Create caveman-commit skill**

```markdown
# src/skills/caveman-commit/SKILL.md
---
name: caveman-commit
description: >
  Generates ultra-compressed Conventional Commits messages. Subject ≤50 chars,
  body only when "why" isn't obvious. Use on "write a commit", "commit message",
  "/commit", or when staging changes.
---
Write commit messages terse and exact. Conventional Commits format. No fluff. Why over what.

## Rules
**Subject:** `<type>(<scope>): <imperative summary>` — scope optional. Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `build`, `ci`, `style`, `revert`. Imperative mood ("add" not "added"). ≤50 chars, hard cap 72. No trailing period.
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
```

- [ ] **Create caveman-compress skill**

```markdown
# src/skills/caveman-compress/SKILL.md
---
name: caveman-compress
description: >
  Ultra-compresses a text or memory file while preserving code, URLs, technical
  terms, and structure. Use on "compress this file", "compress my notes",
  "shrink this document", or when given a file path to condense.
argument-hint: "[filepath]"
---
Compress the given file. Preserve all technical substance. Only fluff gone.

## When to use
User says "compress this", "compress <file>", "shrink", "make terse", or passes a file path with `/caveman-compress`.

## Rules
**Preserve exactly:** code blocks, inline code, URLs, file paths, commands, technical terms, proper nouns, dates/versions/numbers, environment variables, markdown headings, bullet hierarchy, numbered lists, tables, YAML frontmatter.
**Compress:** filler phrases, hedging, redundant explanations, repeated adjectives, long-winded examples, pleasantries, meta-commentary.
**Structure:** Keep the original heading hierarchy. Drop sections that add no information.
**Format:** Output the compressed version. Original: backup as `<filename>.original.md` if writing to disk.

## Output
The compressed content. Nothing else. If the file is already dense, say "Already minimal — no compression needed."

## Boundaries
Never compress source/config files (.py, .js, .ts, .json, .yaml, .toml, .env, .lock, .css, .html, .xml, .sql, .sh) unless explicitly told to. Natural language files only (.md, .txt).
```

- [ ] **Create caveman-help skill**

```markdown
# src/skills/caveman-help/SKILL.md
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
| `/caveman-review` | One-line PR review comments (🔴🟡🔵❓) |
| `/caveman-compress <file>` | Compress a prose/memory file |
| `/caveman-stats` | Show session token usage + savings |
| `/caveman-help` | This card |
| `/cavecrew` | Delegate to compressed-output subagents |

### Natural Language Triggers
- "caveman mode", "talk like caveman", "use caveman", "less tokens", "be brief"
- "stop caveman", "disable caveman", "normal mode"

### Key Rules
- Active every response. No revert after many turns.
- Drop: articles, filler, pleasantries, hedging.
- Keep exact: code blocks, paths, commands, errors, URLs.
- Auto-clarity: security warnings, irreversible actions → write normal.
```

- [ ] **Create caveman-review skill**

```markdown
# src/skills/caveman-review/SKILL.md
---
name: caveman-review
description: >
  Ultra-compressed code review comments. One line per finding: location, problem,
  fix. Use on "review this PR", "code review", "review the diff", "/review".
---
Write code review comments terse and actionable. One line per finding. Location, problem, fix.

## Format
`L<line>: <problem>. <fix>.` — or `<file>:L<line>: ...` for multi-file diffs.

## Severity prefixes (when mixed)
- `🔴 bug:` — broken behavior, will cause incident
- `🟡 risk:` — works but fragile (race, null check, swallowed error)
- `🔵 nit:` — style, naming, micro-optim. Author can ignore
- `❓ q:` — genuine question, not a suggestion

## Drop
"I noticed that...", "It seems like...", "You might want to consider...", "Great work!" (say once at top), hedging ("perhaps", "I think"). Use `q:` if unsure.

## Keep
Exact line numbers. Exact symbol names in backticks. Concrete fix. The *why* if the fix isn't obvious.

## Examples
❌ "I noticed on line 42 you're not checking if the user object is null before accessing email. This could crash."
✅ `L42: 🔴 bug: user can be null after .find(). Add guard before .email.`

❌ "This function is doing a lot and might benefit from breaking up."
✅ `L88-140: 🔵 nit: 50-line fn does 4 things. Extract validate/normalize/persist.`

## Auto-Clarity
Drop terse for: security findings (CVE-class bugs need full explanation), architectural disagreements, onboarding contexts. Write a paragraph, then resume.

## Boundaries
Reviews only — does not write the fix, does not approve/request-changes, does not run linters. Output ready to paste into the PR.
```

- [ ] **Create caveman-stats skill**

```markdown
# src/skills/caveman-stats/SKILL.md
---
name: caveman-stats
description: >
  Show real token usage and estimated savings for the Ultimate Compression session.
  Use on "show me stats", "how many tokens saved", "what's the savings", "/stats".
---
## UC Session Stats

Run `uc status` to display:
- Original tokens vs compressed tokens
- Tokens saved and compression rate
- Cost saved in USD (and estimated BRL)
- Savings by tool: RTK, Headroom, Caveman, Ponytail
- Recent activity (last 5 events)

### What the numbers mean
| Metric | Description |
|--------|-------------|
| Tokens Saved | Total tokens removed by compression |
| Compression Rate | (saved / original) × 100 |
| Cost Saved | Based on configured $/M input/output token costs |
| By Tool | Breakdown per compression engine |

### Cross-session insights
Run `uc status` periodically to track cumulative savings. The SQLite database (`ultimate_compression.db`) persists across sessions.

### Display format
Show the compressed output of `uc status` — totals, breakdown by tool, recent activity. If the dashboard is running, also mention: `http://localhost:20129/dashboard/` for visual charts.
```

- [ ] **Commit**

```bash
git add src/skills/cavecrew/SKILL.md src/skills/caveman-commit/SKILL.md src/skills/caveman-compress/SKILL.md src/skills/caveman-help/SKILL.md src/skills/caveman-review/SKILL.md src/skills/caveman-stats/SKILL.md
git commit -m "feat: add 6 caveman skill definitions"
```

---

### Task 2: Create 5 Ponytail deployable SKILL.md files

**Files:**
- Create: `src/skills/ponytail-audit/SKILL.md`
- Create: `src/skills/ponytail-debt/SKILL.md`
- Create: `src/skills/ponytail-gain/SKILL.md`
- Create: `src/skills/ponytail-help/SKILL.md`
- Create: `src/skills/ponytail-review/SKILL.md`

- [ ] **Create ponytail-audit skill**

```markdown
# src/skills/ponytail-audit/SKILL.md
---
name: ponytail-audit
description: >
  Audit the entire repository for over-engineering, unnecessary abstractions,
  and code bloat. Scans all source files. Use on "audit this repo",
  "find over-engineering", "where is the bloat".
---
Audit the whole repo for over-engineering. Rank findings by lines deletable. Output format per file.

## Tags
- `delete:` dead code, unused flexibility, speculative feature → just delete it
- `stdlib:` hand-rolled thing the standard library ships → name the function
- `native:` dependency or code doing what the platform does → name the feature
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller → inline or remove
- `shrink:` same logic, fewer lines → show the shorter form

## Format
```
<file>:L<line>: <tag> <what>. <replacement>.
```

## Process
1. Identify every source file in the project (exclude .git, node_modules, .venv, vendor, build artifacts)
2. For each file, scan for over-engineering patterns
3. Tag findings with the appropriate tag
4. Sort by impact (most lines deletable first)

## Output
```
net: -<N> lines, -<M> deps possible.
```
Followed by the ranked list of findings. Each finding on its own line.

## Boundaries
Read-only. Does not delete or modify files. Does not run linters or formatters. Does not install/uninstall dependencies.
```

- [ ] **Create ponytail-debt skill**

```markdown
# src/skills/ponytail-debt/SKILL.md
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
```

- [ ] **Create ponytail-gain skill**

```markdown
# src/skills/ponytail-gain/SKILL.md
---
name: ponytail-gain
description: >
  Show the measured-impact scoreboard of Ponytail's effect on the codebase:
  less code, less cost, more speed. Use on "show ponytail gains",
  "what has ponytail saved", "scoreboard", "impact report".
---
## Ponytail Scoreboard

### Benchmark Results (upstream Ponytail v4.8.4)
| Metric | Improvement |
|--------|-------------|
| Lines of Code | 6-20% of baseline |
| Cost | 23-53% reduction |
| Speed | 3-6x faster |

### Per-Repo Impact
Run `git diff --stat` to estimate lines saved vs. a non-Ponytail baseline. Count files touched and total diff size.

### Debt tracking
Run `/ponytail-debt` to see active `ponytail:` markers and their upgrade paths.
Run `/ponytail-audit` to find more opportunities.

### Display format
```
📊 Ponytail Impact
  Lines written: ~N (est. M% of baseline)
  Files changed: N
  ponytail: markers: N active
  Run /ponytail-debt for details
  Run /ponytail-audit to find more
```

## Boundaries
One-shot display. Does not modify files.
```

- [ ] **Create ponytail-help skill**

```markdown
# src/skills/ponytail-help/SKILL.md
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
| full | `/ponytail` (default) | The ladder enforced: YAGNI → stdlib → native → deps → one line |
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
```

- [ ] **Create ponytail-review skill**

```markdown
# src/skills/ponytail-review/SKILL.md
---
name: ponytail-review
description: >
  Review the current working diff for over-engineering, unnecessary abstractions,
  and code bloat. Returns a delete-list of what to remove or simplify.
  Use on "review my changes", "check for over-engineering", "ponytail review".
---
Review the current diff for over-engineering. Apply the Ponytail ladder.

## Process
1. Read the working diff: `git diff` (or staged: `git diff --cached`)
2. For each file changed, apply Ponytail tags
3. Output findings sorted by file → line

## Tags
- `delete:` dead code, unused flexibility, speculative feature
- `stdlib:` hand-rolled thing the standard library ships → name the function
- `native:` dependency or code doing what the platform does → name the feature
- `yagni:` abstraction with one implementation, config nobody sets → inline or remove
- `shrink:` same logic, fewer lines → show shorter form

## Format
```
L<line>: <tag> <what>. <replacement>.
```

## Example
```
L42: delete: unused Result type with single variant. Remove.
L88: stdlib: hand-rolled sort. Use `sorted()`.
L120: yagni: Config class with one field. Inline the value.
```

## Output
End with:
```
net: -<N> lines possible.
```

## Boundaries
Read-only. Does not modify files. Does not run linters.
```

- [ ] **Commit**

```bash
git add src/skills/ponytail-audit/SKILL.md src/skills/ponytail-debt/SKILL.md src/skills/ponytail-gain/SKILL.md src/skills/ponytail-help/SKILL.md src/skills/ponytail-review/SKILL.md
git commit -m "feat: add 5 ponytail skill definitions"
```

---

### Task 3: Create reference SKILL.md for always-on rules (caveman + ponytail)

**Files:**
- Create: `src/skills/caveman/SKILL.md`
- Create: `src/skills/ponytail/SKILL.md`

- [ ] **Create caveman reference SKILL.md** (source for AGENTS.md generation)

```markdown
# src/skills/caveman/SKILL.md
---
name: caveman
description: >
  Ultra-compressed communication. Respond terse like smart caveman. All
  technical substance stays, only fluff dies. Supports levels: lite, full,
  ultra. Use when user says "caveman mode", "talk like caveman",
  "less tokens", "be brief".
---
## Caveman Style

Respond terse like smart caveman. All technical substance stays. Only fluff dies.

## Rules
Drop: articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries (sure/certainly/of course/happy to), hedging. Fragments OK. Short synonyms (big not extensive). No tool-call narration. No decorative tables/emoji. No long raw error logs unless asked. Standard tech acronyms OK (DB/API/HTTP). Never abbreviate code symbols/function names/error strings. Preserve user's dominant language. No self-reference. No "caveman mode on" announcements.

Pattern: `[thing] [action] [reason]. [next step].`

## Auto-Clarity
Drop caveman for: security warnings, irreversible action confirmations, multi-step sequences where fragment order risks misread, when user asks to clarify. Resume after.

## Intensity
| Level | What changes |
|-------|-------------|
| lite | Drop filler/hedging. Keep articles + full sentences. Professional but tight. |
| full | Drop articles, fragments OK, short synonyms. ~65% savings. |
| ultra | Abbreviate prose words, arrows for causality (X → Y). One word when enough. |

## Boundaries
Code/commits/PRs: write normal. Off: "stop caveman" or "normal mode". Active every response.
```

- [ ] **Create ponytail reference SKILL.md** (source for AGENTS.md generation)

```markdown
# src/skills/ponytail/SKILL.md
---
name: ponytail
description: >
  Lazy senior developer mode. Forces the laziest solution that works: YAGNI,
  stdlib first, one line before fifty. Use on ANY coding task. Supports levels:
  lite, full, ultra. Trigger: "ponytail", "lazy mode", "yagni", "simplest".
---
## Ponytail Style

You are a lazy senior developer. The best code is the code never written.

## The Ladder (runs AFTER understanding the problem)
1. Does this need to exist? (YAGNI) → skip it
2. Already in this codebase? → reuse it
3. Stdlib does it? → use it
4. Native platform covers it? → CSS > JS lib, DB constraint > app code
5. Existing dependency solves it? → use it, don't add new ones
6. Can it be one line? → one line
7. Minimum code that works

## Rules
No unrequested abstractions. No boilerplate. Deletion > addition. Boring > clever. Fewest files. Bug fix = root cause (fix where all callers route). Mark shortcuts with `ponytail:` comment.

## Output
Code first. Then at most three lines: what was skipped, when to add it. Pattern: `[code] → skipped: [X], add when [Y].`

## Intensity
| Level | Behavior |
|-------|----------|
| lite | Build what's asked, name lazier alternative in one line. |
| full | The ladder enforced. Stdlib & native first. Shortest diff. |
| ultra | YAGNI extremist. Delete before add. Challenge the requirement. |

## Never simplify
Input validation at trust boundaries. Error handling preventing data loss. Security. Accessibility. Explicit requests. Non-trivial logic leaves ONE runnable check.

## Boundaries
Ponytail governs WHAT you build, not how you talk. Pair with Caveman for terse prose. Off: "stop ponytail" or "normal mode". Active every response.
```

- [ ] **Commit**

```bash
git add src/skills/caveman/SKILL.md src/skills/ponytail/SKILL.md
git commit -m "feat: add reference SKILL.md for always-on rules"
```

---

### Task 4: Update `uc init` to deploy skills and update AGENTS.md

**Files:**
- Modify: `uc`

- [ ] **Add `--skills` flag and update `init_project()`**

Add `--skills` flag to the `init` subparser. Then update `init_project()` to:
1. Create `.agents/skills/` directory
2. Copy all 11 SKILL.md files from `src/skills/` (exclude `caveman/` and `ponytail/` reference dirs)
3. Update AGENTS.md with skills reference section

```python
# Add after line 645 (after init parser creation)
init_parser = subparsers["init"]
init_parser.add_argument("--skills", action="store_true",
    help="Deploy only skills (skip MCP registration and shell profiles)")

# New helper function to deploy skills
SKILLS_TO_DEPLOY = [
    "cavecrew", "caveman-commit", "caveman-compress",
    "caveman-help", "caveman-review", "caveman-stats",
    "ponytail-audit", "ponytail-debt", "ponytail-gain",
    "ponytail-help", "ponytail-review",
]

def deploy_skills(project_root):
    """Copies deployable SKILL.md files to .agents/skills/."""
    src_skills = os.path.join(get_real_path(), "src", "skills")
    target_skills = os.path.join(project_root, ".agents", "skills")
    count = 0
    for skill_name in SKILLS_TO_DEPLOY:
        src = os.path.join(src_skills, skill_name, "SKILL.md")
        dst_dir = os.path.join(target_skills, skill_name)
        dst = os.path.join(dst_dir, "SKILL.md")
        if not os.path.exists(src):
            print(f"Warning: skill {skill_name} not found at {src}")
            continue
        os.makedirs(dst_dir, exist_ok=True)
        with open(src, "r", encoding="utf-8") as f:
            content = f.read()
        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)
        count += 1
    print(f"Deployed {count} skills to {target_skills}")
    return count
```

- [ ] **Update `init_project()` to call `deploy_skills()` and extend AGENTS.md**

After the existing rules section (around line 237, after writing AGENTS.md), add the skills reference section. Insert this before the MCP section:

```python
# Deploy skills
deploy_skills(os.getcwd())

# Add skills reference section to AGENTS.md
with open(agents_file, "r", encoding="utf-8") as f:
    existing = f.read()

skills_section = """

## 🛠️ UC Skills Available

Skills are on-demand commands available via `/skill-name` in your agent:

### Caveman Skills
| Command | Description |
|---------|-------------|
| `/cavecrew` | Delegated subagents for investigation/surgery/review |
| `/caveman-commit` | Generate terse Conventional Commits message |
| `/caveman-compress <file>` | Compress a prose/memory file |
| `/caveman-help` | Quick reference for all caveman commands |
| `/caveman-review` | Ultra-compact code review (🔴🟡🔵❓) |
| `/caveman-stats` | Show session token usage and savings |

### Ponytail Skills
| Command | Description |
|---------|-------------|
| `/ponytail-review` | Review current diff for over-engineering |
| `/ponytail-audit` | Audit entire repo for over-engineering |
| `/ponytail-debt` | Harvest `ponytail:` comments into ledger |
| `/ponytail-gain` | Show measured-impact scoreboard |
| `/ponytail-help` | Quick reference for all ponytail commands |

### Runtime Compression (always active)
- **RTK** — `shims/` on PATH compress git/grep/ls/find/tree/rg output transparently
- **Headroom** — Docker proxy on :8787 compresses conversation context transparently

Your agent will discover these skills automatically and can invoke them when relevant.
"""

if "## 🛠️ UC Skills Available" not in existing:
    with open(agents_file, "a", encoding="utf-8") as f:
        f.write(skills_section)
```

- [ ] **Update the `init` command handler** (line 663-664) to pass `--skills`

```python
# Replace around line 663-664
elif args.command == "init":
    if hasattr(args, 'skills') and args.skills:
        database.init_db()
        deploy_skills(os.getcwd())
        print("Skills deployed. Run `uc init` (without --skills) for full setup including MCP and shell profiles.")
    else:
        init_project()
```

- [ ] **Commit**

```bash
git add uc
git commit -m "feat: uc init deploys skills and extends AGENTS.md"
```

---

### Task 5: Verify everything works

- [ ] **Run `uc init --skills` and verify skills are deployed**

```bash
python3 uc init --skills
# Expected output:
# Deployed 11 skills to C:\path\.agents\skills\
```

Verify files exist:

```bash
ls .agents/skills/
# Expected: 11 directories

ls .agents/skills/ponytail-review/SKILL.md
# Expected: ponytail-review SKILL.md exists
```

- [ ] **Run full `uc init` and verify AGENTS.md has skills section**

```bash
python3 uc init
```

Verify AGENTS.md now has `## 🛠️ UC Skills Available` section with all skill tables.

- [ ] **Run `uc status` to confirm no regressions**

```bash
python3 uc status
# Expected: normal status output, no errors
```

- [ ] **Commit the verified state**

```bash
git add .
git commit -m "chore: verify skills deployment and finalize"
```
