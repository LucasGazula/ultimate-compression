import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import os
import subprocess
from . import database
from . import proxy

# Initialize Database
database.init_db()

app = fastapi.FastAPI(title="Ultimate Compression (uc)")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API: Get Settings
@app.get("/api/settings")
def get_settings():
    return database.get_settings()

# API: Update Settings
@app.post("/api/settings")
def update_settings(settings: dict):
    updated = database.update_settings(settings)
    
    # Optional orchestrator trigger: If headroom is enabled, ensure docker container is running
    if updated.get("headroomEnabled"):
        check_headroom_docker()
        
    return updated

# API: Get Statistics
@app.get("/api/stats")
def get_stats():
    return database.get_stats()

# API: Clear Logs
@app.post("/api/clear")
def clear_logs():
    database.clear_logs()
    return {"status": "success", "message": "Compression logs cleared."}

# Mount Stateless API Proxy
app.include_router(proxy.router, prefix="/v1")

# Mount Static Files (Dashboard UI)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/dashboard", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# Default redirect to dashboard
@app.get("/")
def read_root():
    return fastapi.responses.RedirectResponse(url="/dashboard/")

def check_headroom_docker():
    """Tries to spin up Headroom container via Docker if it is not already running."""
    try:
        # Check if Docker is running
        res = subprocess.run(["docker", "ps", "-a"], capture_output=True, text=True)
        if res.returncode != 0:
            print("[Docker] Docker is not available or not running.")
            return False
            
        # Check if headroom container exists
        if "headroom" in res.stdout:
            # Check if it is running
            running_res = subprocess.run(["docker", "ps", "--filter", "name=headroom", "--format", "{{.Names}}"], capture_output=True, text=True)
            if "headroom" not in running_res.stdout:
                print("[Docker] Starting existing Headroom container...")
                subprocess.run(["docker", "start", "headroom"])
        else:
            # Detect upstream endpoints in environment to chain Headroom with API gateways like 9router
            env_args = []
            upstream_anthropic = os.getenv("UC_UPSTREAM_ANTHROPIC") or os.getenv("ANTHROPIC_BASE_URL")
            upstream_openai = os.getenv("UC_UPSTREAM_OPENAI") or os.getenv("OPENAI_BASE_URL")
            
            # Prevent circular routing back to ultimate-compression (port 20129)
            if upstream_anthropic and "20129" not in upstream_anthropic:
                env_args.extend(["-e", f"ANTHROPIC_BASE_URL={upstream_anthropic}"])
            elif os.path.exists("/home/pi/9router-docker") or "192.168.0.52" in str(os.environ):
                # Fallback to local 9router port if active
                env_args.extend(["-e", "ANTHROPIC_BASE_URL=http://192.168.0.52:20128/v1"])
                
            if upstream_openai and "20129" not in upstream_openai:
                env_args.extend(["-e", f"OPENAI_BASE_URL={upstream_openai}"])
            elif os.path.exists("/home/pi/9router-docker") or "192.168.0.52" in str(os.environ):
                env_args.extend(["-e", "OPENAI_BASE_URL=http://192.168.0.52:20128/v1"])
                
            print(f"[Docker] Launching new Headroom container on port 8787. Upstreams: {env_args}")
            
            run_cmd = [
                "docker", "run", "-d", 
                "--name", "headroom", 
                "-p", "8787:8787"
            ] + env_args + ["ghcr.io/chopratejas/headroom:latest"]
            
            subprocess.run(run_cmd)
        return True
    except Exception as e:
        print(f"[Docker] Error checking Headroom container: {e}")
        return False

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=20129)

