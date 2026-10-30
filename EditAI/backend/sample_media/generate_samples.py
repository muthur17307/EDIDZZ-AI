import os
import sys
import math
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import cv2
import numpy as np
import subprocess

from app.config import FFMPEG_PATH, SAMPLE_DIR

def generate_sample_assets():
    """Generates a complete multi-scene sample video and matching SRT subtitles."""
    video_path = SAMPLE_DIR / "sample_demo.mp4"
    srt_path = SAMPLE_DIR / "sample_demo.srt"
    audio_path = SAMPLE_DIR / "sample_bgm.wav"

    if video_path.exists() and srt_path.exists() and audio_path.exists():
        return str(video_path), str(srt_path), str(audio_path)

    print("Generating demo video with OpenCV & FFmpeg...")

    width, height = 854, 480
    fps = 25
    total_seconds = 30
    total_frames = fps * total_seconds

    temp_raw_avi = SAMPLE_DIR / "temp_raw.avi"
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    out = cv2.VideoWriter(str(temp_raw_avi), fourcc, fps, (width, height))

    scenes_def = [
        {"start": 0, "end": 10, "name": "Scene 1: Introduction & Motion", "color": (30, 40, 180)},
        {"start": 10, "end": 18, "name": "Scene 2: Slide Presentation", "color": (30, 140, 60)},
        {"start": 18, "end": 25, "name": "Scene 3: Target Segment (Split & Delete)", "color": (160, 40, 50)},
        {"start": 25, "end": 30, "name": "Scene 4: Finale & Outro", "color": (90, 30, 140)}
    ]

    for frame_idx in range(total_frames):
        sec = frame_idx / fps

        cur_scene = scenes_def[-1]
        for s in scenes_def:
            if s["start"] <= sec < s["end"]:
                cur_scene = s
                break

        frame = np.zeros((height, width, 3), dtype=np.uint8)
        c = cur_scene["color"]
        frame[:, :] = [c[0], c[1], c[2]]

        if cur_scene["start"] == 0:
            cx = int(width / 2 + math.sin(sec * 3) * 200)
            cy = int(height / 2 + math.cos(sec * 3) * 80)
            cv2.circle(frame, (cx, cy), 40, (255, 255, 255), -1)
            cv2.circle(frame, (cx, cy), 45, (0, 200, 255), 3)
        elif cur_scene["start"] == 10:
            cv2.rectangle(frame, (80, 100), (width - 80, height - 100), (25, 25, 25), -1)
            cv2.rectangle(frame, (80, 100), (width - 80, height - 100), (80, 200, 120), 2)
            cv2.putText(frame, "SLIDE: DATA OVERVIEW", (120, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
            cv2.putText(frame, "Automated Scene Boundary Verification", (120, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        elif cur_scene["start"] == 18:
            cv2.rectangle(frame, (50, 50), (width - 50, height - 50), (40, 20, 120), -1)
            cv2.putText(frame, "[ TARGET SEGMENT: 00:18 - 00:25 ]", (100, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            cv2.putText(frame, "Try: 'Split the clip at 00:20'", (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 255, 255), 2)
            cv2.putText(frame, "Or: 'Delete the selected segment'", (120, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 100), 2)
        else:
            cv2.putText(frame, "AI Video Studio Complete", (150, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            cv2.putText(frame, "Export Ready", (320, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 200), 2)

        timecode_str = f"Time: {int(sec // 60):02d}:{sec % 60:05.2f} / 00:30.00"
        cv2.rectangle(frame, (20, 20), (380, 65), (10, 10, 10), -1)
        cv2.putText(frame, timecode_str, (30, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, cur_scene["name"], (30, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        out.write(frame)

    out.release()

    temp_audio = SAMPLE_DIR / "temp_audio.wav"
    cmd_audio = [
        FFMPEG_PATH, "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=30:beep_factor=4",
        "-c:a", "pcm_s16le",
        str(temp_audio)
    ]
    subprocess.run(cmd_audio, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    cmd_mux = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_raw_avi),
        "-i", str(temp_audio),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(video_path)
    ]
    subprocess.run(cmd_mux, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if temp_raw_avi.exists():
        temp_raw_avi.unlink()
    if temp_audio.exists():
        temp_audio.unlink()

    srt_content = """1
00:00:01,000 --> 00:00:08,000
Welcome to AI Video Studio - Intelligent Video Editor prototype.

2
00:00:10,500 --> 00:00:17,500
This is Scene 2 demonstrating automated scene analysis.

3
00:00:18,500 --> 00:00:24,500
This is the target segment from 00:18 to 00:25 for splitting and deleting.

4
00:00:25,500 --> 00:00:29,500
Export your final edited video with synchronized audio and subtitles.
"""
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content.strip())

    cmd_bgm = [
        FFMPEG_PATH, "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=523.25:duration=30",
        "-af", "volume=0.4",
        "-c:a", "pcm_s16le",
        str(audio_path)
    ]
    subprocess.run(cmd_bgm, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return str(video_path), str(srt_path), str(audio_path)

def generate_multi_clip_pack():
    """
    Generates a pack of 3 distinct video clips to demonstrate multi-clip LLM analysis & assembly:
    - Clip 1: Interview / Speaker Dialogue (12s)
    - Clip 2: High Motion Action B-Roll (10s)
    - Clip 3: Scenic Presentation & Outro (10s)
    """
    clip1_path = SAMPLE_DIR / "clip1_interview.mp4"
    clip2_path = SAMPLE_DIR / "clip2_action_broll.mp4"
    clip3_path = SAMPLE_DIR / "clip3_scenic_overview.mp4"
    srt_path = SAMPLE_DIR / "sample_multiclip.srt"
    bgm_path = SAMPLE_DIR / "sample_bgm.wav"

    if clip1_path.exists() and clip2_path.exists() and clip3_path.exists():
        return [str(clip1_path), str(clip2_path), str(clip3_path)], str(srt_path), str(bgm_path)

    print("Generating multi-clip video production assets...")
    width, height = 854, 480
    fps = 25

    # --- 1. Clip 1: Interview & Keynote Dialogue (12 seconds) ---
    temp_avi1 = SAMPLE_DIR / "temp_c1.avi"
    out1 = cv2.VideoWriter(str(temp_avi1), cv2.VideoWriter_fourcc(*"MJPG"), fps, (width, height))
    for f in range(fps * 12):
        sec = f / fps
        frame = np.full((height, width, 3), (35, 40, 50), dtype=np.uint8)
        # Talking head badge
        cv2.circle(frame, (width // 2, 180), 65, (70, 110, 160), -1)
        cv2.circle(frame, (width // 2, 180), 70, (200, 220, 240), 2)
        cv2.putText(frame, "SPEAKER / KEYNOTE", (width // 2 - 140, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(frame, '"Welcome to EditMind AI Video Assembly"', (width // 2 - 230, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 220, 255), 2)
        # Timecode
        cv2.putText(frame, f"Clip 1 [Interview] - {sec:04.1f}s", (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (100, 255, 100), 2)
        out1.write(frame)
    out1.release()

    temp_aud1 = SAMPLE_DIR / "temp_a1.wav"
    subprocess.run([
        FFMPEG_PATH, "-y", "-f", "lavfi", "-i", "sine=frequency=330:duration=12",
        "-c:a", "pcm_s16le", str(temp_aud1)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    subprocess.run([
        FFMPEG_PATH, "-y", "-i", str(temp_avi1), "-i", str(temp_aud1),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
        str(clip1_path)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # --- 2. Clip 2: High Motion Action B-Roll (10 seconds) ---
    temp_avi2 = SAMPLE_DIR / "temp_c2.avi"
    out2 = cv2.VideoWriter(str(temp_avi2), cv2.VideoWriter_fourcc(*"MJPG"), fps, (width, height))
    for f in range(fps * 10):
        sec = f / fps
        frame = np.full((height, width, 3), (20, 70, 90), dtype=np.uint8)
        # Fast motion animated spheres
        x1 = int(width / 2 + math.sin(sec * 4) * 220)
        y1 = int(height / 2 + math.cos(sec * 4) * 110)
        cv2.circle(frame, (x1, y1), 50, (0, 220, 255), -1)
        x2 = int(width / 2 - math.sin(sec * 4) * 220)
        y2 = int(height / 2 - math.cos(sec * 4) * 110)
        cv2.circle(frame, (x2, y2), 40, (255, 80, 180), -1)

        cv2.putText(frame, "DYNAMIC ACTION B-ROLL", (width // 2 - 180, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(frame, f"Clip 2 [Action] - {sec:04.1f}s", (30, height - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        out2.write(frame)
    out2.release()

    temp_aud2 = SAMPLE_DIR / "temp_a2.wav"
    subprocess.run([
        FFMPEG_PATH, "-y", "-f", "lavfi", "-i", "sine=frequency=587.33:duration=10:beep_factor=3",
        "-c:a", "pcm_s16le", str(temp_aud2)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    subprocess.run([
        FFMPEG_PATH, "-y", "-i", str(temp_avi2), "-i", str(temp_aud2),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
        str(clip2_path)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # --- 3. Clip 3: Scenic Presentation & Outro (10 seconds) ---
    temp_avi3 = SAMPLE_DIR / "temp_c3.avi"
    out3 = cv2.VideoWriter(str(temp_avi3), cv2.VideoWriter_fourcc(*"MJPG"), fps, (width, height))
    for f in range(fps * 10):
        sec = f / fps
        frame = np.full((height, width, 3), (80, 30, 60), dtype=np.uint8)
        # Presentation cards
        cv2.rectangle(frame, (100, 120), (width - 100, height - 120), (35, 15, 30), -1)
        cv2.rectangle(frame, (100, 120), (width - 100, height - 120), (190, 80, 140), 2)
        cv2.putText(frame, "SCENIC OVERVIEW & FINALE", (140, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(frame, "Automated Assembly & Context Preservation", (140, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 200, 230), 2)
        cv2.putText(frame, f"Clip 3 [Scenic] - {sec:04.1f}s", (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 180, 255), 2)
        out3.write(frame)
    out3.release()

    temp_aud3 = SAMPLE_DIR / "temp_a3.wav"
    subprocess.run([
        FFMPEG_PATH, "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=10",
        "-c:a", "pcm_s16le", str(temp_aud3)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    subprocess.run([
        FFMPEG_PATH, "-y", "-i", str(temp_avi3), "-i", str(temp_aud3),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
        str(clip3_path)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Clean up temp files
    for p in [temp_avi1, temp_aud1, temp_avi2, temp_aud2, temp_avi3, temp_aud3]:
        if p.exists():
            p.unlink()

    # Subtitles for multi-clip assembly
    multi_srt = """1
00:00:01,000 --> 00:00:05,000
Welcome to EditMind AI Video Assembly.

2
00:00:06,000 --> 00:00:10,000
Examining source media and pacing.

3
00:00:12,000 --> 00:00:16,000
High-energy visual cut assembled automatically.

4
00:00:18,000 --> 00:00:22,000
Ready for user refinement and timeline inspection.
"""
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(multi_srt.strip())

    return [str(clip1_path), str(clip2_path), str(clip3_path)], str(srt_path), str(bgm_path)

if __name__ == "__main__":
    generate_sample_assets()
    generate_multi_clip_pack()
