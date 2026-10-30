import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app

def test_sqlite_persistence():
    client = TestClient(app)

    print("--- TEST PERSISTENCE: Create, Save & Reload Project ---")
    # 1. Create project
    res_create = client.post("/api/projects", json={"name": "Commercial Cut v1"})
    assert res_create.status_code == 200
    p = res_create.json()
    proj_id = p["id"]
    print(f"[OK] Created project '{p['name']}' with ID: {proj_id}")

    # 2. Save project state with clips and subtitles
    sample_clips = [
        {
            "id": "clip_01",
            "name": "Intro Scene",
            "source_file": "sample_demo.mp4",
            "source_filename": "sample_demo.mp4",
            "source_start": 0.0,
            "source_end": 10.0,
            "timeline_start": 0.0,
            "timeline_end": 10.0,
            "duration": 10.0,
            "speed": 1.0,
            "volume": 1.0
        },
        {
            "id": "clip_02",
            "name": "Outro Scene",
            "source_file": "sample_demo.mp4",
            "source_filename": "sample_demo.mp4",
            "source_start": 25.0,
            "source_end": 30.0,
            "timeline_start": 10.0,
            "timeline_end": 15.0,
            "duration": 5.0,
            "speed": 1.0,
            "volume": 1.0
        }
    ]
    sample_subs = [
        {"start_time": 1.0, "end_time": 5.0, "text": "Welcome to Commercial Cut v1"}
    ]

    res_save = client.post(f"/api/projects/{proj_id}/save", json={
        "name": "Commercial Cut v1",
        "settings": {"fps": 25.0, "resolution": "1080p"},
        "clips": sample_clips,
        "subtitles": sample_subs
    })
    assert res_save.status_code == 200
    print("[OK] Saved project state to SQLite database")

    # 3. Reload project from SQLite and verify data integrity
    res_get = client.get(f"/api/projects/{proj_id}")
    assert res_get.status_code == 200
    loaded = res_get.json()
    assert loaded["name"] == "Commercial Cut v1"
    assert len(loaded["timeline"]["clips"]) == 2
    assert loaded["timeline"]["clips"][0]["id"] == "clip_01"
    assert loaded["timeline"]["clips"][1]["id"] == "clip_02"
    assert loaded["timeline"]["total_duration"] == 15.0
    assert len(loaded["timeline"]["subtitles"]) == 1
    assert loaded["timeline"]["subtitles"][0]["text"] == "Welcome to Commercial Cut v1"

    print("[OK] Verified reload from SQLite: All clips, subtitles, and duration preserved accurately!")
    print("--- PERSISTENCE TEST PASSED ---")

if __name__ == "__main__":
    test_sqlite_persistence()
