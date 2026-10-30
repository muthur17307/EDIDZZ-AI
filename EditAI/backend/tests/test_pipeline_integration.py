import io
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app

def test_complete_pipeline_integration():
    client = TestClient(app)

    print("=============================================================")
    print("   AI VIDEO-ANALYSIS PIPELINE INTEGRATION TEST SUITE        ")
    print("=============================================================")

    # 1. Test POST /projects with multi-clip upload & brief
    print("\n--- TEST 1: Multipart Project Upload & Pipeline Execution ---")
    sample_dir = BASE_DIR / "sample_media"
    clip1 = sample_dir / "clip1_interview.mp4"
    clip2 = sample_dir / "clip2_action_broll.mp4"
    clip3 = sample_dir / "clip3_scenic_overview.mp4"

    assert clip1.exists() and clip2.exists() and clip3.exists(), "Sample media must exist"

    with open(clip1, "rb") as f1, open(clip2, "rb") as f2, open(clip3, "rb") as f3:
        files = [
            ("clips", ("clip1_interview.mp4", f1.read(), "video/mp4")),
            ("clips", ("clip2_action_broll.mp4", f2.read(), "video/mp4")),
            ("clips", ("clip3_scenic_overview.mp4", f3.read(), "video/mp4")),
        ]
        data = {
            "brief": "Produce a high-energy commercial edit with strong opening dialogue hook and dynamic action b-roll."
        }
        res = client.post("/projects", data=data, files=files)

    assert res.status_code == 200, f"Upload pipeline failed: {res.text}"
    result = res.json()
    project_id = result["project_id"]

    print(f"[OK] Project created with ID: {project_id}")
    print(f"[OK] Pipeline status: '{result.get('status')}'")
    print(f"[OK] Story summary: \"{result.get('story_summary')}\"")
    print(f"[OK] Selected segments count: {result.get('selected_segments')}")
    print(f"[OK] Review items count: {result.get('review_items')}")
    assert result.get("selected_segments", 0) > 0, "Pipeline must yield valid selected segments"

    # 2. Test GET /projects/{project_id}/timeline (.otio download)
    print("\n--- TEST 2: OpenTimelineIO (.otio) Download ---")
    res_timeline = client.get(f"/projects/{project_id}/timeline")
    assert res_timeline.status_code == 200, f"Timeline fetch failed: {res_timeline.text}"
    assert len(res_timeline.content) > 100, "OTIO file must not be empty"
    print(f"[OK] Downloaded OpenTimelineIO file: {len(res_timeline.content)} bytes")
    # Verify it can be parsed by OpenTimelineIO
    import opentimelineio as otio
    parsed_tl = otio.adapters.read_from_string(res_timeline.content.decode("utf-8"), "otio_json")
    assert len(parsed_tl.tracks) > 0, "OTIO must have tracks"
    print(f"[OK] OTIO parsed successfully: Track '{parsed_tl.tracks[0].name}' with {len(parsed_tl.tracks[0])} clips")

    # 3. Test GET /projects/{project_id}/edit-plan (edit_plan.json)
    print("\n--- TEST 3: Edit Plan JSON Inspection ---")
    res_plan = client.get(f"/projects/{project_id}/edit-plan")
    assert res_plan.status_code == 200
    plan_json = res_plan.json()
    assert "ordered_segments" in plan_json
    print(f"[OK] Edit plan contains {len(plan_json['ordered_segments'])} ordered segments")
    for idx, seg in enumerate(plan_json["ordered_segments"]):
        print(f"     [{idx + 1}] {seg.get('story_role', 'cut').upper()} | {seg['clip_id']} [{seg['start']}s - {seg['end']}s]: {seg.get('reason')}")

    # 4. Test GET /projects/{project_id}/story-context
    print("\n--- TEST 4: Cross-Clip Story Context ---")
    res_context = client.get(f"/projects/{project_id}/story-context")
    assert res_context.status_code == 200
    ctx_json = res_context.json()
    assert "clips" in ctx_json and len(ctx_json["clips"]) == 3
    print(f"[OK] Story context verified: {len(ctx_json['clips'])} analyzed source clips")

    # 5. Test POST /api/pipeline/sample-pack (Frontend pipeline trigger)
    print("\n--- TEST 5: Frontend Pipeline Sample Pack Trigger ---")
    res_sample = client.post("/api/pipeline/sample-pack", json={"brief": "Fast-paced social media showcase"})
    assert res_sample.status_code == 200
    sample_data = res_sample.json()
    assert sample_data["status"] == "completed"
    assert "timeline_state" in sample_data
    tl_state = sample_data["timeline_state"]
    print(f"[OK] Sample pack pipeline produced timeline with {len(tl_state['clips'])} editable clips")
    print(f"[OK] Total duration: {tl_state['total_duration']}s")
    print(f"[OK] Subtitles synchronized: {len(sample_data.get('subtitles', []))}")

    print("\n=============================================================")
    print("   ALL PIPELINE INTEGRATION TESTS COMPLETED SUCCESSFULLY!    ")
    print("=============================================================")

if __name__ == "__main__":
    test_complete_pipeline_integration()

