from app.main import calculate_metrics
from app.models import WatchEvent, WatchSession


def make_session(sid, duration, events):
    s = WatchSession(id=sid, video_id="abc", video_duration=duration)
    s.events = [
        WatchEvent(session_id=sid, event_type=event_type, previous_position=a, position=b, duration=duration)
        for event_type, a, b in events
    ]
    return s


def progress_session(sid, duration, intervals):
    return make_session(sid, duration, [("progress", a, b) for a, b in intervals])


def test_union_does_not_double_count_rewinds():
    metrics = calculate_metrics([progress_session("s1", 20, [(0, 10), (0, 5), (10, 15)])])
    assert metrics["total_watch_time"] == 15
    assert metrics["average_percent_watched"] == 75


def test_completion_rate_uses_effective_watch_time():
    metrics = calculate_metrics([progress_session("s1", 10, [(0, 10)]), progress_session("s2", 10, [(0, 3)])])
    assert metrics["completion_rate"] == 50
    assert metrics["session_count"] == 2


def test_early_abandonment_does_not_make_max_position_the_duration():
    metrics = calculate_metrics([progress_session("s1", 300, [(0, 10), (10, 20), (20, 30)])])
    assert metrics["total_watch_time"] == 30
    assert metrics["average_percent_watched"] == 10
    assert metrics["completion_rate"] == 0


def test_pause_counts_final_positive_plausible_interval():
    metrics = calculate_metrics([make_session("s1", 60, [("progress", 0, 5), ("pause", 5, 8)])])
    assert metrics["total_watch_time"] == 8


def test_seek_does_not_count_skipped_interval():
    metrics = calculate_metrics([make_session("s1", 120, [("progress", 0, 5), ("seek", 5, 60), ("progress", 60, 65)])])
    assert metrics["total_watch_time"] == 10
    assert metrics["average_percent_watched"] == 8.33
