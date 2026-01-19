"""Structured user data model backed by Pydantic validation."""

from __future__ import annotations

from typing import Dict, List, Sequence
from uuid import UUID

from pydantic import BaseModel, Field


Embedding = Sequence[float]
CreatorID = str


class Demographics(BaseModel):
    """Describes relatively static user attributes."""

    age: int = Field(..., ge=0, le=120)
    gender: str = Field(..., min_length=1)
    primary_language: str = Field(..., min_length=2, max_length=8)
    geographic_location: str = Field(..., min_length=2)


class ContextualState(BaseModel):
    """Captures ephemeral user context needed for short-term personalization."""

    device: str = Field(..., min_length=1)
    time_of_day: str = Field(..., min_length=1)
    network_conditions: str = Field(..., min_length=1)


class HistoricalAggregations(BaseModel):
    """Holds rolling counts that backfill the feature store."""

    videos_watched_last_24h: int = Field(..., ge=0)
    top_categories: List[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    """Canonical representation of a user entity in the system."""

    user_id: UUID
    demographics: Demographics
    subscriptions: List[CreatorID] = Field(default_factory=list)
    user_embedding: Embedding = Field(..., min_length=1)
    contextual_state: ContextualState
    historical_aggs: HistoricalAggregations

    def to_feature_payload(self) -> Dict[str, object]:
        """Flatten the user for downstream storage/serving layers."""

        return self.model_dump(mode="json")
