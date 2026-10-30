from pathlib import Path

target = Path("EditAI/frontend/src/App.jsx")
text = target.read_text(encoding="utf-8")

old_line = "  const selectedClip = timeline.clips.find((c) => c.id === timeline.selected_clip_id) || null;"
new_line = "  const selectedClip = (timeline?.clips || []).find((c) => c.id === timeline?.selected_clip_id) || null;"

assert old_line in text, "old_line not found"
text = text.replace(old_line, new_line, 1)

target.write_text(text, encoding="utf-8")
print("App.jsx selectedClip patched successfully!")

