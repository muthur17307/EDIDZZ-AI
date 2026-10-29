from pathlib import Path

target = Path("EditAI/frontend/src/App.jsx")
text = target.read_text(encoding="utf-8")

old_str = """    addChatMessage(
      'assistant',
      `✨ Assembled ${result.segments.length} sequential cuts into timeline using "${result.style}".\\n• Audio and subtitles synchronized across all cuts.\\n• Sequence mounted as editable clips on the timeline.\\n• You can now scrub, split, trim, delete, reorder, or refine via natural language chatbot.`
    );"""

new_str = """    const cutCount = (result.segments || result.ordered_segments || result.timeline_state?.clips || []).length;
    addChatMessage(
      'assistant',
      `✨ Assembled ${cutCount} sequential cuts into timeline using "${result.style || 'narrative'}".\\n• Audio and subtitles synchronized across all cuts.\\n• Sequence mounted as editable clips on the timeline.\\n• You can now scrub, split, trim, delete, reorder, or refine via natural language chatbot.`
    );"""

if old_str in text:
    text = text.replace(old_str, new_str, 1)
    target.write_text(text, encoding="utf-8")
    print("App.jsx patched successfully!")
else:
    print("old_str not found in App.jsx")

