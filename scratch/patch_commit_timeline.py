from pathlib import Path

target = Path("EditAI/frontend/src/components/MultiVideoAssemblyStage.jsx")
text = target.read_text(encoding="utf-8")

old_commit = """  const handleCommitToTimeline = () => {
    if (!pipelineResult || !pipelineResult.timeline_state) return;
    onApplyAssembly(pipelineResult);
    onClose();
  };"""

new_commit = """  const handleCommitToTimeline = () => {
    if (!pipelineResult) return;
    onApplyAssembly(pipelineResult);
    onClose();
  };"""

assert old_commit in text, "old_commit not found"
text = text.replace(old_commit, new_commit, 1)

target.write_text(text, encoding="utf-8")
print("MultiVideoAssemblyStage handleCommitToTimeline patched successfully!")

