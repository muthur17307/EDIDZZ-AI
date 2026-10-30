import os
import uuid
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, List

from app.config import FFMPEG_PATH, EXPORT_DIR
from app.models.schemas import TimelineState, ExportResponse, SubtitleItem

class ExportService:
    @staticmethod
    def _create_srt_file(subtitles: List[SubtitleItem], out_path: str):
        """Writes SubtitleItems to an SRT file."""
        def format_srt_time(sec: float) -> str:
            hrs = int(sec // 3600)
            mins = int((sec % 3600) // 60)
            secs = int(sec % 60)
            millis = int(round((sec - int(sec)) * 1000))
            return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

        with open(out_path, "w", encoding="utf-8") as f:
            for idx, sub in enumerate(subtitles):
                f.write(f"{idx + 1}\n")
                f.write(f"{format_srt_time(sub.start_time)} --> {format_srt_time(sub.end_time)}\n")
                f.write(f"{sub.text}\n\n")

    @classmethod
    def render_timeline(
        cls,
        timeline: TimelineState,
        resolution: str = "original",
        aspect_ratio: str = "16:9",
        scaling_mode: str = "crop",
        burn_subtitles: bool = False,
        audio_mode: str = "original",
        external_audio_path: Optional[str] = None
    ) -> ExportResponse:
        """
        Renders the active timeline clips into a single finalized MP4 video file.
        """
        if not timeline.clips:
            return ExportResponse(
                success=False,
                export_id="",
                download_url="",
                filename="",
                duration=0.0,
                size_bytes=0,
                message="Cannot export empty timeline."
            )

        export_id = f"export_{uuid.uuid4().hex[:10]}"
        output_filename = f"{export_id}.mp4"
        output_path = EXPORT_DIR / output_filename

        temp_dir = tempfile.mkdtemp(prefix="edit_export_")
        temp_dir_path = Path(temp_dir)

        try:
            rendered_segments: List[str] = []

            # Step 1: Render each individual clip segment
            for i, clip in enumerate(timeline.clips):
                seg_file = temp_dir_path / f"segment_{i:04d}.mp4"
                dur = clip.duration

                # Trim using accurate input seeking
                cmd = [
                    FFMPEG_PATH, "-y",
                    "-ss", str(clip.source_start),
                    "-t", str(dur),
                    "-i", clip.source_file,
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-crf", "22",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-avoid_negative_ts", "make_zero",
                    str(seg_file)
                ]

                # Video filter for aspect ratio and resolution
                vf_filters = []
                if aspect_ratio == "9:16":
                    if scaling_mode == "crop":
                        vf_filters.append("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920")
                    else:
                        vf_filters.append("scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black")
                elif aspect_ratio == "1:1":
                    vf_filters.append("scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080")
                elif resolution == "1080p":
                    vf_filters.append("scale=-2:1080")
                elif resolution == "720p":
                    vf_filters.append("scale=-2:720")

                if vf_filters:
                    cmd.extend(["-vf", ",".join(vf_filters)])

                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
                if res.returncode != 0 or not seg_file.exists():
                    print(f"Segment {i} render warning: {res.stderr.decode('utf-8', errors='ignore')[:300]}")
                rendered_segments.append(str(seg_file))

            if not rendered_segments:
                raise Exception("Failed to generate any video segments.")

            # Step 2: Concatenate all segments
            concat_list_file = temp_dir_path / "concat_list.txt"
            with open(concat_list_file, "w", encoding="utf-8") as f:
                for seg_path in rendered_segments:
                    # Escape backslashes for FFmpeg concat demuxer
                    safe_path = seg_path.replace("\\", "/")
                    f.write(f"file '{safe_path}'\n")

            concatenated_raw = temp_dir_path / "concatenated_raw.mp4"
            cmd_concat = [
                FFMPEG_PATH, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list_file),
                "-c", "copy",
                str(concatenated_raw)
            ]
            subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=120)

            # Step 3: Handle Audio Mode & Subtitles
            current_input = str(concatenated_raw)
            final_cmd = [FFMPEG_PATH, "-y", "-i", current_input]

            # If external audio is supplied and requested
            ext_audio_exists = external_audio_path and os.path.exists(external_audio_path)
            if ext_audio_exists and audio_mode in ["external", "mix"]:
                final_cmd.extend(["-i", external_audio_path])
                if audio_mode == "external":
                    # Replace video audio with external audio, trimmed to video length
                    final_cmd.extend([
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-shortest"
                    ])
                elif audio_mode == "mix":
                    # Mix video original audio and external audio
                    final_cmd.extend([
                        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first[aout]",
                        "-map", "0:v:0",
                        "-map", "[aout]",
                        "-c:v", "copy",
                        "-c:a", "aac"
                    ])
            else:
                # Keep audio from concatenated video
                final_cmd.extend(["-c", "copy"])

            final_cmd.append(str(output_path))
            subprocess.run(final_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=120)

            # Step 4: If subtitles exist and burning is requested, burn them into video
            if burn_subtitles and timeline.subtitles:
                srt_path = temp_dir_path / "subtitles.srt"
                cls._create_srt_file(timeline.subtitles, str(srt_path))

                subbed_output = temp_dir_path / "subbed_output.mp4"
                safe_srt = str(srt_path).replace("\\", "/").replace(":", "\\:")
                burn_cmd = [
                    FFMPEG_PATH, "-y",
                    "-i", str(output_path),
                    "-vf", f"subtitles='{safe_srt}':force_style='FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3'",
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-c:a", "copy",
                    str(subbed_output)
                ]
                res_burn = subprocess.run(burn_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
                if res_burn.returncode == 0 and subbed_output.exists():
                    # Replace output with subbed video using shutil.move (cross-drive safe)
                    if output_path.exists():
                        output_path.unlink()
                    shutil.move(str(subbed_output), str(output_path))

            file_size = output_path.stat().st_size if output_path.exists() else 0
            download_url = f"/media_files/exports/{output_filename}"

            return ExportResponse(
                success=True,
                export_id=export_id,
                download_url=download_url,
                filename=output_filename,
                duration=timeline.total_duration,
                size_bytes=file_size,
                message=f"Export successfully generated: {output_filename} ({timeline.total_duration:.2f}s, {file_size / (1024*1024):.2f} MB)"
            )

        except Exception as e:
            print(f"Export error: {e}")
            return ExportResponse(
                success=False,
                export_id=export_id,
                download_url="",
                filename="",
                duration=0.0,
                size_bytes=0,
                message=f"Export failed: {str(e)}"
            )
        finally:
            # Clean up temp directory
            try:
                for f in temp_dir_path.glob("*"):
                    try:
                        f.unlink()
                    except Exception:
                        pass
                temp_dir_path.rmdir()
            except Exception:
                pass
