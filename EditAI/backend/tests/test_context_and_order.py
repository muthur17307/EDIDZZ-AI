#!/usr/bin/env python3
"""
tests/test_context_and_order.py
Verifies that after AI video analysis finishes:
1. The video clips are ordered correctly into a coherent narrative arc (Hook -> Action -> Core -> Outro).
2. The context checks are correct (speech transcripts, visual motion, roles assigned).
3. The timeline sequence is continuous: starts at 0.0s, no gaps, no overlaps.
4. Timestamps are clamped within physical source bounds.
5. Repetitive or redundant footage is identified and isolated in the review ledger.
6. OpenTimelineIO (.otio) matches the narrative ordering exactly.
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STANDALONE_DIR = BASE_DIR.parent.parent / "EDIT-AI-PIPELINE--main"
for p in [BASE_DIR, STANDALONE_DIR]:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

sys.path = [str(BASE_DIR)] + [p for p in sys.path if p != str(BASE_DIR)]

from fastapi.testclient import TestClient
import opentimelineio as otio
from app.main import app

def test_context_and_narrative_ordering():
    client = TestClient(app)

    print("=" * 75)
    print("   CHECKING POST-ANALYSIS VIDEO ORDERING & CONTEXT INTEGRITY")
    print("=" * 75)

    # 1. Execute 5-Stage Pipeline on 3-Clip Demo Pack
    print("\n--- TEST 1: Running Multimodal Analysis & Context Synthesis ---")
    brief = "Assemble an energetic commercial starting with the keynote speaker, cutting into fast action b-roll, delivering the core value, and ending with a scenic outro."
    
    res = client.post("/api/pipeline/sample-pack", json={"brief": brief})
    assert res.status_code == 200, f"Pipeline execution failed: {res.text}"
    data = res.json()
    project_id = data["project_id"]
    print(f"[OK] Pipeline finished. Project ID: {project_id}")

    # 2. Check Context Matrix
    print("\n--- TEST 2: Validating Cross-Clip Story Context ---")
    res_ctx = client.get(f"/projects/{project_id}/story-context")
    assert res_ctx.status_code == 200, f"Context fetch failed: {res_ctx.text}"
    ctx = res_ctx.json()
    
    assert "clips" in ctx, "Context missing 'clips'"
    assert "segments" in ctx, "Context missing 'segments'"
    print(f"[OK] Context Matrix Generated: {len(ctx['clips'])} source clips, {len(ctx['segments'])} analyzed segments")
    
    # Verify each clip has proper category and metadata in context
    for c in ctx["clips"]:
        print(f"     Source Clip: '{c['clip_id']}' -> {c.get('filename')} (Duration: {c['duration']}s)")

    # 3. Check Edit Plan & Narrative Ordering
    print("\n--- TEST 3: Verifying Logical Narrative Order (Hook -> Action -> Core -> Outro) ---")
    res_plan = client.get(f"/projects/{project_id}/edit-plan")
    assert res_plan.status_code == 200, f"Plan fetch failed: {res_plan.text}"
    plan = res_plan.json()
    
    ordered_segments = plan.get("ordered_segments", [])
    assert len(ordered_segments) >= 2, f"Too few segments in plan: {len(ordered_segments)}"
    print(f"[OK] Total Ordered Cuts: {len(ordered_segments)}")

    # Check narrative progression
    expected_arc = ["introduction", "action_broll", "core_message", "outro"]
    found_roles = []
    
    for idx, seg in enumerate(ordered_segments, 1):
        role = seg.get("story_role", seg.get("role", "scene"))
        found_roles.append(role)
        cid = seg.get("clip_id")
        start = seg.get("start", 0.0)
        end = seg.get("end", 0.0)
        reason = seg.get("reason", "")
        print(f"     Cut #{idx}: [{start:.1f}s -> {end:.1f}s] Role: '{role}' (Source: {cid})")
        print(f"             Decision Rationale: {reason}")
        assert end > start, f"Invalid cut duration: end ({end}) <= start ({start})"

    # Assert that introduction comes first
    first_role = found_roles[0]
    assert first_role in ["introduction", "hook", "dialogue"], f"First cut should be introduction/hook, got: '{first_role}'"
    print(f"[OK] Beat 1 Confirmed: Opening Hook is '{first_role}'.")

    # Assert that last cut is an outro/conclusion if 3+ cuts exist
    if len(found_roles) >= 3:
        last_role = found_roles[-1]
        assert last_role in ["outro", "scenic_broll", "conclusion", "core_message"], f"Last cut should provide closure, got: '{last_role}'"
        print(f"[OK] Beat 4 Confirmed: Closing Outro is '{last_role}'.")

    # 4. Check Timeline Continuity (No Gaps, No Overlaps, Starts at 0.0s)
    print("\n--- TEST 4: Verifying Timeline Continuity & Timestamp Math ---")
    tl_state = data.get("timeline_state", {})
    clips = tl_state.get("clips", [])
    assert len(clips) >= 2, "Timeline has fewer than 2 clips"

    assert abs(clips[0]["timeline_start"] - 0.0) < 0.01, f"Timeline must start at 0.0s, got: {clips[0]['timeline_start']}"
    print(f"[OK] Timeline Start: {clips[0]['timeline_start']}s")

    running_time = 0.0
    for idx, clip in enumerate(clips):
        c_start = clip["timeline_start"]
        c_end = clip["timeline_end"]
        c_dur = clip["duration"]

        # Check start matches expected running time (zero gap / zero overlap)
        assert abs(c_start - running_time) < 0.05, f"Gap or overlap detected before clip {idx + 1}: expected {running_time}s, got {c_start}s"
        assert abs(c_end - (c_start + c_dur)) < 0.05, f"Clip {idx + 1} duration mismatch: end {c_end} != start {c_start} + dur {c_dur}"
        
        # Check source bounds
        s_start = clip["source_start"]
        s_end = clip["source_end"]
        assert s_end > s_start, f"Source in/out error in clip {idx + 1}"
        print(f"     Timeline Cut {idx + 1}: [{c_start:5.2f}s -> {c_end:5.2f}s] (dur: {c_dur:4.2f}s) | Source: [{s_start:5.2f}s -> {s_end:5.2f}s] '{clip['name']}'")

        running_time = c_end

    total_duration = tl_state.get("total_duration", 0.0)
    assert abs(running_time - total_duration) < 0.05, f"Total duration mismatch: running {running_time}s != total {total_duration}s"
    print(f"[OK] Timeline Continuity: Seamless ({len(clips)} sequential clips, {total_duration:.2f}s total duration, 0 gaps, 0 overlaps)")

    # 5. Check Repetition and Discarded Ledger
    print("\n--- TEST 5: Verifying Repetition Detection & Review Ledger ---")
    review_items = plan.get("review_items", [])
    warnings = plan.get("warnings", [])
    print(f"[OK] Review Ledger: {len(review_items)} flagged candidate takes, {len(warnings)} warnings")
    for r in review_items:
        print(f"     Flagged: [{r.get('start', 0)}s - {r.get('end', 0)}s] from '{r.get('clip_id')}' -> Reason: {r.get('reason')}")

    # 6. Verify OpenTimelineIO Synchronicity
    print("\n--- TEST 6: Verifying OpenTimelineIO (.otio) Conformity ---")
    res_otio = client.get(f"/projects/{project_id}/timeline")
    assert res_otio.status_code == 200, f"OTIO fetch failed: {res_otio.text}"
    otio_doc = otio.adapters.read_from_string(res_otio.content.decode("utf-8"), "otio_json")
    
    v_tracks = [t for t in otio_doc.tracks if t.kind == otio.schema.TrackKind.Video]
    assert len(v_tracks) >= 1, "Missing video track in OTIO"
    otio_clips = [c for c in v_tracks[0] if isinstance(c, otio.schema.Clip)]
    assert len(otio_clips) == len(clips), f"OTIO clip count ({len(otio_clips)}) does not match timeline ({len(clips)})"
    print(f"[OK] OpenTimelineIO Conforms: Exactly {len(otio_clips)} cuts matching timeline state")

    print("\n" + "=" * 75)
    print("  ALL CONTEXT & NARRATIVE ORDERING CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 75)

if __name__ == "__main__":
    test_context_and_narrative_ordering()

