"""Data models for user-video interactions."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of user-video interactions."""

    CLICK = "CLICK"
    WATCH_PROGRESS = "WATCH_PROGRESS"
    LIKE = "LIKE"
    COMPLETE = "COMPLETE"
    SKIP = "SKIP"


class Device(str, Enum):
    """Device types for context."""

    MOBILE = "MOBILE"
    DESKTOP = "DESKTOP"
    TV = "TV"


class VideoInteraction(BaseModel):
    """Schema for user-video interaction events."""

    user_id: UUID = Field(..., description="User performing the interaction")
    video_id: UUID = Field(..., description="Video being interacted with")
    event_type: EventType = Field(..., description="Type of interaction")
    watch_time: Optional[int] = Field(
        None, description="Seconds watched (if applicable)"
    )
    duration: Optional[int] = Field(
        None, description="Total video duration in seconds"
    )
    device: Device = Field(..., description="Device type for context")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the interaction occurred",
    )

    def completion_percentage(self) -> Optional[float]:
        """Calculate video completion percentage."""
        if self.duration and self.watch_time:
            return round((self.watch_time / self.duration) * 100, 2)
        return None

    class Config:
        use_enum_values = True


class InteractionMetrics(BaseModel):
    """Aggregated metrics for a user-video pair."""

    user_id: UUID
    video_id: UUID
    total_watch_time: int = Field(default=0, description="Total seconds watched")
    watch_count: int = Field(default=0, description="Number of watch events")
    like_count: int = Field(default=0, description="Number of likes")
    last_watched: Optional[datetime] = Field(None, description="Last watch time")
    completion_rate: float = Field(default=0.0, description="Percentage completed")
    engagement_score: float = Field(
        default=0.0, description="Computed engagement metric"
    )

    class Config:
        use_enum_values = True
