# Project Guidelines

## Overview
This is a Python-based video recommendation system project.

## Tech Stack
- **Language**: Python 3.10+
- **Package Manager**: conda

## Project Structure
```
├── src/                    # Source code
├── tests/                  # Test files
├── data/                   # Data files
├── notebooks/              # Jupyter notebooks
├── config/                 # Configuration files
│   └── db/                 # Postgres/pgvector init scripts
├── .volumes/postgres/      # Local Postgres persistent data
├── .volumes/redis/         # Local Redis persistent data
├── .volumes/dynamodb/      # Local DynamoDB persistent data
├── docker-compose.yml      # Local pgvector + redis + dynamodb stack
├── environment.yml         # Conda environment file
└── README.md              # Project documentation
```

## Code Style & Conventions

### Python Style
- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Maximum line length: 88 characters (Black formatter default)
- Use docstrings for all public modules, functions, classes, and methods

### Naming Conventions
- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

### Import Order
1. Standard library imports
2. Related third-party imports
3. Local application/library specific imports

Separate each group with a blank line.

## Development Workflow

### Setting Up Environment
```bash
# Create conda environment from file
conda env create -f environment.yml

# Or create a new environment
conda create -n video-rec python=3.10

# Activate environment
conda activate video-rec

# Install dependencies (if needed)
conda install --file requirements.txt
# Or for pip packages
pip install -r requirements.txt

# Export environment
conda env export > environment.yml
```

### Local Postgres + Redis + DynamoDB
```bash
# Boot the database
docker-compose up -d pgvector

# Boot cache and event store
docker-compose up -d redis dynamodb

# Tail logs if needed
docker-compose logs -f pgvector

# Connection string for ORM/psql
export DATABASE_URL="postgresql://video_admin:video_admin@localhost:5432/video_rec_dev"

# DynamoDB Local endpoint (dev)
export AWS_ACCESS_KEY_ID=local
export AWS_SECRET_ACCESS_KEY=local
export AWS_REGION=us-east-1
export DYNAMODB_ENDPOINT="http://localhost:8001"

# Inspect Postgres manually
docker exec -it video-rec-pgvector psql -U video_admin -d video_rec_dev
```
- `config/db/init.sql` enables the `vector` extension and seeds `users` + `videos` tables.
- Embedding columns default to `vector(768)`; adjust the DDL if your encoder dimension differs.
- IVFFlat indexes require an `ANALYZE` pass after bulk loads (e.g., `VACUUM ANALYZE users;`).

### Sample Data Ingestion
```bash
# Ensure Postgres is running first
python -m src.data_platform.ingestion.sample_pipeline
```
- Uses psycopg + pgvector to upsert two sample users and videos.
- Respects `DATABASE_URL` and optional `EMBEDDING_DIM` env vars for local overrides.

### Running Ingestion Tests
```bash
# Run ingestion pipeline tests
pytest tests/test_microlens_ingestion.py -v

# Test CSV reader
pytest tests/test_microlens_ingestion.py::TestMicroLensPairsReader -v

# Test ingestor
pytest tests/test_microlens_ingestion.py::TestMicroLensIngestor -v

# Integration tests (requires Docker Compose services)
pytest tests/test_microlens_ingestion.py::TestMicroLensIntegration -v
```

### Using the Ingestion Pipeline
```bash
# Ingest MicroLens-50k dataset (first 1000 records for testing)
python -m src.data_platform.ingestion.microlens_pipeline \
  /path/to/MicroLens-50k_pairs.csv 1000

# Ingest full dataset
python -m src.data_platform.ingestion.microlens_pipeline \
  /path/to/MicroLens-50k_pairs.csv

# Or from Python
from src.data_platform.ingestion.microlens_pipeline import MicroLensIngestor
from src.data_platform.feature_store.interaction_store import InteractionStore

store = InteractionStore()
ingestor = MicroLensIngestor(store)
stats = ingestor.ingest_from_csv(Path("data/MicroLens-50k_pairs.csv"))
```

### Running Tests
```bash
pytest tests/

# Focused
pytest tests/test_db_connection.py -v
pytest tests/test_interaction_store.py -v
pytest tests/test_microlens_ingestion.py -v
```

### Code Formatting
```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8 .

# Type checking
mypy src/
```

## Best Practices

### Error Handling
- Use specific exception types over generic `Exception`
- Always include meaningful error messages
- Use context managers for resource management

### Documentation
- Write clear docstrings using Google or NumPy style
- Keep README.md updated with setup and usage instructions
- Document configuration options and environment variables

### Testing
- Write unit tests for all new functionality
- Aim for high test coverage on critical paths
- Use fixtures for common test setup

## Common Commands
| Task | Command |
|------|---------|
| Run application | `python -m src.main` |
| Run tests | `pytest` |
| Run DB tests | `pytest tests/test_db_connection.py -v` |
| Run interaction tests | `pytest tests/test_interaction_store.py -v` |
| Run ingestion tests | `pytest tests/test_microlens_ingestion.py -v` |
| Ingest MicroLens data | `python -m src.data_platform.ingestion.microlens_pipeline <csv_path> [limit]` |
| Start services | `docker-compose up -d pgvector redis dynamodb` |
| Stop services | `docker-compose down` |
| Reset data (dev) | `docker-compose down -v && rm -rf .volumes/postgres .volumes/redis .volumes/dynamodb` |
| Format code | `black .` |
| Sort imports | `isort .` |
| Lint | `flake8 .` |
| Check types | `mypy src/` |
| Generate docs | `sphinx-build docs/ docs/_build` |

## Dataset Integration

### MicroLens-50k Integration
The project includes an ingestion pipeline for the MicroLens-50k dataset.

**Dataset Information:**
- Source: https://recsys.westlake.edu.cn/MicroLens-50k-Dataset/
- Format: CSV with columns [userID, videoID, timestamp]
- Purpose: Populate interaction history for recommendation system

**Schema Mapping:**
- `userID` → deterministic UUID (namespace: MICROLENS_NAMESPACE)
- `videoID` → deterministic UUID (namespace: MICROLENS_NAMESPACE)
- `timestamp` → ISO datetime (UTC)
- Event Type: `CLICK` (base interaction)
- Device: `MOBILE` (MicroLens default)

**Storage:**
- Redis: Session cache (24hr TTL) + recent interactions (max 100)
- DynamoDB: Persistent event store with metrics aggregation

## Notes
- Keep dependencies minimal and well-documented
- Prefer composition over inheritance
- Write code that is easy to test and maintain
- CSV ingestion supports deterministic UUID generation for reproducibility
