
# app/context_builder.py

from typing import Any
from collections import defaultdict


def build_story_context(
    brief: str,
    clips: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Combine analyses from multiple clips into one story context.

    Expected clip structure:
    {
        "clip_id": "clip_001",
        "duration": 60.0,
        "segments": [
            {
                "start": 0.0,
                "end": 5.0,
                "transcript": "...",
                "visual_summary": "...",
                "story_role": "introduction",
                "quality": 0.9
            }
        ]
    }
    """

    all_segments = []
    clip_summaries = []
    role_groups = defaultdict(list)

    for clip in clips:
        clip_id = clip["clip_id"]
        duration = float(clip["duration"])

        clip_summaries.append({
            "clip_id": clip_id,
            "duration": duration,
            "filename": clip.get("filename", ""),
            "summary": clip.get("summary", ""),
        })

        for index, segment in enumerate(clip.get("segments", [])):
            start = float(segment["start"])
            end = float(segment["end"])

            item = {
                "segment_id": f"{clip_id}_seg_{index:04d}",
                "clip_id": clip_id,
                "start": start,
                "end": end,
                "transcript": segment.get("transcript", ""),
                "visual_summary": segment.get(
                    "visual_summary", ""
                ),
                "story_role": segment.get(
                    "story_role", "unknown"
                ),
                "quality": segment.get("quality"),
            }

            all_segments.append(item)
            role_groups[item["story_role"]].append(
                item["segment_id"]
            )

    # Stable source ordering is for reproducibility only.
    # It is NOT the final narrative order.
    all_segments.sort(
        key=lambda s: (s["clip_id"], s["start"])
    )

    return {
        "brief": brief,
        "clip_count": len(clip_summaries),
        "clips": clip_summaries,
        "segments": all_segments,
        "segments_by_story_role": dict(role_groups),
        "editorial_instructions": [
            "Treat all clips as one story.",
            "Do not assume upload order is story order.",
            "Compare statements across every source clip.",
            "Keep the clearest complete version of repeated information.",
            "Preserve unique facts, qualifications, and useful context.",
            "Use B-roll when it supports the spoken narrative.",
            "Keep uncertain removals in a review list.",
            "Return exact source clip IDs and source timestamps.",
        ],
    }


def build_planner_prompt(
    context: dict[str, Any],
) -> str:
    """
    Create the input prompt for the existing LLM.
    The caller must parse and validate the model's JSON response.
    """

    import json

    return f"""
You are an editorial planning assistant.

Create one coherent video edit from multiple source clips.

CLIENT BRIEF:
{context["brief"]}

CLIP AND SEGMENT ANALYSIS:
{json.dumps(context, ensure_ascii=False, indent=2)}

RULES:
1. Understand all clips together before selecting segments.
2. Choose a logical story order, not upload order.
3. Identify exact and semantic repetition across clips.
4. Prefer the clearest, most complete take.
5. Never remove unique information merely because wording is similar.
6. Preserve enough context for every statement to remain understandable.
7. Do not invent timestamps, clip IDs, or events.
8. Keep uncertain cuts in review_items.
9. Do not include source ranges outside their original clips.
10. Return JSON only, with this structure:

{{
  "story_summary": "...",
  "ordered_segments": [
    {{
      "clip_id": "clip_001",
      "start": 0.0,
      "end": 5.0,
      "decision": "keep",
      "reason": "...",
      "story_role": "introduction"
    }}
  ],
  "review_items": [
    {{
      "clip_id": "clip_002",
      "start": 10.0,
      "end": 14.0,
      "reason": "Potentially repetitive; verify unique information"
    }}
  ]
}}
""".strip()
