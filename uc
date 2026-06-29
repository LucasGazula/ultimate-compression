#!/usr/bin/env python3
import sys
import os

# Self-relaunch in virtualenv if available
venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "python")
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

def main():
    parser = argparse.ArgumentParser(description="Ultimate Compression (uc) CLI tool.")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    subparsers.add_parser("start", help="Starts the uc local server & docker dependencies")
    subparsers.add_parser("stop", help="Stops the uc local server & docker dependencies")
    subparsers.add_parser("env", help="Prints session setup environment variables")
    subparsers.add_parser("init", help="Bootstraps the current directory with agent optimization rules")
    
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
    elif args.command == "rtk-filter":
        handle_rtk_filter(args.action)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
