from pathlib import Path

target = Path("EditAI/backend/app/services/timeline_manager.py")
text = target.read_text(encoding="utf-8")

# Update signature
old_sig = "def delete_range(self, timeline: TimelineState, start_time: float, end_time: float, is_cut: bool = False) -> Tuple[TimelineState, str]:"
new_sig = "def delete_range(self, timeline: TimelineState, start_time: float, end_time: float, is_cut: bool = False, save_history: bool = True) -> Tuple[TimelineState, str]:"
assert old_sig in text, "old_sig not found"
text = text.replace(old_sig, new_sig, 1)

# Update save_state conditional
old_save = """        op_name = "Cut" if is_cut else "Delete"
        self.save_state(timeline, f"{op_name} section {start_time:.2f}s to {end_time:.2f}s")"""

new_save = """        if save_history:
            op_name = "Cut" if is_cut else "Delete"
            self.save_state(timeline, f"{op_name} section {start_time:.2f}s to {end_time:.2f}s")"""
assert old_save in text, "old_save not found"
text = text.replace(old_save, new_save, 1)

# Update trim_timeline calls
old_trim_calls = """        # Step 1: Delete after keep_end if needed
        state = copy.deepcopy(timeline)
        if keep_end < state.total_duration:
            state, _ = self.delete_range(state, keep_end, state.total_duration)

        # Step 2: Delete before keep_start if needed
        if keep_start > 0:
            state, _ = self.delete_range(state, 0.0, keep_start)"""

new_trim_calls = """        # Step 1: Delete after keep_end if needed
        state = copy.deepcopy(timeline)
        if keep_end < state.total_duration:
            state, _ = self.delete_range(state, keep_end, state.total_duration, save_history=False)

        # Step 2: Delete before keep_start if needed
        if keep_start > 0:
            state, _ = self.delete_range(state, 0.0, keep_start, save_history=False)"""
assert old_trim_calls in text, "old_trim_calls not found"
text = text.replace(old_trim_calls, new_trim_calls, 1)

target.write_text(text, encoding="utf-8")
print("timeline_manager.py successfully patched!")

