# Standalone Video Analysis & OpenTimelineIO Pipeline

This directory contains the standalone core pipeline for the **EditMind AI** video editing workstation. It can be run independently as a modular Python package or invoked via the FastAPI web backend.

---

## 🚀 What This Pipeline Does

1. **Clip Ingestion (`ingest.py`)**:
   - Registers source media files in `project_dir/source/`.
   - Probes technical metadata (duration, FPS, resolution) using `ffprobe`, `OpenCV`, or bundled `imageio-ffmpeg`.
   - Writes `media_manifest.json`.

2. **Multimodal Analysis (`model_adapter.py`)**:
   - Analyzes each clip using scene detection (`scenedetect`), motion scoring (`OpenCV`), and speech recognition (`SpeechRecognition`).
   - Categorizes segments into narrative roles (`introduction`, `action_broll`, `benefit`, `outro`).
   - Saves individual clip analysis JSON files in `project_dir/analysis/`.

3. **Cross-Clip Story Synthesis (`context_builder.py`)**:
   - Combines analyses from all source clips into a single narrative context (`story_context.json`).
   - Pairs clip segments with the user's client story brief.

4. **Global Narrative Planning & Deduplication (`model_adapter.py`)**:
   - Invokes local **Qwen 2.5** via Ollama (`http://localhost:11434`) or our offline deterministic editorial engine.
   - Weeds out duplicate takes and low-quality visual sections.
   - Emits an ordered list of segments with explicit editorial rationales.

5. **Guardrails & Timestamp Validation (`pipeline.py`)**:
   - Clamps segment bounds against true video duration.
   - Rejects hallucinated segment timestamps or invalid clip IDs.
   - Emits `edit_plan.json` and `validation_report.json`.

6. **OpenTimelineIO Export (`export_otio.py`)**:
   - Assembles approved segments into a track-based `.otio` timeline (`timeline.otio`).
   - Ready for import into DaVinci Resolve, Adobe Premiere Pro, and Final Cut Pro.

---

## 🛠️ Standalone Python Usage

```python
from pathlib import Path
from app.pipeline import run_pipeline

# 1. Define project folder and brief
project_dir = Path("./sample_project")
brief = "Create a fast-paced 30-second commercial highlight from the best takes."

# 2. Place your raw .mp4 clips inside:
# sample_project/source/clip1.mp4
# sample_project/source/clip2.mp4

# 3. Run the pipeline
result = run_pipeline(project_dir=project_dir, brief=brief)

print("Status:", result["status"])
print("OTIO Timeline:", result["timeline"])
print("Selected Segments:", result["selected_segments"])
print("Review Items:", result["review_items"])
```

---

## 📦 Dependencies

Install dependencies via:
```bash
pip install -r requirements.txt
```
