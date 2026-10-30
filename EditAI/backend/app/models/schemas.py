from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field

class MediaMetadata(BaseModel):
    filename: str
    filepath: str
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    format: str = ""
    has_audio: bool = False
    size_bytes: int = 0
    codec: str = ""

class SceneSegment(BaseModel):
    scene_id: int
    start_time: float
    end_time: float
    duration: float
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None
    thumbnail_url: Optional[str] = None
    visual_description: str = ""
    is_low_activity: bool = False
    average_brightness: float = 0.0
    motion_score: float = 0.0

class SilenceSegment(BaseModel):
    start_time: float
    end_time: float
    duration: float

class SpeechSegment(BaseModel):
    start_time: float
    end_time: float
    text: str
    confidence: float = 1.0

class AnalysisResult(BaseModel):
    video_metadata: MediaMetadata
    scenes: List[SceneSegment] = []
    speech_segments: List[SpeechSegment] = []
    silences: List[SilenceSegment] = []
    low_activity_segments: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {}
    limitations: List[str] = []

class Clip(BaseModel):
    id: str
    source_file: str
    source_filename: str
    source_start: float
    source_end: float
    timeline_start: float
    timeline_end: float
    duration: float
    name: str
    speed: float = 1.0
    volume: float = 1.0
    color: Optional[str] = "#3b82f6"
    stream_url: Optional[str] = None
    role: Optional[str] = None
    editorial_rationale: Optional[str] = None
    trimmed_reason: Optional[str] = None

class SubtitleItem(BaseModel):
    id: int
    start_time: float
    end_time: float
    text: str

class AudioTrackInfo(BaseModel):
    filename: str
    filepath: str
    duration: float
    volume: float = 1.0
    offset: float = 0.0
    mode: str = "original"  # "original", "external", "mix"

class TimelineState(BaseModel):
    clips: List[Clip] = []
    total_duration: float = 0.0
    selected_clip_id: Optional[str] = None
    selection_range: Optional[Tuple[float, float]] = None
    audio_track: Optional[AudioTrackInfo] = None
    subtitles: List[SubtitleItem] = []
    playhead_time: float = 0.0

class EditActionRecord(BaseModel):
    id: str
    description: str
    action_type: str
    timestamp: float
    details: Dict[str, Any] = {}

class ChatbotCommandRequest(BaseModel):
    prompt: str
    current_timeline: TimelineState
    media_metadata: Optional[MediaMetadata] = None
    scenes: Optional[List[SceneSegment]] = None
    confirm_destructive: bool = False
    llm_config: Optional[Dict[str, Any]] = None

class ChatbotCommandResponse(BaseModel):
    understood: bool
    intent: str
    message: str
    target_time: Optional[float] = None
    target_range: Optional[List[float]] = None
    updated_timeline: Optional[TimelineState] = None
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    prompt_for_clarification: Optional[str] = None
    action_description: Optional[str] = None
    action_proposal: Optional[Dict[str, Any]] = None
    llm_provider: Optional[str] = None

class ExportRequest(BaseModel):
    timeline: TimelineState
    resolution: str = "original"  # "original", "1080p", "720p"
    aspect_ratio: str = "16:9"    # "16:9", "9:16", "1:1"
    scaling_mode: str = "crop"    # "crop", "fit", "letterbox"
    burn_subtitles: bool = True
    audio_mode: str = "original"  # "original", "external", "mix"
    external_audio_path: Optional[str] = None

class ExportResponse(BaseModel):
    success: bool
    export_id: str
    download_url: str
    filename: str
    duration: float
    size_bytes: int
    message: str

# ----------------------------------------------------
# MULTI-CLIP ANALYSIS & INTELLIGENT ASSEMBLY SCHEMAS
# ----------------------------------------------------

class SourceClipAnalysis(BaseModel):
    media_id: str
    filename: str
    filepath: str
    duration: float
    width: int
    height: int
    fps: float
    has_audio: bool
    scenes: List[SceneSegment] = []
    content_tags: List[str] = []
    primary_category: str = "general"  # "dialogue", "action_broll", "scenic_broll", "presentation"
    motion_level: str = "medium"        # "high", "medium", "low"
    quality_score: float = 0.85
    speech_summary: str = ""
    silences_count: int = 0
    limitations: List[str] = []

class AssemblySegmentDecision(BaseModel):
    segment_id: str
    source_filename: str
    source_filepath: str
    source_in: float
    source_out: float
    duration: float
    timeline_start: float
    timeline_end: float
    role: str                       # "Hook / Intro", "Core Message", "B-Roll Action", "Scenic Climax", "Finale Outro"
    rationale: str                  # Editorial explanation of why this was selected
    trimmed_reason: Optional[str] = None  # What was trimmed before/after
    confidence: float = 0.9
    caption_text: Optional[str] = None

class MultiClipAssemblyResult(BaseModel):
    assembly_id: str
    style: str
    user_prompt: Optional[str] = None
    total_duration: float
    source_clips_analyzed: int
    clip_analyses: List[SourceClipAnalysis] = []
    segments: List[AssemblySegmentDecision] = []
    discarded_summary: List[Dict[str, Any]] = []
    subtitles: List[SubtitleItem] = []
    audio_sync_note: str = ""
    timeline_state: TimelineState

class AssemblyRequest(BaseModel):
    media_files: List[str]
    style: str = "narrative"  # "narrative", "social", "broll", "chronological", "custom"
    user_prompt: Optional[str] = None
    target_duration: Optional[float] = None
    include_subtitles: bool = True
