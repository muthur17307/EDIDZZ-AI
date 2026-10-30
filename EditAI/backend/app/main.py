import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, UPLOAD_DIR, EXPORT_DIR, SAMPLE_DIR, THUMBNAIL_DIR
from app.routes import media, analysis, chatbot, timeline, export, projects, assembly, pipeline

app = FastAPI(
    title="AI Video Studio Backend",
    description="Intelligent AI-Powered Video Editing API",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static media directories
app.mount("/media_files/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/media_files/exports", StaticFiles(directory=str(EXPORT_DIR)), name="exports")
app.mount("/media_files/sample_media", StaticFiles(directory=str(SAMPLE_DIR)), name="sample_media")
app.mount("/media_files/thumbnails", StaticFiles(directory=str(THUMBNAIL_DIR)), name="thumbnails")

# Register API routes
app.include_router(media.router)
app.include_router(analysis.router)
app.include_router(chatbot.router)
app.include_router(timeline.router)
app.include_router(export.router)
app.include_router(projects.router)
app.include_router(assembly.router)
app.include_router(pipeline.router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": "AI Video Studio API",
        "directories": {
            "uploads": str(UPLOAD_DIR),
            "exports": str(EXPORT_DIR)
        }
    }

# Mount built frontend dist if available
frontend_dist = BASE_DIR.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
