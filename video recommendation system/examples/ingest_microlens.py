#!/usr/bin/env python
"""Example usage of the MicroLens-50k ingestion pipeline.

This script demonstrates how to:
1. Download the MicroLens-50k dataset
2. Parse the CSV file
3. Ingest interactions into the hybrid storage
4. Query the ingested data
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.data_platform.feature_store.interaction_store import InteractionStore
from src.data_platform.ingestion.microlens_pipeline import MicroLensIngestor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main example function."""
    # 1. Initialize interaction store
    logger.info("Initializing interaction store...")
    store = InteractionStore()

    # 2. Check storage availability
    health = store.health_check()
    logger.info(f"Storage health: Redis={health['redis']}, DynamoDB={health['dynamodb']}")

    if not (health["redis"] or health["dynamodb"]):
        logger.error("Neither Redis nor DynamoDB is available. Start services with:")
        logger.error("  docker-compose up -d")
        return

    # 3. Download dataset (if needed)
    # In practice, you would download from:
    # https://recsys.westlake.edu.cn/MicroLens-50k-Dataset/
    dataset_path = Path("data/raw/MicroLens-50k_pairs.csv")

    if not dataset_path.exists():
        logger.warning(f"Dataset not found at {dataset_path}")
        logger.info("To use this example:")
        logger.info("  1. Download from: https://recsys.westlake.edu.cn/MicroLens-50k-Dataset/")
        logger.info("  2. Extract to: data/raw/")
        logger.info("  3. Run this script again")
        return

    # 4. Ingest data
    logger.info(f"Starting ingestion from {dataset_path}")
    ingestor = MicroLensIngestor(store)

    # Ingest with limit for testing (remove limit for full dataset)
    stats = ingestor.ingest_from_csv(dataset_path, limit=1000)

    logger.info(f"Ingestion complete!")
    logger.info(f"  Processed: {stats['processed']}")
    logger.info(f"  Successful: {stats['successful']}")
    logger.info(f"  Failed: {stats['failed']}")

    # 5. Query sample data
    if stats["successful"] > 0:
        logger.info("\nExample: Querying interactions...")
        # Note: In a real scenario, you'd extract a user_id from the ingested data
        # and query their interactions.
        logger.info("See test_interaction_store.py for query examples")


if __name__ == "__main__":
    main()
