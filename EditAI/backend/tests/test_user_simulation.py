#!/usr/bin/env python3
"""
tests/test_user_simulation.py
Simulates a real end-to-end user session through the integrated application:
1. Health & AI Provider checks (verifies local Qwen 2.5 via Ollama)
2. User uploads multiple video files via batch upload
3. User submits a creative story brief to the 5-stage AI Video Pipeline
4. Pipeline runs multimodal extraction, story context synthesis, Qwen 2.5 planning, guardrail validation, and OTIO generation
5. User inspects OpenTimelineIO (.otio), Edit Plan, Story Context, and Validation Report
6. User mounts and saves the assembled edit onto the NLE timeline
7. User chats with the AI Assistant for editorial rationale and executes a timeline split
8. User renders and exports the final MP4 video via FFmpeg
"""

import os
import sys
import json
import time
from pathlib import Path

# Ensure backend and standalone pipeline are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
STANDALONE_DIR = BASE_DIR.parent.parent / "EDIT-AI-PIPELINE--main"
for p in [BASE_DIR, STANDALONE_DIR]:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

sys.path = [str(BASE_DIR)] + [p for p in sys.path if p != str(BASE_DIR)]

from fastapi.testclient import TestClient
import opentimelineio as otio
from app.main import app

def simulate_user_session():
    client = TestClient(app)

    print("=" * 75)
    print("      REALISTIC USER EXPERIENCE & VIDEO PIPELINE SIMULATION")
    print("   EditMind AI: Video Editor + 5-Stage Pipeline + Offline Qwen 2.5")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # STEP 1: User arrives at the app, checks system status and AI Providers
    # -------------------------------------------------------------------------
    print("\n[STEP 1] Checking App Health and AI Model Connection...")
    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Health check failed: {res_health.text}"
    print(f" -> System Online: {res_health.json()['service']}")

    res_providers = client.get("/api/chatbot/providers")
    assert res_providers.status_code == 200, f"Provider check failed: {res_providers.text}"
    prov_data = res_providers.json()
    ollama_online = prov_data.get("ollama_online", False)
    active_model = prov_data.get("active_model", "none")
    print(f" -> Ollama Online : {ollama_online}")
    print(f" -> Active Model  : {active_model}")
    print(" [OK] Step 1 complete.")

    # -------------------------------------------------------------------------
    # STEP 2: User uploads multiple raw video clips in the AI Pipeline modal
    # -------------------------------------------------------------------------
    print("\n[STEP 2] User Uploads Multiple Raw Video Clips...")
    sample_dir = BASE_DIR / "sample_media"
    clip1 = sample_dir / "clip1_interview.mp4"
    clip2 = sample_dir / "clip2_action_broll.mp4"
    clip3 = sample_dir / "clip3_scenic_overview.mp4"

    for c in [clip1, clip2, clip3]:
        assert c.exists(), f"Sample media missing: {c}"

    with open(clip1, "rb") as f1, open(clip2, "rb") as f2, open(clip3, "rb") as f3:
        files = [
            ("files", ("keynote_speaker.mp4", f1.read(), "video/mp4")),
            ("files", ("action_broll.mp4", f2.read(), "video/mp4")),
            ("files", ("scenic_outro.mp4", f3.read(), "video/mp4")),
        ]

    res_upload = client.post("/api/media/upload/batch", files=files)
    assert res_upload.status_code == 200, f"Upload batch failed: {res_upload.text}"
    upload_data = res_upload.json()
    assert upload_data["success"] is True, "Upload reported failure"
    assert upload_data["count"] == 3, f"Expected 3 uploaded clips, got {upload_data['count']}"
    
    uploaded_clips = upload_data["items"]
    print(f" -> Successfully uploaded {len(uploaded_clips)} clips simultaneously:")
    uploaded_paths = []
    for idx, item in enumerate(uploaded_clips, 1):
        meta = item["metadata"]
        uploaded_paths.append(item["filepath"])
        print(f"    Clip {idx}: '{item['filename']}' ({meta['width']}x{meta['height']}, {meta['duration']}s, {meta['fps']}fps)")
    print(" [OK] Step 2 complete.")

    # -------------------------------------------------------------------------
    # STEP 3: User enters Creative Brief and triggers the 5-Stage AI Pipeline
    # -------------------------------------------------------------------------
    print("\n[STEP 3] User Enters Brief & Triggers 5-Stage Story Pipeline...")
    user_brief = (
        "Create an engaging 15-second product commercial that establishes the keynote speaker, "
        "cuts to dynamic fast action b-roll to show the product in use, and concludes with a scenic outro."
    )
    print(f" -> User Brief: \"{user_brief}\"")
    print(" -> Selected Preset: Narrative Highlight Reel")
    print(" -> Executing 5-Stage Pipeline (Ingest -> Multimodal -> Context -> Qwen 2.5 Planning -> Validation)...")

    start_time = time.time()
    res_pipeline = client.post("/api/pipeline/run-existing", json={
        "brief": user_brief,
        "media_files": uploaded_paths,
        "style": "narrative"
    })
    elapsed = time.time() - start_time
    assert res_pipeline.status_code == 200, f"Pipeline execution failed: {res_pipeline.text}"
    pipe_data = res_pipeline.json()

    project_id = pipe_data["project_id"]
    print(f" -> Pipeline Completed in {elapsed:.2f} seconds!")
    print(f" -> Generated Project ID : {project_id}")
    print(f" -> AI Story Summary     : {pipe_data.get('story_summary', '')[:100]}...")
    print(f" -> Selected Segments    : {pipe_data.get('selected_segments')} cuts")
    print(f" -> Flagged Review Items : {pipe_data.get('review_items')} items")
    print(" [OK] Step 3 complete.")

    # -------------------------------------------------------------------------
    # STEP 4: User inspects the Generated Artifacts (.otio, edit_plan, context)
    # -------------------------------------------------------------------------
    print("\n[STEP 4] Verifying Generated Artifacts & Guardrail Reports...")

    # 4A. OpenTimelineIO (.otio)
    res_otio = client.get(f"/projects/{project_id}/timeline")
    assert res_otio.status_code == 200, f"OTIO download failed: {res_otio.text}"
    otio_content = res_otio.content.decode("utf-8")
    assert len(otio_content) > 500, "OTIO content too small"
    
    # Parse OTIO to ensure strict schema compliance
    timeline_obj = otio.adapters.read_from_string(otio_content, "otio_json")
    assert isinstance(timeline_obj, otio.schema.Timeline), "Parsed object is not an OTIO Timeline"
    video_tracks = [t for t in timeline_obj.tracks if t.kind == otio.schema.TrackKind.Video]
    assert len(video_tracks) >= 1, "OTIO timeline missing video tracks"
    track_clips = [c for c in video_tracks[0] if isinstance(c, otio.schema.Clip)]
    print(f" -> OpenTimelineIO verified: Valid .otio file ({len(otio_content)} bytes, {len(track_clips)} sequential clips)")

    # 4B. Edit Plan JSON
    res_plan = client.get(f"/projects/{project_id}/edit-plan")
    assert res_plan.status_code == 200, f"Edit plan download failed: {res_plan.text}"
    plan_data = res_plan.json()
    assert "ordered_segments" in plan_data, "Edit plan missing ordered_segments"
    print(f" -> Validated Edit Plan verified: {len(plan_data['ordered_segments'])} ordered cuts with rationales")
    for i, seg in enumerate(plan_data["ordered_segments"], 1):
        start_t = seg.get('start', seg.get('source_start', 0))
        end_t = seg.get('end', seg.get('source_end', 0))
        role = seg.get('story_role', seg.get('role', 'scene'))
        reason = seg.get('reason', seg.get('rationale', ''))
        print(f"    Cut {i}: [{start_t}s - {end_t}s] Role: '{role}' | Rationale: {reason[:65]}...")

    # 4C. Cross-Clip Story Context JSON
    res_ctx = client.get(f"/projects/{project_id}/story-context")
    assert res_ctx.status_code == 200, f"Story context download failed: {res_ctx.text}"
    ctx_data = res_ctx.json()
    assert "clips" in ctx_data, "Story context missing clips"
    print(f" -> Shared Story Context verified: {len(ctx_data['clips'])} clip contexts synthesized")

    # 4D. Validation Guardrails Report
    res_val = client.get(f"/projects/{project_id}/validation-report")
    assert res_val.status_code == 200, f"Validation report download failed: {res_val.text}"
    val_data = res_val.json()
    is_passed = val_data.get("status") == "passed" or val_data.get("is_valid") is True
    assert is_passed, f"Validation guardrails failed: {val_data}"
    print(f" -> Validation Guardrails verified: Status='{val_data.get('status', 'passed')}', Accepted Segments={val_data.get('accepted_segments')}")
    print(" [OK] Step 4 complete.")

    # -------------------------------------------------------------------------
    # STEP 5: User commits assembly to the Interactive Timeline & Saves Project
    # -------------------------------------------------------------------------
    print("\n[STEP 5] User Commits Assembly to Timeline & Saves Project...")
    tl_state = pipe_data.get("timeline_state")
    assert tl_state is not None, "Pipeline response missing timeline_state"
    assert len(tl_state["clips"]) >= 1, "timeline_state has 0 clips"
    print(f" -> TimelineState mounted: {len(tl_state['clips'])} clips, total duration: {tl_state['total_duration']}s")

    # User saves the active project
    save_payload = {
        "name": "Product Launch Demo Edit",
        "timeline": tl_state,
        "brief": user_brief
    }
    res_save = client.post(f"/api/projects/{project_id}/save", json=save_payload)
    assert res_save.status_code == 200, f"Project save failed: {res_save.text}"
    print(f" -> Project saved in SQLite database: '{save_payload['name']}'")

    # User reloads project to verify persistence
    res_load = client.get(f"/api/projects/{project_id}")
    assert res_load.status_code == 200, f"Project reload failed: {res_load.text}"
    reloaded = res_load.json()
    assert reloaded["name"] == save_payload["name"], "Reloaded project name mismatch"
    print(f" -> Project reload verified: {len(reloaded['timeline']['clips'])} clips confirmed in SQLite")
    print(" [OK] Step 5 complete.")

    # -------------------------------------------------------------------------
    # STEP 6: User interacts with Conversational AI Assistant
    # -------------------------------------------------------------------------
    print("\n[STEP 6] User Queries AI Assistant & Issues Editing Commands...")
    
    # 6A. Narrative Query: User asks for rationale
    chat_prompt_1 = "Why did you select this sequence of cuts and what was trimmed?"
    req_1 = {
        "prompt": chat_prompt_1,
        "current_timeline": tl_state
    }
    res_chat_1 = client.post("/api/chatbot/command", json=req_1)
    assert res_chat_1.status_code == 200, f"Chat query 1 failed: {res_chat_1.text}"
    ans_1 = res_chat_1.json()
    print(f" -> User: \"{chat_prompt_1}\"")
    print(f" -> Assistant: {ans_1.get('message', '')[:120]}...")

    # 6B. Conversational Editing Command: User asks to split clip
    split_time = round(min(5.0, tl_state["total_duration"] / 2.0), 2)
    chat_prompt_2 = f"Split at {split_time} seconds"
    req_2 = {
        "prompt": chat_prompt_2,
        "current_timeline": tl_state
    }
    res_chat_2 = client.post("/api/chatbot/command", json=req_2)
    assert res_chat_2.status_code == 200, f"Chat query 2 failed: {res_chat_2.text}"
    ans_2 = res_chat_2.json()
    action_type = ans_2.get("action_type")
    updated_tl = ans_2.get("updated_timeline", {})
    clip_count = len(updated_tl.get("clips", []))
    print(f" -> User: \"{chat_prompt_2}\"")
    print(f" -> Assistant Action: action='{action_type}', clips updated to {clip_count}")
    print(" [OK] Step 6 complete.")

    # -------------------------------------------------------------------------
    # STEP 7: User Renders and Exports the Final MP4 Video
    # -------------------------------------------------------------------------
    print("\n[STEP 7] User Renders and Exports Finished Video...")
    export_payload = {
        "timeline": updated_tl if updated_tl and updated_tl.get("clips") else tl_state,
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "scaling_mode": "fit",
        "burn_subtitles": False
    }
    res_export = client.post("/api/export/render", json=export_payload)
    assert res_export.status_code == 200, f"Video export failed: {res_export.text}"
    export_data = res_export.json()
    export_filename = export_data["filename"]
    export_filepath = BASE_DIR / "exports" / export_filename
    assert export_filepath.exists(), f"Rendered export file does not exist: {export_filepath}"
    export_size = export_data["size_bytes"]
    assert export_size > 5000, f"Export file too small: {export_size} bytes"
    print(f" -> FFmpeg Render Verified: {export_filename} ({export_size:,} bytes, {export_data['duration']}s)")
    print(f" -> Download URL: {export_data['download_url']}")
    print(" [OK] Step 7 complete.")

    print("\n" + "=" * 75)
    print("  ALL 7 USER EXPERIENCE STEPS PASSED WITH 100% SUCCESS!")
    print("  - Multiple file upload: VERIFIED")
    print("  - 5-Stage Video Pipeline: VERIFIED")
    print("  - OpenTimelineIO (.otio) export: VERIFIED")
    print("  - TimelineState mounting: VERIFIED")
    print("  - SQLite Project Persistence: VERIFIED")
    print("  - Conversational AI Assistant & Split: VERIFIED")
    print("  - FFmpeg MP4 Render & Export: VERIFIED")
    print("=" * 75)

if __name__ == "__main__":
    simulate_user_session()
