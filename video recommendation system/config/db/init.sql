-- Enable uuid and vector support for embeddings
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table mirrors the Pydantic UserProfile schema
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY,
    demographics JSONB NOT NULL,
    subscriptions UUID[] NOT NULL DEFAULT ARRAY[]::UUID[],
    user_embedding vector(768) NOT NULL,
    contextual_state JSONB NOT NULL,
    historical_aggs JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_demographics_gin ON users USING GIN (demographics);
CREATE INDEX IF NOT EXISTS idx_users_subscriptions_gin ON users USING GIN (subscriptions);
CREATE INDEX IF NOT EXISTS idx_users_embedding_ivfflat ON users USING ivfflat (user_embedding vector_l2_ops) WITH (lists = 100);

-- Videos table mirrors the Pydantic VideoAsset schema
CREATE TABLE IF NOT EXISTS videos (
    video_id UUID PRIMARY KEY,
    creator_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    category TEXT NOT NULL,
    duration_seconds REAL NOT NULL CHECK (duration_seconds > 0),
    resolution_height INTEGER NOT NULL CHECK (resolution_height > 0),
    resolution_width INTEGER NOT NULL CHECK (resolution_width > 0),
    upload_timestamp TIMESTAMPTZ NOT NULL,
    video_embedding vector(768) NOT NULL,
    view_count BIGINT NOT NULL DEFAULT 0,
    average_view_duration REAL NOT NULL DEFAULT 0,
    click_through_rate REAL NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_videos_tags_gin ON videos USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_videos_category ON videos (category);
CREATE INDEX IF NOT EXISTS idx_videos_embedding_ivfflat ON videos USING ivfflat (video_embedding vector_l2_ops) WITH (lists = 100);
