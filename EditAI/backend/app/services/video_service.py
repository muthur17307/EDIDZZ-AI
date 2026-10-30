import os
import re
import cv2
import numpy as np
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from app.config import FFMPEG_PATH, THUMBNAIL_DIR
from app.models.schemas import MediaMetadata, SceneSegment, SilenceSegment

class VideoService:
    @staticmethod
    def probe_media(filepath: str) -> MediaMetadata:
        """Extracts complete media metadata using OpenCV and FFmpeg."""
        path = Path(filepath)
        filename = path.name
        size_bytes = os.path.getsize(filepath) if os.path.exists(filepath) else 0

        # Probe with OpenCV
        cap = cv2.VideoCapture(filepath)
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        cap.release()

        duration = (frame_count / fps) if (fps > 0 and frame_count > 0) else 0.0

        # Check audio presence and precise duration with FFmpeg
        has_audio = False
        codec = ""
        try:
            cmd = [FFMPEG_PATH, "-i", filepath]
            result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace", timeout=10)
            output = result.stderr

            # Audio stream check
            if "Audio:" in output:
                has_audio = True

            # Duration regex fallback
            dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", output)
            if dur_match:
                hours = float(dur_match.group(1))
                minutes = float(dur_match.group(2))
                seconds = float(dur_match.group(3))
                ffmpeg_duration = hours * 3600 + minutes * 60 + seconds
                if ffmpeg_duration > 0:
                    duration = ffmpeg_duration

            # Video codec regex
            v_match = re.search(r"Video:\s*([a-zA-Z0-9_-]+)", output)
            if v_match:
                codec = v_match.group(1)
        except Exception as e:
            print(f"FFmpeg probe warning: {e}")

        # Fallback if codec is empty
        if not codec:
            codec = path.suffix.replace(".", "").upper()

        return MediaMetadata(
            filename=filename,
            filepath=str(path.resolve()),
            duration=round(duration, 3),
            width=width,
            height=height,
            fps=round(fps, 2),
            format=path.suffix.lower(),
            has_audio=has_audio,
            size_bytes=size_bytes,
            codec=codec
        )

    @staticmethod
    def extract_thumbnail(filepath: str, timestamp: float, output_filename: Optional[str] = None) -> Optional[str]:
        """Extracts a frame at timestamp and saves as JPEG thumbnail."""
        try:
            if not output_filename:
                stem = Path(filepath).stem
                safe_time = f"{timestamp:.2f}".replace(".", "_")
                output_filename = f"{stem}_thumb_{safe_time}.jpg"

            out_path = THUMBNAIL_DIR / output_filename

            # If thumbnail already exists, return relative URL
            if out_path.exists():
                return f"/media_files/thumbnails/{output_filename}"

            cap = cv2.VideoCapture(filepath)
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            success, frame = cap.read()
            cap.release()

            if success and frame is not None:
                # Resize thumbnail to max 320x180 for efficient loading
                h, w = frame.shape[:2]
                target_w = 320
                target_h = int(h * (target_w / w)) if w > 0 else 180
                thumb = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
                cv2.imwrite(str(out_path), thumb)
                return f"/media_files/thumbnails/{output_filename}"

            # Fallback with FFmpeg if OpenCV seek fails
            cmd = [
                FFMPEG_PATH, "-ss", str(max(0, timestamp)),
                "-i", filepath,
                "-vframes", "1",
                "-vf", "scale=320:-1",
                "-y", str(out_path)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            if out_path.exists():
                return f"/media_files/thumbnails/{output_filename}"

        except Exception as e:
            print(f"Thumbnail extraction error at {timestamp}: {e}")

        return None

    @classmethod
    def detect_scenes(cls, filepath: str, duration: float) -> List[SceneSegment]:
        """Detects scenes using PySceneDetect with OpenCV fallback."""
        scenes: List[SceneSegment] = []

        # 1. Attempt PySceneDetect
        try:
            from scenedetect import detect, ContentDetector, AdaptiveDetector
            scene_list = detect(filepath, ContentDetector(threshold=27.0))
            if scene_list:
                for idx, (start_timecode, end_timecode) in enumerate(scene_list):
                    start_sec = round(start_timecode.get_seconds(), 2)
                    end_sec = round(end_timecode.get_seconds(), 2)
                    dur = round(end_sec - start_sec, 2)
                    if dur < 0.2:
                        continue
                    thumb = cls.extract_thumbnail(filepath, start_sec + (dur / 2))
                    scenes.append(SceneSegment(
                        scene_id=idx + 1,
                        start_time=start_sec,
                        end_time=end_sec,
                        duration=dur,
                        start_frame=start_timecode.get_frames(),
                        end_frame=end_timecode.get_frames(),
                        thumbnail_url=thumb,
                        visual_description=f"Scene {idx + 1} ({dur:.1f}s)"
                    ))
        except Exception as e:
            print(f"PySceneDetect error or fallback: {e}")

        # 2. OpenCV fallback if no scenes found or single scene detected on long video
        if not scenes or (len(scenes) <= 1 and duration > 5.0):
            scenes = cls._detect_scenes_opencv(filepath, duration)

        # 3. Post-process scenes for motion, brightness, and low-activity detection
        cls._analyze_scene_activity(filepath, scenes)

        return scenes

    @classmethod
    def _detect_scenes_opencv(cls, filepath: str, duration: float) -> List[SceneSegment]:
        """Fallback scene detection using OpenCV histogram differences."""
        scenes: List[SceneSegment] = []
        cap = cv2.VideoCapture(filepath)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        if total_frames <= 0 or fps <= 0:
            cap.release()
            return [SceneSegment(
                scene_id=1,
                start_time=0.0,
                end_time=round(duration, 2),
                duration=round(duration, 2),
                thumbnail_url=cls.extract_thumbnail(filepath, 0.5),
                visual_description="Full Video Scene"
            )]

        # Sample every 0.25 seconds
        step = max(1, int(fps * 0.25))
        prev_hist = None
        scene_start_sec = 0.0
        scene_id = 1

        frame_idx = 0
        while frame_idx < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [32], [0, 256])
            cv2.normalize(hist, hist)

            current_sec = frame_idx / fps

            if prev_hist is not None:
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                # Significant change detected
                if diff < 0.65 and (current_sec - scene_start_sec) >= 1.5:
                    end_sec = round(current_sec, 2)
                    dur = round(end_sec - scene_start_sec, 2)
                    mid_sec = scene_start_sec + (dur / 2)
                    thumb = cls.extract_thumbnail(filepath, mid_sec)
                    scenes.append(SceneSegment(
                        scene_id=scene_id,
                        start_time=round(scene_start_sec, 2),
                        end_time=end_sec,
                        duration=dur,
                        thumbnail_url=thumb,
                        visual_description=f"Scene {scene_id} ({dur:.1f}s)"
                    ))
                    scene_id += 1
                    scene_start_sec = end_sec

            prev_hist = hist
            frame_idx += step

        cap.release()

        # Add the final scene
        final_end = round(duration, 2)
        if final_end > scene_start_sec:
            dur = round(final_end - scene_start_sec, 2)
            mid_sec = scene_start_sec + (dur / 2)
            thumb = cls.extract_thumbnail(filepath, mid_sec)
            scenes.append(SceneSegment(
                scene_id=scene_id,
                start_time=round(scene_start_sec, 2),
                end_time=final_end,
                duration=dur,
                thumbnail_url=thumb,
                visual_description=f"Scene {scene_id} ({dur:.1f}s)"
            ))

        return scenes

    @classmethod
    def _analyze_scene_activity(cls, filepath: str, scenes: List[SceneSegment]):
        """Evaluates motion score and brightness for each scene to tag low-activity segments."""
        cap = cv2.VideoCapture(filepath)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

        for scene in scenes:
            midpoint = scene.start_time + (scene.duration / 2)
            cap.set(cv2.CAP_PROP_POS_MSEC, midpoint * 1000)
            ret, frame1 = cap.read()

            cap.set(cv2.CAP_PROP_POS_MSEC, min(midpoint + 0.3, scene.end_time) * 1000)
            ret2, frame2 = cap.read()

            if ret and ret2 and frame1 is not None and frame2 is not None:
                gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

                brightness = float(np.mean(gray1))
                diff = cv2.absdiff(gray1, gray2)
                motion_score = float(np.mean(diff))

                scene.average_brightness = round(brightness, 1)
                scene.motion_score = round(motion_score, 2)

                # Low-activity detection: if motion is very small and duration is notable
                if motion_score < 1.8 and scene.duration >= 2.0:
                    scene.is_low_activity = True
                    scene.visual_description += " [Low Activity / Static]"
                elif motion_score > 15.0:
                    scene.visual_description += " [High Motion Action]"
                else:
                    scene.visual_description += " [Standard Activity]"

        cap.release()

    @staticmethod
    def detect_silence(filepath: str) -> List[SilenceSegment]:
        """Detects silence intervals using FFmpeg silencedetect audio filter."""
        silences: List[SilenceSegment] = []
        try:
            cmd = [
                FFMPEG_PATH, "-i", filepath,
                "-af", "silencedetect=noise=-30dB:d=0.8",
                "-f", "null", "-"
            ]
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace", timeout=30)
            output = res.stderr

            starts = [float(m.group(1)) for m in re.finditer(r"silence_start:\s*([0-9.]+)", output)]
            ends = []
            durs = []
            for m in re.finditer(r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)", output):
                ends.append(float(m.group(1)))
                durs.append(float(m.group(2)))

            count = min(len(starts), len(ends))
            for i in range(count):
                s = round(starts[i], 2)
                e = round(ends[i], 2)
                d = round(durs[i], 2)
                if d >= 0.5:
                    silences.append(SilenceSegment(start_time=s, end_time=e, duration=d))
        except Exception as e:
            print(f"Silence detection error: {e}")

        return silences
