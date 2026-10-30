#!/usr/bin/env python3
"""
AI Video Studio - Prototype Launcher
Starts the FastAPI backend and serves the React frontend at http://127.0.0.1:8000
Automatically frees stale instances on port 8000 or selects next available port.
"""

import os
import sys
import socket
import subprocess
import time
import webbrowser
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from sample_media.generate_samples import generate_sample_assets

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def kill_process_on_port(port: int):
    """Attempts to kill stale process holding the port on Windows/Unix."""
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

def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    # First attempt to free default port 8000 if occupied
    if is_port_in_use(start_port):
        kill_process_on_port(start_port)

    # Check if freed
    if not is_port_in_use(start_port):
        return start_port

    # Otherwise scan for next open port
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return start_port

def main():
    print("=" * 60)
    print("      AI Video Studio - Intelligent Video Editor")
    print("=" * 60)
    print("[1/2] Verifying sample media assets...")
    try:
        generate_sample_assets()
        print("      Sample assets ready in backend/sample_media/")
    except Exception as e:
        print(f"      Notice: {e}")

    # Determine free port
    port = find_available_port(8000)
    url = f"http://127.0.0.1:{port}"

    print(f"[2/2] Starting application server on port {port}...")
    print(f"      URL: {url}")
    print("      Press Ctrl+C to terminate.")
    print("=" * 60)

    # Automatically open browser
    try:
        webbrowser.open(url)
    except Exception:
        pass

    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)

if __name__ == "__main__":
    main()
