import copy
import uuid
from typing import List, Optional, Tuple, Dict, Any

from app.models.schemas import TimelineState, Clip, SubtitleItem, MediaMetadata, EditActionRecord

class TimelineManager:
    def __init__(self):
        # In-memory session history stacks for undo/redo
        self.history_stack: List[Tuple[TimelineState, str]] = []
        self.redo_stack: List[Tuple[TimelineState, str]] = []
        self.clipboard: Optional[List[Clip]] = None

    def create_initial_timeline(self, media: MediaMetadata) -> TimelineState:
        """Initializes timeline with a single full-length clip from uploaded video."""
        clip_id = f"clip_{uuid.uuid4().hex[:8]}"
        initial_clip = Clip(
            id=clip_id,
            source_file=media.filepath,
            source_filename=media.filename,
            source_start=0.0,
            source_end=media.duration,
            timeline_start=0.0,
            timeline_end=media.duration,
            duration=media.duration,
            name=f"{media.filename} (Original)",
            speed=1.0,
            volume=1.0,
            color="#3b82f6"
        )
        timeline = TimelineState(
            clips=[initial_clip],
            total_duration=media.duration,
            selected_clip_id=clip_id,
            selection_range=None,
            subtitles=[],
            playhead_time=0.0
        )
        self.history_stack.clear()
        self.redo_stack.clear()
        return timeline

    def save_state(self, current_timeline: TimelineState, action_desc: str):
        """Pushes current state onto undo history before applying modification."""
        self.history_stack.append((copy.deepcopy(current_timeline), action_desc))
        self.redo_stack.clear()
        # Keep maximum 50 history entries
        if len(self.history_stack) > 50:
            self.history_stack.pop(0)

    def undo(self, current_timeline: TimelineState) -> Tuple[TimelineState, str]:
        """Reverts to the previous timeline state."""
        if not self.history_stack:
            return current_timeline, "Nothing to undo."

        prev_state, action_desc = self.history_stack.pop()
        self.redo_stack.append((copy.deepcopy(current_timeline), action_desc))
        return prev_state, f"Undid: {action_desc}"

    def redo(self, current_timeline: TimelineState) -> Tuple[TimelineState, str]:
        """Restores the previously undone timeline state."""
        if not self.redo_stack:
            return current_timeline, "Nothing to redo."

        next_state, action_desc = self.redo_stack.pop()
        self.history_stack.append((copy.deepcopy(current_timeline), action_desc))
        return next_state, f"Redid: {action_desc}"

    @staticmethod
    def recalculate_timeline_offsets(clips: List[Clip]) -> float:
        """Recalculates timeline_start and timeline_end for all sequential clips."""
        current_time = 0.0
        for clip in clips:
            clip.timeline_start = round(current_time, 3)
            clip.timeline_end = round(current_time + clip.duration, 3)
            current_time = clip.timeline_end
        return round(current_time, 3)

    def split_clip(self, timeline: TimelineState, split_time: float) -> Tuple[TimelineState, str]:
        """
        Splits the clip located at split_time into two separate clips.
        """
        if split_time <= 0 or split_time >= timeline.total_duration:
            return timeline, f"Split timestamp {split_time:.2f}s is out of range (0.00s - {timeline.total_duration:.2f}s)."

        self.save_state(timeline, f"Split at {split_time:.2f}s")
        new_timeline = copy.deepcopy(timeline)

        target_index = -1
        target_clip = None
        for idx, clip in enumerate(new_timeline.clips):
            if clip.timeline_start < split_time < clip.timeline_end:
                target_index = idx
                target_clip = clip
                break

        if target_clip is None or target_index == -1:
            return timeline, f"No clip spans timestamp {split_time:.2f}s or split point is exactly on a boundary."

        # Calculate offset into source
        offset_into_clip = split_time - target_clip.timeline_start
        source_split = target_clip.source_start + (offset_into_clip * target_clip.speed)

        # Clip A (left portion)
        clip_a = copy.deepcopy(target_clip)
        clip_a.id = f"clip_{uuid.uuid4().hex[:8]}"
        clip_a.source_end = round(source_split, 3)
        clip_a.duration = round(source_split - target_clip.source_start, 3)
        clip_a.name = f"{target_clip.name} (Part 1)"
        clip_a.color = "#3b82f6"

        # Clip B (right portion)
        clip_b = copy.deepcopy(target_clip)
        clip_b.id = f"clip_{uuid.uuid4().hex[:8]}"
        clip_b.source_start = round(source_split, 3)
        clip_b.duration = round(target_clip.source_end - source_split, 3)
        clip_b.name = f"{target_clip.name} (Part 2)"
        clip_b.color = "#6366f1"

        # Replace target with clip_a and clip_b
        new_clips = new_timeline.clips[:target_index] + [clip_a, clip_b] + new_timeline.clips[target_index + 1:]
        new_timeline.clips = new_clips
        new_timeline.total_duration = self.recalculate_timeline_offsets(new_timeline.clips)
        new_timeline.selected_clip_id = clip_b.id
        new_timeline.playhead_time = split_time

        return new_timeline, f"Successfully split clip at {split_time:.2f}s into two clips."

    def select_range(self, timeline: TimelineState, start_time: float, end_time: float) -> Tuple[TimelineState, str]:
        """Sets active selection range on timeline."""
        start_time = max(0.0, round(start_time, 2))
        end_time = min(timeline.total_duration, round(end_time, 2))

        if start_time >= end_time:
            return timeline, f"Invalid selection range [{start_time:.2f}s - {end_time:.2f}s]."

        new_timeline = copy.deepcopy(timeline)
        new_timeline.selection_range = (start_time, end_time)

        # If a single clip falls within this range, highlight it
        matched_clip = None
        for clip in new_timeline.clips:
            if abs(clip.timeline_start - start_time) < 0.2 and abs(clip.timeline_end - end_time) < 0.2:
                matched_clip = clip.id
                break
        new_timeline.selected_clip_id = matched_clip
        new_timeline.playhead_time = start_time

        return new_timeline, f"Selected range from {start_time:.2f}s to {end_time:.2f}s (duration: {end_time - start_time:.2f}s)."

    def delete_selected_clip(self, timeline: TimelineState) -> Tuple[TimelineState, str]:
        """Deletes the currently selected clip or selected range from the timeline."""
        if timeline.selection_range:
            start, end = timeline.selection_range
            return self.delete_range(timeline, start, end)

        if not timeline.selected_clip_id:
            return timeline, "No clip or range is currently selected to delete."

        target_clip = next((c for c in timeline.clips if c.id == timeline.selected_clip_id), None)
        if not target_clip:
            return timeline, "Selected clip not found."

        if len(timeline.clips) <= 1:
            return timeline, "Cannot delete the only remaining clip on timeline."

        self.save_state(timeline, f"Delete clip '{target_clip.name}'")
        new_timeline = copy.deepcopy(timeline)

        cut_start = target_clip.timeline_start
        cut_duration = target_clip.duration

        new_timeline.clips = [c for c in new_timeline.clips if c.id != target_clip.id]
        new_timeline.total_duration = self.recalculate_timeline_offsets(new_timeline.clips)
        new_timeline.selected_clip_id = new_timeline.clips[0].id if new_timeline.clips else None
        new_timeline.selection_range = None
        new_timeline.playhead_time = min(cut_start, new_timeline.total_duration)

        # Sync subtitles
        new_timeline.subtitles = self.adjust_subtitles_after_cut(new_timeline.subtitles, cut_start, cut_start + cut_duration)

        return new_timeline, f"Deleted clip '{target_clip.name}' ({cut_duration:.2f}s removed)."

    def delete_selection(self, timeline: TimelineState) -> Tuple[TimelineState, str]:
        """Alias for delete_selected_clip."""
        return self.delete_selected_clip(timeline)

    def split_at(self, timeline: TimelineState, split_time: float) -> Tuple[TimelineState, str]:
        """Alias for split_clip."""
        return self.split_clip(timeline, split_time)

    def cut_selection(self, timeline: TimelineState) -> Tuple[TimelineState, str]:
        """
        Removes selected section, copies it to clipboard/undo history, and ripples timeline.
        """
        if timeline.selection_range:
            start, end = timeline.selection_range
            return self.delete_range(timeline, start, end, is_cut=True)

        if timeline.selected_clip_id:
            return self.delete_selected_clip(timeline)

        return timeline, "No section or clip selected to cut."

    def delete_range(self, timeline: TimelineState, start_time: float, end_time: float, is_cut: bool = False, save_history: bool = True) -> Tuple[TimelineState, str]:
        """
        Deletes or cuts a time range [start_time, end_time] across clips, rippling following clips.
        """
        start_time = max(0.0, round(start_time, 2))
        end_time = min(timeline.total_duration, round(end_time, 2))
        dur_to_remove = round(end_time - start_time, 2)

        if dur_to_remove <= 0:
            return timeline, f"Invalid range [{start_time:.2f}s - {end_time:.2f}s]."

        if save_history:
            op_name = "Cut" if is_cut else "Delete"
            self.save_state(timeline, f"{op_name} section {start_time:.2f}s to {end_time:.2f}s")
        new_timeline = copy.deepcopy(timeline)

        new_clips: List[Clip] = []

        for clip in new_timeline.clips:
            # Case 1: clip ends before cut range -> keep untouched
            if clip.timeline_end <= start_time:
                new_clips.append(clip)
            # Case 2: clip starts after cut range -> keep, will be offset later
            elif clip.timeline_start >= end_time:
                new_clips.append(clip)
            # Case 3: clip is completely inside cut range -> omit (deleted)
            elif clip.timeline_start >= start_time and clip.timeline_end <= end_time:
                continue
            # Case 4: cut range falls entirely inside this single clip -> split into 2 parts
            elif clip.timeline_start < start_time and clip.timeline_end > end_time:
                # Part A (before start_time)
                left_dur = start_time - clip.timeline_start
                source_left_end = clip.source_start + left_dur * clip.speed
                clip_left = copy.deepcopy(clip)
                clip_left.id = f"clip_{uuid.uuid4().hex[:8]}"
                clip_left.source_end = round(source_left_end, 3)
                clip_left.duration = round(left_dur, 3)
                new_clips.append(clip_left)

                # Part B (after end_time)
                right_skip = end_time - clip.timeline_start
                source_right_start = clip.source_start + right_skip * clip.speed
                clip_right = copy.deepcopy(clip)
                clip_right.id = f"clip_{uuid.uuid4().hex[:8]}"
                clip_right.source_start = round(source_right_start, 3)
                clip_right.duration = round(clip.source_end - source_right_start, 3)
                new_clips.append(clip_right)
            # Case 5: clip overlaps start of cut range -> trim right end
            elif clip.timeline_start < start_time and clip.timeline_end > start_time:
                kept_dur = start_time - clip.timeline_start
                clip.source_end = round(clip.source_start + kept_dur * clip.speed, 3)
                clip.duration = round(kept_dur, 3)
                new_clips.append(clip)
            # Case 6: clip overlaps end of cut range -> trim left start
            elif clip.timeline_start < end_time and clip.timeline_end > end_time:
                cut_amount = end_time - clip.timeline_start
                clip.source_start = round(clip.source_start + cut_amount * clip.speed, 3)
                clip.duration = round(clip.duration - cut_amount, 3)
                new_clips.append(clip)

        if not new_clips:
            return timeline, "Operation would remove all video clips. Action aborted."

        new_timeline.clips = new_clips
        new_timeline.total_duration = self.recalculate_timeline_offsets(new_timeline.clips)
        new_timeline.selection_range = None
        new_timeline.selected_clip_id = new_timeline.clips[0].id if new_timeline.clips else None
        new_timeline.playhead_time = min(start_time, new_timeline.total_duration)

        # Sync subtitles
        new_timeline.subtitles = self.adjust_subtitles_after_cut(new_timeline.subtitles, start_time, end_time)

        action_word = "Cut" if is_cut else "Deleted"
        return new_timeline, f"{action_word} segment from {start_time:.2f}s to {end_time:.2f}s ({dur_to_remove:.2f}s removed)."

    def trim_timeline(self, timeline: TimelineState, keep_start: float, keep_end: float) -> Tuple[TimelineState, str]:
        """
        Trims the video to only keep the interval [keep_start, keep_end], discarding the rest.
        """
        keep_start = max(0.0, round(keep_start, 2))
        keep_end = min(timeline.total_duration, round(keep_end, 2))

        if keep_start >= keep_end:
            return timeline, f"Invalid trim range [{keep_start:.2f}s - {keep_end:.2f}s]."

        self.save_state(timeline, f"Trim video to {keep_start:.2f}s - {keep_end:.2f}s")

        # Step 1: Delete after keep_end if needed
        state = copy.deepcopy(timeline)
        if keep_end < state.total_duration:
            state, _ = self.delete_range(state, keep_end, state.total_duration, save_history=False)

        # Step 2: Delete before keep_start if needed
        if keep_start > 0:
            state, _ = self.delete_range(state, 0.0, keep_start, save_history=False)

        state.selection_range = None
        state.playhead_time = 0.0

        return state, f"Trimmed video to range {keep_start:.2f}s - {keep_end:.2f}s (new duration: {state.total_duration:.2f}s)."

    @staticmethod
    def adjust_subtitles_after_cut(subtitles: List[SubtitleItem], cut_start: float, cut_end: float) -> List[SubtitleItem]:
        """
        Ripples subtitles after a time range [cut_start, cut_end] is removed:
        - Drops subtitles completely inside the range.
        - Trims subtitles overlapping boundaries.
        - Shifts all subtitles occurring after cut_end earlier by (cut_end - cut_start).
        """
        cut_duration = cut_end - cut_start
        updated: List[SubtitleItem] = []

        for sub in subtitles:
            # Case 1: sub ends before cut -> unchanged
            if sub.end_time <= cut_start:
                updated.append(sub)
            # Case 2: sub starts after cut -> shifted forward
            elif sub.start_time >= cut_end:
                shifted = copy.deepcopy(sub)
                shifted.start_time = round(sub.start_time - cut_duration, 2)
                shifted.end_time = round(sub.end_time - cut_duration, 2)
                updated.append(shifted)
            # Case 3: sub completely inside cut -> deleted
            elif sub.start_time >= cut_start and sub.end_time <= cut_end:
                continue
            # Case 4: sub overlaps cut_start -> truncate end to cut_start
            elif sub.start_time < cut_start and sub.end_time > cut_start:
                trimmed = copy.deepcopy(sub)
                trimmed.end_time = cut_start
                if (trimmed.end_time - trimmed.start_time) >= 0.3:
                    updated.append(trimmed)
            # Case 5: sub overlaps cut_end -> shift and adjust start
            elif sub.start_time < cut_end and sub.end_time > cut_end:
                trimmed = copy.deepcopy(sub)
                trimmed.start_time = cut_start
                trimmed.end_time = round(sub.end_time - cut_duration, 2)
                if (trimmed.end_time - trimmed.start_time) >= 0.3:
                    updated.append(trimmed)

        # Re-number subtitles
        for idx, sub in enumerate(updated):
            sub.id = idx + 1

        return updated
