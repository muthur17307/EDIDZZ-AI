from pathlib import Path

target = Path("EditAI/frontend/src/App.jsx")
text = target.read_text(encoding="utf-8")

old_code = """  // Handle Multi-Video AI Assembly application
  const handleApplyAssembly = (result) => {
    setAssemblyResult(result);
    setTimeline(result.timeline_state);
    setSubtitles(result.subtitles || []);

    if (result.timeline_state && result.timeline_state.clips.length > 0) {
      const firstClip = result.timeline_state.clips[0];
      setVideoSrc(firstClip.stream_url || '');
      setVideoMetadata({
        filename: `Assembled Production (${result.style})`,
        duration: result.total_duration,
        width: 1920,
        height: 1080,
        fps: 25.0,
        has_audio: true,
        filepath: firstClip.source_file,
      });
    }

    setCurrentTime(0.0);
    setActiveRightTab('inspector');
    setIsEdited(true);
    const cutCount = (result.segments || result.ordered_segments || result.timeline_state?.clips || []).length;
    addChatMessage(
      'assistant',
      `✨ Assembled ${cutCount} sequential cuts into timeline using "${result.style || 'narrative'}".\\n• Audio and subtitles synchronized across all cuts.\\n• Sequence mounted as editable clips on the timeline.\\n• You can now scrub, split, trim, delete, reorder, or refine via natural language chatbot.`
    );
  };"""

new_code = """  // Handle Multi-Video AI Assembly application
  const handleApplyAssembly = (result) => {
    if (!result) return;
    setAssemblyResult(result);

    const tl = result.timeline_state || {
      clips: [],
      total_duration: result.total_duration || 0,
      selected_clip_id: null,
      selection_range: null,
      subtitles: result.subtitles || [],
      playhead_time: 0.0,
    };
    setTimeline(tl);
    setSubtitles(result.subtitles || tl.subtitles || []);

    if (tl.clips && tl.clips.length > 0) {
      const firstClip = tl.clips[0];
      setVideoSrc(firstClip.stream_url || '');
      setVideoMetadata({
        filename: `Assembled Production (${result.style || 'narrative'})`,
        duration: tl.total_duration || result.total_duration || 10.0,
        width: 1920,
        height: 1080,
        fps: 25.0,
        has_audio: true,
        filepath: firstClip.source_file || '',
      });
    }

    setCurrentTime(0.0);
    setActiveRightTab('inspector');
    setIsEdited(true);
    const cutCount = (result.segments || result.ordered_segments || tl.clips || []).length;
    addChatMessage(
      'assistant',
      `✨ Assembled ${cutCount} sequential cuts into timeline using "${result.style || 'narrative'}".\\n• Audio and subtitles synchronized across all cuts.\\n• Sequence mounted as editable clips on the timeline.\\n• You can now scrub, split, trim, delete, reorder, or refine via natural language chatbot.`
    );
  };"""

assert old_code in text, "old_code not found in App.jsx"
text = text.replace(old_code, new_code, 1)

target.write_text(text, encoding="utf-8")
print("App.jsx handleApplyAssembly patched successfully!")

