# Code conventions

Updated from source on 2026-10-11 after the requested refactor.

- Keep the feature layout: routes, schemas, SQL models, services, workers, vector_database, and inference adapters in ml.
- Put shared domain helpers in app/base/extensions and typed `{Domain}Config` classes in app/base/config/{domain_name}_config.py. Import classes through the config package and read their attributes directly. Add a module when it owns a useful responsibility, not just to shorten a file.
- Name application modules `{domain_name}_{role}.py`, such as document_router.py, document_service.py, document_model.py, document_schema.py, and document_extension.py. Standard __init__.py/main.py and test_*.py names are exceptions.
- Use Python 3.12 types: built-in collections, T | None, and collections.abc for callable/iterator types. Use typing.Any when values have genuinely varied shapes.
- Use explicit package exports in __init__.py for models, schemas, service modules, enums, extensions, and model adapters. Import multiple local names through these packages, or import a configuration class and qualify its settings.
- Keep heavy inference imports lazy. Package exports must not start workers, construct remote clients, or connect to the database.
- Use ConfigDict(from_attributes=True) for Pydantic schemas that read ORM objects.
- Persist task outcomes through the shared task runner. Use rollback on failed SQL writes and keep session ownership explicit.
- Use UTC for new timestamps. Retain existing SQL column timezone types and persisted/API field names, including finshed_at.
- Preserve API routes/methods and stored contracts unless an explicit task changes them. Legacy entity strings and metadata_id remain accepted by the chunk schema.

## Ruff

[pyproject.toml](../../pyproject.toml) configures Ruff for Python 3.12, 88-character formatting, double quotes, spaces, LF line endings, import ordering, basic correctness checks, and modern annotation syntax. UP042 is disabled to preserve the current string-enum behavior. Notebooks, local tooling, uploaded documents, and model assets are excluded.

Run poetry run ruff check . and poetry run ruff format --check . for verification. Use poetry run ruff check . --fix followed by poetry run ruff format . when applying safe lint fixes and formatting.
