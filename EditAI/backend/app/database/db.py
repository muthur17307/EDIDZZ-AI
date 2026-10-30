import os
import json
import sqlite3
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "editmind.db"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Projects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        settings TEXT NOT NULL DEFAULT '{}'
    )
    """)

    # Media Assets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS media_assets (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        media_type TEXT NOT NULL,
        duration REAL DEFAULT 0.0,
        width INTEGER DEFAULT 0,
        height INTEGER DEFAULT 0,
        fps REAL DEFAULT 0.0,
        size_bytes INTEGER DEFAULT 0,
        metadata_json TEXT DEFAULT '{}',
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
    """)

    # Timeline Clips Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timeline_clips (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        track_id TEXT NOT NULL DEFAULT 'V1',
        source_file TEXT NOT NULL,
        source_filename TEXT NOT NULL,
        source_start REAL NOT NULL,
        source_end REAL NOT NULL,
        timeline_start REAL NOT NULL,
        timeline_end REAL NOT NULL,
        duration REAL NOT NULL,
        name TEXT NOT NULL,
        speed REAL DEFAULT 1.0,
        volume REAL DEFAULT 1.0,
        color TEXT DEFAULT '#2b3648',
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
    """)

    # Subtitles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subtitles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        text TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
    """)

    # Edit History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS edit_history (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        action_desc TEXT NOT NULL,
        snapshot_json TEXT NOT NULL,
        timestamp REAL NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()

# Database CRUD Operations
class ProjectDB:
    @staticmethod
    def create_project(name: str = "New Project 1", settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        proj_id = f"proj_{uuid.uuid4().hex[:10]}"
        settings_str = json.dumps(settings or {"fps": 25.0, "resolution": "1080p", "aspect_ratio": "16:9"})
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO projects (id, name, settings) VALUES (?, ?, ?)", (proj_id, name, settings_str))
        conn.commit()
        conn.close()
        return {"id": proj_id, "name": name, "settings": json.loads(settings_str)}

    @staticmethod
    def list_projects() -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, created_at, updated_at, settings FROM projects ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        projects = []
        for r in rows:
            projects.append({
                "id": r["id"],
                "name": r["name"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "settings": json.loads(r["settings"])
            })
        conn.close()
        return projects

    @staticmethod
    def get_project(proj_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (proj_id,))
        p = cursor.fetchone()
        if not p:
            conn.close()
            return None

        # Fetch media assets
        cursor.execute("SELECT * FROM media_assets WHERE project_id = ?", (proj_id,))
        media = [dict(m) for m in cursor.fetchall()]

        # Fetch clips
        cursor.execute("SELECT * FROM timeline_clips WHERE project_id = ? ORDER BY timeline_start ASC", (proj_id,))
        clips = [dict(c) for c in cursor.fetchall()]

        # Fetch subtitles
        cursor.execute("SELECT id, start_time, end_time, text FROM subtitles WHERE project_id = ? ORDER BY start_time ASC", (proj_id,))
        subs = [dict(s) for s in cursor.fetchall()]

        # Fetch history
        cursor.execute("SELECT action_desc, timestamp FROM edit_history WHERE project_id = ? ORDER BY timestamp DESC LIMIT 20", (proj_id,))
        history = [dict(h) for h in cursor.fetchall()]

        conn.close()

        total_dur = round(max((c["timeline_end"] for c in clips), default=0.0), 3)

        return {
            "id": p["id"],
            "name": p["name"],
            "settings": json.loads(p["settings"]),
            "media_assets": media,
            "timeline": {
                "clips": clips,
                "total_duration": total_dur,
                "subtitles": subs,
                "playhead_time": 0.0
            },
            "history": history
        }

    @staticmethod
    def save_project(proj_id: str, name: str, settings: Dict[str, Any], clips: List[Dict[str, Any]], subtitles: List[Dict[str, Any]]):
        conn = get_connection()
        cursor = conn.cursor()

        # Insert or update project record (upsert)
        cursor.execute("""
        INSERT INTO projects (id, name, settings, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            settings = excluded.settings,
            updated_at = CURRENT_TIMESTAMP
        """, (proj_id, name, json.dumps(settings)))

        # Replace timeline clips
        cursor.execute("DELETE FROM timeline_clips WHERE project_id = ?", (proj_id,))
        for idx, c in enumerate(clips):
            cursor.execute("""
            INSERT OR REPLACE INTO timeline_clips (id, project_id, track_id, source_file, source_filename, source_start, source_end, timeline_start, timeline_end, duration, name, speed, volume, color, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c.get("id", f"clip_{uuid.uuid4().hex[:8]}"),
                proj_id,
                c.get("track_id", "V1"),
                c.get("source_file", ""),
                c.get("source_filename", ""),
                c.get("source_start", 0.0),
                c.get("source_end", c.get("duration", 0.0)),
                c.get("timeline_start", 0.0),
                c.get("timeline_end", c.get("duration", 0.0)),
                c.get("duration", 0.0),
                c.get("name", "Clip"),
                c.get("speed", 1.0),
                c.get("volume", 1.0),
                c.get("color", "#2b3648"),
                idx
            ))

        # Replace subtitles
        cursor.execute("DELETE FROM subtitles WHERE project_id = ?", (proj_id,))
        for s in subtitles:
            cursor.execute("INSERT INTO subtitles (project_id, start_time, end_time, text) VALUES (?, ?, ?, ?)",
                           (proj_id, s.get("start_time", 0.0), s.get("end_time", 0.0), s.get("text", "")))

        conn.commit()
        conn.close()

# Initialize database on module load
init_db()
