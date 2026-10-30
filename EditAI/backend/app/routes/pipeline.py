# app/routes/pipeline.py
"""
AI Video-Analysis Pipeline Routes.
Provides full integration between the offline AI video pipeline and the frontend:
- Media upload and project creation
- Clip analysis and feature extraction
- Global story planning (offline Qwen / heuristic)
- Timing & reference validation
- OpenTimelineIO editable timeline export
- Ready-to-edit TimelineState conversion for immediate UI playback & refinement
"""

import os
import shutil
from pathlib import Path
from uuid import uuid4
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import BASE_DIR, SAMPLE_DIR
from app.models.schemas import Clip, TimelineState, SubtitleItem
from app.pipeline.pipeline import run_pipeline
from sample_media.generate_samples import generate_multi_clip_pack

router = APIRouter(tags=["AI Pipeline"])

PROJECTS_DIR = BASE_DIR / "storage" / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


class RunExistingPipelineRequest(BaseModel):
    brief: str
    media_files: List[str]
    style: Optional[str] = "narrative"


def _build_timeline_state_from_pipeline(
    clips: List[Dict[str, Any]],
    ordered_segments: List[Dict[str, Any]],
    project_id: str
) -> tuple[TimelineState, List[SubtitleItem]]:
    """Converts validated pipeline segments into an interactive TimelineState."""
    by_id = {c["clip_id"]: c for c in clips}
    timeline_clips: List[Clip] = []
    subtitles: List[SubtitleItem] = []
    cur_time = 0.0

    role_colors = {
        "introduction": "#2a3b50",
        "action_broll": "#4a2d35",
        "core_message": "#1e3b2e",
        "benefit": "#1e3b2e",
        "presentation": "#3d3322",
        "outro": "#382845",
        "scenic_broll": "#253540",
    }

    for idx, seg in enumerate(ordered_segments):
        cid = seg.get("clip_id")
        clip_info = by_id.get(cid, {})
        source_path = clip_info.get("path", "")
        filename = clip_info.get("filename", Path(source_path).name)

        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", 0.0))
        dur = round(max(0.1, end - start), 2)
        role = seg.get("story_role", "broll")
        reason = seg.get("reason", "Selected narrative segment")

        # Determine streaming URL for video player
        clean_name = Path(filename).name
        if "sample_media" in str(source_path):
            stream_url = f"/media_files/sample_media/{clean_name}"
        elif "uploads" in str(source_path):
            stream_url = f"/media_files/uploads/{clean_name}"
        else:
            # Check if source is inside projects storage
            stream_url = f"/api/pipeline/projects/{project_id}/media/{clean_name}"

        timeline_clips.append(Clip(
            id=f"clip_pipe_{idx + 1}_{cid}",
            source_file=source_path,
            source_filename=filename,
            source_start=start,
            source_end=end,
            timeline_start=round(cur_time, 2),
            timeline_end=round(cur_time + dur, 2),
            duration=dur,
            name=f"{Path(filename).stem} ({role})",
            speed=1.0,
            volume=1.0,
            color=role_colors.get(role, "#2a3b50"),
            stream_url=stream_url,
            role=role.replace("_", " ").title(),
            editorial_rationale=reason,
            trimmed_reason=seg.get("trimmed_reason", None)
        ))

        # Add synchronized subtitle if transcript exists
        transcript = seg.get("transcript", "")
        if transcript and not any(w in transcript.lower() for w in ["ambient", "without spoken dialogue", "visual sequence beat"]):
            subtitles.append(SubtitleItem(
                id=idx + 1,
                start_time=round(cur_time + 0.3, 2),
                end_time=round(min(cur_time + dur - 0.2, cur_time + 4.0), 2),
                text=transcript
            ))

        cur_time += dur

    total_duration = round(cur_time, 2)
    state = TimelineState(
        clips=timeline_clips,
        total_duration=total_duration,
        selected_clip_id=timeline_clips[0].id if timeline_clips else None,
        selection_range=None,
        subtitles=subtitles,
        playhead_time=0.0
    )
    return state, subtitles


@router.post("/projects")
@router.post("/api/pipeline/projects")
async def create_project_pipeline(
    brief: str = Form(...),
    clips: List[UploadFile] = File(...),
):
    """
    Standard pipeline project endpoint matching the contract:
    - Accepts brief & multiple video clip files via multipart form
    - Executes ingest, analysis, global story planning, validation, and OTIO export
    - Returns pipeline URLs and rich interactive timeline state
    """
    if not brief or not brief.strip():
        raise HTTPException(status_code=400, detail="Client brief is required.")

    if not clips or len(clips) == 0:
        raise HTTPException(status_code=400, detail="At least one video clip is required.")

    project_id = str(uuid4())[:12]
    project_dir = PROJECTS_DIR / project_id
    source_dir = project_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)

    allowed = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

    try:
        saved_clips = []
        for index, upload in enumerate(clips, start=1):
            suffix = Path(upload.filename or "").suffix.lower()
            if suffix not in allowed:
                raise ValueError(f"Unsupported video type: {suffix}")

            safe_name = f"upload_{index:03d}_{Path(upload.filename or '').name}"
            destination = source_dir / safe_name

            with destination.open("wb") as out:
                while chunk := await upload.read(1024 * 1024):
                    out.write(chunk)
            saved_clips.append(str(destination.resolve()))

        (project_dir / "brief.txt").write_text(brief, encoding="utf-8")

        result = run_pipeline(project_dir, brief)

        # Build Interactive TimelineState for the UI
        import json
        manifest_path = project_dir / "media_manifest.json"
        manifest_clips = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []

        ordered = result.get("ordered_segments", [])
        tl_state, subs = _build_timeline_state_from_pipeline(manifest_clips, ordered, project_id)

        return {
            "project_id": project_id,
            "status": "completed",
            "timeline": result["timeline"],
            "selected_segments": result["selected_segments"],
            "review_items": result["review_items"],
            "story_summary": result["story_summary"],
            "ordered_segments": result["ordered_segments"],
            "segments": result["ordered_segments"],
            "total_duration": tl_state.total_duration,
            "style": "narrative",
            "review_segments": result.get("review_segments", []),
            "warnings": result.get("warnings", []),
            "timeline_url": f"/projects/{project_id}/timeline",
            "edit_plan_url": f"/projects/{project_id}/edit-plan",
            "story_context_url": f"/projects/{project_id}/story-context",
            "validation_report_url": f"/projects/{project_id}/validation-report",
            "timeline_state": tl_state,
            "subtitles": subs,
            "media_files": saved_clips
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline processing failed: {str(exc)}",
        ) from exc
    finally:
        for upload in clips:
            await upload.close()


@router.post("/api/pipeline/run-existing")
async def run_pipeline_on_existing_media(request: RunExistingPipelineRequest):
    """
    Runs the complete 5-stage pipeline on files already in Media Pool or Sample Media.
    """
    if not request.media_files:
        raise HTTPException(status_code=400, detail="No media files supplied.")

    project_id = str(uuid4())[:12]
    project_dir = PROJECTS_DIR / project_id
    source_dir = project_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Copy or hardlink existing media files into project source
        for idx, src in enumerate(request.media_files, start=1):
            src_path = Path(src)
            if not src_path.exists():
                if (UPLOAD_DIR / src_path.name).exists():
                    src_path = UPLOAD_DIR / src_path.name
                elif (SAMPLE_DIR / src_path.name).exists():
                    src_path = SAMPLE_DIR / src_path.name
                else:
                    continue
            dest_name = f"upload_{idx:03d}_{src_path.name}"
            shutil.copy2(src_path, source_dir / dest_name)

        if not list(source_dir.glob("*")):
            raise HTTPException(
                status_code=400,
                detail="None of the specified media files exist on disk."
            )

        brief = request.brief or f"Assemble a {request.style or 'narrative'} video edit highlighting the best moments."
        (project_dir / "brief.txt").write_text(brief, encoding="utf-8")

        result = run_pipeline(project_dir, brief)

        import json
        manifest_path = project_dir / "media_manifest.json"
        manifest_clips = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []

        ordered = result.get("ordered_segments", [])
        tl_state, subs = _build_timeline_state_from_pipeline(manifest_clips, ordered, project_id)

        return {
            "project_id": project_id,
            "status": "completed",
            "timeline": result["timeline"],
            "selected_segments": result["selected_segments"],
            "review_items": result["review_items"],
            "story_summary": result["story_summary"],
            "ordered_segments": result["ordered_segments"],
            "segments": result["ordered_segments"],
            "total_duration": tl_state.total_duration,
            "style": request.style or "narrative",
            "review_segments": result.get("review_segments", []),
            "warnings": result.get("warnings", []),
            "timeline_url": f"/projects/{project_id}/timeline",
            "edit_plan_url": f"/projects/{project_id}/edit-plan",
            "story_context_url": f"/projects/{project_id}/story-context",
            "validation_report_url": f"/projects/{project_id}/validation-report",
            "timeline_state": tl_state,
            "subtitles": subs,
            "media_files": request.media_files
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution error: {str(exc)}"
        ) from exc


@router.post("/api/pipeline/sample-pack")
async def run_pipeline_sample_pack(brief: Optional[str] = Body(None, embed=True)):
    """
    Loads the 3-clip demo pack and executes the complete 5-stage pipeline:
    - Ingests interview, action B-roll, and scenic clips
    - Analyzes scenes, audio, and visual pacing
    - Synthesizes global story plan with offline Qwen / heuristic planner
    - Validates source IDs, durations, and timing bounds
    - Generates OpenTimelineIO timeline (.otio) and mounts to interactive timeline
    """
    clips, srt_path, bgm_path = generate_multi_clip_pack()
    client_brief = brief or "Create a dynamic product showcase highlighting the speaker and fast action."
    req = RunExistingPipelineRequest(brief=client_brief, media_files=clips, style="narrative")
    return await run_pipeline_on_existing_media(req)


@router.get("/projects/{project_id}/timeline")
@router.get("/api/pipeline/projects/{project_id}/timeline")
def download_timeline_file(project_id: str):
    """Serves the OpenTimelineIO editable timeline file."""
    path = PROJECTS_DIR / project_id / "timeline.otio"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Timeline .otio file not found")

    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename="timeline.otio",
        headers={"Content-Disposition": 'attachment; filename="timeline.otio"'}
    )


@router.get("/projects/{project_id}/edit-plan")
@router.get("/api/pipeline/projects/{project_id}/edit-plan")
def get_edit_plan_file(project_id: str):
    """Serves the validated edit plan JSON."""
    path = PROJECTS_DIR / project_id / "edit_plan.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Edit plan JSON not found")

    return FileResponse(
        path,
        media_type="application/json",
        filename="edit_plan.json",
        headers={"Content-Disposition": 'attachment; filename="edit_plan.json"'}
    )


@router.get("/projects/{project_id}/story-context")
@router.get("/api/pipeline/projects/{project_id}/story-context")
def get_story_context_file(project_id: str):
    """Serves the cross-clip story context JSON."""
    path = PROJECTS_DIR / project_id / "story_context.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Story context not found")

    return FileResponse(
        path,
        media_type="application/json",
        filename="story_context.json",
        headers={"Content-Disposition": 'attachment; filename="story_context.json"'}
    )


@router.get("/projects/{project_id}/validation-report")
@router.get("/api/pipeline/projects/{project_id}/validation-report")
def get_validation_report_file(project_id: str):
    """Serves the validation report JSON."""
    path = PROJECTS_DIR / project_id / "validation_report.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Validation report not found")

    return FileResponse(
        path,
        media_type="application/json",
        filename="validation_report.json"
    )


@router.get("/projects/{project_id}/media/{filename}")
@router.get("/api/pipeline/projects/{project_id}/media/{filename}")
def stream_project_media(project_id: str, filename: str):
    """Streams source video files stored in project directory."""
    path = PROJECTS_DIR / project_id / "source" / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")

    return FileResponse(path, media_type="video/mp4")

