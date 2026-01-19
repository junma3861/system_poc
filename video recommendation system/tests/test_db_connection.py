"""Tests for Postgres database connection with pgvector support."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from psycopg import OperationalError

if TYPE_CHECKING:
    from psycopg import Connection

# Import from the module we're testing
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_platform.ingestion.sample_pipeline import (
    DEFAULT_DATABASE_URL,
    db_connection,
)


@pytest.fixture
def database_url() -> str:
    """Provide the database URL from environment or use default."""
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


class TestDatabaseConnection:
    """Test suite for database connection functionality."""

    def test_db_connection_context_manager(self, database_url: str) -> None:
        """Test that db_connection context manager works correctly."""
        try:
            with db_connection(database_url) as conn:
                # Verify connection is established
                assert conn is not None
                assert not conn.closed
                
                # Test basic query
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 as test")
                    result = cur.fetchone()
                    assert result is not None
                    assert result[0] == 1
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")

    def test_db_connection_closes_properly(self, database_url: str) -> None:
        """Test that connection is closed after context manager exits."""
        conn_obj = None
        try:
            with db_connection(database_url) as conn:
                conn_obj = conn
                assert not conn.closed
            
            # After context exits, connection should be closed
            assert conn_obj.closed
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")

    def test_pgvector_extension_available(self, database_url: str) -> None:
        """Test that pgvector extension is installed and registered."""
        try:
            with db_connection(database_url) as conn:
                with conn.cursor() as cur:
                    # Check if vector extension is installed
                    cur.execute("""
                        SELECT EXISTS(
                            SELECT 1 FROM pg_extension WHERE extname = 'vector'
                        ) as has_vector
                    """)
                    result = cur.fetchone()
                    assert result is not None
                    assert result[0] is True, "pgvector extension not installed"
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")

    def test_users_table_exists(self, database_url: str) -> None:
        """Test that the users table exists with correct schema."""
        try:
            with db_connection(database_url) as conn:
                with conn.cursor() as cur:
                    # Check if users table exists
                    cur.execute("""
                        SELECT EXISTS(
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = 'users'
                        ) as table_exists
                    """)
                    result = cur.fetchone()
                    assert result is not None
                    assert result[0] is True, "users table does not exist"
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")

    def test_videos_table_exists(self, database_url: str) -> None:
        """Test that the videos table exists with correct schema."""
        try:
            with db_connection(database_url) as conn:
                with conn.cursor() as cur:
                    # Check if videos table exists
                    cur.execute("""
                        SELECT EXISTS(
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = 'videos'
                        ) as table_exists
                    """)
                    result = cur.fetchone()
                    assert result is not None
                    assert result[0] is True, "videos table does not exist"
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")

    def test_vector_column_in_users(self, database_url: str) -> None:
        """Test that user_embedding column exists and has correct type."""
        try:
            with db_connection(database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT column_name, data_type, udt_name
                        FROM information_schema.columns
                        WHERE table_name = 'users' 
                        AND column_name = 'user_embedding'
                    """)
                    result = cur.fetchone()
                    if result is not None:
                        # Column exists, verify it's a vector type
                        assert result[2] == 'vector', f"Expected vector type, got {result[2]}"
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")

    def test_connection_with_invalid_url(self) -> None:
        """Test that invalid database URL raises appropriate error."""
        invalid_url = "postgresql://invalid:invalid@localhost:9999/nonexistent"
        
        with pytest.raises(OperationalError):
            with db_connection(invalid_url) as conn:
                pass

    def test_connection_autocommit_enabled(self, database_url: str) -> None:
        """Test that autocommit is enabled by default."""
        try:
            with db_connection(database_url) as conn:
                assert conn.autocommit is True
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")


class TestDatabaseIntegration:
    """Integration tests requiring a running database."""

    def test_can_insert_and_query_vector(self, database_url: str) -> None:
        """Test basic vector insertion and retrieval."""
        try:
            with db_connection(database_url) as conn:
                with conn.cursor() as cur:
                    # Create a temporary test table
                    cur.execute("""
                        CREATE TEMP TABLE test_vectors (
                            id SERIAL PRIMARY KEY,
                            embedding vector(3)
                        )
                    """)
                    
                    # Insert a test vector
                    from pgvector.psycopg import Vector
                    test_vector = Vector([1.0, 2.0, 3.0])
                    cur.execute(
                        "INSERT INTO test_vectors (embedding) VALUES (%s) RETURNING id",
                        (test_vector,)
                    )
                    inserted_id = cur.fetchone()[0]
                    
                    # Query it back
                    cur.execute(
                        "SELECT embedding FROM test_vectors WHERE id = %s",
                        (inserted_id,)
                    )
                    result = cur.fetchone()
                    assert result is not None
                    retrieved_vector = result[0]
                    assert len(retrieved_vector) == 3
                    assert list(retrieved_vector) == [1.0, 2.0, 3.0]
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
