---
name: ponytail-audit
description: >
  Audit the entire repository for over-engineering, unnecessary abstractions,
  and code bloat. Scans all source files. Use on "audit this repo",
  "find over-engineering", "where is the bloat".
---
Audit the whole repo for over-engineering. Rank findings by lines deletable. Output format per file.

## Tags
- `delete:` dead code, unused flexibility, speculative feature -> just delete it
- `stdlib:` hand-rolled thing the standard library ships -> name the function
- `native:` dependency or code doing what the platform does -> name the feature
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller -> inline or remove
- `shrink:` same logic, fewer lines -> show the shorter form

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
Read-only. Does not delete or modify files. Does not run linters or formatters.
