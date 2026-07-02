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
| Compression Rate | (saved / original) x 100 |
| Cost Saved | Based on configured $/M input/output token costs |
| By Tool | Breakdown per compression engine |

### Display format
Show the compressed output of `uc status` — totals, breakdown by tool, recent activity. If the dashboard is running, also mention: `http://localhost:20129/dashboard/` for visual charts.
