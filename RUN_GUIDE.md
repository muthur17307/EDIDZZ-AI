# 🚀 EditMind AI — Complete Setup & Run Guide

This guide walks you step-by-step through setting up, configuring, and running the **EditMind AI Video Editing Pipeline** on your machine.

---

## 📋 System Requirements & Prerequisites

| Requirement | Minimum | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **OS** | Windows 10/11, macOS, Linux | Windows 11 / Ubuntu 22.04 | Tested on Windows |
| **Python** | Python 3.10+ | Python 3.11 or 3.12 | Ensure `python` is added to PATH |
| **Node.js** | *Optional* | Node 18+ / 20+ | Frontend is **already pre-built** in `EditAI/frontend/dist/` |
| **FFmpeg** | Auto-bundled | Bundled via `imageio-ffmpeg` | No manual system installation needed |
| **Ollama** | *Optional* | Latest version | Needed to run Qwen 2.5 locally offline |

---

## ⚡ 1-Click Master Launchers (Recommended)

We have provided all-in-one setup & run scripts that automatically:
1. Create and activate `.venv` (if not already created)
2. Install all Python dependencies from `requirements.txt`
3. Verify the frontend bundle (`EditAI/frontend/dist`)
4. Connect the standalone pipeline and backend in Python's path
5. Start the server on port 8000 and launch your default browser

### Option 1: Double-Click Batch File (Windows)
Double-click **`start.bat`** or **`run_all.bat`** in the root workspace folder.

### Option 2: PowerShell (Single Command)
```powershell
.\run_all.ps1
```

### Option 3: Cross-Platform Python Launcher
```powershell
python run_all.py
```
*(Automatically creates `.venv`, switches into it, installs dependencies, and launches the web studio).*

---


---

## 🔀 Running Frontend & Backend Separately

You can run the backend and frontend in completely independent terminal sessions or processes.

### 🌟 1-Click Split Launcher (Opens Two Separate Windows)
* **Double-click**: **`run_separate.bat`** (or in PowerShell: `.\run_separate.ps1`)
* *What happens:*
  - **Window 1**: Launches the **FastAPI Backend** on `http://127.0.0.1:8000`.
  - **Window 2**: Launches the **React 19 / Vite Dev Server** on `http://localhost:5173`.
  - Each window has its own live log stream, reload triggers, and independent `Ctrl+C` stop control!

---

### 🖥️ Option B: Run in Separate Manual Terminals

#### Terminal 1 — Backend (FastAPI + AI Pipeline + Local Qwen 2.5)
```powershell
# From workspace root:
.\run_backend.bat

# Or using Python:
python run_backend.py

# Or directly:
cd EditAI\backend
python run.py
```
* **URL**: `http://127.0.0.1:8000`
* **Swagger API Docs**: `http://127.0.0.1:8000/docs`
* **Features**: Live reloading enabled, automatic port-conflict resolution, connected to local Ollama (`qwen2.5:7b`), OpenTimelineIO generator, SQLite persistence.

#### Terminal 2 — Frontend (React 19 + Vite HMR)
```powershell
# From workspace root:
.\run_frontend.bat

# Or using Python:
python run_frontend.py

# Or directly with npm:
cd EditAI\frontend
npm run dev
```
* **URL**: `http://localhost:5173`
* **Features**: Hot Module Replacement (instant UI code updates without restarting), DaVinci Resolve-inspired dark UI.
* **Auto-Proxying**: Vite automatically proxies all `/api`, `/media_files`, and `/projects` requests directly to `http://127.0.0.1:8000`.

---

## 🛠️ Manual Step-by-Step Setup (If preferred)

---

## 🧠 Setting Up Local Qwen 2.5 with Ollama (Zero API Costs & Total Privacy)

Our system connects to a locally running instance of **Qwen 2.5** via **Ollama**.

> **Note on Fallback**: If Ollama is not installed or running, EditMind AI **will not crash**. It automatically falls back to our deterministic, offline rule-based narrative engine with semantic role assignment and repetition detection.

### 1. Install Ollama
Download and install Ollama from [https://ollama.com/download](https://ollama.com/download).

### 2. Pull & Run Qwen 2.5
Open a separate PowerShell / Terminal window and run:

```bash
# Recommended: 7B model (balanced speed and creative narrative reasoning)
ollama run qwen2.5:7b

# For low-spec laptops / limited VRAM:
ollama run qwen2.5:3b
# or
ollama run qwen2.5:1.5b
```

### 3. Verify Ollama is Active
You can test if Ollama is accessible by visiting:
```
http://localhost:11434/api/tags
```
When running, EditMind AI's `AIModelAdapter` automatically queries this endpoint, detects `qwen2.5:7b`, and uses it to plan cross-clip story sequences and drop repeated takes.

---

## 🖥️ Running the Application

### Option A: Via Python Launcher (Recommended)
```powershell
cd "c:\Users\user\Desktop\RYHATHON - 2026\EditAI"
python run_app.py
```
**Features of `run_app.py`:**
- Checks if port `8000` is currently occupied by a stale zombie process and terminates it cleanly.
- If port `8000` cannot be freed, it automatically increments to an open port (8001, 8002, etc.).
- Verifies that sample media assets exist (or generates them automatically).
- Starts FastAPI + Uvicorn with auto-reload.
- Opens your browser to the editing workspace.

### Option B: Via Windows Batch File
Double-click `start.bat` located inside `EditAI/` or `start.bat` in the root folder.

### Option C: Running the Backend Directly via Uvicorn
```powershell
cd "c:\Users\user\Desktop\RYHATHON - 2026\EditAI\backend"
python run.py
```

### Option D: (Optional) Frontend Development with Vite HMR
If you want to edit frontend TypeScript/React source code with live Hot Module Replacement:
```powershell
cd "c:\Users\user\Desktop\RYHATHON - 2026\EditAI\frontend"
npm install
npm run dev
```
Open `http://localhost:5173`. (Ensure the backend is running on `http://127.0.0.1:8000`).

---

## 🎬 Hackathon Demo Walkthrough (Step-by-Step)

Follow these steps during your presentation or evaluation:

### Step 1: Open the Application
Navigate to `http://127.0.0.1:8000`. You will see the **DaVinci Resolve-inspired dark workspace**.

### Step 2: Ingest Footage & Run AI Assembly
1. Click the **"AI Auto-Assemble"** button in the top toolbar (or click the **"Cut"** page tab at the bottom).
2. Click **"Load 3-Clip Demo Pack"** (or drag and drop your own raw `.mp4` / `.mov` files).
   - *Clip 1: Interview & Dialogue* (Speaker keynote monologue)
   - *Clip 2: Dynamic Action B-Roll* (Fast motion visuals)
   - *Clip 3: Scenic Presentation & Outro* (Atmospheric closure)
3. Enter a **Creative Story Brief** in the text box, for example:
   > *"Assemble an engaging product showcase highlighting key benefits, using energetic B-roll cutaways, and finishing with a clean outro."*
4. Choose an assembly style (e.g. `Narrative Highlight Reel`).
5. Click **"Analyze & Assemble Sequence"**.
   - *What happens under the hood*:
     - Scene detection scans cuts & shot boundaries.
     - OpenCV computes visual motion scores.
     - Speech-to-text transcribes dialogue.
     - Local Qwen 2.5 compares segments across all 3 clips, eliminates repeated or weak takes, and constructs an optimal narrative sequence.
     - Timestamp boundaries are validated and clamped.

### Step 3: Review Editorial Decisions & Rationales
- The assembly view displays:
  - **Assembled Segments**: The exact chosen parts, their assigned story roles (`Introduction`, `Action B-roll`, `Core Message`, `Outro`), and **detailed editorial rationales** explaining why the AI chose each cut.
  - **Discarded / Trimmed Ledger**: Why duplicate takes, low-motion pauses, or false starts were cut.
  - **Synchronized Subtitles**: Frame-aligned dialogue captions.

### Step 4: Apply to Timeline & Fine-Tune
1. Click **"Apply to Timeline & Open Editor"**.
2. The clips are instantly mounted onto track `V1`, audio onto `A1`, and subtitles onto `Sub1`.
3. Try out the non-destructive editing controls:
   - **Playhead Transport**: Hit `Space` to play/pause, or use frame-stepping buttons (`<`, `>`).
   - **Split / Blade**: Move playhead and press `S` (or click the Blade icon) to slice a clip.
   - **Inspector**: Click any clip to view its properties, playback speed (0.25x - 3.0x), volume, and AI selection rationale.
   - **Ripple Delete**: Select a segment and press `Delete` to remove it and ripple subsequent clips forward.

### Step 5: Test the Conversational AI Assistant
In the right-hand **AI Assistant** panel, test conversational commands:
- *"Select the clip from 00:05 to 00:12."*
- *"Split at 00:08."*
- *"Delete the selected clip."*
- *"Undo the last edit."*

### Step 6: Export OpenTimelineIO (`.otio`) & MP4
1. **Download OpenTimelineIO (`.otio`)**:
   - Access `http://127.0.0.1:8000/api/pipeline/projects/{project_id}/timeline` (or via the UI Export panel) to save your `.otio` timeline.
   - Open this file in **DaVinci Resolve** (`File -> Import -> Timeline -> OpenTimelineIO`) or **Premiere Pro** to demonstrate lossless NLE handoff!
2. **Render Direct MP4**:
   - Click **"Quick Export"** in the top toolbar.
   - Choose your format:
     - `16:9 Landscape` (YouTube / Presentations)
     - `9:16 Vertical` (TikTok / Instagram Reels / YouTube Shorts)
     - `1:1 Square` (LinkedIn / Instagram Feed)
   - Click **"Render & Download MP4"** to generate the final processed video file.

---

## 🧪 Running the Automated Test Suites

We include 7 comprehensive end-to-end and unit test suites in `EditAI/backend/tests/`:

```powershell
cd "c:\Users\user\Desktop\RYHATHON - 2026"

# 0. Complete User Journey & Video Pipeline Simulation Test (Recommended)
# Simulates exact end-to-end user session: multi-clip upload, 5-stage pipeline, OTIO export, timeline mount, DB save, AI chat, and FFmpeg MP4 render
python -u EditAI/backend/tests/test_user_simulation.py

# 1. Live Offline Qwen 2.5 Inference & Ollama Connectivity Test
# Verifies live detection of qwen2.5:7b, cross-clip narrative planning, guardrails, and chatbot split
python EditAI/backend/tests/test_live_qwen.py

# 2. 5-Stage AI Video Pipeline & OpenTimelineIO (.otio) Generation Test
# Verifies full 5 stages, timeline.otio file download (5KB+), and frontend TimelineState sync
python EditAI/backend/tests/test_pipeline.py

# 3. Section 5 Conversational NLE Chatbot Narrative Reasoning Test
# Verifies why cuts were chosen, finding repeated statements, highlighting moments, and shortening cuts
python EditAI/backend/tests/test_narrative_assistant.py

# 4. Multi-Clip Sequence Assembly Test
# Verifies pack generation, multimodal analysis, LLM planning, rationale assignment, and timeline mounting
python EditAI/backend/tests/test_assembly.py

# 5. Full End-to-End Workflow & FFmpeg MP4 Export Test
# Verifies sample loading, scene analysis, chatbot split/delete/ripple operations, and FFmpeg MP4 export
python EditAI/backend/tests/test_workflow.py

# 6. SQLite Persistence Test
# Verifies project creation, saving clips/subtitles, and DB reload
python EditAI/backend/tests/test_persistence.py
```

All 7 test suites exit with code `0` and print `[OK]` status indicators.

---

## 🛠️ Standalone Pipeline Usage (Python Script / CLI)

If you wish to run the pipeline without the web interface:

```python
from pathlib import Path
from EditAI.backend.app.pipeline.pipeline import run_pipeline

# 1. Setup project directory
project_dir = Path("./my_test_project")
source_dir = project_dir / "source"
source_dir.mkdir(parents=True, exist_ok=True)

# 2. Place your raw .mp4 clips into project_dir / "source"
# (Copy footage into ./my_test_project/source/)

# 3. Execute pipeline with brief
brief = "Create a fast-paced 30-second commercial highlight from the best takes."
result = run_pipeline(project_dir=project_dir, brief=brief)

print("Status:", result["status"])
print("OTIO Timeline File:", result["timeline"])
print("Edit Plan JSON:", result["edit_plan"])
print("Validation Report:", result["validation_report"])
```

Output files generated in `project_dir`:
- `media_manifest.json`: Probed metadata and durations of raw footage.
- `analysis/*.json`: Granular scene, motion, and speech tags for each clip.
- `story_context.json`: Cross-clip unified context matrix.
- `edit_plan_raw.json`: Unmodified LLM story plan.
- `edit_plan.json`: Validated edit plan with selected segments.
- `validation_report.json`: Guardrail checks and flagged review items.
- `timeline.otio`: Validated OpenTimelineIO timeline.

---

## ❓ Troubleshooting & FAQs

### Q1: "Port 8000 is already in use"
**Solution**: `run_app.py` automatically detects and clears stale processes on port 8000. If you are starting via `uvicorn` directly, kill the hanging process in PowerShell:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

### Q2: "OpenTimelineIO module not found"
**Solution**: Install it into your active environment:
```powershell
pip install opentimelineio>=0.15.0
```

### Q3: "Ollama connection failed / refused"
**Solution**: Make sure Ollama is running in the background. In PowerShell, execute:
```powershell
ollama serve
```
If you don't want to run Ollama, you don't have to! The system automatically falls back to our deterministic offline story planner without throwing errors.

### Q4: "PowerShell script activation is disabled"
**Solution**: If `.venv\Scripts\Activate.ps1` gives a security error:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

---

## 🏁 Summary Checklist for RYHATHON 2026 Presentation

- [x] Python virtual environment created and dependencies installed.
- [x] Pre-compiled frontend served seamlessly at `http://127.0.0.1:8000`.
- [x] Ollama with `qwen2.5:7b` running locally for privacy-preserving AI inferences (or offline fallback active).
- [x] 3-clip demo pack ready for 1-click loading.
- [x] Editorial rationales and trimmed take ledger visible in UI.
- [x] OpenTimelineIO (`.otio`) file export verified.
- [x] Backend test suites passing (`test_assembly.py`, `test_workflow.py`, `test_persistence.py`).
