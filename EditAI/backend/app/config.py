import os
import sys
from pathlib import Path
import imageio_ffmpeg

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
EXPORT_DIR = BASE_DIR / "exports"
THUMBNAIL_DIR = BASE_DIR / "uploads" / "thumbnails"
SAMPLE_DIR = BASE_DIR / "sample_media"

# Ensure all directories exist
for d in [UPLOAD_DIR, EXPORT_DIR, THUMBNAIL_DIR, SAMPLE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Locate FFmpeg binary
try:
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_PATH = "ffmpeg"

# Add the directory containing ffmpeg to PATH so sub-processes can locate it if needed
ffmpeg_dir = str(Path(FFMPEG_PATH).parent)
if ffmpeg_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

MAX_UPLOAD_SIZE_MB = 200
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".m4a", ".ogg"}
ALLOWED_SUBTITLE_EXTENSIONS = {".srt", ".vtt"}
