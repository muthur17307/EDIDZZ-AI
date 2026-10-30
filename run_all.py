#!/usr/bin/env python3
"""
Master Launcher for EditMind AI / EditAI Video Pipeline
Sets up virtual environment (.venv), installs all backend & frontend requirements,
connects the pipeline and UI, and launches the entire application.
"""

import os
import sys
import subprocess
import socket
import time
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
VENV_DIR = ROOT_DIR / ".venv"
BACKEND_DIR = ROOT_DIR / "EditAI" / "backend"
FRONTEND_DIR = ROOT_DIR / "EditAI" / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"
STANDALONE_PIPELINE_DIR = ROOT_DIR / "EDIT-AI-PIPELINE--main"
REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"

def print_banner():
    print("=" * 70)
    print("       EditMind AI — Autonomous Video Editing Pipeline Workstation")
    print("   OpenTimelineIO + Local Qwen 2.5 + DaVinci Resolve-Inspired UI")
    print("=" * 70)

def get_venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def get_venv_pip() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"

def ensure_venv():
    """Ensures .venv exists in ROOT_DIR; creates it if missing."""
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("\n[1/5] Creating Python virtual environment (.venv)...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
        print(f"      Virtual environment created at {VENV_DIR}")
    else:
        print("\n[1/5] Virtual environment (.venv) detected.")

def ensure_in_venv():
    """If running outside .venv, re-executes this script using .venv python."""
    venv_python = get_venv_python()
    current_python = Path(sys.executable).resolve()
    target_python = venv_python.resolve()

    if current_python != target_python and target_python.exists():
        print(f"      Switching execution into virtual environment ({target_python})...")
        os.execv(str(target_python), [str(target_python), str(Path(__file__).resolve())] + sys.argv[1:])

def install_backend_requirements():
    """Installs required Python packages into .venv."""
    print("\n[2/5] Checking and installing backend & pipeline dependencies...")
    pip_exe = get_venv_pip()
    pip_cmd = [str(pip_exe), "install", "--upgrade", "pip"]
    try:
        subprocess.run(pip_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    install_cmd = [str(pip_exe), "install", "-r", str(REQUIREMENTS_FILE)]
    result = subprocess.run(install_cmd)
    if result.returncode != 0:
        print("[WARNING] Pip install returned a non-zero exit code. Retrying with backend requirements...")
        backend_req = BACKEND_DIR / "requirements.txt"
        subprocess.run([str(pip_exe), "install", "-r", str(backend_req)])

    print("      Backend dependencies verified.")

def ensure_frontend_built():
    """Verifies that the frontend bundle exists. If missing, builds via npm if available."""
    print("\n[3/5] Checking frontend UI bundle...")
    index_html = FRONTEND_DIST / "index.html"
    if index_html.exists():
        print(f"      Pre-compiled frontend dist verified at {FRONTEND_DIST}.")
        return

    print("      Frontend dist missing. Attempting to build via npm...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    try:
        subprocess.check_call([npm_cmd, "install"], cwd=str(FRONTEND_DIR))
        subprocess.check_call([npm_cmd, "run", "build"], cwd=str(FRONTEND_DIR))
        print("      Frontend successfully built!")
    except Exception as e:
        print(f"[WARNING] Could not build frontend via npm ({e}).")
        print("          If you have pre-built assets, place them in EditAI/frontend/dist.")

def connect_pipeline_paths():
    """Adds backend directory to sys.path and PYTHONPATH."""
    print("\n[4/5] Connecting pipeline modules and FastAPI backend...")
    # BACKEND_DIR must be FIRST so EditAI/backend/app is always imported
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    if str(ROOT_DIR) not in sys.path:
        sys.path.append(str(ROOT_DIR))

    current_pythonpath = os.environ.get("PYTHONPATH", "")
    new_paths = [str(BACKEND_DIR), str(ROOT_DIR)]
    os.environ["PYTHONPATH"] = os.pathsep.join(new_paths + ([current_pythonpath] if current_pythonpath else []))
    print(f"      Connected pipeline modules: EditAI/backend")

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def kill_process_on_port(port: int):
    """Kills any stale process holding the port."""
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
    if is_port_in_use(start_port):
        kill_process_on_port(start_port)
    if not is_port_in_use(start_port):
        return start_port
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return start_port

def run_tests_if_requested():
    if "--test" in sys.argv:
        print("\n--- Running Automated Backend Tests ---")
        import tests.test_pipeline as tp
        tp.test_pipeline_integration()
        sys.exit(0)

def main():
    print_banner()

    # Step 1: Ensure .venv exists
    ensure_venv()

    # Step 2: Ensure executing with .venv python
    ensure_in_venv()

    # Step 3: Install backend dependencies
    install_backend_requirements()

    # Step 4: Ensure frontend is ready
    ensure_frontend_built()

    # Step 5: Connect pipeline and backend modules
    connect_pipeline_paths()

    # Check for test flag
    run_tests_if_requested()

    # Generate sample media assets
    try:
        from sample_media.generate_samples import generate_sample_assets
        generate_sample_assets()
    except Exception as e:
        print(f"Note on sample media generation: {e}")

    # Step 6: Launch Web Studio
    port = find_available_port(8000)
    url = f"http://127.0.0.1:{port}"

    print("\n[5/5] Launching EditMind AI Studio...")
    print(f"      Target URL: {url}")
    print(f"      Backend API & Frontend running simultaneously.")
    print("      Press Ctrl+C to terminate.")
    print("=" * 70)

    # Open browser slightly after start
    def open_browser():
        time.sleep(1.2)
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    os.chdir(str(BACKEND_DIR))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)

if __name__ == "__main__":
    main()

