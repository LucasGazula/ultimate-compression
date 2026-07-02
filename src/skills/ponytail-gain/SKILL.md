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
Ponytail Impact
- Lines written: ~N (est. M% of baseline)
- Files changed: N
- ponytail: markers: N active
- Run /ponytail-debt for details
- Run /ponytail-audit to find more

## Boundaries
One-shot display. Does not modify files.
