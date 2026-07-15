import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

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
