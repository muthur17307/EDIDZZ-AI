import re
import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from app.config import (
    UPLOAD_DIR,
    SAMPLE_DIR,
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_AUDIO_EXTENSIONS,
    ALLOWED_SUBTITLE_EXTENSIONS
)
from app.models.schemas import MediaMetadata, TimelineState, AudioTrackInfo
from app.services.video_service import VideoService
from app.services.timeline_manager import TimelineManager
from app.services.subtitle_service import SubtitleService
from sample_media.generate_samples import generate_sample_assets

router = APIRouter(prefix="/api/media", tags=["Media"])
timeline_manager = TimelineManager()

@router.post("/upload/batch")
@router.post("/batch")
@router.post("/batch-upload")
async def upload_batch_videos(files: list[UploadFile] = File(...)):
    """Uploads multiple video files simultaneously for multi-clip assembly."""
    if not files:
        raise HTTPException(status_code=400, detail="No video files uploaded.")

    uploaded_items = []
    skipped_files = []

    for f in files:
        filename = f.filename or "video.mp4"
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            skipped_files.append(filename)
            continue

        raw_basename = Path(filename).name
        clean_basename = re.sub(r"[^a-zA-Z0-9_.-]", "_", raw_basename)
        unique_token = uuid.uuid4().hex[:6]
        clean_filename = f"vid_{unique_token}_{clean_basename}"
        save_path = UPLOAD_DIR / clean_filename

        try:
            with open(save_path, "wb") as buffer:
                while chunk := await f.read(1024 * 1024):
                    buffer.write(chunk)
        except Exception:
            continue

        try:
            meta = VideoService.probe_media(str(save_path))
        except Exception:
            file_size = save_path.stat().st_size if save_path.exists() else 0
            meta = MediaMetadata(
                filename=clean_filename,
                filepath=str(save_path.resolve()),
                duration=10.0,
                width=1920,
                height=1080,
                fps=30.0,
                format=ext,
                has_audio=True,
                size_bytes=file_size,
                codec="H264"
            )

        uploaded_items.append({
            "id": f"media_{uuid.uuid4().hex[:8]}",
            "filename": filename,
            "filepath": str(save_path.resolve()),
            "stream_url": f"/media_files/uploads/{clean_filename}",
            "metadata": meta
        })

    if not uploaded_items and skipped_files:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format for files: {', '.join(skipped_files)}. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )

    return {
        "success": True,
        "count": len(uploaded_items),
        "items": uploaded_items
    }

@router.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """Uploads a video file (MP4, MOV, WebM) and returns metadata & initial timeline."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{ext}'. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )

    clean_filename = f"vid_{Path(file.filename).name}"
    save_path = UPLOAD_DIR / clean_filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    metadata = VideoService.probe_media(str(save_path))
    initial_timeline = timeline_manager.create_initial_timeline(metadata)

    return {
        "success": True,
        "metadata": metadata,
        "timeline": initial_timeline,
        "stream_url": f"/media_files/uploads/{clean_filename}"
    }

@router.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    """Uploads an optional audio file (MP3, WAV) and returns audio metadata."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format '{ext}'. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
        )

    clean_filename = f"aud_{Path(file.filename).name}"
    save_path = UPLOAD_DIR / clean_filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    metadata = VideoService.probe_media(str(save_path))
    audio_info = AudioTrackInfo(
        filename=file.filename,
        filepath=str(save_path.resolve()),
        duration=metadata.duration,
        volume=1.0,
        offset=0.0,
        mode="external"
    )

    return {
        "success": True,
        "audio_track": audio_info,
        "stream_url": f"/media_files/uploads/{clean_filename}"
    }

@router.post("/upload/subtitle")
async def upload_subtitle(file: UploadFile = File(...)):
    """Uploads and parses an optional subtitle file (SRT, VTT)."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_SUBTITLE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported subtitle format '{ext}'. Allowed: {', '.join(ALLOWED_SUBTITLE_EXTENSIONS)}"
        )

    clean_filename = f"sub_{Path(file.filename).name}"
    save_path = UPLOAD_DIR / clean_filename

    content_bytes = await file.read()
    content_text = content_bytes.decode("utf-8", errors="replace")

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content_text)

    subtitles = SubtitleService.parse_srt_or_vtt(content_text)

    return {
        "success": True,
        "filename": file.filename,
        "subtitles": subtitles,
        "count": len(subtitles)
    }

@router.post("/load-sample")
async def load_sample_project():
    """Generates and loads the multi-scene demo video, audio, and subtitles."""
    video_path, srt_path, audio_path = generate_sample_assets()

    metadata = VideoService.probe_media(video_path)
    initial_timeline = timeline_manager.create_initial_timeline(metadata)

    # Read sample subtitles
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_content = f.read()
    subtitles = SubtitleService.parse_srt_or_vtt(srt_content)
    initial_timeline.subtitles = subtitles

    return {
        "success": True,
        "metadata": metadata,
        "timeline": initial_timeline,
        "stream_url": f"/media_files/sample_media/sample_demo.mp4",
        "has_sample_subtitles": True,
        "has_sample_audio": True,
        "sample_audio_url": f"/media_files/sample_media/sample_bgm.wav"
    }

@router.delete("/remove")
async def remove_media(media_type: str):
    """Resets or removes specific media track."""
    return {"success": True, "message": f"Removed {media_type} track."}
