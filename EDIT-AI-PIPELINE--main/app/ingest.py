
# app/ingest.py
import json
import subprocess
from pathlib import Path


def get_duration(path: Path) -> float:
    # 1. Try ffprobe if available
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(json.loads(result.stdout)["format"]["duration"])
    except Exception:
        pass

    # 2. Robust fallback via OpenCV
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        cap.release()
        if fps > 0 and frames > 0:
            return round(frames / fps, 3)
    except Exception:
        pass

    # 3. Fallback via FFmpeg
    try:
        import re
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        res = subprocess.run([ffmpeg_exe, "-i", str(path)], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        if dur_match:
            hours, minutes, seconds = float(dur_match.group(1)), float(dur_match.group(2)), float(dur_match.group(3))
            return round(hours * 3600 + minutes * 60 + seconds, 3)
    except Exception:
        pass

    return 0.0


def register_clips(source_dir: Path) -> list[dict]:
    clips = []

    for index, path in enumerate(sorted(source_dir.iterdir()), start=1):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {
            ".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"
        }:
            continue

        clips.append({
            "clip_id": f"clip_{index:03d}",
            "path": str(path.resolve()),
            "filename": path.name,
            "duration": get_duration(path),
        })

    if not clips:
        raise ValueError("No supported video clips were uploaded.")

    return clips
