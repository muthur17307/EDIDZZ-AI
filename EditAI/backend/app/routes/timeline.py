from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Tuple

from app.models.schemas import TimelineState
from app.services.timeline_manager import TimelineManager

router = APIRouter(prefix="/api/timeline", tags=["Timeline"])
timeline_manager = TimelineManager()

class SplitRequest(BaseModel):
    timeline: TimelineState
    split_time: float

class RangeRequest(BaseModel):
    timeline: TimelineState
    start_time: float
    end_time: float

class TimelineActionRequest(BaseModel):
    timeline: TimelineState

@router.post("/split")
async def split_at_time(req: SplitRequest):
    updated, msg = timeline_manager.split_clip(req.timeline, req.split_time)
    return {"timeline": updated, "message": msg}

@router.post("/delete")
async def delete_current(req: TimelineActionRequest):
    updated, msg = timeline_manager.delete_selected_clip(req.timeline)
    return {"timeline": updated, "message": msg}

@router.post("/cut")
async def cut_current(req: TimelineActionRequest):
    updated, msg = timeline_manager.cut_selection(req.timeline)
    return {"timeline": updated, "message": msg}

@router.post("/select")
async def select_time_range(req: RangeRequest):
    updated, msg = timeline_manager.select_range(req.timeline, req.start_time, req.end_time)
    return {"timeline": updated, "message": msg}

@router.post("/trim")
async def trim_time_range(req: RangeRequest):
    updated, msg = timeline_manager.trim_timeline(req.timeline, req.start_time, req.end_time)
    return {"timeline": updated, "message": msg}

@router.post("/undo")
async def undo_action(req: TimelineActionRequest):
    updated, msg = timeline_manager.undo(req.timeline)
    return {"timeline": updated, "message": msg}

@router.post("/redo")
async def redo_action(req: TimelineActionRequest):
    updated, msg = timeline_manager.redo(req.timeline)
    return {"timeline": updated, "message": msg}
