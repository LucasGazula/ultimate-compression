# Ultimate Compression (`uc`)

**Ultimate Compression** is a lightweight, cross-platform local developer tool designed to optimize token usage and reduce LLM costs. It bundles four powerful open-source utilities (**RTK**, **Headroom**, **Caveman**, and **Ponytail**) into a single, unified system running locally on your machine (compatible with Windows 11, macOS, Linux, and WSL).

By leveraging shell wrappers (shims) for local commands and a stateless API proxy/MCP server, **Ultimate Compression** reduces token usage by 60–90% while keeping your subscription accounts safe from proxy-related bans.

---

## Features

- **Command-Line Shims (RTK)**: Intercepts verbose CLI commands like `git diff`, `git status`, `grep`, and `ls` at the shell level, compressing their outputs locally before sending them to your AI agent.
- **Stateless API Proxy**: For tools where you can configure the API Base URL, the local proxy intercepts requests, applies context compression, and injects optimization prompts.
- **MCP Server**: Seamlessly integrates with modern agents (like Antigravity CLI and Claude Code) as a Model Context Protocol server, enabling safe, ban-proof context compression.
- **Telemetry Dashboard (SQLite)**: A local web UI served on `http://localhost:20129/dashboard/` that displays real-time statistics, token savings, cost reduction, and tool activity logs.
- **Dynamic Mode**: Automatically routes requests via MCP for subscription-based agents and via Proxy for API key-based tools.
- **Interactive Configuration TUI**: View stats and edit tool parameters directly from your terminal session using keyboard arrow keys.

---

## Installation

Run the appropriate one-liner installer command in your terminal:

### Linux / WSL / macOS
```bash
curl -fsSL https://raw.githubusercontent.com/LucasGazula/ultimate-compression/main/install.sh | bash
```

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/LucasGazula/ultimate-compression/main/install.ps1 | iex
```

*The installer will install all files directly to your home directory (`~/.ultimate-compression`) and add the `uc` CLI command to your PATH.*

---

## Usage

Use the `uc` CLI command to manage and configure Ultimate Compression:

### Start Backend Services
Start the local FastAPI server and Docker containers:
```bash
uc start
```

### Stop Backend Services
Stop local servers and containers:
```bash
uc stop
```

### System Status & Stats
View server status, lifetime token savings, tool breakdown, and recent activity logs directly in the terminal:
```bash
uc status
```

### Interactive Settings Configuration
Open the terminal-based interactive Configuration TUI. Use **Up/Down** arrow keys to navigate, **Left/Right** to toggle boolean settings or cycle options, and **Enter** to edit numeric/string fields:
```bash
uc config
```

### Set Settings directly
Configure parameters programmatically:
```bash
uc config --set <KEY>=<VALUE>
```

### Setup Workspace Rules
Bootstrap the current directory with agent optimization rules (adds `.agents/AGENTS.md`):
```bash
uc init
```

### Print Shell Environment Setup
Output proxy environment setup variables to load into your active shell:
```bash
uc env
```

---

## Credits & Thanks

This project is a compilation and orchestration of incredible work done by the open-source community. We want to thank and credit the original authors of the following projects:

1. **RTK (Rust Token Killer)** — [rtk-ai/rtk](https://github.com/rtk-ai/rtk)
   * *Contribution*: Original Rust-based CLI proxy concept and filters to compress terminal outputs.
2. **Headroom** — [chopratejas/headroom](https://github.com/chopratejas/headroom) by **Tejas Chopra**
   * *Contribution*: Context-Compressed Retrieval (CCR) concept and context compression layers.
3. **Caveman** — [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) by **Julius Brussee**
   * *Contribution*: Concept of forcing the LLM to output concise, filler-free "caveman-speak".
4. **Ponytail** — [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) by **Dietrich Gebert**
   * *Contribution*: Prompt guidelines biasing the model toward minimal, YAGNI-compliant code.
5. **9router** — [9router/9router](https://github.com/9router/9router)
   * *Contribution*: Inspiration for unified proxy orchestration, local localization, and JS-based filter ports.

*Thank you to all the original authors for making these tools available to the developer community!*

---

## License

MIT License. See LICENSE for details.
