
# app/pipeline.py

import json
from pathlib import Path
from typing import Any

from app.ingest import register_clips
from app.model_adapter import analyze_clip, plan_global_edit
from app.export_otio import export_timeline


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
    3. Ask Qwen to create a global story plan.
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

    # A. Register original uploaded media.
    clips = register_clips(source_dir)

    if not isinstance(clips, list):
        raise ValueError("register_clips() must return a list of clip dictionaries.")

    by_id = validate_clips(clips)

    # Keep the registered metadata authoritative.
    save_json(
        project_dir / "media_manifest.json",
        list(by_id.values()),
    )

    # B. Analyze each clip independently.
    analyses = []

    for clip_id, clip in by_id.items():
        result = analyze_clip(
            video_path=clip["path"],
            clip_id=clip_id,
            brief=brief.strip(),
        )

        if not isinstance(result, dict):
            raise ValueError(
                f"Clip analysis failed for {clip_id}: expected a dictionary."
            )

        # The real source ID and duration always take priority.
        result["clip_id"] = clip_id
        result["duration"] = clip["duration"]

        save_json(
            analysis_dir / f"{clip_id}.json",
            result,
        )

        analyses.append(result)

    if not analyses:
        raise ValueError("No clip analyses were generated.")

    # C. Save context shared across all clips.
    context = {
        "brief": brief.strip(),
        "clips": analyses,
    }

    save_json(
        project_dir / "story_context.json",
        context,
    )

    # Ask the locally running Qwen model for one global edit plan.
    plan = plan_global_edit(
        brief=brief.strip(),
        analyses=analyses,
    )

    if not isinstance(plan, dict):
        raise ValueError("The global planner must return a JSON object.")

    if not isinstance(plan.get("ordered_segments"), list):
        raise ValueError(
            "The model response is missing a valid ordered_segments list."
        )

    # Save the unmodified model output for debugging and review.
    save_json(
        project_dir / "edit_plan_raw.json",
        plan,
    )

    # D. Validate all proposed segments before timeline export.
    review_items = plan.get("review_items", [])

    if not isinstance(review_items, list):
        review_items = [{
            "reason": "Model returned invalid review_items; manual review required."
        }]

    accepted = []
    review = list(review_items)

    for item in plan["ordered_segments"]:
        if not isinstance(item, dict):
            review.append({
                "item": item,
                "reason": "Segment must be a JSON object.",
            })
            continue

        decision = item.get("decision")

        # Only explicitly approved "keep" segments can enter the timeline.
        if decision != "keep":
            continue

        clip_id = item.get("clip_id")
        clip = by_id.get(clip_id)

        if clip is None:
            review.append({
                "item": item,
                "reason": "Unknown source clip ID.",
            })
            continue

        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            review.append({
                "item": item,
                "reason": "Missing or invalid start/end timestamps.",
            })
            continue

        duration = clip["duration"]

        if start < 0 or end <= start or end > duration + 0.05:
            review.append({
                "item": item,
                "reason": (
                    f"Invalid time range: start={start}, end={end}, "
                    f"source duration={duration}."
                ),
            })
            continue

        # Clamp tiny floating-point overflows to the real source duration.
        validated_item = {
            **item,
            "clip_id": clip_id,
            "start": start,
            "end": min(end, duration),
        }

        accepted.append(validated_item)

    if not accepted:
        save_json(
            project_dir / "validation_report.json",
            {
                "status": "failed",
                "accepted_segments": 0,
                "review_items": review,
            },
        )

        raise ValueError(
            "No valid segments remain after validation. "
            "Check edit_plan_raw.json and the analysis files."
        )

    # Store only validated segments in the final edit plan.
    final_plan = {
        **plan,
        "ordered_segments": accepted,
        "review_items": review,
    }

    save_json(
        project_dir / "edit_plan.json",
        final_plan,
    )

    save_json(
        project_dir / "validation_report.json",
        {
            "status": "passed_with_review" if review else "passed",
            "total_proposed_segments": len(plan["ordered_segments"]),
            "accepted_segments": len(accepted),
            "review_item_count": len(review),
            "review_items": review,
        },
    )

    # E. Export an editable timeline, not a flattened video.
    timeline_path = project_dir / "timeline.otio"

    export_timeline(
        list(by_id.values()),
        final_plan,
        timeline_path,
    )

    # Confirm that the exporter actually created the file.
    if not timeline_path.is_file():
        raise RuntimeError(
            f"Timeline export returned without creating {timeline_path}."
        )

    # F. Return information for the FastAPI backend/frontend.
    return {
        "status": "completed",
        "timeline": str(timeline_path.resolve()),
        "edit_plan": str((project_dir / "edit_plan.json").resolve()),
        "validation_report": str(
            (project_dir / "validation_report.json").resolve()
        ),
        "selected_segments": len(accepted),
        "review_items": len(review),
        "story_summary": final_plan.get("story_summary", ""),
        "ordered_segments": accepted,
        "review_segments": review,
        "warnings": [],
    }
