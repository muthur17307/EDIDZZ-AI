
# app/export_otio.py
from pathlib import Path
import opentimelineio as otio


def export_timeline(
    clips: list[dict],
    edit_plan: dict,
    output_path: Path,
) -> None:
    by_id = {clip["clip_id"]: clip for clip in clips}

    timeline = otio.schema.Timeline(name="AI Story Edit")
    track = otio.schema.Track(
        name="Main Video",
        kind=otio.schema.TrackKind.Video,
    )

    for item in edit_plan["ordered_segments"]:
        if item.get("decision") != "keep":
            continue

        clip_id = item["clip_id"]
        if clip_id not in by_id:
            raise ValueError(f"Unknown clip ID: {clip_id}")

        source = by_id[clip_id]
        start = float(item["start"])
        end = float(item["end"])

        if start < 0 or end <= start:
            raise ValueError(f"Invalid range: {item}")

        if end > source["duration"] + 0.05:
            raise ValueError(f"Range exceeds source duration: {item}")

        media_ref = otio.schema.ExternalReference(
            target_url=Path(source["path"]).as_uri()
        )

        clip = otio.schema.Clip(
            name=f'{clip_id}: {item.get("reason", "Selected segment")}',
            media_reference=media_ref,
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(start, 1),
                duration=otio.opentime.RationalTime(end - start, 1),
            ),
        )

        clip.metadata["AIEdit"] = {
            "clip_id": clip_id,
            "source_filename": source["filename"],
            "reason": item.get("reason", ""),
        }

        track.append(clip)

    timeline.tracks.append(track)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    otio.adapters.write_to_file(timeline, str(output_path))
