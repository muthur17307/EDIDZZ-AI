from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.models.schemas import AnalysisResult, MediaMetadata
from app.services.video_service import VideoService
from app.services.speech_service import SpeechService

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

class AnalyzeRequest(BaseModel):
    filepath: str
    duration: float

@router.post("/analyze", response_model=AnalysisResult)
async def analyze_video(request: AnalyzeRequest):
    """
    Examines uploaded video media and generates a complete structured summary:
    - Duration, resolution, frame rate
    - Scene & shot changes with timestamps & thumbnails
    - Speech transcription & timestamps (when available)
    - Silence & long-pause detection
    - Visual brightness and motion activity (identifying low-activity segments)
    - Clearly indicates any unavailable capability without fake results
    """
    if not request.filepath:
        raise HTTPException(status_code=400, detail="Missing video filepath for analysis.")

    # 1. Probing video metadata
    metadata = VideoService.probe_media(request.filepath)

    # 2. Scene detection & visual activity
    scenes = VideoService.detect_scenes(request.filepath, metadata.duration)

    # 3. Silence detection
    silences = VideoService.detect_silence(request.filepath)

    # 4. Speech transcription
    speech_segments, speech_limitation = SpeechService.transcribe(request.filepath, metadata.duration)

    # 5. Low-activity segments identification
    low_activity = [
        {
            "scene_id": s.scene_id,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "duration": s.duration,
            "description": s.visual_description,
            "motion_score": s.motion_score
        }
        for s in scenes if s.is_low_activity
    ]

    # 6. Gather limitations
    limitations = []
    if speech_limitation:
        limitations.append(speech_limitation)
    if not metadata.has_audio:
        limitations.append("Media file contains no audio track. Audio analysis skipped.")

    # 7. Summary metrics
    summary = {
        "total_scenes": len(scenes),
        "total_silence_segments": len(silences),
        "total_speech_segments": len(speech_segments),
        "low_activity_count": len(low_activity),
        "average_scene_duration": round(sum(s.duration for s in scenes) / len(scenes), 2) if scenes else 0.0
    }

    return AnalysisResult(
        video_metadata=metadata,
        scenes=scenes,
        speech_segments=speech_segments,
        silences=silences,
        low_activity_segments=low_activity,
        summary=summary,
        limitations=limitations
    )
