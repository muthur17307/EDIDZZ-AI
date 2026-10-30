import os
import sys
from pathlib import Path

# Add backend directory and standalone pipeline to sys.path
BASE_DIR = Path(__file__).resolve().parent
STANDALONE_PIPELINE = BASE_DIR.parent.parent / "EDIT-AI-PIPELINE--main"

for p in [BASE_DIR, STANDALONE_PIPELINE]:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import uvicorn

if __name__ == "__main__":
    print(f"Starting AI Video Studio Backend at http://127.0.0.1:8000 ...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
