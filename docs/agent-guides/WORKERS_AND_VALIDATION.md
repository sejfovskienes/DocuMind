# Workers, configuration, and validation

This guide records worker behavior observed in the repository for future implementation work. It distinguishes current behavior from recommended design and does not claim that the worker code has been run or tested.

## Queue and task flow (observed)

WorkerTask rows use string task types DOCUMENT_PROCESSING, ENTITY_EXTRACTION, and SUMMARIZATION. Declared status values are QUEUED, PROCESSING, FINISHED, and FAILED. The model declares status with SQLAlchemy insert_default=QUEUED; it does not declare a database server default. Task payloads are JSON and carry document IDs, plus user ID for summarization. Task creation is done by the document upload endpoint and the NLP endpoints. The task service fetches the first matching queued task by type, without an ordering or claim/lock operation.

The intended sequence is upload -> queued document processing -> PDF text extraction, normalization, chunking, embeddings, relational chunk persistence, and Qdrant upsert -> queued entity extraction or summarization on request. NER reads relational chunks and writes extracted entity values back to those rows. Summarization currently fetches Qdrant chunks, logs them, and does not produce a summary.

The actual terminal-state behavior is inconsistent. Document and NER handlers set a task to FAILED on exceptions but their finally blocks set it to FINISHED unconditionally. Document processing also marks the row finished after a false result. Summarization's processing method has no explicit return, so the loop treats its result as false and marks the task failed. Finished rows are deleted by each worker at startup, so task history is short-lived; failed rows are retained. Document worker's finally also removes the uploaded local file, including after processing failure. A worker that exits while a task is processing leaves no visible recovery/lease mechanism in the code inspected.

## Worker startup and runtime assumptions (observed)

Each processor module has a worker loop that polls its task type and sleeps when no work is found (document: 10 seconds, NER: 1 second, summarization: 5 seconds). Loops are long-running and handle KeyboardInterrupt. The combined app/start_all_workers.py contains two definitions of main and two main guards. The NER processor's guard is the non-empty string condition if "__name__==__main__":, which is always truthy; importing that module invokes its worker startup. Since the combined launcher imports this processor at module scope, if its initialization succeeds, execution enters the NER loop during that import, before either main guard runs. Even if that import side effect were fixed, the first main guard calls the NER processor directly in a blocking loop before the later terminal-launching main definition is reached. The second launcher is therefore only structural intent, not the effective runtime path.

The document worker module constructs a SentenceTransformer for all-mpnet-base-v2 at import time. NERWorker initialization loads Hugging Face dslim/bert-base-NER, xlm-roberta-base, and an ONNX runtime session; importing its processor invokes this initialization through the malformed guard. The model path points to app/core/onnx/xlm_roberta_ner.onnx. Qdrant is contacted by document processing and summarization. This guide did not open model binaries or run workers.

## Configuration and dependencies

Observed environment variable names:

- DB_CONNECTION_STRING for SQLAlchemy database setup.
- SECRET_KEY and HASHING_ALGORITHM for JWT helpers in app/auth.py.
- UPLOAD_DIR for upload storage; the document route creates this directory during import.
- QDRANT_URL, QDRANT_API_KEY, and QDRANT_COLLECTION_NAME for Qdrant.

Database and Qdrant modules call load_dotenv(override=True). Missing required values can therefore prevent import/client initialization. Avoid copying real environment values into docs or logs.

The declared project dependencies in pyproject.toml and inspected Poetry lock package list do not include the worker-specific imports observed in source (for example SQLAlchemy, PyMuPDF/fitz, sentence-transformers, transformers, onnxruntime, numpy, qdrant-client, and art). The lock inventory lists only FastAPI-related and authentication packages plus dotenv libraries. Confirm the intended dependency manager and make worker dependencies reproducible before claiming a clean install supports worker execution. Python is declared as >=3.12.

## Validation status and suggested checks

No Python test suite was found in the repository scan; the only file named like a test is a model-testing Jupyter notebook. No tests or workers were executed for this guide. In particular, there is no evidence here that database or Qdrant connectivity, model downloads, or PDF processing work in the current environment.

For future worker changes, keep validation offline and deterministic where possible: exercise task status transitions with a temporary/mock database session; verify task selection and that failures remain failures; test text normalization/chunk overlap and empty input without loading models; mock embedding, Qdrant, and filesystem calls; and test each processor's import/startup behavior without entering infinite loops. A separate integration check can validate database schema, model availability, PDF parsing, and Qdrant configuration where those services are intentionally provisioned. Do not use real uploaded documents or production credentials in unit checks.

## Improvement candidates (recommendations, not current behavior)

1. Make each worker's task claim atomic so multiple processes cannot take the same queued row; consider leases/recovery for abandoned processing tasks.
2. Centralize success/failure transitions so terminal status is set once, only after the operation actually succeeds, and retain task history according to an explicit policy.
3. Make document cleanup conditional on the intended retry/retention policy; ensure a failed task can still be retried with its source file.
4. Repair the combined startup entry point and NER module guard; keep module imports side-effect free.
5. Declare and lock the runtime dependencies needed by the workers, and document model artifacts/download expectations separately from Python package installation.
6. Add tests around state transitions and task selection before changing the polling/queue implementation.
