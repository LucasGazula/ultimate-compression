#!/usr/bin/env python3
import sys
import os

# Configure stdout and stderr to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Self-relaunch in virtualenv if available
venv_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(venv_dir, ".venv", "bin", "python")
if not os.path.exists(venv_python):
    venv_python = os.path.join(venv_dir, ".venv", "Scripts", "python.exe")

if os.path.exists(venv_python) and sys.executable != venv_python:
    os.execv(venv_python, [venv_python] + sys.argv)

import argparse
import subprocess
import json
import signal
from datetime import datetime


# Set up path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import database
from src.rtk import compress_text

PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uc.pid")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uc.log")

def get_real_path():
    return os.path.dirname(os.path.abspath(__file__))

def is_process_running(pid):
    if os.name == 'nt':
        try:
            res = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
            return str(pid) in res.stdout
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, ValueError, OSError):
            return False

def start_server():
    """Starts the FastAPI backend and Docker Headroom container."""
    database.init_db()
    
    # Check if server is already running
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            if is_process_running(pid):
                print("Ultimate Compression backend already running.")
                return
            else:
                os.remove(PID_FILE)
        except (ValueError, OSError):
            os.remove(PID_FILE)
            
    print("Starting Ultimate Compression server on port 20129...")
    
    # Run Uvicorn in background
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "src.main:app", 
        "--host", "0.0.0.0", 
        "--port", "20129", 
        "--log-level", "warning"
    ]
    
    log_fd = open(LOG_FILE, "w")
    proc = subprocess.Popen(
        cmd, 
        cwd=get_real_path(),
        stdout=log_fd, 
        stderr=log_fd,
        start_new_session=True # Detach process
    )
    
    # Save PID
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
        
    print(f"Backend started (PID: {proc.pid}). Logs: {LOG_FILE}")
    print("Dashboard available at: http://localhost:20129/dashboard/")
    
    # Check Headroom Docker container
    settings = database.get_settings()
    if settings.get("headroomEnabled"):
        from src.main import check_headroom_docker
        check_headroom_docker()

def stop_server():
    """Stops the FastAPI backend and Headroom container."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            print(f"Stopping backend (PID: {pid})...")
            
            # Send stop command cross-platform
            if os.name == 'nt':
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
            
            # Verify and clean up
            os.remove(PID_FILE)
            print("Ultimate Compression backend stopped.")
        except Exception as e:
            print(f"Error stopping backend: {e}")
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
    else:
        print("Backend is not running.")
        
    # Optional: stop headroom container
    try:
        res = subprocess.run(["docker", "ps", "--filter", "name=headroom", "--format", "{{.Names}}"], capture_output=True, text=True)
        if "headroom" in res.stdout:
            print("Stopping Headroom Docker container...")
            subprocess.run(["docker", "stop", "headroom"], stdout=subprocess.DEVNULL)
    except Exception:
        pass

def print_env():
    """Outputs environment variables to initialize the current shell session."""
    shims_path = os.path.join(get_real_path(), "shims")
    
    # Detect if we are on Windows or Unix
    is_windows = os.name == 'nt' or 'comspec' in os.environ.get('PROMPT', '').lower()
    
    if is_windows:
        # PowerShell output
        print(f'$env:PATH = "{shims_path};" + $env:PATH')
        print('$env:OPENAI_API_BASE = "http://localhost:20129/v1"')
        print('$env:OPENAI_BASE_URL = "http://localhost:20129/v1"')
        print('$env:ANTHROPIC_API_BASE = "http://localhost:20129/v1"')
        print('$env:ANTHROPIC_BASE_URL = "http://localhost:20129/v1"')
        print('$env:GEMINI_API_BASE = "http://localhost:20129/v1"')
        print('$env:GOOGLE_API_BASE = "http://localhost:20129/v1"')
        print('$env:ANTIGRAVITY_BASE_URL = "http://localhost:20129/v1"')
        print('$env:API_BASE = "http://localhost:20129/v1"')
        print('# Execute: uc env | iex')
    else:
        # Bash / Zsh output
        print(f'export PATH="{shims_path}:$PATH"')
        print('export OPENAI_API_BASE="http://localhost:20129/v1"')
        print('export OPENAI_BASE_URL="http://localhost:20129/v1"')
        print('export ANTHROPIC_API_BASE="http://localhost:20129/v1"')
        print('export ANTHROPIC_BASE_URL="http://localhost:20129/v1"')
        print('export GEMINI_API_BASE="http://localhost:20129/v1"')
        print('export GOOGLE_API_BASE="http://localhost:20129/v1"')
        print('export ANTIGRAVITY_BASE_URL="http://localhost:20129/v1"')
        print('export API_BASE="http://localhost:20129/v1"')
        print('# Execute: eval $(uc env)')

def handle_rtk_filter(action):
    """Filters stdin text using RTK and writes to stdout."""
    # Ensure database settings are initialized
    database.init_db()
    settings = database.get_settings()
    
    # Read raw text from stdin
    raw_input = sys.stdin.read()
    
    if not settings.get("rtkEnabled") or not raw_input.strip():
        # Fallback to verbatim stdout
        sys.stdout.write(raw_input)
        sys.stdout.flush()
        return

    # Process compression
    compressed, filter_name, saved = compress_text(raw_input)
    
    if saved > 0:
        # Log compression in database
        orig_tokens = len(raw_input) // 3
        comp_tokens = len(compressed) // 3
        database.log_compression("rtk", f"shim-{action}-{filter_name}", orig_tokens, comp_tokens)
        sys.stdout.write(compressed)
    else:
        sys.stdout.write(raw_input)
        
    sys.stdout.flush()

def init_project():
    """Initializes the active directory with project-scoped rules for Antigravity/Claude Code."""
    database.init_db()
    settings = database.get_settings()
    
    agents_dir = os.path.join(os.getcwd(), ".agents")
    if not os.path.exists(agents_dir):
        os.makedirs(agents_dir, exist_ok=True)
        print("Created .agents/ directory.")
        
    agents_file = os.path.join(agents_dir, "AGENTS.md")
    
    # Write custom rules
    rules = []
    rules.append("# Ultimate Compression: Agent Rules\n")
    rules.append("This file contains rules for local agent optimization. Modifying settings in the dashboard will update these rules.\n")
    
    from src import prompts
    
    # Add Caveman rules
    if settings.get("cavemanEnabled") and settings.get("cavemanLevel") in prompts.CAVEMAN_PROMPTS:
        level = settings["cavemanLevel"]
        rules.append("## 🪨 Caveman Style (Constraint)")
        rules.append(prompts.CAVEMAN_PROMPTS[level])
        rules.append("")
        
    # Add Ponytail rules
    if settings.get("ponytailEnabled") and settings.get("ponytailLevel") in prompts.PONYTAIL_PROMPTS:
        level = settings["ponytailLevel"]
        rules.append("## 💈 Ponytail (Constraint)")
        rules.append(prompts.PONYTAIL_PROMPTS[level])
        rules.append("")
        
    # Add Headroom / MCP configuration instructions
    mcp_path = os.path.join(get_real_path(), "src", "mcp_server.py")
    rules.append("## ⚡ Model Context Protocol (MCP) Integration")
    rules.append(f"To enable direct Headroom and RTK tools in your agent, add this command to your MCP server list:")
    rules.append(f"Command: `{sys.executable} {mcp_path}`\n")
    
    with open(agents_file, "w", encoding="utf-8") as f:
        f.write("\n".join(rules))
        
    print(f"Successfully configured workspace rules in: {agents_file}")

    # Auto-configure shell profiles (Bash/Zsh on Linux/Mac, PowerShell on Windows/Linux)
    home = os.path.expanduser("~")
    shims_path = os.path.join(get_real_path(), "shims")
    
    # Register MCP server globally in all common agent configuration folders
    mcp_config = {
        "command": sys.executable,
        "args": [os.path.join(get_real_path(), "src", "mcp_server.py")]
    }
    
    mcp_targets = [
        os.path.join(home, ".gemini", "antigravity-cli", "mcp_config.json"),
        os.path.join(home, ".gemini", "config", "mcp_config.json"),
        os.path.join(home, ".clauderc.json"),
        os.path.join(home, ".claude", "settings.json")
    ]
    
    for path in mcp_targets:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {}
            if os.path.exists(path) and os.path.getsize(path) > 0:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            if not isinstance(data, dict):
                data = {}
            if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
                data["mcpServers"] = {}
            data["mcpServers"]["ultimate-compression"] = mcp_config
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Registered MCP server in: {path}")
        except Exception as e:
            print(f"Could not register MCP server in {path}: {e}")

    # 1. Linux/Unix Shells (.bashrc, .zshrc, .profile)
    env_block_sh = f"""
# >>> ultimate-compression env >>>
export PATH="{shims_path}:$PATH"
export OPENAI_API_BASE="http://localhost:20129/v1"
export OPENAI_BASE_URL="http://localhost:20129/v1"
export ANTHROPIC_API_BASE="http://localhost:20129/v1"
export ANTHROPIC_BASE_URL="http://localhost:20129/v1"
export GEMINI_API_BASE="http://localhost:20129/v1"
export GOOGLE_API_BASE="http://localhost:20129/v1"
export ANTIGRAVITY_BASE_URL="http://localhost:20129/v1"
export API_BASE="http://localhost:20129/v1"
# <<< ultimate-compression env <<<
"""
    
    sh_files = [os.path.join(home, ".bashrc"), os.path.join(home, ".zshrc"), os.path.join(home, ".profile")]
    updated_sh = False
    for path in sh_files:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "ultimate-compression env" not in content:
                    with open(path, "a", encoding="utf-8") as f:
                        f.write(env_block_sh)
                    print(f"Added proxy setup to shell profile: {path}")
                    updated_sh = True
            except Exception as e:
                print(f"Could not update shell profile {path}: {e}")

    # 2. Windows/PowerShell Shells (Microsoft.PowerShell_profile.ps1)
    env_block_ps = f"""
# >>> ultimate-compression env >>>
$env:PATH = "{shims_path};" + $env:PATH
$env:OPENAI_API_BASE = "http://localhost:20129/v1"
$env:OPENAI_BASE_URL = "http://localhost:20129/v1"
$env:ANTHROPIC_API_BASE = "http://localhost:20129/v1"
$env:ANTHROPIC_BASE_URL = "http://localhost:20129/v1"
$env:GEMINI_API_BASE = "http://localhost:20129/v1"
$env:GOOGLE_API_BASE = "http://localhost:20129/v1"
$env:ANTIGRAVITY_BASE_URL = "http://localhost:20129/v1"
$env:API_BASE = "http://localhost:20129/v1"
# <<< ultimate-compression env <<<
"""
    
    ps_profiles = [
        os.path.join(home, "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1"),
        os.path.join(home, "Documents", "PowerShell", "Microsoft.PowerShell_profile.ps1"),
        os.path.join(home, "My Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1"),
        os.path.join(home, "My Documents", "PowerShell", "Microsoft.PowerShell_profile.ps1"),
    ]
    
    updated_ps = False
    for path in ps_profiles:
        parent = os.path.dirname(path)
        if os.path.exists(parent) or (os.name == 'nt' and "PowerShell" in path):
            try:
                os.makedirs(parent, exist_ok=True)
                content = ""
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                if "ultimate-compression env" not in content:
                    with open(path, "a", encoding="utf-8") as f:
                        f.write(env_block_ps)
                    print(f"Added proxy setup to PowerShell profile: {path}")
                    updated_ps = True
            except Exception as e:
                print(f"Could not update PowerShell profile {path}: {e}")
                
    if updated_sh or updated_ps:
        print("\n👉 Environment variables configured globally!")
        if sys.stdout.isatty() and sys.stdin.isatty():
            shell = os.environ.get("SHELL")
            if shell and os.path.exists(shell):
                print(f"🔄 Automatically reloading your shell ({os.path.basename(shell)}) to apply changes...")
                os.execvp(shell, [shell])
            elif os.name == 'nt':
                print(f"🔄 Automatically reloading PowerShell to apply changes...")
                os.system("powershell")
        else:
            print("Please reload your shell ('exec bash' or restart terminal) to apply proxy environment changes.")

OPTION_VALUES = {
    "cavemanLevel": ["lite", "full", "ultra"],
    "ponytailLevel": ["lite", "full", "ultra"],
    "dynamicMode": ["dynamic", "mcp", "proxy"]
}

settings_keys = [
    ("rtkEnabled", "RTK Enabled", "bool"),
    ("headroomEnabled", "Headroom Enabled", "bool"),
    ("headroomUrl", "Headroom URL", "str"),
    ("headroomCompressUserMessages", "Headroom Compress User Msgs", "bool"),
    ("cavemanEnabled", "Caveman Enabled", "bool"),
    ("cavemanLevel", "Caveman Level", "option"),
    ("ponytailEnabled", "Ponytail Enabled", "bool"),
    ("ponytailLevel", "Ponytail Level", "option"),
    ("dynamicMode", "Dynamic Mode", "option"),
    ("tokenCostPerMillionInput", "Input Token Cost ($/M)", "float"),
    ("tokenCostPerMillionOutput", "Output Token Cost ($/M)", "float"),
]

def run_interactive_tui(stdscr):
    import curses
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN) # Highlight
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK) # Enabled/True
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK) # Disabled/False
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Header
    
    settings = database.get_settings()
    working_settings = settings.copy()
    current_row = 0
    modified = False
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        if height < 18 or width < 70:
            stdscr.addstr(0, 0, "Terminal window too small.")
            stdscr.addstr(1, 0, f"Current: {width}x{height}. Need: at least 70x18.")
            stdscr.addstr(3, 0, "Press any key to exit.")
            stdscr.refresh()
            stdscr.getch()
            return False
            
        title = "ULTIMATE COMPRESSION CONFIGURATION"
        stdscr.addstr(0, max(0, (width - len(title)) // 2), title, curses.color_pair(4) | curses.A_BOLD)
        
        instr1 = "Use UP/DOWN to navigate | LEFT/RIGHT to toggle/cycle | ENTER to edit value"
        instr2 = "Press [S] to Save & Exit | [Q] or [Esc] to Quit"
        stdscr.addstr(1, max(0, (width - len(instr1)) // 2), instr1, curses.A_DIM)
        stdscr.addstr(2, max(0, (width - len(instr2)) // 2), instr2, curses.A_DIM)
        
        start_y = 4
        for idx, (key, label, val_type) in enumerate(settings_keys):
            y = start_y + idx
            val = working_settings.get(key)
            label_str = f"  {label:<30}: "
            stdscr.addstr(y, 2, label_str)
            
            val_x = 2 + len(label_str)
            
            if val_type == "bool":
                val_str = "ON" if val else "OFF"
                color = curses.color_pair(2) if val else curses.color_pair(3)
                if idx == current_row:
                    stdscr.addstr(y, val_x, f"[{val_str}]", curses.color_pair(1) | curses.A_BOLD)
                else:
                    stdscr.addstr(y, val_x, f"[{val_str}]", color | curses.A_BOLD)
            elif val_type == "option":
                opt_str = f"< {val} >"
                if idx == current_row:
                    stdscr.addstr(y, val_x, opt_str, curses.color_pair(1) | curses.A_BOLD)
                else:
                    stdscr.addstr(y, val_x, opt_str, curses.A_NORMAL)
            else:
                val_str = str(val)
                if idx == current_row:
                    stdscr.addstr(y, val_x, val_str, curses.color_pair(1) | curses.A_BOLD)
                else:
                    stdscr.addstr(y, val_x, val_str, curses.A_NORMAL)
                    
        status_y = start_y + len(settings_keys) + 1
        if status_y < height - 1:
            if modified:
                stdscr.addstr(status_y, 2, "* Settings modified (Press S to Save)", curses.color_pair(4) | curses.A_BOLD)
            else:
                stdscr.addstr(status_y, 2, "Settings match saved state", curses.A_DIM)
                
        stdscr.refresh()
        key = stdscr.getch()
        
        if key in (curses.KEY_UP, ord('k')):
            current_row = (current_row - 1) % len(settings_keys)
        elif key in (curses.KEY_DOWN, ord('j')):
            current_row = (current_row + 1) % len(settings_keys)
        elif key in (curses.KEY_LEFT, curses.KEY_RIGHT, ord('h'), ord('l'), ord(' ')):
            s_key, s_label, val_type = settings_keys[current_row]
            val = working_settings.get(s_key)
            if val_type == "bool":
                working_settings[s_key] = not val
                modified = True
            elif val_type == "option":
                opts = OPTION_VALUES[s_key]
                cur_idx = opts.index(val) if val in opts else 0
                step = -1 if key in (curses.KEY_LEFT, ord('h')) else 1
                working_settings[s_key] = opts[(cur_idx + step) % len(opts)]
                modified = True
        elif key in (10, 13, curses.KEY_ENTER):
            s_key, s_label, val_type = settings_keys[current_row]
            if val_type in ("str", "float", "int"):
                curses.curs_set(1)
                stdscr.move(height - 1, 0)
                stdscr.clrtoeol()
                stdscr.addstr(height - 1, 2, f"Enter new {s_label}: ")
                stdscr.refresh()
                curses.echo()
                input_bytes = stdscr.getstr(height - 1, len(s_label) + 15, 60)
                curses.noecho()
                curses.curs_set(0)
                
                input_str = input_bytes.decode('utf-8').strip()
                if input_str:
                    try:
                        if val_type == "int":
                            working_settings[s_key] = int(input_str)
                        elif val_type == "float":
                            working_settings[s_key] = float(input_str)
                        else:
                            working_settings[s_key] = input_str
                        modified = True
                    except ValueError:
                        pass
        elif key in (ord('s'), ord('S')):
            if modified:
                database.update_settings(working_settings)
                if os.path.exists(os.path.join(os.getcwd(), ".agents", "AGENTS.md")):
                    init_project()
                return True
            return False
        elif key in (ord('q'), ord('Q'), 27):
            return False

def run_interactive_config():
    try:
        import curses
    except ImportError:
        print("Warning: The 'curses' module is not available. TUI configuration is disabled.")
        print("To enable TUI on Windows, run: pip install windows-curses")
        print("Falling back to text-based configuration dashboard:")
        return False
    try:
        saved = curses.wrapper(run_interactive_tui)
        if saved:
            print("Settings updated successfully.")
        else:
            print("Configuration closed without changes.")
        return True
    except Exception as e:
        print(f"Error running interactive config: {e}")
        return False

def handle_config(sets=None, interactive=False):
    database.init_db()
    if sets:
        from src.database import DEFAULT_SETTINGS
        updates = {}
        for s in sets:
            if "=" not in s:
                print(f"Error: Invalid set format '{s}'. Use KEY=VALUE.")
                sys.exit(1)
            key, val_str = s.split("=", 1)
            key = key.strip()
            val_str = val_str.strip()
            if key not in DEFAULT_SETTINGS:
                print(f"Error: Unknown setting '{key}'.")
                print("Available settings: " + ", ".join(DEFAULT_SETTINGS.keys()))
                sys.exit(1)
            default_val = DEFAULT_SETTINGS[key]
            try:
                if isinstance(default_val, bool):
                    val = val_str.lower() in ("true", "1", "yes", "on", "t")
                elif isinstance(default_val, int):
                    val = int(val_str)
                elif isinstance(default_val, float):
                    val = float(val_str)
                else:
                    val = val_str
                updates[key] = val
            except ValueError:
                print(f"Error: Could not convert '{val_str}' to the type of '{key}'.")
                sys.exit(1)
        database.update_settings(updates)
        print("Settings updated successfully.")
        if os.path.exists(os.path.join(os.getcwd(), ".agents", "AGENTS.md")):
            print("Updating workspace agent rules...")
            init_project()
    elif interactive or sys.stdout.isatty():
        run_interactive_config()
        
    stats = database.get_stats()
    settings = database.get_settings()
    print("=========================================")
    print("      ULTIMATE COMPRESSION DASHBOARD")
    print("=========================================")
    totals = stats["totals"]
    print("Totals:")
    print(f"  Original Tokens:  {totals['original_tokens']:,}")
    print(f"  Compressed:       {totals['compressed_tokens']:,}")
    print(f"  Saved Tokens:     {totals['tokens_saved']:,} ({totals['compression_rate']}% rate)")
    print(f"  Cost Saved:       ${totals['cost_saved_usd']:.4f} USD")
    print()
    print("Savings by Tool:")
    for tool, data in stats["by_tool"].items():
        print(f"  {tool:<10}:      {data['saved']:,} tokens (${data['cost_saved']:.4f})")
    print()
    print("=========================================")
    print("               SETTINGS")
    print("=========================================")
    for key, val in settings.items():
        print(f"  {key:<30} {val}")
    print("=========================================")
    print("To change a setting, run:")
    print("  uc config --set <KEY>=<VALUE>")

def handle_status():
    database.init_db()
    running, pid = False, None
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            if is_process_running(pid):
                running = True
        except (ValueError, OSError):
            pass
            
    print("=========================================")
    print("             SYSTEM STATUS")
    print("=========================================")
    if running:
        print(f"  Backend Server:  RUNNING (PID: {pid})")
        print(f"  Dashboard URL:   http://localhost:20129/dashboard/")
    else:
        print("  Backend Server:  STOPPED")
    print()
    
    stats = database.get_stats()
    totals = stats["totals"]
    print("=========================================")
    print("      ULTIMATE COMPRESSION DASHBOARD")
    print("=========================================")
    print("Totals:")
    print(f"  Original Tokens:  {totals['original_tokens']:,}")
    print(f"  Compressed:       {totals['compressed_tokens']:,}")
    print(f"  Saved Tokens:     {totals['tokens_saved']:,} ({totals['compression_rate']}% rate)")
    print(f"  Cost Saved:       ${totals['cost_saved_usd']:.4f} USD")
    print()
    print("Savings by Tool:")
    for tool, data in stats["by_tool"].items():
        print(f"  {tool:<10}:      {data['saved']:,} tokens (${data['cost_saved']:.4f})")
    print()
    
    print("=========================================")
    print("             RECENT ACTIVITY")
    print("=========================================")
    recent = stats.get("recent", [])
    if recent:
        for log in recent[:5]:
            ts = log["timestamp"].split(".")[0]
            print(f"  {ts} | {log['tool']:<8} | {log['action'][:20]:<20} | Saved {log['tokens_saved']:,} tokens (${log['cost_saved_usd']:.4f})")
    else:
        print("  No activity logged yet.")
    print("=========================================")

def main():
    parser = argparse.ArgumentParser(description="Ultimate Compression (uc) CLI tool.")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    subparsers.add_parser("start", help="Starts the uc local server & docker dependencies")
    subparsers.add_parser("stop", help="Stops the uc local server & docker dependencies")
    subparsers.add_parser("env", help="Prints session setup environment variables")
    subparsers.add_parser("init", help="Bootstraps the current directory with agent optimization rules")
    subparsers.add_parser("status", help="Displays current system status, compression stats and recent activity")
    
    config_parser = subparsers.add_parser("config", help="View dashboard stats and get/set configuration")
    config_parser.add_argument("--set", action="append", help="Set configuration value (e.g. --set cavemanEnabled=true)")
    config_parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive TUI config")
    
    filter_parser = subparsers.add_parser("rtk-filter", help="Filters stdin content and returns compressed text")
    filter_parser.add_argument("action", help="The command action identifier (e.g. git-diff, grep)")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start_server()
    elif args.command == "stop":
        stop_server()
    elif args.command == "env":
        print_env()
    elif args.command == "init":
        init_project()
    elif args.command == "config":
        handle_config(args.set, args.interactive)
    elif args.command == "status":
        handle_status()
    elif args.command == "rtk-filter":
        handle_rtk_filter(args.action)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
