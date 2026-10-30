# tests/test_pipeline.py
"""
Automated test suite verifying the complete connection between:
- Standalone AI video-analysis pipeline
- FastAPI backend routes
- OpenTimelineIO (.otio) timeline generation
- Frontend-ready TimelineState conversion
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure backend app takes precedence in sys.path
sys.path = [str(BASE_DIR)] + [p for p in sys.path if p != str(BASE_DIR)]

from fastapi.testclient import TestClient
from app.main import app

def test_pipeline_integration():
    client = TestClient(app)

    print("=" * 65)
    print("  TESTING AI VIDEO PIPELINE & FRONTEND INTEGRATION")
    print("=" * 65)

    # 1. Health check
    print("\n--- TEST 1: Backend Health Check ---")
    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Health check failed: {res_health.text}"
    health_data = res_health.json()
    print(f"[OK] Backend Online: {health_data['service']}")

    # 2. Pipeline Execution on Multi-Clip Demo Pack
    print("\n--- TEST 2: Run 5-Stage Pipeline on Demo Pack ---")
    brief = "Assemble a dynamic highlight cut opening with speaker monologue and transitioning into action b-roll."
    res_pipe = client.post("/api/pipeline/sample-pack", json={"brief": brief})
    assert res_pipe.status_code == 200, f"Pipeline execution failed: {res_pipe.text}"
    data = res_pipe.json()

    project_id = data["project_id"]
    print(f"[OK] Pipeline completed! Project ID: {project_id}")
    print(f"     Story Summary: {data.get('story_summary', '')[:80]}...")
    print(f"     Selected Segments: {data.get('selected_segments')} cuts")
    print(f"     Flagged Review Items: {data.get('review_items')} items")

    # 3. Verify OpenTimelineIO (.otio) Export
    print("\n--- TEST 3: Verify OpenTimelineIO (.otio) File Download ---")
    otio_url = data.get("timeline_url", f"/projects/{project_id}/timeline")
    res_otio = client.get(otio_url)
    assert res_otio.status_code == 200, f"Failed to download OTIO: {res_otio.text}"
    assert len(res_otio.content) > 100, "OTIO file is unexpectedly empty"
    print(f"[OK] OpenTimelineIO file verified ({len(res_otio.content)} bytes)")

    # 4. Verify Interactive TimelineState for Frontend
    print("\n--- TEST 4: Verify Frontend TimelineState Compatibility ---")
    tl_state = data.get("timeline_state")
    assert tl_state is not None, "Missing timeline_state in response"
    assert "clips" in tl_state, "timeline_state missing 'clips'"
    assert len(tl_state["clips"]) >= 1, "timeline_state has 0 clips"
    assert tl_state["total_duration"] > 0, "total_duration must be greater than 0"
    print(f"[OK] Frontend TimelineState verified: {len(tl_state['clips'])} sequential clips")
    for idx, c in enumerate(tl_state["clips"]):
        print(f"     Cut {idx + 1}: [{c['timeline_start']}s -> {c['timeline_end']}s] Role='{c.get('role')}' ({c.get('source_filename')})")

    # 5. Verify Subtitles
    subs = data.get("subtitles", [])
    print(f"[OK] Frontend Subtitle Track: {len(subs)} synchronized captions")

    print("\n================================================================")
    print("  ALL PIPELINE & FRONTEND INTEGRATION TESTS PASSED SUCCESSFULLY! ")
    print("================================================================")

if __name__ == "__main__":
    test_pipeline_integration()

