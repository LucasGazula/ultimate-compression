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
- **bug:** — broken behavior, will cause incident
- **risk:** — works but fragile (race, null check, swallowed error)
- **nit:** — style, naming, micro-optim. Author can ignore
- **q:** — genuine question, not a suggestion

## Drop
"I noticed that...", "It seems like...", "You might want to consider...", "Great work!" (say once at top), hedging ("perhaps", "I think"). Use `q:` if unsure.

## Keep
Exact line numbers. Exact symbol names in backticks. Concrete fix. The *why* if the fix isn't obvious.

## Examples
L42: user can be null after .find(). Add guard before .email.

L88-140: 50-line fn does 4 things. Extract validate/normalize/persist.

## Auto-Clarity
Drop terse for: security findings (CVE-class bugs need full explanation), architectural disagreements, onboarding contexts. Write a paragraph, then resume.

## Boundaries
Reviews only — does not write the fix, does not approve/request-changes, does not run linters.
