"""Ingestion pipeline for MicroLens-50k dataset."""

from __future__ import annotations

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional
from uuid import UUID, uuid5

from ..data_model.interaction import Device, EventType, VideoInteraction
from ..feature_store.interaction_store import InteractionStore

logger = logging.getLogger(__name__)

# MicroLens-50k namespace UUID for deterministic UUID generation
MICROLENS_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


class MicroLensPairsReader:
    """Reader for MicroLens-50k_pairs.csv format (userID, videoID, timestamp)."""

    @staticmethod
    def read_interactions(
        csv_path: Path, limit: Optional[int] = None
    ) -> Generator[VideoInteraction, None, None]:
        """Read interactions from MicroLens CSV file.

        Args:
            csv_path: Path to MicroLens-50k_pairs.csv
            limit: Maximum number of interactions to read (None = all)

        Yields:
            VideoInteraction objects
        """
        count = 0
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if limit and count >= limit:
                        break

                    try:
                        # Generate deterministic UUIDs from dataset IDs
                        user_id = uuid5(
                            MICROLENS_NAMESPACE, f"user_{row['userID']}"
                        )
                        video_id = uuid5(
                            MICROLENS_NAMESPACE, f"video_{row['videoID']}"
                        )

                        # Parse timestamp
                        timestamp = datetime.fromisoformat(row["timestamp"])
                        if timestamp.tzinfo is None:
                            timestamp = timestamp.replace(tzinfo=timezone.utc)

                        interaction = VideoInteraction(
                            user_id=user_id,
                            video_id=video_id,
                            event_type=EventType.CLICK,  # Base interaction is a click
                            device=Device.MOBILE,  # Default device for MicroLens
                            session_id=f"session_{row['userID']}_{timestamp.date()}",
                            timestamp=timestamp,
                        )
                        yield interaction
                        count += 1
                    except Exception as e:
                        logger.warning(
                            f"Error parsing row: {row}. Error: {e}"
                        )
                        continue
        except FileNotFoundError:
            logger.error(f"File not found: {csv_path}")
            raise


class MicroLensIngestor:
    """Ingestor for MicroLens-50k dataset."""

    def __init__(self, interaction_store: InteractionStore):
        """Initialize ingestor with interaction store.

        Args:
            interaction_store: InteractionStore instance for persistence
        """
        self.interaction_store = interaction_store
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
        }

    def ingest_from_csv(
        self, csv_path: Path, limit: Optional[int] = None
    ) -> dict:
        """Ingest interactions from MicroLens CSV file.

        Args:
            csv_path: Path to MicroLens-50k_pairs.csv
            limit: Maximum number of interactions to ingest

        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting ingestion from {csv_path}")

        for interaction in MicroLensPairsReader.read_interactions(csv_path, limit):
            self.stats["processed"] += 1

            if self.interaction_store.record_interaction(interaction):
                self.stats["successful"] += 1
            else:
                self.stats["failed"] += 1

            if self.stats["processed"] % 100 == 0:
                logger.info(
                    f"Progress: {self.stats['processed']} interactions processed "
                    f"({self.stats['successful']} successful, "
                    f"{self.stats['failed']} failed)"
                )

        logger.info(
            f"Ingestion complete. Stats: {self.stats}"
        )
        return self.stats


def main(csv_path: str, limit: Optional[int] = None) -> None:
    """Main entry point for MicroLens ingestion.

    Args:
        csv_path: Path to MicroLens-50k_pairs.csv
        limit: Maximum number of interactions to ingest (None = all)
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    csv_file = Path(csv_path)
    if not csv_file.exists():
        logger.error(f"File not found: {csv_path}")
        return

    # Initialize interaction store
    store = InteractionStore()

    # Check connectivity
    health = store.health_check()
    if not (health["redis"] or health["dynamodb"]):
        logger.error("Neither Redis nor DynamoDB is available")
        logger.error(f"Health check: {health}")
        return

    logger.info(f"Storage health: {health}")

    # Run ingestion
    ingestor = MicroLensIngestor(store)
    stats = ingestor.ingest_from_csv(csv_file, limit)

    logger.info(f"Final stats: {stats}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.data_platform.ingestion.microlens_pipeline <csv_path> [limit]")
        sys.exit(1)

    csv_path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None

    main(csv_path, limit)
