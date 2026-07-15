import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_create_session_and_record_event():
    response = client.post("/api/sessions", json={"video_id": "abc123", "video_duration": 60})
    assert response.status_code == 201
    sid = response.json()["id"]
    event = client.post(f"/api/sessions/{sid}/events", json={"event_type": "progress", "position": 5, "previous_position": 0, "duration": 60})
    assert event.status_code == 201
    metrics = client.get("/api/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["total_watch_time"] >= 5


def test_reject_invalid_video_id():
    response = client.post("/api/sessions", json={"video_id": "bad id", "video_duration": 60})
    assert response.status_code == 422


def test_update_session_duration_with_in_memory_sqlite_testclient():
    response = client.post("/api/sessions", json={"video_id": "abc123", "video_duration": 0})
    assert response.status_code == 201
    sid = response.json()["id"]

    update = client.patch(f"/api/sessions/{sid}/duration", json={"video_duration": 300})
    assert update.status_code == 200
    assert update.json()["video_duration"] == 300

    event = client.post(f"/api/sessions/{sid}/events", json={"event_type": "progress", "position": 30, "previous_position": 20, "duration": 300})
    assert event.status_code == 201
    metrics = client.get("/api/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["average_percent_watched"] == 3.33
