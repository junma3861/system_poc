"""Interaction storage layer with Redis (cache) and DynamoDB (persistence)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

import boto3
import redis
from botocore.exceptions import ClientError

from data_platform.data_model.interaction import (
    EventType,
    InteractionMetrics,
    VideoInteraction,
)

logger = logging.getLogger(__name__)

# Redis key patterns
REDIS_USER_INTERACTIONS_KEY = "user:interactions:{user_id}"
REDIS_USER_METRICS_KEY = "user:metrics:{user_id}:{video_id}"
REDIS_SESSION_KEY = "session:{session_id}"

# DynamoDB configuration
DYNAMODB_REGION = "us-east-1"
DYNAMODB_ENDPOINT = "http://localhost:8001"  # Local development
INTERACTIONS_TABLE = "user-video-interactions"
METRICS_TABLE = "interaction-metrics"

# Redis TTL (24 hours for session data, 7 days for metrics)
REDIS_SESSION_TTL = 86400
REDIS_METRICS_TTL = 604800


class InteractionStore:
    """Hybrid storage for user-video interactions."""

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        dynamodb_endpoint: str = DYNAMODB_ENDPOINT,
        dynamodb_region: str = DYNAMODB_REGION,
    ):
        """Initialize interaction store with Redis and DynamoDB clients.

        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            dynamodb_endpoint: DynamoDB endpoint (local or AWS)
            dynamodb_region: AWS region for DynamoDB
        """
        self.redis_client = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=dynamodb_endpoint,
            region_name=dynamodb_region,
            aws_access_key_id="local",
            aws_secret_access_key="local",
        )
        self._ensure_tables_exist()

    def _ensure_tables_exist(self) -> None:
        """Create DynamoDB tables if they don't exist."""
        self._ensure_interactions_table()
        self._ensure_metrics_table()

    def _ensure_interactions_table(self) -> None:
        """Ensure interactions table exists (recreate if missing)."""
        try:
            self.dynamodb.meta.client.describe_table(TableName=INTERACTIONS_TABLE)
            logger.info(f"Table {INTERACTIONS_TABLE} already exists")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                self._create_interactions_table()
            else:
                raise

    def _ensure_metrics_table(self) -> None:
        """Ensure metrics table exists with correct schema (recreate if mismatched)."""
        try:
            resp = self.dynamodb.meta.client.describe_table(TableName=METRICS_TABLE)
            key_schema = resp.get("Table", {}).get("KeySchema", [])
            expected = [
                {"AttributeName": "user_video_id", "KeyType": "HASH"},
            ]
            if key_schema != expected:
                logger.warning(
                    "Metrics table schema mismatch; recreating table for local dev"
                )
                table_ref = self.dynamodb.Table(METRICS_TABLE)
                table_ref.delete()
                table_ref.wait_until_not_exists()
                self._create_metrics_table()
            else:
                logger.info(f"Table {METRICS_TABLE} already exists")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                self._create_metrics_table()
            else:
                raise

    def _create_interactions_table(self) -> None:
        """Create DynamoDB table for interactions."""
        try:
            table = self.dynamodb.create_table(
                TableName=INTERACTIONS_TABLE,
                KeySchema=[
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "user_id", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "S"},
                    {"AttributeName": "video_id", "AttributeType": "S"},
                ],
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "video_id-timestamp-index",
                        "KeySchema": [
                            {"AttributeName": "video_id", "KeyType": "HASH"},
                            {"AttributeName": "timestamp", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    }
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            )
            table.wait_until_exists()
            logger.info(f"Created table {INTERACTIONS_TABLE}")
        except ClientError as e:
            logger.error(f"Error creating interactions table: {e}")
            raise

    def _create_metrics_table(self) -> None:
        """Create DynamoDB table for aggregated metrics."""
        try:
            table = self.dynamodb.create_table(
                TableName=METRICS_TABLE,
                KeySchema=[
                    {"AttributeName": "user_video_id", "KeyType": "HASH"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "user_video_id", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            )
            table.wait_until_exists()
            logger.info(f"Created table {METRICS_TABLE}")
        except ClientError as e:
            logger.error(f"Error creating metrics table: {e}")
            raise

    def record_interaction(self, interaction: VideoInteraction) -> bool:
        """Record interaction with write-aside pattern.

        Writes to Redis immediately (fast) and DynamoDB asynchronously (durable).

        Args:
            interaction: VideoInteraction to record

        Returns:
            True if interaction was recorded successfully
        """
        try:
            # Fast write to Redis
            self._write_to_redis(interaction)

            # Persistent write to DynamoDB
            self._write_to_dynamodb(interaction)

            logger.info(
                f"Recorded interaction: user={interaction.user_id}, "
                f"video={interaction.video_id}, event={interaction.event_type}"
            )
            return True
        except Exception as e:
            logger.error(f"Error recording interaction: {e}")
            return False

    def _write_to_redis(self, interaction: VideoInteraction) -> None:
        """Write interaction to Redis cache.

        Args:
            interaction: VideoInteraction to cache
        """
        # Store in user interactions list
        key = REDIS_USER_INTERACTIONS_KEY.format(user_id=str(interaction.user_id))
        interaction_json = interaction.model_dump_json()
        self.redis_client.lpush(key, interaction_json)

        # Keep only last 100 interactions per user
        self.redis_client.ltrim(key, 0, 99)
        self.redis_client.expire(key, REDIS_SESSION_TTL)

        # Update session data
        session_key = REDIS_SESSION_KEY.format(session_id=interaction.session_id)
        session_data = {
            "user_id": str(interaction.user_id),
            "last_event": interaction.event_type,
            "last_video_id": str(interaction.video_id),
            "last_timestamp": interaction.timestamp.isoformat(),
        }
        self.redis_client.hset(session_key, mapping=session_data)
        self.redis_client.expire(session_key, REDIS_SESSION_TTL)

    def _write_to_dynamodb(self, interaction: VideoInteraction) -> None:
        """Write interaction to DynamoDB for persistence.

        Args:
            interaction: VideoInteraction to persist
        """
        table = self.dynamodb.Table(INTERACTIONS_TABLE)

        item = {
            "user_id": str(interaction.user_id),
            "video_id": str(interaction.video_id),
            "timestamp": interaction.timestamp.isoformat(),
            "event_type": interaction.event_type,
            "device": interaction.device,
            "session_id": interaction.session_id,
        }

        # Add optional fields
        if interaction.watch_time is not None:
            item["watch_time"] = Decimal(str(interaction.watch_time))
        if interaction.duration is not None:
            item["duration"] = Decimal(str(interaction.duration))

        table.put_item(Item=item)

        # Update metrics
        self._update_metrics_in_dynamodb(interaction)

    def _update_metrics_in_dynamodb(self, interaction: VideoInteraction) -> None:
        """Update aggregated metrics in DynamoDB.

        Args:
            interaction: VideoInteraction to include in metrics
        """
        table = self.dynamodb.Table(METRICS_TABLE)
        user_video_id = f"{interaction.user_id}#{interaction.video_id}"
        now = datetime.now(timezone.utc).isoformat()

        # Fetch existing metrics (if any)
        existing_resp = table.get_item(Key={"user_video_id": user_video_id})
        existing = existing_resp.get("Item", {})

        watch_count = int(existing.get("watch_count", 0)) + 1
        like_count = int(existing.get("like_count", 0))
        total_watch_time = int(existing.get("total_watch_time", 0))
        completion_rate = Decimal(str(existing.get("completion_rate", 0)))

        if interaction.event_type == EventType.LIKE:
            like_count += 1
        elif interaction.event_type == EventType.COMPLETE:
            completion_rate = Decimal("100")
        elif (
            interaction.event_type == EventType.WATCH_PROGRESS
            and interaction.duration
            and interaction.watch_time is not None
        ):
            completion_rate = Decimal(
                str(round((interaction.watch_time / interaction.duration) * 100, 2))
            )
            total_watch_time += interaction.watch_time

        item = {
            "user_video_id": user_video_id,
            "user_id": str(interaction.user_id),
            "video_id": str(interaction.video_id),
            "watch_count": Decimal(str(watch_count)),
            "like_count": Decimal(str(like_count)),
            "total_watch_time": Decimal(str(total_watch_time)),
            "completion_rate": completion_rate,
            "last_watched": interaction.timestamp.isoformat(),
            "updated_at": now,
        }

        if interaction.event_type == EventType.COMPLETE:
            item["last_completed_at"] = interaction.timestamp.isoformat()

        table.put_item(Item=item)

    def get_user_interactions(
        self, user_id: UUID, limit: int = 100, from_redis: bool = True
    ) -> list[VideoInteraction]:
        """Get user interactions from cache or database.

        Args:
            user_id: User ID to fetch interactions for
            limit: Maximum number of interactions to return
            from_redis: Whether to fetch from Redis (cache) first

        Returns:
            List of VideoInteraction objects
        """
        interactions = []

        if from_redis:
            # Try Redis first (faster)
            interactions = self._get_from_redis(user_id, limit)

        if not interactions:
            # Fallback to DynamoDB
            interactions = self._get_from_dynamodb(user_id, limit)

        return interactions

    def _get_from_redis(self, user_id: UUID, limit: int) -> list[VideoInteraction]:
        """Fetch interactions from Redis cache.

        Args:
            user_id: User ID
            limit: Maximum number of interactions

        Returns:
            List of VideoInteraction objects
        """
        try:
            key = REDIS_USER_INTERACTIONS_KEY.format(user_id=str(user_id))
            interactions_json = self.redis_client.lrange(key, 0, limit - 1)

            interactions = []
            for json_str in interactions_json:
                try:
                    interaction = VideoInteraction(**json.loads(json_str))
                    interactions.append(interaction)
                except Exception as e:
                    logger.warning(f"Error parsing interaction from Redis: {e}")

            return interactions
        except Exception as e:
            logger.error(f"Error fetching from Redis: {e}")
            return []

    def _get_from_dynamodb(
        self, user_id: UUID, limit: int
    ) -> list[VideoInteraction]:
        """Fetch interactions from DynamoDB.

        Args:
            user_id: User ID
            limit: Maximum number of interactions

        Returns:
            List of VideoInteraction objects
        """
        try:
            table = self.dynamodb.Table(INTERACTIONS_TABLE)
            response = table.query(
                KeyConditionExpression="user_id = :user_id",
                ExpressionAttributeValues={":user_id": str(user_id)},
                Limit=limit,
                ScanIndexForward=False,  # Most recent first
            )

            interactions = []
            for item in response.get("Items", []):
                try:
                    interaction = VideoInteraction(
                        user_id=UUID(item["user_id"]),
                        video_id=UUID(item["video_id"]),
                        event_type=item["event_type"],
                        watch_time=(
                            int(item["watch_time"])
                            if "watch_time" in item
                            else None
                        ),
                        duration=(
                            int(item["duration"]) if "duration" in item else None
                        ),
                        device=item["device"],
                        session_id=item["session_id"],
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                    )
                    interactions.append(interaction)
                except Exception as e:
                    logger.warning(f"Error parsing interaction from DynamoDB: {e}")

            return interactions
        except Exception as e:
            logger.error(f"Error fetching from DynamoDB: {e}")
            return []

    def get_user_video_metrics(
        self, user_id: UUID, video_id: UUID
    ) -> Optional[InteractionMetrics]:
        """Get aggregated metrics for user-video pair.

        Args:
            user_id: User ID
            video_id: Video ID

        Returns:
            InteractionMetrics or None if not found
        """
        # Try Redis cache first
        metrics = self._get_metrics_from_redis(user_id, video_id)
        if metrics:
            return metrics

        # Fallback to DynamoDB
        return self._get_metrics_from_dynamodb(user_id, video_id)

    def _get_metrics_from_redis(
        self, user_id: UUID, video_id: UUID
    ) -> Optional[InteractionMetrics]:
        """Fetch metrics from Redis cache.

        Args:
            user_id: User ID
            video_id: Video ID

        Returns:
            InteractionMetrics or None
        """
        try:
            key = REDIS_USER_METRICS_KEY.format(
                user_id=str(user_id), video_id=str(video_id)
            )
            metrics_json = self.redis_client.get(key)
            if metrics_json:
                return InteractionMetrics(**json.loads(metrics_json))
        except Exception as e:
            logger.warning(f"Error fetching metrics from Redis: {e}")
        return None

    def _get_metrics_from_dynamodb(
        self, user_id: UUID, video_id: UUID
    ) -> Optional[InteractionMetrics]:
        """Fetch metrics from DynamoDB.

        Args:
            user_id: User ID
            video_id: Video ID

        Returns:
            InteractionMetrics or None
        """
        try:
            table = self.dynamodb.Table(METRICS_TABLE)
            user_video_id = f"{user_id}#{video_id}"
            response = table.query(
                KeyConditionExpression="user_video_id = :id",
                ExpressionAttributeValues={":id": user_video_id},
                Limit=1,
                ScanIndexForward=False,
            )

            items = response.get("Items", [])
            if items:
                item = items[0]
                metrics = InteractionMetrics(
                    user_id=user_id,
                    video_id=video_id,
                    total_watch_time=item.get("total_watch_time", 0),
                    watch_count=item.get("watch_count", 0),
                    like_count=item.get("like_count", 0),
                    last_watched=(
                        datetime.fromisoformat(item["updated_at"])
                        if "updated_at" in item
                        else None
                    ),
                    completion_rate=item.get("completion_rate", 0.0),
                )

                # Cache in Redis
                self._cache_metrics_in_redis(metrics)
                return metrics
        except Exception as e:
            logger.error(f"Error fetching metrics from DynamoDB: {e}")
        return None

    def _cache_metrics_in_redis(self, metrics: InteractionMetrics) -> None:
        """Cache metrics in Redis.

        Args:
            metrics: InteractionMetrics to cache
        """
        try:
            key = REDIS_USER_METRICS_KEY.format(
                user_id=str(metrics.user_id), video_id=str(metrics.video_id)
            )
            self.redis_client.setex(
                key, REDIS_METRICS_TTL, metrics.model_dump_json()
            )
        except Exception as e:
            logger.warning(f"Error caching metrics in Redis: {e}")

    def health_check(self) -> dict[str, bool]:
        """Check health of Redis and DynamoDB connections.

        Returns:
            Dictionary with health status of each service
        """
        redis_ok = False
        dynamodb_ok = False

        try:
            self.redis_client.ping()
            redis_ok = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")

        try:
            self.dynamodb.meta.client.list_tables()
            dynamodb_ok = True
        except Exception as e:
            logger.error(f"DynamoDB health check failed: {e}")

        return {"redis": redis_ok, "dynamodb": dynamodb_ok}
