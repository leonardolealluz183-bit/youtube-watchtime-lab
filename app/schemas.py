from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

EventType = Literal["play", "pause", "seek", "buffering", "progress", "ended"]

class SessionCreate(BaseModel):
    video_id: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    video_duration: float = Field(default=0, ge=0, le=86400)

class SessionOut(BaseModel):
    id: str
    video_id: str
    video_duration: float
    started_at: datetime

class SessionDurationUpdate(BaseModel):
    video_duration: float = Field(gt=0, le=86400)

class EventCreate(BaseModel):
    event_type: EventType
    position: float = Field(ge=0, le=86400)
    previous_position: float | None = Field(default=None, ge=0, le=86400)
    duration: float = Field(default=0, ge=0, le=86400)
    meta: dict[str, Any] | None = None

    @field_validator("previous_position")
    @classmethod
    def finite_previous(cls, value):
        return value

class MetricsOut(BaseModel):
    total_watch_time: float
    average_watch_time: float
    average_percent_watched: float
    completion_rate: float
    session_count: int
    retention_curve: list[dict[str, float | int]]
    dropoff_points: list[dict[str, float | int]]
