import json
import os
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import WatchEvent, WatchSession
from .schemas import EventCreate, MetricsOut, SessionCreate, SessionDurationUpdate, SessionOut

Base.metadata.create_all(bind=engine)
app = FastAPI(title="YouTube Watchtime Lab")
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/dashboard")
def dashboard_page():
    return FileResponse(STATIC_DIR / "dashboard.html")

@app.get("/api/config")
def config():
    return {"default_video_id": os.getenv("DEFAULT_YOUTUBE_VIDEO_ID", "dQw4w9WgXcQ")}

@app.post("/api/sessions", response_model=SessionOut, status_code=201)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    session = WatchSession(id=str(uuid.uuid4()), video_id=payload.video_id, video_duration=payload.video_duration)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@app.patch("/api/sessions/{session_id}/duration", response_model=SessionOut)
def update_session_duration(session_id: str, payload: SessionDurationUpdate, db: Session = Depends(get_db)):
    session = db.get(WatchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    session.video_duration = payload.video_duration
    db.commit()
    db.refresh(session)
    return session

@app.post("/api/sessions/{session_id}/events", status_code=201)
def record_event(session_id: str, payload: EventCreate, db: Session = Depends(get_db)):
    session = db.get(WatchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if payload.duration > 0:
        session.video_duration = payload.duration
    if payload.event_type == "ended":
        session.ended_at = datetime.utcnow()
    event = WatchEvent(
        session_id=session_id,
        event_type=payload.event_type,
        position=payload.position,
        previous_position=payload.previous_position,
        duration=payload.duration,
        meta=json.dumps(payload.meta) if payload.meta else None,
    )
    db.add(event)
    db.commit()
    return {"ok": True}

def _watched_intervals(events: list[WatchEvent]) -> list[tuple[float, float]]:
    intervals = []
    for event in events:
        if event.event_type not in {"progress", "pause", "buffering", "ended"} or event.previous_position is None:
            continue
        start, end = event.previous_position, event.position
        if end - start > 0 and end - start <= 15:
            intervals.append((start, end))
    return intervals

def _union_seconds(intervals: list[tuple[float, float]]) -> float:
    if not intervals:
        return 0.0
    merged = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return round(sum(end - start for start, end in merged), 2)

def calculate_metrics(sessions: list[WatchSession]) -> dict:
    session_count = len(sessions)
    per_session = []
    retention = defaultdict(int)
    completions = 0
    for session in sessions:
        intervals = _watched_intervals(sorted(session.events, key=lambda e: e.occurred_at or datetime.min))
        watched = _union_seconds(intervals)
        per_session.append(watched)
        duration = session.video_duration
        if duration and watched / duration >= 0.9:
            completions += 1
        covered = set()
        for start, end in intervals:
            bucket = int(start // 5) * 5
            while bucket < end:
                covered.add(bucket)
                bucket += 5
        for bucket in covered:
            retention[bucket] += 1
    total = round(sum(per_session), 2)
    avg = round(total / session_count, 2) if session_count else 0
    avg_pct_values = []
    for session, watched in zip(sessions, per_session):
        duration = session.video_duration
        avg_pct_values.append((watched / duration * 100) if duration else 0)
    curve = [{"bucket": b, "viewers": retention[b], "percent": round(retention[b] / session_count * 100, 2) if session_count else 0} for b in sorted(retention)]
    dropoffs = []
    for current, nxt in zip(curve, curve[1:]):
        loss = current["viewers"] - nxt["viewers"]
        if loss > 0:
            dropoffs.append({"bucket": nxt["bucket"], "lost_viewers": loss})
    return {
        "total_watch_time": total,
        "average_watch_time": avg,
        "average_percent_watched": round(sum(avg_pct_values) / session_count, 2) if session_count else 0,
        "completion_rate": round(completions / session_count * 100, 2) if session_count else 0,
        "session_count": session_count,
        "retention_curve": curve,
        "dropoff_points": sorted(dropoffs, key=lambda d: d["lost_viewers"], reverse=True)[:5],
    }

@app.get("/api/metrics", response_model=MetricsOut)
def metrics(video_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(WatchSession)
    if video_id:
        query = query.filter(WatchSession.video_id == video_id)
    return calculate_metrics(query.all())
