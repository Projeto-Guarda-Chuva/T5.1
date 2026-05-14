import json
import os
from typing import List, Dict, Optional

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "videos.json")

def _load_videos() -> List[Dict]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def _save_videos(videos: List[Dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2)

def get_videos_by_email(email: str) -> List[Dict]:
    return [v for v in _load_videos() if v.get("participant_email") == email]

def get_unclaimed_videos() -> List[Dict]:
    return [v for v in _load_videos() if not v.get("participant_email")]

def update_video_participant(video_id: str, email: str) -> Optional[Dict]:
    videos = _load_videos()
    for v in videos:
        if v["id"] == video_id:
            v["participant_email"] = email
            _save_videos(videos)
            return v
    return None