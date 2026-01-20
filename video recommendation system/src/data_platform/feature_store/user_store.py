"""PostgreSQL + pgvector-backed user feature store.

Manages CRUD for users and embeds using the users table
initialized via config/db/init.sql.
"""

from __future__ import annotations

import logging
from typing import Iterable, List, Optional
from uuid import UUID

import psycopg2
import psycopg2.extras

from ..data_model.user import (
    UserProfile,
    Demographics,
    ContextualState,
    HistoricalAggregations,
)

logger = logging.getLogger(__name__)


class UserStore:
    """User storage using Postgres + pgvector.

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
        return "[" + ",".join(str(float(v)) for v in vec) + "]"

    def upsert_user(self, user_profile: UserProfile) -> bool:
        """Insert or update a user row including embedding."""
        # Attempt to coerce subscriptions (List[str]) into UUID list for DB
        subs_uuid: List[UUID] = []
        for s in user_profile.subscriptions:
            try:
                subs_uuid.append(UUID(str(s)))
            except Exception:
                logger.warning(f"Skipping non-UUID subscription: {s}")

        sql = """
        INSERT INTO users (
            user_id,
            demographics,
            subscriptions,
            user_embedding,
            contextual_state,
            historical_aggs,
            created_at,
            updated_at
        ) VALUES (
            %(user_id)s,
            %(demographics)s::jsonb,
            %(subscriptions)s,
            %(user_embedding)s::vector,
            %(contextual_state)s::jsonb,
            %(historical_aggs)s::jsonb,
            NOW(),
            NOW()
        )
        ON CONFLICT (user_id) DO UPDATE SET
            demographics = EXCLUDED.demographics,
            subscriptions = EXCLUDED.subscriptions,
            user_embedding = EXCLUDED.user_embedding,
            contextual_state = EXCLUDED.contextual_state,
            historical_aggs = EXCLUDED.historical_aggs,
            updated_at = NOW();
        """

        params = {
            "user_id": str(user_profile.user_id),
            "demographics": user_profile.demographics.dict(),
            "subscriptions": subs_uuid,
            "user_embedding": self._to_vector_literal(user_profile.user_embedding),
            "contextual_state": user_profile.contextual_state.dict(),
            "historical_aggs": user_profile.historical_aggs.dict(),
        }

        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
            return True
        except Exception as e:
            logger.error(f"Upsert user failed: {e}")
            return False

    def update_embedding(self, user_id: UUID, embedding: Iterable[float]) -> bool:
        sql = """
        UPDATE users
        SET user_embedding = %(embedding)s::vector,
            updated_at = NOW()
        WHERE user_id = %(user_id)s;
        """
        params = {
            "embedding": self._to_vector_literal(embedding),
            "user_id": str(user_id),
        }
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
            return True
        except Exception as e:
            logger.error(f"Update user embedding failed: {e}")
            return False

    def get_user(self, user_id: UUID) -> Optional[UserProfile]:
        sql = """
        SELECT user_id, demographics, subscriptions, user_embedding,
               contextual_state, historical_aggs
        FROM users
        WHERE user_id = %(user_id)s
        LIMIT 1;
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, {"user_id": str(user_id)})
                row = cur.fetchone()
                if not row:
                    return None

                # Parse vector text like "[x,y,z]" into list[float]
                emb_text = row["user_embedding"]
                if isinstance(emb_text, str) and emb_text.startswith("["):
                    emb = [float(x) for x in emb_text.strip("[]").split(",") if x]
                else:
                    emb = list(emb_text) if isinstance(emb_text, (list, tuple)) else []

                # subscriptions come back as list of UUIDs: convert to strings
                subs = row.get("subscriptions") or []
                subs_str: List[str] = [str(x) for x in subs]

                return UserProfile(
                    user_id=UUID(row["user_id"]),
                    demographics=Demographics(**(row["demographics"] or {})),
                    subscriptions=subs_str,
                    user_embedding=emb,
                    contextual_state=ContextualState(**(row["contextual_state"] or {})),
                    historical_aggs=HistoricalAggregations(**(row["historical_aggs"] or {})),
                )
        except Exception as e:
            logger.error(f"Get user failed: {e}")
            return None

    def delete_user(self, user_id: UUID) -> bool:
        sql = "DELETE FROM users WHERE user_id = %(user_id)s;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, {"user_id": str(user_id)})
            return True
        except Exception as e:
            logger.error(f"Delete user failed: {e}")
            return False
