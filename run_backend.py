#!/usr/bin/env python3
"""
Dedicated Backend Launcher for EditMind AI / EditAI
Runs the FastAPI Backend with 5-stage pipeline, local Qwen 2.5 adapter, and SQLite persistence.
Listens on http://127.0.0.1:8000
"""

import os
import sys
import socket
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
VENV_DIR = ROOT_DIR / ".venv"
BACKEND_DIR = ROOT_DIR / "EditAI" / "backend"
STANDALONE_PIPELINE = ROOT_DIR / "EDIT-AI-PIPELINE--main"

# Add directories to sys.path
for p in [BACKEND_DIR, STANDALONE_PIPELINE]:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def kill_process_on_port(port: int):
    """Frees stale process occupying the port."""
    try:
        if os.name == "nt":
            output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
            for line in output.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and "LISTENING" in parts:
                    pid = parts[-1]
                    if pid.isdigit() and int(pid) != os.getpid():
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
    except Exception:
        pass

def main():
    print("=" * 70)
    print("       EditMind AI — Dedicated FastAPI Backend Server")
    print("   AI Video Pipeline + Offline Qwen 2.5 + OpenTimelineIO (.otio)")
    print("=" * 70)

    # 1. Check & free port 8000
    if is_port_in_use(8000):
        print("[*] Port 8000 is occupied. Clearing stale process...")
        kill_process_on_port(8000)

    # 2. Check Ollama
    print("[*] Checking local Ollama connection...")
    try:
        import urllib.request
        import json
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", headers={"User-Agent": "EditMindAI"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name") for m in data.get("models", [])]
            print(f"    [OK] Ollama Online. Installed models: {models}")
    except Exception:
        print("    [Notice] Ollama not detected at http://127.0.0.1:11434.")
        print("             System will run with offline rule-based heuristic fallback.")

    print("\n[*] Starting FastAPI Uvicorn server on http://127.0.0.1:8000 ...")
    print("    - REST API Base : http://127.0.0.1:8000/api")
    print("    - Swagger Docs  : http://127.0.0.1:8000/docs")
    print("    - Press Ctrl+C to stop the backend.")
    print("=" * 70)

    import uvicorn
    # Change working directory to BACKEND_DIR so relative paths inside backend resolve properly
    os.chdir(str(BACKEND_DIR))
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()

