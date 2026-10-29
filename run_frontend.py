#!/usr/bin/env python3
"""
Dedicated Frontend Launcher for EditMind AI / EditAI
Runs the React 19 + Vite development server with Hot Module Replacement (HMR).
Proxies /api, /media_files, and /projects to http://127.0.0.1:8000.
Listens on http://localhost:5173
"""

import os
import sys
import shutil
import subprocess
import time
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "EditAI" / "frontend"
NODE_MODULES = FRONTEND_DIR / "node_modules"

def main():
    print("=" * 70)
    print("       EditMind AI — Dedicated React 19 Frontend Dev Server")
    print("   Vite HMR + TailwindCSS + DaVinci Resolve-Inspired UI")
    print("=" * 70)

    # 1. Verify Node.js
    node_cmd = shutil.which("node")
    npm_cmd = shutil.which("npm")

    if not node_cmd or not npm_cmd:
        print("[!] Node.js or npm not found in your system PATH.")
        print("    Please install Node.js (v18+) from https://nodejs.org/")
        sys.exit(1)

    node_version = subprocess.check_output([node_cmd, "-v"]).decode().strip()
    npm_version = subprocess.check_output([npm_cmd, "-v"]).decode().strip()
    print(f"[*] Node.js runtime : {node_version} (npm: {npm_version})")

    # 2. Check node_modules
    if not NODE_MODULES.exists():
        print("[*] node_modules not found. Installing frontend dependencies...")
        subprocess.check_call([npm_cmd, "install"], cwd=str(FRONTEND_DIR))
    else:
        print("[OK] Frontend dependencies detected.")

    print("\n[*] Starting Vite Development Server at http://localhost:5173 ...")
    print("    - Proxy Target  : http://127.0.0.1:8000 (Backend API)")
    print("    - Proxied Paths : /api, /media_files, /projects")
    print("    - Press Ctrl+C to stop the frontend server.")
    print("=" * 70)

    # Automatically open browser after 1.5 seconds
    def open_browser():
        time.sleep(1.5)
        try:
            webbrowser.open("http://localhost:5173")
        except Exception:
            pass

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch npm run dev
    try:
        subprocess.run([npm_cmd, "run", "dev"], cwd=str(FRONTEND_DIR), check=True)
    except KeyboardInterrupt:
        print("\n[OK] Frontend server stopped.")

if __name__ == "__main__":
    main()

