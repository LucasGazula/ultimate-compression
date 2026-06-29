import fastapi
from fastapi.responses import StreamingResponse
import requests
import json
import re
from . import database
from . import prompts
from .rtk import compress_text

router = fastapi.APIRouter()

import os
UPSTREAM_OPENAI = os.getenv("UC_UPSTREAM_OPENAI", "https://api.openai.com")
UPSTREAM_ANTHROPIC = os.getenv("UC_UPSTREAM_ANTHROPIC", "https://api.anthropic.com")
UPSTREAM_GEMINI = os.getenv("UC_UPSTREAM_GEMINI", "https://generativelanguage.googleapis.com")

def estimate_tokens(text):
    """Simple offline token estimator (3 chars = 1 token for code/diffs/logs)."""
    if not text:
        return 0
    return len(text) // 3

def process_rtk_compression(body):
    """Processes RTK compression on tool results in the message body in-place."""
    settings = database.get_settings()
    if not settings.get("rtkEnabled"):
        return body
        
    messages = body.get("messages") or body.get("input")
    if not isinstance(messages, list):
        return body

    for msg in messages:
        if not isinstance(msg, dict):
            continue
            
        role = msg.get("role")
        content = msg.get("content")
        
        # 1. OpenAI tool/function response shape
        if role == "tool" and isinstance(content, str):
            compressed, filter_name, saved = compress_text(content)
            if saved > 0:
                msg["content"] = compressed
                database.log_compression("rtk", f"openai-{filter_name}", estimate_tokens(content), estimate_tokens(compressed))
                
        # 2. Claude/Anthropic blocks shape
        elif isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                # Claude tool result content can be in a text block inside tool_result
                if part.get("type") == "tool_result":
                    tool_content = part.get("content")
                    if isinstance(tool_content, str):
                        compressed, filter_name, saved = compress_text(tool_content)
                        if saved > 0:
                            part["content"] = compressed
                            database.log_compression("rtk", f"claude-{filter_name}", estimate_tokens(tool_content), estimate_tokens(compressed))
                    elif isinstance(tool_content, list):
                        for subpart in tool_content:
                            if isinstance(subpart, dict) and subpart.get("type") == "text":
                                subtext = subpart.get("text")
                                if isinstance(subtext, str):
                                    compressed, filter_name, saved = compress_text(subtext)
                                    if saved > 0:
                                        subpart["text"] = compressed
                                        database.log_compression("rtk", f"claude-array-{filter_name}", estimate_tokens(subtext), estimate_tokens(compressed))
                                        
                elif part.get("type") == "text" and role == "tool":
                    subtext = part.get("text")
                    if isinstance(subtext, str):
                        compressed, filter_name, saved = compress_text(subtext)
                        if saved > 0:
                            part["text"] = compressed
                            database.log_compression("rtk", f"openai-array-{filter_name}", estimate_tokens(subtext), estimate_tokens(compressed))
    return body

def call_headroom_compress(messages, model, url, compress_user_messages=False):
    """Calls Headroom endpoint to compress context messages."""
    try:
        payload = {"messages": messages, "model": model}
        if compress_user_messages:
            payload["config"] = {"compress_user_messages": True}
            
        res = requests.post(f"{url.rstrip('/')}/v1/compress", json=payload, timeout=5.0)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data.get("messages"), list):
                return data["messages"], data.get("stats", {})
    except Exception as e:
        print(f"[Headroom] Failed to call headroom: {e}")
    return None, None

def process_headroom_compression(body, model, is_claude=False):
    """Applies Headroom context compression if enabled."""
    settings = database.get_settings()
    if not settings.get("headroomEnabled") or not settings.get("headroomUrl"):
        return body
        
    messages = body.get("messages") or body.get("input")
    if not isinstance(messages, list):
        return body
        
    # Translate Claude messages format to OpenAI shape if needed for Headroom
    # (Headroom standard v1/compress accepts OpenAI shaped messages)
    # Simple conversion here for local headless integration
    headroom_msgs = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        # Simplify block structures for Headroom parser if necessary
        if isinstance(content, list):
            text_parts = []
            for p in content:
                if isinstance(p, dict):
                    if p.get("type") == "text":
                        text_parts.append(p.get("text", ""))
                    elif p.get("type") == "tool_result" and isinstance(p.get("content"), str):
                        text_parts.append(p["content"])
            content = "\n".join(text_parts)
        headroom_msgs.append({"role": role, "content": str(content)})

    compressed_msgs, stats = call_headroom_compress(
        headroom_msgs, 
        model, 
        settings["headroomUrl"],
        settings.get("headroomCompressUserMessages", False)
    )
    
    if compressed_msgs:
        # Re-apply to request body
        body["messages" if "messages" in body else "input"] = compressed_msgs
        
        orig_tokens = stats.get("tokens_before", sum(estimate_tokens(m["content"]) for m in headroom_msgs))
        comp_tokens = stats.get("tokens_after", sum(estimate_tokens(m["content"]) for m in compressed_msgs))
        database.log_compression("headroom", "context-compress", orig_tokens, comp_tokens)
        
    return body

def inject_behavior_prompts(body):
    """Injects Caveman and Ponytail system prompts if enabled."""
    settings = database.get_settings()
    
    # Ponytail
    if settings.get("ponytailEnabled") and settings.get("ponytailLevel") in prompts.PONYTAIL_PROMPTS:
        level = settings["ponytailLevel"]
        prompts.inject_system_prompt(body, prompts.PONYTAIL_PROMPTS[level])
        # Log estimated savings: Ponytail saves ~30% code output, assume ~100 tokens saved per request
        database.log_compression("ponytail", f"inject-{level}", 100, 70)
        
    # Caveman
    if settings.get("cavemanEnabled") and settings.get("cavemanLevel") in prompts.CAVEMAN_PROMPTS:
        level = settings["cavemanLevel"]
        prompts.inject_system_prompt(body, prompts.CAVEMAN_PROMPTS[level])
        # Log estimated savings: Caveman saves ~65% output text, assume ~150 tokens saved per request
        database.log_compression("caveman", f"inject-{level}", 150, 52)
        
    return body

@router.post("/{path:path}")
async def handle_proxy(path: str, request: fastapi.Request):
    """Stateless proxy interceptor forwarding calls to upstream providers."""
    # 1. Read request headers and body
    headers = dict(request.headers)
    body_bytes = await request.body()
    
    body = {}
    if body_bytes:
        try:
            body = json.loads(body_bytes)
        except Exception:
            pass

    # 2. Determine target host and service
    upstream_url = None
    is_claude = "api.anthropic.com" in path or "x-api-key" in headers or "v1/messages" in path
    
    if is_claude:
        upstream_url = f"{UPSTREAM_ANTHROPIC}/{path}"
    elif "generativelanguage.googleapis.com" in path or "x-goog-api-key" in headers or "v1beta" in path:
        upstream_url = f"{UPSTREAM_GEMINI}/{path}"
    else:
        upstream_url = f"{UPSTREAM_OPENAI}/{path}"

    # 3. Process compression if it's a Chat/Messages completions request
    model = body.get("model", "default-model")
    is_chat = "completions" in path or "messages" in path or "models" in path
    
    if is_chat and body:
        # A. Apply RTK
        body = process_rtk_compression(body)
        
        # B. Apply Headroom
        body = process_headroom_compression(body, model, is_claude)
        
        # C. Apply Prompts (Caveman & Ponytail)
        body = inject_behavior_prompts(body)
        
        # Re-serialize body
        body_bytes = json.dumps(body).encode("utf-8")

    # Check for local dummy testing key to allow offline validation
    if headers.get("authorization") == "Bearer sk-dummy-key-for-local-testing":
        mock_content = "Olá! O proxy de compressão está funcionando com sucesso! As diretrizes do Caveman/Ponytail foram injetadas nos prompts do sistema."
        # If caveman is active, respond in caveman style for the demo
        settings = database.get_settings()
        if settings.get("cavemanEnabled"):
            mock_content = "Proxy ativo. Homem das cavernas falar. Compreensao ok."
            
        mock_response = {
            "id": "chatcmpl-mock123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": mock_content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 40,
                "completion_tokens": 30,
                "total_tokens": 70
            }
        }
        return fastapi.Response(
            content=json.dumps(mock_response),
            status_code=200,
            headers={"Content-Type": "application/json"}
        )

    # 4. Cleanup headers to avoid host header errors on upstream forwarding
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # 5. Call Upstream
    try:
        # Set steam based on request body or headers
        stream = body.get("stream", False) or "text/event-stream" in headers.get("accept", "")
        
        upstream_res = requests.post(
            upstream_url,
            headers=headers,
            data=body_bytes,
            stream=stream,
            timeout=30.0
        )
        
        # Return Streaming Response for SSE
        if stream:
            def sse_generator():
                for line in upstream_res.iter_lines():
                    if line:
                        yield line + b"\n"
            return StreamingResponse(
                sse_generator(),
                status_code=upstream_res.status_code,
                headers=dict(upstream_res.headers)
            )
        else:
            return fastapi.Response(
                content=upstream_res.content,
                status_code=upstream_res.status_code,
                headers=dict(upstream_res.headers)
            )
            
    except Exception as e:
        print(f"[Proxy] Upstream request failed: {e}")
        return fastapi.Response(
            content=json.dumps({"error": f"Upstream connection failed: {str(e)}"}),
            status_code=502,
            headers={"Content-Type": "application/json"}
        )
