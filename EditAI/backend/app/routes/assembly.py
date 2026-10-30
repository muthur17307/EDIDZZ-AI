from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional

from app.models.schemas import (
    AssemblyRequest,
    MultiClipAssemblyResult,
    TimelineState
)
from app.services.assembly_service import AssemblyService
from sample_media.generate_samples import generate_multi_clip_pack

router = APIRouter(prefix="/api/assembly", tags=["Multi-Clip Assembly"])

@router.post("/analyze-and-assemble", response_model=MultiClipAssemblyResult)
async def analyze_and_assemble(request: AssemblyRequest):
    """
    Analyzes multiple supplied video clips with multimodal feature extraction
    and assembles a coherent single video sequence with explicit editorial rationales.
    """
    if not request.media_files:
        raise HTTPException(status_code=400, detail="Please supply at least one video file for assembly.")

    # Step 1: Deep inspection on all clips
    clip_analyses = AssemblyService.analyze_source_clips(request.media_files)
    if not clip_analyses:
        raise HTTPException(status_code=400, detail="Unable to inspect provided media files.")

    # Step 2: Intelligent sequence assembly with editorial decisions
    result = AssemblyService.assemble_production(
        clip_analyses=clip_analyses,
        style=request.style,
        user_prompt=request.user_prompt,
        target_duration=request.target_duration
    )
    return result

@router.post("/sample-pack")
async def load_sample_multi_pack():
    """
    Generates and returns the multi-clip video pack:
    - Clip 1: Interview & Keynote Dialogue (12s)
    - Clip 2: High Motion Action B-Roll (10s)
    - Clip 3: Scenic Presentation & Outro (10s)
    """
    clips, srt_path, bgm_path = generate_multi_clip_pack()
    analyses = AssemblyService.analyze_source_clips(clips)
    return {
        "success": True,
        "clip_paths": clips,
        "clip_analyses": analyses,
        "srt_path": srt_path,
        "bgm_path": bgm_path
    }
