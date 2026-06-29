import sys
import os

# Add package root to sys.path to enable absolute imports when run directly as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import traceback
from src.rtk import compress_text
from src import database

# Disable print to stdout for standard logging to prevent breaking JSON-RPC stdio protocol
def log_err(msg):
    sys.stderr.write(f"[MCP Error] {msg}\n")
    sys.stderr.flush()

def read_input_loop():
    """Main input loop reading from stdin and writing to stdout."""
    # Ensure stdin is in UTF-8
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        
    log_err("Starting ultimate-compression MCP server...")
    
    # Initialize DB in case it's the first run
    database.init_db()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            req = json.loads(line.strip())
            method = req.get("method")
            req_id = req.get("id")
            
            # Dispatch
            if method == "initialize":
                handle_initialize(req_id)
            elif method == "notifications/initialized" or method == "initialized":
                pass # Initialized notification, no response
            elif method == "tools/list":
                handle_tools_list(req_id)
            elif method == "tools/call":
                handle_tools_call(req_id, req.get("params", {}))
            else:
                # Unsupported method
                if req_id is not None:
                    send_error(req_id, -32601, f"Method not found: {method}")
                    
        except Exception as e:
            log_err(f"Error in read loop: {e}\n{traceback.format_exc()}")

def send_response(response_dict):
    """Sends JSON-RPC response to stdout followed by newline."""
    payload = json.dumps(response_dict)
    sys.stdout.write(payload + "\n")
    sys.stdout.flush()

def send_error(req_id, code, message):
    send_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": code,
            "message": message
        }
    })

def handle_initialize(req_id):
    send_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "ultimate-compression",
                "version": "1.0.0"
            }
        }
    })

def handle_tools_list(req_id):
    send_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "tools": [
                {
                    "name": "compress_text",
                    "description": (
                        "Compresses a verbose text block, terminal output, git diff, or log output "
                        "using local RTK token-saving compression algorithms. Use this to reduce "
                        "token usage before sending verbose data to the LLM."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The raw verbose text to compress."
                            }
                        },
                        "required": ["text"]
                    }
                },
                {
                    "name": "compress_file",
                    "description": (
                        "Reads a local file from disk, applies smart AST or prose compression, "
                        "and returns the compressed content to fit in small context windows."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Absolute file path on the system to read and compress."
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            ]
        }
    })

def compress_via_headroom(text):
    """Compresses text via Headroom's v1/compress API if headroom is enabled."""
    settings = database.get_settings()
    if not settings.get("headroomEnabled") or not settings.get("headroomUrl"):
        return None, 0
        
    import requests
    url = settings["headroomUrl"].rstrip("/")
    payload = {
        "messages": [
            {"role": "tool", "content": text}
        ],
        "model": "gemini-1.5-flash"
    }
    
    try:
        res = requests.post(f"{url}/v1/compress", json=payload, timeout=5.0)
        if res.status_code == 200:
            data = res.json()
            messages = data.get("messages", [])
            if messages and len(messages) > 0:
                compressed = messages[0].get("content", text)
                tokens_before = data.get("tokens_before", len(text) // 3)
                tokens_after = data.get("tokens_after", len(compressed) // 3)
                saved = data.get("tokens_saved", tokens_before - tokens_after)
                if saved > 0:
                    return compressed, saved
    except Exception as e:
        log_err(f"Failed to call headroom in MCP: {e}")
    return None, 0

def handle_tools_call(req_id, params):
    name = params.get("name")
    arguments = params.get("arguments", {})
    
    if name == "compress_text":
        text = arguments.get("text", "")
        if not text:
            send_tool_result(req_id, "Error: 'text' parameter is empty.")
            return
            
        try:
            # Try Headroom compression first
            compressed, saved = compress_via_headroom(text)
            if saved > 0:
                orig_tokens = len(text) // 3
                comp_tokens = len(compressed) // 3
                database.log_compression("headroom", "mcp-tool-headroom", orig_tokens, comp_tokens)
                send_tool_result(req_id, compressed)
                return
                
            # Fallback to RTK
            compressed, filter_name, saved = compress_text(text)
            if saved > 0:
                orig_tokens = len(text) // 3
                comp_tokens = len(compressed) // 3
                database.log_compression("rtk", f"mcp-tool-{filter_name}", orig_tokens, comp_tokens)
                send_tool_result(req_id, compressed)
            else:
                send_tool_result(req_id, text)
        except Exception as e:
            send_tool_result(req_id, f"Error running compression: {str(e)}")
            
    elif name == "compress_file":
        file_path = arguments.get("file_path", "")
        if not file_path:
            send_tool_result(req_id, "Error: 'file_path' parameter is empty.")
            return
            
        if not os.path.exists(file_path):
            send_tool_result(req_id, f"Error: File does not exist: {file_path}")
            return
            
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            # Try Headroom compression first
            compressed, saved = compress_via_headroom(content)
            if saved > 0:
                orig_tokens = len(content) // 3
                comp_tokens = len(compressed) // 3
                database.log_compression("headroom", "mcp-file-headroom", orig_tokens, comp_tokens)
                send_tool_result(req_id, compressed)
                return
                
            # Fallback to RTK
            compressed, filter_name, saved = compress_text(content)
            if saved > 0:
                orig_tokens = len(content) // 3
                comp_tokens = len(compressed) // 3
                database.log_compression("rtk", f"mcp-file-{filter_name}", orig_tokens, comp_tokens)
                send_tool_result(req_id, compressed)
            else:
                send_tool_result(req_id, content)
        except Exception as e:
            send_tool_result(req_id, f"Error compressing file: {str(e)}")
    else:
        send_error(req_id, -32601, f"Tool not found: {name}")

def send_tool_result(req_id, text_content):
    send_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": text_content
                }
            ],
            "isError": False
        }
    })

if __name__ == "__main__":
    read_input_loop()
