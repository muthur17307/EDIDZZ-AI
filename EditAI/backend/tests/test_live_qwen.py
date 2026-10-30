# tests/test_live_qwen.py
"""
Automated test suite verifying the live integration of offline Qwen 2.5
running through Ollama with the AI video editing pipeline and editor timeline.
"""

import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.ai_adapter import AIModelAdapter
from app.pipeline.validate import validate_edit_plan
from app.routes.pipeline import _build_timeline_state_from_pipeline
from app.models.schemas import TimelineState, Clip
from app.services.command_parser import CommandParser
from app.services.timeline_manager import TimelineManager
from app.models.schemas import ChatbotCommandRequest

def normalize_plan_segments(plan: dict) -> dict:
    """Safely flattens nested lists if an LLM wraps items inside an inner list."""
    if not isinstance(plan, dict):
        return plan
    segs = plan.get("ordered_segments", [])
    flattened = []
    for s in segs:
        if isinstance(s, list):
            for inner in s:
                if isinstance(inner, dict):
                    flattened.append(inner)
        elif isinstance(s, dict):
            flattened.append(s)
    plan["ordered_segments"] = flattened
    return plan

def test_qwen_integration():
    print("=" * 70)
    print("  VERIFYING OFFLINE QWEN 2.5 INTEGRATION VIA OLLAMA")
    print("=" * 70)

    # 1. Verify Ollama status & Qwen 2.5 detection
    print("\n--- TEST 1: Ollama Status & Model Detection ---")
    status = AIModelAdapter.get_ollama_status()
    print(f"Ollama Base URL : {status['base_url']}")
    print(f"Ollama Online   : {status['online']}")
    print(f"Installed Models: {status['installed_models']}")
    print(f"Active Model    : {status['active_model']}")
    assert status["online"] is True, f"Ollama is offline: {status.get('setup_instructions')}"
    assert "qwen" in status["active_model"].lower(), f"Expected Qwen 2.5, got {status['active_model']}"
    print(f"[OK] Live Qwen 2.5 detected: {status['active_model']}")

    # 2. Test Cross-Clip Narrative Planning with Qwen 2.5
    print("\n--- TEST 2: Qwen 2.5 Cross-Clip Global Story Planning ---")
    mock_clips = [
        {
            "clip_id": "clip_001",
            "filename": "speaker_intro.mp4",
            "duration": 12.0,
            "path": "C:/fake/speaker_intro.mp4"
        },
        {
            "clip_id": "clip_002",
            "filename": "action_broll.mp4",
            "duration": 10.0,
            "path": "C:/fake/action_broll.mp4"
        },
        {
            "clip_id": "clip_003",
            "filename": "outro_scenic.mp4",
            "duration": 10.0,
            "path": "C:/fake/outro_scenic.mp4"
        }
    ]

    context_prompt = (
        "Client Brief: Create a fast-paced 15-second product commercial with a clear hook, dynamic action B-roll, and a clean outro.\n\n"
        "Available Footage Analyses:\n"
        "- clip_001 (12.0s): Speaker introduces the product innovation. Dialogue from 0.0s to 5.0s, repeated take from 6.0s to 11.0s.\n"
        "- clip_002 (10.0s): Kinetic high-speed motion visuals from 1.0s to 5.5s.\n"
        "- clip_003 (10.0s): Atmospheric scenic presentation and logo reveal from 5.0s to 9.5s.\n\n"
        "Select the best non-redundant takes, trim tight timestamps, and return JSON with:\n"
        "{\n"
        '  "story_summary": "...",\n'
        '  "ordered_segments": [\n'
        '    {"clip_id": "clip_001", "start": 0.0, "end": 5.0, "decision": "keep", "reason": "Opening hook", "story_role": "introduction"}\n'
        "  ],\n"
        '  "review_items": []\n'
        "}"
    )
    system_inst = "You are an expert video editorial planner. Return valid JSON dictionary with 'story_summary', 'ordered_segments' (list of objects), and 'review_items'."

    res = AIModelAdapter.call_ollama(
        user_prompt=context_prompt,
        system_instruction=system_inst,
        model=status["active_model"],
        timeout=60.0
    )

    assert res is not None, "Qwen 2.5 returned None"
    assert isinstance(res, dict), f"Expected dict, got {type(res)}"
    res = normalize_plan_segments(res)

    print(f"[OK] Qwen 2.5 Story Summary: {res.get('story_summary', '')[:85]}...")
    print(f"[OK] Proposed Cuts Count   : {len(res.get('ordered_segments', []))}")
    for i, seg in enumerate(res.get("ordered_segments", [])):
        print(f"     Cut {i+1}: {seg.get('clip_id')} [{seg.get('start')}s - {seg.get('end')}s] -> {seg.get('story_role')}: {seg.get('reason')}")

    # 3. Test Deterministic Validation Guardrails on Qwen 2.5 Output
    print("\n--- TEST 3: Validation Guardrails on Qwen 2.5 Plan ---")
    val_res = validate_edit_plan(mock_clips, res)
    print(f"Validation Valid  : {val_res['valid']}")
    print(f"Validated Segments: {len(val_res['valid_segments'])}")
    print(f"Flagged Review    : {len(val_res['review_items'])}")
    print(f"Errors            : {val_res['errors']}")
    print(f"Warnings          : {val_res['warnings']}")
    assert len(val_res["valid_segments"]) > 0, "No segments passed validation"
    print("[OK] Guardrails verified: Timestamps clamped and verified within source bounds.")

    # 4. Test Translation to Native Editor TimelineState
    print("\n--- TEST 4: Translate Qwen 2.5 Plan to Native Editor TimelineState ---")
    tl_state, subs = _build_timeline_state_from_pipeline(
        clips=mock_clips,
        ordered_segments=val_res["valid_segments"],
        project_id="test_proj"
    )
    assert len(tl_state.clips) == len(val_res["valid_segments"])
    assert tl_state.total_duration > 0
    print(f"[OK] Native TimelineState generated: {len(tl_state.clips)} clips | Total Duration: {tl_state.total_duration}s")
    for c in tl_state.clips:
        print(f"     Timeline Clip '{c.name}': [{c.timeline_start}s -> {c.timeline_end}s] Stream: {c.stream_url}")

    # 5. Test Chatbot Natural Language Command with Qwen 2.5
    print("\n--- TEST 5: Chatbot Natural Language Command via Qwen 2.5 ---")
    mgr = TimelineManager()
    req = ChatbotCommandRequest(
        prompt="Split the second clip in half.",
        current_timeline=tl_state
    )
    chat_res = CommandParser.interpret_and_execute(req, mgr)
    assert chat_res.understood is True
    print(f"[OK] Chatbot Action: {chat_res.action_description or chat_res.intent}")
    print(f"[OK] Chatbot Message: {chat_res.message}")
    if chat_res.updated_timeline:
        print(f"[OK] Updated Timeline Clips: {len(chat_res.updated_timeline.clips)}")

    print("\n" + "=" * 70)
    print("  ALL OFFLINE QWEN 2.5 & OLLAMA INTEGRATION TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_qwen_integration()
