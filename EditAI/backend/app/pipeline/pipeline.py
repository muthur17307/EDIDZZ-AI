# app/pipeline/pipeline.py
import json
from pathlib import Path
from typing import Any

from app.pipeline.ingest import register_clips
from app.pipeline.context_builder import build_story_context
from app.pipeline.model_adapter import analyze_clip, plan_global_edit
from app.pipeline.export_otio import export_timeline
from app.pipeline.validate import validate_edit_plan


def save_json(path: Path, data: Any) -> None:
    """Save data as readable UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def validate_clips(clips: list[dict]) -> dict[str, dict]:
    """Validate registered media and build a clip-ID lookup."""
    if not clips:
        raise ValueError(
            "No video clips found. Upload at least one clip into the source folder."
        )

    by_id: dict[str, dict] = {}
    for clip in clips:
        clip_id = clip.get("clip_id")
        if not clip_id:
            raise ValueError("A registered clip is missing its clip_id.")
        if clip_id in by_id:
            raise ValueError(f"Duplicate clip ID found: {clip_id}")

        try:
            duration = float(clip["duration"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(
                f"Clip {clip_id} has a missing or invalid duration."
            ) from None

        if duration <= 0:
            raise ValueError(f"Clip {clip_id} has an invalid duration.")
        if not clip.get("path"):
            raise ValueError(f"Clip {clip_id} is missing its source path.")

        by_id[clip_id] = {
            **clip,
            "duration": duration,
        }

    return by_id


def run_pipeline(project_dir: Path, brief: str) -> dict:
    """
    Run the complete video editing pipeline:
    1. Register source clips.
    2. Analyze clips individually.
    3. Ask Qwen / Offline AI model to create a global story plan.
    4. Validate the plan against source clips.
    5. Export an editable OTIO timeline.
    """
    project_dir = Path(project_dir)
    source_dir = project_dir / "source"
    analysis_dir = project_dir / "analysis"

    project_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    if not brief or not brief.strip():
        raise ValueError("Please provide a client brief before running the pipeline.")

    # A. Register original uploaded media
    clips = register_clips(source_dir)
    if not isinstance(clips, list):
        raise ValueError("register_clips() must return a list of clip dictionaries.")

    by_id = validate_clips(clips)
    save_json(project_dir / "media_manifest.json", list(by_id.values()))

    # B. Analyze each clip independently
    analyses = []
    for clip_id, clip in by_id.items():
        result = analyze_clip(
            video_path=clip["path"],
            clip_id=clip_id,
            brief=brief.strip(),
        )

        result["clip_id"] = clip_id
        result["duration"] = clip["duration"]

        save_json(analysis_dir / f"{clip_id}.json", result)
        analyses.append(result)

    if not analyses:
        raise ValueError("No clip analyses were generated.")

    # C. Save context shared across all clips
    context = build_story_context(brief=brief.strip(), clips=analyses)
    save_json(project_dir / "story_context.json", context)

    # D. Ask the offline model (Qwen 2.5 / Heuristic) for one global edit plan
    plan = plan_global_edit(
        brief=brief.strip(),
        analyses=analyses,
    )

    if not isinstance(plan, dict) or not isinstance(plan.get("ordered_segments"), list):
        raise ValueError("The global planner must return a JSON object with 'ordered_segments'.")

    save_json(project_dir / "edit_plan_raw.json", plan)

    # E. Validate proposed segments using validate_edit_plan
    val_result = validate_edit_plan(list(by_id.values()), plan)
    accepted = val_result["valid_segments"]
    review = val_result["review_items"]
    errors = val_result["errors"]
    warnings = val_result["warnings"]

    if not accepted:
        save_json(
            project_dir / "validation_report.json",
            {
                "status": "failed",
                "errors": errors,
                "warnings": warnings,
                "accepted_segments": 0,
                "review_items": review,
            },
        )
        raise ValueError(f"No valid segments remain after validation: {'; '.join(errors)}")

    final_plan = {
        **plan,
        "ordered_segments": accepted,
        "review_items": review,
        "validation_warnings": warnings,
    }
    save_json(project_dir / "edit_plan.json", final_plan)

    save_json(
        project_dir / "validation_report.json",
        {
            "status": "passed_with_review" if review else "passed",
            "total_proposed_segments": len(plan["ordered_segments"]),
            "accepted_segments": len(accepted),
            "review_item_count": len(review),
            "review_items": review,
            "warnings": warnings,
        },
    )

    # F. Export an editable timeline (OTIO)
    timeline_path = project_dir / "timeline.otio"
    export_timeline(
        list(by_id.values()),
        final_plan,
        timeline_path,
    )

    if not timeline_path.is_file():
        raise RuntimeError(f"Timeline export failed to create {timeline_path}.")

    return {
        "status": "completed",
        "timeline": str(timeline_path.resolve()),
        "edit_plan": str((project_dir / "edit_plan.json").resolve()),
        "validation_report": str((project_dir / "validation_report.json").resolve()),
        "selected_segments": len(accepted),
        "review_items": len(review),
        "story_summary": final_plan.get("story_summary", ""),
        "ordered_segments": accepted,
        "review_segments": review,
        "warnings": warnings,
    }

