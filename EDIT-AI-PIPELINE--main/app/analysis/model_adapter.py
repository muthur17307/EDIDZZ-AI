
import json
import os
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


def ask_qwen(prompt: str) -> dict:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AI video editing assistant. "
                        "Return valid JSON only. Do not invent "
                        "clip IDs, timestamps, or events."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=600,
    )
    response.raise_for_status()

    content = response.json()["message"]["content"]
    result = json.loads(content)

    if not isinstance(result, dict):
        raise ValueError("Qwen must return a JSON object")

    return result


def plan_global_edit(brief: str, analyses: list[dict]) -> dict:
    prompt = f"""
Create one coherent video edit from these analyzed clips.

CLIENT BRIEF:
{brief}

ALL CLIP ANALYSES:
{json.dumps(analyses, ensure_ascii=False)}

Requirements:
- Order segments into one logical story.
- Detect repeated statements across different clips.
- Keep the clearest complete version of repeated information.
- Preserve unique facts and necessary context.
- Use only supplied clip IDs and timestamps.
- Flag uncertain editing decisions for human review.

Return this JSON structure:
{{
  "story_summary": "...",
  "ordered_segments": [
    {{
      "clip_id": "clip_001",
      "start": 0.0,
      "end": 5.0,
      "decision": "keep",
      "reason": "...",
      "story_role": "introduction"
    }}
  ],
  "review_items": []
}}
"""
    return ask_qwen(prompt)
