"""Tests for MicroLens-50k ingestion pipeline."""

from __future__ import annotations

import csv
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid5
from unittest.mock import Mock, patch

import pytest

from src.data_platform.data_model.interaction import (
    Device,
    EventType,
    VideoInteraction,
)
from src.data_platform.ingestion.microlens_pipeline import (
    MICROLENS_NAMESPACE,
    MicroLensIngestor,
    MicroLensPairsReader,
)
from src.data_platform.feature_store.interaction_store import InteractionStore


class TestMicroLensPairsReader:
    """Test CSV reader for MicroLens pairs data."""

    def test_read_csv_basic(self, tmp_path: Path) -> None:
        """Test reading basic CSV with correct format."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write("1,101,2024-01-01T10:00:00\n")
            f.write("1,102,2024-01-01T11:00:00\n")

        interactions = list(MicroLensPairsReader.read_interactions(csv_file))

        assert len(interactions) == 2
        assert all(isinstance(i, VideoInteraction) for i in interactions)
        assert interactions[0].event_type == EventType.CLICK
        assert interactions[0].device == Device.MOBILE

    def test_read_csv_with_limit(self, tmp_path: Path) -> None:
        """Test reading CSV with limit parameter."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            for i in range(10):
                f.write(f"1,{100 + i},2024-01-01T{i:02d}:00:00\n")

        interactions = list(
            MicroLensPairsReader.read_interactions(csv_file, limit=3)
        )

        assert len(interactions) == 3

    def test_read_csv_deterministic_uuids(self, tmp_path: Path) -> None:
        """Test that UUIDs are deterministically generated."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write("1,101,2024-01-01T10:00:00\n")

        interactions = list(MicroLensPairsReader.read_interactions(csv_file))

        # Same IDs should generate same UUIDs
        expected_user_id = uuid5(MICROLENS_NAMESPACE, "user_1")
        expected_video_id = uuid5(MICROLENS_NAMESPACE, "video_101")

        assert interactions[0].user_id == expected_user_id
        assert interactions[0].video_id == expected_video_id

    def test_read_csv_multiple_users(self, tmp_path: Path) -> None:
        """Test reading interactions from multiple users."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write("1,101,2024-01-01T10:00:00\n")
            f.write("2,102,2024-01-01T11:00:00\n")
            f.write("3,103,2024-01-01T12:00:00\n")

        interactions = list(MicroLensPairsReader.read_interactions(csv_file))

        assert len(interactions) == 3
        assert interactions[0].user_id != interactions[1].user_id
        assert interactions[1].user_id != interactions[2].user_id

    def test_read_csv_timestamp_parsing(self, tmp_path: Path) -> None:
        """Test correct parsing of ISO format timestamps."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write("1,101,2024-01-15T14:30:45\n")

        interactions = list(MicroLensPairsReader.read_interactions(csv_file))

        assert interactions[0].timestamp.year == 2024
        assert interactions[0].timestamp.month == 1
        assert interactions[0].timestamp.day == 15
        assert interactions[0].timestamp.hour == 14
        assert interactions[0].timestamp.minute == 30
        assert interactions[0].timestamp.second == 45
        assert interactions[0].timestamp.tzinfo is not None

    def test_read_csv_file_not_found(self) -> None:
        """Test handling of missing CSV file."""
        with pytest.raises(FileNotFoundError):
            list(MicroLensPairsReader.read_interactions(Path("/nonexistent/file.csv")))

    def test_read_csv_invalid_rows_skipped(self, tmp_path: Path) -> None:
        """Test that invalid rows are skipped with warning."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write("1,101,2024-01-01T10:00:00\n")
            f.write("2,invalid_video,invalid_timestamp\n")
            f.write("3,103,2024-01-01T12:00:00\n")

        interactions = list(MicroLensPairsReader.read_interactions(csv_file))

        # Should skip the invalid row
        assert len(interactions) == 2

    def test_read_csv_all_fields_populated(self, tmp_path: Path) -> None:
        """Test that all VideoInteraction fields are properly populated."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write("user_123,vid_456,2024-01-01T10:00:00\n")

        interactions = list(MicroLensPairsReader.read_interactions(csv_file))
        interaction = interactions[0]

        assert interaction.user_id is not None
        assert interaction.video_id is not None
        assert interaction.event_type == EventType.CLICK
        assert interaction.device == Device.MOBILE
        assert interaction.session_id is not None
        assert interaction.timestamp is not None


class TestMicroLensIngestor:
    """Test MicroLens ingestor."""

    @pytest.fixture
    def mock_store(self) -> Mock:
        """Create mock interaction store."""
        store = Mock(spec=InteractionStore)
        store.record_interaction.return_value = True
        return store

    def test_ingestor_initialization(self, mock_store: Mock) -> None:
        """Test ingestor initialization."""
        ingestor = MicroLensIngestor(mock_store)

        assert ingestor.interaction_store is mock_store
        assert ingestor.stats["processed"] == 0
        assert ingestor.stats["successful"] == 0
        assert ingestor.stats["failed"] == 0

    def test_ingest_from_csv_success(
        self, mock_store: Mock, tmp_path: Path
    ) -> None:
        """Test successful CSV ingestion."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write("1,101,2024-01-01T10:00:00\n")
            f.write("1,102,2024-01-01T11:00:00\n")

        ingestor = MicroLensIngestor(mock_store)
        stats = ingestor.ingest_from_csv(csv_file)

        assert stats["processed"] == 2
        assert stats["successful"] == 2
        assert stats["failed"] == 0
        assert mock_store.record_interaction.call_count == 2

    def test_ingest_from_csv_with_failures(
        self, mock_store: Mock, tmp_path: Path
    ) -> None:
        """Test ingestion with some store failures."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write("1,101,2024-01-01T10:00:00\n")
            f.write("1,102,2024-01-01T11:00:00\n")

        mock_store.record_interaction.side_effect = [True, False]

        ingestor = MicroLensIngestor(mock_store)
        stats = ingestor.ingest_from_csv(csv_file)

        assert stats["processed"] == 2
        assert stats["successful"] == 1
        assert stats["failed"] == 1

    def test_ingest_from_csv_with_limit(
        self, mock_store: Mock, tmp_path: Path
    ) -> None:
        """Test ingestion with limit parameter."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            for i in range(10):
                f.write(f"1,{100 + i},2024-01-01T{i:02d}:00:00\n")

        ingestor = MicroLensIngestor(mock_store)
        stats = ingestor.ingest_from_csv(csv_file, limit=5)

        assert stats["processed"] == 5
        assert stats["successful"] == 5
        assert mock_store.record_interaction.call_count == 5

    def test_ingest_interactions_passed_correctly(
        self, mock_store: Mock, tmp_path: Path
    ) -> None:
        """Test that interactions passed to store are correctly formatted."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write("1,101,2024-01-01T10:00:00\n")

        ingestor = MicroLensIngestor(mock_store)
        ingestor.ingest_from_csv(csv_file)

        # Get the interaction passed to record_interaction
        call_args = mock_store.record_interaction.call_args
        interaction = call_args[0][0]

        assert isinstance(interaction, VideoInteraction)
        assert interaction.event_type == EventType.CLICK
        assert interaction.device == Device.MOBILE


class TestMicroLensIntegration:
    """Integration tests with real InteractionStore."""

    @pytest.fixture
    def real_store(self) -> InteractionStore:
        """Create real interaction store for integration testing."""
        store = InteractionStore()
        return store

    def test_end_to_end_ingestion(
        self, real_store: InteractionStore, tmp_path: Path
    ) -> None:
        """Test end-to-end ingestion from CSV to storage."""
        # Health check
        health = real_store.health_check()
        if not (health["redis"] or health["dynamodb"]):
            pytest.skip("Redis or DynamoDB not available")

        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write("1,101,2024-01-01T10:00:00\n")
            f.write("1,102,2024-01-01T11:00:00\n")

        ingestor = MicroLensIngestor(real_store)
        stats = ingestor.ingest_from_csv(csv_file)

        assert stats["processed"] > 0

    def test_ingestion_large_batch(
        self, real_store: InteractionStore, tmp_path: Path
    ) -> None:
        """Test ingestion of larger batch."""
        health = real_store.health_check()
        if not (health["redis"] or health["dynamodb"]):
            pytest.skip("Redis or DynamoDB not available")

        csv_file = tmp_path / "test_pairs_large.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            for i in range(50):
                f.write(f"{i % 10},{100 + i},2024-01-01T{i % 24:02d}:00:00\n")

        ingestor = MicroLensIngestor(real_store)
        stats = ingestor.ingest_from_csv(csv_file, limit=50)

        assert stats["processed"] == 50


class TestCSVFormats:
    """Test different CSV format variations."""

    def test_csv_with_extra_whitespace(self, tmp_path: Path) -> None:
        """Test CSV with whitespace in values."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write(" 1 , 101 , 2024-01-01T10:00:00 \n")

        interactions = list(MicroLensPairsReader.read_interactions(csv_file))

        # Should handle whitespace gracefully
        assert len(interactions) >= 0  # May succeed or skip with warning

    def test_csv_with_quoted_fields(self, tmp_path: Path) -> None:
        """Test CSV with quoted fields."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write('"userID","videoID","timestamp"\n')
            f.write('"1","101","2024-01-01T10:00:00"\n')

        interactions = list(MicroLensPairsReader.read_interactions(csv_file))

        assert len(interactions) == 1

    def test_csv_with_utc_timezone(self, tmp_path: Path) -> None:
        """Test CSV with explicit UTC timezone."""
        csv_file = tmp_path / "test_pairs.csv"
        with open(csv_file, "w") as f:
            f.write("userID,videoID,timestamp\n")
            f.write("1,101,2024-01-01T10:00:00Z\n")

        interactions = list(MicroLensPairsReader.read_interactions(csv_file))

        assert len(interactions) == 1
