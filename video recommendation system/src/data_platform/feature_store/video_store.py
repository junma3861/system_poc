"""PostgreSQL + pgvector-backed video feature store.

Provides CRUD and nearest-neighbor retrieval using the videos table
initialized via config/db/init.sql.
"""

from __future__ import annotations

import logging
from typing import Iterable, List, Optional
from uuid import UUID

import psycopg2
import psycopg2.extras

from ..data_model.video import VideoAsset, VideoMetadata, ContentStats, EngagementMetrics

logger = logging.getLogger(__name__)


class VideoStore:
    """Video storage and retrieval using Postgres + pgvector.

    Defaults align with docker-compose service `pgvector`.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = "video_rec_dev",
        user: str = "video_admin",
        password: str = "video_admin",
    ) -> None:
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        self.conn.autocommit = True

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    @staticmethod
    def _to_vector_literal(vec: Iterable[float]) -> str:
        # pgvector accepts '[v1,v2,...]' string literal casted to vector
        return "[" + ",".join(str(float(v)) for v in vec) + "]"

    def upsert_video(self, video: VideoAsset) -> bool:
        """Insert or update a video row including embedding.

        Returns True on success.
        """
        sql = """
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
        ) VALUES (
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
            %(video_embedding)s::vector,
            %(view_count)s,
            %(average_view_duration)s,
            %(click_through_rate)s,
            NOW(),
            NOW()
        )
        ON CONFLICT (video_id) DO UPDATE SET
            creator_id = EXCLUDED.creator_id,
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
        """

        params = {
            "video_id": str(video.video_id),
            "creator_id": str(video.creator_id),
            "title": video.metadata.title,
            "description": video.metadata.description,
            "tags": video.metadata.tags,
            "category": video.metadata.category,
            "duration_seconds": float(video.content_stats.duration_seconds),
            "resolution_height": int(video.content_stats.resolution_height),
            "resolution_width": int(video.content_stats.resolution_width),
            "upload_timestamp": video.content_stats.upload_timestamp,
            "video_embedding": self._to_vector_literal(video.video_embedding),
            "view_count": int(video.engagement_metrics.view_count),
            "average_view_duration": float(
                video.engagement_metrics.average_view_duration
            ),
            "click_through_rate": float(video.engagement_metrics.click_through_rate),
        }

        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
            return True
        except Exception as e:
            logger.error(f"Upsert video failed: {e}")
            return False

    def update_embedding(self, video_id: UUID, embedding: Iterable[float]) -> bool:
        """Update only the video embedding for a given video_id."""
        sql = """
        UPDATE videos
        SET video_embedding = %(embedding)s::vector,
            updated_at = NOW()
        WHERE video_id = %(video_id)s;
        """
        params = {
            "embedding": self._to_vector_literal(embedding),
            "video_id": str(video_id),
        }
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
            return True
        except Exception as e:
            logger.error(f"Update embedding failed: {e}")
            return False

    def get_video(self, video_id: UUID) -> Optional[VideoAsset]:
        """Fetch a video row and convert to `VideoAsset`."""
        sql = """
        SELECT 
            video_id, creator_id, title, description, tags, category,
            duration_seconds, resolution_height, resolution_width,
            upload_timestamp, video_embedding,
            view_count, average_view_duration, click_through_rate
        FROM videos
        WHERE video_id = %(video_id)s
        LIMIT 1;
        """

        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, {"video_id": str(video_id)})
                row = cur.fetchone()
                if not row:
                    return None

                metadata = VideoMetadata(
                    title=row["title"],
                    description=row["description"],
                    tags=row["tags"] or [],
                    category=row["category"],
                )
                content_stats = ContentStats(
                    duration_seconds=row["duration_seconds"],
                    resolution_height=float(row["resolution_height"]),
                    resolution_width=float(row["resolution_width"]),
                    upload_timestamp=row["upload_timestamp"],
                )
                engagement = EngagementMetrics(
                    view_count=row["view_count"],
                    average_view_duration=row["average_view_duration"],
                    click_through_rate=row["click_through_rate"],
                )
                # pgvector returns text for vectors when selected; parse comma-separated inside []
                emb_text = row["video_embedding"]
                if isinstance(emb_text, str) and emb_text.startswith("["):
                    emb = [float(x) for x in emb_text.strip("[]").split(",") if x]
                else:
                    # Fallback in case driver returns already parsed values
                    emb = list(emb_text) if isinstance(emb_text, (list, tuple)) else []

                return VideoAsset(
                    video_id=UUID(row["video_id"]),
                    creator_id=UUID(row["creator_id"]),
                    metadata=metadata,
                    content_stats=content_stats,
                    video_embedding=emb,
                    engagement_metrics=engagement,
                )
        except Exception as e:
            logger.error(f"Get video failed: {e}")
            return None

    def delete_video(self, video_id: UUID) -> bool:
        sql = "DELETE FROM videos WHERE video_id = %(video_id)s;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, {"video_id": str(video_id)})
            return True
        except Exception as e:
            logger.error(f"Delete video failed: {e}")
            return False

    def top_k_for_user(self, user_id: UUID, k: int = 100) -> List[UUID]:
        """Return up to k nearest videos for a given user embedding.

        Uses L2 distance ordering via `<->` operator consistent with ivfflat index.
        """
        sql = """
        SELECT v.video_id
        FROM videos v
        ORDER BY v.video_embedding <-> (
            SELECT u.user_embedding FROM users u WHERE u.user_id = %(user_id)s
        )
        LIMIT %(k)s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, {"user_id": str(user_id), "k": k})
                rows = cur.fetchall()
                return [UUID(r[0]) for r in rows]
        except Exception as e:
            logger.error(f"Top-K for user failed: {e}")
            return []

    def top_k_for_vector(self, user_vector: Iterable[float], k: int = 100) -> List[UUID]:
        """Return up to k nearest videos for a given user embedding vector."""
        sql = """
        SELECT v.video_id
        FROM videos v
        ORDER BY v.video_embedding <-> %(user_vec)s::vector
        LIMIT %(k)s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, {"user_vec": self._to_vector_literal(user_vector), "k": k})
                rows = cur.fetchall()
                return [UUID(r[0]) for r in rows]
        except Exception as e:
            logger.error(f"Top-K for vector failed: {e}")
            return []
