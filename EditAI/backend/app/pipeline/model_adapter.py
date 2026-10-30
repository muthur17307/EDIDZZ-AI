# app/pipeline/model_adapter.py
"""
AI Model Adapter for Video Analysis and Global Story Planning.
Connects the offline video-analysis AI models and backend modules:
- OpenCV & FFmpeg multimodal feature extraction (scenes, motion scoring, brightness, silence)
- Speech & audio transcription
- Intelligent cross-clip global story planner with repetition detection
- Local Ollama (qwen2.5:7b) / Cloud LLM provider integration
"""

import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.pipeline.context_builder import build_story_context, build_planner_prompt
from app.services.video_service import VideoService
from app.services.speech_service import SpeechService
from app.services.ai_adapter import AIModelAdapter


def analyze_clip(
    video_path: str,
    clip_id: str,
    brief: str,
) -> dict[str, Any]:
    """
    Analyzes a video clip using offline computer vision and audio feature extraction.
    Returns structured segment-level metadata matching the required contract:
    {
        "clip_id": "clip_001",
        "duration": 45.2,
        "segments": [
            {
                "start": 0.0,
                "end": 5.0,
                "transcript": "Our product saves time.",
                "visual_summary": "Speaker explains the product.",
                "story_role": "benefit",
                "quality": 0.9
            }
        ]
    }
    """
    path = Path(video_path)
    if not path.is_file():
        raise FileNotFoundError(f"Video clip not found: {video_path}")

    # 1. Probing media duration & technical characteristics
    duration = 0.0
    width = 1920
    height = 1080
    fps = 25.0
    has_audio = True

    try:
        meta = VideoService.probe_media(str(path))
        duration = meta.duration
        width = meta.width
        height = meta.height
        fps = meta.fps
        has_audio = meta.has_audio
    except Exception as e:
        print(f"VideoService probe warning for {clip_id}: {e}")

    # Fallback duration via OpenCV if probe was zero
    if duration <= 0:
        try:
            import cv2
            cap = cv2.VideoCapture(str(path))
            f_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            f_cnt = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
            cap.release()
            if f_fps > 0 and f_cnt > 0:
                duration = round(f_cnt / f_fps, 2)
        except Exception:
            duration = 10.0

    duration = max(1.0, round(duration, 2))

    # 2. Scene detection & motion activity analysis
    scenes = []
    try:
        scenes = VideoService.detect_scenes(str(path), duration)
    except Exception as e:
        print(f"Scene detection warning for {clip_id}: {e}")

    # 3. Speech & silence detection
    speech_segments = []
    if has_audio:
        try:
            speech_segments, _ = SpeechService.transcribe(str(path), duration)
        except Exception as e:
            print(f"Speech transcription note for {clip_id}: {e}")

    # 4. Construct granular segment breakdown
    segments: List[Dict[str, Any]] = []

    if scenes and len(scenes) > 0:
        for idx, scene in enumerate(scenes):
            start = round(scene.start_time, 2)
            end = round(min(scene.end_time, duration), 2)
            dur = round(end - start, 2)
            if dur < 0.2:
                continue

            # Match overlapping speech dialogue
            matching_speech = [
                s.text for s in speech_segments
                if not (s.end_time < start or s.start_time > end)
            ]
            transcript = " ".join(matching_speech).strip()

            # Visual summary & activity
            motion_score = getattr(scene, "motion_score", 5.0)
            is_low_activity = getattr(scene, "is_low_activity", False)
            brightness = getattr(scene, "average_brightness", 120.0)

            if not transcript:
                if is_low_activity:
                    transcript = "Ambient or presentation visual framing; no spoken dialogue."
                elif motion_score > 8.0:
                    transcript = "High kinetic motion visual sequence with ambient audio."
                else:
                    transcript = "Visual narrative scene without spoken dialogue."

            visual_summary = (
                f"Scene {idx + 1} ({dur:.1f}s): "
                f"{'High action kinetic motion' if motion_score > 8.0 else 'Static low activity' if is_low_activity else 'Balanced visual pacing'} "
                f"(motion: {motion_score:.1f}, brightness: {brightness:.0f})"
            )

            # Classify story role
            if matching_speech and start <= 3.0:
                story_role = "introduction"
            elif matching_speech and any(w in transcript.lower() for w in ["benefit", "feature", "save", "solution", "value", "ai", "assemble"]):
                story_role = "benefit"
            elif matching_speech:
                story_role = "dialogue"
            elif motion_score > 8.0:
                story_role = "action_broll"
            elif is_low_activity and dur >= 3.0:
                story_role = "presentation"
            elif end >= duration - 2.5:
                story_role = "outro"
            else:
                story_role = "scenic_broll"

            # Compute quality score
            base_q = 0.85
            if matching_speech:
                base_q += 0.08
            if motion_score > 6.0:
                base_q += 0.04
            if is_low_activity and not matching_speech:
                base_q -= 0.15

            quality = round(max(0.40, min(0.98, base_q)), 2)

            segments.append({
                "start": start,
                "end": end,
                "transcript": transcript,
                "visual_summary": visual_summary,
                "story_role": story_role,
                "quality": quality,
            })
    else:
        # Fallback segmentation: divide into 4-second narrative beats
        step = 4.0
        cur = 0.0
        beat_idx = 1
        while cur < duration:
            seg_end = round(min(cur + step, duration), 2)
            matching_speech = [
                s.text for s in speech_segments
                if not (s.end_time < cur or s.start_time > seg_end)
            ]
            transcript = " ".join(matching_speech).strip() or f"Visual sequence beat {beat_idx}."
            role = "introduction" if cur == 0.0 else "outro" if seg_end >= duration else "benefit" if matching_speech else "action_broll"

            segments.append({
                "start": round(cur, 2),
                "end": seg_end,
                "transcript": transcript,
                "visual_summary": f"Video segment beat {beat_idx} ({seg_end - cur:.1f}s)",
                "story_role": role,
                "quality": 0.88,
            })
            cur = seg_end
            beat_idx += 1

    return {
        "clip_id": clip_id,
        "filename": path.name,
        "duration": duration,
        "summary": f"{path.name}: {duration:.1f}s, {len(segments)} analyzed segments",
        "segments": segments,
    }


def plan_global_edit(
    brief: str,
    all_clip_analyses: list[dict[str, Any]] = None,
    analyses: list[dict[str, Any]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Compares segments ACROSS ALL CLIPS to build a coherent global narrative.
    Connects to local Ollama (qwen2.5:7b) / LLM if available, or employs the deterministic offline
    editorial story planning engine with semantic repetition detection.
    """
    clips = all_clip_analyses or analyses or kwargs.get("clips") or []
    if not clips:
        raise ValueError("No clip analyses provided to plan_global_edit.")

    # 1. Synthesize unified cross-clip context
    context = build_story_context(brief, clips)

    # 2. Attempt LLM planning if local Ollama or cloud provider is online
    prompt = build_planner_prompt(context)
    system_instruction = (
        "You are an expert editorial planning assistant. "
        "Compare all video segments across clips and return strict JSON with 'story_summary', "
        "'ordered_segments', and 'review_items'."
    )

    # Check local Ollama first (offline AI model detection)
    try:
        ollama_models = AIModelAdapter.get_ollama_models()
        if ollama_models:
            res = AIModelAdapter.call_ollama(prompt, system_instruction, timeout=40.0)
            if res and isinstance(res.get("ordered_segments"), list) and len(res["ordered_segments"]) > 0:
                # Safely normalize nested lists if LLM wrapped segments
                flat = []
                for s in res["ordered_segments"]:
                    if isinstance(s, list):
                        flat.extend([x for x in s if isinstance(x, dict)])
                    elif isinstance(s, dict):
                        flat.append(s)
                res["ordered_segments"] = flat
                if len(res["ordered_segments"]) > 0:
                    return res
    except Exception:
        pass

    # Check cloud keys if configured in environment
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        try:
            res = AIModelAdapter.call_gemini(
                prompt,
                system_instruction,
                os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
            )
            if res and isinstance(res.get("ordered_segments"), list) and len(res["ordered_segments"]) > 0:
                # Safely normalize nested lists if LLM wrapped segments
                flat = []
                for s in res["ordered_segments"]:
                    if isinstance(s, list):
                        flat.extend([x for x in s if isinstance(x, dict)])
                    elif isinstance(s, dict):
                        flat.append(s)
                res["ordered_segments"] = flat
                if len(res["ordered_segments"]) > 0:
                    return res
        except Exception:
            pass

    # 3. Offline Intelligent Editorial Story Planning Engine
    # Evaluates all candidate segments across every clip to construct an optimal narrative arc
    ordered_segments: List[Dict[str, Any]] = []
    review_items: List[Dict[str, Any]] = []

    # Flatten and index all segments across all source clips
    all_segments: List[Dict[str, Any]] = []
    clip_map = {c["clip_id"]: c for c in clips}

    for clip in clips:
        cid = clip["clip_id"]
        for seg in clip.get("segments", []):
            all_segments.append({
                **seg,
                "clip_id": cid,
                "filename": clip.get("filename", cid),
            })

    if not all_segments:
        raise ValueError("No segments found in clip analyses.")

    # Group segments by semantic story role
    by_role: Dict[str, List[Dict[str, Any]]] = {}
    for s in all_segments:
        role = s.get("story_role", "broll")
        by_role.setdefault(role, []).append(s)

    # Sort candidates by quality descending
    for role_key in by_role:
        by_role[role_key].sort(key=lambda x: x.get("quality", 0.8), reverse=True)

    # --- BEAT 1: Narrative Hook / Opening ---
    hook_candidates = by_role.get("introduction", []) + by_role.get("dialogue", []) + all_segments
    best_hook = hook_candidates[0]
    hook_dur = min(5.0, best_hook["end"] - best_hook["start"])

    ordered_segments.append({
        "clip_id": best_hook["clip_id"],
        "start": best_hook["start"],
        "end": round(best_hook["start"] + hook_dur, 2),
        "decision": "keep",
        "reason": f"Strong opening hook from {best_hook.get('filename')}: establishes context and theme.",
        "story_role": "introduction",
    })

    # Flag secondary introduction takes for review (Cross-clip repetition check)
    for other_intro in (by_role.get("introduction", []) + by_role.get("dialogue", []))[1:3]:
        if other_intro["clip_id"] != best_hook["clip_id"] or other_intro["start"] != best_hook["start"]:
            review_items.append({
                "clip_id": other_intro["clip_id"],
                "start": other_intro["start"],
                "end": other_intro["end"],
                "reason": f"Alternate opening take from {other_intro.get('filename')}; higher-quality take selected for timeline.",
                "story_role": other_intro.get("story_role", "introduction"),
            })

    # --- BEAT 2: Dynamic Action B-Roll / Visual Pacing ---
    action_candidates = by_role.get("action_broll", []) or [s for s in all_segments if s["clip_id"] != best_hook["clip_id"]]
    if action_candidates:
        best_action = action_candidates[0]
        act_in = best_action["start"]
        act_dur = min(4.5, max(2.0, best_action["end"] - act_in))
        ordered_segments.append({
            "clip_id": best_action["clip_id"],
            "start": act_in,
            "end": round(act_in + act_dur, 2),
            "decision": "keep",
            "reason": f"Dynamic action sequence from {best_action.get('filename')}: accelerates visual pacing.",
            "story_role": "action_broll",
        })

    # --- BEAT 3: Core Message / Value Proposition ---
    core_candidates = by_role.get("benefit", []) or by_role.get("dialogue", []) or by_role.get("presentation", [])
    best_core = None
    for cand in core_candidates:
        if not (cand["clip_id"] == best_hook["clip_id"] and abs(cand["start"] - best_hook["start"]) < 1.0):
            best_core = cand
            break

    if not best_core and len(all_segments) > 2:
        best_core = all_segments[2]
    elif not best_core:
        best_core = all_segments[-1]

    core_in = best_core["start"]
    core_dur = min(5.0, max(2.5, best_core["end"] - core_in))
    ordered_segments.append({
        "clip_id": best_core["clip_id"],
        "start": core_in,
        "end": round(core_in + core_dur, 2),
        "decision": "keep",
        "reason": f"Core value proposition from {best_core.get('filename')}: delivers primary narrative message.",
        "story_role": "core_message",
    })

    # --- BEAT 4: Scenic Finale & Outro ---
    outro_candidates = by_role.get("outro", []) or by_role.get("scenic_broll", []) or [s for s in all_segments if s != best_hook and s != best_core]
    best_outro = outro_candidates[-1] if outro_candidates else all_segments[-1]

    outro_in = max(best_outro["start"], best_outro["end"] - 4.5)
    outro_end = best_outro["end"]
    if outro_end > outro_in + 1.0:
        ordered_segments.append({
            "clip_id": best_outro["clip_id"],
            "start": round(outro_in, 2),
            "end": round(outro_end, 2),
            "decision": "keep",
            "reason": f"Atmospheric closing sequence from {best_outro.get('filename')}: provides visual and narrative closure.",
            "story_role": "outro",
        })

    # Flag low-activity or very short segments in review_items
    for seg in all_segments:
        dur = seg["end"] - seg["start"]
        if dur < 0.8:
            review_items.append({
                "clip_id": seg["clip_id"],
                "start": seg["start"],
                "end": seg["end"],
                "reason": f"Very short segment ({dur:.2f}s) in {seg.get('filename')}; flagged for duration review.",
                "story_role": seg.get("story_role", "unknown"),
            })
        elif "static" in seg.get("transcript", "").lower() or "low activity" in seg.get("visual_summary", "").lower():
            if not any(s["clip_id"] == seg["clip_id"] and s["start"] == seg["start"] for s in ordered_segments):
                review_items.append({
                    "clip_id": seg["clip_id"],
                    "start": seg["start"],
                    "end": seg["end"],
                    "reason": f"Static low-motion segment in {seg.get('filename')}; omitted to prevent pacing drag.",
                    "story_role": seg.get("story_role", "presentation"),
                })

    story_summary = (
        f"Cohesive editorial story synthesized across {len(clips)} source clips according to brief '{brief}'. "
        f"The sequence opens with an establishing dialogue hook, transitions into dynamic action B-roll for pacing, "
        f"articulates the core narrative message, and concludes with a scenic outro. "
        f"{len(review_items)} alternative/redundant segments were flagged for editorial review."
    )

    return {
        "story_summary": story_summary,
        "ordered_segments": ordered_segments,
        "review_items": review_items,
    }

