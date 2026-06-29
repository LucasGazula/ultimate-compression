#!/usr/bin/env python3
import sys
import os

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

def start_server():
    """Starts the FastAPI backend and Docker Headroom container."""
    database.init_db()
    
    # Check if server is already running
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            print("Ultimate Compression backend already running.")
            return
        except (ProcessLookupError, ValueError, OSError):
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
            
            # Send SIGTERM
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
    rules.append(f"Command: `python3 {mcp_path}`\n")
    
    with open(agents_file, "w") as f:
        f.write("\n".join(rules))
        
    print(f"Successfully configured workspace rules in: {agents_file}")

    # Auto-configure shell profiles (Bash/Zsh on Linux/Mac, PowerShell on Windows/Linux)
    home = os.path.expanduser("~")
    shims_path = os.path.join(get_real_path(), "shims")
    
    # Register MCP server globally in all common agent configuration folders
    mcp_config = {
        "command": "python3",
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

def handle_config(sets=None):
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

def main():
    parser = argparse.ArgumentParser(description="Ultimate Compression (uc) CLI tool.")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    subparsers.add_parser("start", help="Starts the uc local server & docker dependencies")
    subparsers.add_parser("stop", help="Stops the uc local server & docker dependencies")
    subparsers.add_parser("env", help="Prints session setup environment variables")
    subparsers.add_parser("init", help="Bootstraps the current directory with agent optimization rules")
    
    config_parser = subparsers.add_parser("config", help="View dashboard stats and get/set configuration")
    config_parser.add_argument("--set", action="append", help="Set configuration value (e.g. --set cavemanEnabled=true)")
    
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
        handle_config(args.set)
    elif args.command == "rtk-filter":
        handle_rtk_filter(args.action)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
