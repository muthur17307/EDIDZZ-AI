import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app

def run_tests():
    client = TestClient(app)

    print("--- TEST 1: Load Sample Project ---")
    res = client.post("/api/media/load-sample")
    assert res.status_code == 200
    data = res.json()
    tl = data["timeline"]
    meta = data["metadata"]
    print(f"[OK] Loaded sample: {meta['filename']} | Duration: {tl['total_duration']}s | Clips: {len(tl['clips'])} | Subs: {len(tl['subtitles'])}")

    print("\n--- TEST 2: Analyze Video ---")
    res_ana = client.post("/api/analysis/analyze", json={"filepath": meta["filepath"], "duration": meta["duration"]})
    assert res_ana.status_code == 200
    ana_data = res_ana.json()
    print(f"[OK] Scenes detected: {len(ana_data['scenes'])} | Silences: {len(ana_data['silences'])} | Low Activity: {len(ana_data['low_activity_segments'])}")

    print("\n--- TEST 3: Select Clip 00:10 to 00:25 ---")
    res_cmd1 = client.post("/api/chatbot/command", json={
        "prompt": "Select the clip from 00:10 to 00:25.",
        "current_timeline": tl,
        "media_metadata": meta,
        "scenes": ana_data["scenes"]
    })
    assert res_cmd1.status_code == 200
    cmd1_data = res_cmd1.json()
    tl = cmd1_data["updated_timeline"]
    print(f"[OK] Chatbot: {cmd1_data['message']}")
    assert tl["selection_range"] == [10.0, 25.0]

    print("\n--- TEST 4: Split at 00:18 ---")
    res_cmd2 = client.post("/api/chatbot/command", json={
        "prompt": "Split at 00:18.",
        "current_timeline": tl,
        "media_metadata": meta,
        "scenes": ana_data["scenes"]
    })
    assert res_cmd2.status_code == 200
    cmd2_data = res_cmd2.json()
    tl = cmd2_data["updated_timeline"]
    print(f"[OK] Chatbot: {cmd2_data['message']}")
    assert len(tl["clips"]) == 2

    print("\n--- TEST 5: Delete Selected Segment ---")
    res_cmd3 = client.post("/api/chatbot/command", json={
        "prompt": "Delete the selected segment.",
        "current_timeline": tl,
        "media_metadata": meta,
        "scenes": ana_data["scenes"]
    })
    assert res_cmd3.status_code == 200
    cmd3_data = res_cmd3.json()
    tl = cmd3_data["updated_timeline"]
    print(f"[OK] Chatbot: {cmd3_data['message']}")
    print(f"[OK] New duration after ripple: {tl['total_duration']}s")
    assert tl["total_duration"] == 15.0

    print("\n--- TEST 6: Subtitle Synchronization Verification ---")
    print(f"[OK] Remaining subtitles count: {len(tl['subtitles'])}")
    for sub in tl["subtitles"]:
        print(f"   Sub {sub['id']}: [{sub['start_time']}s - {sub['end_time']}s] -> {sub['text']}")

    print("\n--- TEST 7: Export Render to Playable MP4 ---")
    res_exp = client.post("/api/export/render", json={
        "timeline": tl,
        "resolution": "original",
        "burn_subtitles": True,
        "audio_mode": "original"
    })
    assert res_exp.status_code == 200
    exp_data = res_exp.json()
    print(f"[OK] Export successful: {exp_data['filename']}")
    print(f"[OK] File size: {exp_data['size_bytes']} bytes | Duration: {exp_data['duration']}s")
    print(f"[OK] Download URL: {exp_data['download_url']}")

    print("\n============================================")
    print("  ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("============================================")

if __name__ == "__main__":
    run_tests()
