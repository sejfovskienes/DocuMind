# DocuMind

Python 3.12 document processing and NLP API with SQLAlchemy, background workers, and Qdrant vector storage. Summarization is still incomplete.

## Development

Install the declared dependencies with Poetry 2.2.1 or later:

```powershell
poetry install
poetry run uvicorn app.main:app
poetry run python -m app.worker_launcher
```

Run the API and workers in separate terminals. Configure DB_CONNECTION_STRING, SECRET_KEY, HASHING_ALGORITHM, UPLOAD_DIR, QDRANT_URL, QDRANT_API_KEY, and QDRANT_COLLECTION_NAME locally. Do not commit secret values. The API initializes SQL tables at startup; inference adapters load models on first use. Optional ONNX inference needs its local model artifact.

## Checks

```powershell
poetry run python -m unittest discover -s tests
poetry run ruff check .
poetry run ruff format --check .
```

Tests use temporary SQLite databases and fake inference/vector backends. Actual PostgreSQL/Qdrant/model integration and a clean install of all heavy dependencies have not been validated. The existing .venv may need rebuilding if its base Python installation is missing.

## Project layout

- app/base/config: typed domain configuration classes in *_config.py files
- app/base/extensions: shared domain helpers
- app/ml: lazy inference model classes
- app/routes, app/schemas, app/models, app/services: API and SQL boundaries
- app/workers: document, NER, and summarization processing
- app/vector_database: Qdrant integration

See [agent guides](docs/agent-guides/README.md) for current architecture, compatibility, and known limits. Ruff options are documented in the [official configuration guide](https://docs.astral.sh/ruff/configuration/).

<img width="813" height="383" alt="image" src="https://github.com/user-attachments/assets/d4c8a00b-86d6-4cb7-9fd6-64fe858412d7" />
