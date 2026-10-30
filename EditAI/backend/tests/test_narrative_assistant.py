# tests/test_narrative_assistant.py
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app

def test_narrative_queries():
    client = TestClient(app)

    print("=" * 65)
    print("  TESTING AI ASSISTANT NARRATIVE & CROSS-CLIP QUERIES")
    print("=" * 65)

    # 1. First run pipeline sample pack to have assembled multi-clip timeline
    res_pipe = client.post("/api/pipeline/sample-pack")
    assert res_pipe.status_code == 200
    p_data = res_pipe.json()
    tl_state = p_data["timeline_state"]
    print(f"[OK] Multi-clip sequence active: {len(tl_state['clips'])} clips ({tl_state['total_duration']}s)")

    # 2. Test: Explain why this section was selected or removed
    print("\n--- TEST 1: 'Explain why this section was selected or removed' ---")
    res1 = client.post("/api/chatbot/command", json={
        "prompt": "Explain why this section was selected or removed.",
        "current_timeline": tl_state
    })
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["understood"] is True
    print(f"[OK] Response: {d1['message']}")

    # 3. Test: Find repeated statements across these videos
    print("\n--- TEST 2: 'Find repeated statements across these videos' ---")
    res2 = client.post("/api/chatbot/command", json={
        "prompt": "Find repeated statements across these videos.",
        "current_timeline": tl_state
    })
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["understood"] is True
    print(f"[OK] Response: {d2['message']}")

    # 4. Test: Arrange these clips into a logical story
    print("\n--- TEST 3: 'Arrange these clips into a logical story' ---")
    res3 = client.post("/api/chatbot/command", json={
        "prompt": "Arrange these clips into a logical story.",
        "current_timeline": tl_state
    })
    assert res3.status_code == 200
    d3 = res3.json()
    assert d3["understood"] is True
    print(f"[OK] Response: {d3['message']}")

    # 5. Test: Show me the important moments
    print("\n--- TEST 4: 'Show me the important moments' ---")
    res4 = client.post("/api/chatbot/command", json={
        "prompt": "Show me the important moments.",
        "current_timeline": tl_state
    })
    assert res4.status_code == 200
    d4 = res4.json()
    assert d4["understood"] is True
    print(f"[OK] Response: {d4['message']}")

    # 6. Test: Create a shorter version while preserving the main message
    print("\n--- TEST 5: 'Create a shorter version while preserving the main message' ---")
    res5 = client.post("/api/chatbot/command", json={
        "prompt": "Create a shorter version while preserving the main message.",
        "current_timeline": tl_state
    })
    assert res5.status_code == 200
    d5 = res5.json()
    assert d5["understood"] is True
    print(f"[OK] Response: {d5['message']}")

    print("\n" + "=" * 65)
    print("  ALL NARRATIVE ASSISTANT QUERIES TESTED AND PASSED!")
    print("=" * 65)

if __name__ == "__main__":
    test_narrative_queries()

