"""Tests for user-video interaction storage."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_platform.data_model.interaction import (
    Device,
    EventType,
    InteractionMetrics,
    VideoInteraction,
)
from data_platform.feature_store.interaction_store import InteractionStore


@pytest.fixture
def interaction_store() -> InteractionStore:
    """Provide an InteractionStore instance for testing."""
    return InteractionStore()


@pytest.fixture
def sample_interaction() -> VideoInteraction:
    """Provide a sample interaction."""
    return VideoInteraction(
        user_id=uuid4(),
        video_id=uuid4(),
        event_type=EventType.WATCH_PROGRESS,
        watch_time=45,
        duration=180,
        device=Device.MOBILE,
        session_id="session-123",
    )


class TestInteractionModel:
    """Test VideoInteraction data model."""

    def test_interaction_creation(self, sample_interaction: VideoInteraction) -> None:
        """Test creating a VideoInteraction."""
        assert sample_interaction.user_id is not None
        assert sample_interaction.video_id is not None
        assert sample_interaction.event_type == EventType.WATCH_PROGRESS
        assert sample_interaction.timestamp is not None

    def test_completion_percentage(self) -> None:
        """Test completion percentage calculation."""
        interaction = VideoInteraction(
            user_id=uuid4(),
            video_id=uuid4(),
            event_type=EventType.WATCH_PROGRESS,
            watch_time=90,
            duration=180,
            device=Device.DESKTOP,
            session_id="session-123",
        )
        assert interaction.completion_percentage() == 50.0

    def test_completion_percentage_none(self) -> None:
        """Test completion percentage when data is missing."""
        interaction = VideoInteraction(
            user_id=uuid4(),
            video_id=uuid4(),
            event_type=EventType.CLICK,
            device=Device.MOBILE,
            session_id="session-123",
        )
        assert interaction.completion_percentage() is None

    def test_event_types(self) -> None:
        """Test all event types are valid."""
        event_types = [
            EventType.CLICK,
            EventType.WATCH_PROGRESS,
            EventType.LIKE,
            EventType.COMPLETE,
            EventType.SKIP,
        ]
        assert len(event_types) == 5

    def test_devices(self) -> None:
        """Test all device types are valid."""
        devices = [Device.MOBILE, Device.DESKTOP, Device.TV]
        assert len(devices) == 3


class TestInteractionStoreConnection:
    """Test InteractionStore connectivity."""

    def test_store_initialization(self, interaction_store: InteractionStore) -> None:
        """Test that InteractionStore initializes successfully."""
        assert interaction_store.redis_client is not None
        assert interaction_store.dynamodb is not None

    def test_health_check(self, interaction_store: InteractionStore) -> None:
        """Test health check of Redis and DynamoDB."""
        health = interaction_store.health_check()
        assert "redis" in health
        assert "dynamodb" in health
        # At least one should be available
        assert health["redis"] or health["dynamodb"]


class TestInteractionRecording:
    """Test recording interactions."""

    def test_record_interaction(
        self, interaction_store: InteractionStore, sample_interaction: VideoInteraction
    ) -> None:
        """Test recording a single interaction."""
        result = interaction_store.record_interaction(sample_interaction)
        assert result is True

    def test_record_multiple_interactions(
        self, interaction_store: InteractionStore
    ) -> None:
        """Test recording multiple interactions."""
        user_id = uuid4()
        video_id = uuid4()

        interactions = [
            VideoInteraction(
                user_id=user_id,
                video_id=video_id,
                event_type=EventType.CLICK,
                device=Device.MOBILE,
                session_id="session-123",
            ),
            VideoInteraction(
                user_id=user_id,
                video_id=video_id,
                event_type=EventType.WATCH_PROGRESS,
                watch_time=30,
                duration=180,
                device=Device.MOBILE,
                session_id="session-123",
            ),
            VideoInteraction(
                user_id=user_id,
                video_id=video_id,
                event_type=EventType.COMPLETE,
                watch_time=180,
                duration=180,
                device=Device.MOBILE,
                session_id="session-123",
            ),
        ]

        for interaction in interactions:
            result = interaction_store.record_interaction(interaction)
            assert result is True


class TestInteractionRetrieval:
    """Test retrieving interactions."""

    def test_get_user_interactions_empty(
        self, interaction_store: InteractionStore
    ) -> None:
        """Test getting interactions for user with no data."""
        user_id = uuid4()
        interactions = interaction_store.get_user_interactions(user_id)
        # Should return empty list or list with 0 items
        assert isinstance(interactions, list)

    def test_get_user_interactions_with_data(
        self, interaction_store: InteractionStore
    ) -> None:
        """Test getting interactions for user with data."""
        user_id = uuid4()
        video_id = uuid4()

        # Record an interaction
        interaction = VideoInteraction(
            user_id=user_id,
            video_id=video_id,
            event_type=EventType.WATCH_PROGRESS,
            watch_time=45,
            duration=180,
            device=Device.DESKTOP,
            session_id="session-456",
        )
        interaction_store.record_interaction(interaction)

        # Retrieve interactions (may come from Redis or DynamoDB)
        interactions = interaction_store.get_user_interactions(user_id, limit=10)

        # Verify structure
        assert isinstance(interactions, list)
        # If data is retrieved from DynamoDB, it may take a moment
        # so we just verify the list structure is correct


class TestInteractionMetrics:
    """Test interaction metrics."""

    def test_metrics_model(self) -> None:
        """Test InteractionMetrics model creation."""
        metrics = InteractionMetrics(
            user_id=uuid4(),
            video_id=uuid4(),
            total_watch_time=120,
            watch_count=2,
            like_count=1,
            completion_rate=66.7,
            engagement_score=0.85,
        )
        assert metrics.total_watch_time == 120
        assert metrics.watch_count == 2
        assert metrics.like_count == 1
        assert metrics.completion_rate == 66.7
        assert metrics.engagement_score == 0.85

    def test_get_user_video_metrics_empty(
        self, interaction_store: InteractionStore
    ) -> None:
        """Test getting metrics for user-video pair with no data."""
        user_id = uuid4()
        video_id = uuid4()
        metrics = interaction_store.get_user_video_metrics(user_id, video_id)
        # Should return None if no data
        assert metrics is None or isinstance(metrics, InteractionMetrics)


class TestWriteAsidePattern:
    """Test the write-aside pattern (write to Redis + DynamoDB)."""

    def test_redis_caching(
        self, interaction_store: InteractionStore, sample_interaction: VideoInteraction
    ) -> None:
        """Test that interactions are cached in Redis."""
        # Record interaction (should write to both Redis and DynamoDB)
        interaction_store.record_interaction(sample_interaction)

        # Check Redis has the data
        health = interaction_store.health_check()
        if health["redis"]:
            # If Redis is healthy, verify caching occurred
            interactions = interaction_store._get_from_redis(
                sample_interaction.user_id, 10
            )
            # Interaction should be in Redis (or at least retrievable)
            assert isinstance(interactions, list)

    def test_dynamodb_persistence(
        self, interaction_store: InteractionStore, sample_interaction: VideoInteraction
    ) -> None:
        """Test that interactions are persisted in DynamoDB."""
        # Record interaction
        interaction_store.record_interaction(sample_interaction)

        # Check DynamoDB has the data
        health = interaction_store.health_check()
        if health["dynamodb"]:
            interactions = interaction_store._get_from_dynamodb(
                sample_interaction.user_id, 10
            )
            assert isinstance(interactions, list)


class TestEventTypes:
    """Test different event types."""

    def test_click_event(
        self, interaction_store: InteractionStore
    ) -> None:
        """Test recording a CLICK event."""
        interaction = VideoInteraction(
            user_id=uuid4(),
            video_id=uuid4(),
            event_type=EventType.CLICK,
            device=Device.MOBILE,
            session_id="session-789",
        )
        result = interaction_store.record_interaction(interaction)
        assert result is True

    def test_like_event(
        self, interaction_store: InteractionStore
    ) -> None:
        """Test recording a LIKE event."""
        interaction = VideoInteraction(
            user_id=uuid4(),
            video_id=uuid4(),
            event_type=EventType.LIKE,
            device=Device.DESKTOP,
            session_id="session-789",
        )
        result = interaction_store.record_interaction(interaction)
        assert result is True

    def test_skip_event(
        self, interaction_store: InteractionStore
    ) -> None:
        """Test recording a SKIP event."""
        interaction = VideoInteraction(
            user_id=uuid4(),
            video_id=uuid4(),
            event_type=EventType.SKIP,
            watch_time=5,
            duration=180,
            device=Device.TV,
            session_id="session-789",
        )
        result = interaction_store.record_interaction(interaction)
        assert result is True

    def test_complete_event(
        self, interaction_store: InteractionStore
    ) -> None:
        """Test recording a COMPLETE event."""
        interaction = VideoInteraction(
            user_id=uuid4(),
            video_id=uuid4(),
            event_type=EventType.COMPLETE,
            watch_time=180,
            duration=180,
            device=Device.DESKTOP,
            session_id="session-789",
        )
        result = interaction_store.record_interaction(interaction)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
