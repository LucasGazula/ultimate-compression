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
<path:line> -- `symbol` -- short note (<=6 words)
totals: <counts>.
```
**Avoid:** When you want architecture opinions or design suggestions (use `Explore`).

### builder
**Use:** Surgical edit, <=2 files, scope obvious. Provide exact path:line.
**Output:**
```
<path:line-range> -- <change <=10 words>.
verified: <re-read OK | mismatch @ path:line>.
```
**Terminal refusals:** `too-big.` / `needs-confirm.` / `ambiguous.` / `regressed.`
**Avoid:** 3+ file changes, new features, cross-cutting refactors (use main thread).

### reviewer
**Use:** Review diff, branch, or file for correctness/security.
**Output:**
```
path:line: <emoji> <severity>: <problem>. <fix>.
totals: N bug N risk N nit N question
```
**Severities:** bug (broken behavior), risk (works but fragile), nit (style), question (genuine query)
**Avoid:** Deep architecture feedback or prose (use vanilla `Code Reviewer`).

### Chaining patterns
- **Locate -> fix -> verify:** investigator returns sites -> builder patches 1-2 -> reviewer audits diff
- **Parallel scout:** 2-3 investigator calls in one message (different angles), aggregate results
- **Single-shot edit:** Skip investigator, hand exact path:line to builder directly

### When NOT to use
- **cavecrew-builder** without knowing the file first — spawn investigator
- **cavecrew-reviewer** for "general feedback" — it returns findings only, no opinions
- Expecting prose — output is structured, paraphrase if a human reads it
