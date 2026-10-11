# Workers, configuration, and validation

Updated from source on 2026-10-11 after the refactor.

## Task lifecycle

Task types remain DOCUMENT_PROCESSING, ENTITY_EXTRACTION, and SUMMARIZATION. Status values remain QUEUED, PROCESSING, FINISHED, and FAILED.

The task service selects queued rows in ID order and claims one with a conditional QUEUED-to-PROCESSING update. Competing claims cannot both succeed for the same row. The shared task runner sets FINISHED after success and FAILED after exceptions or a false processor result. Polling closes sessions on success, failure, idle passes, and interruption. Finished task history is still removed at worker startup; failed rows remain.

Document processing keeps the source after extraction, SQL, or vector-upload failures. Matching persisted chunks and embeddings are reused on retry; inconsistent persisted chunks are rejected. Cleanup happens after successful processing. NER inference is lazy and writes structured JSON; the schema still reads old string values. Summarization deliberately fails until a generation/persistence implementation is provided.

Worker processors have proper main guards. The combined launcher starts processors concurrently with sys.executable and cleans up child processes on shutdown or partial startup failure. Run it as python -m app.worker_launcher from the repository root.

## Configuration

Typed domain configuration classes live in [app/base/config](../../app/base/config), in {domain_name}_config.py files. Consumers import classes from app.base.config and access their settings directly. Existing environment keys are DB_CONNECTION_STRING, SECRET_KEY, HASHING_ALGORITHM, UPLOAD_DIR, QDRANT_URL, QDRANT_API_KEY, and QDRANT_COLLECTION_NAME. Dotenv loading retains override=True. Required database/JWT/Qdrant settings fail clearly at first use rather than during module import.

Model defaults remain all-mpnet-base-v2 for 768-dimensional embeddings, dslim/bert-base-NER for active entity extraction, and xlm-roberta-base plus app/core/onnx/xlm_roberta_ner.onnx for optional ONNX helpers. Model assets/downloads are separate from Python dependency installation. Chunk defaults remain 100 words with 90-word overlap. Poll intervals remain 10, 1, and 5 seconds for document, NER, and summarization.

[pyproject.toml](../../pyproject.toml) declares the imports required by API and workers, plus Ruff and HTTP test tooling in the dev group. poetry.lock is regenerated with Poetry 2.2.1. No dependency-manager migration was made.

## Verification

Focused unittest regressions live in [tests](../../tests). Run poetry run python -m unittest discover -s tests. Tests use temporary SQLite databases, fake model/vector backends, mocked calls, and disposable files. The import smoke test verifies that importing app.main and processor modules does not create SQL/Qdrant clients or load inference models.

Run poetry run ruff check . and poetry run ruff format --check . for source checks. No production databases, Qdrant instances, uploaded documents, or inference downloads are needed for these checks.

On 2026-10-11, all 40 offline regressions passed under isolated Python 3.12.10 using the existing installed project packages. Ruff 0.15.22 passed lint and formatting checks for 69 Python files, Poetry 2.2.1 passed check --lock, and git diff --check passed. The original .venv references a missing base interpreter; ignored .tools tooling was used for validation without rewriting that environment. These results do not establish a clean installation or production runtime behavior.

## Remaining limits

Production PostgreSQL/Qdrant connectivity, actual model inference, and a clean install of every heavy dependency require intentional integration checks. Conditional task claiming does not provide leases or crash recovery. A process crash can leave PROCESSING work. Cross-store writes are not atomic, legacy data is not migrated, and external file/vector deletion retention is not coordinated by a new policy. No CI or migration framework was introduced.
