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
3. Output findings sorted by file -> line

## Tags
- `delete:` dead code, unused flexibility, speculative feature
- `stdlib:` hand-rolled thing the standard library ships -> name the function
- `native:` dependency or code doing what the platform does -> name the feature
- `yagni:` abstraction with one implementation, config nobody sets -> inline or remove
- `shrink:` same logic, fewer lines -> show shorter form

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
