import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app

def test_multi_clip_assembly_pipeline():
    client = TestClient(app)

    print("--- TEST 1: Load Multi-Clip Sample Pack ---")
    res_pack = client.post("/api/assembly/sample-pack")
    assert res_pack.status_code == 200
    pack_data = res_pack.json()
    clip_paths = pack_data["clip_paths"]
    print(f"[OK] Multi-clip pack loaded: {len(clip_paths)} source clips")
    for a in pack_data["clip_analyses"]:
        print(f"   • {a['filename']}: Category='{a['primary_category']}', Duration={a['duration']}s, Motion={a['motion_level']}, Tags={a['content_tags']}")

    print("\n--- TEST 2: AI Multi-Clip Analysis & Sequence Assembly ---")
    res_asm = client.post("/api/assembly/analyze-and-assemble", json={
        "media_files": clip_paths,
        "style": "narrative",
        "user_prompt": "Assemble a coherent highlight cut opening with speaker and building up to action b-roll."
    })
    assert res_asm.status_code == 200
    asm_data = res_asm.json()
    print(f"[OK] Assembly Style: '{asm_data['style']}' | Total Duration: {asm_data['total_duration']}s")
    print(f"[OK] Assembled Segments Count: {len(asm_data['segments'])}")

    print("\n--- TEST 3: Inspect Editorial Decisions & Rationales ---")
    for idx, seg in enumerate(asm_data["segments"]):
        print(f"   [{idx + 1}] {seg['role']} ({seg['duration']}s): {seg['source_filename']} [src: {seg['source_in']}s - {seg['source_out']}s] -> timeline: {seg['timeline_start']}s - {seg['timeline_end']}s")
        print(f"       Rationale: {seg['rationale']}")
        if seg.get("trimmed_reason"):
            print(f"       Trimmed: {seg['trimmed_reason']}")

    print(f"\n[OK] Discarded/Trimmed Sections Count: {len(asm_data['discarded_summary'])}")
    print(f"[OK] Synchronized Captions Count: {len(asm_data['subtitles'])}")
    for sub in asm_data["subtitles"]:
        print(f"       Sub {sub['id']} [{sub['start_time']}s - {sub['end_time']}s]: \"{sub['text']}\"")

    print("\n--- TEST 4: Verify Assembled Timeline State ---")
    tl = asm_data["timeline_state"]
    assert len(tl["clips"]) >= 3
    assert tl["total_duration"] > 0
    print(f"[OK] Timeline clips populated: {len(tl['clips'])} sequential clips ready for timeline refinement!")

    print("\n============================================")
    print("  MULTI-CLIP AI ASSEMBLY PIPELINE VERIFIED! ")
    print("============================================")

if __name__ == "__main__":
    test_multi_clip_assembly_pipeline()
