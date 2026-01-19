"""Simple ingestion pipeline that loads sample users/videos into Postgres."""

from __future__ import annotations

import os
import random
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterable, List
from uuid import UUID, uuid4

from psycopg import Connection, connect
from psycopg.types.json import Json
from pgvector.psycopg import Vector, register_vector

from data_platform.data_model.user import (
    ContextualState,
    Demographics,
    HistoricalAggregations,
    UserProfile,
)
from data_platform.data_model.video import (
    ContentStats,
    EngagementMetrics,
    VideoAsset,
    VideoMetadata,
)

DEFAULT_DATABASE_URL = "postgresql://video_admin:video_admin@localhost:5432/video_rec_dev"
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))


@contextmanager
def db_connection(database_url: str) -> Iterable[Connection]:
    """Yield a Postgres connection with pgvector support registered."""

    conn = connect(database_url, autocommit=True)
    try:
        register_vector(conn)
        yield conn
    finally:
        conn.close()


def _rand_embedding(seed: int) -> List[float]:
    rng = random.Random(seed)
    return [round(rng.random(), 6) for _ in range(EMBEDDING_DIM)]


def sample_users() -> List[UserProfile]:
    creator_a = uuid4()
    creator_b = uuid4()
    return [
        UserProfile(
            user_id=creator_a,
            demographics=Demographics(
                age=29,
                gender="female",
                primary_language="en",
                geographic_location="US",
            ),
            subscriptions=[str(creator_b)],
            user_embedding=_rand_embedding(1),
            contextual_state=ContextualState(
                device="mobile",
                time_of_day="morning",
                network_conditions="wifi",
            ),
            historical_aggs=HistoricalAggregations(
                videos_watched_last_24h=12,
                top_categories=["gaming", "music", "travel"],
            ),
        ),
        UserProfile(
            user_id=creator_b,
            demographics=Demographics(
                age=35,
                gender="male",
                primary_language="es",
                geographic_location="MX",
            ),
            subscriptions=[str(creator_a)],
            user_embedding=_rand_embedding(2),
            contextual_state=ContextualState(
                device="tv",
                time_of_day="evening",
                network_conditions="ethernet",
            ),
            historical_aggs=HistoricalAggregations(
                videos_watched_last_24h=5,
                top_categories=["sports", "technology"],
            ),
        ),
    ]


def sample_videos(users: List[UserProfile]) -> List[VideoAsset]:
    now = datetime.now(timezone.utc)
    return [
        VideoAsset(
            video_id=uuid4(),
            creator_id=users[0].user_id,
            metadata=VideoMetadata(
                title="Top 10 Speedrun Tricks",
                description="Breaking down advanced strats for 2026",
                tags=["gaming", "speedrun", "guide"],
                category="Gaming",
            ),
            content_stats=ContentStats(
                duration_seconds=480,
                resolution_height=1080,
                resolution_width=1920,
                upload_timestamp=now,
            ),
            video_embedding=_rand_embedding(3),
            engagement_metrics=EngagementMetrics(
                view_count=120_000,
                average_view_duration=345.6,
                click_through_rate=0.072,
            ),
        ),
        VideoAsset(
            video_id=uuid4(),
            creator_id=users[1].user_id,
            metadata=VideoMetadata(
                title="Street Food Tour",
                description="48 hours eating through CDMX",
                tags=["travel", "food"],
                category="Travel",
            ),
            content_stats=ContentStats(
                duration_seconds=900,
                resolution_height=2160,
                resolution_width=3840,
                upload_timestamp=now,
            ),
            video_embedding=_rand_embedding(4),
            engagement_metrics=EngagementMetrics(
                view_count=45_000,
                average_view_duration=612.1,
                click_through_rate=0.058,
            ),
        ),
    ]


def upsert_user(conn: Connection, user: UserProfile) -> None:
    payload = user.model_dump()
    subscriptions = [UUID(sub) for sub in payload["subscriptions"]]
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (
                user_id,
                demographics,
                subscriptions,
                user_embedding,
                contextual_state,
                historical_aggs,
                created_at,
                updated_at
            )
            VALUES (%(user_id)s, %(demographics)s, %(subscriptions)s, %(user_embedding)s,
                    %(contextual_state)s, %(historical_aggs)s, NOW(), NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                demographics = EXCLUDED.demographics,
                subscriptions = EXCLUDED.subscriptions,
                user_embedding = EXCLUDED.user_embedding,
                contextual_state = EXCLUDED.contextual_state,
                historical_aggs = EXCLUDED.historical_aggs,
                updated_at = NOW();
            """,
            {
                "user_id": user.user_id,
                "demographics": Json(payload["demographics"]),
                "subscriptions": subscriptions,
                "user_embedding": Vector(payload["user_embedding"]),
                "contextual_state": Json(payload["contextual_state"]),
                "historical_aggs": Json(payload["historical_aggs"]),
            },
        )


def upsert_video(conn: Connection, video: VideoAsset) -> None:
    payload = video.model_dump()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO videos (
                video_id,
                creator_id,
                title,
                description,
                tags,
                category,
                duration_seconds,
                resolution_height,
                resolution_width,
                upload_timestamp,
                video_embedding,
                view_count,
                average_view_duration,
                click_through_rate,
                created_at,
                updated_at
            )
            VALUES (
                %(video_id)s,
                %(creator_id)s,
                %(title)s,
                %(description)s,
                %(tags)s,
                %(category)s,
                %(duration_seconds)s,
                %(resolution_height)s,
                %(resolution_width)s,
                %(upload_timestamp)s,
                %(video_embedding)s,
                %(view_count)s,
                %(average_view_duration)s,
                %(click_through_rate)s,
                NOW(),
                NOW()
            )
            ON CONFLICT (video_id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                tags = EXCLUDED.tags,
                category = EXCLUDED.category,
                duration_seconds = EXCLUDED.duration_seconds,
                resolution_height = EXCLUDED.resolution_height,
                resolution_width = EXCLUDED.resolution_width,
                upload_timestamp = EXCLUDED.upload_timestamp,
                video_embedding = EXCLUDED.video_embedding,
                view_count = EXCLUDED.view_count,
                average_view_duration = EXCLUDED.average_view_duration,
                click_through_rate = EXCLUDED.click_through_rate,
                updated_at = NOW();
            """,
            {
                "video_id": video.video_id,
                "creator_id": video.creator_id,
                "title": payload["metadata"]["title"],
                "description": payload["metadata"]["description"],
                "tags": payload["metadata"]["tags"],
                "category": payload["metadata"]["category"],
                "duration_seconds": payload["content_stats"]["duration_seconds"],
                "resolution_height": payload["content_stats"]["resolution_height"],
                "resolution_width": payload["content_stats"]["resolution_width"],
                "upload_timestamp": payload["content_stats"]["upload_timestamp"],
                "video_embedding": Vector(payload["video_embedding"]),
                "view_count": payload["engagement_metrics"]["view_count"],
                "average_view_duration": payload["engagement_metrics"]["average_view_duration"],
                "click_through_rate": payload["engagement_metrics"]["click_through_rate"],
            },
        )


def run_sample_ingestion() -> None:
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    users = sample_users()
    videos = sample_videos(users)

    with db_connection(database_url) as conn:
        for user in users:
            upsert_user(conn, user)
        for video in videos:
            upsert_video(conn, video)

    print(f"Inserted/updated {len(users)} users and {len(videos)} videos into {database_url}.")


if __name__ == "__main__":
    run_sample_ingestion()
