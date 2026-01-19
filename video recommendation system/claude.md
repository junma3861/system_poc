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
├── docker-compose.yml      # Local pgvector stack
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

# Install dependencies
conda install --file requirements.txt
# Or for pip packages
pip install -r requirements.txt

# Export environment
conda env export > environment.yml
```
### Local Postgres + pgvector
```bash
# Boot the database
docker-compose up -d pgvector

# Tail logs if needed
docker-compose logs -f pgvector

# Connection string for ORM/psql
export DATABASE_URL="postgresql://video_admin:video_admin@localhost:5432/video_rec_dev"

# Inspect manually
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

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8 .
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
| Format code | `black .` |
| Check types | `mypy src/` |
| Generate docs | `sphinx-build docs/ docs/_build` |

## Notes
- Keep dependencies minimal and well-documented
- Prefer composition over inheritance
- Write code that is easy to test and maintain
