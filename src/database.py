import sqlite3
import os
import json
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ultimate_compression.db")

DEFAULT_SETTINGS = {
    "rtkEnabled": True,
    "headroomEnabled": False,
    "headroomUrl": "http://localhost:8787",
    "headroomCompressUserMessages": False,
    "cavemanEnabled": False,
    "cavemanLevel": "full",
    "ponytailEnabled": False,
    "ponytailLevel": "full",
    "dynamicMode": "dynamic", # "dynamic", "mcp", "proxy"
    "tokenCostPerMillionInput": 3.0,  # USD
    "tokenCostPerMillionOutput": 15.0 # USD
}

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compression_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tool TEXT NOT NULL,
            action TEXT NOT NULL,
            original_tokens INTEGER NOT NULL,
            compressed_tokens INTEGER NOT NULL,
            tokens_saved INTEGER NOT NULL,
            cost_saved_usd REAL NOT NULL
        )
    """)
    
    # Create settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Create crawled_transcripts tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawled_transcripts (
            session_id TEXT PRIMARY KEY,
            last_parsed_line INTEGER NOT NULL
        )
    """)
    
    # Insert default settings if not exists
    for key, val in DEFAULT_SETTINGS.items():
        cursor.execute("SELECT 1 FROM settings WHERE key = ?", (key,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(val)))
            
    conn.commit()
    conn.close()

def log_compression(tool, action, original_tokens, compressed_tokens, cost_saved_usd=0.0):
    """Logs a compression event in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate tokens saved
    tokens_saved = max(0, original_tokens - compressed_tokens)
    
    # Calculate estimated cost if cost_saved_usd is not provided
    if cost_saved_usd == 0.0 and tokens_saved > 0:
        settings = get_settings()
        cost_per_token = settings.get("tokenCostPerMillionInput", 3.0) / 1000000.0
        # For caveman/ponytail output token saving, use output token cost
        if tool in ("caveman", "ponytail"):
            cost_per_token = settings.get("tokenCostPerMillionOutput", 15.0) / 1000000.0
        cost_saved_usd = tokens_saved * cost_per_token
        
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    cursor.execute("""
        INSERT INTO compression_logs 
        (timestamp, tool, action, original_tokens, compressed_tokens, tokens_saved, cost_saved_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, tool, action, original_tokens, compressed_tokens, tokens_saved, cost_saved_usd))
    
    conn.commit()
    conn.close()
    return tokens_saved, cost_saved_usd

def get_settings():
    """Retrieves all settings from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    
    settings = DEFAULT_SETTINGS.copy()
    for row in rows:
        try:
            settings[row["key"]] = json.loads(row["value"])
        except Exception:
            pass
    return settings

def update_settings(updates):
    """Updates settings in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    for key, val in updates.items():
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(val)))
    conn.commit()
    conn.close()
    return get_settings()

def get_stats():
    """Compiles compression and token statistics from the SQLite database."""
    # Crawl local transcripts first to ensure statistics are up to date
    try:
        crawl_session_transcripts()
    except Exception as e:
        print(f"[Crawler] Error crawling transcripts: {e}")
        
    # Sync Headroom container metrics
    try:
        sync_headroom_stats()
    except Exception as e:
        print(f"[Crawler] Error syncing Headroom stats: {e}")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Total statistics
    cursor.execute("""
        SELECT 
            SUM(original_tokens) as total_orig,
            SUM(compressed_tokens) as total_comp,
            SUM(tokens_saved) as total_saved,
            SUM(cost_saved_usd) as total_cost_saved
        FROM compression_logs
    """)
    totals = cursor.fetchone()
    total_orig = totals["total_orig"] or 0
    total_comp = totals["total_comp"] or 0
    total_saved = totals["total_saved"] or 0
    total_cost_saved = totals["total_cost_saved"] or 0.0
    
    avg_rate = ((total_saved / total_orig) * 100) if total_orig > 0 else 0.0
    
    # 2. Tool breakdown
    cursor.execute("""
        SELECT 
            tool,
            SUM(tokens_saved) as saved,
            SUM(cost_saved_usd) as cost_saved
        FROM compression_logs
        GROUP BY tool
    """)
    tool_rows = cursor.fetchall()
    by_tool = {row["tool"]: {"saved": row["saved"], "cost_saved": row["cost_saved"]} for row in tool_rows}
    # Ensure all tools exist in output
    for t in ("rtk", "headroom", "caveman", "ponytail"):
        if t not in by_tool:
            by_tool[t] = {"saved": 0, "cost_saved": 0.0}
            
    # 3. Daily trends (last 7 days)
    cursor.execute("""
        SELECT 
            strftime('%Y-%m-%d', timestamp) as day,
            SUM(tokens_saved) as saved
        FROM compression_logs
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY day
        ORDER BY day ASC
    """)
    daily_rows = cursor.fetchall()
    daily_trend = {row["day"]: row["saved"] for row in daily_rows}
    
    # 4. Recent activity log (latest 10 logs)
    cursor.execute("""
        SELECT timestamp, tool, action, original_tokens, compressed_tokens, tokens_saved, cost_saved_usd
        FROM compression_logs
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    recent = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "totals": {
            "original_tokens": total_orig,
            "compressed_tokens": total_comp,
            "tokens_saved": total_saved,
            "cost_saved_usd": total_cost_saved,
            "compression_rate": round(avg_rate, 1)
        },
        "by_tool": by_tool,
        "daily_trend": daily_trend,
        "recent": recent
    }

def clear_logs():
    """Clears all compression logs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM compression_logs")
    cursor.execute("DELETE FROM crawled_transcripts")
    conn.commit()
    conn.close()

def crawl_session_transcripts():
    """
    Crawls local Antigravity CLI and Claude Code conversation transcripts to find
    assistant responses and log Caveman & Ponytail savings.
    """
    import glob
    conn = get_db_connection()
    cursor = conn.cursor()
    
    settings = get_settings()
    caveman_enabled = settings.get("cavemanEnabled", False)
    ponytail_enabled = settings.get("ponytailEnabled", False)
    caveman_level = settings.get("cavemanLevel", "full")
    ponytail_level = settings.get("ponytailLevel", "full")
    
    # 1. Gather all transcript files
    # Antigravity CLI logs: /home/pi/.gemini/antigravity-cli/brain/*/logs/transcript.jsonl
    search_pattern = "/home/pi/.gemini/antigravity-cli/brain/*/.system_generated/logs/transcript.jsonl"
    transcript_files = glob.glob(search_pattern)
    
    # Support Claude Code logs if they exist in standard paths
    claude_search = "/home/pi/.claude/projects/**/*.jsonl"
    transcript_files.extend(glob.glob(claude_search, recursive=True))
    
    for file_path in transcript_files:
        # Determine a clean session identifier from path
        session_id = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(file_path))))
        if not session_id or session_id == "logs" or len(session_id) < 10:
            session_id = os.path.basename(file_path)
            
        # Get last parsed line number
        cursor.execute("SELECT last_parsed_line FROM crawled_transcripts WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        last_parsed = row["last_parsed_line"] if row else 0
        
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            continue
            
        if len(lines) <= last_parsed:
            continue
            
        new_lines = lines[last_parsed:]
        output_tokens = 0
        
        for line in new_lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                # Antigravity shape
                if data.get("source") == "MODEL" and data.get("type") in ("PLANNER_RESPONSE", "assistant"):
                    content = data.get("content", "")
                    if content and isinstance(content, str):
                        # Estimate output tokens: ~4 chars per token for prose/fragments
                        output_tokens += len(content) // 4
                # Claude Code shape
                elif data.get("type") == "assistant" and data.get("message") and isinstance(data["message"], dict):
                    usage = data["message"].get("usage")
                    if usage:
                        output_tokens += usage.get("output_tokens", 0)
            except Exception:
                continue
                
        # If we found output tokens, calculate savings and log them!
        if output_tokens > 0:
            # Caveman
            if caveman_enabled:
                ratio_map = {"lite": 0.25, "full": 0.65, "ultra": 0.75}
                ratio = ratio_map.get(caveman_level, 0.65)
                saved = int(output_tokens * (ratio / (1.0 - ratio)))
                original = output_tokens + saved
                log_timestamp = datetime.utcnow().isoformat() + "Z"
                cost_per_token = settings.get("tokenCostPerMillionOutput", 15.0) / 1000000.0
                cost = saved * cost_per_token
                
                cursor.execute("""
                    INSERT INTO compression_logs 
                    (timestamp, tool, action, original_tokens, compressed_tokens, tokens_saved, cost_saved_usd)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (log_timestamp, "caveman", f"transcript-{session_id}-{caveman_level}", original, output_tokens, saved, cost))
                
            # Ponytail
            if ponytail_enabled:
                ratio_map = {"lite": 0.15, "full": 0.30, "ultra": 0.45}
                ratio = ratio_map.get(ponytail_level, 0.30)
                saved = int(output_tokens * (ratio / (1.0 - ratio)))
                original = output_tokens + saved
                log_timestamp = datetime.utcnow().isoformat() + "Z"
                cost_per_token = settings.get("tokenCostPerMillionOutput", 15.0) / 1000000.0
                cost = saved * cost_per_token
                
                cursor.execute("""
                    INSERT INTO compression_logs 
                    (timestamp, tool, action, original_tokens, compressed_tokens, tokens_saved, cost_saved_usd)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (log_timestamp, "ponytail", f"transcript-{session_id}-{ponytail_level}", original, output_tokens, saved, cost))

        # Update last parsed line
        cursor.execute("""
            INSERT OR REPLACE INTO crawled_transcripts (session_id, last_parsed_line)
            VALUES (?, ?)
        """, (session_id, len(lines)))
        
    conn.commit()
    conn.close()

def sync_headroom_stats():
    """
    Queries the local Headroom container on port 8787 and imports its
    lifetime token savings into the SQLite database.
    """
    import requests
    try:
        res = requests.get("http://127.0.0.1:8787/stats", timeout=0.3)
        if res.status_code != 200:
            return
        data = res.json()
        
        # Extract savings
        lifetime = data.get("persistent_savings", {}).get("lifetime", {})
        tokens_saved = lifetime.get("tokens_saved", 0)
        cost_saved = lifetime.get("compression_savings_usd", 0.0)
        total_input = lifetime.get("total_input_tokens", 0)
        
        if tokens_saved <= 0:
            return
            
        # Get currently logged headroom savings in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(tokens_saved) as total FROM compression_logs WHERE tool = 'headroom'")
        logged_row = cursor.fetchone()
        logged_saved = logged_row["total"] if logged_row and logged_row["total"] else 0
        
        delta_saved = tokens_saved - logged_saved
        if delta_saved > 0:
            # Estimate cost delta
            delta_cost = cost_saved * (delta_saved / tokens_saved) if tokens_saved > 0 else 0.0
            
            # Log delta to SQLite
            log_timestamp = datetime.utcnow().isoformat() + "Z"
            cursor.execute("""
                INSERT INTO compression_logs 
                (timestamp, tool, action, original_tokens, compressed_tokens, tokens_saved, cost_saved_usd)
                VALUES (?, 'headroom', 'docker-sync', ?, ?, ?, ?)
            """, (log_timestamp, total_input, total_input - delta_saved, delta_saved, delta_cost))
            
            conn.commit()
        conn.close()
    except Exception:
        # Silently fail if headroom is down
        pass


