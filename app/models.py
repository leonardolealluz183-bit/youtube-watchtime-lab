from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class WatchSession(Base):
    __tablename__ = "watch_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(String(32), index=True)
    video_duration: Mapped[float] = mapped_column(Float, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    events: Mapped[list["WatchEvent"]] = relationship(back_populates="session", cascade="all, delete-orphan")

class WatchEvent(Base):
    __tablename__ = "watch_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("watch_sessions.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    position: Mapped[float] = mapped_column(Float)
    previous_position: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration: Mapped[float] = mapped_column(Float, default=0)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)
    session: Mapped[WatchSession] = relationship(back_populates="events")
