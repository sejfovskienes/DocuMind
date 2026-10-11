# Observed code conventions

This guide records patterns present in the repository as inspected on 2026-10-11. These are observations, not confirmed personal preferences. Follow the surrounding module when making a small compatible change; use the recommendations in [CLEAN_CODE.md](CLEAN_CODE.md) when a change requires new structure.

## Project shape

- Python application code lives under `app/`, grouped into `routes`, `services`, `models`, `schemas`, `workers`, and `core`. The top-level `main.py` only prints a greeting; `app/main.py` builds the FastAPI app.
- Routes usually declare an `APIRouter` with a prefix and tags, then use FastAPI dependency injection for a SQLAlchemy `Session` and current user. Examples: `app/routes/auth.py`, `app/routes/document.py`, `app/routes/nlp.py`.
- Routes delegate persistence and lookup work to service modules. Services commonly receive `db: Session` explicitly. Examples: `app/services/user_service.py`, `app/services/document_service.py`, `app/services/task_service.py`.
- SQLAlchemy models use declarative `Base`, `__tablename__`, `Column` fields, and string relationship references. Examples: `app/models/user.py`, `app/models/document.py`.
- Pydantic schemas are separate from ORM models. Recent schemas use `ConfigDict(from_attributes=True)` (`app/schemas/task.py`); older schema code uses nested `Config` and `orm_mode` (`app/schemas/user.py`).
- Worker entry-point modules call a `main()` function under an `if __name__ == "__main__":` guard in the document and summarization processors. The NER processor currently has a malformed string condition instead (`app/workers/ner_worker/ner_worker_processor.py`).

## Naming and Python syntax

- Functions and variables use `snake_case`; classes use `PascalCase`; constants use uppercase names (for example `ACCESS_TOKEN_EXPIRES_MINUTES` in `app/auth.py` and `COLLECTION` in `app/vector_database/qdrant_client.py`).
- Type annotations are used on many service and route signatures. The codebase mixes built-in generics such as `list[str]` / `dict[str, Any]` with `typing.Optional` and `typing.List`. Examples: `app/services/document_service.py`, `app/schemas/task.py`, `app/schemas/document_chunk_schema.py`.
- Enums are string enums and their values are uppercase strings (`app/core/enum/worker_task_status.py`, `app/core/enum/worker_task_type.py`).
- Imports are generally at module top. Some modules group local imports after third-party imports, while others mix ordering; no formatter or linter is configured in `pyproject.toml`.

## Formatting and behavior patterns

- Four-space indentation is typical, but blank-line spacing and multiline argument wrapping vary.
- FastAPI failures are often expressed as `HTTPException` with `status_code` and `detail` (for example `app/routes/auth.py`, `app/services/document_service.py`).
- SQLAlchemy writes commonly follow `add` → `commit` → `refresh`; worker task updates use a data dictionary (`app/services/task_service.py`).
- Worker task state is represented with `WorkerTaskStatus`; task types are represented with `WorkerTaskType`.
- Some modules load dotenv values and read settings into module-level constants (`app/database.py`, `app/auth.py`, `app/vector_database/qdrant_client.py`). Do not infer from this that secrets should be loaded or printed in new code.
- Logging is inconsistent: workers and auth code use `print`, and there is no common logging convention evident from the inspected files.
- `pyproject.toml` declares Python `>=3.12` and project dependencies. It contains no configured formatter, linter, or test tool sections.

## Inconsistencies to account for

These examples are evidence that a pattern is mixed; they are not conventions to reproduce.

- Whitespace, trailing spaces, comment styles, and line wrapping vary, including in `app/auth.py`, `app/routes/document.py`, and worker modules.
- ORM schema configuration varies between Pydantic v2-style `model_config` and legacy `Config.orm_mode` (`app/schemas/task.py` vs. `app/schemas/user.py`).
- Optional annotations vary between `Optional[T]` and `T | None`.
- Service error handling varies: some services raise `HTTPException`, some return `None` or booleans, and some catch broad exceptions (`app/services/document_service.py`, `app/services/task_service.py`).
- Worker loops do not consistently handle database session lifetime and task outcomes; for example, `app/workers/document_worker/document_worker.py` and `app/workers/ner_worker/ner_worker.py` differ from `app/workers/summarization_worker/summarization_worker.py`.
- Existing identifiers include apparent misspellings such as `finshed_at` in `app/models/worker_task.py` and `occurred` misspelled in error text in several files. Preserve persisted/API names unless the task explicitly handles migration compatibility.
