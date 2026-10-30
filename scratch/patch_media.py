from pathlib import Path

target = Path("EditAI/backend/app/routes/media.py")
text = target.read_text(encoding="utf-8")

old_decor = """@router.post("/upload/batch")
async def upload_batch_videos(files: list[UploadFile] = File(...)):"""

new_decor = """@router.post("/upload/batch")
@router.post("/batch")
@router.post("/batch-upload")
async def upload_batch_videos(files: list[UploadFile] = File(...)):"""

if old_decor in text:
    text = text.replace(old_decor, new_decor, 1)
    target.write_text(text, encoding="utf-8")
    print("media.py patched successfully!")
else:
    print("old_decor not found in media.py")

