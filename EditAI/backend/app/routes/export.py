from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import EXPORT_DIR
from app.models.schemas import ExportRequest, ExportResponse
from app.services.export_service import ExportService

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.post("/render", response_model=ExportResponse)
async def render_video(request: ExportRequest):
    """
    Renders the active edited timeline into a synchronized MP4 file.
    """
    result = ExportService.render_timeline(
        timeline=request.timeline,
        resolution=request.resolution,
        aspect_ratio=request.aspect_ratio,
        scaling_mode=request.scaling_mode,
        burn_subtitles=request.burn_subtitles,
        audio_mode=request.audio_mode,
        external_audio_path=request.external_audio_path
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    return result

@router.get("/download/{filename}")
async def download_file(filename: str):
    """Provides direct file download for rendered video."""
    file_path = EXPORT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Exported file not found.")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="video/mp4"
    )
