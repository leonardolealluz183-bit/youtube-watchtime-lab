from app.main import calculate_metrics
from app.models import WatchEvent, WatchSession

def make_session(sid, duration, intervals):
    s = WatchSession(id=sid, video_id="abc", video_duration=duration)
    s.events = [WatchEvent(session_id=sid, event_type="progress", previous_position=a, position=b, duration=duration) for a, b in intervals]
    return s

def test_union_does_not_double_count_rewinds():
    metrics = calculate_metrics([make_session("s1", 20, [(0, 10), (0, 5), (10, 15)])])
    assert metrics["total_watch_time"] == 15
    assert metrics["average_percent_watched"] == 75

def test_completion_rate_uses_effective_watch_time():
    metrics = calculate_metrics([make_session("s1", 10, [(0, 10)]), make_session("s2", 10, [(0, 3)])])
    assert metrics["completion_rate"] == 50
    assert metrics["session_count"] == 2
