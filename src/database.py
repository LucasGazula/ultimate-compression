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
    conn.commit()
    conn.close()
