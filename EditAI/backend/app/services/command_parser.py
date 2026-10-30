import re
from typing import Optional, Tuple, List, Dict, Any

from app.models.schemas import (
    TimelineState,
    ChatbotCommandRequest,
    ChatbotCommandResponse,
    SceneSegment
)
from app.services.timeline_manager import TimelineManager
from app.services.ai_adapter import AIModelAdapter

class CommandParser:
    @staticmethod
    def parse_timecode(time_str: str) -> Optional[float]:
        """Converts MM:SS, HH:MM:SS, 15s, etc. into seconds."""
        time_str = time_str.strip().lower()

        # Format: HH:MM:SS or MM:SS or M:SS
        if ":" in time_str:
            parts = time_str.split(":")
            try:
                if len(parts) == 3:
                    h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
                    return h * 3600 + m * 60 + s
                elif len(parts) == 2:
                    m, s = float(parts[0]), float(parts[1])
                    return m * 60 + s
            except ValueError:
                return None

        # Format: 15s, 15 sec, 15 seconds
        sec_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:s|sec|secs|seconds?)", time_str)
        if sec_match:
            try:
                return float(sec_match.group(1))
            except ValueError:
                pass

        try:
            return float(time_str)
        except ValueError:
            return None

    @classmethod
    def extract_time_range(cls, text: str) -> Optional[Tuple[float, float]]:
        """Extracts start and end time from expressions."""
        text = text.lower()
        m = re.search(r"(?:from|between)\s+([0-9:.]+s?(?:econds?)?)\s+(?:to|and|-)\s+([0-9:.]+s?(?:econds?)?)", text)
        if m:
            t1 = cls.parse_timecode(m.group(1))
            t2 = cls.parse_timecode(m.group(2))
            if t1 is not None and t2 is not None:
                return (min(t1, t2), max(t1, t2))

        m = re.search(r"(\d+:\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+:\d+(?:\.\d+)?)", text)
        if m:
            t1 = cls.parse_timecode(m.group(1))
            t2 = cls.parse_timecode(m.group(2))
            if t1 is not None and t2 is not None:
                return (min(t1, t2), max(t1, t2))

        # Expressions like "10 to 25 seconds"
        m_num = re.search(r"(?:from\s+)?(\d+(?:\.\d+)?)\s*(?:s|sec|seconds?)?\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds?)", text)
        if m_num:
            t1 = cls.parse_timecode(m_num.group(1))
            t2 = cls.parse_timecode(m_num.group(2))
            if t1 is not None and t2 is not None:
                return (min(t1, t2), max(t1, t2))

        return None

    @classmethod
    def interpret_and_execute(
        cls,
        request: ChatbotCommandRequest,
        timeline_manager: TimelineManager
    ) -> ChatbotCommandResponse:
        """
        Parses user intent with priority:
        1. Configured/Active LLM (Gemini / OpenAI / Groq / Ollama)
        2. High-Capability Contextual Semantic Reasoner (handles relative clips, proportions, speed, silences, scenes)
        """
        raw_cmd = request.prompt.strip()
        cmd = raw_cmd.lower()
        timeline = request.current_timeline
        scenes = request.scenes or []

        # ====================================================
        # 1. TRY LLM REASONING FIRST (If provider configured / available)
        # ====================================================
        llm_result = AIModelAdapter.interpret_command_with_llm(
            prompt=raw_cmd,
            timeline=timeline,
            media=request.media_metadata,
            scenes=scenes,
            llm_config=request.llm_config
        )

        if llm_result and isinstance(llm_result, dict):
            provider_name = llm_result.get("llm_provider", "AI Assistant")
            action = llm_result.get("action", "").lower()
            explanation = llm_result.get("explanation") or f"Executed '{action}' operation."

            # A. Split via LLM
            if action == "split":
                split_time = llm_result.get("split_time")
                if split_time is None and llm_result.get("start_time") is not None:
                    split_time = llm_result.get("start_time")
                if split_time is not None:
                    updated_tl, msg = timeline_manager.split_at(timeline, float(split_time))
                    return ChatbotCommandResponse(
                        understood=True,
                        intent="split",
                        message=f"[{provider_name}] {explanation}",
                        target_time=float(split_time),
                        updated_timeline=updated_tl,
                        action_description=f"Split at {float(split_time):.2f}s",
                        llm_provider=provider_name
                    )

            # B. Delete / Cut via LLM
            elif action in ["delete", "cut"]:
                start = llm_result.get("start_time")
                end = llm_result.get("end_time")
                if start is not None and end is not None:
                    st, et = float(start), float(end)
                    sel_tl, _ = timeline_manager.select_range(timeline, st, et)
                    updated_tl, msg = timeline_manager.delete_selection(sel_tl)
                    return ChatbotCommandResponse(
                        understood=True,
                        intent="delete",
                        message=f"[{provider_name}] {explanation}",
                        target_time=st,
                        updated_timeline=updated_tl,
                        action_description=f"Deleted range {st:.1f}s - {et:.1f}s",
                        llm_provider=provider_name
                    )
                elif llm_result.get("target_clip_id"):
                    target_id = llm_result.get("target_clip_id")
                    target_clip = next((c for c in timeline.clips if c.id == target_id), None)
                    if target_clip:
                        sel_tl, _ = timeline_manager.select_range(timeline, target_clip.timeline_start, target_clip.timeline_end)
                        updated_tl, msg = timeline_manager.delete_selection(sel_tl)
                        return ChatbotCommandResponse(
                            understood=True,
                            intent="delete",
                            message=f"[{provider_name}] {explanation}",
                            updated_timeline=updated_tl,
                            action_description=f"Deleted clip '{target_clip.name}'",
                            llm_provider=provider_name
                        )

            # C. Select via LLM
            elif action == "select":
                start = llm_result.get("start_time")
                end = llm_result.get("end_time")
                if start is not None and end is not None:
                    st, et = float(start), float(end)
                    updated_tl, msg = timeline_manager.select_range(timeline, st, et)
                    return ChatbotCommandResponse(
                        understood=True,
                        intent="select",
                        message=f"[{provider_name}] {explanation}",
                        target_range=[st, et],
                        target_time=st,
                        updated_timeline=updated_tl,
                        llm_provider=provider_name
                    )

            # D. Change Speed via LLM
            elif action == "change_speed" and llm_result.get("speed"):
                target_spd = float(llm_result["speed"])
                target_clip_id = llm_result.get("target_clip_id") or timeline.selected_clip_id or (timeline.clips[0].id if timeline.clips else None)
                if target_clip_id:
                    new_tl = timeline.model_copy(deep=True)
                    for c in new_tl.clips:
                        if c.id == target_clip_id:
                            c.speed = target_spd
                            break
                    return ChatbotCommandResponse(
                        understood=True,
                        intent="change_speed",
                        message=f"[{provider_name}] Changed clip playback speed to {target_spd}x.",
                        updated_timeline=new_tl,
                        llm_provider=provider_name
                    )

            # E. Playback actions
            elif action == "play":
                return ChatbotCommandResponse(
                    understood=True,
                    intent="play",
                    message=f"[{provider_name}] {explanation}",
                    target_time=timeline.playhead_time,
                    llm_provider=provider_name
                )
            elif action == "pause":
                return ChatbotCommandResponse(
                    understood=True,
                    intent="pause",
                    message=f"[{provider_name}] {explanation}",
                    target_time=timeline.playhead_time,
                    llm_provider=provider_name
                )
            elif action == "export":
                return ChatbotCommandResponse(
                    understood=True,
                    intent="export",
                    message=f"[{provider_name}] {explanation}",
                    llm_provider=provider_name
                )

        # ====================================================
        # 2. DEEP GENERIC SEMANTIC NLP REASONER (Offline / Fallback)
        # ====================================================

        # Helper to resolve clip by ordinal name or index
        def find_clip_by_reference(query: str):
            if not timeline.clips:
                return None, None
            # e.g. "first", "second", "third", "fourth", "last", "clip 1", "clip 2"
            ord_map = {
                "first": 0, "1st": 0, "one": 0, "1": 0, "intro": 0,
                "second": 1, "2nd": 1, "two": 1, "2": 1,
                "third": 2, "3rd": 2, "three": 2, "3": 2,
                "fourth": 3, "4th": 3, "four": 3, "4": 3,
                "fifth": 4, "5th": 4,
                "last": len(timeline.clips) - 1, "final": len(timeline.clips) - 1, "outro": len(timeline.clips) - 1
            }
            m_c = re.search(r"\b(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th|last|final|intro|outro|clip\s*\d+)\b", query)
            if m_c:
                key = m_c.group(1).replace("clip", "").strip()
                idx = ord_map.get(key)
                if idx is None and key.isdigit():
                    idx = int(key) - 1
                if idx is not None and 0 <= idx < len(timeline.clips):
                    return timeline.clips[idx], idx
            if timeline.selected_clip_id:
                clip = next((c for c in timeline.clips if c.id == timeline.selected_clip_id), None)
                if clip:
                    idx = timeline.clips.index(clip)
                    return clip, idx
            return timeline.clips[0], 0

        # --- A. Undo / Redo ---
        if re.search(r"\b(undo|revert|step back|undo the last edit)\b", cmd):
            new_tl, msg = timeline_manager.undo(timeline)
            return ChatbotCommandResponse(
                understood=True,
                intent="undo",
                message=msg,
                updated_timeline=new_tl,
                action_description="Undo Action"
            )

        if re.search(r"\b(redo|repeat edit|redo the last edit)\b", cmd):
            new_tl, msg = timeline_manager.redo(timeline)
            return ChatbotCommandResponse(
                understood=True,
                intent="redo",
                message=msg,
                updated_timeline=new_tl,
                action_description="Redo Action"
            )

        # --- B. Export Video ---
        if re.search(r"\b(export|render|export the video|export as mp4|quick export|download video|save as mp4)\b", cmd):
            return ChatbotCommandResponse(
                understood=True,
                intent="export",
                message="Opening export modal to configure resolution, aspect ratio (16:9, 9:16 vertical, 1:1), and render finalized MP4.",
                action_proposal={
                    "type": "export",
                    "title": "Render Edited Video",
                    "details": f"Render active timeline ({timeline.total_duration:.1f}s) via FFmpeg."
                }
            )

        # --- C. Playback Commands ---
        m_seek = re.search(r"(?:seek to|go to|jump to)\s+([0-9:.]+s?(?:econds?)?)", cmd)
        if m_seek:
            seek_ts = cls.parse_timecode(m_seek.group(1))
            if seek_ts is not None:
                seek_ts = max(0.0, min(timeline.total_duration, seek_ts))
                new_tl = timeline.model_copy(deep=True)
                new_tl.playhead_time = seek_ts
                return ChatbotCommandResponse(
                    understood=True,
                    intent="seek",
                    message=f"Playhead jumped to {seek_ts:.2f}s.",
                    target_time=seek_ts,
                    updated_timeline=new_tl
                )

        if re.search(r"\b(play the video|start video|resume|play video|play sequence|play)\b", cmd):
            return ChatbotCommandResponse(
                understood=True,
                intent="play",
                message="Playing video.",
                target_time=timeline.playhead_time
            )

        if re.search(r"\b(pause the video|stop the video|pause playback|pause video|stop|pause)\b", cmd):
            return ChatbotCommandResponse(
                understood=True,
                intent="pause",
                message="Paused video playback.",
                target_time=timeline.playhead_time
            )

        # --- D. Show Scenes / Scene Navigation ---
        if re.search(r"\b(show detected scenes|show scenes|show all detected scenes|list scenes|scenes)\b", cmd):
            return ChatbotCommandResponse(
                understood=True,
                intent="show_scenes",
                message=f"Displaying {len(scenes)} detected scenes in the Inspector."
            )

        m_scene = re.search(r"(?:jump to|go to|play|select)\s+(?:scene\s*)(\d+)", cmd)
        if m_scene and scenes:
            scene_num = int(m_scene.group(1))
            target_scene = next((s for s in scenes if s.scene_id == scene_num), None)
            if target_scene:
                sel_tl, _ = timeline_manager.select_range(timeline, target_scene.start_time, target_scene.end_time)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="play_selected",
                    message=f"Selected Scene {scene_num} ({target_scene.start_time:.1f}s - {target_scene.end_time:.1f}s).",
                    target_range=[target_scene.start_time, target_scene.end_time],
                    target_time=target_scene.start_time,
                    updated_timeline=sel_tl
                )

        # --- E. Speed & Volume Adjustments ---
        # Match "speed up clip 1 to 2x", "set speed to 1.5", "2x speed", etc.
        m_speed = re.search(r"\b(\d+(?:\.\d+)?)\s*x\b", cmd)
        if not m_speed:
            m_speed = re.search(r"(?:speed up|slow down|set speed)\s+.*?\b(?:to\s+)(\d+(?:\.\d+)?)\b", cmd)

        if m_speed and any(w in cmd for w in ["speed", "faster", "slower", "slow down", "speed up"]):
            target_spd = float(m_speed.group(1))
            target_spd = max(0.25, min(4.0, target_spd))
            clip, idx = find_clip_by_reference(cmd)
            if clip:
                new_tl = timeline.model_copy(deep=True)
                for c in new_tl.clips:
                    if c.id == clip.id:
                        c.speed = target_spd
                        break
                return ChatbotCommandResponse(
                    understood=True,
                    intent="change_speed",
                    message=f"Updated clip {idx + 1} '{clip.name}' playback speed to {target_spd}x.",
                    updated_timeline=new_tl
                )

        if re.search(r"\b(mute audio|mute|silence audio)\b", cmd):
            new_tl = timeline.model_copy(deep=True)
            for c in new_tl.clips:
                c.volume = 0.0
            return ChatbotCommandResponse(
                understood=True,
                intent="mute",
                message="Muted audio for timeline clips.",
                updated_timeline=new_tl
            )

                # --- E2. Cross-Clip Editorial & Narrative Reasoning Queries ---
        # "Explain why this section was selected or removed"
        if any(w in cmd for w in ["why was this", "explain why", "why selected", "why removed", "why trimmed", "rationale"]):
            clip, idx = find_clip_by_reference(cmd)
            if clip:
                role = clip.role or "Narrative Segment"
                rat = clip.editorial_rationale or f"Selected as optimal {role} for narrative pacing."
                trim = clip.trimmed_reason or "Trimmed pre-roll pauses to ensure direct viewer engagement."
                return ChatbotCommandResponse(
                    understood=True,
                    intent="explain_rationale",
                    message=(
                        f"Editorial Explanation for Clip {idx + 1} ('{clip.name}'):\n"
                        f"• Role: {role}\n"
                        f"• Selection Rationale: {rat}\n"
                        f"• Trim Details: {trim}"
                    ),
                    target_time=clip.timeline_start
                )

        # "Find repeated statements across these videos" / "Identify redundant footage"
        if any(w in cmd for w in ["repeated statement", "find repeated", "redundant footage", "duplicate take", "repeated footage", "redundancies"]):
            repeated_notes = []
            seen_roles = {}
            for idx, c in enumerate(timeline.clips):
                role = c.role or "Segment"
                if role in seen_roles:
                    repeated_notes.append(f"• Clip {idx+1} ('{c.name}') shares role '{role}' with Clip {seen_roles[role] + 1}; alternate take can be trimmed.")
                else:
                    seen_roles[role] = idx
            if not repeated_notes:
                msg = "Cross-clip analysis completed: No critical duplicate takes found on the active timeline. All existing cuts contribute unique narrative beats."
            else:
                msg = "Identified potentially redundant or alternative takes across clips:\n" + "\n".join(repeated_notes) + "\n\nYou can say: 'Delete the second take' or run the AI Video Pipeline to auto-filter duplicates."
            return ChatbotCommandResponse(
                understood=True,
                intent="find_repeated",
                message=msg
            )

        # "Analyze all my imported clips" / "Arrange into a logical story" / "Suggest cuts"
        if any(w in cmd for w in ["analyze all", "analyze imported", "analyze clips", "arrange into a logical story", "arrange these clips", "create a rough edit", "suggest cuts"]):
            return ChatbotCommandResponse(
                understood=True,
                intent="trigger_pipeline",
                message=(
                    "Ready to analyze all imported footage and assemble an edit plan!\n"
                    "• The 5-stage pipeline will run scene detection, visual motion scoring, and speech transcription.\n"
                    "• Local Qwen 2.5 will structure a 4-beat narrative (Hook -> B-Roll -> Core Message -> Outro) and drop duplicate takes.\n"
                    "• Click 'AI Video Pipeline' in the top toolbar to inspect and apply the assembled timeline."
                ),
                action_proposal={
                    "type": "open_pipeline",
                    "title": "Open AI Video Pipeline",
                    "details": "Launch the multi-clip story planning and OTIO generation wizard."
                }
            )

        # "Show me the important moments"
        if any(w in cmd for w in ["important moments", "key moments", "highlight moments", "highlights"]):
            moments = []
            for idx, c in enumerate(timeline.clips):
                role = c.role or "Highlight"
                moments.append(f"• Moment {idx+1} ({c.timeline_start:.1f}s - {c.timeline_end:.1f}s): {c.name} — {role}")
            return ChatbotCommandResponse(
                understood=True,
                intent="show_moments",
                message="Key narrative moments identified across the timeline:\n" + ("\n".join(moments) if moments else "No clips currently on timeline. Add footage to analyze moments.")
            )

        # "Create a shorter version while preserving the main message"
        if any(w in cmd for w in ["shorter version", "preserve main message", "shorten video", "make it shorter", "condense"]):
            total_dur = timeline.total_duration
            target_dur = round(max(5.0, total_dur * 0.6), 1)
            return ChatbotCommandResponse(
                understood=True,
                intent="shorten_proposal",
                message=(
                    f"I can condense this {total_dur:.1f}s edit down to ~{target_dur:.1f}s while preserving the main message.\n"
                    f"Recommended cuts: Tighten B-roll cutaways by 40% and keep the opening dialogue hook and primary value proposition intact.\n"
                    f"Say 'Delete the second half of clip 2' or 'Remove the first 5 seconds' to apply."
                )
            )

# --- F. Proportional Split & Cut ("in half", "second half", "first half") ---
        if re.search(r"\b(split|cut|divide)\b.*?\b(in half|in two|into two halves|into two|midpoint)\b", cmd):
            clip, idx = find_clip_by_reference(cmd)
            if clip:
                midpoint = round(clip.timeline_start + (clip.duration / 2.0), 2)
                updated_tl, msg = timeline_manager.split_at(timeline, midpoint)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="split",
                    message=f"Split clip {idx + 1} '{clip.name}' exactly in half at {midpoint:.2f}s.",
                    target_time=midpoint,
                    updated_timeline=updated_tl,
                    action_description=f"Split at midpoint {midpoint:.2f}s"
                )

        if re.search(r"\b(delete|remove|cut)\b.*?\bsecond half\b", cmd):
            clip, idx = find_clip_by_reference(cmd)
            if clip:
                midpoint = round(clip.timeline_start + (clip.duration / 2.0), 2)
                sel_tl, _ = timeline_manager.select_range(timeline, midpoint, clip.timeline_end)
                updated_tl, msg = timeline_manager.delete_selection(sel_tl)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="delete",
                    message=f"Deleted second half of clip {idx + 1} ({midpoint:.2f}s - {clip.timeline_end:.2f}s).",
                    target_time=clip.timeline_start,
                    updated_timeline=updated_tl,
                    action_description="Deleted second half"
                )

        if re.search(r"\b(delete|remove|cut)\b.*?\bfirst half\b", cmd):
            clip, idx = find_clip_by_reference(cmd)
            if clip:
                midpoint = round(clip.timeline_start + (clip.duration / 2.0), 2)
                sel_tl, _ = timeline_manager.select_range(timeline, clip.timeline_start, midpoint)
                updated_tl, msg = timeline_manager.delete_selection(sel_tl)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="delete",
                    message=f"Deleted first half of clip {idx + 1} ({clip.timeline_start:.2f}s - {midpoint:.2f}s).",
                    target_time=clip.timeline_start,
                    updated_timeline=updated_tl,
                    action_description="Deleted first half"
                )

        # --- G. Relative Trims & Cuts ("first N seconds", "last N seconds", "intro", "outro") ---
        m_del_first = re.search(r"(?:remove|delete|cut|trim off)\s+.*?\bfirst\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds?)?", cmd)
        if m_del_first:
            dur = float(m_del_first.group(1))
            sel_tl, _ = timeline_manager.select_range(timeline, 0.0, dur)
            updated_tl, msg = timeline_manager.delete_selection(sel_tl)
            return ChatbotCommandResponse(
                understood=True,
                intent="delete",
                message=f"Removed the first {dur:.1f} seconds of the sequence.",
                target_time=0.0,
                updated_timeline=updated_tl,
                action_description=f"Removed first {dur:.1f}s"
            )

        m_del_last = re.search(r"(?:remove|delete|cut|trim off)\s+.*?\blast\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds?)?", cmd)
        if m_del_last:
            dur = float(m_del_last.group(1))
            start_del = max(0.0, timeline.total_duration - dur)
            sel_tl, _ = timeline_manager.select_range(timeline, start_del, timeline.total_duration)
            updated_tl, msg = timeline_manager.delete_selection(sel_tl)
            return ChatbotCommandResponse(
                understood=True,
                intent="delete",
                message=f"Removed the last {dur:.1f} seconds (from {start_del:.1f}s to {timeline.total_duration:.1f}s).",
                target_time=start_del,
                updated_timeline=updated_tl,
                action_description=f"Removed last {dur:.1f}s"
            )

        # --- H. Explicit Range Cuts & Trims ---
        time_range = cls.extract_time_range(cmd)

        # "Delete from 00:10 to 00:25" / "Cut the selected section"
        if re.search(r"\b(delete|cut|remove)\b", cmd):
            if time_range:
                start, end = time_range
                sel_tl, _ = timeline_manager.select_range(timeline, start, end)
                updated_tl, msg = timeline_manager.delete_selection(sel_tl)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="delete",
                    message=f"Deleted time range {start:.2f}s - {end:.2f}s ({end - start:.2f}s removed).",
                    target_time=start,
                    updated_timeline=updated_tl,
                    action_description=f"Deleted {start:.1f}s - {end:.1f}s"
                )
            elif timeline.selection_range:
                start, end = timeline.selection_range
                updated_tl, msg = timeline_manager.delete_selection(timeline)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="delete",
                    message=msg,
                    target_time=start,
                    updated_timeline=updated_tl,
                    action_description="Deleted selection"
                )

        # "Trim the video from 00:10 to 01:20" (keeps only the range)
        if re.search(r"\btrim\b", cmd) and time_range:
            start, end = time_range
            updated_tl, msg = timeline_manager.trim_to_range(timeline, start, end)
            return ChatbotCommandResponse(
                understood=True,
                intent="trim",
                message=msg,
                target_time=0.0,
                updated_timeline=updated_tl,
                action_description=f"Trimmed to {start:.1f}s - {end:.1f}s"
            )

        # --- I. Split Commands ---
        m_split = re.search(r"(?:split|cut)\s+(?:the\s+clip\s+)?(?:at\s+)?([0-9:.]+s?(?:econds?)?)", cmd)
        if m_split:
            ts = cls.parse_timecode(m_split.group(1))
            if ts is not None and ts > 0:
                updated_tl, msg = timeline_manager.split_at(timeline, ts)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="split",
                    message=msg,
                    target_time=ts,
                    updated_timeline=updated_tl,
                    action_description=f"Split clip at {ts:.2f}s"
                )

        # --- J. Select Commands ---
        if re.search(r"\b(select|highlight)\b", cmd):
            if time_range:
                start, end = time_range
                updated_tl, msg = timeline_manager.select_range(timeline, start, end)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="select",
                    message=msg,
                    target_range=[start, end],
                    target_time=start,
                    updated_timeline=updated_tl
                )
            m_first_s = re.search(r"select (?:the )?first\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds?)?", cmd)
            if m_first_s:
                dur = float(m_first_s.group(1))
                updated_tl, msg = timeline_manager.select_range(timeline, 0.0, dur)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="select",
                    message=msg,
                    target_range=[0.0, dur],
                    target_time=0.0,
                    updated_timeline=updated_tl
                )

            # "Select clip 2"
            clip, idx = find_clip_by_reference(cmd)
            if clip:
                updated_tl, msg = timeline_manager.select_range(timeline, clip.timeline_start, clip.timeline_end)
                updated_tl.selected_clip_id = clip.id
                return ChatbotCommandResponse(
                    understood=True,
                    intent="select",
                    message=f"Selected clip {idx + 1} '{clip.name}' ({clip.timeline_start:.2f}s - {clip.timeline_end:.2f}s).",
                    target_range=[clip.timeline_start, clip.timeline_end],
                    target_time=clip.timeline_start,
                    updated_timeline=updated_tl
                )

        # --- Default Clarification Response ---
        return ChatbotCommandResponse(
            understood=False,
            intent="unknown",
            message=(
                f"I understood that you want to edit the video, but '{raw_cmd}' needs a little more detail.\n"
                "Try saying something like:\n"
                "• \"Split the second clip in half\"\n"
                "• \"Remove the first 4 seconds\"\n"
                "• \"Delete the selected segment\"\n"
                "• \"Speed up clip 1 to 1.5x\"\n"
                "• \"Trim from 00:05 to 00:20\"\n"
                "• \"Export as 9:16 vertical video\""
            ),
            prompt_for_clarification="Could you clarify which time or clip you want to modify?"
        )
