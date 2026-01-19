# Quick Start: MicroLens-50k Ingestion

## Installation

```bash
# Install dependencies (if not already installed)
pip install boto3 redis psycopg pgvector pydantic

# Or use conda environment
conda env create -f environment.yml
conda activate video-rec
```

## Verify Services

```bash
# Start Docker services
docker-compose up -d

# Check services are running
docker-compose ps
docker compose ps --format "table {{.Service}}\t{{.Status}}"
```

## Run Ingestion

### Option 1: Command Line
```bash
# Full dataset ingestion
python -m src.data_platform.ingestion.microlens_pipeline \
  /path/to/MicroLens-50k_pairs.csv

# Test with first 100 records
python -m src.data_platform.ingestion.microlens_pipeline \
  /path/to/MicroLens-50k_pairs.csv 100
```

### Option 2: Python Script
```python
from pathlib import Path
from src.data_platform.ingestion.microlens_pipeline import MicroLensIngestor
from src.data_platform.feature_store.interaction_store import InteractionStore

# Initialize
store = InteractionStore()
ingestor = MicroLensIngestor(store)

# Ingest
stats = ingestor.ingest_from_csv(
    Path("data/MicroLens-50k_pairs.csv"),
    limit=1000  # Optional: limit number of records
)

# Check results
print(f"Processed: {stats['processed']}")
print(f"Successful: {stats['successful']}")
print(f"Failed: {stats['failed']}")
```

## Test Pipeline

```bash
# Run all tests
pytest tests/test_microlens_ingestion.py -v

# Run specific test class
pytest tests/test_microlens_ingestion.py::TestMicroLensPairsReader -v
pytest tests/test_microlens_ingestion.py::TestMicroLensIngestor -v

# With coverage
pytest tests/test_microlens_ingestion.py --cov=src/data_platform/ingestion
```

## Verify Data

After ingestion, verify data is stored:

```python
from src.data_platform.feature_store.interaction_store import InteractionStore
from uuid import UUID

store = InteractionStore()

# Check health
health = store.health_check()
print(f"Redis: {health['redis']}, DynamoDB: {health['dynamodb']}")

# Query a user's interactions (example with known user_id)
user_id = UUID("...")  # UUID from ingested data
interactions = store.get_user_interactions(user_id)
print(f"Found {len(interactions)} interactions for user")
```

## Dataset Location

**Download from**: https://recsys.westlake.edu.cn/MicroLens-50k-Dataset/

**Extract to**: `data/raw/MicroLens-50k_pairs.csv`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Activate conda: `conda activate video-rec` |
| `Connection refused` | Start services: `docker-compose up -d` |
| `CSV file not found` | Download dataset from https://recsys.westlake.edu.cn/MicroLens-50k-Dataset/ |
| `Redis/DynamoDB unavailable` | Check `docker-compose ps` and service logs |
| `UUID parse error` | Ensure CSV has valid userID/videoID columns |

## Performance

- **Speed**: ~500-1000 interactions/sec
- **Memory**: Streaming (constant usage regardless of dataset size)
- **Storage**: Redis (hot cache) + DynamoDB (cold persistence)

## Documentation

- **Architecture**: See `docs/INGESTION_PIPELINE.md`
- **Tests**: See `tests/test_microlens_ingestion.py`
- **Usage Examples**: See `examples/ingest_microlens.py`
- **API Reference**: See docstrings in `src/data_platform/ingestion/`

## File Structure

```
src/data_platform/ingestion/
├── microlens_pipeline.py      # Pipeline implementation
└── sample_pipeline.py          # Sample pipeline (existing)

tests/
├── test_microlens_ingestion.py # Comprehensive tests
├── test_interaction_store.py    # Storage layer tests
└── test_db_connection.py        # Database tests

docs/
└── INGESTION_PIPELINE.md        # Detailed documentation

examples/
└── ingest_microlens.py          # Example usage script
```

## Next Steps

1. ✅ **Verify Tests**: Run `pytest tests/ -v` (all 46 tests should pass)
2. 📥 **Download Dataset**: Get CSV from MicroLens-50k official site
3. 🚀 **Run Ingestion**: Execute ingestion pipeline with dataset
4. 🔍 **Verify Data**: Query stored interactions from Redis/DynamoDB
5. 📊 **Analyze**: Use ingested data for recommendation system development

## Support

For issues or questions:
- Check `docs/INGESTION_PIPELINE.md` for detailed troubleshooting
- Review test examples in `tests/test_microlens_ingestion.py`
- See `claude.md` for project guidelines
