"""Video entity data model backed by Pydantic validation."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Sequence
from uuid import UUID

from pydantic import BaseModel, Field


Embedding = Sequence[float]


class VideoMetadata(BaseModel):
    """Describes the editorial aspects of the video."""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    category: str = Field(default="", description="Top-level category label")


class ContentStats(BaseModel):
    """Captures objective content properties relevant for freshness and quality."""

    duration_seconds: float = Field(..., gt=0)
    resolution_height: float = Field(..., gt=0)
    resolution_width: float = Field(..., gt=0)
    upload_timestamp: datetime


class EngagementMetrics(BaseModel):
    """Aggregated counters that summarize viewer reactions."""

    view_count: int = Field(..., ge=0)
    average_view_duration: float = Field(..., ge=0)
    click_through_rate: float = Field(..., ge=0)


class VideoAsset(BaseModel):
    """Canonical representation of a video row in the platform."""

    video_id: UUID
    creator_id: UUID
    metadata: VideoMetadata
    content_stats: ContentStats
    video_embedding: Embedding = Field(...)
    engagement_metrics: EngagementMetrics

    def to_feature_payload(self) -> Dict[str, object]:
        """Flatten the video entity into a JSON-compatible payload."""

        return self.dict()
