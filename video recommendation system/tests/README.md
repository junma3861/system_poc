# Testing Guide

## Running Database Connection Tests

### Prerequisites
1. **Conda environment** must be activated:
   ```bash
   conda activate video-rec
   ```

2. **PostgreSQL with pgvector** must be running:
   ```bash
   # Start the database
   docker-compose up -d pgvector
   
   # Verify it's running
   docker-compose ps
   ```

3. **Local PostgreSQL** (if installed via Homebrew) should be stopped to avoid port conflicts:
   ```bash
   brew services stop postgresql@14  # or your version
   ```

### Running Tests

```bash
# Run all database connection tests
pytest tests/test_db_connection.py -v

# Or using conda run (without activating)
conda run -n video-rec pytest tests/test_db_connection.py -v

# Run with coverage
pytest tests/test_db_connection.py --cov=src/data_platform/ingestion

# Run specific test
pytest tests/test_db_connection.py::TestDatabaseConnection::test_pgvector_extension_available -v
```

## Running Interaction Store Tests

### Prerequisites
1. **Conda environment** must be activated:
   ```bash
   conda activate video-rec
   ```

2. **Redis and DynamoDB Local** must be running:
   ```bash
   docker-compose up -d redis dynamodb
   docker-compose ps
   ```

3. **Local DynamoDB endpoint and creds** (for local dev):
   ```bash
   export AWS_ACCESS_KEY_ID=local
   export AWS_SECRET_ACCESS_KEY=local
   export AWS_REGION=us-east-1
   export DYNAMODB_ENDPOINT=http://localhost:8001
   ```

### Running Tests
```bash
# Run all interaction store tests
pytest tests/test_interaction_store.py -v

# Or using conda run (without activating)
conda run -n video-rec pytest tests/test_interaction_store.py -v

# Run specific test class or case
pytest tests/test_interaction_store.py::TestInteractionRecording -v
pytest tests/test_interaction_store.py::TestWriteAsidePattern::test_dynamodb_persistence -v
```

### Test Coverage
- ✅ Redis cache write/read (recent interactions, session hash)
- ✅ DynamoDB persistence (interactions table + metrics table)
- ✅ Write-aside pattern (cache + durable write)
- ✅ Event types: CLICK, WATCH_PROGRESS, LIKE, COMPLETE, SKIP
- ✅ Metrics aggregation (watch_count, like_count, total_watch_time, completion_rate)

### Troubleshooting (Interaction Tests)
- If DynamoDB port is busy, adjust mapping in docker-compose (default 8001).
- Ensure Redis is healthy: `docker-compose logs redis | tail`.
- To reset local data: `docker-compose down -v && rm -rf .volumes/redis .volumes/dynamodb`.

## Test Coverage

The database connection test suite includes:

### Basic Connection Tests
- ✅ Context manager functionality
- ✅ Connection closure after context exit
- ✅ Autocommit mode verification
- ✅ Invalid URL error handling

### pgvector Extension Tests
- ✅ Extension installation verification
- ✅ Vector column type validation
- ✅ Vector insertion and retrieval

### Schema Tests
- ✅ `users` table existence
- ✅ `videos` table existence
- ✅ `user_embedding` column with vector type

### Integration Tests
- ✅ Insert and query vector data
- ✅ Temporary table creation with vectors

## Running Ingestion Pipeline Tests

### MicroLens-50k Ingestion Tests

```bash
# Run all ingestion tests
pytest tests/test_microlens_ingestion.py -v

# Run specific test class
pytest tests/test_microlens_ingestion.py::TestMicroLensPairsReader -v
pytest tests/test_microlens_ingestion.py::TestMicroLensIngestor -v

# Run with coverage
pytest tests/test_microlens_ingestion.py --cov=src/data_platform/ingestion
```

### Test Coverage

**CSV Reader Tests:**
- ✅ Basic CSV parsing with correct column format
- ✅ Limit parameter for stopping early
- ✅ Deterministic UUID generation from dataset IDs
- ✅ Multiple user handling
- ✅ ISO timestamp parsing and UTC conversion
- ✅ File not found error handling
- ✅ Invalid row skipping with logging
- ✅ All VideoInteraction fields populated correctly

**Ingestor Tests:**
- ✅ Initialization with interaction store
- ✅ Successful CSV ingestion with statistics
- ✅ Handling partial failures
- ✅ Limit parameter enforcement
- ✅ Correct interaction object formatting

**Integration Tests:**
- ✅ End-to-end ingestion from CSV to storage (requires Redis/DynamoDB)
- ✅ Large batch ingestion (50+ interactions)

**CSV Format Variation Tests:**
- ✅ Whitespace handling
- ✅ Quoted fields
- ✅ UTC timezone support

### Using the Ingestion Pipeline

```bash
# From command line with conda
conda run -n video-rec python -m src.data_platform.ingestion.microlens_pipeline \
  /path/to/MicroLens-50k_pairs.csv

# With limit parameter (first N interactions)
conda run -n video-rec python -m src.data_platform.ingestion.microlens_pipeline \
  /path/to/MicroLens-50k_pairs.csv 1000

# From Python code
from src.data_platform.ingestion.microlens_pipeline import MicroLensIngestor
from src.data_platform.feature_store.interaction_store import InteractionStore
from pathlib import Path

store = InteractionStore()
ingestor = MicroLensIngestor(store)
stats = ingestor.ingest_from_csv(Path("data/MicroLens-50k_pairs.csv"))
print(f"Processed: {stats['processed']}, Successful: {stats['successful']}, Failed: {stats['failed']}")
```

### Dataset Format

The ingestion pipeline expects CSV files in this format:

```csv
userID,videoID,timestamp
1,101,2024-01-01T10:00:00
1,102,2024-01-01T11:00:00
2,101,2024-01-02T14:30:00
```

- `userID`: User identifier (converted to UUID)
- `videoID`: Video identifier (converted to UUID)
- `timestamp`: ISO format datetime (automatically added UTC if missing)

Default mapping:
- Event type: `EventType.CLICK` (base interaction)
- Device: `Device.MOBILE` (MicroLens default)
- Session: Generated as `session_{userID}_{date}`

## Troubleshooting

### Port Conflict Issues
If tests fail with "role does not exist" errors, check for port conflicts:
```bash
# Check what's using port 5432
lsof -i :5432

# Stop local PostgreSQL if needed
brew services list
brew services stop postgresql@14  # adjust version
```

### Database Not Ready
If tests skip with "Database not available", wait for initialization:
```bash
# Check database health
docker-compose logs pgvector

# Wait for "database system is ready" message
docker exec video-rec-pgvector pg_isready -U video_admin -d video_rec_dev
```

### Reset Database
To start fresh:
```bash
docker-compose down -v
rm -rf .volumes/postgres
docker-compose up -d pgvector
sleep 5  # wait for initialization
```

### Redis/DynamoDB Not Available
Integration tests will skip if storage services aren't running:
```bash
# Start all services
docker-compose up -d

# Verify services
docker-compose ps

# Check health
docker-compose exec redis redis-cli ping
aws dynamodb list-tables --endpoint-url http://localhost:8001 --region us-east-1
```

## Environment Variables

Tests respect these environment variables:
- `DATABASE_URL` - Override default PostgreSQL connection string
- `REDIS_URL` - Override default Redis connection (default: redis://localhost:6379)
- `AWS_ENDPOINT_URL` - Override DynamoDB endpoint (default: http://localhost:8001)
- `EMBEDDING_DIM` - Change vector dimension (default: 768)

Example:
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
export REDIS_URL="redis://localhost:6379"
pytest tests/test_microlens_ingestion.py
